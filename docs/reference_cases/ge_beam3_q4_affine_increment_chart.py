"""Independent increment-resolved proper-polar chart and analytic derivatives.

Only the independently authored Scalar/Sylvester machinery is reused. The
producer's eigenvectors, derivatives, mechanics and recovered matrices are not
imported. Decimal refines values of the same real map of binary64 input data;
derivatives are analytic, never obtained by numerical frame differentiation.
"""
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import math
import numpy as np
import ge_beam3_q4_affine_numerical_chart as base

DIM = base.DIM
Scalar = base.Scalar
spatial_work = base.spatial_work
NUMERICS_ID = 'GE_BEAM3_Q4_AFFINE_INCREMENT_RESOLVED_CHART_NUMERICS_V1'


class IncrementChartError(ValueError):
    """The independently checked numerical chart cannot be represented safely."""


def _eye():
    return [[Decimal(int(i == j)) for j in range(3)] for i in range(3)]


def _transpose(a):
    return [list(column) for column in zip(*a)]


def _dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Decimal(0))


def _multiply(a, b):
    columns = _transpose(b)
    return [[_dot(row, column) for column in columns] for row in a]


def _norm(a):
    values = [x for row in a for x in row] if isinstance(a[0], list) else a
    return _dot(values, values).sqrt()


