"""Bounded outward interval Schur proof for a sparse symmetric representative.

Development primitive, not a solver tangent repair or F03 acceptance. A factor
producer supplies only ordering and a fill candidate. Every initial entry and
every elimination clique must be present; no cancellation drops interval fill.
Positive interval pivots prove the stated shifted lower-triangle completion
positive. They do not alone bound error to a different mechanical operator.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Context, Decimal, ROUND_FLOOR, ROUND_CEILING, Underflow, Subnormal
import time

import numpy as np
from scipy import sparse
from scripts._b3_e4_f03_sparse_certificate import (
    SparseBudget, validate_sparse, check_arithmetic,
)


@dataclass(frozen=True)
class IntervalBudget:
    max_order: int = 2400
    max_pattern_nnz: int = 1_000_000
    max_clique_entries: int = 250_000
    max_updates: int = 50_000_000
    max_workspace_bytes: int = 384 * 1024**2
    max_seconds: int = 120

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ValueError("explicit positive integer interval budgets required")


def down(value):
    result = np.nextafter(value, -np.inf)
    if not np.isfinite(result).all():
        raise ArithmeticError("nonfinite outward lower bound; no certificate")
    return result


def up(value):
    result = np.nextafter(value, np.inf)
    if not np.isfinite(result).all():
        raise ArithmeticError("nonfinite outward upper bound; no certificate")
    return result


def sum_up(values):
    total = 0.
    for value in np.ravel(values):
        if value < 0 or not np.isfinite(value):
            raise ArithmeticError("finite nonnegative upper summands required")
        if value:
            total = float(up(total + float(value)))
    return total


def dot_interval(left, right):
    """Exact stored binary64 operands; outward elementary dot accumulation.

    Used only for bounded local inverse/graph residuals, never a global inverse.
    """
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[0] or a.shape[1] > 24:
        raise ValueError("bounded local dot dimension must be no greater than24")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("finite local operands required")
    lo = np.zeros((a.shape[0], b.shape[1])); hi = lo.copy()
    for k in range(a.shape[1]):
        product = a[:, k, None] * b[None, k, :]
        lo = down(lo + down(product)); hi = up(hi + up(product))
    return lo, hi


def product_quotient_bounds(alo, ahi, blo, bhi, dlo, dhi):
    """Enclose a*b/d for arbitrary numerator signs and a positive denominator."""
    if not 0 < dlo <= dhi:
        raise ArithmeticError("strictly positive pivot interval required")
    lower, upper = None, None
    for a in (alo, ahi):
        for b in (blo, bhi):
            product = a * b
            qlo, qhi = down(product), up(product)
            lower = qlo if lower is None else np.minimum(lower, qlo)
            upper = qhi if upper is None else np.maximum(upper, qhi)
    return down(np.minimum(lower / dlo, lower / dhi)), up(np.maximum(upper / dlo, upper / dhi))


def certify_shifted_lower(matrix, pattern, permutation, *, shift=0., budget=None):
    """Prove SPD of the exact lower completion after symmetric permutation/shift.

    A zero-crossing interval is HOLD; a strictly negative pivot is a certificate
    against SPD of this representative. Pattern failure is an error, never an
    accepted absence of fill. Original upper-triangle defects remain caller work.
    """
    started = time.monotonic()
    budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget or type(shift) not in (float, int) or not np.isfinite(shift) or shift < 0:
        raise ValueError("valid interval budget and finite nonnegative shift required")
    check_arithmetic()
    sb = SparseBudget(budget.max_order, budget.max_pattern_nnz, 1, budget.max_workspace_bytes)
    a = validate_sparse(matrix, sb)
    fill = validate_sparse(pattern, sb)
    n = a.shape[0]
    if fill.shape != a.shape:
        raise ValueError("square fill candidate shape differs")
    if (type(permutation) not in (tuple, list) or len(permutation) != n or
            any(type(v) is not int for v in permutation) or set(permutation) != set(range(n))):
        raise ValueError("complete symmetric new-to-old permutation required")
    fc = fill.tocoo()
    if np.any(fc.row < fc.col) or not np.array_equal(fill.diagonal(), np.ones(n)):
        raise ValueError("unit diagonal lower structural fill required")
    keys = np.sort(fc.row.astype(np.int64) * n + fc.col)
    columns = fill.tocsc()
    sizes = np.diff(columns.indptr) - 1
    update_counts = sizes.astype(np.int64) * (sizes + 1) // 2
    maximum = int(update_counts.max(initial=0)); updates = int(update_counts.sum())
    workspace = 128 * (a.nnz + fill.nnz + n) + 128 * maximum
    if maximum > budget.max_clique_entries or updates > budget.max_updates or workspace > budget.max_workspace_bytes:
        raise ValueError("interval fill/update/workspace ceiling exceeded before products")
    target = sparse.tril(a[permutation][:, permutation], format="coo")

    def locations(query):
        pos = np.searchsorted(keys, query)
        valid = pos < len(keys)
        if not np.all(valid) or not np.array_equal(keys[pos], query):
            raise ValueError("missing initial entry or elimination clique in fill candidate")
        return pos

    lo = np.zeros(len(keys)); hi = lo.copy()
    initial = locations(target.row.astype(np.int64) * n + target.col)
    lo[initial], hi[initial] = target.data, target.data
    diagonal = locations(np.arange(n, dtype=np.int64) * (n + 1))
    if shift:
        lo[diagonal] = down(lo[diagonal] - shift)
        hi[diagonal] = up(hi[diagonal] - shift)
    pivlo, pivhi = np.empty(n), np.empty(n)
    completed, status, stopping = 0, "POSITIVE_SHIFTED_LOWER_COMPLETION", None
    for j in range(n):
        if time.monotonic() - started > budget.max_seconds:
            raise TimeoutError("interval sparse proof time ceiling exceeded")
        dlow, dhigh = float(lo[diagonal[j]]), float(hi[diagonal[j]])
        pivlo[j], pivhi[j] = dlow, dhigh
        completed = j + 1
        if dlow <= 0:
            status = "NONPOSITIVE_REPRESENTATIVE" if dhigh < 0 else "HOLD_INTERVAL_PIVOT"
            stopping = j
            break
        rows = columns.indices[columns.indptr[j]:columns.indptr[j+1]]
        rows = rows[rows > j]
        if not len(rows):
            continue
        column = locations(rows.astype(np.int64) * n + j)
        ii, jj = np.tril_indices(len(rows))
        destinations = locations(rows[ii].astype(np.int64) * n + rows[jj])
        qlo, qhi = product_quotient_bounds(lo[column[ii]], hi[column[ii]],
            lo[column[jj]], hi[column[jj]], dlow, dhigh)
        lo[destinations] = down(lo[destinations] - qhi)
        hi[destinations] = up(hi[destinations] - qlo)
    return dict(status=status, target="exact stored binary64 LOWER completion after symmetric permutation minus shiftI",
        shift=float(shift), order=n, pattern_nnz=fill.nnz, update_count=updates,
        maximum_clique_entries=maximum, workspace_estimate_bytes=workspace,
        pivot_lower=pivlo[:completed].copy(), pivot_upper=pivhi[:completed].copy(),
        completed_pivots=completed, stopping_pivot=stopping, elapsed_seconds=time.monotonic()-started,
        budget=asdict(budget), limitations="Caller must bound C/kernel graph, mechanical operator and triangle errors; no qualification claim.")


def factor_pattern(matrix, *, budget=None):
    """SuperLU is an ordering/structural candidate only; it supplies no verdict."""
    budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget:
        raise ValueError("valid interval budget required before factor producer")
    owned = validate_sparse(matrix, SparseBudget(budget.max_order,
        budget.max_pattern_nnz, 1, budget.max_workspace_bytes))
    factor = sparse.linalg.splu(owned.tocsc(), permc_spec="MMD_AT_PLUS_A",
        diag_pivot_thresh=0., options={"SymmetricMode": True, "Equil": False})
    if not np.array_equal(factor.perm_r, factor.perm_c):
        raise ValueError("factor producer did not supply a symmetric permutation")
    # Current SciPy may expose factor buffers as sparse arrays. Normalize only
    # this trusted producer output; input validation remains strict/owned.
    pattern = sparse.csr_matrix(factor.L, copy=True)
    pattern.data[:] = 1.
    return pattern, np.argsort(factor.perm_r).tolist()


def complete_symbolic_pattern(matrix, permutation, *, budget=None):
    """Structural elimination closure, including numerically cancelled fill.

    Backend factors may omit exact-zero/cancelled entries. Interval elimination
    cannot do that: those entries can have nonzero enclosure widths. This bounded
    symbolic traversal uses the complete stored initial graph, never values or
    a positive-pivot assumption. It leaves the old missing-fill guard intact.
    """
    started = time.monotonic()
    budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget:
        raise ValueError('valid interval budget required')
    owned = validate_sparse(matrix, SparseBudget(budget.max_order,
        budget.max_pattern_nnz, 1, budget.max_workspace_bytes))
    n = owned.shape[0]
    if (type(permutation) not in (tuple, list) or len(permutation) != n or
            any(type(v) is not int for v in permutation) or set(permutation) != set(range(n))):
        raise ValueError('complete symmetric new-to-old permutation required')
    lower = sparse.tril(owned[permutation][:, permutation], format='csc')
    columns = [set(map(int, lower.indices[lower.indptr[j]:lower.indptr[j+1]])) | {j}
               for j in range(n)]
    nnz = sum(map(len, columns)); updates = 0
    for j in range(n):
        if time.monotonic()-started > budget.max_seconds:
            raise TimeoutError('symbolic closure time ceiling exceeded')
        neighbours = sorted(columns[j]-{j})
        clique = len(neighbours)*(len(neighbours)+1)//2
        updates += clique
        if (nnz > budget.max_pattern_nnz or clique > budget.max_clique_entries or
                updates > budget.max_updates or 512*nnz+128*clique > budget.max_workspace_bytes):
            raise ValueError('symbolic fill/update/workspace ceiling exceeded')
        for index, k in enumerate(neighbours):
            before = len(columns[k])
            columns[k].update(neighbours[index+1:])
            nnz += len(columns[k])-before
            if nnz > budget.max_pattern_nnz or 512*nnz+128*clique > budget.max_workspace_bytes:
                raise ValueError('symbolic fill/workspace ceiling exceeded')
    rows = []; cols = []
    for j, entries in enumerate(columns):
        row = sorted(entries); rows.extend(row); cols.extend([j]*len(row))
    return sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=owned.shape).tocsr()


def certify_decimal_lower(matrix, pattern, permutation, *, shift=0., budget=None):
    """Same proof target, fixed50-digit directed arithmetic, no tolerance change.

    Decimal.from_float stores the exact input. FLOOR/CEILING elementary
    operations enclose exact-real Schur steps without binary64 dependency-width
    accumulation. A width crossing zero remains HOLD. No backend pivot verdict.
    """
    started = time.monotonic(); budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget or not np.isfinite(shift) or shift < 0.:
        raise ValueError('valid finite nonnegative shift and budget required')
    sb = SparseBudget(budget.max_order, budget.max_pattern_nnz, 1, budget.max_workspace_bytes)
    a, fill = validate_sparse(matrix, sb), validate_sparse(pattern, sb)
    n = a.shape[0]
    if (fill.shape != a.shape or type(permutation) not in (tuple, list) or len(permutation) != n or
            any(type(v) is not int for v in permutation) or set(permutation) != set(range(n))):
        raise ValueError('complete symmetric permutation and matching square pattern required')
    fc = fill.tocoo()
    if np.any(fc.row < fc.col) or not np.array_equal(fill.diagonal(), np.ones(n)):
        raise ValueError('unit diagonal lower structural pattern required')
    keys = np.sort(fc.row.astype(np.int64)*n+fc.col)
    columns = fill.tocsc(); sizes = np.diff(columns.indptr)-1
    counts = sizes.astype(np.int64)*(sizes+1)//2
    maximum, updates = int(counts.max(initial=0)), int(counts.sum())
    workspace = 512*(a.nnz+fill.nnz+n)+512*maximum
    if maximum > budget.max_clique_entries or updates > budget.max_updates or workspace > budget.max_workspace_bytes:
        raise ValueError('decimal fill/update/workspace ceiling exceeded')
    def locations(query):
        pos = np.searchsorted(keys, query)
        if np.any(pos >= len(keys)) or np.any(keys[pos] != query):
            raise ValueError('missing initial entry or elimination clique in fill candidate')
        return pos
    lowctx = Context(prec=50, rounding=ROUND_FLOOR)
    highctx = Context(prec=50, rounding=ROUND_CEILING)
    for context in (lowctx, highctx):
        context.traps[Underflow] = context.traps[Subnormal] = True
    zero = Decimal(0); lo = [zero]*len(keys); hi = lo.copy()
    target = sparse.tril(a[permutation][:, permutation], format='coo')
    positions = locations(target.row.astype(np.int64)*n+target.col)
    for position, value in zip(positions, target.data, strict=True):
        lo[position] = hi[position] = Decimal.from_float(float(value))
    diagonal = locations(np.arange(n, dtype=np.int64)*(n+1))
    dshift = Decimal.from_float(float(shift))
    for position in diagonal:
        lo[position] = lowctx.subtract(lo[position], dshift)
        hi[position] = highctx.subtract(hi[position], dshift)
    pivlo, pivhi = [], []; status = 'POSITIVE_SHIFTED_LOWER_COMPLETION'; stopping = None
    for j in range(n):
        if time.monotonic()-started > budget.max_seconds:
            raise TimeoutError('decimal interval sparse proof time ceiling exceeded')
        dl, dh = lo[diagonal[j]], hi[diagonal[j]]
        pivlo.append(str(dl)); pivhi.append(str(dh))
        if dl <= zero:
            status = 'NONPOSITIVE_REPRESENTATIVE' if dh < zero else 'HOLD_INTERVAL_PIVOT'
            stopping = j; break
        rows = columns.indices[columns.indptr[j]:columns.indptr[j+1]]
        rows = rows[rows > j]
        column = locations(rows.astype(np.int64)*n+j)
        ii, jj = np.tril_indices(len(rows))
        destinations = locations(rows[ii].astype(np.int64)*n+rows[jj])
        for ia, ib, dest in zip(column[ii], column[jj], destinations, strict=True):
            endpoints = ((lo[ia], lo[ib]), (lo[ia], hi[ib]), (hi[ia], lo[ib]), (hi[ia], hi[ib]))
            pl = min(lowctx.multiply(left, right) for left, right in endpoints)
            ph = max(highctx.multiply(left, right) for left, right in endpoints)
            ql = min(lowctx.divide(pl, dl), lowctx.divide(pl, dh))
            qh = max(highctx.divide(ph, dl), highctx.divide(ph, dh))
            lo[dest] = lowctx.subtract(lo[dest], qh)
            hi[dest] = highctx.subtract(hi[dest], ql)
    return dict(status=status, target='exact stored binary64 LOWER completion after symmetric permutation minus shiftI',
        arithmetic='exact binary64 inputs; Decimal50 digits FLOOR/CEILING elementary operations',
        shift=float(shift), order=n, pattern_nnz=fill.nnz, update_count=updates,
        maximum_clique_entries=maximum, workspace_estimate_bytes=workspace,
        pivot_lower=np.asarray(pivlo), pivot_upper=np.asarray(pivhi),
        completed_pivots=len(pivlo), stopping_pivot=stopping, elapsed_seconds=time.monotonic()-started,
        budget=asdict(budget), limitations='Same caller mechanical/graph/triangle obligations; development only.')
