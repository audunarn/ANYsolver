"""Exact symbolic quotient-control identities for the Q1H campaign.

This module is intentionally independent of the binary64 point evaluator and
the outward interval implementation.  It reconstructs the frozen Q1F/Q1Y3
kinematics over ``QQ(p,q,u,v,sqrt(3))`` and exposes the square 18 by 18
control operator obtained after fixing the six degrees of freedom of node 1.

The operator contains the fourteen mixed-core coupling rows, the three
centre-Taylor drill rows, and the retained hourglass row.  Its nonsingularity
is the algebraic step used by the H quotient-kernel certificate; ordered
coercivity bounds are deliberately outside this module.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path

import sympy as sp
from sympy.polys.matrices import DomainMatrix


P, Q, U, V = sp.symbols("p q u v")
R, S = sp.symbols("r s")
SQRT3 = sp.sqrt(3)
GAUSS = (
    (-1 / SQRT3, -1 / SQRT3),
    (1 / SQRT3, -1 / SQRT3),
    (1 / SQRT3, 1 / SQRT3),
    (-1 / SQRT3, 1 / SQRT3),
)


def _shape(r: sp.Expr, s: sp.Expr) -> tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    r, s = sp.sympify(r), sp.sympify(s)
    n = sp.Matrix(
        (
            (1 - r) * (1 - s) / 4,
            (1 + r) * (1 - s) / 4,
            (1 + r) * (1 + s) / 4,
            (1 - r) * (1 + s) / 4,
        )
    )
    nr = sp.Matrix((-(1 - s) / 4, (1 - s) / 4, (1 + s) / 4, -(1 + s) / 4))
    ns = sp.Matrix((-(1 - r) / 4, -(1 + r) / 4, (1 + r) / 4, (1 - r) / 4))
    return n, nr, ns


def _jacobian(r: sp.Expr, s: sp.Expr) -> tuple[sp.Expr, sp.Expr, sp.Expr, sp.Expr, sp.Expr]:
    r, s = sp.sympify(r), sp.sympify(s)
    xr = 1 + U * s
    xs = P + U * r
    yr = V * s
    ys = Q + V * r
    det = sp.expand(xr * ys - xs * yr)
    return xr, xs, yr, ys, det


def _natural_shear(r: sp.Expr, s: sp.Expr, direction: int) -> sp.Matrix:
    r, s = sp.sympify(r), sp.sympify(s)
    n, nr, ns = _shape(r, s)
    derivative = nr if direction == 0 else ns
    x = sp.Matrix((-1 - P + U, 1 - P - U, 1 + P + U, -1 + P - U))
    y = sp.Matrix((-Q + V, -Q - V, Q + V, Q - V))
    xd = (x.T * derivative)[0]
    yd = (y.T * derivative)[0]
    row = sp.zeros(1, 20)
    for node in range(4):
        base = 5 * node
        row[0, base + 2] = derivative[node]
        row[0, base + 3] = -yd * n[node]
        row[0, base + 4] = xd * n[node]
    return row


def _compatible(r: sp.Expr, s: sp.Expr) -> tuple[sp.Matrix, sp.Expr]:
    r, s = sp.sympify(r), sp.sympify(s)
    _n, nr, ns = _shape(r, s)
    xr, xs, yr, ys, det = _jacobian(r, s)
    nx = (ys * nr - yr * ns) / det
    ny = (-xs * nr + xr * ns) / det
    result = sp.zeros(8, 20)
    for node in range(4):
        base = 5 * node
        result[0, base] = nx[node]
        result[1, base + 1] = ny[node]
        result[2, base] = ny[node]
        result[2, base + 1] = nx[node]
        result[3, base + 4] = nx[node]
        result[4, base + 3] = -ny[node]
        result[5, base + 4] = ny[node]
        result[5, base + 3] = -nx[node]
    gr = (1 - s) * _natural_shear(0, -1, 0) / 2 + (1 + s) * _natural_shear(0, 1, 0) / 2
    gs = (1 + r) * _natural_shear(1, 0, 1) / 2 + (1 - r) * _natural_shear(-1, 0, 1) / 2
    result[6, :] = (ys * gr - yr * gs) / det
    result[7, :] = (-xs * gr + xr * gs) / det
    return result, det


def _shape_hessian(r: sp.Expr, s: sp.Expr, node: int) -> tuple[sp.Expr, ...]:
    _n, nr, ns = _shape(r, s)
    nrs = sp.Rational(1 if node in (0, 2) else -1, 4)
    xr, xs, yr, ys, det = _jacobian(r, s)
    nx = sp.cancel((ys * nr[node] - yr * ns[node]) / det)
    ny = sp.cancel((-xs * nr[node] + xr * ns[node]) / det)
    common = nrs - U * nx - V * ny
    nx_r = sp.cancel(-yr * common / det)
    ny_r = sp.cancel(xr * common / det)
    nx_s = sp.cancel(ys * common / det)
    ny_s = sp.cancel(-xs * common / det)
    nxx = sp.cancel((nx_r * ys - nx_s * yr) / det)
    nxy = sp.cancel((-nx_r * xs + nx_s * xr) / det)
    nyx = sp.cancel((ny_r * ys - ny_s * yr) / det)
    nyy = sp.cancel((-ny_r * xs + ny_s * xr) / det)
    return nx, ny, nxx, sp.cancel((nxy + nyx) / 2), nyy


def h_factor_rows() -> sp.Matrix:
    """Return unweighted exact rows whose positive Gram sum is ``H``."""

    rows: list[sp.Matrix] = []
    for r, s in GAUSS:
        n, _nr, _ns = _shape(r, s)
        compatible20, _det = _compatible(r, s)
        compatible24 = sp.zeros(8, 24)
        for node in range(4):
            compatible24[:, 6 * node : 6 * node + 5] = compatible20[
                :, 5 * node : 5 * node + 5
            ]
        rows.extend(compatible24[row, :] for row in range(8))
        delta = sp.zeros(1, 24)
        delta_x = sp.zeros(1, 24)
        delta_y = sp.zeros(1, 24)
        for node in range(4):
            nx, ny, nxx, nxy, nyy = _shape_hessian(r, s, node)
            base = 6 * node
            delta[0, base] = ny / 2
            delta[0, base + 1] = -nx / 2
            delta[0, base + 5] = n[node]
            delta_x[0, base] = nxy / 2
            delta_x[0, base + 1] = -nxx / 2
            delta_x[0, base + 5] = nx
            delta_y[0, base] = nyy / 2
            delta_y[0, base + 1] = -nxy / 2
            delta_y[0, base + 5] = ny
        rows.extend((delta, delta_x, delta_y))
    return sp.Matrix.vstack(*rows).applyfunc(sp.cancel)


def analytical_rigid_matrix() -> sp.Matrix:
    x = (-1 - P + U, 1 - P - U, 1 + P + U, -1 + P - U)
    y = (-Q + V, -Q - V, Q + V, Q - V)
    result = sp.zeros(24, 6)
    for node in range(4):
        base = 6 * node
        result[base, 0] = 1
        result[base + 1, 1] = 1
        result[base + 2, 2] = 1
        result[base + 2, 3] = y[node]
        result[base + 3, 3] = 1
        result[base + 2, 4] = -x[node]
        result[base + 4, 4] = 1
        result[base, 5] = -y[node]
        result[base + 1, 5] = x[node]
        result[base + 5, 5] = 1
    return result


def h_factor_rigid_residuals() -> tuple[sp.Expr, ...]:
    residual = h_factor_rows() * analytical_rigid_matrix()
    return tuple(sp.cancel(value, extension=SQRT3) for value in residual)


@lru_cache(maxsize=1)
def h_polynomial_factor_rows() -> sp.Matrix:
    """Return the rational Gauss-coefficient basis for compatible+delta rows."""

    factors = h_factor_rows()
    signs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    transformed: list[sp.Matrix] = []
    for field in range(9):
        station_rows = []
        for gauss, (r, s) in enumerate(GAUSS):
            determinant = _jacobian(r, s)[-1]
            station_rows.append(
                (determinant * factors[11 * gauss + field, :]).applyfunc(
                    lambda value: sp.cancel(value, extension=SQRT3)
                )
            )
        for mode, scale in enumerate((1, SQRT3, SQRT3, 3)):
            weights = tuple((1, sr, ss, sr * ss)[mode] for sr, ss in signs)
            row = scale * sum(
                (weights[index] * station_rows[index] for index in range(4)),
                sp.zeros(1, 24),
            )
            transformed.append(
                row.applyfunc(lambda value: sp.cancel(value, extension=SQRT3))
            )
    result = sp.Matrix.vstack(*transformed)
    if any(value.has(SQRT3) for value in result):
        raise RuntimeError("Gauss coefficient transform did not eliminate sqrt(3)")
    return result


def h_quotient_minor_identity() -> dict[str, object]:
    rows = h_polynomial_factor_rows()
    membrane_rows = (0, 2, 4, 5, 8, 32, 33, 34, 35)
    membrane_columns = tuple(6 * node + component for node in range(1, 4) for component in (0, 1, 5))
    bending_rows = (12, 14, 16, 17, 20, 24, 26, 28, 29)
    bending_columns = tuple(6 * node + component for node in range(1, 4) for component in (2, 3, 4))
    domain = sp.QQ.poly_ring(P, Q, U, V)

    def determinant(selected_rows: tuple[int, ...], selected_columns: tuple[int, ...]) -> sp.Expr:
        minor = rows[list(selected_rows), list(selected_columns)]
        values = [
            [domain.from_sympy(minor[row, column]) for column in range(9)]
            for row in range(9)
        ]
        return sp.factor(DomainMatrix.from_list(values, domain).det().as_expr())

    membrane = determinant(membrane_rows, membrane_columns)
    bending = determinant(bending_rows, bending_columns)
    a, b = sp.symbols("a b")
    membrane_variation = sp.factor(membrane.subs({U: a + P * b, V: Q * b}))
    expected_membrane = (
        sp.Rational(64, 9)
        * Q**6
        * ((a + b) ** 2 - 3)
        * ((a - b) ** 2 - 3)
    )
    expected_bending = -128 * Q**5
    return {
        "bending_determinant": bending,
        "bending_residual": sp.cancel(bending - expected_bending),
        "bending_rows": bending_rows,
        "membrane_determinant": membrane,
        "membrane_residual": sp.cancel(membrane_variation - expected_membrane),
        "membrane_rows": membrane_rows,
        "membrane_variation_determinant": membrane_variation,
    }


def _tensor(xr: sp.Expr, xs: sp.Expr, yr: sp.Expr, ys: sp.Expr, a: int, b: int) -> sp.Matrix:
    return sp.Matrix(
        (
            (xr * xr, xs * xs, a * xr * xs),
            (yr * yr, ys * ys, a * yr * ys),
            (b * xr * yr, b * xs * ys, xr * ys + yr * xs),
        )
    )


def _stress_interpolation(r: sp.Expr, s: sp.Expr, det: sp.Expr) -> sp.Matrix:
    r, s = sp.sympify(r), sp.sympify(s)
    del det  # Stress interpolation has no determinant enrichment.
    r_bar = U / 3
    s_bar = (U * Q - P * V) / (3 * Q)
    transform = _tensor(1, P, 0, Q, 2, 1)
    shear = sp.Matrix(((1, P), (0, Q)))
    result = sp.zeros(8, 14)
    result[:, :8] = sp.eye(8)
    seed = sp.Matrix(((s - s_bar, 0), (0, r - r_bar), (0, 0)))
    varying = transform * seed
    result[0:3, 8:10] = varying
    result[3:6, 10:12] = varying
    shear_seed = sp.Matrix(((s - s_bar, 0), (0, r - r_bar)))
    result[6:8, 12:14] = shear * shear_seed
    return result


def core_coupling() -> sp.Matrix:
    """Return the exact 14 by 24 core coupling operator."""

    gq = sp.zeros(14, 20)
    for r, s in GAUSS:
        compatible, det = _compatible(r, s)
        stress = _stress_interpolation(r, s, det)
        # The compatible rows carry 1/det; multiplying first keeps the
        # cancellation explicit and avoids generic simplification as evidence.
        gq += (det * stress.T * compatible).applyfunc(sp.cancel)
    embedded = sp.zeros(14, 24)
    for node in range(4):
        embedded[:, 6 * node : 6 * node + 5] = gq[:, 5 * node : 5 * node + 5]
    return embedded.applyfunc(sp.cancel)


def centre_taylor() -> sp.Matrix:
    f0 = (sp.Rational(1, 4),) * 4
    fr = tuple(sp.Rational(value, 4) for value in (-1, 1, 1, -1))
    fs = tuple(sp.Rational(value, 4) for value in (-1, -1, 1, 1))
    frs = tuple(sp.Rational(value, 4) for value in (1, -1, 1, -1))
    result = sp.zeros(3, 24)
    jr = V
    js = U * Q - P * V
    for coordinate in range(24):
        node, component = divmod(coordinate, 6)
        ur = fr[node] if component == 0 else 0
        us = fs[node] if component == 0 else 0
        urs = frs[node] if component == 0 else 0
        vr = fr[node] if component == 1 else 0
        vs = fs[node] if component == 1 else 0
        vrs = frs[node] if component == 1 else 0
        d0 = f0[node] if component == 5 else 0
        dr = fr[node] if component == 5 else 0
        ds = fs[node] if component == 5 else 0
        n0 = -P * ur + us - Q * vr
        nr = -U * ur + urs - V * vr
        ns = -P * urs + U * us - Q * vrs + V * vs
        result[0, coordinate] = d0 + n0 / (2 * Q)
        result[1, coordinate] = dr + (nr * Q - n0 * jr) / (2 * Q**2)
        result[2, coordinate] = ds + (ns * Q - n0 * js) / (2 * Q**2)
    return result.applyfunc(sp.cancel)


def hourglass_row() -> sp.Matrix:
    x = sp.Matrix((-1 - P + U, 1 - P - U, 1 + P + U, -1 + P - U))
    y = sp.Matrix((-Q + V, -Q - V, Q + V, Q - V))
    xi = sp.Matrix((-1, 1, 1, -1))
    eta = sp.Matrix((-1, -1, 1, 1))
    alternating = sp.Matrix((1, -1, 1, -1))
    area = 4 * Q
    eta_y = (eta.T * y)[0]
    xi_y = (xi.T * y)[0]
    eta_x = (eta.T * x)[0]
    xi_x = (xi.T * x)[0]
    b1 = (eta_y * xi - xi_y * eta) / (4 * area)
    b2 = (-eta_x * xi + xi_x * eta) / (4 * area)
    gamma = (alternating - (alternating.T * x)[0] * b1 - (alternating.T * y)[0] * b2) / 4
    row = sp.zeros(1, 24)
    for node in range(4):
        row[0, 6 * node + 5] = sp.cancel(gamma[node])
    return row


def anchored_control_operator() -> sp.Matrix:
    full = core_coupling().col_join(centre_taylor()).col_join(hourglass_row())
    return full[:, 6:24]


@lru_cache(maxsize=1)
def variation_control_inverse_expressions() -> tuple[sp.Expr, ...]:
    """Return row-major exact inverse entries in ``p,q,a,b`` coordinates."""

    a, b = sp.symbols("a b")
    domain = DomainMatrix.from_Matrix(anchored_control_operator())
    numerator, denominator = domain.inv_den()
    inverse = (numerator.to_Matrix() / denominator.as_expr()).applyfunc(sp.cancel)
    inverse = inverse.subs({U: a + P * b, V: Q * b}).applyfunc(sp.cancel)
    return tuple(inverse)


@lru_cache(maxsize=1)
def variation_control_inverse_evaluator():
    """Compile the exact inverse DAG for scalar-like outward arithmetic."""

    a, b = sp.symbols("a b")
    return sp.lambdify((P, Q, a, b), variation_control_inverse_expressions(), modules="math")


def determinant_identity() -> tuple[sp.Expr, sp.Expr, bool]:
    determinant = sp.factor(DomainMatrix.from_Matrix(anchored_control_operator()).det().as_expr())
    expected = sp.Rational(32, 729) * Q**12
    residual = sp.cancel(determinant - expected)
    return determinant, residual, residual == 0


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--determinant-certificate", action="store_true")
    parser.add_argument("--h-kernel-certificate", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.determinant_certificate == args.h_kernel_certificate:
        parser.error("select exactly one certificate mode")
    if args.h_kernel_certificate:
        identity = h_quotient_minor_identity()
        rigid_residuals = h_factor_rigid_residuals()
        exact = (
            identity["membrane_residual"] == 0
            and identity["bending_residual"] == 0
            and all(value == 0 for value in rigid_residuals)
        )
        record = {
            "anchored_dimension": 18,
            "bending_determinant": str(identity["bending_determinant"]),
            "bending_residual": str(identity["bending_residual"]),
            "bending_rows": list(identity["bending_rows"]),
            "membrane_determinant": str(identity["membrane_determinant"]),
            "membrane_residual": str(identity["membrane_residual"]),
            "membrane_rows": list(identity["membrane_rows"]),
            "membrane_variation_determinant": str(
                identity["membrane_variation_determinant"]
            ),
            "registered_disk_bound": "(a+b)**2,(a-b)**2 <= 1/4 < 3",
            "rigid_factor_residual_nonzero_count": sum(
                value != 0 for value in rigid_residuals
            ),
            "rigid_range_authority": "Q1G_ESTABLISHED_NOT_REVISITED",
            "schema": "anysolver.s4.e4-pl-q1h-symbolic-h-kernel-v1",
            "status": "PASS" if exact else "FAIL",
        }
        payload = _canonical_bytes(record)
        if args.output is None:
            print(payload.decode(), end="")
        else:
            args.output.write_bytes(payload)
        return 0 if exact else 1
    determinant, residual, exact = determinant_identity()
    record = {
        "anchored_dimension": 18,
        "determinant": str(determinant),
        "expected": "32*q**12/729",
        "residual": str(residual),
        "schema": "anysolver.s4.e4-pl-q1h-symbolic-kernel-v1",
        "status": "PASS" if exact else "FAIL",
    }
    payload = _canonical_bytes(record)
    if args.output is None:
        print(payload.decode(), end="")
    else:
        args.output.write_bytes(payload)
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
