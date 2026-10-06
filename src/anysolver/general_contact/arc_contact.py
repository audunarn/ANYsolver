"""Fixed-tool penalty transaction adapter for the existing arc continuation."""
from contextlib import contextmanager
from dataclasses import replace
import numpy as np
from .core import ContactDefinition, ContactSolverSettings, ContactValidationReport
from .triangulated_rigid import TriangulatedRigidContactBody
from .triangulated_rigid_static import TriangulatedRigidManager, validate_triangulated_rigid
from .runtime import _ACTIVE_CONTACT
from . import transient_results_archive as codec

PROFILE = 'S3_FIXED_TRIANGULATED_RIGID_ARC_PENALTY_DEV_V1'
STATE_SCHEMA = 'ANYSOLVER_ARC_CONTACT_STATE_V1'


def validate_arc_contact(model, definition, settings=None):
    if type(definition) is not ContactDefinition or not definition.rigid_bodies or any(
            type(body) is not TriangulatedRigidContactBody for body in definition.rigid_bodies):
        return ContactValidationReport('unsupported', ('arc contact requires fixed triangulated rigid tools',), PROFILE)
    report = validate_triangulated_rigid(model, definition, settings, analysis_control='force')
    return replace(report, profile=PROFILE)


class ArcContactAdapter:
    """The penalty contributor has no pressure or material history to import."""
    def __init__(self, model, definition, settings):
        report = validate_arc_contact(model, definition, settings)
        if not report.valid: raise ValueError('unsupported arc contact: ' + '; '.join(report.issues))
        self.manager = TriangulatedRigidManager(model, definition, settings)
        self.history = []
        self._bound_contract = self.manager.restart_contract()

    def _guard(self):
        if self.manager.restart_contract() != self._bound_contract:
            raise ValueError('arc contact operator mutated')

    def evaluate(self, displacement, *, tangent=True):
        self._guard()
        return self.manager.evaluate(displacement, tangent=tangent)

    def restart_contract(self):
        self._guard()
        return {'profile': PROFILE, 'contributor': self._bound_contract,
                'state_policy': 'stateless_penalty_accepted_pose_history_exact_bits_v1'}

    def admissible(self, start, end):
        self._guard()
        return self.manager._swept_admissible(start, end)

    def prepare(self, displacement, step_index, load_factor):
        self._guard()
        _, _, result = self.manager.evaluate(displacement, tangent=False)
        if not result.gap_tolerance_met: raise ValueError('arc endpoint gap exceeds tolerance')
        candidate = {'step_index': int(step_index), 'load_factor': float(load_factor),
                'displacements': np.array(displacement, dtype=float, copy=True),
                'contact': result.to_dict()}
        codec._encode(self.history + [candidate], codec._Budget(codec.MAX_BYTES), {})
        return candidate

    def commit(self, candidate):
        # All potentially failing geometry and codec validation occurs before
        # the structural commit; append is the only contact commit operation.
        self.history.append(candidate)

    def encoded_state(self):
        return {'schema': STATE_SCHEMA,
                'history': codec._encode(self.history, codec._Budget(codec.MAX_BYTES), {})}

    def restore(self, state, path, final_displacements):
        if type(state) is not dict or set(state) != {'schema','history'} or state['schema'] != STATE_SCHEMA:
            raise ValueError('incompatible arc contact state')
        history = codec._decode(state['history'], codec._Budget(codec.MAX_BYTES), {})
        if type(history) is not list or len(history) != path['step_index']:
            raise ValueError('incomplete arc contact accepted history')
        previous = np.zeros(self.manager.n_dof)
        for index, row in enumerate(history, 1):
            if type(row) is not dict or set(row) != {'step_index','load_factor','displacements','contact'}:
                raise ValueError('invalid arc contact record')
            pose = row['displacements']
            if type(pose) is not np.ndarray or pose.shape != (self.manager.n_dof,) or not np.all(np.isfinite(pose)):
                raise ValueError('invalid arc contact accepted pose')
            step = path['steps'][index-1]
            if row['step_index'] != index or row['load_factor'] != step['load_factor']:
                raise ValueError('arc contact record differs from accepted structural path')
            if not self.admissible(previous, pose): raise ValueError('uncertified restored arc contact path')
            observed = self.prepare(pose, index, row['load_factor'])
            if codec._canonical(codec._encode(observed,codec._Budget(codec.MAX_BYTES),{})) != codec._canonical(
                    codec._encode(row,codec._Budget(codec.MAX_BYTES),{})):
                raise ValueError('arc contact accepted state failed replay')
            previous = pose
        if history and previous.tobytes() != np.asarray(final_displacements).tobytes():
            raise ValueError('arc contact final pose differs from structural checkpoint')
        if not history and (np.any(final_displacements) or path['load_factor'] != 0.):
            raise ValueError('empty contact history requires virgin zero endpoint')
        self.history = history

    def validate_path(self, path, reduce_pose, full_pose, metric, arc_tolerance):
        previous_q = reduce_pose(np.zeros(self.manager.n_dof), 0.)
        previous_lambda = 0.
        last_delta = None
        for row, step in zip(self.history, path['steps']):
            pose = row['displacements']; lam = row['load_factor']
            q = reduce_pose(pose, lam)
            reconstructed = full_pose(q, lam)
            guard = 512*np.finfo(float).eps*max(1.,float(np.linalg.norm(pose)))
            if np.linalg.norm(reconstructed-pose) > guard:
                raise ValueError('arc contact history violates structural constraints')
            delta_q = q-previous_q; delta_lambda = lam-previous_lambda
            norm2 = metric(delta_q,delta_lambda,delta_q,delta_lambda)
            radius2 = step['arc_radius']**2
            if abs(norm2-radius2) > arc_tolerance*radius2+guard**2:
                raise ValueError('arc contact history violates spherical constraint')
            for actual, saved in ((np.linalg.norm(pose),step['displacement_norm']),
                    (np.sqrt(norm2),step['path_increment_norm']),
                    (delta_lambda,step['load_increment'])):
                if abs(actual-saved) > guard:
                    raise ValueError('arc contact history differs from structural step metric')
            previous_q,previous_lambda=q,lam;last_delta=delta_q
        if last_delta is not None:
            if np.linalg.norm(last_delta-np.asarray(path['previous_dq'])) > guard or \
                    abs(delta_lambda-path['previous_dlambda']) > guard:
                raise ValueError('arc contact predictor history differs from accepted path')


@contextmanager
def arc_contact_scope(model, definition, settings):
    adapter = ArcContactAdapter(model, definition, settings)
    token = _ACTIVE_CONTACT.set(adapter)
    try: yield adapter
    finally: _ACTIVE_CONTACT.reset(token)
