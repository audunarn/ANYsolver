"""Experimental bounded sparse congruence-residual positivity check for Q6.

The factor and inverse columns are candidates. The original represented matrix,
not the rounded symmetric factorization input, is the proof target. This is a
source-level feasibility tool until its compiled arithmetic and full evidence
contract receive independent qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import numba
import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as certificate
from scripts._b3_e4_f03_q6_interval_kernel import compiled_product_bounds


@dataclass(frozen=True, slots=True)
class PositivityIntervalBudget:
    sparse_budget: certificate.SparseBudget
    max_product_paths: int
    max_pattern_nnz: int

    def __post_init__(self):
        if (type(self.sparse_budget) is not certificate.SparseBudget or
                type(self.max_product_paths) is not int or
                self.max_product_paths <= 0 or
                type(self.max_pattern_nnz) is not int or
                self.max_pattern_nnz <= 0):
            raise ValueError("explicit positive Q6 positivity budgets required")


@numba.njit(cache=False, fastmath=False)
def _residual_norms(k_indptr, k_indices, k_data,
                    l_indptr, l_indices, l_data, diagonal,
                    p_indptr, p_indices):
    n = len(l_indptr)-1
    row_sums = np.zeros(n, dtype=np.float64)
    column_sums = np.zeros(n, dtype=np.float64)
    maximum = 0.
    for row in range(n):
        k_pointer = k_indptr[row]
        for pattern_pointer in range(p_indptr[row], p_indptr[row+1]):
            column = p_indices[pattern_pointer]
            while k_pointer < k_indptr[row+1] and k_indices[k_pointer] < column:
                k_pointer += 1
            target = 0.
            if k_pointer < k_indptr[row+1] and k_indices[k_pointer] == column:
                target = k_data[k_pointer]
            left = l_indptr[row]
            right = l_indptr[column]
            low = 0.
            high = 0.
            while left < l_indptr[row+1] and right < l_indptr[column+1]:
                left_index = l_indices[left]
                right_index = l_indices[right]
                if left_index < right_index:
                    left += 1
                elif right_index < left_index:
                    right += 1
                else:
                    a = l_data[left]
                    b = l_data[right]
                    if a != 0. and b != 0.:
                        first = a*diagonal[left_index]
                        first_low = np.nextafter(first, -np.inf)
                        first_high = np.nextafter(first, np.inf)
                        if b >= 0.:
                            term_low = np.nextafter(first_low*b, -np.inf)
                            term_high = np.nextafter(first_high*b, np.inf)
                        else:
                            term_low = np.nextafter(first_high*b, -np.inf)
                            term_high = np.nextafter(first_low*b, np.inf)
                        low = np.nextafter(low+term_low, -np.inf)
                        high = np.nextafter(high+term_high, np.inf)
                    left += 1
                    right += 1
            residual_low = np.nextafter(target-high, -np.inf)
            residual_high = np.nextafter(target-low, np.inf)
            bound = max(abs(residual_low), abs(residual_high))
            row_sums[row] = np.nextafter(row_sums[row]+bound, np.inf)
            column_sums[column] = np.nextafter(column_sums[column]+bound, np.inf)
            maximum = max(maximum, bound)
    return row_sums, column_sums, maximum


def _permutation(value, order: int) -> np.ndarray:
    if (type(value) not in (tuple, list, np.ndarray) or len(value) != order or
            any(not (type(item) is int or isinstance(item, np.integer))
                for item in value)):
        raise ValueError("complete Q6 factor permutation required")
    permutation = np.asarray(value, dtype=np.int64)
    if not np.array_equal(np.sort(permutation), np.arange(order)):
        raise ValueError("invalid Q6 factor permutation")
    return permutation.copy()


def certify_positive(original, lower, diagonal, permutation,
                     inverse_blocks, *, budget: PositivityIntervalBudget) -> dict:
    """Bound x.T original x using a supplied sparse L,D congruence candidate."""
    if type(budget) is not PositivityIntervalBudget:
        raise ValueError("explicit Q6 positivity interval budget required")
    k = certificate.validate_sparse(original, budget.sparse_budget)
    l = certificate.validate_sparse(lower, budget.sparse_budget)
    n = k.shape[0]
    if (l.shape != k.shape or type(diagonal) is not np.ndarray or
            diagonal.dtype != np.float64 or diagonal.shape != (n,) or
            not np.isfinite(diagonal).all() or np.any(diagonal <= 0) or
            not np.array_equal(l.diagonal(), np.ones(n)) or
            sparse.triu(l, k=1).nnz):
        raise ValueError("finite positive unit-lower congruence candidate required")
    if n > 10_000:
        raise ValueError("Q6 positivity order exceeds reviewed integer-pattern domain")
    diagonal = diagonal.copy()
    order = _permutation(permutation, n)
    column_counts = np.diff(l.tocsc().indptr).astype(np.int64)
    paths = sum(int(count)**2 for count in column_counts)
    if (paths > budget.max_product_paths or
            paths + int(k.nnz) > budget.max_pattern_nnz):
        raise ValueError("Q6 positivity product/pattern preflight cap exceeded")
    inverse = certificate.certificate_a(
        l, inverse_blocks, budget.sparse_budget,
        interval_kernel="compiled_experimental")
    if inverse.get("status") != "CONDITION_BOUND_ONLY":
        return {"status": "HOLD", "reason": "triangular inverse candidate unverified",
                "inverse": inverse}
    k_permuted = k[order, :][:, order].tocsr()
    k_permuted.sum_duplicates()
    k_permuted.sort_indices()
    lp = l.copy()
    lp.data = np.ones(lp.nnz, dtype=np.int32)
    pattern = (lp @ lp.T).tocsr()
    kp = k_permuted.copy()
    kp.data = np.ones(kp.nnz, dtype=np.int32)
    pattern = (pattern + kp).tocsr()
    pattern.sum_duplicates()
    pattern.sort_indices()
    if pattern.nnz > budget.max_pattern_nnz:
        raise ValueError("Q6 positivity observed pattern cap exceeded")
    # Verify the active arithmetic mode adjacent to the compiled residual
    # calculation. This fixed input is never a proof operand.
    compiled_product_bounds(sparse.csr_matrix([[1.]]), np.ones((1, 1)))
    rows, columns, maximum = _residual_norms(
        k_permuted.indptr, k_permuted.indices, k_permuted.data,
        l.indptr, l.indices, l.data, diagonal,
        pattern.indptr, pattern.indices)
    if not (np.isfinite(rows).all() and np.isfinite(columns).all() and
            np.isfinite(maximum)):
        raise ArithmeticError("nonfinite Q6 congruence residual enclosure")
    r_inf = float(np.max(rows))
    r_one = float(np.max(columns))
    b_one = float(inverse["inverse_one_upper"])
    b_inf = float(inverse["inverse_infinity_upper"])
    dmin = float(np.min(diagonal))
    ratio_squared = ((Fraction.from_float(b_one) *
                      Fraction.from_float(b_inf) / Fraction.from_float(dmin))**2 *
                     Fraction.from_float(r_one) * Fraction.from_float(r_inf))
    return {
        "status": "POSITIVE_QUADRATIC_FORM" if ratio_squared < 1 else "HOLD",
        "reason": None if ratio_squared < 1 else "congruence residual bound not contractive",
        "matrix_order": n,
        "matrix_nnz": int(k.nnz),
        "lower_nnz": int(l.nnz),
        "product_paths": paths,
        "residual_pattern_nnz": int(pattern.nnz),
        "residual_one_upper": r_one,
        "residual_infinity_upper": r_inf,
        "residual_entry_upper": float(maximum),
        "diagonal_minimum": dmin,
        "inverse_one_upper": b_one,
        "inverse_infinity_upper": b_inf,
        "strict_margin_squared_numerator": (1-ratio_squared).numerator,
        "strict_margin_squared_denominator": (1-ratio_squared).denominator,
        "inverse": inverse,
        "scientific_registration": False,
    }