def _solve(a, b):
    """Deterministic complete row operations with lowest-index pivot ties."""
    n = len(a)
    rows = [list(row)+[b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda i: abs(rows[i][col]))
        if not rows[pivot][col] or not rows[pivot][col].is_finite():
            raise IncrementChartError('checker singular polar refinement pivot')
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        rows[col] = [x/divisor for x in rows[col]]
        for i in range(n):
            if i == col:
                continue
            factor = rows[i][col]
            rows[i] = [x-factor*y for x, y in zip(rows[i], rows[col])]
    return [row[-1] for row in rows]


def _proper_seed(rotation):
    columns = _transpose([[Decimal.from_float(float(x)) for x in row]
                          for row in rotation])
    basis = []
    for column in columns[:2]:
        v = column[:]
        for _ in range(2):
            for previous in basis:
                projection = _dot(previous, v)
                v = [x-projection*y for x, y in zip(v, previous)]
        length = _norm(v)
        if not Decimal('.5') <= length <= Decimal(2):
            raise IncrementChartError('checker defective proper polar seed')
        basis.append([x/length for x in v])
    a, b = basis
    basis.append([a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
                  a[0]*b[1]-a[1]*b[0]])
    return _transpose(basis)


def _cayley_step(rotation, omega):
    x, y, z = omega
    w = [[Decimal(0), -z, y], [z, Decimal(0), -x], [-y, x, Decimal(0)]]
    identity = _eye()
    minus = [[identity[i][j]-w[i][j]/2 for j in range(3)] for i in range(3)]
    plus = [[identity[i][j]+w[i][j]/2 for j in range(3)] for i in range(3)]
    cayley = _transpose([_solve(minus, column) for column in _transpose(plus)])
    return _multiply(rotation, cayley)


def _properness(rotation):
    gram = _multiply(_transpose(rotation), rotation)
    if max(abs(gram[i][j]-int(i == j)) for i in range(3) for j in range(3)) > Decimal('1e-70'):
        raise IncrementChartError('checker refinement lost orthogonality')
    a = rotation
    determinant = (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
                   -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
                   +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
    if abs(determinant-1) > Decimal('1e-70'):
        raise IncrementChartError('checker refinement is not a proper rotation')


def _positive_pair_sums(stretch):
    symmetric = [[(stretch[i][j]+stretch[j][i])/2 for j in range(3)] for i in range(3)]
    trace = sum(symmetric[i][i] for i in range(3))
    k = [[trace*int(i == j)-symmetric[i][j] for j in range(3)] for i in range(3)]
    lower = [[Decimal(0) for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(i+1):
            value = k[i][j]-sum((lower[i][p]*lower[j][p] for p in range(j)), Decimal(0))
            if i == j:
                if value <= 0:
                    raise IncrementChartError('checker polar stationary branch is not maximizing')
                lower[i][j] = value.sqrt()
            else:
                lower[i][j] = value/lower[j][j]
    return symmetric


def _refined_polar(reference, translation):
    with localcontext() as context:
        context.prec = 80
        context.rounding = ROUND_HALF_EVEN
        x = [[Decimal.from_float(float(v)) for v in row] for row in reference]
        u = [[Decimal.from_float(float(v)) for v in row] for row in translation]
        xc = [[x[i][j]-sum(x[k][j] for k in range(4))/4 for j in range(3)] for i in range(4)]
        uc = [[u[i][j]-sum(u[k][j] for k in range(4))/4 for j in range(3)] for i in range(4)]
        a0 = [[Decimal(0) for _ in range(3)] for _ in range(3)]
        for i in range(3):
            for j in range(i, 3):
                a0[i][j] = a0[j][i] = sum(xc[k][i]*xc[k][j] for k in range(4))
        a = [[a0[i][j]+sum(uc[k][i]*xc[k][j] for k in range(4))
              for j in range(3)] for i in range(3)]
        beta = sum(_dot(row, row) for row in xc)
        scale = _norm(a)
        if beta <= 0 or scale <= 0:
            raise IncrementChartError('checker degenerate polar covariance')
        af = np.asarray(a, dtype=float)
        bf = float(beta)
        if not np.isfinite(af).all() or not math.isfinite(bf) or bf <= 0:
            raise IncrementChartError('checker unrepresentable polar covariance')
        left, singular, right = np.linalg.svd(af)
        sign = 1. if np.linalg.det(left@right) > 0 else -1.
        spectral_scale = float(np.sum(singular))/bf
        gap = 2*(singular[1]+sign*singular[2])/bf
        if not gap > 1e-11*max(np.finfo(float).tiny, spectral_scale):
            raise IncrementChartError('checker nonunique proper polar fit')
        rotation = _proper_seed(left@np.diag([1., 1., sign])@right)
        for iteration in range(32):
            stretch = _multiply(_transpose(rotation), a)
            residual = [stretch[2][1]-stretch[1][2], stretch[0][2]-stretch[2][0],
                        stretch[1][0]-stretch[0][1]]
            if _norm(residual)/scale <= Decimal('1e-60'):
                break
            if iteration == 31:
                raise IncrementChartError('checker polar refinement did not converge')
            trace = sum(stretch[i][i] for i in range(3))
            jacobian = [[trace*int(i == j)-stretch[i][j] for j in range(3)] for i in range(3)]
            rotation = _cayley_step(rotation, _solve(jacobian, residual))
        _properness(rotation)
        symmetric = _positive_pair_sums(stretch)
        eigenvalues = np.linalg.eigvalsh(np.asarray(symmetric, dtype=float))
        refined_gap = 2*(eigenvalues[0]+eigenvalues[1])/bf
        if not refined_gap > 1e-11*max(np.finfo(float).tiny, spectral_scale):
            raise IncrementChartError('checker refined proper polar gap')
        objective = float(sum(stretch[i][i] for i in range(3)))
        maximum = float(singular[0]+singular[1]+sign*singular[2])
        if abs(objective-maximum)/float(scale) > 1e-11:
            raise IncrementChartError('checker refined fit is not the proper maximum')
        delta = [[rotation[i][j]-int(i == j) for j in range(3)] for i in range(3)]
        return tuple(np.asarray(v, dtype=float) for v in (rotation, delta, a, xc, uc))


def polar_derivatives(reference, translation):
    rotation, delta, a, xc, uc = _refined_polar(reference, translation)
    stretch = rotation.T@a
    k = np.trace(stretch)*np.eye(3)-stretch
    ai = np.zeros((DIM, 3, 3))
    for node in range(4):
        for component in range(3):
            ai[6*node+component, component] = xc[node]
    m = np.einsum('ab,ibc->iac', rotation.T, ai)
    omega = np.array([np.linalg.solve(k, base.axl(v-v.T)) for v in m])
    w = np.array([base.skew(v) for v in omega])
    first = np.array([rotation@v for v in w])
    second = np.zeros((DIM, DIM, 3, 3))
    for j in range(DIM):
        sj = -w[j]@stretch+m[j]
        kj = np.trace(sj)*np.eye(3)-sj
        for i in range(DIM):
            mij = -w[j]@m[i]
            wij = np.linalg.solve(k, base.axl(mij-mij.T)-kj@omega[i])
            second[i, j] = rotation@(w[j]@w[i]+base.skew(wij))
    return rotation, delta, first, second, xc, uc


def exponential_increment(vector):
    s = sum(a*a for a in vector)
    if s.v < .1:
        a, b = base.series(s, 1), base.series(s, 2)
    else:
        theta = s**.5
        a, b = base.sine(theta)/theta, (1-base.cosine(theta))/s
    w = base.hat(vector)
    return base.a_matrix(w, a)+base.a_matrix(w@w, b)


def logarithm_increment(delta_rotation):
    delta = -sum(delta_rotation[i, i] for i in range(3))/2
    if delta.v < .02:
        factor = Scalar(0.)
        power = Scalar(1.)
        for k in range(16):
            factor += (2**k*math.factorial(k)**2/math.factorial(2*k+1))*power
            power *= delta
    else:
        cosine = 1-delta
        angle = base.arccosine(cosine)
        if angle.v >= .9*math.pi:
            raise IncrementChartError('checker relative rotation requires cutback')
        factor = angle/(1-cosine*cosine)**.5
    return [factor*(delta_rotation[b, a]-delta_rotation[a, b])/2
            for a, b in ((1, 2), (2, 0), (0, 1))]


def evaluate(reference, displacement, accepted):
    reference = np.asarray(reference, dtype=float)
    displacement = np.asarray(displacement, dtype=float)
    accepted = np.asarray(accepted, dtype=float)
    if reference.shape != (4, 3) or displacement.shape != (24,) or accepted.shape != (4, 3, 3):
        raise IncrementChartError('checker chart shapes')
    if not all(np.isfinite(a).all() for a in (reference, displacement, accepted)):
        raise IncrementChartError('checker nonfinite chart input')
    for rotation in accepted:
        if np.linalg.norm(rotation.T@rotation-np.eye(3)) > 1e-11 or abs(np.linalg.det(rotation)-1) > 1e-11:
            raise IncrementChartError('checker improper accepted rotation')
    if np.any(np.linalg.norm(displacement.reshape(4, 6)[:, 3:], axis=1) >= .9*math.pi):
        raise IncrementChartError('checker trial increment requires cutback')
    r, dr, first, second, xc, uc = polar_derivatives(reference, displacement.reshape(4, 6)[:, :3])
    rj = np.array([[Scalar(r[i, j], first[:, i, j], second[:, :, i, j])
                    for j in range(3)] for i in range(3)], dtype=object)
    drj = np.array([[Scalar(dr[i, j], first[:, i, j], second[:, :, i, j])
                     for j in range(3)] for i in range(3)], dtype=object)
    q = [Scalar.coordinate(displacement[i], i) for i in range(DIM)]
    uj = np.array([[q[6*i+j] for j in range(3)] for i in range(4)], dtype=object)
    centre = sum(uj)/4
    centered = uj-centre
    ucj = np.array([[Scalar(uc[i, j], centered[i, j].g, centered[i, j].h)
                     for j in range(3)] for i in range(4)], dtype=object)
    data, rotations = [], []
    for i in range(4):
        local = rj.T@ucj[i]+drj.T@xc[i]
        data.extend(local)
        increment = exponential_increment(q[6*i+3:6*i+6])
        accepted_delta = base.constants(accepted[i]-np.eye(3))
        trial_delta = accepted_delta+increment+increment@accepted_delta
        relative_delta = drj.T+trial_delta+drj.T@trial_delta
        data.extend(logarithm_increment(relative_delta))
        trial = base.constants(np.eye(3))+trial_delta
        rotations.append([[v.v for v in row] for row in trial])
    return dict(d=np.array([a.v for a in data]), D=np.array([a.g for a in data]),
                D2=np.array([a.h for a in data]), R=r, Q=np.array(rotations),
                x=reference+displacement.reshape(4, 6)[:, :3],
                polar_first=first, polar_second=second)
