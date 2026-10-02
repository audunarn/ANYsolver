"""Restricted coupled retained B3-GE and elastic S3 static contact owner."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite

import numpy as np

from anymaterial import IsotropicMaterial
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
from anysolver.e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement
from anysolver.fe_core import FEModel

from .native_retained_line_s3_work import (
    NativeRetainedLineS3Work,
    NativeRetainedLineS3WorkResult,
)
from .native_retained_station import _readonly
from .s3_skin_work import S3SkinWorkAdapter


PROFILE = "NATIVE_B3_GE_ELASTIC_S3_INTERIOR_STATIC_DEV_V1"
CHECKPOINT_SCHEMA = "NATIVE_B3_GE_ELASTIC_S3_CHECKPOINT_DEV_V1"


@dataclass(frozen=True)
class NativeRetainedS3Accepted:
    mechanical: object
    native_histories: tuple
    shell_displacement: np.ndarray
    completed_targets: int
    contact: NativeRetainedLineS3WorkResult


@dataclass(frozen=True)
class NativeRetainedS3Run:
    status: str
    accepted: NativeRetainedS3Accepted
    failure: str | None
    checkpoint: bytes
    profile: str = PROFILE

    @property
    def checkpoint_sha256(self) -> str:
        return sha256(self.checkpoint).hexdigest()


class NativeRetainedRoundS3Analysis:
    """One native beam and one elastic S3, both active in one Newton system."""

    def __init__(self, definitions: tuple[NativeBeamDefinition, ...],
                 native_boundaries: tuple, program: NativeNodalProgram,
                 shell_model: FEModel, contact: NativeRetainedLineS3Work, *,
                 gap_tolerance_m: float, equilibrium_tolerance: float,
                 maximum_swept_intervals: int):
        if (type(definitions) is not tuple or len(definitions) != 1
                or type(definitions[0]) is not NativeBeamDefinition
                or type(program) is not NativeNodalProgram):
            raise TypeError("native/S3 owner needs one exact native beam and program")
        if type(shell_model) is not FEModel or type(contact) is not NativeRetainedLineS3Work:
            raise TypeError("native/S3 owner needs exact S3 model and contact work")
        if (type(gap_tolerance_m) not in (int, float)
                or not isfinite(gap_tolerance_m) or gap_tolerance_m <= 0.0
                or type(equilibrium_tolerance) not in (int, float)
                or not isfinite(equilibrium_tolerance) or equilibrium_tolerance <= 0.0
                or type(maximum_swept_intervals) is not int
                or maximum_swept_intervals < 1):
            raise ValueError("native/S3 owner needs positive finite solver controls")
        self.native = NativeBeamAnalysis(definitions, native_boundaries)
        self.context = NativeNodalContext(self.native.model, program)
        if (len(self.context.elements) != 1
                or type(self.context.elements[0][1]) is not NativeGeneralizedStaticElement):
            raise ValueError("native/S3 owner needs one native generalized element")
        element_id, element = self.context.elements[0]
        kernel = contact.contact
        if (element_id != kernel.beam_element_id
                or tuple(element.node_ids) != kernel.beam_node_ids
                or sha(element.operator.reference.canonical_data())
                   != sha(kernel.beam_reference.canonical_data())):
            raise ValueError("native/S3 contact does not bind native beam")
        self.shell_model = shell_model
        self.contact = contact
        self.program = program
        self.gap_tolerance = float(gap_tolerance_m)
        self.equilibrium_tolerance = float(equilibrium_tolerance)
        self.maximum_swept_intervals = maximum_swept_intervals
        self.shell_stiffness, self.shell_free, self.shell_fixed = self._shell_contract()
        self.shell_contract_sha = self._shell_contract_sha()
        self.identity = self._identity()
        displacement = np.zeros(self.shell_stiffness.shape[0])
        initial_native = self.context.initial
        first = self._contact(initial_native.mechanical, displacement)
        scale = max(1.0, float(np.max(np.abs(kernel.beam_reference.coordinates))),
                    float(np.max(np.abs(contact.shell.reference_positions))))
        if first.contact.minimum_gap_m < -256.0*np.finfo(float).eps*scale:
            raise ValueError("unresolved initial native/S3 contact penetration: "
                             f"{first.contact.minimum_gap_m} m")
        self.initial = NativeRetainedS3Accepted(
            initial_native.mechanical, initial_native.histories,
            _readonly(displacement), 0, first,
        )

    def _identity(self) -> str:
        return sha(dict(
            profile=PROFILE,
            native_model=self.context.identity,
            native_support_sha256=sha256(self.context.support_identity).hexdigest(),
            shell_contract=self.shell_contract_sha,
            contact=self.contact.identity,
            gap_tolerance_m=self.gap_tolerance,
            equilibrium_tolerance=self.equilibrium_tolerance,
            maximum_swept_intervals=self.maximum_swept_intervals,
        ))

    def _shell_contract(self):
        model = self.shell_model
        if (len(model.mesh.elements) != 1 or model.constraint_equations
                or model.load_cases or model.mesh.element_activity is not None):
            raise ValueError("native/S3 owner needs one active S3 with simple supports")
        element_id = self.contact.shell.element_id
        element = model.mesh.elements.get(element_id)
        if (type(element) is not NativeParityE4PLS3V2DShellElement
                or element.shell_section is not None
                or tuple(element.node_ids) != self.contact.shell.node_ids):
            raise ValueError("native/S3 owner needs exact elastic S3 V2D")
        material = model.materials.get(element.material_name)
        if (type(material) is not IsotropicMaterial
                or material.yield_stress != 0.0
                or material.hardening_curve is not None):
            raise ValueError("native/S3 owner needs isotropic elastic S3 material")
        fresh = S3SkinWorkAdapter.from_model(
            model, self.contact.shell.body_id, element_id, self.contact.shell.side,
        )
        if (not np.array_equal(fresh.reference_positions,
                               self.contact.shell.reference_positions)
                or not np.array_equal(fresh.director, self.contact.shell.director)
                or fresh.physical_offset != self.contact.shell.physical_offset
                or (fresh.work_map != self.contact.shell.work_map).nnz):
            raise ValueError("native/S3 shell contact adapter does not bind model")
        n = model.mesh.dof_manager.total_dofs
        stiffness = np.zeros((n, n))
        slots = np.asarray(element.get_dof_mapping(model.mesh), dtype=int)
        local = element.compute_stiffness_matrix(model.mesh, material)
        if local.shape != (18, 18) or not np.all(np.isfinite(local)):
            raise ValueError("native/S3 shell stiffness is invalid")
        stiffness[np.ix_(slots, slots)] += local
        if not np.allclose(stiffness, stiffness.T, rtol=1e-10, atol=1e-10):
            raise ValueError("native/S3 shell stiffness is nonsymmetric")
        fixed = set()
        for boundary in model.boundary_conditions:
            for dof, value in boundary.get_constrained_dofs(model.mesh.dof_manager):
                if not np.isfinite(value) or value != 0.0:
                    raise ValueError("native/S3 owner admits only zero shell supports")
                fixed.add(int(dof))
        free = np.array(sorted(set(range(n))-fixed), dtype=int)
        if len(free) == 0 or np.linalg.matrix_rank(stiffness[np.ix_(free, free)]) < len(free):
            raise ValueError("native/S3 shell has a static rigid mechanism")
        return stiffness, free, np.array(sorted(fixed), dtype=int)

    def _shell_contract_sha(self):
        stiffness, free, fixed = self._shell_contract()
        element = self.shell_model.mesh.elements[self.contact.shell.element_id]
        material = self.shell_model.materials[element.material_name]
        return sha(dict(
            stiffness=stiffness, free=free, fixed=fixed,
            contact=self.contact._fingerprint(),
            kernel=self.contact.contact._fingerprint(),
            element=dict(identity=self.contact.shell.element_id,
                         nodes=element.node_ids,
                         formulation=element.formulation_id,
                         thickness=element.thickness,
                         reference_surface_offset=element.reference_surface_offset,
                         director_polarity=element.director_polarity),
            node_coordinates=[self.shell_model.mesh.nodes[node].coords()
                              for node in element.node_ids],
            material=dict(name=material.name,
                          elastic_modulus=material.elastic_modulus,
                          poisson_ratio=material.poisson_ratio,
                          density=material.density,
                          yield_stress=material.yield_stress),
        ))

    def _guard(self):
        self.context.guard()
        if self._identity() != self.identity:
            raise ValueError("native/S3 definition/settings changed")
        if self._shell_contract_sha() != self.shell_contract_sha:
            raise ValueError("native/S3 shell model/contact definition changed")
        self.native._guard()

    def _record(self, target: int, mechanical, displacement, origins,
                previous_sha256: str):
        if type(target) is not int or not 1 <= target <= len(self.program.targets):
            raise ValueError("native/S3 checkpoint target")
        mechanical = self.context.make(mechanical.descriptor())
        shell_u = np.asarray(displacement, dtype=float).reshape(-1)
        if (shell_u.size != self.shell_stiffness.shape[0]
                or not np.all(np.isfinite(shell_u))
                or np.any(shell_u[self.shell_fixed] != 0.0)):
            raise ValueError("native/S3 checkpoint shell displacement")
        residual, tangent, metrics, responses, contact = self._assemble(
            mechanical, shell_u, self.program.targets[target-1], origins,
        )
        _, correction = self._step(residual, tangent)
        if max(*metrics, correction) > self.equilibrium_tolerance:
            raise ValueError("native/S3 checkpoint requires coupled equilibrium")
        if contact.contact.minimum_gap_m < -self.gap_tolerance:
            raise ValueError("native/S3 checkpoint gap tolerance")
        histories = self.context.histories(
            tuple(response.history for response in responses)
        )
        physical = contact.contact
        summary = dict(
            potential_j=physical.potential_j,
            minimum_gap_m=physical.minimum_gap_m,
            minimum_rim_clearance_m=physical.minimum_rim_clearance_m,
            beam_force_n=physical.beam_force_n,
            shell_force_n=physical.shell_force_n,
            beam_moment_nm=physical.beam_moment_nm,
            shell_moment_nm=physical.shell_moment_nm,
            active_intervals=physical.active_intervals,
            integration_intervals=physical.integration_intervals,
            integration_evaluations=physical.integration_evaluations,
            energy_error_j=physical.energy_error_j,
            force_error_n=physical.force_error_n,
            tangent_error_n_per_m=physical.tangent_error_n_per_m,
        )
        row = dict(
            target=target, previous_sha256=previous_sha256,
            mechanical=mechanical.descriptor(),
            histories=histories, shell_displacement=shell_u,
            contact=summary,
        )
        accepted = NativeRetainedS3Accepted(
            mechanical, histories, _readonly(shell_u), target, contact,
        )
        return accepted, _load(canonical(row).decode("ascii"))

    def _checkpoint(self, records: tuple[dict, ...]) -> bytes:
        self._guard()
        if type(records) is not tuple or len(records) > len(self.program.targets):
            raise ValueError("native/S3 checkpoint record extent")
        body = dict(schema=CHECKPOINT_SCHEMA, profile=PROFILE,
                    identity=self.identity, completed_targets=len(records),
                    records=records)
        raw = canonical({**body, "checkpoint_sha256": sha(body)})
        if len(raw) > MAX_BYTES:
            raise ValueError("native/S3 checkpoint byte limit")
        return raw

    def _restore(self, raw: bytes, expected_sha256: str):
        self._guard()
        if (type(raw) is not bytes or type(expected_sha256) is not str
                or sha256(raw).hexdigest() != expected_sha256):
            raise ValueError("native/S3 external checkpoint hash mismatch")
        value = _load(raw.decode("ascii"))
        keys = {"schema", "profile", "identity", "completed_targets",
                "records", "checkpoint_sha256"}
        if type(value) is not dict or set(value) != keys:
            raise ValueError("native/S3 checkpoint schema")
        body = {key: item for key, item in value.items()
                if key != "checkpoint_sha256"}
        if (value["schema"] != CHECKPOINT_SCHEMA
                or value["profile"] != PROFILE
                or value["identity"] != self.identity
                or value["checkpoint_sha256"] != sha(body)):
            raise ValueError("native/S3 checkpoint definition/settings binding")
        count = value["completed_targets"]
        if (type(count) is not int or not 0 <= count <= len(self.program.targets)
                or type(value["records"]) is not list
                or len(value["records"]) != count):
            raise ValueError("native/S3 checkpoint target extent")
        accepted = self.initial
        previous = sha(dict(schema=CHECKPOINT_SCHEMA, identity=self.identity))
        records = ()
        for index, row in enumerate(value["records"], 1):
            if (type(row) is not dict or set(row) !=
                    {"target", "previous_sha256", "mechanical", "histories",
                     "shell_displacement", "contact"}
                    or row["target"] != index
                    or row["previous_sha256"] != previous):
                raise ValueError("native/S3 checkpoint accepted chain")
            mechanical = self.context.make(row["mechanical"], decoded=True)
            values = row["shell_displacement"]
            if (type(values) is not list
                    or len(values) != self.shell_stiffness.shape[0]
                    or any(type(item) is not float or not isfinite(item)
                           for item in values)):
                raise ValueError("native/S3 checkpoint shell displacement schema")
            proposed, replay = self._record(
                index, mechanical, np.array(values),
                accepted.native_histories, previous,
            )
            if canonical(row) != canonical(replay):
                raise ValueError("native/S3 checkpoint physical replay mismatch")
            accepted = proposed
            records = (*records, replay)
            previous = sha(replay)
        if self._checkpoint(records) != raw:
            raise ValueError("native/S3 noncanonical checkpoint replay")
        return accepted, records

    def _contact(self, mechanical, displacement):
        nodes = self.context.nodes[0]
        return self.contact.evaluate(
            mechanical.positions[nodes], mechanical.position_low[nodes],
            mechanical.cell_rotations[0], displacement,
        )

    def _assemble_structural(self, mechanical, displacement, parameter, origins):
        """Shared retained/native and S3 blocks, before any contact profile."""
        self._guard()
        native_r, native_j, _, responses, _ = self.context.assemble(
            mechanical, parameter, origins,
        )
        n_native = self.context.count
        n_shell = len(displacement)
        residual = np.r_[native_r, self.shell_stiffness@displacement]
        tangent = np.zeros((n_native+n_shell, n_native+n_shell))
        tangent[:n_native, :n_native] = native_j
        tangent[n_native:, n_native:] = self.shell_stiffness
        return residual, tangent, responses

    def _add_spatial_contact(self, residual, tangent, contact_residual, contact_tangent):
        """Add complete work blocks once; callers own chart conversion."""
        n_native = self.context.count
        n_shell = self.shell_stiffness.shape[0]
        slots = np.asarray((*self.context.slots[0],
                            *(n_native+i for i in range(n_shell))), dtype=int)
        np.add.at(residual, slots, contact_residual)
        rows, columns = np.meshgrid(slots, slots, indexing="ij")
        np.add.at(tangent, (rows, columns), contact_tangent)
        native_scaled = residual[:n_native]/self.context.scale
        metrics = (
            float(np.linalg.norm(native_scaled[self.context.equilibrium])),
            float(np.linalg.norm(native_scaled[self.context.compatibility])),
            float(np.linalg.norm(residual[n_native+self.shell_free])),
        )
        return metrics

    def _assemble(self, mechanical, displacement, parameter, origins):
        residual, tangent, responses = self._assemble_structural(
            mechanical, displacement, parameter, origins)
        contact = self._contact(mechanical, displacement)
        block = contact.tangent.toarray()
        block[:42, :42] = spatial_jacobian(contact.residual[:42], block[:42, :42])
        metrics = self._add_spatial_contact(residual, tangent, contact.residual, block)
        return residual, tangent, metrics, responses, contact

    def _step(self, residual, tangent):
        n_native = self.context.count
        free = np.r_[self.context.free, n_native+self.shell_free]
        step = np.zeros(len(residual))
        step[free] = np.linalg.solve(tangent[np.ix_(free, free)], -residual[free])
        if not np.all(np.isfinite(step)):
            raise ValueError("native/S3 Newton step is nonfinite")
        correction = max(
            float(np.max(np.abs(step[:n_native]/self.context.scale))),
            float(np.max(np.abs(step[n_native:]))/self.context.length),
        )
        return step, correction

    def solve_material_increment(self, transaction, parameter, *, cancellation_token=None):
        """Bounded opt-in material increment on this retained structural owner.

        Uses the same constraint solve, equilibrium scale and iteration limits.
        Total physical-origin chart coordinates use their declared tangent.
        Unresolved contact transitions require caller continuation/event cutback;
        no rejected Newton iterate can advance the transaction's physical state.
        """
        from anysolver.control import cancellation_safe_point
        from .native_surface_transaction import NativeS3MaterialTransaction

        if type(transaction) is not NativeS3MaterialTransaction or transaction.contributor.owner is not self:
            raise ValueError('material transaction does not belong to native/S3 owner')
        n = self.context.count
        increment = np.zeros(n+self.shell_stiffness.shape[0])
        for iteration in range(self.program.max_iterations+1):
            cancellation_safe_point(cancellation_token, 'native material equilibrium')
            proposal = transaction.propose(increment[:n], increment[n:], parameter,
                                           cancellation_token=cancellation_token)
            assembly = proposal.assembly
            step, correction = self._step(assembly.residual, assembly.origin_chart_tangent)
            if max(*assembly.metrics, correction) <= self.equilibrium_tolerance:
                return transaction.commit(proposal, cancellation_token=cancellation_token)
            if iteration == self.program.max_iterations:
                raise RuntimeError('native material Newton iteration limit; physical state unchanged')
            accepted = False
            for cut in range(self.program.max_backtracks+1):
                cancellation_safe_point(cancellation_token, 'native material backtrack')
                candidate_increment = increment+(0.5**cut)*step
                try:
                    candidate = transaction.propose(candidate_increment[:n], candidate_increment[n:], parameter,
                                                      cancellation_token=cancellation_token)
                except ValueError as exc:
                    if str(exc).startswith(('native/S3 material history path requires subdivision',
                            'native material path exceeds admitted rotation chart',
                            'first-touch transverse monotone path unresolved',
                            'first-touch physical ownership unresolved',
                            'first-touch needs resolved open and closed endpoints',
                            'first-touch target area bound unresolved',
                            'first-touch root residual unresolved',
                            'first-touch derivative lost transversality',
                            'first-touch differentiated root mismatch',
                            'first-touch endpoint work geometry mismatch',
                            'retained nodal chart requires cutback', 'retained cell chart requires cutback')):
                        continue
                    raise
                if candidate.assembly.material.contribution.normal_gap_m < -self.gap_tolerance:
                    continue
                if max(candidate.assembly.metrics) < max(assembly.metrics):
                    increment = candidate_increment
                    accepted = True
                    break
            if not accepted:
                raise RuntimeError('native material backtracking/event limit; physical state unchanged')

    @staticmethod
    def _recoverable_trial_error(exc):
        message = str(exc)
        if type(exc) is MemoryError:
            return message.startswith((
                "native line-S3 integration interval budget exhausted",
                "native line-S3 parameter resolution exhausted",
            ))
        return type(exc) is ValueError and message.startswith((
            "native line-S3 curve approaches unadmitted physical rim",
            "native line-S3 has unresolved or degenerate geometry",
            "native line-S3 activation interval is unresolved",
            "native line-S3 activation is ambiguous",
            "retained generalized step requires cutback",
        ))

    def _swept_admissible(self, start, u_start, increment, end, u_end,
                          start_gap, end_gap, start_rim, end_rim):
        if min(start_gap, end_gap) < -self.gap_tolerance:
            return False
        first = self.contact.shell.current_positions(u_start)
        last = self.contact.shell.current_positions(u_end)
        a0, b0 = first[1]-first[0], first[2]-first[0]
        a1, b1 = last[1]-last[0], last[2]-last[0]
        c0, c2 = np.cross(a0, b0), np.cross(a1, b1)
        middle = np.cross(0.5*(a0+a1), 0.5*(b0+b1))
        c1 = 2.0*middle-0.5*(c0+c2)
        normal0 = c0/np.linalg.norm(c0)
        area_lower = min(float(normal0@item) for item in (c0, c1, c2))
        if area_lower <= self.contact.contact.geometry_tolerance**2:
            return False
        cross_speed = (
            np.linalg.norm(a1-a0)*max(np.linalg.norm(b0), np.linalg.norm(b1))
            +np.linalg.norm(b1-b0)*max(np.linalg.norm(a0), np.linalg.norm(a1))
        )
        normal_speed = cross_speed/area_lower
        nodes = self.context.nodes[0]
        before = start.positions[nodes]+start.position_low[nodes]
        after = end.positions[nodes]+end.position_low[nodes]
        lift = max(np.linalg.norm(self.contact.contact.beam_reference.half_cell_lift(c, 0.5))
                   for c in (0, 1))
        angular = max(np.linalg.norm(increment[self.context.nodal_count+3*c:
                                               self.context.nodal_count+3*c+3])
                      for c in (0, 1))
        node_speed = float(np.max(np.linalg.norm(after-before, axis=1)))
        beam_speed = node_speed+angular*lift
        bezier_speed = node_speed+2.0*angular*lift
        shell_speed = float(np.linalg.norm(last[0]-first[0]))
        radius = max(float(np.linalg.norm(point-base))
                     for points, base in ((before, first[0]), (after, last[0]))
                     for point in points)+lift
        lipschitz = beam_speed+shell_speed+normal_speed*radius
        rim_speed = 0.0
        for index in range(3):
            j = (index+1) % 3
            edge_first = first[j]-first[index]
            edge_last = last[j]-last[index]
            edge_change = edge_last-edge_first
            denominator = float(edge_change@edge_change)
            station = (0.0 if denominator == 0.0 else float(np.clip(
                -float(edge_first@edge_change)/denominator, 0.0, 1.0,
            )))
            edge_lower = float(np.linalg.norm(edge_first+station*edge_change))
            if edge_lower <= self.contact.contact.geometry_tolerance:
                return False
            inward_speed = normal_speed+float(np.linalg.norm(edge_change))/edge_lower
            vertex_speed = float(np.linalg.norm(last[index]-first[index]))
            vertex_radius = max(float(np.linalg.norm(point-base))
                                for points, base in ((before, first[index]),
                                                     (after, last[index]))
                                for point in points)+2.0*lift
            rim_speed = max(rim_speed,
                            bezier_speed+vertex_speed+inward_speed*vertex_radius)
        roundoff = 256.0*np.finfo(float).eps*max(
            1.0, float(np.max(np.abs(before))), float(np.max(np.abs(after))),
            float(np.max(np.abs(first))), float(np.max(np.abs(last))),
        )
        rim_required = (self.contact.contact.radius
                        +self.contact.contact.rim_clearance)
        if min(start_rim, end_rim)-roundoff < rim_required:
            return False
        stack = [(0.0, 1.0, start_gap, end_gap,
                  start_rim-rim_required, end_rim-rim_required)]
        visited = 0
        while stack:
            left, right, lower_left, lower_right, rim_left, rim_right = stack.pop()
            visited += 1
            if visited > self.maximum_swept_intervals:
                return False
            gap_certified = (min(lower_left, lower_right)
                             -0.5*(right-left)*lipschitz-roundoff
                             >= -self.gap_tolerance)
            rim_certified = (min(rim_left, rim_right)
                             -0.5*(right-left)*rim_speed-roundoff >= 0.0)
            if gap_certified and rim_certified:
                continue
            t = 0.5*(left+right)
            try:
                state = self.context.advance(start, t*increment[:self.context.count])
                u = u_start+t*(u_end-u_start)
                middle_contact = self._contact(state, u).contact
            except (ValueError, MemoryError) as exc:
                if self._recoverable_trial_error(exc):
                    return False
                raise
            gap = middle_contact.minimum_gap_m
            rim = middle_contact.minimum_rim_clearance_m-rim_required
            if gap < -self.gap_tolerance:
                return False
            stack.extend(((left, t, lower_left, gap, rim_left, rim),
                          (t, right, gap, lower_right, rim, rim_right)))
        return True

    def solve(self, *, checkpoint: bytes | None = None,
              expected_sha256: str | None = None,
              stop_after: int | None = None) -> NativeRetainedS3Run:
        end = len(self.program.targets) if stop_after is None else stop_after
        if type(end) is not int or not 0 <= end <= len(self.program.targets):
            raise ValueError("native/S3 bounded stop target")
        if checkpoint is None:
            if expected_sha256 is not None:
                raise ValueError("native/S3 hash requires checkpoint")
            accepted, records = self.initial, ()
            capsule = self._checkpoint(records)
        else:
            accepted, records = self._restore(checkpoint, expected_sha256)
            capsule = checkpoint
        if accepted.completed_targets > end:
            raise ValueError("native/S3 accepted target cannot rewind")
        try:
            for index in range(accepted.completed_targets, end):
                parameter = self.program.targets[index]
                trial = accepted.mechanical
                u = accepted.shell_displacement.copy()
                origins = accepted.native_histories
                for iteration in range(self.program.max_iterations+1):
                    r, j, metrics, responses, contact = self._assemble(
                        trial, u, parameter, origins,
                    )
                    step, correction = self._step(r, j)
                    if max(*metrics, correction) <= self.equilibrium_tolerance:
                        if contact.contact.minimum_gap_m < -self.gap_tolerance:
                            raise RuntimeError("native/S3 endpoint gap tolerance not met")
                        previous = (sha(records[-1]) if records else sha(dict(
                            schema=CHECKPOINT_SCHEMA, identity=self.identity,
                        )))
                        proposed, record = self._record(
                            index+1, trial, u, origins, previous,
                        )
                        next_records = (*records, record)
                        staged = self._checkpoint(next_records)
                        accepted, records, capsule = proposed, next_records, staged
                        break
                    if iteration == self.program.max_iterations:
                        raise RuntimeError("native/S3 Newton iteration limit")
                    angular = [step[6*i+3:6*i+6]
                               for i in range(len(self.context.node_ids))]
                    angular.extend(step[self.context.nodal_count+3*c:
                                        self.context.nodal_count+3*c+3]
                                   for c in (0, 1))
                    fraction = min(1.0, 0.45*np.pi/max(
                        max(float(np.linalg.norm(value)) for value in angular),
                        np.finfo(float).tiny,
                    ))
                    rejected = dict(geometry=0, gap=0, swept=0, merit=0)
                    last_rejection = ""
                    for cut in range(self.program.max_backtracks+1):
                        increment = step*(fraction*0.5**cut)
                        candidate = self.context.advance(
                            trial, increment[:self.context.count],
                        )
                        candidate_u = u+increment[self.context.count:]
                        try:
                            candidate_contact = self._contact(candidate, candidate_u)
                        except (ValueError, MemoryError) as exc:
                            if self._recoverable_trial_error(exc):
                                rejected["geometry"] += 1
                                last_rejection = str(exc)[:160]
                                continue
                            raise
                        if candidate_contact.contact.minimum_gap_m < -self.gap_tolerance:
                            rejected["gap"] += 1
                            last_rejection = ("gap "
                                              f"{candidate_contact.contact.minimum_gap_m} m")
                            continue
                        if not self._swept_admissible(
                                trial, u, increment, candidate, candidate_u,
                                contact.contact.minimum_gap_m,
                                candidate_contact.contact.minimum_gap_m,
                                contact.contact.minimum_rim_clearance_m,
                                candidate_contact.contact.minimum_rim_clearance_m):
                            rejected["swept"] += 1
                            last_rejection = "swept path not certified"
                            continue
                        _, _, changed, _, _ = self._assemble(
                            candidate, candidate_u, parameter, origins,
                        )
                        if max(changed) < max(metrics):
                            trial, u = candidate, candidate_u
                            break
                        rejected["merit"] += 1
                        last_rejection = f"merit {max(changed)} >= {max(metrics)}"
                    else:
                        raise RuntimeError(
                            "native/S3 line-search/gap limit: "
                            f"iteration={iteration}, rejected={rejected}, "
                            f"last={last_rejection}"
                        )
            status = "completed" if end == len(self.program.targets) else "paused"
            return NativeRetainedS3Run(status, accepted, None, capsule)
        except Exception as exc:
            return NativeRetainedS3Run(
                "failed", accepted, type(exc).__name__+": "+str(exc), capsule,
            )
