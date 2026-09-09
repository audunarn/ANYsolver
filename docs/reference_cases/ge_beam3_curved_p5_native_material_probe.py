"""Private P5 element through real native scalar dispatch and state transactions.

This is not registered or packaged as a selectable element. The mandatory
session validates P5 fallback dictionaries before invoking the native commit;
the generic store alone does not know this research history schema.
"""

from copy import deepcopy
from dataclasses import asdict, is_dataclass
import hashlib
import json

import numpy as np

from anysolver.elements import Element
from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from anysolver.nonlinear_element_evaluation import evaluate_nonlinear_element
from anysolver.nonlinear_state import NonlinearStateStore, create_model_native_rotation_store, native_trial_full_coordinates
from docs.reference_cases.ge_beam3_curved_p5_compensated_mixed import CompensatedMixedBeamProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames
from docs.reference_cases.ge_beam3_curved_p5_native_chart_probe import pullback
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import LocalForceAccuracy
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe, SectionHistory, _history


SCHEMA='GE_BEAM3_P5_PRIVATE_NATIVE_STATION_STATE_V1'
FORMULATION='CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_NATIVE_V1'


def canonical(value):
    def encode(item):
        if is_dataclass(item): return asdict(item)
        if isinstance(item, np.ndarray): return item.tolist()
        raise TypeError('unsupported private state value')
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False,
                       default=encode)+'\n').encode('ascii')


def sha(value): return hashlib.sha256(canonical(value)).hexdigest()


def seal(state):
    body={key: value for key, value in state.items() if key!='state_sha256'}
    return {**deepcopy(body), 'state_sha256': sha(body)}


class NativeMaterialError(ValueError):
    """Private P5 state/model/route mismatch; no accepted state changed."""


