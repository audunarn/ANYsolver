"""Bounded exact rectangle/native work prerequisites; DEVELOPMENT ONLY.

Coordinates z=(u,ell*theta), y in m, H in N/m. No floating rank,
candidate eigenvalues, fitted margins, global inverse, or F03 acceptance.
"""
from dataclasses import dataclass
from fractions import Fraction as F


class Unresolved(RuntimeError):
    pass


@dataclass
class ExactBudget:
    operations: int = 0
    operation_cap: int = 2_000_000
    bit_cap: int = 4096

    def check(self, value):
        self.operations += 1
        value = F(value)
        if self.operations > self.operation_cap:
            raise Unresolved('exact operation cap')
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > self.bit_cap:
            raise Unresolved('exact rational bit cap')
        return value


def rational(x):
    if type(x) not in (int, F):
        raise Unresolved('explicit exact rational inputs required')
    return F(x)


def zero(n, m):
    return [[F() for _ in range(m)] for _ in range(n)]


def transpose(a):
    return [list(r) for r in zip(*a)]


def multiply(a, b, budget):
    out = zero(len(a), len(b[0]))
    for i, row in enumerate(a):
        for k, x in enumerate(row):
            if x:
                for j, y in enumerate(b[k]):
                    if y:
                        out[i][j] = budget.check(out[i][j] + budget.check(x*y))
    return out


def solve(a, b, budget, *, order_cap=18):
    """Exact bounded local elimination; never a global inverse service."""
    n = len(a)
    if not 0 < n <= order_cap or any(len(r) != n for r in a) or len(b) != n:
        raise Unresolved('local order/shape cap')
    w = [[budget.check(x) for x in (*r, *s)] for r, s in zip(a, b)]
    for k in range(n):
        pivot = next((i for i in range(k, n) if w[i][k]), None)
        if pivot is None:
            raise Unresolved('exact singular local minor')
        w[k], w[pivot] = w[pivot], w[k]
        d = w[k][k]
        for j in range(k, len(w[k])):
            w[k][j] = budget.check(w[k][j]/d)
        for i in range(n):
            if i != k and w[i][k]:
                scale = w[i][k]
                for j in range(k, len(w[i])):
                    w[i][j] = budget.check(w[i][j] - budget.check(scale*w[k][j]))
    return [r[n:] for r in w]


def identity(n):
    return [[F(i == j) for j in range(n)] for i in range(n)]


def spd_inverse_bound(h, budget):
    """Exact positive LDL pivots and exact <=18 inverse infinity norm."""
    n = len(h)
    if not 0 < n <= 18 or any(len(r) != n for r in h) or h != transpose(h):
        raise Unresolved('symmetric material block order<=18 required')
    l, d = identity(n), []
    for j in range(n):
        pivot = budget.check(h[j][j] - sum((budget.check(l[j][k]**2*d[k]) for k in range(j)), F()))
        if pivot <= 0:
            raise Unresolved('nonpositive exact material LDL pivot')
        d.append(pivot)
        for i in range(j+1, n):
            l[i][j] = budget.check((h[i][j] - sum((budget.check(l[i][k]*l[j][k]*d[k]) for k in range(j)), F()))/pivot)
    inv = solve(h, identity(n), budget)
    norm = max(sum(map(abs, row), F()) for row in inv)
    return {'k0_N_per_m': budget.check(1/norm), 'inverse_inf_norm': norm,
            'positive_pivots': tuple(d), 'order': n}


def isotropic_shell(e, nu, thickness, shear_factor=F(5, 6)):
    """Original elastic membrane, bending, transverse shear; no extra stiffness."""
    e, nu, t, sf = map(rational, (e, nu, thickness, shear_factor))
    if e <= 0 or t <= 0 or not -1 < nu < F(1, 2) or sf <= 0:
        raise Unresolved('positive isotropic source section required')
    c = zero(8, 8)
    for offset, factor in ((0, e*t/(1-nu**2)), (3, e*t**3/(12*(1-nu**2)))):
        c[offset][offset] = c[offset+1][offset+1] = factor
        c[offset][offset+1] = c[offset+1][offset] = nu*factor
        c[offset+2][offset+2] = (1-nu)*factor/2
    c[6][6] = c[7][7] = sf*e*t/(2*(1+nu))
    return c, e*t/(2*(1+nu))


