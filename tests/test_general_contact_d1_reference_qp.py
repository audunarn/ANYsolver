"""Analytical controls for the source-only D1 pressure-QP certificate."""

from types import SimpleNamespace

import numpy as np
import pytest

from scripts import general_contact_d1_linearized_front_reference as reference


def test_iteration_limited_preliminary_qp_needs_complete_active_set_certificate(
    monkeypatch,
):
    hessian = np.array(((2.0, -1.0), (-1.0, 2.0)))
    linear = np.array((-1.0, 1.0))
    support = np.ones(2)
    expected_pressure = np.array((0.5, 0.0))

    def preliminary(*_args, **_kwargs):
        return SimpleNamespace(
            x=np.array((0.4, 0.0)), success=False,
            message="STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT",
        )

    monkeypatch.setattr(reference, "minimize", preliminary)
    with pytest.raises(RuntimeError, match="ITERATIONS REACHED LIMIT"):
        reference._nonnegative_quadratic(hessian, linear, support)

    diagnostics = {}
    pressure = reference._nonnegative_quadratic(
        hessian, linear, support,
        accept_iteration_limit_with_certificate=True,
        diagnostics=diagnostics,
    )
    np.testing.assert_allclose(pressure, expected_pressure, rtol=0, atol=1e-15)
    np.testing.assert_allclose(hessian @ pressure+linear, (0.0, 0.5),
                               rtol=0, atol=1e-15)
    assert diagnostics["certificate_passed"] is True
    assert diagnostics["active_stationarity_gap_m"] == pytest.approx(0.0)
    assert diagnostics["inactive_minimum_gap_m"] == pytest.approx(0.5)

    def abnormal(*_args, **_kwargs):
        return SimpleNamespace(x=np.array((0.4, 0.0)), success=False,
                               message="ABNORMAL TERMINATION")

    monkeypatch.setattr(reference, "minimize", abnormal)
    with pytest.raises(RuntimeError, match="ABNORMAL TERMINATION"):
        reference._nonnegative_quadratic(
            hessian, linear, support,
            accept_iteration_limit_with_certificate=True,
        )
