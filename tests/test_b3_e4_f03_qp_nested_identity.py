"""Preparatory exact Qp nesting checks; no physical settling claim."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_energy import assemble, solve
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0, U0, YAW_LENGTH
from scripts._b3_e4_f03_qp_nested_identity import (
    evaluate_nested_identity, prolongate,
)


X = (-.5, -.12, .29, .81, 1.5)
Y = (-.5, -.08, .18, .5)


@pytest.mark.parametrize("coarse_p,fine_p", ((1, 2), (1, 3), (2, 3)))
def test_exact_piecewise_embedding_preserves_pose_and_energy(coarse_p, fine_p):
    coarse = FinitePadQpTrace(coarse_p, x=X, y=Y)
    fine = FinitePadQpTrace(fine_p, x=X, y=Y)
    rng = np.random.default_rng(1270+10*coarse_p+fine_p)
    q = 2e-5*rng.normal(size=2*coarse.n)
    embedded = prolongate(coarse, fine, q)
    for station in (.0, .071, .2, .447, .77, 1.):
        for row_coarse, row_fine in zip(coarse.matrices(station),
                                        fine.matrices(station)):
            np.testing.assert_allclose(row_coarse@q, row_fine@embedded,
                                       rtol=2e-11, atol=2e-11)

def test_solved_nested_energy_identity_and_same_physics_rejection():
    traces = [FinitePadQpTrace(p, x=X, y=Y) for p in (1, 2, 3)]
    operators = [assemble(trace) for trace in traces]
    solutions = [solve(item)[0] for item in operators]
    for coarse_index, fine_index in ((0, 1), (0, 2), (1, 2)):
        rng = np.random.default_rng(4410+10*coarse_index+fine_index)
        coarse = operators[coarse_index]
        fine = operators[fine_index]
        qc = 2e-5*rng.normal(size=coarse.dof_count)
        full = np.zeros(2*coarse.trace.n)
        full[coarse.free_columns] = qc
        pf = prolongate(coarse.trace, fine.trace, full)[fine.free_columns]
        coarse_work = qc@((coarse.shell_stiffness+
                           coarse.beam_stiffness)@qc)/2
        fine_work = pf@((fine.shell_stiffness+
                         fine.beam_stiffness)@pf)/2
        assert abs(coarse_work-fine_work)/max(E0, abs(coarse_work),
                                              abs(fine_work)) <= 1e-10
        assert abs(coarse.load@qc-fine.load@pf)/E0 <= 1e-10
        pose_scale = np.array((1/U0, 1/U0, YAW_LENGTH/U0))
        for action in ("root_constraint", "tip_pose"):
            c = pose_scale*(getattr(coarse, action)@qc)
            f = pose_scale*(getattr(fine, action)@pf)
            assert np.max(np.abs(c-f))/max(
                1., np.max(np.abs(c)), np.max(np.abs(f))) <= 1e-10
    for index in (0, 1):
        identity = evaluate_nested_identity(
            operators[index], operators[index+1],
            solutions[index], solutions[index+1])
        assert identity.fine_energy >= identity.coarse_energy-1e-10*E0
        assert identity.defect_scaled <= 1e-10
        assert identity.load_embedding_scaled <= 1e-10
        assert identity.root_embedding_scaled <= 1e-10
        assert identity.tip_embedding_scaled <= 1e-10
    with pytest.raises(ValueError, match="share physical"):
        prolongate(traces[0], FinitePadQpTrace(2, x=X, y=Y,
                   j=1.01*traces[0].j), np.zeros(2*traces[0].n))


def test_q6_nested_x_preserves_pose_work_and_ritz_identity():
    coarse_x = (-.5, 0., 1.5)
    fine_x = (-.5, -.25, 0., .75, 1.5)
    y = (-.5, 0., .5)
    coarse = FinitePadQpTrace(6, x=coarse_x, y=y)
    fine = FinitePadQpTrace(6, x=fine_x, y=y)
    rng = np.random.default_rng(6601)
    q = rng.normal(size=2*coarse.n)*1e-5
    q[np.setdiff1d(np.arange(2*coarse.n), coarse.free_columns)] = 0.
    embedded = prolongate(coarse, fine, q)
    for station in (0., .137, .43, .9, 1.):
        for original, refined in zip(coarse.matrices(station),
                                     fine.matrices(station)):
            np.testing.assert_allclose(original@q, refined@embedded,
                                       rtol=1e-10, atol=1e-11)
    coarse_operator, fine_operator = assemble(coarse), assemble(fine)
    qc, _, _ = solve(coarse_operator)
    qf, _, _ = solve(fine_operator)
    identity = evaluate_nested_identity(coarse_operator, fine_operator,
                                        qc, qf)
    assert identity.fine_energy >= identity.coarse_energy-1e-10*E0
    assert identity.defect_scaled <= 1e-10
    assert identity.load_embedding_scaled <= 1e-10
    assert identity.root_embedding_scaled <= 1e-10
    assert identity.tip_embedding_scaled <= 1e-10
    with pytest.raises(ValueError, match="share physical"):
        prolongate(coarse, FinitePadQpTrace(6, x=(-.5, .1, 1.5), y=y), q)
    with pytest.raises(ValueError, match="share physical"):
        prolongate(coarse, FinitePadQpTrace(6, x=(-.6, -.5, 0., 1.5), y=y), q)
