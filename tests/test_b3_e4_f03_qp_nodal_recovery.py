"""Bounded coupled nodal balance and physical support-work checks."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_energy import assemble, solve
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_nodal_recovery import (
    assemble_line_nodal_load, recover_nodal, support_liftings,
)
from scripts._b3_e4_f03_qp_shell_recovery import PiecewiseQpShellRecovery


X = (-.5, -.12, .29, .81, 1.5)
Y = (-.5, -.08, .18, .5)


@pytest.mark.parametrize("p", (1, 2, 3))
def test_nodal_projection_and_support_work(p):
    trace = FinitePadQpTrace(p, x=X, y=Y)
    operators = assemble(trace)
    free_q, eta, _ = solve(operators)
    q = np.zeros(2*trace.n)
    q[operators.free_columns] = free_q
    adjoint = FinitePadAreaAdjoint(trace, q, eta)
    recovered = recover_nodal(adjoint)
    force_scale = max(F0, np.max(np.abs(recovered.line_nodal_load)))
    line_gap = np.max(np.abs(recovered.area_nodal_load-
                             recovered.line_nodal_load))/force_scale
    equilibrium_gap = np.max(np.abs(recovered.free_residual))/force_scale
    wrench_scale = max(F0, np.max(np.abs(recovered.line_wrench)))
    wrench_gap = np.max(np.abs(recovered.area_wrench-
                               recovered.line_wrench))/wrench_scale
    assert line_gap <= 2e-9, line_gap
    comparison_line = assemble_line_nodal_load(adjoint, order=64)
    assert np.max(np.abs(comparison_line-recovered.line_nodal_load))/force_scale <= 2e-10
    assert equilibrium_gap <= 2e-9, equilibrium_gap
    assert wrench_gap <= 2e-9, wrench_gap

    lifts = support_liftings(trace)
    shell = PiecewiseQpShellRecovery(trace)
    support = np.setdiff1d(np.arange(2*trace.n), trace.free_columns)
    for index, lift in enumerate(lifts):
        green = shell.integration_by_parts(q, lift)
        work_reaction = green.total-recovered.area_nodal_load@lift
        assert abs(work_reaction-recovered.support_wrenches[index]) <= (
            2e-10*max(1., F0, abs(work_reaction)))
        assert abs(recovered.support_wrenches[index]-
                   lift[support]@recovered.support_residual) <= (
            2e-10*max(1., F0, abs(work_reaction)))

    assert np.linalg.norm(recovered.support_wrenches[:3]) > 0
    assert np.linalg.norm(recovered.support_wrenches[3:]) > 0
    np.testing.assert_array_equal(recovered.beam_root_reaction, -eta)
    # The beam root is a distinct physical support: its reaction is -eta.
    shell_total = recovered.support_wrenches[:3]+recovered.support_wrenches[3:]
    np.testing.assert_allclose(shell_total, -recovered.line_wrench,
                               rtol=0, atol=2e-9*F0)
    assert abs(shell_total[0]+recovered.beam_root_reaction[0]) < 2e-9*F0
    assert abs(shell_total[1]+recovered.beam_root_reaction[1]+F0) < 2e-9*F0
