"""Sparse residual/triangular nonsingularity certificate, DEVELOPMENT ONLY.

No inertia or coercivity is inferred here. Caller must separately prove the
physical symmetric reference, assembly intervals, kernel/rank and ideal margin.
Only factor storage plus one sparse product row; no inverse columns.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
import numbers
import sys

from scripts.r8_f03_finite_local_dev import Unresolved


@dataclass
class Caps:
    dimension: int = 4096
    fill: int = 20_000
    operations: int = 100_000
    bits: int = 4096
    used: int = 0

    def tick(self, value=None):
        self.used += 1
        if self.used > self.operations:
            raise Unresolved('sparse interval operation cap')
        if value is not None and max(value.numerator.bit_length(), value.denominator.bit_length()) > self.bits:
            raise Unresolved('sparse interval rational bit cap')


def normal(x):
    # Never turn a rounded non-binary64 source scalar into an exact point.
    if isinstance(x, numbers.Integral):
        made = float(x)
        if not math.isfinite(made) or int(made) != int(x):
            raise Unresolved('integer scalar is not exactly binary64 representable')
        x = made
    elif not isinstance(x, float):
        raise Unresolved('actual binary64 scalar storage required')
    if not math.isfinite(x) or (x != 0 and abs(x) < sys.float_info.min):
        raise Unresolved('overflow/nonfinite or uncertified subnormal/flush arithmetic')
    return x


def directed(value, up, caps):
    """Exact binary64 primitive error determination then outward endpoint."""
    caps.tick(value)
    try:
        made = normal(float(value))
    except OverflowError as exc:
        raise Unresolved('interval overflow') from exc
    if made == 0 and value:
        raise Unresolved('uncertified underflow/subnormal arithmetic')
    relation = Fraction(made)
    if (up and relation < value) or (not up and relation > value):
        made = normal(math.nextafter(made, math.inf if up else -math.inf))
    return made


@dataclass(frozen=True)
class Interval:
    lo: float
    hi: float

    def __post_init__(self):
        normal(self.lo); normal(self.hi)
        if self.lo > self.hi:
            raise Unresolved('reversed interval')

    @classmethod
    def point(cls, x):
        return cls(normal(x), normal(x))

    def add(self, other, caps):
        return Interval(directed(Fraction(self.lo)+Fraction(other.lo), False, caps),
                        directed(Fraction(self.hi)+Fraction(other.hi), True, caps))

    def negate(self):
        return Interval(-self.hi, -self.lo)

    def multiply(self, other, caps):
        values = [Fraction(x)*Fraction(y) for x in (self.lo, self.hi) for y in (other.lo, other.hi)]
        return Interval(directed(min(values), False, caps), directed(max(values), True, caps))

    def magnitude(self):
        return max(abs(self.lo), abs(self.hi))


def upper_add(a, b, caps):
    return directed(Fraction(normal(a))+Fraction(normal(b)), True, caps)


def upper_mul(a, b, caps):
    return directed(Fraction(normal(a))*Fraction(normal(b)), True, caps)


def row_map(matrix, caps):
    """Canonical sparse entries; duplicate accumulation has explicit interval error."""
    from scipy import sparse
    if (not sparse.issparse(matrix) or len(matrix.shape) != 2 or
            matrix.dtype.name != 'float64' or max(matrix.shape) > caps.dimension):
        raise Unresolved('sparse matrix required')
    coo = matrix.tocoo(copy=True)
    if coo.nnz > caps.fill:
        raise Unresolved('input sparse fill cap')
    for _ in range(matrix.shape[0]): caps.tick()
    rows = [{} for _ in range(matrix.shape[0])]
    for i, j, v in zip(coo.row, coo.col, coo.data):
        value = Interval.point(v)
        rows[i][j] = rows[i].get(j, Interval.point(0)).add(value, caps)
    return rows


def permutations(factor, n):
    """Pr[perm_r[j],j]=1 and Pc[j,perm_c[j]]=1, SciPy/SuperLU convention."""
    pr, pc = tuple(map(int, factor.perm_r)), tuple(map(int, factor.perm_c))
    if sorted(pr) != list(range(n)) or sorted(pc) != list(range(n)):
        raise Unresolved('invalid SuperLU permutation')
    return pr, pc


def permute_rows(rows, pr, pc):
    out = [{} for _ in rows]
    for i, row in enumerate(rows):
        out[pr[i]] = {pc[j]: value for j, value in row.items()}
    return out


def triangular_bound(rows, rhs, lower, caps):
    n = len(rows); result = [0.]*n
    for i in (range(n) if lower else range(n-1, -1, -1)):
        diag = rows[i].get(i)
        if diag is None or diag.lo != diag.hi or diag.lo == 0:
            raise Unresolved('missing/zero/uncertain factor diagonal')
        value = normal(rhs[i])
        for j, entry in rows[i].items():
            if j == i:
                continue
            if (lower and j >= i) or (not lower and j <= i):
                if entry.magnitude():
                    raise Unresolved('factor triangular structure violation')
                continue
            value = upper_add(value, upper_mul(entry.magnitude(), result[j], caps), caps)
        result[i] = directed(Fraction(value)/Fraction(abs(diag.lo)), True, caps)
    return result


def sparse_lu_homotopy(a0, ahalf, radius0, radiushalf, factor, *, uncertainty_provenance, caps=None):
    """Enclose residual uniformly for affine0<=t<=.5 about a supplied LU.

    radius* are outward absolute assembly/scatter/scaling/shift uncertainty in
    A0/Ahalf coordinates, INCLUDING stored skew versus the independent physical
    reference. Zero radii require an explicit exact-input provenance declaration.
    Max endpoint magnitudes bounds each affine residual entry throughout interval.
    Successful result certifies invertibility only of the declared interval pencil.
    """
    caps = Caps() if caps is None else caps
    if any(type(v) is not int or v <= 0 for v in (caps.dimension, caps.fill, caps.operations, caps.bits)):
        raise Unresolved('positive frozen integer resource caps required')
    required = {'assembly', 'scatter', 'scaling', 'shift', 'physical_reference'}
    if (not isinstance(uncertainty_provenance, dict) or set(uncertainty_provenance) != required or
            any(not isinstance(v, str) or not v for v in uncertainty_provenance.values())):
        raise Unresolved('missing assembly/scatter/scaling/shift/physical reference uncertainty')
    n = a0.shape[0]
    if n <= 0 or n > caps.dimension or any(a.shape != (n, n) for a in (a0, ahalf, radius0, radiushalf, factor.L, factor.U)):
        raise Unresolved('sparse pencil/factor shape')
    if factor.L.nnz+factor.U.nnz > caps.fill or any(a.nnz > caps.fill for a in (a0, ahalf, radius0, radiushalf)):
        raise Unresolved('preflight sparse fill cap')
    pr, pc = permutations(factor, n)
    ar = [permute_rows(row_map(a, caps), pr, pc) for a in (a0, ahalf)]
    rr = [permute_rows(row_map(a, caps), pr, pc) for a in (radius0, radiushalf)]
    for rows in rr:
        if any(value.lo < 0 for row in rows for value in row.values()):
            raise Unresolved('negative endpoint uncertainty')
    l, u = row_map(factor.L, caps), row_map(factor.U, caps)
    fill = factor.L.nnz+factor.U.nnz
    if fill > caps.fill:
        raise Unresolved('factor fill cap')
    count = sum(len(u[k]) for row in l for k, value in row.items() if value.magnitude())
    # Bound the upcoming products and residual/triangular primitives before work.
    if count*8 > caps.operations-caps.used:
        raise Unresolved('sparse product operation forecast cap')
    b = [0.]*n; max_row = 0
    for i, row in enumerate(l):
        product = {}
        for k, lv in row.items():
            for j, uv in u[k].items():
                product[j] = product.get(j, Interval.point(0)).add(lv.multiply(uv, caps), caps)
        if len(product) > caps.fill:
            raise Unresolved('sparse product row fill cap')
        max_row = max(max_row, len(product))
        keys = set(product) | set(ar[0][i]) | set(ar[1][i]) | set(rr[0][i]) | set(rr[1][i])
        for j in keys:
            residual = []
            for endpoint in range(2):
                x = ar[endpoint][i].get(j, Interval.point(0)).add(product.get(j, Interval.point(0)).negate(), caps)
                radius = rr[endpoint][i].get(j, Interval.point(0)).hi
                residual.append(upper_add(x.magnitude(), radius, caps))
            b[i] = upper_add(b[i], max(residual), caps)
    ab = triangular_bound(l, b, True, caps)
    vb = triangular_bound(u, ab, False, caps)
    contraction = max(vb)
    return {'status': 'CERTIFIED_NONSINGULAR_DECLARED_INTERVAL' if contraction < 1 else 'UNRESOLVED',
            'uniform_interval': (0., .5), 'contraction_upper': contraction,
            'residual_row_bound': b, 'lower_bound': ab, 'inverse_residual_row_bound': vb,
            'product_multiplications': count, 'max_product_row_entries': max_row,
            'factor_fill': fill, 'operations_used': caps.used,
            'inertia': None, 'coercivity': None, 'qualification': False,
            'uncertainty_provenance': dict(uncertainty_provenance)}