def rectangle_fields(a, b, r, s):
    """Literal specialization of _source_fields/_compatible, no fitted map."""
    ns, ne, compatible = zero(8, 14), zero(8, 21), zero(8, 24)
    for i in range(8):
        ns[i][i] = ne[i][i] = F(1)
    for row, col in ((0, 8), (3, 10)):
        ns[row][col] = ne[row][col] = a*a*s
        ns[row+1][col+1] = ne[row+1][col+1] = b*b*r
    ns[6][12] = ne[6][12] = a*s
    ns[7][13] = ne[7][13] = b*r
    for row, col, value in ((0, 14, a*a*r), (1, 15, b*b*s),
                            (2, 16, a*b*r), (2, 17, a*b*s),
                            (0, 18, a*a*r*s), (1, 19, b*b*r*s), (2, 20, a*b*r*s)):
        ne[row][col] = value
    for node, (ri, si) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        nx, ny = F(ri, 4)*(1+si*s)/a, F(si, 4)*(1+ri*r)/b
        j = 6*node
        compatible[0][j], compatible[1][j+1] = nx, ny
        compatible[2][j], compatible[2][j+1] = ny, nx
        compatible[3][j+4], compatible[4][j+3] = nx, -ny
        compatible[5][j+4], compatible[5][j+3] = ny, -nx
        compatible[6][j+2] = nx
        compatible[6][j+4] = (1+si*s)/4
        compatible[7][j+2] = ny
        compatible[7][j+3] = -(1+ri*r)/4
    return ns, ne, compatible


def rectangle_work(a, b, ell, constitutive, drill, budget, *, pl=F(1), hg=F(1, 1000)):
    """Return source Q,F,E and exact completed eighteen-row work factorization.

    Tensor Simpson integrates degrees<=3 in each variable exactly. Every source
    integrand has degree<=2 here. Thus this is the same ideal two-point Gauss
    integral, not altered quadrature. Geometry-only normalizers S:
    Q rows0:3,6:8 /ell;3:6 unchanged;8:10 /ell^3;
    10:12 /ell^2;12:14 /ell^2. PL/hg rows multiplied by ell.
    """
    a, b, ell, drill, pl, hg = map(rational, (a, b, ell, drill, pl, hg))
    if min(a, b, ell, drill, pl, hg) <= 0:
        raise Unresolved('strictly positive rectangle/actual completions required')
    if len(constitutive) != 8 or any(len(r) != 8 for r in constitutive):
        raise Unresolved('original source eight-field constitutive required')
    c = [[rational(x) for x in row] for row in constitutive]
    q, f, e = zero(14, 24), zero(21, 14), zero(21, 21)
    for r, wr in ((F(-1), F(1, 3)), (F(), F(4, 3)), (F(1), F(1, 3))):
        for s, ws in ((F(-1), F(1, 3)), (F(), F(4, 3)), (F(1), F(1, 3))):
            ns, ne, bc = rectangle_fields(a, b, r, s)
            for target, term, sign in ((q, multiply(transpose(ns), bc, budget), 1),
                                       (f, multiply(transpose(ne), ns, budget), -1),
                                       (e, multiply(multiply(transpose(ne), c, budget), ne, budget), 1)):
                for i, row in enumerate(target):
                    for j in range(len(row)):
                        row[j] = budget.check(row[j]+sign*a*b*wr*ws*term[i][j])
    # E is the actual local source21 block; only this inversion exceeds18.
    ef = solve(e, f, budget, order_cap=21)
    m = multiply(transpose(f), ef, budget)
    hi = solve(m, identity(14), budget)
    scale = [1/ell]*3 + [F(1)]*3 + [1/ell]*2 + [1/ell**3]*2 + [1/ell**2]*4
    rows = [[budget.check(v*scale[i]/(ell if j % 6 >= 3 else 1)) for j, v in enumerate(row)] for i, row in enumerate(q)]
    h = zero(18, 18)
    for i in range(14):
        for j in range(14):
            h[i][j] = budget.check(hi[i][j]/scale[i]/scale[j])
    centre = zero(3, 24)
    gamma = [F() for _ in range(24)]
    for n, (ri, si) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        j = 6*n
        centre[0][j] = F(si, 8)/b
        centre[0][j+1] = -F(ri, 8)/a
        centre[0][j+5] = F(1, 4)
        centre[1][j] = F(ri*si, 8)/b
        centre[1][j+5] = F(ri, 4)
        centre[2][j+1] = -F(ri*si, 8)/a
        centre[2][j+5] = F(si, 4)
        gamma[j+5] = F(ri*si, 4)
    for i, row in enumerate((*centre, gamma)):
        rows.append([budget.check(v*ell/(ell if j % 6 >= 3 else 1)) for j, v in enumerate(row)])
        h[14+i][14+i] = budget.check((pl if i < 3 else 2*hg)*drill*4*a*b/(ell**2*(3 if i in (1, 2) else 1)))
    bound = spd_inverse_bound(h, budget)
    return {'rows_z': rows, 'H_N_per_m': h, 'Q': q, 'F': f, 'E': e,
            'core_rows': tuple(range(14)), 'completion_rows': (14, 15, 16, 17),
            'normalizers': tuple(scale), 'ell_m': ell, 'bound': bound,
            'units': {'z': 'm', 'y': 'm', 'H': 'N/m'}}


