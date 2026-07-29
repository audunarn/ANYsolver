"""Vectorized J2 plane-stress plasticity with isotropic hardening.

The return mapping follows the classical plane-stress projected algorithm
(Simo & Hughes).  In the eigenbasis of C*P the update decouples into two
scalar modes, so the plastic multiplier is found by a scalar Newton iteration
that runs simultaneously for every yielding integration point / thickness
layer (numpy arrays, no Python-level point loops).

When a tangent is requested for a nonlinear global solve, the return-map
residual is differentiated analytically with the implicit-function theorem.
The resulting algorithmic tangent includes the dependence of both the plastic
multiplier and the isotropic-hardening variable on total strain.  A central
finite-difference derivative of the same discrete update remains available as
an explicit qualification oracle and as an automatic fallback for
non-finite/ill-conditioned pathological states.

Conventions
-----------
Stress/strain vectors are [xx, yy, xy] with engineering shear strain.
The yield function is f = 1/2 sigma^T P sigma - 1/3 sigma_y(alpha)^2 with

    P = 1/3 [[ 2, -1, 0],
             [-1,  2, 0],
             [ 0,  0, 6]]

and alpha the equivalent plastic strain with rate
alpha_dot = lambda_dot * sqrt(2/3 sigma^T P sigma).
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Dict, Iterator, Tuple

import numpy as np

from .jit_compiler import njit

if TYPE_CHECKING:
    from .material_curves import DNVC208MaterialCurve

_P_MATRIX = np.array(
    [[2.0, -1.0, 0.0], [-1.0, 2.0, 0.0], [0.0, 0.0, 6.0]],
    dtype=float,
) / 3.0


@njit
def plane_stress_elastic_matrix(E: float, nu: float) -> np.ndarray:
    return E / (1.0 - nu**2) * np.array(
        [[1.0, nu, 0.0], [nu, 1.0, 0.0], [0.0, 0.0, (1.0 - nu) / 2.0]],
    )


_ANALYTICAL_TANGENT_CONDITION_LIMIT = 1.0e12
_ANALYTICAL_TANGENT_AMPLIFICATION_LIMIT = 1.0e8
_TANGENT_METHOD_OVERRIDE: ContextVar[str | None] = ContextVar(
    "anysolver_plane_stress_tangent_method",
    default=None,
)


class PlaneStressConvergenceError(RuntimeError):
    """Raised when the local plane-stress consistency solve does not converge."""


def _validate_plane_stress_inputs(
    strain: np.ndarray,
    plastic_strain: np.ndarray,
    alpha: np.ndarray,
    E: float,
    nu: float,
    max_iterations: int,
    tolerance: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float, int, float]:
    """Normalize and validate the shared constitutive-array contract."""
    strain_array = np.asarray(strain, dtype=float)
    plastic_array = np.asarray(plastic_strain, dtype=float)
    alpha_array = np.asarray(alpha, dtype=float)
    if strain_array.ndim != 2 or strain_array.shape[1:] != (3,):
        raise ValueError("strain must have shape (n_points, 3)")
    if plastic_array.shape != strain_array.shape:
        raise ValueError("plastic_strain must have the same shape as strain")
    if alpha_array.shape != (strain_array.shape[0],):
        raise ValueError("alpha must have shape (n_points,)")
    if np.any(~np.isfinite(strain_array)) or np.any(~np.isfinite(plastic_array)):
        raise ValueError("strain and plastic_strain must contain only finite values")
    if np.any(~np.isfinite(alpha_array)):
        raise ValueError("alpha must contain only finite values")
    if np.any(alpha_array < 0.0):
        raise ValueError("alpha must be nonnegative")

    modulus = float(E)
    poisson = float(nu)
    if not np.isfinite(modulus) or modulus <= 0.0:
        raise ValueError("E must be finite and positive")
    if not np.isfinite(poisson) or not (-1.0 < poisson < 0.5):
        raise ValueError("nu must be finite and satisfy -1 < nu < 0.5")
    if isinstance(max_iterations, (bool, np.bool_)):
        raise ValueError("max_iterations must be a positive integer")
    iterations = int(max_iterations)
    if iterations <= 0 or float(iterations) != float(max_iterations):
        raise ValueError("max_iterations must be a positive integer")
    local_tolerance = float(tolerance)
    if not np.isfinite(local_tolerance) or local_tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    return (
        strain_array,
        plastic_array,
        alpha_array,
        modulus,
        poisson,
        iterations,
        local_tolerance,
    )


def _normalize_tangent_method(tangent_method: str) -> str:
    method = str(tangent_method).strip().lower().replace("-", "_")
    if method in {"analytic", "automatic", "auto"}:
        method = "analytical"
    if method in {"finite_difference", "fd", "oracle"}:
        method = "numerical"
    if method not in {"analytical", "numerical"}:
        raise ValueError(
            "tangent_method must be 'analytical' or 'numerical' "
            f"(got {tangent_method!r})"
        )
    return method


@contextmanager
def plane_stress_tangent_method(tangent_method: str) -> Iterator[None]:
    """Temporarily override the tangent used by all plane-stress updates.

    This context-local diagnostic hook lets qualification run an unchanged
    global nonlinear model with the numerical oracle.  Normal production
    calls should use the default analytical tangent.  ``ContextVar`` keeps
    concurrent solver contexts isolated.
    """
    method = _normalize_tangent_method(tangent_method)
    token = _TANGENT_METHOD_OVERRIDE.set(method)
    try:
        yield
    finally:
        _TANGENT_METHOD_OVERRIDE.reset(token)


@njit
def _jit_flow_stress(
    eps_p: np.ndarray,
    sigma_prop: float,
    sigma_yield: float,
    sigma_yield_2: float,
    eps_p_y1: float,
    eps_p_y2: float,
    K: float,
    n: float,
    power_offset: float,
) -> np.ndarray:
    eps_p = np.maximum(eps_p, 0.0)
    slope_1 = (sigma_yield - sigma_prop) / eps_p_y1
    slope_2 = (sigma_yield_2 - sigma_yield) / (eps_p_y2 - eps_p_y1)
    part_1 = sigma_prop + slope_1 * eps_p
    part_2 = sigma_yield + slope_2 * (eps_p - eps_p_y1)

    res = np.zeros(eps_p.shape[0])
    for i in range(eps_p.shape[0]):
        val = eps_p[i]
        if val <= eps_p_y1:
            res[i] = part_1[i]
        elif val <= eps_p_y2:
            res[i] = part_2[i]
        else:
            res[i] = K * np.power(max(val + power_offset, 1.0e-12), n)
    return res


@njit
def _jit_flow_stress_scalar(
    eps_p: float,
    sigma_prop: float,
    sigma_yield: float,
    sigma_yield_2: float,
    eps_p_y1: float,
    eps_p_y2: float,
    K: float,
    n: float,
    power_offset: float,
) -> float:
    """Scalar flow stress used by the safeguarded consistency solve."""
    value = max(eps_p, 0.0)
    if value <= eps_p_y1:
        slope = (sigma_yield - sigma_prop) / eps_p_y1
        return sigma_prop + slope * value
    if value <= eps_p_y2:
        slope = (sigma_yield_2 - sigma_yield) / (eps_p_y2 - eps_p_y1)
        return sigma_yield + slope * (value - eps_p_y1)
    return K * np.power(max(value + power_offset, 1.0e-12), n)


@njit
def _jit_consistency_residual_scalar(
    plastic_multiplier: float,
    b1: float,
    b23: float,
    alpha_n: float,
    c_a: float,
    shear_modulus: float,
    sigma_prop: float,
    sigma_yield: float,
    sigma_yield_2: float,
    eps_p_y1: float,
    eps_p_y2: float,
    K: float,
    n: float,
    power_offset: float,
) -> Tuple[float, float]:
    """Return the scalar consistency residual and current flow stress."""
    d_a = 1.0 + c_a * plastic_multiplier
    d_b = 1.0 + 2.0 * shear_modulus * plastic_multiplier
    phi2 = b1**2 / (12.0 * d_a**2) + b23 / d_b**2
    g = 2.0 * np.sqrt(max(phi2 / 3.0, 1.0e-30))
    alpha_value = alpha_n + plastic_multiplier * g
    flow = _jit_flow_stress_scalar(
        alpha_value,
        sigma_prop,
        sigma_yield,
        sigma_yield_2,
        eps_p_y1,
        eps_p_y2,
        K,
        n,
        power_offset,
    )
    return phi2 - flow**2 / 3.0, flow


@njit
def _jit_hardening_modulus(
    eps_p: np.ndarray,
    sigma_prop: float,
    sigma_yield: float,
    sigma_yield_2: float,
    eps_p_y1: float,
    eps_p_y2: float,
    K: float,
    n: float,
    power_offset: float,
) -> np.ndarray:
    eps_p = np.maximum(eps_p, 0.0)
    slope_1 = (sigma_yield - sigma_prop) / eps_p_y1
    slope_2 = (sigma_yield_2 - sigma_yield) / (eps_p_y2 - eps_p_y1)

    res = np.zeros(eps_p.shape[0])
    for i in range(eps_p.shape[0]):
        val = eps_p[i]
        if val <= eps_p_y1:
            res[i] = slope_1
        elif val <= eps_p_y2:
            res[i] = slope_2
        else:
            base = max(val + power_offset, 1.0e-12)
            res[i] = K * n * np.power(base, n - 1.0)
    return res


@njit
def _jit_plane_stress_return_map(
    strain: np.ndarray,
    plastic_strain: np.ndarray,
    alpha: np.ndarray,
    E: float,
    nu: float,
    sigma_prop: float,
    sigma_yield: float,
    sigma_yield_2: float,
    eps_p_y1: float,
    eps_p_y2: float,
    K: float,
    n: float,
    power_offset: float,
    max_iterations: int = 30,
    tolerance: float = 1.0e-10,
    compute_tangent: bool = True,
) -> Tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    n_points = strain.shape[0]
    C = plane_stress_elastic_matrix(E, nu)
    C_inv = np.linalg.inv(C)
    G = E / (2.0 * (1.0 + nu))
    c_a = E / (3.0 * (1.0 - nu))

    sigma = (strain - plastic_strain) @ C.T
    sy_n = _jit_flow_stress(
        alpha, sigma_prop, sigma_yield, sigma_yield_2, eps_p_y1, eps_p_y2, K, n, power_offset
    )
    a1 = sigma[:, 0] + sigma[:, 1]
    a2 = sigma[:, 0] - sigma[:, 1]
    a3 = sigma[:, 2]
    phi2_trial = a1**2 / 12.0 + a2**2 / 4.0 + a3**2
    f_trial = phi2_trial - sy_n**2 / 3.0

    yielding = f_trial > tolerance * np.maximum(sy_n**2, 1.0)
    C_ep = np.zeros((n_points, 3, 3))
    if compute_tangent:
        for i in range(n_points):
            C_ep[i] = C
    new_plastic = plastic_strain.copy()
    new_alpha = alpha.copy()
    converged = np.ones(n_points, dtype=np.bool_)
    scaled_residual = np.zeros(n_points, dtype=float)

    if not np.any(yielding):
        return sigma, C_ep, new_plastic, new_alpha, converged, scaled_residual

    # Identify yielding indices
    yielding_indices = np.where(yielding)[0]
    n_yielding = yielding_indices.shape[0]

    b1 = a1[yielding]
    b2 = a2[yielding]
    b3 = a3[yielding]
    b23 = b2**2 / 4.0 + b3**2
    alpha_y = alpha[yielding]
    dl = np.zeros(n_yielding)

    for _ in range(max_iterations):
        dA = 1.0 + c_a * dl
        dB = 1.0 + 2.0 * G * dl
        phi2 = b1**2 / (12.0 * dA**2) + b23 / dB**2
        phi = np.sqrt(np.maximum(phi2, 1.0e-30))
        g = 2.0 * np.sqrt(np.maximum(phi2 / 3.0, 1.0e-30))
        alpha_new = alpha_y + dl * g
        sy = _jit_flow_stress(
            alpha_new, sigma_prop, sigma_yield, sigma_yield_2, eps_p_y1, eps_p_y2, K, n, power_offset
        )
        H = _jit_hardening_modulus(
            alpha_new, sigma_prop, sigma_yield, sigma_yield_2, eps_p_y1, eps_p_y2, K, n, power_offset
        )
        f = phi2 - sy**2 / 3.0

        all_scaled = True
        for i in range(n_yielding):
            if np.abs(f[i]) > tolerance * max(sy[i]**2, 1.0):
                all_scaled = False
                break
        if all_scaled:
            break

        d_phi2 = -2.0 * (b1**2 * c_a / (12.0 * dA**3) + 2.0 * G * b23 / dB**3)
        d_g = d_phi2 / (3.0 * np.maximum(np.sqrt(phi2 / 3.0), 1.0e-30))
        d_alpha = g + dl * d_g
        d_f = d_phi2 - (2.0 / 3.0) * sy * H * d_alpha

        # Safe division step
        for i in range(n_yielding):
            df_val = d_f[i]
            if np.abs(df_val) <= 1.0e-30:
                df_val = -1.0e-30 if df_val < 0.0 else 1.0e-30
            step = f[i] / df_val
            dl[i] = max(dl[i] - step, 0.0)

    # Newton is fast for ordinary increments but can stall at a piecewise
    # hardening corner or during severe impact increments. The consistency
    # residual is monotone for the supported isotropic-hardening curves, so a
    # bracketed bisection safely completes any unconverged point.
    for i in range(n_yielding):
        residual_i, flow_i = _jit_consistency_residual_scalar(
            dl[i],
            b1[i],
            b23[i],
            alpha_y[i],
            c_a,
            G,
            sigma_prop,
            sigma_yield,
            sigma_yield_2,
            eps_p_y1,
            eps_p_y2,
            K,
            n,
            power_offset,
        )
        if (
            np.isfinite(residual_i)
            and np.abs(residual_i) <= tolerance * max(flow_i**2, 1.0)
        ):
            continue

        lower = 0.0
        upper = max(dl[i], 1.0 / max(np.abs(E), 1.0))
        upper_residual, upper_flow = _jit_consistency_residual_scalar(
            upper,
            b1[i],
            b23[i],
            alpha_y[i],
            c_a,
            G,
            sigma_prop,
            sigma_yield,
            sigma_yield_2,
            eps_p_y1,
            eps_p_y2,
            K,
            n,
            power_offset,
        )
        for _ in range(100):
            if np.isfinite(upper_residual) and upper_residual <= 0.0:
                break
            upper *= 2.0
            upper_residual, upper_flow = _jit_consistency_residual_scalar(
                upper,
                b1[i],
                b23[i],
                alpha_y[i],
                c_a,
                G,
                sigma_prop,
                sigma_yield,
                sigma_yield_2,
                eps_p_y1,
                eps_p_y2,
                K,
                n,
                power_offset,
            )

        if not np.isfinite(upper_residual) or upper_residual > 0.0:
            dl[i] = upper
            continue

        midpoint = 0.5 * (lower + upper)
        for _ in range(100):
            midpoint = 0.5 * (lower + upper)
            midpoint_residual, midpoint_flow = _jit_consistency_residual_scalar(
                midpoint,
                b1[i],
                b23[i],
                alpha_y[i],
                c_a,
                G,
                sigma_prop,
                sigma_yield,
                sigma_yield_2,
                eps_p_y1,
                eps_p_y2,
                K,
                n,
                power_offset,
            )
            if (
                np.isfinite(midpoint_residual)
                and np.abs(midpoint_residual)
                <= tolerance * max(midpoint_flow**2, 1.0)
            ):
                break
            if not np.isfinite(midpoint_residual) or midpoint_residual > 0.0:
                lower = midpoint
            else:
                upper = midpoint
        dl[i] = midpoint

    dA = 1.0 + c_a * dl
    dB = 1.0 + 2.0 * G * dl
    sig_a = b1 / dA
    sig_b = b2 / dB
    tau = b3 / dB

    sigma_y_pts = np.zeros((n_yielding, 3))
    sigma_y_pts[:, 0] = (sig_a + sig_b) / 2.0
    sigma_y_pts[:, 1] = (sig_a - sig_b) / 2.0
    sigma_y_pts[:, 2] = tau

    for idx, i in enumerate(yielding_indices):
        sigma[i] = sigma_y_pts[idx]

    phi2 = sig_a**2 / 12.0 + sig_b**2 / 4.0 + tau**2
    new_alpha[yielding] = alpha_y + dl * 2.0 * np.sqrt(np.maximum(phi2 / 3.0, 1.0e-30))
    sy_final = _jit_flow_stress(
        new_alpha[yielding],
        sigma_prop,
        sigma_yield,
        sigma_yield_2,
        eps_p_y1,
        eps_p_y2,
        K,
        n,
        power_offset,
    )
    final_residual = phi2 - sy_final**2 / 3.0
    for idx, i in enumerate(yielding_indices):
        denominator = max(sy_final[idx] ** 2, 1.0)
        scaled_residual[i] = np.abs(final_residual[idx]) / denominator
        if (
            not np.isfinite(final_residual[idx])
            or scaled_residual[i] > tolerance
        ):
            converged[i] = False

    p_strain_yielding = strain[yielding] - sigma_y_pts @ C_inv.T
    for idx, i in enumerate(yielding_indices):
        new_plastic[i] = p_strain_yielding[idx]

    if not compute_tangent:
        return sigma, C_ep, new_plastic, new_alpha, converged, scaled_residual

    # Exact derivative of the discrete projected return map.
    #
    # In the invariant trial-stress basis b = [sx+sy, sx-sy, txy],
    # returned modes are
    #
    #   q = [b1/A, b2/B, b3/B],
    #   A = 1 + c_a*dl,  B = 1 + 2G*dl.
    #
    # The scalar consistency equation f(b, dl) = 0 therefore gives
    # d(dl)/db = -f_b/f_dl.  The chain T * dq/db * L * C maps the mode
    # derivative back to [sxx, syy, txy] versus engineering strain.
    H_final = _jit_hardening_modulus(
        new_alpha[yielding], sigma_prop, sigma_yield, sigma_yield_2, eps_p_y1, eps_p_y2, K, n, power_offset
    )
    T = np.array(
        [[0.5, 0.5, 0.0], [0.5, -0.5, 0.0], [0.0, 0.0, 1.0]]
    )
    L = np.array(
        [[1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [0.0, 0.0, 1.0]]
    )

    for idx, i in enumerate(yielding_indices):
        p = max(phi2[idx], 1.0e-30)
        sqrt_p = np.sqrt(p)
        g = 2.0 * np.sqrt(p / 3.0)
        dp_dl = -2.0 * (
            b1[idx] ** 2 * c_a / (12.0 * dA[idx] ** 3)
            + 2.0 * G * b23[idx] / dB[idx] ** 3
        )
        dg_dl = dp_dl / (np.sqrt(3.0) * sqrt_p)
        da_dl = g + dl[idx] * dg_dl
        df_dl = dp_dl - (2.0 / 3.0) * sy_final[idx] * H_final[idx] * da_dl

        dp_db = np.empty(3)
        dp_db[0] = b1[idx] / (6.0 * dA[idx] ** 2)
        dp_db[1] = b2[idx] / (2.0 * dB[idx] ** 2)
        dp_db[2] = 2.0 * b3[idx] / dB[idx] ** 2

        dl_db = np.empty(3)
        derivative_scale = (
            np.abs(dp_dl)
            + np.abs(
                (2.0 / 3.0)
                * sy_final[idx]
                * H_final[idx]
                * da_dl
            )
            + 1.0
        )
        local_derivative_valid = (
            np.isfinite(df_dl)
            and np.isfinite(g)
            and g > 1.0e-30
            and np.isfinite(dA[idx])
            and np.isfinite(dB[idx])
            and np.abs(dA[idx]) > 1.0e-14
            and np.abs(dB[idx]) > 1.0e-14
            and np.abs(df_dl) > 1.0e-14 * derivative_scale
        )
        for col in range(3):
            dg_db = dp_db[col] / (np.sqrt(3.0) * sqrt_p)
            da_db = dl[idx] * dg_db
            df_db = dp_db[col] - (2.0 / 3.0) * sy_final[idx] * H_final[idx] * da_db
            if local_derivative_valid:
                dl_db[col] = -df_db / df_dl
            else:
                dl_db[col] = np.nan

        dq_db = np.zeros((3, 3))
        dq_db[0, 0] = 1.0 / dA[idx]
        dq_db[1, 1] = 1.0 / dB[idx]
        dq_db[2, 2] = 1.0 / dB[idx]
        dq_dl = np.empty(3)
        dq_dl[0] = -c_a * b1[idx] / dA[idx] ** 2
        dq_dl[1] = -2.0 * G * b2[idx] / dB[idx] ** 2
        dq_dl[2] = -2.0 * G * b3[idx] / dB[idx] ** 2
        for row in range(3):
            for col in range(3):
                dq_db[row, col] += dq_dl[row] * dl_db[col]

        # T maps invariant returned modes to stress, while L maps trial
        # stress to the invariant basis.
        mode_tangent = T @ dq_db @ L
        material_tangent = mode_tangent @ C
        for r in range(3):
            for c in range(3):
                C_ep[i, r, c] = 0.5 * (
                    material_tangent[r, c] + material_tangent[c, r]
                )

    return sigma, C_ep, new_plastic, new_alpha, converged, scaled_residual


def _require_local_convergence(
    converged: np.ndarray,
    scaled_residual: np.ndarray,
    *,
    max_iterations: int,
) -> None:
    """Fail closed when any local consistency solve exhausted its iteration budget."""
    converged = np.asarray(converged, dtype=bool).reshape(-1)
    if np.all(converged):
        return
    residual = np.asarray(scaled_residual, dtype=float).reshape(-1)
    failed = np.flatnonzero(~converged)
    maximum = float(np.max(residual[failed])) if failed.size else float("nan")
    preview = ", ".join(str(int(index)) for index in failed[:8])
    suffix = "" if failed.size <= 8 else ", ..."
    raise PlaneStressConvergenceError(
        "Plane-stress return mapping did not satisfy the scaled yield "
        f"residual after {int(max_iterations)} iterations at point(s) "
        f"{preview}{suffix}; maximum scaled residual={maximum:.6g}."
    )


def plane_stress_return_map(
    strain: np.ndarray,
    plastic_strain: np.ndarray,
    alpha: np.ndarray,
    E: float,
    nu: float,
    curve: "DNVC208MaterialCurve",
    max_iterations: int = 30,
    tolerance: float = 1.0e-10,
    compute_tangent: bool = True,
    tangent_method: str = "analytical",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Map total strains to stresses, tangents and updated plastic state.

    ``tangent_method="analytical"`` (the default) implicitly differentiates
    the converged scalar consistency equation.  Invalid analytical rows
    automatically fall back to the numerical oracle.  Use
    ``tangent_method="numerical"`` to request that central-difference oracle
    explicitly for qualification and diagnosis.
    """
    (
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        max_iterations,
        tolerance,
    ) = _validate_plane_stress_inputs(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        max_iterations,
        tolerance,
    )
    override = _TANGENT_METHOD_OVERRIDE.get()
    method = (
        _normalize_tangent_method(override)
        if override is not None
        else _normalize_tangent_method(tangent_method)
    )

    if curve is None:
        C = plane_stress_elastic_matrix(E, nu)
        n_points = strain.shape[0]
        C_ep = np.broadcast_to(C, (n_points, 3, 3)).copy() if compute_tangent else np.zeros((n_points, 3, 3))
        sigma = (strain - plastic_strain) @ C.T
        return sigma, C_ep, plastic_strain.copy(), alpha.copy()

    (
        sigma,
        analytical_tangent,
        new_plastic,
        new_alpha,
        converged,
        scaled_residual,
    ) = _jit_plane_stress_return_map(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        float(curve.sigma_prop),
        float(curve.sigma_yield),
        float(curve.sigma_yield_2),
        float(curve.eps_p_y1),
        float(curve.eps_p_y2),
        float(curve.K),
        float(curve.n),
        float(curve._power_offset),
        max_iterations,
        tolerance,
        compute_tangent and method == "analytical",
    )
    _require_local_convergence(
        converged,
        scaled_residual,
        max_iterations=max_iterations,
    )
    if not compute_tangent:
        return sigma, analytical_tangent, new_plastic, new_alpha

    if method == "numerical":
        numerical_tangent = plane_stress_numerical_tangent(
            strain,
            plastic_strain,
            alpha,
            E,
            nu,
            curve,
            max_iterations=max_iterations,
            tolerance=tolerance,
        )
        return sigma, numerical_tangent, new_plastic, new_alpha

    fallback_mask = _analytical_tangent_fallback_mask(
        analytical_tangent, E=E, nu=nu
    )
    if np.any(fallback_mask):
        analytical_tangent[fallback_mask] = plane_stress_numerical_tangent(
            strain[fallback_mask],
            plastic_strain[fallback_mask],
            alpha[fallback_mask],
            E,
            nu,
            curve,
            max_iterations=max_iterations,
            tolerance=tolerance,
        )
    if np.any(~np.isfinite(analytical_tangent)):
        raise FloatingPointError(
            "Plane-stress tangent remained non-finite after the numerical fallback"
        )
    return sigma, analytical_tangent, new_plastic, new_alpha


