"""Differential tests: fused shell element kernels against the reference arithmetic.

The fused compiled kernels (``_compensated_native.fused_*``) must reproduce the
numpy-level reference bit for bit (values, signed zeros) and must either succeed
with the reference value or leave the reference to raise its own exception.
``ANYSOLVER_FUSED_CASES`` sets the randomized case count (default is small; the
acceptance run uses >= 100000).
"""
import os
import warnings

import numpy as np
import pytest

from anysolver import _compensated_contractions as cc
from anysolver import vectorized_nonlinear as vn

pytestmark = pytest.mark.skipif(not cc._USE_FUSED, reason="fused compiled kernels unavailable")

CASES = int(os.environ.get("ANYSOLVER_FUSED_CASES", "1500"))
TINY = 5e-324


def _rnd(rng, shape, mode):
    base = rng.standard_normal(shape)
    if mode == 0:
        return base
    if mode == 1:
        return base * 2.0 ** rng.integers(-40, 40, shape)
    if mode == 2:  # extreme magnitudes: overflow and subnormal products
        return base * 2.0 ** rng.integers(-520, 520, shape)
    if mode == 3:  # sparse with signed zeros and subnormals
        out = base * 2.0 ** rng.integers(-60, 60, shape)
        pick = rng.integers(0, 6, shape)
        out = np.where(pick == 0, 0.0, out)
        out = np.where(pick == 1, -0.0, out)
        out = np.where(pick == 2, TINY * rng.integers(-5, 6, shape), out)
        return out
    # mode 4: values on a coarse binary grid so that sums cancel exactly or by one ulp
    return rng.integers(-8, 9, shape) * 2.0 ** rng.integers(-3, 4, shape) * (1.0 + (rng.integers(0, 3, shape) == 0) * 2.0 ** -52)


def _geometry(rng, n, ng, ns, mode):
    return {"B_m_all": _rnd(rng, (ng, 3, n), mode), "B_b_all": _rnd(rng, (ng, 3, n), mode),
            "B_d_all": _rnd(rng, (ng, 1, n), mode), "Gw_all": _rnd(rng, (ng, 2, n), mode),
            "B_s_all": _rnd(rng, (ns, 2, n), mode), "T0": _rnd(rng, (n, n), mode),
            "detw_all": np.abs(_rnd(rng, (ng,), min(mode, 1))) + 0.05,
            "detw_shear_all": np.abs(_rnd(rng, (ns,), min(mode, 1))) + 0.05}


def _poison(rng, arrays):
    """Inject a nonfinite value into one randomly chosen array (in place)."""
    target = arrays[rng.integers(0, len(arrays))]
    flat = target.reshape(-1)
    if flat.size:
        flat[rng.integers(0, flat.size)] = (np.nan, np.inf, -np.inf)[rng.integers(0, 3)]


def _run(function, *args):
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore")
        try:
            result = function(*args)
        except Exception as exc:  # noqa: BLE001 - exception identity is compared
            return ("error", type(exc), str(exc))
    if isinstance(result, tuple):
        return ("ok",) + tuple(np.asarray(r).tobytes() for r in result)
    return ("ok", np.asarray(result).tobytes())


def test_randomized_zero_tangent_matches_reference():
    rng = np.random.default_rng(20261023)
    fused_ok = 0
    for case in range(CASES):
        mode = int(rng.integers(0, 5))
        n = int(rng.choice((2, 3, 6, 8, 12)))
        ng, ns = int(rng.integers(0, 4)), int(rng.integers(0, 4))
        geometry = _geometry(rng, n, ng, ns, mode)
        membrane, bending, shear = (_rnd(rng, (3, 3), mode), _rnd(rng, (3, 3), mode),
                                    _rnd(rng, (2, 2), mode))
        drill = float(_rnd(rng, (1,), mode)[0])
        if case % 9 == 4:
            _poison(rng, [*geometry.values(), membrane, bending, shear])
        want = _run(cc._shell_zero_tangent_reference, geometry, membrane, bending, shear, drill)
        got = _run(cc.shell_zero_tangent, geometry, membrane, bending, shear, drill)
        assert got == want, (case, mode, n, ng, ns)
        fused_ok += want[0] == "ok"
    if CASES >= 1000:
        assert fused_ok > CASES // 5


def test_randomized_elastic_increment_matches_reference():
    rng = np.random.default_rng(20261024)
    fused_ok = 0
    for case in range(CASES):
        mode = int(rng.integers(0, 5))
        n = int(rng.choice((2, 3, 6, 8, 12)))
        ng = int(rng.integers(0, 4))
        geometry = _geometry(rng, n, ng, 0, mode)
        u_elem = _rnd(rng, (n,), mode) * (1e-2 if mode < 2 else 1.0)
        constitutive = _rnd(rng, (3, 3), mode)
        tangent = bool(rng.integers(0, 2))
        if case % 9 == 4:
            _poison(rng, [geometry["T0"], geometry["B_m_all"], geometry["Gw_all"], u_elem, constitutive])
        want = _run(cc.elastic_increment_reference, u_elem, geometry, lambda: constitutive, tangent)

        def routed():
            fused = cc.fused_elastic_increment(u_elem, geometry, constitutive, tangent)
            if fused is not None:
                return fused
            return cc.elastic_increment_reference(u_elem, geometry, lambda: constitutive, tangent)

        got = _run(routed)
        assert got == want, (case, mode, n, ng, tangent)
        fused_ok += want[0] == "ok"
    if CASES >= 1000:
        assert fused_ok > CASES // 5


