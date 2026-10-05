"""G0 F07 small conservative descriptor feasibility, not production modes."""

from __future__ import annotations

import json

import numpy as np
from scipy import linalg, sparse
from scipy.sparse.linalg import spsolve


def main() -> int:
    k = np.array([[3., -1., .2], [-1., 4., .1], [.2, .1, 2.]])
    m = np.diag([2., 1., 0.])
    c = np.array([[1., -1., 0.]])
    a = np.block([[k, c.T], [c, np.zeros((1, 1))]])
    b = np.block([[m, np.zeros((3, 1))], [np.zeros((1, 3)), np.zeros((1, 1))]])
    values, vectors = linalg.eig(a, b)
    finite = np.flatnonzero(np.isfinite(values))
    expected = (5. - .3**2 / 2.) / 3.
    assert len(finite) == 1 and np.isinf(values).sum() == 3
    index = finite[0]
    value = float(values[index].real)
    vector = vectors[:, index].real
    vector /= np.linalg.norm(vector[:2])
    equation = a @ vector - value * b @ vector
    equation_error = float(np.linalg.norm(equation) /
                           max(1., np.linalg.norm(a @ vector),
                               abs(value) * np.linalg.norm(b @ vector)))
    constraint_error = float(np.linalg.norm(c @ vector[:3]))
    physical_mass = float(vector[:3] @ m @ vector[:3])
    rhs = np.array([1., -2., .5, 0.])
    shift = a - b
    sparse_result = spsolve(sparse.csc_matrix(shift), rhs)
    dense_result = np.linalg.solve(shift, rhs)
    sparse_error = float(np.linalg.norm(sparse_result - dense_result) /
                         max(1., np.linalg.norm(dense_result)))
    status = (abs(value - expected) / expected <= 1e-12
              and equation_error <= 1e-12 and constraint_error <= 1e-12
              and physical_mass > 0. and sparse_error <= 1e-12)
    print(json.dumps({"case": "G0_F07_DESCRIPTOR_V1", "status": "diagnostic_pass" if status else "failed",
                      "eigenvalue": value, "expected": expected,
                      "finite_modes": int(len(finite)), "infinite_modes": int(np.isinf(values).sum()),
                      "equation_error": equation_error, "constraint_error": constraint_error,
                      "physical_mass": physical_mass, "sparse_error": sparse_error}, sort_keys=True))
    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())
