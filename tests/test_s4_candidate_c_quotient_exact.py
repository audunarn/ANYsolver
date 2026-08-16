from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases/s4_candidate_c_quotient_cases.json"
A2 = ROOT / "docs/reference_cases/s4_candidate_a_open_a2_certificate.json"


def _f(value: int | str | Fraction) -> Fraction:
    return Fraction(value)


def _dot(left: list[Fraction], right: list[Fraction]) -> Fraction:
    return sum((a * b for a, b in zip(left, right)), Fraction(0))


def _norm2(values: list[Fraction]) -> Fraction:
    return _dot(values, values)


def _zeros(rows: int, columns: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _maps(n: int, *, clamped: bool) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    if clamped:
        difference = _zeros(n - 1, n)
        unsigned = _zeros(n - 1, n)
        for node in range(1, n):
            difference[node - 1][node - 1] = -1
            difference[node - 1][node] = 1
            unsigned[node - 1][node - 1] = 1
            unsigned[node - 1][node] = 1
        return difference, unsigned
    incidence = _zeros(n + 1, n)
    unsigned = _zeros(n + 1, n)
    for cell in range(n):
        incidence[cell][cell] = -1
        incidence[cell + 1][cell] = 1
        unsigned[cell][cell] = 1
        unsigned[cell + 1][cell] = 1
    return incidence, unsigned


def _matvec(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [_dot(row, vector) for row in matrix]


def _kron_vector(left: list[Fraction], right: list[Fraction]) -> list[Fraction]:
    return [a * b for a in left for b in right]


def _kron_action(
    left_matrix: list[list[Fraction]],
    right_matrix: list[list[Fraction]],
    vector: list[Fraction],
    n: int,
) -> list[Fraction]:
    grid = [vector[row * n : (row + 1) * n] for row in range(n)]
    return [
        sum(
            (
                left_matrix[row][i]
                * right_matrix[column][j]
                * grid[i][j]
                for i in range(n)
                for j in range(n)
            ),
            Fraction(0),
        )
        for row in range(len(left_matrix))
        for column in range(len(right_matrix))
    ]


def _clamped_action(
    alpha: list[Fraction], beta: list[Fraction], n: int
) -> tuple[list[Fraction], list[Fraction], list[Fraction]]:
    difference, unsigned = _maps(n, clamped=True)
    u = _kron_action(difference, unsigned, alpha, n)
    v = _kron_action(unsigned, difference, alpha, n)
    psi_alpha = _kron_action(unsigned, unsigned, alpha, n)
    psi_beta = _kron_action(difference, difference, beta, n)
    psi = [a + b / 3 for a, b in zip(psi_alpha, psi_beta)]
    return u, v, psi


def _zero(values: tuple[list[Fraction], ...] | list[Fraction]) -> bool:
    if isinstance(values, tuple):
        return all(_zero(value) for value in values)
    return not any(values)


def _integral_power(power: int) -> Fraction:
    return Fraction(0) if power % 2 else Fraction(2, power + 1)


def test_normalized_a2_local_mass_and_rs_row_are_exact() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    assert cases["candidate"]["multiplier_basis"] == [
        {"coefficient": "1/2", "polynomial": "1"},
        {"coefficient": "3/2", "polynomial": "rs"},
    ]
    a = Fraction(7, 5)
    mass_one = a * a * Fraction(1, 4) * _integral_power(0) ** 2
    mass_rs = a * a * Fraction(9, 4) * _integral_power(2) ** 2
    cross = a * a * Fraction(3, 4) * _integral_power(1) ** 2
    assert (mass_one, mass_rs, cross) == (a * a, a * a, 0)

    signs = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    # Node order is bl, br, tr, tl.  Integral(rs*N_i)=sign_r*sign_s/9.
    rs_row = [
        3 * a * a * Fraction(sign_r * sign_s, 9)
        for sign_r, sign_s in signs
    ]
    assert rs_row == [a * a / 3, -a * a / 3, a * a / 3, -a * a / 3]

    accepted = json.loads(A2.read_text(encoding="utf-8"))
    accepted_row = [
        Fraction(value)
        for value in accepted["counterexample"]["local_rows"]["normalized_rs_drill"]
    ]
    assert accepted_row == [Fraction(1, 3), Fraction(-1, 3), Fraction(1, 3), Fraction(-1, 3)]
    zero = [Fraction(0)] * 3
    constant_row = (
        [Fraction(-1, 2), Fraction(1, 2), *zero, Fraction(1)]
        + [Fraction(-1, 2), Fraction(-1, 2), *zero, Fraction(1)]
        + [Fraction(1, 2), Fraction(-1, 2), *zero, Fraction(1)]
        + [Fraction(1, 2), Fraction(1, 2), *zero, Fraction(1)]
    )
    assert constant_row == [
        Fraction(value)
        for value in accepted["counterexample"]["local_rows"]["normalized_1_full"]
    ]


def test_free_all_n_witness_has_exact_decaying_bound() -> None:
    prior: Fraction | None = None
    for n in range(1, 65):
        incidence, _ = _maps(n, clamped=False)
        x = [Fraction((index + 1) * (n - index)) for index in range(n)]
        norm = _norm2(x)
        action = _norm2(_matvec(incidence, x))
        assert norm == Fraction(n * (n + 1) * (n + 2) * (n * n + 2 * n + 2), 30)
        assert action == Fraction(n * (n + 1) * (n + 2), 3)
        bound = action / norm
        assert bound == Fraction(10, n * n + 2 * n + 2)
        if prior is not None:
            assert bound < prior
        prior = bound
    assert Fraction(10, 64 * 64 + 2 * 64 + 2) < Fraction(1, 400)


def test_clamped_witness_is_in_the_complete_quotient_complement() -> None:
    for n in (3, 4, 8, 16, 32):
        difference, unsigned = _maps(n, clamped=True)
        centre = Fraction(n - 1, 2)
        r = [Fraction(index) - centre for index in range(n)]
        x = [value * value - Fraction(n * n - 1, 12) for value in r]
        one = [Fraction(1) for _ in range(n)]
        z = [Fraction((-1) ** index) for index in range(n)]
        beta = _kron_vector(x, x)
        zero_alpha = [Fraction(0) for _ in range(n * n)]

        assert sum(x, Fraction(0)) == 0
        assert _dot(x, r) == 0
        assert _matvec(difference, r) == [Fraction(1)] * (n - 1)
        assert _matvec(unsigned, one) == [Fraction(2)] * (n - 1)
        assert _matvec(unsigned, z) == [Fraction(0)] * (n - 1)

        # Zero mean proves x is in range(D^T), hence beta is orthogonal to the
        # complete ker(D tensor D).  Small meshes also enumerate its exact
        # 2n-1 basis independently.
        if n <= 8:
            standard = [
                [Fraction(index == column) for index in range(n)]
                for column in range(n)
            ]
            beta_kernel = [_kron_vector(one, vector) for vector in standard]
            beta_kernel.extend(_kron_vector(vector, one) for vector in standard[:-1])
            assert len(beta_kernel) == 2 * n - 1
            assert all(
                _zero(_kron_action(difference, difference, vector, n))
                for vector in beta_kernel
            )
            assert all(_dot(beta, vector) == 0 for vector in beta_kernel)

        checkerboard_alpha = _kron_vector(z, z)
        assert _zero(_clamped_action(checkerboard_alpha, zero_alpha, n))
        mixed_alpha = _kron_vector(one, one)
        mixed_beta = [-12 * value for value in _kron_vector(r, r)]
        assert _zero(_clamped_action(mixed_alpha, mixed_beta, n))
        assert _dot(beta, mixed_beta) == 0

        quotient_action = _kron_action(difference, difference, beta, n)
        assert any(quotient_action)
        assert _norm2(x) == Fraction(n * (n * n - 1) * (n * n - 4), 180)
        assert _norm2(_matvec(difference, x)) == Fraction(n * (n - 1) * (n - 2), 3)


def test_clamped_quotient_bound_tends_exactly_to_zero() -> None:
    expected = {
        4: Fraction(1),
        8: Fraction(1, 3),
        16: Fraction(5, 51),
        32: Fraction(5, 187),
    }
    observed = {
        n: Fraction(30, (n + 1) * (n + 2))
        for n in expected
    }
    assert observed == expected
    assert list(observed.values()) == sorted(observed.values(), reverse=True)
    assert Fraction(30, (1024 + 1) * (1024 + 2)) < Fraction(1, 30000)


def test_quotient_changes_no_primal_constraint_identity() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    candidate = cases["candidate"]
    assert candidate["primal_operator"] == "byte_equal_candidate_a_a2_C"
    assert candidate["quotient"] == "Lambda/ker(C_adm^T)"
    assert candidate["representative"] == "minimum_physical_L2"
    assert all(value is False for value in cases["exclusions"].values())