def _analytical_tangent_fallback_mask(
    tangent: np.ndarray,
    *,
    E: float,
    nu: float,
    condition_limit: float = _ANALYTICAL_TANGENT_CONDITION_LIMIT,
    amplification_limit: float = _ANALYTICAL_TANGENT_AMPLIFICATION_LIMIT,
) -> np.ndarray:
    """Identify analytical tangent rows that require the numerical fallback."""
    tangent = np.asarray(tangent, dtype=float)
    if tangent.ndim != 3 or tangent.shape[1:] != (3, 3):
        raise ValueError("tangent must have shape (n_points, 3, 3)")
    fallback = ~np.all(np.isfinite(tangent), axis=(1, 2))
    try:
        elastic_eigenvalues = np.array(
            [
                float(E) / (1.0 - float(nu)),
                float(E) / (1.0 + float(nu)),
                float(E) / (2.0 * (1.0 + float(nu))),
            ],
            dtype=float,
        )
        elastic_magnitudes = np.abs(elastic_eigenvalues)
        elastic_norm = float(np.linalg.norm(elastic_magnitudes))
        elastic_condition = float(
            np.max(elastic_magnitudes)
            / max(np.min(elastic_magnitudes), np.finfo(float).tiny)
        )
    except (FloatingPointError, ValueError, ZeroDivisionError):
        return np.ones(tangent.shape[0], dtype=bool)
    if not np.isfinite(elastic_norm) or not np.isfinite(elastic_condition):
        return np.ones(tangent.shape[0], dtype=bool)
    # A large elastic condition number is diagnostic evidence, not by itself
    # proof that the analytical derivative is invalid. In particular, the
    # exact elastic tangent remains preferable to a differenced derivative
    # when nu approaches a stability boundary.
    _ = condition_limit
    tangent_norm = np.linalg.norm(tangent, axis=(1, 2))
    fallback |= tangent_norm > float(amplification_limit) * max(elastic_norm, 1.0)
    return fallback


