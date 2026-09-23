"""Signed cell/edge/jump work checks for the classical Qp reference."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_nodal_recovery import (
    assemble_line_nodal_load, support_liftings,
)
from scripts._b3_e4_f03_qp_spatial_recovery import SpatialQpRecovery


X = (-.5, -.12, .29, .81, 1.5)
Y = (-.5, -.08, .18, .5)


@pytest.mark.parametrize("p", (1, 4, 5))
def test_signed_cell_boundary_jump_and_support_work(p):
    trace = FinitePadQpTrace(p, x=X, y=Y)
    rng = np.random.default_rng(7073)
    q = 2e-5*rng.normal(size=2*trace.n)
    z = 3e-5*rng.normal(size=2*trace.n)
    eta = np.array((1.7e4, -8.1e3, 3.2e3))
    adjoint = FinitePadAreaAdjoint(trace, q, eta)
    spatial = SpatialQpRecovery(adjoint)
    assert spatial.area_order_error <= 2e-10
    line_load = assemble_line_nodal_load(adjoint)

    inside = spatial.cell(0, 0, -.2, -.23)
    np.testing.assert_allclose(inside["residual"],
                               inside["divergence"]+inside["area_force"],
                               rtol=0, atol=0)
    assert np.linalg.norm(inside["area_force"]) > 0
    outside = spatial.cell(0, 2, -.4, .4)
    np.testing.assert_array_equal(outside["area_force"], np.zeros(2))
    np.testing.assert_array_equal(outside["residual"], outside["divergence"])

    work = spatial.work(z)
    direct = line_load@z-spatial.shell.energy_work(q, z)
    assert abs(work.total-direct)/max(E0, abs(work.total), abs(direct)) <= 2e-9
    assert abs(work.support) > 1e-7
    assert abs(work.free) > 1e-7
    assert abs(work.interior) > 1e-7

    for lift in support_liftings(trace):
        reaction = spatial.work(lift).reaction
        direct_reaction = spatial.shell.energy_work(q, lift)-line_load@lift
        assert abs(reaction-direct_reaction)/max(
            E0, abs(reaction), abs(direct_reaction)) <= 2e-9

    # The wrapper exposes the physical outward and two-cell jump fields.
    np.testing.assert_array_equal(
        spatial.outer_traction("y", 1, 1, .1),
        spatial.shell.outer_traction(spatial.coefficients, "y", 1, 1, .1))
    np.testing.assert_array_equal(
        spatial.interior_jump("x", 1, 1, .1),
        spatial.shell.interior_jump(spatial.coefficients, "x", 1, 1, .1))
