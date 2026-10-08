"""Independent planar Q1 edge-jump screen for the D1 cut-front mode.

This is a development discriminator, not a contact law or qualification run.
The reference Q4 grid is the one in d1_cut_front_shell_work.py.  Only its
pressure interpolation enters here; no ANYsolver geometry or solver kernel is
called.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from d1_cut_front_two_hat_limit import limit_matrix, null_coefficients


X = np.linspace(0.0, 2.0, 5)
Y = np.array([0.0, 1.0, 2.0])


def _nodal_pressure(theta: float) -> np.ndarray:
    coefficients = null_coefficients(sum(limit_matrix()))
    b = theta**2 / 2.0 - theta**3 / 3.0
    d = 0.25 + theta - theta**2 + theta**3 / 3.0
    beta = -b / d
    pressure = np.zeros((3, 5))
    for column, factor in ((2, coefficients[0]), (3, coefficients[1])):
        pressure[:, column] = factor * np.array((-beta / 2.0, beta, 1.0))
    return pressure.ravel()


def _shape_gradient(xi: float, eta: float, hx: float, hy: float) -> np.ndarray:
    return np.array((
        (-(1.0 - eta) / hx, -(1.0 - xi) / hy),
        ((1.0 - eta) / hx, -xi / hy),
        (eta / hx, xi / hy),
        (-eta / hx, (1.0 - xi) / hy),
    ))


def _cell_nodes(row: int, column: int) -> tuple[int, ...]:
    lower_left = 5 * row + column
    return (lower_left, lower_left + 1, lower_left + 6, lower_left + 5)


def edge_jump_matrix() -> np.ndarray:
    """Return sum h_n^3 integral [normal derivative Q1]^2 ds (m^2)."""
    matrix = np.zeros((15, 15))
    samples = ((0.5 - 0.5 / np.sqrt(3.0), 0.5),
               (0.5 + 0.5 / np.sqrt(3.0), 0.5))

    def add_edge(left, right, left_coordinate, right_coordinate,
                 axis: int, length: float, normal_size: float) -> None:
        for parameter, weight in samples:
            derivative = np.zeros(15)
            for cell, coordinate, sign in ((left, left_coordinate, 1.0),
                                           (right, right_coordinate, -1.0)):
                row, column = cell
                hx = X[column + 1] - X[column]
                hy = Y[row + 1] - Y[row]
                xi, eta = ((coordinate, parameter) if axis == 0
                           else (parameter, coordinate))
                gradient = _shape_gradient(xi, eta, hx, hy)[:, axis]
                derivative[list(_cell_nodes(row, column))] += sign * gradient
            matrix[:] += normal_size**3 * length * weight * np.outer(
                derivative, derivative,
            )

    for row in range(2):
        for column in range(1, 4):
            add_edge((row, column - 1), (row, column), 1.0, 0.0,
                     0, Y[row + 1] - Y[row], X[column] - X[column - 1])
    for column in range(4):
        add_edge((0, column), (1, column), 1.0, 0.0,
                 1, X[column + 1] - X[column], Y[1] - Y[0])
    return matrix


def screen() -> dict:
    matrix = edge_jump_matrix()
    eigenvalues = np.linalg.eigvalsh(matrix)
    if eigenvalues[0] < -1.0e-12 * max(eigenvalues[-1], 1.0):
        raise AssertionError("edge-jump form is not positive semidefinite")
    x, y = np.meshgrid(X, Y)
    preserved = {}
    for name, values in (("constant", np.ones_like(x)),
                         ("x", x), ("y", y), ("xy", x * y)):
        preserved[name] = float(np.linalg.norm(matrix @ values.ravel()))
        if preserved[name] > 1.0e-11 * max(np.linalg.norm(matrix), 1.0):
            raise AssertionError(f"{name} pressure is not in the jump nullspace")
    rows = []
    for theta in (0.1, 0.05, 0.025, 0.0125):
        pressure = _nodal_pressure(theta)
        jump = float(pressure @ matrix @ pressure)
        if not jump > 0.0:
            raise AssertionError("cut-front mode is not controlled")
        rows.append({"theta": theta, "jump_norm_squared_m2": jump})
    return {
        "method": "full-reference Q1 normal-gradient jump across shared Q4 edges",
        "status": "algebraic screen only; no physical law or coupled result",
        "matrix_minimum_eigenvalue": float(eigenvalues[0]),
        "matrix_maximum_eigenvalue": float(eigenvalues[-1]),
        "preserved_pressure_residual_norms": preserved,
        "two_hat_rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    result = screen()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"preserved": result["preserved_pressure_residual_norms"],
                      "jump": result["two_hat_rows"]}))