def local_reconstruction(rows, new, old, budget):
    """Exact independent work minor; R_new z_new = y - R_old z_old."""
    if not 0 < len(new) <= 12 or set(new) & set(old) or set(new) | set(old) != set(range(24)):
        raise Unresolved('literal two-node frontier requires <=12 new and24 local columns')
    reduced, chosen, pivots = [], [], []
    for i, row in enumerate(rows):
        w = [row[j] for j in new]
        for pivot, rr in zip(pivots, reduced):
            value = w[pivot]
            w = [budget.check(x-value*y) for x, y in zip(w, rr)]
        pivot = next((j for j, x in enumerate(w) if x), None)
        if pivot is not None:
            value = w[pivot]
            reduced.append([budget.check(x/value) for x in w])
            pivots.append(pivot); chosen.append(i)
        if len(chosen) == len(new):
            break
    if len(chosen) != len(new):
        raise Unresolved('source local frontier has no exact full-column work minor')
    minor = [[rows[i][j] for j in new] for i in chosen]
    inv = solve(minor, identity(len(new)), budget, order_cap=12)
    oldmap = [[rows[i][j] for j in old] for i in chosen]
    transport = multiply(inv, oldmap, budget)
    return {'selected_rows': tuple(chosen), 'new': tuple(new), 'old': tuple(old),
            'inverse': inv, 'transport': transport}


def rectangular_strip_bounds(work, cells, budget):
    """Literal one-row chain rooted at all six coordinates of both left nodes.

    Each new cell adds bottom/top right nodes. No global solve or nullspace.
    Sum absolute inverse entries bounds every selected y by ||y_all||2.
    """
    if type(cells) is not int or not 1 <= cells <= 2:
        raise Unresolved('development inventory at most two rectangle cells')
    new = tuple(range(6, 18)); old = tuple(range(6))+tuple(range(18, 24))
    rec = local_reconstruction(work['rows_z'], new, old, budget)
    left = [F()]*12; inventory = [left[:]]
    for _ in range(cells):
        right = [budget.check(sum(map(abs, inv), F()) + sum((abs(x)*v for x, v in zip(tr, left)), F()))
                 for inv, tr in zip(rec['inverse'], rec['transport'])]
        inventory.append(right)
        # new order bottom-right,top-right; old order bottom-left,top-left.
        left = right
    return {'node_pair_bounds': inventory, 'local_minor': rec,
            'supported_coordinates': 'all six coordinates of both root shell nodes'}