def plane_stress_tangent_diagnostics(
    strain: np.ndarray,
    plastic_strain: np.ndarray,
    alpha: np.ndarray,
    E: float,
    nu: float,
    curve: "DNVC208MaterialCurve",
    max_iterations: int = 30,
    tolerance: float = 1.0e-10,
    oracle_step: float = 1.0e-7,
) -> Dict[str, Any]:
    """Compare analytical rows with the numerical oracle and report fallbacks."""
    (
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        max_iterations,
        tolerance,
    ) = _validate_plane_stress_inputs(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        max_iterations,
        tolerance,
    )
    (
        _stress,
        analytical,
        _plastic,
        _alpha,
        converged,
        scaled_residual,
    ) = _jit_plane_stress_return_map(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        float(curve.sigma_prop),
        float(curve.sigma_yield),
        float(curve.sigma_yield_2),
        float(curve.eps_p_y1),
        float(curve.eps_p_y2),
        float(curve.K),
        float(curve.n),
        float(curve._power_offset),
        max_iterations,
        tolerance,
        True,
    )
    _require_local_convergence(
        converged,
        scaled_residual,
        max_iterations=max_iterations,
    )
    fallback_mask = _analytical_tangent_fallback_mask(analytical, E=E, nu=nu)
    oracle = plane_stress_numerical_tangent(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        curve,
        max_iterations=max_iterations,
        tolerance=tolerance,
        step=oracle_step,
    )
    relative_errors = np.linalg.norm(analytical - oracle, axis=(1, 2)) / np.maximum(
        np.linalg.norm(oracle, axis=(1, 2)), 1.0
    )
    symmetry_errors = np.linalg.norm(
        analytical - np.swapaxes(analytical, 1, 2),
        axis=(1, 2),
    ) / np.maximum(np.linalg.norm(analytical, axis=(1, 2)), 1.0)
    return {
        "method": "analytical_implicit_consistent",
        "oracle": "central_finite_difference_discrete_return_map",
        "num_points": int(strain.shape[0]),
        "fallback_count": int(np.count_nonzero(fallback_mask)),
        "fallback_indices": np.flatnonzero(fallback_mask).astype(int).tolist(),
        "relative_errors": relative_errors.tolist(),
        "max_relative_error": float(np.max(relative_errors)) if relative_errors.size else 0.0,
        "symmetry_relative_errors": symmetry_errors.tolist(),
        "max_symmetry_relative_error": (
            float(np.max(symmetry_errors)) if symmetry_errors.size else 0.0
        ),
    }