class PrivateP5NativeElement(Element):
    formulation_native_total_lagrangian=True
    formulation_id=FORMULATION
    num_nodes=3
    dofs_per_node=6

    def __init__(self, element_id, node_ids, reference, section, *, order=8):
        if type(element_id) is not int or type(node_ids) is not tuple or len(node_ids)!=3:
            raise NativeMaterialError('exact element ID and three-node tuple required')
        if any(type(i) is not int for i in node_ids) or len(set(node_ids))!=3:
            raise NativeMaterialError('distinct integer nodes required')
        if type(section) is not DirectedHardeningSectionProbe:
            raise NativeMaterialError('only declared directed-hardening section is implemented')
        super().__init__(element_id, node_ids, material_name=f'private-p5-section-{element_id}')
        self.reference=CurvedBeam3ReferenceGeometry(reference.coordinates, reference.nodal_triads)
        self.section=deepcopy(section);self.order=order
        # Validate quadrature/section now, without solving or generating history.
        CompensatedMixedBeamProbe(self.reference, self.section, order=order, position_low=np.zeros((3, 3)))
        self.length=max(np.linalg.norm(a-b) for a in self.reference.coordinates for b in self.reference.coordinates)
        self.model_sha256=sha(self._identity())
        self._native_session=None

    def _identity(self):
        return dict(formulation=FORMULATION, schema=SCHEMA, element=self.element_id, nodes=self.node_ids,
            coordinates=self.reference.coordinates, frames=self.reference.nodal_triads,
            elastic=self.section._elastic, direction=self.section._direction,
            yield_force=self.section._yield, hardening=self.section._hardening, order=self.order)

    def get_node_coordinates(self, mesh):
        return np.array([mesh.get_node(i).coords() for i in self.node_ids], dtype=float)

    def _check_model(self, mesh):
        if type(self) is not PrivateP5NativeElement or sha(self._identity())!=self.model_sha256:
            raise NativeMaterialError('private model identity changed')
        expected_length=max(np.linalg.norm(a-b) for a in self.reference.coordinates for b in self.reference.coordinates)
        if self.length!=expected_length: raise NativeMaterialError('local accuracy length changed')
        if not np.array_equal(self.get_node_coordinates(mesh), self.reference.coordinates):
            raise NativeMaterialError('mesh reference geometry disagrees with frozen element')

    def native_reference_directors(self, mesh):
        self._check_model(mesh)
        return self.reference.nodal_triads[:, :, 2].copy()

    def _solve(self, positions, operators, origins):
        model=CompensatedMixedBeamProbe(self.reference, self.section, order=self.order,
            position_low=np.zeros((3, 3)), origins=origins)
        return model.solve(positions, operators@self.reference.nodal_triads,
            force_accuracy=LocalForceAccuracy(1e-12, float(self.length)))

    def _state(self, epoch, total, positions, operators, origins, response):
        return seal(dict(schema=SCHEMA, model_sha256=self.model_sha256, epoch=epoch,
            committed_total_u=np.array(total, copy=True), committed_positions=np.array(positions, copy=True),
            committed_nodal_rotation_matrices=np.array(operators, copy=True),
            origins=tuple(origins), histories=tuple(s.response.history for s in response.stations), response=response))

    def init_model_bound_nonlinear_state(self, mesh, material=None, num_layers=1):
        self._arguments(mesh, material, num_layers)
        operators=np.tile(np.eye(3), (3, 1, 1));origins=tuple(SectionHistory() for _ in range(2*self.order))
        response=self._solve(self.reference.coordinates, operators, origins)
        return self._state(0, np.zeros(18), self.reference.coordinates, operators, origins, response)

    def _arguments(self, mesh, material, num_layers):
        self._check_model(mesh)
        if (material is not None and material is not self.section) or type(num_layers) is not int or num_layers!=1:
            raise NativeMaterialError('exact owned section or None and one private state layout required')

    def validate_model_bound_nonlinear_state(self, mesh, material, state, num_layers,
                                            *, expected_committed_total_u=None):
        self._arguments(mesh, material, num_layers)
        keys={'schema', 'model_sha256', 'epoch', 'committed_total_u', 'committed_positions',
              'committed_nodal_rotation_matrices', 'origins', 'histories', 'response', 'state_sha256'}
        if type(state) is not dict or set(state)!=keys:
            raise NativeMaterialError('exact native station state schema required')
        body={k: v for k, v in state.items() if k!='state_sha256'}
        if state['schema']!=SCHEMA or state['model_sha256']!=self.model_sha256 or state['state_sha256']!=sha(body):
            raise NativeMaterialError('native station identity/hash mismatch')
        if type(state['epoch']) is not int or not 0<=state['epoch']<2**31:
            raise NativeMaterialError('bounded exact station epoch required')
        u=_array(state['committed_total_u'], (18,), 'committed displacement')
        positions=_array(state['committed_positions'], (3, 3), 'committed coordinates')
        operators=_frames(state['committed_nodal_rotation_matrices'], 3, 'committed operators')
        if expected_committed_total_u is not None and not np.array_equal(u, expected_committed_total_u):
            raise NativeMaterialError('state/global displacement mismatch')
        if not np.allclose(positions, self.reference.coordinates+u.reshape(3, 6)[:, :3],
                           rtol=0., atol=1e-12*max(1., self.length)):
            raise NativeMaterialError('state coordinates/displacement mismatch')
        for name in ('origins', 'histories'):
            if type(state[name]) is not tuple or len(state[name])!=2*self.order:
                raise NativeMaterialError('exact station ordering/count required')
            for value in state[name]: _history(value)
        if state['epoch']==0:
            if (np.any(u) or not np.array_equal(positions, self.reference.coordinates)
                or not np.array_equal(operators, np.tile(np.eye(3), (3, 1, 1)))
                or any(value!=SectionHistory() for value in state['origins'])):
                raise NativeMaterialError('initial state must be declared stress-free origin')
        # Replay from the PREVIOUS accepted origins, never the new plastic history.
        replay=self._solve(positions, operators, state['origins'])
        if sha(replay)!=sha(state['response']):
            raise NativeMaterialError('accepted-origin local replay mismatch')
        if tuple(s.response.history for s in replay.stations)!=state['histories']:
            raise NativeMaterialError('station history/recovery mismatch')
        return deepcopy(state)

    def compute_nonlinear_response(self, mesh, material, displacement, state=None, num_layers=1,
                                   tangent=True, *, native_rotation_trial=None):
        self._arguments(mesh, material, num_layers)
        view=native_rotation_trial
        if view is None or view.element_id!=self.element_id or tuple(view.node_ids)!=self.node_ids:
            raise NativeMaterialError('matching solver-owned native view required')
        self._require_live_view(view)
        committed=self.validate_model_bound_nonlinear_state(mesh, material, state, num_layers)
        if committed['epoch']!=view.generation:
            raise NativeMaterialError('material/native generation mismatch')
        if (not np.array_equal(committed['committed_positions'], view.committed_coordinates)
            or not np.array_equal(committed['committed_nodal_rotation_matrices'], view.committed_rotation_matrices)
            or not np.array_equal(committed['committed_total_u'].reshape(3, 6)[:, 3:], view.committed_rotation_coordinates)):
            raise NativeMaterialError('committed native/material pose mismatch')
        total=_array(displacement, (18,), 'element total displacement')
        if (not np.array_equal(total.reshape(3, 6)[:, 3:], view.trial_rotation_coordinates)
            or not np.allclose(self.reference.coordinates+total.reshape(3, 6)[:, :3], view.trial_coordinates,
                               rtol=0., atol=1e-12*max(1., self.length))):
            raise NativeMaterialError('element displacement/native trial mismatch')
        response=self._solve(view.trial_coordinates, view.trial_rotation_matrices, committed['histories'])
        force, hessian, _=pullback(response.residual, response.tangent, view.rotation_coordinate_increment)
        self._require_live_view(view)
        candidate=self._state(committed['epoch']+1, total, view.trial_coordinates,
                              view.trial_rotation_matrices, committed['histories'], response)
        return force.copy(), hessian.copy() if tangent else None, candidate

    def _require_live_view(self, view):
        session=self._native_session
        if session is None: raise NativeMaterialError('private element has no owning native session')
        session._check_model()
        token=session.store.active_trial_token()
        fresh=session.store.native_element_rotation_view(token, self.element_id, self.node_ids,
                                                         self.reference.nodal_triads[:, :, 2])
        if sha(view)!=sha(fresh): raise NativeMaterialError('detached or foreign native view')

    def _unsupported(self, *args, **kwargs):
        raise NativeMaterialError('private native station adapter: workflow not authorized')

    compute_stiffness_matrix=_unsupported
    compute_mass_matrix=_unsupported
    compute_geometric_stiffness_matrix=_unsupported
    compute_internal_forces=_unsupported
    compute_stresses=_unsupported
    to_dict=_unsupported


