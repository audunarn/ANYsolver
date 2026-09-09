"""Actual Q4/S3-V2D plus retained-beam trial assembly; no coupled commit API.

The shell side is an owned virgin elastic model. The beam predecessor must be
issued by its real retained Context. This seam evaluates genuine mechanics,
but cannot issue accepted coupled history, restart or spectral authority.

Shell residual rows are spatial forces/moments, while its columns are additive
total rotation coordinates. Consequently the joint contribution is r, J P,
NOT P.T r, P.T J P + dP.T r. The latter belongs to chart-covector equations.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from threading import Lock
import numpy as np

from .fe_core import FEModel
from .e4_pl_element import QualifiedE4PLShellElement
from .e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement
from .corotational import corotational_element_response
from .control import cancellation_safe_point
from ._ge_beam3_pose_joint import RigidPoseJoint, _array
from ._ge_beam3_retained_generalized_state import Context
from ._ge_beam3_retained_nodal_loading import Context as NodalContext
from ._ge_beam3_p5_seeded.core import canonical
from ._native_reference_modal import _owned


@dataclass(frozen=True)
class ShellBeamTrial:
    definition_sha256: str
    beam_predecessor_sha256: str
    input_sha256: str
    residual: np.ndarray
    tangent: np.ndarray
    constraints: np.ndarray
    joint_residual: np.ndarray
    joint_tangent: np.ndarray
    shell_candidate: bytes
    beam_histories: bytes
    production_qualified: bool = field(default=False, init=False)
    coupled_state_committed: bool = field(default=False, init=False)


class ShellBeamTrialAssembly:
    """One real elastic shell and one owned retained beam submodel.

