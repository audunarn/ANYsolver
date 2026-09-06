"""Private P5 successor using native driver-owned validation, not a session."""

from copy import deepcopy

import numpy as np

from anysolver.elements import Element
from anysolver._native_material_protocol import PROTOCOL, NativeMaterialContext, NativeMaterialValidator
from docs.reference_cases.ge_beam3_curved_p5_native_material_probe import (
    PrivateP5NativeElement, NativeMaterialError, sha, seal,
)
from docs.reference_cases.ge_beam3_curved_p5_native_chart_probe import pullback
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array


SCHEMA='GE_BEAM3_P5_PRIVATE_DRIVER_STATION_STATE_V1'
FORMULATION='CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_NATIVE_DRIVER_V1'


class DriverP5Element(Element):
    """Scalar native-driver test candidate; public registration remains absent."""

    formulation_native_total_lagrangian=True
    native_material_state_protocol=PROTOCOL
    formulation_id=FORMULATION
    num_nodes=3
    dofs_per_node=6

    def __init__(self, element_id, nodes, reference, section, *, order=8):
        self.core=PrivateP5NativeElement(element_id, nodes, reference, section, order=order)
        super().__init__(element_id, nodes, self.core.material_name)
        self._layout=None
        self.driver_sha256=sha(dict(schema=SCHEMA, formulation=FORMULATION,
                                   element=element_id, nodes=nodes, core=self.core.model_sha256))

    def _check(self, mesh):
        if type(self) is not DriverP5Element:
            raise NativeMaterialError('exact private driver candidate required')
        if mesh.elements.get(self.element_id) is not self or any(type(e) is not DriverP5Element for e in mesh.elements.values()):
            raise NativeMaterialError('private driver candidate is standalone-only; no unqualified joints or shells')
        self.core._check_model(mesh)
        expected=sha(dict(schema=SCHEMA, formulation=FORMULATION, element=self.element_id,
                          nodes=self.node_ids, core=self.core.model_sha256))
        if expected!=self.driver_sha256 or tuple(self.node_ids)!=self.core.node_ids:
            raise NativeMaterialError('driver identity changed')
        layout=tuple(self.get_dof_mapping(mesh))
        if len(layout)!=18 or len(set(layout))!=18:
            raise NativeMaterialError('driver requires eighteen distinct nodal DOFs')
        if self._layout is None: self._layout=layout
        elif layout!=self._layout: raise NativeMaterialError('driver DOF ownership changed')

    def get_node_coordinates(self, mesh): return self.core.get_node_coordinates(mesh)

    def native_reference_directors(self, mesh):
        self._check(mesh)
        return self.core.native_reference_directors(mesh)

    def _wrap(self, state):
        return seal(dict(driver_schema=SCHEMA, driver_sha256=self.driver_sha256,
            committed_total_u=state['committed_total_u'],
            committed_nodal_rotation_matrices=state['committed_nodal_rotation_matrices'], material_state=state))

    def _validate(self, mesh, state, expected=None):
        self._check(mesh)
        keys={'driver_schema', 'driver_sha256', 'committed_total_u',
              'committed_nodal_rotation_matrices', 'material_state', 'state_sha256'}
        if type(state) is not dict or set(state)!=keys:
            raise NativeMaterialError('exact private driver state required')
        if (state['driver_schema']!=SCHEMA or state['driver_sha256']!=self.driver_sha256
            or seal(state)['state_sha256']!=state['state_sha256']):
            raise NativeMaterialError('driver state identity/hash mismatch')
        inner=self.core.validate_model_bound_nonlinear_state(mesh, None, state['material_state'], 1,
                                                            expected_committed_total_u=expected)
        for key in ('committed_total_u', 'committed_nodal_rotation_matrices'):
            if not np.array_equal(state[key], inner[key]):
                raise NativeMaterialError('driver/native state redundancy mismatch')
        return inner

    def init_model_bound_nonlinear_state(self, mesh, material, num_layers):
        self._check(mesh)
        return self._wrap(self.core.init_model_bound_nonlinear_state(mesh, material, num_layers))

    def validate_model_bound_nonlinear_state(self, mesh, material, state, num_layers,
                                            *, expected_committed_total_u=None):
        self.core._arguments(mesh, material, num_layers)
        self._validate(mesh, state, expected_committed_total_u)
        return deepcopy(state)

    @staticmethod
    def _pose(inner, view, *, committed):
        positions=view.committed_coordinates if committed else view.trial_coordinates
        matrices=view.committed_rotation_matrices if committed else view.trial_rotation_matrices
        rotations=view.committed_rotation_coordinates if committed else view.trial_rotation_coordinates
        if (not np.array_equal(inner['committed_positions'], positions)
            or not np.array_equal(inner['committed_nodal_rotation_matrices'], matrices)
            or not np.array_equal(inner['committed_total_u'].reshape(3, 6)[:, 3:], rotations)):
            raise NativeMaterialError('driver material/native pose mismatch')

    def create_native_material_validator(self, mesh):
        self._check(mesh)
        def validate(state, *, previous_state, native_view, displacement, phase):
            inner=self._validate(mesh, state, displacement)
            if phase=='committed':
                if previous_state is not None: raise NativeMaterialError('invalid initial validator phase')
                self._pose(inner, native_view, committed=True)
            elif phase=='trial':
                previous=self._validate(mesh, previous_state)
                self._pose(previous, native_view, committed=True)
                self._pose(inner, native_view, committed=False)
                if inner['epoch']!=previous['epoch']+1 or inner['origins']!=previous['histories']:
                    raise NativeMaterialError('driver accepted-origin linkage mismatch')
            else: raise NativeMaterialError('unknown native validation phase')
        return NativeMaterialValidator(validate)

    def compute_nonlinear_response(self, mesh, material, displacement, state=None, num_layers=1,
                                   tangent=True, *, native_rotation_trial=None, native_material_context=None):
        self.core._arguments(mesh, material, num_layers)
        context=native_material_context;view=native_rotation_trial
        if type(context) is not NativeMaterialContext or context.element_id!=self.element_id:
            raise NativeMaterialError('live driver material context required')
        context.require_view(view)
        previous=self._validate(mesh, state)
        self._pose(previous, view, committed=True)
        total=_array(displacement, (18,), 'driver element displacement')
        if (not np.array_equal(total.reshape(3, 6)[:, 3:], view.trial_rotation_coordinates)
            or not np.allclose(self.core.reference.coordinates+total.reshape(3, 6)[:, :3], view.trial_coordinates,
                               rtol=0., atol=1e-12*max(1., self.core.length))):
            raise NativeMaterialError('driver total displacement/view mismatch')
        response=self.core._solve(view.trial_coordinates, view.trial_rotation_matrices, previous['histories'])
        force, matrix, _=pullback(response.residual, response.tangent, view.rotation_coordinate_increment)
        context.require_view(view)
        inner=self.core._state(previous['epoch']+1, total, view.trial_coordinates,
                               view.trial_rotation_matrices, previous['histories'], response)
        return force.copy(), matrix.copy() if tangent else None, self._wrap(inner)

    def _unsupported(self, *args, **kwargs):
        raise NativeMaterialError('private driver candidate: workflow not yet authorized')

    def compute_stiffness_matrix(self, mesh, material):
        # The actual Newton driver requests a virgin reference K0 to build its
        # constraint reduction. This is the native stationary Hessian, not a
        # legacy/reference-beam surrogate or a current plastic tangent.
        initial=self.init_model_bound_nonlinear_state(mesh, material, 1)
        return initial['material_state']['response'].tangent.copy()

    compute_mass_matrix=_unsupported
    compute_geometric_stiffness_matrix=_unsupported
    compute_internal_forces=_unsupported
    compute_stresses=_unsupported
    to_dict=_unsupported