def native_halfcell(h, ell, cn, cm, budget):
    """Literal straight uncoupled native eta,ell*dtheta,ell*(mean-theta-phi)."""
    h, ell = map(rational, (h, ell))
    if min(h, ell) <= 0 or any(len(c) != 3 or any(len(r) != 3 for r in c) for c in (cn, cm)):
        raise Unresolved('positive straight uncoupled native halfcell required')
    hmat = zero(9, 9)
    for start, c, scale in ((0, cn, 1/h), (3, cm, 1/(h*ell**2)), (6, cm, 12/(h*ell**2))):
        for i in range(3):
            for j in range(3):
                hmat[start+i][start+j] = budget.check(rational(c[i][j])*scale)
    return {'H_N_per_m': hmat, 'bound': spd_inverse_bound(hmat, budget),
            'coordinates': ('eta_m', 'ell_Delta_theta_m', 'ell_mean_theta_minus_phi_m')}


def native_member_rows(length, ell, budget):
    """All24 physical native q slots; nodal18 + two independent cell rotations6.

    R maps z=(u,ell*theta,ell*phi) into18 local work measurements.
    Native negative complementary block is intentionally NOT replaced here.
    """
    length, ell = map(rational, (length, ell))
    if min(length, ell) <= 0:
        raise Unresolved('positive straight native geometry')
    rows = zero(18, 24); d = length/2
    for cell in range(2):
        off, left, right, phi = 9*cell, 6*cell, 6*(cell+1), 18+3*cell
        for axis in range(3):
            rows[off+axis][right+axis] = F(1); rows[off+axis][left+axis] = F(-1)
            rows[off+3+axis][right+3+axis] = F(1); rows[off+3+axis][left+3+axis] = F(-1)
            rows[off+6+axis][left+3+axis] = rows[off+6+axis][right+3+axis] = F(1, 2)
            rows[off+6+axis][phi+axis] = F(-1)
        # eta = du - phi cross(d,0,0).
        rows[off+1][phi+2] = budget.check(-d/ell)
        rows[off+2][phi+1] = budget.check(d/ell)
    return rows


def native_chain_bounds(length, ell, budget):
    """One member, two halfcells; root theta_z yaw excluded until exact C closure."""
    length, ell = map(rational, (length, ell))
    if min(length, ell) <= 0:
        raise Unresolved('positive native recurrence geometry')
    b = [F()]*24
    for cell in range(2):
        left, right, phi = 6*cell, 6*(cell+1), 18+3*cell
        for axis in range(3):
            b[right+3+axis] = budget.check(b[left+3+axis]+1)
            b[phi+axis] = budget.check(b[left+3+axis]+F(3, 2))
        # Transverse translation uses another axis's phi: all three phi
        # bounds must exist before evaluating any translation bound.
        for axis in range(3):
            b[right+axis] = budget.check(b[left+axis]+1 + (length/(2*ell)*b[phi+(2 if axis == 1 else 1)] if axis in (1, 2) else 0))
    return b


def close_yaw(bounds, rigid, action, budget):
    """Literal exact row action c and cr, never a floating rank or solve."""
    if not len(bounds) == len(rigid) == len(action):
        raise Unresolved('exact applicable yaw row dimensions')
    c = list(map(rational, action)); r = list(map(rational, rigid)); b = list(map(rational, bounds))
    if any(v < 0 for v in b):
        raise Unresolved('nonnegative geometry bounds required')
    cr = budget.check(sum((x*y for x, y in zip(c, r)), F()))
    if cr == 0:
        raise Unresolved('constraint has exactly zero yaw action')
    value = budget.check(sum((abs(x)*y for x, y in zip(c, b)), F())/abs(cr))
    return [budget.check(x+abs(y)*value) for x, y in zip(b, r)], cr


def geometry_constant(sparse_entries, bounds, budget):
    """Exact sparse |Gz| b b sum; input is the independent physical norm."""
    total = F()
    for i, j, value in sparse_entries:
        if not 0 <= i < len(bounds) or not 0 <= j < len(bounds) or min(bounds[i], bounds[j]) < 0:
            raise Unresolved('norm/bounds indexing')
        total = budget.check(total+budget.check(abs(rational(value))*bounds[i]*bounds[j]))
    if total <= 0:
        raise Unresolved('nonpositive geometry constant')
    return total
