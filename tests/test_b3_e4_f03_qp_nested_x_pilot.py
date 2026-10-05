"""Uniform case runner preflight for a prospective fixed-Q6 h gate."""

import pytest
import json

from scripts import b3_e4_f03_qp_nested_x_pilot as pilot
from scripts import b3_e4_f03_qp_nested_x2_spatial as spatial
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace


class _PreflightReached(Exception):
    pass


def test_x0_uses_the_same_case_route_with_the_frozen_default_grid(monkeypatch):
    def inspect(trace):
        assert trace.p == 6
        assert len(trace.x) == 10
        assert len(trace.station_intervals()) == 11
        assert len(trace.free_columns) == 3286
        raise _PreflightReached

    monkeypatch.setattr(pilot, "assemble", inspect)
    with pytest.raises(_PreflightReached):
        pilot.run(6, "x0")


def test_x0_and_x2_reject_a_change_of_polynomial_degree():
    for grid in ("x0", "x2"):
        with pytest.raises(ValueError, match="fixed Q6"):
            pilot.run(5, grid)


@pytest.mark.parametrize("grid,x,status", (
    ("x0", None, "UNREGISTERED_NESTED_X0_PILOT"),
    ("x1", pilot.refined_x(), "UNREGISTERED_NESTED_X_PILOT"),
    ("x2", pilot.refined_x2(), "UNREGISTERED_NESTED_X2_PILOT"),
))
def test_spatial_route_checks_each_exact_grid_before_evaluation(
        grid, x, status, monkeypatch, tmp_path):
    trace = FinitePadQpTrace(6, x=x)
    path = tmp_path / f"{grid}.json"
    path.write_text(json.dumps({
        "grid": grid, "status": status, "degree": 6,
        "x_hex": [v.hex() for v in trace.x],
        "y_hex": [v.hex() for v in trace.y],
        "dof_count": len(trace.free_columns),
        "physical_coordinates": 2*trace.n,
        "free_state": [0.]*len(trace.free_columns),
        "root_multiplier": [0., 0., 0.],
    }), encoding="utf-8")

    def stop(actual, q, eta):
        assert actual.x == trace.x
        assert q.shape == (2*trace.n,)
        raise _PreflightReached

    monkeypatch.setattr(spatial, "from_qp_recovery_precise", stop)
    with pytest.raises(_PreflightReached):
        spatial.run(path)
