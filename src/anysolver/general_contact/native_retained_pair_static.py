"""Internal two-beam retained-coordinate native static contact development."""

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

from .native_retained_cell_pair import (
    NativeRetainedCellPairResult,
    NativeRetainedSelectedCellPair,
)


PROFILE = "NATIVE_B3_GE_SELECTED_CELL_PAIR_STATIC_DEV_V0"


@dataclass(frozen=True)
class NativeRetainedPairAccepted:
    mechanical: object
    histories: tuple
    completed_targets: int
    contact: NativeRetainedCellPairResult


@dataclass(frozen=True)
class NativeRetainedPairRun:
    status: str
    accepted: NativeRetainedPairAccepted
    failure: str | None
    profile: str = PROFILE


class NativeRetainedRoundPairAnalysis:
    """Two disjoint native beams, one explicitly selected half-cell pair."""

    def __init__(self, definitions: tuple[NativeBeamDefinition, ...],
                 boundaries: tuple, program: NativeNodalProgram,
                 contact: NativeRetainedSelectedCellPair, *,
                 gap_tolerance_m: float, equilibrium_tolerance: float,
                 maximum_swept_intervals: int):
        if (type(definitions) is not tuple or len(definitions) != 2
                or any(type(item) is not NativeBeamDefinition for item in definitions)):
            raise ValueError("native pair owner needs two exact beam definitions")
        if type(program) is not NativeNodalProgram:
            raise TypeError("native pair owner needs exact retained nodal program")
        if type(contact) is not NativeRetainedSelectedCellPair:
            raise TypeError("native pair owner needs exact distributed pair kernel")
        controls = (gap_tolerance_m, equilibrium_tolerance)
        if any(type(item) not in (int, float) or not isfinite(item) or item <= 0.0
               for item in controls):
            raise ValueError("native pair owner needs positive gap/equilibrium tolerances")
        if type(maximum_swept_intervals) is not int or maximum_swept_intervals < 1:
            raise ValueError("native pair owner needs finite swept interval budget")
        self.native = NativeBeamAnalysis(definitions, boundaries)
        self.context = NativeNodalContext(self.native.model, program)
        if (len(self.context.elements) != 2
                or any(type(element) is not NativeGeneralizedStaticElement
                       for _, element in self.context.elements)):
            raise ValueError("native pair owner needs two generalized elements")
        ids = (contact.cells_a[0].element_id, contact.cells_b[0].element_id)
        index = {element_id: i for i, (element_id, _) in enumerate(self.context.elements)}
        if set(index) != set(ids):
            raise ValueError("native pair contact beam identities do not bind model")
        self.indices = (index[ids[0]], index[ids[1]])
        a, b = (self.context.elements[i][1] for i in self.indices)
        if (sha(a.operator.reference.canonical_data())
                != sha(contact.cells_a[0].reference.canonical_data())
                or sha(b.operator.reference.canonical_data())
                != sha(contact.cells_b[0].reference.canonical_data())):
            raise ValueError("native pair contact references do not bind model")
        if set(a.node_ids) & set(b.node_ids):
            raise ValueError("selected native pair does not admit shared material nodes")
        self.contact = contact
        self.program = program
        self.gap_tolerance = float(gap_tolerance_m)
        self.equilibrium_tolerance = float(equilibrium_tolerance)
        self.maximum_swept_intervals = maximum_swept_intervals
        self._settings_identity = self._settings_digest()
        initial = self.context.initial
        first = self._contact(initial.mechanical)
        roundoff = 256.0*np.finfo(float).eps*max(
            1.0, *(float(np.max(np.abs(element.operator.reference.coordinates)))
                   for _, element in self.context.elements),
            contact.radius,
        )
        if first.conservative_lower_gap_m < -roundoff:
            raise ValueError(
                f"unresolved initial native pair penetration "
                f"{first.conservative_lower_gap_m} m"
            )
        self.initial = NativeRetainedPairAccepted(
            initial.mechanical, initial.histories, 0, first,
        )

    def _settings_digest(self) -> str:
        return sha(dict(profile=PROFILE, contact=self.contact.identity,
                        gap_tolerance_m=self.gap_tolerance,
                        equilibrium_tolerance=self.equilibrium_tolerance,
                        maximum_swept_intervals=self.maximum_swept_intervals))

    def _guard(self) -> None:
        if self._settings_digest() != self._settings_identity:
            raise ValueError("native pair settings changed")
        self.native._guard()

    def _contact(self, mechanical) -> NativeRetainedCellPairResult:
        a, b = self.indices
        return self.contact.evaluate(
            mechanical.positions[self.context.nodes[a]],
            mechanical.position_low[self.context.nodes[a]],
            mechanical.cell_rotations[a],
            mechanical.positions[self.context.nodes[b]],
            mechanical.position_low[self.context.nodes[b]],
            mechanical.cell_rotations[b],
        )

    def _assemble(self, mechanical, parameter, origins):
        self._guard()
        residual, tangent, _, responses, _ = self.context.assemble(
            mechanical, parameter, origins,
        )
        contact = self._contact(mechanical)
        slots = self.context.slots[self.indices[0]]+self.context.slots[self.indices[1]]
        np.add.at(residual, slots, contact.residual)
        block = contact.tangent.copy()
        for first in (0, 42):
            block[first:first+42, first:first+42] = spatial_jacobian(
                contact.residual[first:first+42],
                block[first:first+42, first:first+42],
            )
        rows, columns = np.meshgrid(slots, slots, indexing="ij")
        np.add.at(tangent, (rows, columns), block)
        scaled = residual/self.context.scale
        metrics = (float(np.linalg.norm(scaled[self.context.equilibrium])),
                   float(np.linalg.norm(scaled[self.context.compatibility])))
        return residual, tangent, metrics, responses, contact

    def _swept_admissible(self, start, increment, end,
                          start_gap: float, end_gap: float) -> bool:
        self._guard()
        if min(start_gap, end_gap) < -self.gap_tolerance:
            return False
        speed = 0.0
        for index in self.indices:
            nodes = self.context.nodes[index]
            before = start.positions[nodes]+start.position_low[nodes]
            after = end.positions[nodes]+end.position_low[nodes]
            translation = float(np.max(np.linalg.norm(after-before, axis=1)))
            reference = self.context.elements[index][1].operator.reference
            cell_first = self.context.nodal_count+24*index
            rotation = max(
                float(np.linalg.norm(increment[cell_first+3*c:
                                               cell_first+3*c+3])
                      * np.linalg.norm(reference.half_cell_lift(c, 0.5)))
                for c in (0, 1)
            )
            speed += translation+rotation
        roundoff = 256.0*np.finfo(float).eps*max(
            1.0, float(np.max(np.abs(start.positions))),
            float(np.max(np.abs(end.positions))), self.contact.radius,
        )
        stack = [(0.0, 1.0)]
        visited = 0
        while stack:
            left, right = stack.pop()
            visited += 1
            if visited > self.maximum_swept_intervals:
                return False
            middle = 0.5*(left+right)
            state = self.context.advance(start, middle*increment)
            try:
                gap = self._contact(state).conservative_lower_gap_m
            except ValueError as exc:
                if "undeclared native half-cell pair" in str(exc):
                    return False
                raise
            if gap < -self.gap_tolerance:
                return False
            if gap-0.5*(right-left)*speed-roundoff >= -self.gap_tolerance:
                continue
            stack.extend(((left, middle), (middle, right)))
        return True

    def solve(self) -> NativeRetainedPairRun:
        accepted = self.initial
        try:
            for index, parameter in enumerate(self.program.targets):
                trial = accepted.mechanical
                origins = accepted.histories
                for iteration in range(self.program.max_iterations+1):
                    residual, tangent, metrics, responses, contact = self._assemble(
                        trial, parameter, origins,
                    )
                    step, correction = self.context.step(trial, residual, tangent)
                    if max(*metrics, correction) <= self.equilibrium_tolerance:
                        if contact.conservative_lower_gap_m < -self.gap_tolerance:
                            raise RuntimeError("native pair endpoint gap tolerance not met")
                        histories = self.context.histories(
                            tuple(response.history for response in responses)
                        )
                        accepted = NativeRetainedPairAccepted(
                            trial, histories, index+1, contact,
                        )
                        break
                    if iteration == self.program.max_iterations:
                        raise RuntimeError("native pair Newton iteration limit")
                    angular = [step[6*i+3:6*i+6]
                               for i in range(len(self.context.node_ids))]
                    angular.extend(
                        step[self.context.nodal_count+24*i+3*c:
                             self.context.nodal_count+24*i+3*c+3]
                        for i in range(len(self.context.elements)) for c in (0, 1)
                    )
                    fraction = min(
                        1.0, 0.45*np.pi/max(
                            max(float(np.linalg.norm(value)) for value in angular),
                            np.finfo(float).tiny,
                        ),
                    )
                    for cut in range(self.program.max_backtracks+1):
                        increment = step*(fraction*0.5**cut)
                        candidate = self.context.advance(trial, increment)
                        try:
                            candidate_contact = self._contact(candidate)
                        except ValueError as exc:
                            if "undeclared native half-cell pair" in str(exc):
                                continue
                            raise
                        if (candidate_contact.conservative_lower_gap_m
                                < -self.gap_tolerance
                                or not self._swept_admissible(
                                    trial, increment, candidate,
                                    contact.conservative_lower_gap_m,
                                    candidate_contact.conservative_lower_gap_m,
                                )):
                            continue
                        _, _, changed, _, _ = self._assemble(
                            candidate, parameter, origins,
                        )
                        if max(changed) < max(metrics):
                            trial = candidate
                            break
                    else:
                        raise RuntimeError("native pair line-search/gap limit")
            return NativeRetainedPairRun("completed", accepted, None)
        except Exception as exc:
            return NativeRetainedPairRun(
                "failed", accepted, type(exc).__name__+": "+str(exc),
            )
