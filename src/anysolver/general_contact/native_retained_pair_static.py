"""Internal two-beam retained-coordinate native static contact development."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
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
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from anysolver._ge_beam3_p5_seeded.codec import MAX_BYTES, _load

from .native_retained_cell_pair import (
    NativeRetainedCellPairResult,
    NativeRetainedSelectedCellPair,
)
from .native_retained_whole_pair import (
    NativeRetainedWholeCurvePair,
    NativeRetainedWholePairResult,
)


PROFILE = "NATIVE_B3_GE_SELECTED_CELL_PAIR_STATIC_DEV_V1"
CHECKPOINT_SCHEMA = "NATIVE_RETAINED_SELECTED_CELL_PAIR_CHECKPOINT_DEV_V1"
WHOLE_PROFILE = "NATIVE_B3_GE_WHOLE_CURVE_PAIR_STATIC_DEV_V4"
WHOLE_CHECKPOINT_SCHEMA = "NATIVE_RETAINED_WHOLE_CURVE_PAIR_CHECKPOINT_DEV_V4"
FIBRE_WHOLE_PROFILE = "NATIVE_B3_GE_PHYSICAL_FIBRE_WHOLE_CURVE_PAIR_STATIC_DEV_V1"
FIBRE_WHOLE_CHECKPOINT_SCHEMA = "NATIVE_PHYSICAL_FIBRE_WHOLE_CURVE_PAIR_CHECKPOINT_DEV_V1"


@dataclass(frozen=True)
class NativeRetainedPairAccepted:
    mechanical: object
    histories: tuple
    completed_targets: int
    contact: NativeRetainedCellPairResult | NativeRetainedWholePairResult


@dataclass(frozen=True)
class NativeRetainedPairRun:
    status: str
    accepted: NativeRetainedPairAccepted
    failure: str | None
    checkpoint: bytes
    profile: str = PROFILE

    @property
    def checkpoint_sha256(self) -> str:
        return sha256(self.checkpoint).hexdigest()


class NativeRetainedRoundPairAnalysis:
    """Two disjoint native beams with an exact admitted pair contact kernel."""

    def __init__(self, definitions: tuple[NativeBeamDefinition, ...],
                 boundaries: tuple, program: NativeNodalProgram,
                 contact: NativeRetainedSelectedCellPair | NativeRetainedWholeCurvePair, *,
                 gap_tolerance_m: float, equilibrium_tolerance: float,
                 maximum_swept_intervals: int):
        if (type(definitions) is not tuple or len(definitions) != 2
                or any(type(item) is not NativeBeamDefinition for item in definitions)):
            raise ValueError("native pair owner needs two exact beam definitions")
        if type(program) is not NativeNodalProgram:
            raise TypeError("native pair owner needs exact retained nodal program")
        if type(contact) not in (NativeRetainedSelectedCellPair,
                                 NativeRetainedWholeCurvePair):
            raise TypeError("native pair owner needs exact distributed pair kernel")
        self.profile = (PROFILE if type(contact) is NativeRetainedSelectedCellPair
                        else WHOLE_PROFILE)
        self.checkpoint_schema = (
            CHECKPOINT_SCHEMA if self.profile == PROFILE
            else WHOLE_CHECKPOINT_SCHEMA
        )
        controls = (gap_tolerance_m, equilibrium_tolerance)
        if any(type(item) not in (int, float) or not isfinite(item) or item <= 0.0
               for item in controls):
            raise ValueError("native pair owner needs positive gap/equilibrium tolerances")
        if type(maximum_swept_intervals) is not int or maximum_swept_intervals < 1:
            raise ValueError("native pair owner needs finite swept interval budget")
        self.native = NativeBeamAnalysis(definitions, boundaries)
        if self.native._family=='PHYSICAL_FIBRE_NODAL':
            if type(contact) is not NativeRetainedWholeCurvePair:
                raise ValueError('physical-fibre pair currently requires whole-curve geometry')
            from .native_fibre_context import NativeFibreContactContext,NativeRetainedFibreElement
            self.context=NativeFibreContactContext(self.native,program)
            expected=NativeRetainedFibreElement
            self.profile=FIBRE_WHOLE_PROFILE
            self.checkpoint_schema=FIBRE_WHOLE_CHECKPOINT_SCHEMA
        else:
            if (type(contact) is NativeRetainedWholeCurvePair
                    and contact.certify_open_intervals):
                raise ValueError('chord open certificates require the physical-fibre pair profile')
            self.context = NativeNodalContext(self.native.model, program)
            expected=NativeGeneralizedStaticElement
        if (len(self.context.elements) != 2
                or any(type(element) is not expected
                       for _, element in self.context.elements)):
            raise ValueError("native pair owner needs two exact homogeneous retained elements")
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
        if (type(contact) is NativeRetainedWholeCurvePair
                and (tuple(a.node_ids) != contact.node_ids_a
                     or tuple(b.node_ids) != contact.node_ids_b)):
            raise ValueError("native whole-pair material node identities do not bind model")
        self.contact = contact
        self.program = program
        self.gap_tolerance = float(gap_tolerance_m)
        self.equilibrium_tolerance = float(equilibrium_tolerance)
        self.maximum_swept_intervals = maximum_swept_intervals
        self.identity = self._identity()
        initial = self.context.initial
        first = self._contact(initial.mechanical)
        roundoff = 256.0*np.finfo(float).eps*max(
            1.0, *(float(np.max(np.abs(element.operator.reference.coordinates)))
                   for _, element in self.context.elements),
            contact.radius,
        )
        if first.conservative_lower_gap_m < -roundoff:
            raise ValueError(
                f"initial native pair gap not certified: conservative lower "
                f"bound {first.conservative_lower_gap_m} m"
            )
        self.initial = NativeRetainedPairAccepted(
            initial.mechanical, initial.histories, 0, first,
        )

    def _identity(self) -> str:
        return sha(dict(
            profile=self.profile,
            native_model=self.context.identity,
            native_support_sha256=sha256(self.context.support_identity).hexdigest(),
            contact=self.contact.identity,
            gap_tolerance_m=self.gap_tolerance,
            equilibrium_tolerance=self.equilibrium_tolerance,
            maximum_swept_intervals=self.maximum_swept_intervals,
        ))

    def _guard(self) -> None:
        if self._identity() != self.identity:
            raise ValueError("native pair definition/settings changed")
        if self.contact._fingerprint() != self.contact.identity:
            raise ValueError("native pair contact definition changed")
        self.native._guard()
        if self.native._family=='PHYSICAL_FIBRE_NODAL':self.context.guard()

    def _record(self, target: int, mechanical, origins,
                previous_sha256: str):
        if type(target) is not int or not 1 <= target <= len(self.program.targets):
            raise ValueError("native pair checkpoint target")
        mechanical = self.context.make(mechanical.descriptor())
        residual, tangent, metrics, responses, contact = self._assemble(
            mechanical, self.program.targets[target-1], origins,
        )
        _, correction = self.context.step(mechanical, residual, tangent)
        if max(*metrics, correction) > self.equilibrium_tolerance:
            raise ValueError("native pair checkpoint requires coupled equilibrium")
        if contact.conservative_lower_gap_m < -self.gap_tolerance:
            raise ValueError("native pair checkpoint gap tolerance")
        histories = self.context.histories(
            tuple(response.history for response in responses)
        )
        summary = dict(
            potential_j=contact.potential_j,
            conservative_lower_gap_m=contact.conservative_lower_gap_m,
            beam_a_force_n=contact.beam_a_force_n,
            beam_b_force_n=contact.beam_b_force_n,
            beam_a_moment_nm=contact.beam_a_moment_nm,
            beam_b_moment_nm=contact.beam_b_moment_nm,
        )
        if type(contact) is NativeRetainedCellPairResult:
            summary.update(
                sampled_gap_m=contact.sampled_gap_m,
                integration_points=contact.integration_points,
                integrated_intervals=contact.integrated_intervals,
                projection_evaluations=contact.projection_evaluations,
                maximum_relative_integration_error=(
                    contact.maximum_relative_integration_error
                ),
                gap_cells_checked=contact.gap_cells_checked,
            )
        else:
            summary.update(
                minimum_sampled_gap_m=contact.minimum_sampled_gap_m,
                energy_error_j=contact.energy_error_j,
                force_error_n=contact.force_error_n,
                tangent_error_n_per_m=contact.tangent_error_n_per_m,
                search_cells=contact.search_cells,
                integration_intervals=contact.integration_intervals,
                integration_evaluations=contact.integration_evaluations,
                integration_cells_checked=contact.integration_cells_checked,
                bounded_omission_cells=contact.bounded_omission_cells,
                unresolved_search_intervals=contact.unresolved_search_intervals,
            )
        row = dict(target=target, previous_sha256=previous_sha256,
                   mechanical=mechanical.descriptor(), histories=histories,
                   contact=summary)
        return NativeRetainedPairAccepted(
            mechanical, histories, target, contact,
        ), _load(canonical(row).decode("ascii"))

    def _checkpoint(self, records: tuple[dict, ...]) -> bytes:
        self._guard()
        if type(records) is not tuple or len(records) > len(self.program.targets):
            raise ValueError("native pair checkpoint record extent")
        body = dict(schema=self.checkpoint_schema, profile=self.profile,
                    identity=self.identity, completed_targets=len(records),
                    records=records)
        raw = canonical({**body, "checkpoint_sha256": sha(body)})
        if len(raw) > MAX_BYTES:
            raise ValueError("native pair checkpoint byte limit")
        return raw

    def _restore(self, raw: bytes, expected_sha256: str):
        self._guard()
        if (type(raw) is not bytes or type(expected_sha256) is not str
                or sha256(raw).hexdigest() != expected_sha256):
            raise ValueError("native pair external checkpoint hash mismatch")
        value = _load(raw.decode("ascii"))
        keys = {"schema", "profile", "identity", "completed_targets",
                "records", "checkpoint_sha256"}
        if type(value) is not dict or set(value) != keys:
            raise ValueError("native pair checkpoint schema")
        body = {key: item for key, item in value.items()
                if key != "checkpoint_sha256"}
        if (value["schema"] != self.checkpoint_schema
                or value["profile"] != self.profile
                or value["identity"] != self.identity
                or value["checkpoint_sha256"] != sha(body)):
            raise ValueError("native pair checkpoint definition/settings binding")
        count = value["completed_targets"]
        if (type(count) is not int or not 0 <= count <= len(self.program.targets)
                or type(value["records"]) is not list
                or len(value["records"]) != count):
            raise ValueError("native pair checkpoint target extent")
        accepted = self.initial
        previous = sha(dict(schema=self.checkpoint_schema,
                            identity=self.identity))
        records = ()
        for index, row in enumerate(value["records"], 1):
            if (type(row) is not dict or set(row) !=
                    {"target", "previous_sha256", "mechanical", "histories", "contact"}
                    or row["target"] != index or row["previous_sha256"] != previous):
                raise ValueError("native pair checkpoint accepted chain")
            mechanical = self.context.make(row["mechanical"], decoded=True)
            proposed, replay = self._record(
                index, mechanical, accepted.histories, previous,
            )
            if canonical(row) != canonical(replay):
                raise ValueError("native pair checkpoint physical replay mismatch")
            accepted = proposed
            records = (*records, replay)
            previous = sha(replay)
        if self._checkpoint(records) != raw:
            raise ValueError("native pair noncanonical checkpoint replay")
        return accepted, records

    def _contact(self, mechanical) -> (
        NativeRetainedCellPairResult | NativeRetainedWholePairResult
    ):
        a, b = self.indices
        return self.contact.evaluate(
            mechanical.positions[self.context.nodes[a]],
            mechanical.position_low[self.context.nodes[a]],
            mechanical.cell_rotations[a],
            mechanical.positions[self.context.nodes[b]],
            mechanical.position_low[self.context.nodes[b]],
            mechanical.cell_rotations[b],
        )

    def _recoverable_trial_contact_error(self, exc: Exception) -> bool:
        """Only geometric/resource non-admission may trigger a path cutback."""
        message = str(exc)
        if type(self.contact) is NativeRetainedSelectedCellPair:
            return (type(exc) is ValueError
                    and "undeclared native half-cell pair" in message)
        return (
            type(exc) in (ValueError, MemoryError)
            and message.startswith((
                "native whole pair integration interval budget exhausted",
                "native whole pair integration parameter resolution exhausted",
                "native whole pair has competing target minima",
                "native whole pair target ownership is unresolved",
                "native union has competing",
                "native union search cell budget exhausted",
                "native union search depth budget exhausted",
                "B3 projection has competing equal-distance minima",
                "B3 closest-point branch lacks positive curvature",
                "coincident B3 centrelines cannot define a contact normal",
            ))
        )

    def _assemble(self, mechanical, parameter, origins, *, prepared_contact=None):
        self._guard()
        if prepared_contact is not None and prepared_contact[0] is not mechanical:
            raise ValueError('native pair prepared contact requires the exact candidate pose')
        residual, tangent, _, responses, _ = self.context.assemble(
            mechanical, parameter, origins,
        )
        contact = (self._contact(mechanical) if prepared_contact is None
                   else prepared_contact[1])
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
        stack = [(0.0, 1.0, start_gap, end_gap)]
        visited = 0
        while stack:
            left, right, left_gap, right_gap = stack.pop()
            visited += 1
            if visited > self.maximum_swept_intervals:
                return False
            # Every path point is within half this interval of one endpoint.
            # Both stored gaps are conservative lower bounds, so this proves
            # safety without constructing another contact candidate.
            if (min(left_gap, right_gap)
                    -0.5*(right-left)*speed-roundoff >= -self.gap_tolerance):
                continue
            middle = 0.5*(left+right)
            state = self.context.advance(start, middle*increment)
            try:
                gap = self._contact(state).conservative_lower_gap_m
            except (ValueError, MemoryError) as exc:
                if self._recoverable_trial_contact_error(exc):
                    return False
                raise
            if gap < -self.gap_tolerance:
                return False
            if gap-0.5*(right-left)*speed-roundoff >= -self.gap_tolerance:
                continue
            stack.extend(((left, middle, left_gap, gap),
                          (middle, right, gap, right_gap)))
        return True

    def solve(self, *, checkpoint: bytes | None = None,
              expected_sha256: str | None = None,
              stop_after: int | None = None, cancellation_token=None) -> NativeRetainedPairRun:
        if self.native._family=='PHYSICAL_FIBRE_NODAL':
            with self.context.operation(cancellation_token):
                return self._solve(checkpoint=checkpoint,expected_sha256=expected_sha256,
                    stop_after=stop_after,cancellation_token=cancellation_token)
        if cancellation_token is not None:
            raise ValueError('cancellation token requires the physical-fibre pair profile')
        return self._solve(checkpoint=checkpoint,expected_sha256=expected_sha256,stop_after=stop_after)

    def _solve(self, *, checkpoint=None,expected_sha256=None,stop_after=None,cancellation_token=None):
        end = len(self.program.targets) if stop_after is None else stop_after
        if type(end) is not int or not 0 <= end <= len(self.program.targets):
            raise ValueError("native pair bounded stop target")
        if checkpoint is None:
            if expected_sha256 is not None:
                raise ValueError("native pair hash requires checkpoint")
            accepted, records = self.initial, ()
            capsule = self._checkpoint(records)
        else:
            accepted, records = self._restore(checkpoint, expected_sha256)
            capsule = checkpoint
        if accepted.completed_targets > end:
            raise ValueError("native pair accepted target cannot rewind")
        if self.native._family=='PHYSICAL_FIBRE_NODAL':self.context.activate_cancellation(cancellation_token)
        try:
            for index in range(accepted.completed_targets, end):
                parameter = self.program.targets[index]
                trial = accepted.mechanical
                origins = accepted.histories
                prepared_evaluation = None
                for iteration in range(self.program.max_iterations+1):
                    if prepared_evaluation is None:
                        residual, tangent, metrics, responses, contact = self._assemble(
                            trial, parameter, origins,
                        )
                    else:
                        self._guard()
                        residual, tangent, metrics, responses, contact = prepared_evaluation
                        prepared_evaluation = None
                    step, correction = self.context.step(trial, residual, tangent)
                    if max(*metrics, correction) <= self.equilibrium_tolerance:
                        if contact.conservative_lower_gap_m < -self.gap_tolerance:
                            raise RuntimeError("native pair endpoint gap tolerance not met")
                        previous = (sha(records[-1]) if records else sha(dict(
                            schema=self.checkpoint_schema, identity=self.identity,
                        )))
                        proposed, record = self._record(
                            index+1, trial, origins, previous,
                        )
                        next_records = (*records, record)
                        staged = self._checkpoint(next_records)
                        if self.native._family == 'PHYSICAL_FIBRE_NODAL':
                            self.context._safe_point()
                        accepted, records, capsule = proposed, next_records, staged
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
                    rejected = dict(geometry=0, gap=0, swept=0, merit=0)
                    last_rejection = ""
                    for cut in range(self.program.max_backtracks+1):
                        increment = step*(fraction*0.5**cut)
                        candidate = self.context.advance(trial, increment)
                        try:
                            candidate_contact = self._contact(candidate)
                        except (ValueError, MemoryError) as exc:
                            if self._recoverable_trial_contact_error(exc):
                                rejected["geometry"] += 1
                                last_rejection = (f"geometry {type(exc).__name__}: "
                                                  f"{str(exc)[:320]}")
                                continue
                            raise
                        if (candidate_contact.conservative_lower_gap_m
                                < -self.gap_tolerance):
                            rejected["gap"] += 1
                            last_rejection = (
                                "gap lower bound "
                                f"{candidate_contact.conservative_lower_gap_m} m"
                            )
                            continue
                        if not self._swept_admissible(
                                    trial, increment, candidate,
                                    contact.conservative_lower_gap_m,
                                    candidate_contact.conservative_lower_gap_m,
                                ):
                            rejected["swept"] += 1
                            last_rejection = "swept gap not certified"
                            continue
                        fibre = self.native._family == 'PHYSICAL_FIBRE_NODAL'
                        evaluated = self._assemble(candidate, parameter, origins,
                            prepared_contact=(candidate,candidate_contact) if fibre else None)
                        changed = evaluated[2]
                        if max(changed) < max(metrics):
                            trial = candidate
                            if fibre:prepared_evaluation = evaluated
                            break
                        rejected["merit"] += 1
                        last_rejection = f"merit {max(changed)} >= {max(metrics)}"
                    else:
                        if type(self.contact) is NativeRetainedWholeCurvePair:
                            raise RuntimeError(
                                "native whole pair line-search/gap limit: "
                                f"iteration={iteration}, rejected={rejected}, "
                                f"last={last_rejection}"
                            )
                        raise RuntimeError("native pair line-search/gap limit")
            status = "completed" if end == len(self.program.targets) else "paused"
            return NativeRetainedPairRun(status, accepted, None, capsule,
                                         self.profile)
        except Exception as exc:
            return NativeRetainedPairRun(
                "failed", accepted, type(exc).__name__+": "+str(exc), capsule,
                self.profile,
            )
