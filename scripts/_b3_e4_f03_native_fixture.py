"""Unregistered F03 diagnostic fixture for the native retained generalized B3 chain.

The straight reference axis is x=s in [0, 1] metres.  ``n_half_cells`` is
4, 8, or 16; two half-cells form each actual three-node native B3 element.
The law is a positive *generalized resultant* law, not a fibre surrogate:
E=210 GPa, nu=.3, G=E/(2*(1+nu)), A=.01 m², Ay=Az=.008 m²,
Iy=Iz=8.333333333333333e-6 m⁴, J=1.6666666666666667e-5 m⁴.
In [N,Vy,Vz,Mx,My,Mz] work order the diagonal elastic entries are
[EA,G Ay,G Az,G J,E Iy,E Iz].  Yield force 1e20 and hardening 1e9
are declared section parameters; all observations here are virgin elastic.

The six physical DOFs of the root node are fixed.  All other nodal DOFs and
all native internal coordinates are free.  Assembly calls the same retained
Context.assemble/F08 local spatial-Jacobian seam as the native implementation.
No registered gate or product code is called by importing this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.spatial.transform import Rotation

from anysolver.boundary import BoundaryCondition
from anysolver.fe_core import FEModel
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_retained_generalized_state import Context, Program
from anysolver._ge_beam3_fibre_line_work import evaluate as line_work
from anysolver._ge_beam3_generalized_static_boundary import cell_couple_load, spatial_jacobian
from anysolver._ge_beam3_operator_validation_scope import operator_call


E = 210e9
NU = .3
G = E / (2 * (1 + NU))
AREA = .01
SHEAR_AREA = .008
I = 8.333333333333333e-6
J = 2 * I
SECTION_DIAGONAL = np.array([E * AREA, G * SHEAR_AREA, G * SHEAR_AREA,
                             G * J, E * I, E * I])


@dataclass
class Fixture:
    """Live native assembly, with local full-block access for a coupled KKT.

    ``tangent`` is the actual sparse virgin residual Jacobian, including retained
    rotational spatial-chart corrections. ``physical`` lists supported nodal
    DOF indices; ``internal`` lists all native cell rotations and 18 resultants
    per element.  The full tangent is a mixed saddle matrix, not an SPD energy
    norm.  ``blocks()`` returns Kpp,Kpr,Krp,Krr; callers may eliminate internal
    coordinates only while carrying the trace's Cr columns as well.
    """

    n_half_cells: int
    model: FEModel
    context: Context
    residual: np.ndarray
    tangent: sparse.csr_matrix
    physical: np.ndarray
    internal: np.ndarray
    dense_oracle_max_error: float

    def blocks(self):
        k = self.tangent
        return (k[np.ix_(self.physical, self.physical)].toarray(),
                k[np.ix_(self.physical, self.internal)].toarray(),
                k[np.ix_(self.internal, self.physical)].toarray(),
                k[np.ix_(self.internal, self.internal)].toarray())

    def _locate(self, s):
        if not np.isfinite(s) or not 0 <= s <= 1:
            raise ValueError('station s must be finite and in [0, 1]')
        h = 1 / self.n_half_cells
        half = min(int(s / h), self.n_half_cells - 1)
        element, cell = divmod(half, 2)
        t = (s - half * h) / h
        return element, cell, t, cell - 1 + t

    def pose(self, s, step=None):
        """Return actual native lifted station (position, spatial frame).

        ``step`` is a full retained increment with fixed physical DOFs zero;
        cell frames are updated by the native Context.advance spatial chart.
        The reference has zero quadratic lift, but the same native lift is
        evaluated here to preserve the declared pose route.
        """
        e, c, t, xi = self._locate(s)
        state = self.context.initial.mechanical
        if step is not None:
            delta = np.asarray(step, dtype=float)
            if delta.shape != (self.context.count,):
                raise ValueError('full retained step required')
            state = self.context.advance(state, delta)
        nodes = self.context.nodes[e]
        left, right = nodes[c:c+2]
        op = self.context.elements[e][1].operator
        lift = op.reference.half_cell_lift(c, t)
        rot = state.cell_rotations[e, c]
        position = ((1-t) * (state.positions[left] + state.position_low[left])
                    + t * (state.positions[right] + state.position_low[right])
                    + rot @ lift)
        return position, rot @ op.reference.frame(xi)

    def planar_trace(self, s, step=None):
        """Return [ux, uy, spatial Rz] at the station relative to virgin pose."""
        position, frame = self.pose(s, step)
        reference_position, reference_frame = self.pose(s)
        angle = Rotation.from_matrix(frame @ reference_frame.T).as_rotvec()[2]
        return np.array([*(position-reference_position)[:2], angle])

    def planar_trace_jacobian(self, s):
        """Exact virgin derivative, 3 by full retained DOFs (Cp and Cr).

        For a straight axis the native half-cell lift vanishes.  Translation
        rows interpolate adjacent native positions; Rz is the spatial cell
        rotation increment.  The selected native cell rotation column belongs
        to ``internal``, never to the nodal ``physical`` block.
        """
        e, c, t, _ = self._locate(s)
        nodes = self.context.nodes[e]
        out = np.zeros((3, self.context.count))
        out[0, 6*nodes[c]] = 1-t
        out[0, 6*nodes[c+1]] = t
        out[1, 6*nodes[c]+1] = 1-t
        out[1, 6*nodes[c+1]+1] = t
        out[2, self.context.nodal_count + 24*e + 3*c + 2] = 1
        return out

    def trace_blocks(self, s):
        trace = self.planar_trace_jacobian(s)
        return trace[:, self.physical], trace[:, self.internal]


def _sparse_native_assembly(context):
    """F08 seam: exact local operator evaluation and COO to CSR gather.

    The local 42-vector contains 18 physical DOFs, 6 cell rotations, and 18
    generalized resultants.  Its spatial Jacobian is the actual native seam,
    not an interpolated or surrogate beam stiffness.
    """
    state = context.initial.mechanical
    origins = context.initial.origins
    residual = np.zeros(context.count)
    rows, cols, data = [], [], []
    for i, (eid, element) in enumerate(context.elements):
        nodes = context.nodes[i]
        op = element.operator
        response = operator_call(
            op, 'evaluate', context.guard, context.started,
            state.positions[nodes], state.position_low[nodes], state.nodal_frames[nodes],
            state.cell_rotations[i], state.resultants[i], origin=origins[i])
        work = line_work(op.reference, state.positions[nodes], state.position_low[nodes],
                         state.cell_rotations[i], context.program.pattern.force(eid),
                         order=op.order)
        rc = response.residual - work.gradient
        local_r = rc - cell_couple_load(op, context.program.pattern.density(eid))
        local_k = spatial_jacobian(rc, response.hessian + response.hessian_low - work.hessian)
        ids = np.asarray(context.slots[i], dtype=int)
        np.add.at(residual, ids, local_r)
        rows.extend(np.repeat(ids, len(ids)))
        cols.extend(np.tile(ids, len(ids)))
        data.extend(local_k.ravel())
    tangent = sparse.coo_matrix((data, (rows, cols)),
                                shape=(context.count, context.count)).tocsr()
    tangent.eliminate_zeros()
    return residual, tangent


def build(n_half_cells: int) -> Fixture:
    """Construct and assemble an actual virgin elastic retained B3 chain."""
    if type(n_half_cells) is not int or n_half_cells not in (4, 8, 16, 32):
        raise ValueError('n_half_cells must be exactly 4, 8, 16, or 32')
    n_elements = n_half_cells // 2
    h = 1 / n_half_cells
    model = FEModel(f'f03-native-virgin-{n_half_cells}')
    for node in range(n_half_cells + 1):
        model.add_node(node + 1, node*h, 0., 0.)
    section = EllipsoidalGeneralizedSection(np.diag(SECTION_DIAGONAL), np.eye(6),
                                           1e20, 1e9)
    for element in range(n_elements):
        ids = (2*element+1, 2*element+2, 2*element+3)
        coords = np.array([model.mesh.nodes[node].coords() for node in ids])
        frames = np.tile(np.eye(3), (3, 1, 1))
        reference = CenteredCurvedBeam3ReferenceGeometry(coords, frames)
        native = NativeGeneralizedStaticElement(element+1, ids, reference,
                                                section, order=4)
        model.add_element(element+1, native)
        model.materials[native.material_name] = native.section
    model.add_boundary_condition(BoundaryCondition(
        'root', [1], {dof: 0. for dof in ('ux','uy','uz','rx','ry','rz')}))
    no_load = DistributedPattern(LinePattern(()), ())
    context = Context(model, Program((1.,), no_load))
    residual, tangent = _sparse_native_assembly(context)
    oracle_r, oracle_k, _, _, _ = context.assemble(
        context.initial.mechanical, 0., context.initial.origins)
    parity = max(float(np.max(np.abs(oracle_r-residual))),
                 float(np.max(np.abs(oracle_k-tangent.toarray()))))
    if parity > 1e-9:
        raise AssertionError(f'native local sparse/dense parity failed: {parity}')
    physical = np.array([i for i in range(context.nodal_count)
                         if i not in context.fixed], dtype=int)
    internal = np.arange(context.nodal_count, context.count)
    return Fixture(n_half_cells, model, context, residual, tangent,
                   physical, internal, parity)