def test_public_increment_exception_order_and_full_size_element():
    rng = np.random.default_rng(7)
    geometry = _geometry(rng, 24, 4, 4, 1)
    u = rng.standard_normal(24) * 1e-2
    for E, nu, h in ((2.1e11, 0.3, 0.01), (2.1e11, 1.0, 0.01), (2.1e11, float("nan"), 0.01),
                     (float("inf"), 0.3, 0.01), (2.1e11, 0.3, 0.0)):
        for tangent in (True, False):
            def reference():
                return cc.elastic_increment_reference(
                    u, geometry, lambda: h * vn.plane_stress_elastic_matrix(E, nu), tangent)
            assert (_run(lambda *a: vn.elastic_shell_nonlinear_increment(*a, tangent=tangent), u, geometry, E, nu, h)
                    == _run(reference))
    bad = u.copy()
    bad[3] = np.nan
    assert (_run(vn.elastic_shell_nonlinear_increment, bad, geometry, 2.1e11, 1.0, 0.01)
            == _run(cc.elastic_increment_reference, bad, geometry,
                    lambda: 0.01 * vn.plane_stress_elastic_matrix(2.1e11, 1.0), True))


@pytest.mark.parametrize("dtype,readonly,order", [(np.float32, False, "C"), (np.float64, True, "C"),
                                                  (np.float64, False, "F")])
def test_layout_variants_match_reference(dtype, readonly, order):
    rng = np.random.default_rng(11)
    geometry = _geometry(rng, 6, 2, 2, 1)
    membrane, bending, shear = rng.standard_normal((3, 3)), rng.standard_normal((3, 3)), rng.standard_normal((2, 2))
    geometry = {k: np.asarray(np.asfortranarray(v) if order == "F" else v, dtype=dtype)
                for k, v in geometry.items()}
    if readonly:
        for v in geometry.values():
            v.flags.writeable = False
    assert (_run(cc.shell_zero_tangent, geometry, membrane, bending, shear, 0.3)
            == _run(cc._shell_zero_tangent_reference, geometry, membrane, bending, shear, 0.3))


def test_signed_zero_and_cancellation_results_are_bitwise_equal():
    n = 4
    geometry = {k: np.zeros(s) for k, s in (("B_m_all", (1, 3, n)), ("B_b_all", (1, 3, n)), ("B_d_all", (1, 1, n)),
                                           ("Gw_all", (1, 2, n)), ("B_s_all", (1, 2, n)), ("T0", (n, n)))}
    geometry["T0"][:] = -0.0
    geometry["detw_all"] = np.array([-0.0])
    geometry["detw_shear_all"] = np.array([0.0])
    args = (geometry, np.eye(3), -np.eye(3), np.eye(2), -0.0)
    assert _run(cc.shell_zero_tangent, *args) == _run(cc._shell_zero_tangent_reference, *args)
    # a huge pair cancelling exactly plus a tiny remainder: compensation must survive
    geometry = _geometry(np.random.default_rng(3), n, 2, 2, 4)
    geometry["B_m_all"][1] = -geometry["B_m_all"][0]
    geometry["detw_all"][:] = 1.0
    args = (geometry, np.eye(3) * 1e150, np.eye(3) * 1e-150, np.eye(2), 1.0)
    assert _run(cc.shell_zero_tangent, *args) == _run(cc._shell_zero_tangent_reference, *args)


def test_scalar_square_uses_libm_pow_not_multiply():
    """numpy's float64 scalar ``**2`` is libm pow; the kernel must follow it, not ``x * x``."""
    rng = np.random.default_rng(2)
    n = 3
    base = _geometry(rng, n, 1, 0, 0)
    u = np.zeros(n)
    mismatch = 0
    for _ in range(4000):
        geometry = dict(base)
        geometry["Gw_all"] = rng.uniform(1, 2, (1, 2, n))
        geometry["T0"] = np.eye(n)
        u = rng.uniform(1, 2, n)
        constitutive = np.eye(3)
        want = cc.elastic_increment_reference(u, geometry, lambda: constitutive, True)
        got = cc.fused_elastic_increment(u, geometry, constitutive, True)
        assert got is not None
        mismatch += any(a.tobytes() != b.tobytes() for a, b in zip(got, want))
    assert mismatch == 0


def test_fused_backend_flag_is_authority_guarded():
    from anysolver import prepared_static_q4 as q
    q.require_q4_kernel_authority()
    names = {row[0] for row in q._NATIVE_KERNEL_FACTS}
    assert {"fused_shell_zero_tangent", "fused_elastic_increment", "_mm", "_tc"} <= names
    assert {row[0] for row in q._CONTRACTION_FACTS} >= {
        "shell_zero_tangent", "fused_elastic_increment", "elastic_increment_reference",
        "_shell_zero_tangent_reference", "_fused_array", "_fused_scalar"}
    cc._USE_FUSED = False
    try:
        with pytest.raises(Exception, match="authority"):
            q.require_q4_kernel_authority()
    finally:
        cc._USE_FUSED = True
    q.require_q4_kernel_authority()
