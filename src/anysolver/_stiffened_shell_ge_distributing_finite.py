"""Private physical-pose assembly seam; no public/driver admission.

Prepare reference correspondence once from the existing GE owner. Keep its
spatial rows and pull shell increment columns only. This adapter owns no state,
changes no owner flags, and cannot publish a trial or authorize a checkpoint.
"""
from dataclasses import dataclass
from math import fsum
import weakref

import numpy as np
from scipy import sparse

from ._ge_beam3_pose_joint import _exp_terms
from ._stiffened_shell_distributing_pose import (
    FiniteDistributingPose, DistributingPoseDomainError, _owned, _frozen_sparse,
)
from ._stiffened_shell_ge_distributing_reference import _compile_reference_geometry, _reference_owner
from ._stiffened_shell_rotation_charts import physical_frames


@dataclass(frozen=True)
class FiniteDistributingAssembly:
    """Owned candidate work, local saddle block and explicit global scatter."""
    model_identity: str
    candidate_identity: str
    generation: int
    slots: np.ndarray
    residual: np.ndarray
    tangent: sparse.csr_matrix
    gap: np.ndarray
    shell_positions: np.ndarray
    shell_position_low: np.ndarray
    beam_position: np.ndarray
    beam_position_low: np.ndarray
    shell_action: np.ndarray
    beam_action: np.ndarray
    shell_node_actions: np.ndarray
    centroid: np.ndarray
    centroid_low: np.ndarray
    production_qualified: bool = False
    owner_binding_authorized: bool = False

    def scatter(self, global_dimension):
        if (type(global_dimension) is not int or global_dimension <= 0 or
                self.slots.max() >= global_dimension):
            raise ValueError("complete declared extended global dimension required")
        matrix = self.tangent.tocoo()
        tangent = sparse.coo_matrix((matrix.data,
            (self.slots[matrix.row], self.slots[matrix.col])),
            shape=(global_dimension, global_dimension)).tocsr()
        residual = np.zeros(global_dimension)
        np.add.at(residual, self.slots, self.residual)
        return _owned(residual), _frozen_sparse(tangent)


class PreparedFiniteDistributingAttachment:
    """Private reusable local operator compiled from an unadvanced owner.

    Current trial state is supplied explicitly, using the existing owner's
    additive shell chart and spatial beam update. No model-wide hash/search
    occurs during evaluation. A different/closed/recompiled owner is rejected.
    """
    __slots__ = ("reference", "pose", "model_identity", "_owner", "_K",
                 "_shell_parts", "_count", "_shell_nodes", "_beam_node", "_sealed")

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise AttributeError("prepared finite attachment is immutable")
        object.__setattr__(self, name, value)

    def __init__(self, owner, definition):
        _reference_owner(owner)
        self.reference = _compile_reference_geometry(definition,
            shell_parts=owner._shell_parts, shell_index=owner._shell_index,
            shell_xyz=owner._shell_xyz, beam_index=owner._beam_index,
            beam_nodes=owner._beam_nodes, shell_count=owner._shell_count,
            global_dimension=owner._K.shape[0])
        self.pose = FiniteDistributingPose(self.reference)
        self.model_identity = owner._identity
        self._owner = weakref.ref(owner)
        self._K = owner._K
        self._shell_parts = owner._shell_parts
        self._count = owner._K.shape[0]
        self._shell_nodes = _owned(np.array(
            [owner._shell_index[node] for node in self.reference.shell_node_ids], dtype=np.int64))
        self._beam_node = owner._beam_index[self.reference.beam_node_id]
        self._sealed = True

    def descriptor(self):
        return dict(self.pose.descriptor(), model_identity=self.model_identity,
            scatter="LOCAL_SPARSE_SADDLE_BLOCK", accepted_state_owned=False,
            checkpoint_admission=False)

    def evaluate(self, owner, state, multipliers, *, multiplier_row_start=0):
        from ._stiffened_shell_ge_finite_experimental import _State, _position_pair
        if (self._owner() is not owner or owner._identity != self.model_identity or
                owner._K is not self._K or owner._shell_parts is not self._shell_parts):
            raise ValueError("stale or different finite attachment owner")
        owner._require_open()
        if (type(state) is not _State or state.q.shape != (self._count,) or
                state.frames.shape != (len(owner._beam_ids), 3, 3) or
                type(multiplier_row_start) is not int or multiplier_row_start < 0):
            raise ValueError("complete owner trial and explicit multiplier row start required")
        nodes = self._shell_nodes
        local_q = state.q[:owner._shell_count].reshape(-1, 6)[nodes]
        anchors = (None if state.shell_anchors is None else state.shell_anchors[nodes])
        frames = physical_frames(local_q.ravel(), anchors)
        pairs = [_position_pair(owner._shell_xyz[node], q[:3]) for node, q in zip(nodes, local_q)]
        positions, low = np.array([v[0] for v in pairs]), np.array([v[1] for v in pairs])
        start = owner._shell_count+6*self._beam_node
        beam, beam_low = _position_pair(owner._beam_nodes[self.reference.beam_node_id][0], state.q[start:start+3])
        result = self.pose.evaluate(positions, frames, beam, state.frames[self._beam_node],
            multipliers, shell_position_low=low, beam_position_low=beam_low)
        blocks = []
        for q in local_q:
            left = _exp_terms(q[3:])[1]
            if np.linalg.svd(left, compute_uv=False)[-1] <= 1e-11:
                raise ValueError("singular distributing shell chart; owner must rebase")
            blocks.append(sparse.block_diag((np.eye(3), left), format="csr"))
        blocks.append(sparse.eye(6, format="csr"))
        columns = sparse.block_diag(blocks, format="csr")
        C = sparse.csr_matrix(result.constraint_jacobian)
        tangent = sparse.bmat(((result.spatial_jacobian@columns, C.T),
            (C@columns, sparse.csr_matrix((6, 6)))), format="csr")
        slots = np.r_[self.reference.gather_slots,
            self._count+multiplier_row_start+np.arange(6, dtype=np.int64)]
        # Exerted physical actions are minus the evaluated spatial work rows;
        # raw Log multipliers are not recovered display moments.
        action = -result.residual.reshape(-1, 6)
        arms = np.array([[fsum((float(x[j]),float(xl[j]),
            -float(result.shell_position[j]),-float(result.shell_position_low[j])))
            for j in range(3)] for x,xl in zip(positions,low)])
        with np.errstate(over="ignore", invalid="ignore"):
            couples = np.cross(arms, action[:-1,:3])+action[:-1,3:]
        if not np.isfinite(arms).all() or not np.isfinite(couples).all():
            raise DistributingPoseDomainError("unrepresentable distributing recovery moment")
        try:
            shell_action = np.array([fsum(float(v) for v in column)
                for column in np.c_[action[:-1,:3], couples].T])
        except OverflowError as error:
            raise DistributingPoseDomainError("unrepresentable distributing recovery resultant") from error
        if not np.isfinite(shell_action).all():
            raise DistributingPoseDomainError("unrepresentable distributing recovery resultant")
        return FiniteDistributingAssembly(self.model_identity, self.pose.identity, owner._generation,
            _owned(slots), _owned(np.r_[result.residual,result.constraints]), _frozen_sparse(tangent),
            result.constraints, _owned(positions), _owned(low), _owned(beam), _owned(beam_low),
            _owned(shell_action), _owned(action[-1]), _owned(action[:-1]),
            result.shell_position, result.shell_position_low)