def plane_stress_numerical_tangent(
    strain: np.ndarray,
    plastic_strain: np.ndarray,
    alpha: np.ndarray,
    E: float,
    nu: float,
    curve: "DNVC208MaterialCurve",
    max_iterations: int = 30,
    tolerance: float = 1.0e-10,
    step: float = 1.0e-7,
) -> np.ndarray:
    """Central-difference oracle for the exact discrete stress update."""
    (
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        max_iterations,
        tolerance,
    ) = _validate_plane_stress_inputs(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        max_iterations,
        tolerance,
    )
    step = float(step)
    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be finite and positive")

    n_points = int(strain.shape[0])
    if curve is None:
        return np.broadcast_to(
            plane_stress_elastic_matrix(E, nu),
            (n_points, 3, 3),
        ).copy()
    tangent = np.zeros((n_points, 3, 3), dtype=float)
    elastic = plane_stress_elastic_matrix(E, nu)
    for col in range(3):
        # Keep the perturbation stress scale bounded when the elastic matrix
        # is highly conditioned (for example nu -> -1+). This preserves the
        # local derivative and avoids driving the perturbed return maps many
        # orders of magnitude away from the base state.
        column_scale = float(np.linalg.norm(elastic[:, col]))
        effective_step = step * min(
            1.0,
            max(abs(float(E)), 1.0) / max(column_scale, 1.0),
        )
        if not np.isfinite(effective_step) or effective_step <= 0.0:
            raise ValueError(
                "Could not construct a finite numerical-tangent perturbation"
            )
        strain_plus = strain.copy()
        strain_minus = strain.copy()
        strain_plus[:, col] = strain[:, col] + effective_step
        strain_minus[:, col] = strain[:, col] - effective_step
        unchanged_plus = strain_plus[:, col] == strain[:, col]
        unchanged_minus = strain_minus[:, col] == strain[:, col]
        strain_plus[unchanged_plus, col] = np.nextafter(
            strain[unchanged_plus, col],
            np.inf,
        )
        strain_minus[unchanged_minus, col] = np.nextafter(
            strain[unchanged_minus, col],
            -np.inf,
        )
        denominator = strain_plus[:, col] - strain_minus[:, col]
        if np.any(~np.isfinite(denominator)) or np.any(denominator <= 0.0):
            raise ValueError(
                "Could not construct a representable numerical-tangent perturbation"
            )
        sigma_plus, _, _, _, plus_converged, plus_residual = _jit_plane_stress_return_map(
            strain_plus,
            plastic_strain,
            alpha,
            E,
            nu,
            float(curve.sigma_prop),
            float(curve.sigma_yield),
            float(curve.sigma_yield_2),
            float(curve.eps_p_y1),
            float(curve.eps_p_y2),
            float(curve.K),
            float(curve.n),
            float(curve._power_offset),
            max_iterations,
            tolerance,
            False,
        )
        _require_local_convergence(
            plus_converged,
            plus_residual,
            max_iterations=max_iterations,
        )
        sigma_minus, _, _, _, minus_converged, minus_residual = _jit_plane_stress_return_map(
            strain_minus,
            plastic_strain,
            alpha,
            E,
            nu,
            float(curve.sigma_prop),
            float(curve.sigma_yield),
            float(curve.sigma_yield_2),
            float(curve.eps_p_y1),
            float(curve.eps_p_y2),
            float(curve.K),
            float(curve.n),
            float(curve._power_offset),
            max_iterations,
            tolerance,
            False,
        )
        _require_local_convergence(
            minus_converged,
            minus_residual,
            max_iterations=max_iterations,
        )
        tangent[:, :, col] = (
            sigma_plus - sigma_minus
        ) / denominator[:, None]
    if np.any(~np.isfinite(tangent)):
        raise FloatingPointError("Numerical plane-stress tangent is non-finite")
    return tangent