class NativeMaterialSession:
    """Mandatory private bridge; real store/dispatch, no substitute material commit."""

    def __init__(self, model):
        self.model=model
        self.elements=dict(model.mesh.elements)
        if not self.elements or any(type(e) is not PrivateP5NativeElement for e in self.elements.values()):
            raise NativeMaterialError('only explicit private P5 elements admitted')
        if any(e._native_session is not None for e in self.elements.values()):
            raise NativeMaterialError('private elements already have an owning session')
        for element in self.elements.values():
            if element.material_name in model.materials:
                raise NativeMaterialError('private section registration must be exclusive')
        self._full=np.zeros(model.mesh.dof_manager.total_dofs)
        states={i: e.init_model_bound_nonlinear_state(model.mesh) for i, e in self.elements.items()}
        self.store=NonlinearStateStore.from_shell_layouts((), states)
        rotations=create_model_native_rotation_store(model, states, self._full)
        self.store.attach_native_rotation_store(rotations)
        self._layout_sha256=sha(self._layout())
        for element in self.elements.values(): model.materials[element.material_name]=element.section
        for element in self.elements.values(): element._native_session=self
        self._pending=None

    def _layout(self):
        return dict(total_dofs=self.model.mesh.dof_manager.total_dofs,
            nodes=[dict(id=i, coordinates=node.coords(), dofs=list(node.dofs))
                   for i, node in sorted(self.model.mesh.nodes.items())])

    def _check_model(self):
        if sha(self._layout())!=self._layout_sha256:
            raise NativeMaterialError('native node/DOF ownership changed')
        if set(self.model.mesh.elements)!=set(self.elements) or any(self.model.mesh.elements[k] is not e for k, e in self.elements.items()):
            raise NativeMaterialError('native session element graph changed')
        for element in self.elements.values():
            element._check_model(self.model.mesh)
            if element._native_session is not self:
                raise NativeMaterialError('native session ownership changed')
            if self.model.get_material(element.material_name) is not element.section:
                raise NativeMaterialError('private section registration changed')

    def begin(self, full):
        self._check_model()
        full=_array(full, self._full.shape, 'full candidate displacement')
        nodes=self.model.mesh.nodes
        coords=np.array([nodes[i].coords()+full[np.array(nodes[i].dofs[:3])] for i in sorted(nodes)])
        token=self.store.replace_trial(full_displacement=full, full_coordinates=coords)
        self._pending=(token, full.copy(), coords.copy(), {})
        return token

    def _active(self, token):
        self._check_model()
        if self._pending is None or token is not self._pending[0] or self.store.active_trial_token() is not token:
            raise NativeMaterialError('stale or foreign native material candidate')
        return self._pending

    def evaluate(self, token, element_id, *, tangent=True):
        _, full, _, staged=self._active(token)
        element=self.elements[element_id];ids=np.array(element.get_dof_mapping(self.model.mesh))
        force, matrix, state=evaluate_nonlinear_element(element, self.model.mesh, None, full[ids],
            self.store[element_id], 1, tangent, committed_states=self.store, state_token=token, element_id=element_id)
        self._active(token)
        self.store.set_trial_state(token, element_id, state)
        staged[element_id]=deepcopy(state)
        return force, matrix, deepcopy(state)

    def assemble(self, full, *, tangent=True):
        """Use the actual reference nonlinear assembler, not a new scatter implementation."""
        from anysolver.nonlinear_static import _assemble_nonlinear_system
        self._check_model()
        full=_array(full, self._full.shape, 'full assembly displacement')
        coords=native_trial_full_coordinates(self.store, self.model, full)
        try:
            force, matrix, payload=_assemble_nonlinear_system(self.model, full, self.store, 1,
                tangent=tangent, require_full_coordinates=True)
            token=self.store.active_trial_token()
            staged={key: deepcopy(value) for key, value in payload.items()}
            self._pending=(token, full.copy(), coords.copy(), staged)
            self._active(token)
            return token, force, matrix
        except BaseException:
            if self.store.has_active_trial: self.store.discard_trial(self.store.active_trial_token())
            self._pending=None
            raise

    def commit(self, token):
        _, full, coords, staged=self._active(token)
        if set(staged)!=set(self.elements): raise NativeMaterialError('every element must produce trial state')
        actual=self.store.materialize(trial_token=token)
        for key, element in self.elements.items():
            candidate=staged[key];old=self.store[key]
            if sha(actual[key])!=sha(candidate) or candidate['origins']!=old['histories'] or candidate['epoch']!=old['epoch']+1:
                raise NativeMaterialError('candidate changed or origin linkage mismatch')
            ids=np.array(element.get_dof_mapping(self.model.mesh))
            element.validate_model_bound_nonlinear_state(self.model.mesh, None, candidate, 1,
                                                         expected_committed_total_u=full[ids])
            view=self.store.native_element_rotation_view(token, key, element.node_ids, element.native_reference_directors(self.model.mesh))
            if (not np.array_equal(candidate['committed_positions'], view.trial_coordinates)
                or not np.array_equal(candidate['committed_nodal_rotation_matrices'], view.trial_rotation_matrices)):
                raise NativeMaterialError('candidate pose disagrees with active native trial')
        self._active(token)
        accepted_full=full.copy()
        generation=self.store.commit(token, accepted_full_displacement=full, accepted_full_coordinates=coords)
        self._full=accepted_full;self._pending=None
        return generation

    def discard(self, token):
        # Cleanup remains possible after model mutation; never evaluate mechanics here.
        if self._pending is None or token is not self._pending[0]: raise NativeMaterialError('stale discard')
        self.store.discard_trial(token);self._pending=None

    def replay(self):
        self._check_model()
        if self.store.has_active_trial: raise NativeMaterialError('replay requires no pending candidate')
        return {key: element.validate_model_bound_nonlinear_state(self.model.mesh, None, self.store[key], 1,
            expected_committed_total_u=self._full[np.array(element.get_dof_mapping(self.model.mesh))])
            for key, element in self.elements.items()}
