"""Bounded F08 native B3 local-operator seam; not G0B acceptance."""

import numpy as np
import pytest
from scipy import sparse

from anysolver._ge_beam3_fibre_line_work import evaluate as line_work
from anysolver._ge_beam3_generalized_static_boundary import (
    cell_couple_load, spatial_jacobian,
)
from anysolver._ge_beam3_operator_validation_scope import operator_call
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._ge_beam3_retained_fibre_state import Context as FibreContext
from anysolver._ge_beam3_seeded_load_program import ForceProgram
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from test_ge_beam3_retained_fibre import make_model


def _relative_error(first, second):
    return float(np.linalg.norm(first-second)/max(1., np.linalg.norm(second)))


def _sparse_local_gather(context, state, origin, parameter, *, fibre):
    """Gather only 42-coordinate element blocks, including shared nodes."""
    layout = context.layout if fibre else context
    residual = np.zeros(layout.count)
    row, column, data = [], [], []
    candidates = []
    for i, (eid, element) in enumerate(layout.elements):
        nodes = layout.nodes[i]
        operator = element.operator
        response = (operator.evaluate(
            state.positions[nodes], state.position_low[nodes],
            state.nodal_frames[nodes], state.cell_rotations[i],
            state.resultants[i], origin=origin[i], check=context.check)
            if fibre else operator_call(
                operator, "evaluate", context.guard, context.started,
                state.positions[nodes], state.position_low[nodes],
                state.nodal_frames[nodes], state.cell_rotations[i],
                state.resultants[i], origin=origin[i]))
        if fibre:
            local_r = response.residual
            local_k = response.hessian+response.hessian_low
        else:
            work = line_work(
                operator.reference, state.positions[nodes],
                state.position_low[nodes], state.cell_rotations[i],
                parameter*context.program.pattern.force(eid),
                order=operator.order)
            corrected = response.residual-work.gradient
            local_r = corrected-cell_couple_load(
                operator, parameter*context.program.pattern.density(eid))
            local_k = spatial_jacobian(
                corrected, response.hessian+response.hessian_low-
                work.hessian)
        slots = np.asarray(layout.slots[i], dtype=int)
        assert local_r.shape == (42,) and local_k.shape == (42, 42)
        assert np.isfinite(local_r).all() and np.isfinite(local_k).all()
        np.add.at(residual, slots, local_r)
        row.extend(np.repeat(slots, 42))
        column.extend(np.tile(slots, 42))
        data.extend(local_k.ravel())
        candidates.append(canonical(response.history))
    if fibre:
        residual[:layout.nodal_count] -= parameter*layout.force
    tangent = sparse.coo_matrix(
        (data, (row, column)), shape=(layout.count, layout.count)).tocsr()
    tangent.eliminate_zeros()
    return residual, tangent, tuple(candidates)


@pytest.mark.parametrize("family", ("generalized", "physical_fibre"))
@pytest.mark.parametrize("trial", (False, True))
def test_native_two_element_local_sparse_seam_matches_dense_owner(
        family, trial):
    if family == "generalized":
        context = build(4, z_offset=.0675,
                        torsion_constant=square_torsion_constant()).context
        state = context.initial.mechanical
        origin = context.initial.origins
        count = context.count
        nodal_count = context.nodal_count
        advance = context.advance
        dense = lambda values: context.assemble(values, .25, origin)
    else:
        context = FibreContext(
            make_model(contrast=1.),
            ForceProgram((.25,), ((5, .4, -.005, 0.),),
                         max_iterations=24))
        state = context.initial.mechanical
        origin = context.initial.origins
        count = context.layout.count
        nodal_count = context.layout.nodal_count
        advance = context.layout.advance
        dense = lambda values: context.assemble(values, .25, origin)
    assert len(origin) == 2 and count <= 256
    before = canonical(origin)
    if trial:
        delta = np.zeros(count)
        delta[nodal_count-6+1] = 1e-6
        delta[nodal_count-6+3] = 2e-6
        delta[nodal_count] = 1e-6
        state = advance(state, delta)
    residual, tangent, candidate = _sparse_local_gather(
        context, state, origin, .25, fibre=(family == "physical_fibre"))
    dense_result = dense(state)
    assert _relative_error(residual, dense_result[0]) <= 1e-12
    assert _relative_error(tangent.toarray(), dense_result[1]) <= 1e-12
    assert candidate == tuple(canonical(response.history)
                              for response in dense_result[3])
    assert canonical(origin) == before
