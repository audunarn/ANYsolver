"""Internal coupled retained-coordinate native beam/plane static development owner.

One generalized native B3-GE beam and one fixed round-centreline plane kernel
are admitted. No public native workflow profile or restart is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from anysolver._ge_beam3_generalized_static_boundary import spatial_jacobian
from anysolver._ge_beam3_native_analysis import NativeBeamAnalysis
from anysolver._ge_beam3_native_definition import NativeBeamDefinition
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_retained_nodal_loading import (
    Context as NativeNodalContext,
    Program as NativeNodalProgram,
)
from anysolver._ge_beam3_p5_seeded.core import sha

from .native_retained_line_plane import (
    NativeRetainedLinePlaneResult,
    NativeRetainedRoundLinePlane,
)


PROFILE = "NATIVE_B3_GE_RETAINED_ROUND_LINE_PLANE_STATIC_DEV_V0"


@dataclass(frozen=True)
class NativeRetainedContactAccepted:
    mechanical: object
    histories: tuple
    completed_targets: int
    contact: NativeRetainedLinePlaneResult


@dataclass(frozen=True)
class NativeRetainedContactRun:
    status: str
    accepted: NativeRetainedContactAccepted
    failure: str | None
    profile: str = PROFILE


class NativeRetainedRoundPlaneAnalysis:
    """Separate owner; all native internal coordinates remain in the solve."""

    def __init__(self, definitions: tuple[NativeBeamDefinition, ...],
                 boundaries: tuple, program: NativeNodalProgram,
                 contact: NativeRetainedRoundLinePlane, *,
                 gap_tolerance_m: float, equilibrium_tolerance: float):
        if (type(definitions) is not tuple or len(definitions) != 1
                or type(definitions[0]) is not NativeBeamDefinition):
            raise ValueError("native contact development owner needs one exact beam definition")
        if type(program) is not NativeNodalProgram:
            raise TypeError("native contact owner needs exact retained nodal program")
        if type(contact) is not NativeRetainedRoundLinePlane:
            raise TypeError("native contact owner needs exact retained line/plane kernel")
        if (type(gap_tolerance_m) not in (int, float)
                or not isfinite(gap_tolerance_m) or gap_tolerance_m <= 0.0
                or type(equilibrium_tolerance) not in (int, float)
                or not isfinite(equilibrium_tolerance) or equilibrium_tolerance <= 0.0):
            raise ValueError("native contact owner needs positive gap/equilibrium tolerances")
        self.native = NativeBeamAnalysis(definitions, boundaries)
        self.context = NativeNodalContext(self.native.model, program)
        if len(self.context.elements) != 1:
            raise ValueError("native contact owner needs exactly one element")
        element_id, element = self.context.elements[0]
        if (type(element) is not NativeGeneralizedStaticElement
                or element_id != contact.element_id
                or sha(element.operator.reference.canonical_data())
                != sha(contact.reference.canonical_data())):
            raise ValueError("native contact kernel does not bind the generalized beam")
        self.contact = contact
        self.gap_tolerance = float(gap_tolerance_m)
        self.equilibrium_tolerance = float(equilibrium_tolerance)
        self.program = program
        initial = self.context.initial
        first = self._contact(initial.mechanical)
        roundoff = 256.0*np.finfo(float).eps*max(
            1.0, float(np.max(np.abs(element.operator.reference.coordinates))),
            contact.radius,
        )
        if first.minimum_gap_m < -roundoff:
            raise ValueError(
                f"unresolved initial native contact penetration {first.minimum_gap_m} m"
            )
        self.initial = NativeRetainedContactAccepted(
            initial.mechanical, initial.histories, 0, first,
        )

    def _contact(self, mechanical) -> NativeRetainedLinePlaneResult:
        nodes = self.context.nodes[0]
        return self.contact.evaluate(
            mechanical.positions[nodes], mechanical.position_low[nodes],
            mechanical.cell_rotations[0],
        )

    def _assemble(self, mechanical, parameter, origins):
        self.native._guard()
        r, j, _structural_metrics, responses, _works = self.context.assemble(
            mechanical, parameter, origins,
        )
        contact = self._contact(mechanical)
        slots = self.context.slots[0]
        r[slots] += contact.residual
        j[np.ix_(slots, slots)] += spatial_jacobian(
            contact.residual, contact.tangent,
        )
        scaled = r/self.context.scale
        metrics = (float(np.linalg.norm(scaled[self.context.equilibrium])),
                   float(np.linalg.norm(scaled[self.context.compatibility])))
        return r, j, metrics, responses, contact

    def solve(self) -> NativeRetainedContactRun:
        accepted = self.initial
        try:
            for index, parameter in enumerate(self.program.targets):
                trial = accepted.mechanical
                origins = accepted.histories
                for iteration in range(self.program.max_iterations+1):
                    r, j, metrics, responses, contact = self._assemble(
                        trial, parameter, origins,
                    )
                    step, correction = self.context.step(trial, r, j)
                    if max(*metrics, correction) <= self.equilibrium_tolerance:
                        if contact.minimum_gap_m < -self.gap_tolerance:
                            raise RuntimeError("native contact endpoint gap tolerance not met")
                        histories = self.context.histories(
                            tuple(response.history for response in responses)
                        )
                        accepted = NativeRetainedContactAccepted(
                            trial, histories, index+1, contact,
                        )
                        break
                    if iteration == self.program.max_iterations:
                        raise RuntimeError("native contact Newton iteration limit")
                    angular = [step[6*i+3:6*i+6]
                               for i in range(len(self.context.node_ids))]
                    angular.extend((step[self.context.nodal_count+3*c:
                                         self.context.nodal_count+3*c+3]
                                    for c in (0, 1)))
                    fraction = min(
                        1.0, 0.45*np.pi/max(
                            max(float(np.linalg.norm(value)) for value in angular),
                            np.finfo(float).tiny,
                        ),
                    )
                    for cut in range(self.program.max_backtracks+1):
                        candidate = self.context.advance(
                            trial, step*(fraction*0.5**cut),
                        )
                        _, _, changed, _, candidate_contact = self._assemble(
                            candidate, parameter, origins,
                        )
                        if (candidate_contact.minimum_gap_m >= -self.gap_tolerance
                                and max(changed) < max(metrics)):
                            trial = candidate
                            break
                    else:
                        raise RuntimeError("native contact line-search/gap limit")
            return NativeRetainedContactRun("completed", accepted, None)
        except Exception as exc:
            return NativeRetainedContactRun(
                "failed", accepted, type(exc).__name__+": "+str(exc),
            )