Separate namespaces avoid accidental node/DOF aliasing. The global order is
all shell DOFs, all retained beam DOFs, then six joint multipliers. Only the
explicit attachment node is coupled; no legacy MPC or beam batch is invoked.
This is a trial/diagnostic seam, not a supported coupled analysis driver.
"""

    def __init__(self, beam_context, *, topology, coordinates, reference_normal,
                 thickness, elastic_modulus, poisson_ratio, shell_node, beam_node):
        if type(beam_context) not in (Context, NodalContext):
            raise ValueError('exact retained generalized beam owner required')
        beam_context.guard()
        if topology not in ('Q4', 'S3-V2D'):
            raise ValueError('explicit unchanged Q4 or S3-V2D formulation required')
        count = 4 if topology == 'Q4' else 3
        self.coordinates = _array(coordinates, (count, 3))
        self.normal = _array(reference_normal, (3,))
        if abs(np.linalg.norm(self.normal)-1.) > 1e-11:
            raise ValueError('physical unit reference normal required')
        if (any(type(x) is not float or not np.isfinite(x) for x in
                (thickness, elastic_modulus, poisson_ratio)) or thickness <= 0.
                or elastic_modulus <= 0. or not -1. < poisson_ratio < .5):
            raise ValueError('finite positive elastic shell definition required')
        if (type(shell_node) is not int or not 0 <= shell_node < count
                or type(beam_node) is not int or beam_node not in beam_context.index):
            raise ValueError('explicit shell row and owned beam node required')
        self.beam = beam_context
        self.beam_identity = beam_context.identity
        self.topology = topology
        self.shell_node, self.beam_node = shell_node, beam_node
        self.shell_count = 6*count
        self.count = self.shell_count+beam_context.count+6
        self.model = FEModel('owned-elastic-shell-joint-trial')
        self.model.add_material('joint-shell', elastic_modulus, poisson_ratio)
        for i, x in enumerate(self.coordinates, 1):
            self.model.add_node(i, *x)
        cls = QualifiedE4PLShellElement if topology == 'Q4' else NativeParityE4PLS3V2DShellElement
        self.element = cls(1, tuple(range(1, count+1)), 'joint-shell',
            thickness=thickness, reference_normal=self.normal.copy())
        self.model.add_element(1, self.element)
        self.layers = 3
        material = self.model.get_material('joint-shell')
        self.shell_origin = (self.element.init_nonlinear_state(self.layers) if topology == 'Q4'
            else self.element.init_model_bound_nonlinear_state(self.model.mesh, material, self.layers))
        self.origin_bytes = canonical(self.shell_origin)
        # A physical shell triad, fixed by its authoritative normal and edge.
        tangent = self.coordinates[1]-self.coordinates[0]
        tangent = tangent-self.normal*(tangent@self.normal)
        if np.linalg.norm(tangent) <= 1e-14:
            raise ValueError('shell reference edge parallel to director')
        tangent /= np.linalg.norm(tangent)
        self.frame = _owned(np.column_stack((tangent, np.cross(self.normal, tangent), self.normal)))
        bi = self.beam.index[beam_node]
        self.joint = RigidPoseJoint(np.array([self.coordinates[shell_node], self.beam.reference_positions[bi]]),
            np.array([self.frame, self.beam.reference_frames[bi]]))
        self.slots = tuple(range(6*shell_node, 6*shell_node+6)) + tuple(
            self.shell_count+int(d) for d in self.beam.model.mesh.dof_manager.get_node_dofs(beam_node)) + tuple(
            range(self.count-6, self.count))
        self.identity = sha256(canonical(self._descriptor())).hexdigest()
        self._lock = Lock()
        self.guard()

    def _descriptor(self):
        material = self.model.get_material('joint-shell')
        e = self.element
        return dict(policy='GE_BEAM3_REAL_SHELL_RETAINED_BEAM_TRIAL_ONLY_V1',
            topology=self.topology, beam=self.beam.identity,
            nodes=[(i, self.model.mesh.nodes[i].coords()) for i in sorted(self.model.mesh.nodes)],
            shell_nodes=e.node_ids, shell_formulation=e.formulation_id,
            shell_implementation=e.implementation_id, thickness=e.thickness,
            normal=e.reference_normal, material_direction=e.material_direction,
            material_angle=e.material_angle_deg, section=e.shell_section,
            offset=getattr(e, 'reference_surface_offset', None),
            elastic_modulus=material.elastic_modulus, poisson_ratio=material.poisson_ratio,
            yield_stress=material.yield_stress, curve=material.hardening_curve,
            shell_node=self.shell_node, beam_node=self.beam_node,
            layers=self.layers, joint=self.joint.identity, slots=self.slots,
            production_qualified=False)

    def guard(self):
        self.beam.guard(); self.joint.guard()
        cls = QualifiedE4PLShellElement if self.topology == 'Q4' else NativeParityE4PLS3V2DShellElement
        if (type(self.element) is not cls or self.model.mesh.elements != {1: self.element}
                or self.beam.identity != self.beam_identity
                or canonical(self.shell_origin) != self.origin_bytes
                or sha256(canonical(self._descriptor())).hexdigest() != self.identity):
            raise ValueError('coupled trial definition or shell origin changed')
        count = len(self.coordinates)
        bi = self.beam.index[self.beam_node]
        if (self.shell_count != 6*count or self.count != self.shell_count+self.beam.count+6
                or not np.array_equal(self.joint.reference_positions,
                    np.array([self.coordinates[self.shell_node], self.beam.reference_positions[bi]]))
                or not np.array_equal(self.joint.reference_frames,
                    np.array([self.frame, self.beam.reference_frames[bi]]))):
            raise ValueError('coupled compiled pose or extent changed')

    def evaluate(self, accepted_beam, beam_trial, shell_displacements, multipliers,
                 *, parameter, cancellation_token=None):
        cancellation_safe_point(cancellation_token, 'shell-joint.start')
        if not self._lock.acquire(blocking=False):
            raise RuntimeError('concurrent coupled trial use forbidden')
        try:
            self.guard()
            predecessor = self.beam._require_issued(accepted_beam)
            if type(parameter) is not float or not np.isfinite(parameter) or abs(parameter) > 16.:
                raise ValueError('bounded explicit trial load parameter required')
            mechanical = self.beam.make(beam_trial.descriptor())
            u = _array(shell_displacements, (self.shell_count,))
            force = _array(multipliers, (6,))
            before = canonical(accepted_beam)
            br, bj, _, responses, _ = self.beam.assemble(mechanical, parameter, accepted_beam.histories)
            cancellation_safe_point(cancellation_token, 'shell-joint.beam-complete')
            sr, sj, candidate = corotational_element_response(self.model, 1, self.element, u,
                True, committed_state=self.shell_origin, num_layers=self.layers, tangent_mode='consistent')
            bi = self.beam.index[self.beam_node]
            shell = u.reshape(-1, 6)[self.shell_node]
            ports = self.joint.evaluate_ports(
                np.array([self.coordinates[self.shell_node]+shell[:3], mechanical.positions[bi]]),
                np.array([self.frame, mechanical.nodal_frames[bi]]), force,
                rotation_coordinates=np.array([shell[3:], np.zeros(3)]), charted_ports=(True, False),
                position_low=np.array([np.zeros(3), mechanical.position_low[bi]]),
                cancellation_token=cancellation_token)
            # EICR returns spatial wrench rows, not additive-chart covectors.
            jr = ports.pose.residual
            jj = ports.pose.spatial_jacobian@ports.coordinate_map
            r = np.r_[sr, br, np.zeros(6)]
            j = np.zeros((self.count, self.count))
            j[:self.shell_count, :self.shell_count] = sj
            j[self.shell_count:-6, self.shell_count:-6] = bj
            r[list(self.slots)] += jr
            j[np.ix_(self.slots, self.slots)] += jj
            if not np.isfinite(r).all() or not np.isfinite(j).all():
                raise ValueError('nonfinite coupled residual or tangent')
            self.guard(); self.beam._require_issued(accepted_beam)
            if canonical(accepted_beam) != before:
                raise ValueError('beam predecessor mutated during coupled trial')
            fingerprint = sha256(canonical(dict(mechanical=mechanical, shell_u=u,
                multipliers=force, parameter=parameter))).hexdigest()
            result = ShellBeamTrial(self.identity, sha256(predecessor).hexdigest(), fingerprint,
                _owned(r), _owned(j), ports.pose.constraints, _owned(jr), _owned(jj),
                canonical(candidate), canonical(tuple(a.history for a in responses)))
            cancellation_safe_point(cancellation_token, 'shell-joint.complete')
            return result
        finally:
            self._lock.release()