def _finite_difference_algorithmic_tangent(
    strain: np.ndarray,
    plastic_strain: np.ndarray,
    alpha: np.ndarray,
    E: float,
    nu: float,
    curve: "DNVC208MaterialCurve",
    max_iterations: int = 30,
    tolerance: float = 1.0e-10,
    step: float = 1.0e-7,
) -> np.ndarray:
    """Backward-compatible private alias for the numerical tangent oracle."""
    return plane_stress_numerical_tangent(
        strain,
        plastic_strain,
        alpha,
        E,
        nu,
        curve,
        max_iterations=max_iterations,
        tolerance=tolerance,
        step=step,
    )


_LOBATTO_RULES = {
    3: (np.array([-1.0, 0.0, 1.0]), np.array([1.0, 4.0, 1.0]) / 3.0),
    5: (
        np.array([-1.0, -np.sqrt(3.0 / 7.0), 0.0, np.sqrt(3.0 / 7.0), 1.0]),
        np.array([1.0 / 10.0, 49.0 / 90.0, 32.0 / 45.0, 49.0 / 90.0, 1.0 / 10.0]),
    ),
    7: (
        np.array(
            [-1.0, -0.830223896278567, -0.468848793470714, 0.0,
             0.468848793470714, 0.830223896278567, 1.0]
        ),
        np.array(
            [0.047619047619048, 0.276826047361566, 0.431745381209863, 0.487619047619048,
             0.431745381209863, 0.276826047361566, 0.047619047619048]
        ),
    ),
    9: (
        np.array(
            [-1.0, -0.899757995411460, -0.677186279510738, -0.363117463826178, 0.0,
             0.363117463826178, 0.677186279510738, 0.899757995411460, 1.0]
        ),
        np.array(
            [0.027777777777778, 0.165495361560806, 0.274538712500162, 0.346428510973046,
             0.371519274376417, 0.346428510973046, 0.274538712500162, 0.165495361560806,
             0.027777777777778]
        ),
    ),
    11: (
        np.array(
            [-1.0, -0.934001430408059, -0.784483473663144, -0.565235326996205,
             -0.295758135586939, 0.0, 0.295758135586939, 0.565235326996205,
             0.784483473663144, 0.934001430408059, 1.0]
        ),
        np.array(
            [0.018181818181818, 0.109612273266995, 0.187169881780305, 0.248048104264028,
             0.286879124779008, 0.300217595455691, 0.286879124779008, 0.248048104264028,
             0.187169881780305, 0.109612273266995, 0.018181818181818]
        ),
    ),
}


def lobatto_layers(num_layers: int, thickness: float) -> Tuple[np.ndarray, np.ndarray]:
    """Through-thickness Gauss-Lobatto coordinates and weights.

    Lobatto rules include the surface points, where yielding starts first.
    Returns (z, w) with z in [-h/2, h/2] and sum(w) = h.
    """
    if num_layers not in _LOBATTO_RULES:
        raise ValueError(f"num_layers must be one of {sorted(_LOBATTO_RULES)}")
    points, weights = _LOBATTO_RULES[num_layers]
    return 0.5 * thickness * points, 0.5 * thickness * weights
