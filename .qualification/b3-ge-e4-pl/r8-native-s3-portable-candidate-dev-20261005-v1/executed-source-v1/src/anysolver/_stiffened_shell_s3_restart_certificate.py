"""Bounded, value-only certificates for opt-in S3 checkpoint admission.

This module never repairs a checkpoint or supplies a material predecessor.  Its
private directed scalar arithmetic is confined to three-node/4x4 witnesses;
it is deliberately independent of producer BLAS and elementary-function error.
"""
from dataclasses import dataclass
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
import math
import numpy as np

POLICY = "B3_GE_S3_RESTART_PORTABLE_CONSISTENCY_V1_DEV"
_PRECISION = 72
_PI_LO = Decimal("3.14159265358979323846264338327950288419716939937510")
_PI_HI = Decimal("3.14159265358979323846264338327950288419716939937511")
_UNIT_ROUNDOFF = Decimal.from_float(2.0**-53)
_MIN_SUBNORMAL = Decimal.from_float(float(np.nextafter(0., 1.)))


class UncertifiedS3Restart(ValueError):
    """A portable association or material certificate could not be proved."""


def _direct(rounding, operation):
    with localcontext() as context:
        context.prec = _PRECISION
        context.rounding = rounding
        return operation()


class _Bound:
    """Private scalar enclosure; no float arithmetic in proof operations."""
    __slots__ = ("lo", "hi")

    def __init__(self, value, hi=None):
        if isinstance(value, _Bound):
            self.lo, self.hi = value.lo, value.hi
            return
        self.lo = (Decimal.from_float(float(value)) if isinstance(value, (float, np.floating))
                   else Decimal(value))
        self.hi = self.lo if hi is None else Decimal(hi)
        if not self.lo.is_finite() or not self.hi.is_finite() or self.lo > self.hi:
            raise UncertifiedS3Restart("invalid scalar certificate enclosure")

    def __add__(self, other):
        other = _Bound(other)
        return _Bound(_direct(ROUND_FLOOR, lambda: self.lo + other.lo),
                      _direct(ROUND_CEILING, lambda: self.hi + other.hi))

    __radd__ = __add__

    def __neg__(self):
        return _Bound(self.hi.copy_negate(), self.lo.copy_negate())

    def __sub__(self, other):
        return self + -_Bound(other)

    def __rsub__(self, other):
        return _Bound(other) - self

    def __mul__(self, other):
        other = _Bound(other)
        pairs = ((self.lo, other.lo), (self.lo, other.hi),
                 (self.hi, other.lo), (self.hi, other.hi))
        return _Bound(min(_direct(ROUND_FLOOR, lambda a=a, b=b: a*b) for a, b in pairs),
                      max(_direct(ROUND_CEILING, lambda a=a, b=b: a*b) for a, b in pairs))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = _Bound(other)
        if other.lo <= 0 <= other.hi:
            raise UncertifiedS3Restart("certificate division has unresolved zero denominator")
        inverse = _Bound(_direct(ROUND_FLOOR, lambda: Decimal(1)/other.hi),
                         _direct(ROUND_CEILING, lambda: Decimal(1)/other.lo))
        return self * inverse

    def __rtruediv__(self, other):
        return _Bound(other)/self

    def square(self):
        maximum = max(self.lo.copy_abs(), self.hi.copy_abs())
        minimum = Decimal(0) if self.lo <= 0 <= self.hi else min(self.lo.copy_abs(), self.hi.copy_abs())
        return _Bound(_direct(ROUND_FLOOR, lambda: minimum*minimum),
                      _direct(ROUND_CEILING, lambda: maximum*maximum))

    def sqrt(self):
        if self.lo < 0:
            raise UncertifiedS3Restart("negative certificate square-root domain")
        if self.hi == 0:
            return _Bound(0)
        # Decimal.sqrt is correctly rounded to nearest, regardless of rounding
        # mode. Adjacent Decimal values enclose it in the working precision.
        with localcontext() as context:
            context.prec = _PRECISION
            lower, upper = self.lo.sqrt(), self.hi.sqrt()
            return _Bound(context.next_minus(lower) if lower else Decimal(0),
                          context.next_plus(upper))

    def absolute(self):
        return _Bound(0 if self.lo <= 0 <= self.hi else min(self.lo.copy_abs(), self.hi.copy_abs()),
                      max(self.lo.copy_abs(), self.hi.copy_abs()))

    def upper_float(self):
        value = float(self.hi)
        if not math.isfinite(value):
            raise UncertifiedS3Restart("unrepresentable certificate bound")
        return float(np.nextafter(value, math.inf))


def _dot(left, right):
    return sum((a*b for a, b in zip(left, right)), _Bound(0))


def _norm(values):
    return sum((value.square() for value in values), _Bound(0)).sqrt()


def _transpose(matrix):
    return list(map(list, zip(*matrix)))


def _multiply(left, right):
    columns = _transpose(right)
    return [[_dot(row, column) for column in columns] for row in left]


def _inverse(matrix):
    """Local 3x3/5x5 inverse enclosure from a checked inverse residual."""
    n = len(matrix)
    if n not in (3, 5):
        raise UncertifiedS3Restart("only local chart/bordered inverses are admitted")
    midpoint = np.array([[float((value.lo+value.hi)/2) for value in row] for row in matrix])
    try:
        witness = np.linalg.inv(midpoint)
    except np.linalg.LinAlgError as exc:
        raise UncertifiedS3Restart("singular local inverse witness") from exc
    inverse = [[_Bound(value) for value in row] for row in witness]
    product = _multiply(matrix, inverse)
    residual = _norm([product[i][j]-int(i == j) for i in range(n) for j in range(n)])
    if residual.hi >= 1:
        raise UncertifiedS3Restart("local inverse residual does not certify nonsingularity")
    magnitude = _norm([value for row in inverse for value in row])
    error = magnitude*residual/(1-residual)
    return [[value+_Bound(error.hi.copy_negate(), error.hi) for value in row] for row in inverse]


def _exp_differential(vector):
    """Directed Rodrigues value and all three first derivatives."""
    vector = [_Bound(value) for value in vector]
    argument = _dot(vector, vector)
    if argument.hi > 16:
        raise UncertifiedS3Restart("portable exponential differential exceeds bounded domain")
    coefficients, derivatives = [], []
    for offset in (1, 2):
        total, derivative = _Bound(0), _Bound(0)
        power, previous = _Bound(1), _Bound(1)
        for k in range(65):
            coefficient = _Bound((-1)**k)/math.factorial(2*k+offset)
            total = total+coefficient*power
            if k:
                derivative = derivative+k*coefficient*previous
            previous, power = power, power*argument
        ratio = _Bound(16)/(130*131)
        tail = power.absolute()/math.factorial(130+offset)/(1-ratio)
        derivative_tail = 65*previous.absolute()/math.factorial(130+offset)/(1-ratio)/(1-ratio)
        coefficients.append(total+_Bound(tail.hi.copy_negate(), tail.hi))
        derivatives.append(derivative+_Bound(derivative_tail.hi.copy_negate(), derivative_tail.hi))
    x, y, z = vector
    cross = [[_Bound(0), -z, y], [z, _Bound(0), -x], [-y, x, _Bound(0)]]
    cross2 = _multiply(cross, cross)
    value = [[_Bound(int(i == j))+coefficients[0]*cross[i][j]+coefficients[1]*cross2[i][j]
              for j in range(3)] for i in range(3)]
    derivative = []
    for axis in range(3):
        basis = [int(i == axis) for i in range(3)]
        dx, dy, dz = basis
        dc = [[_Bound(0), _Bound(-dz), _Bound(dy)], [_Bound(dz), _Bound(0), _Bound(-dx)],
              [_Bound(-dy), _Bound(dx), _Bound(0)]]
        first, second = _multiply(dc, cross), _multiply(cross, dc)
        derivative.append([[2*vector[axis]*derivatives[0]*cross[i][j]+coefficients[0]*dc[i][j]
                            +2*vector[axis]*derivatives[1]*cross2[i][j]
                            +coefficients[1]*(first[i][j]+second[i][j]) for j in range(3)]
                           for i in range(3)])
    return value, derivative


def _log_differential_factor(cosine):
    delta = 1-cosine
    limit = _exp([_Bound(_PI_LO, _PI_HI)*Decimal("0.9"), 0, 0])[1][1]
    if cosine.lo <= limit.hi:
        raise UncertifiedS3Restart("relative differential crosses frozen 0.9*pi chart")
    if delta.absolute().hi <= Decimal("0.1"):
        # Analytic continuation of acos(c)/sqrt(1-c*c) at c=1.
        # a_(k+1)/a_k=(k+1)/(2*k+3), hence |a_k|<=1.
        total, derivative = _Bound(0), _Bound(0)
        coefficient, power, previous = _Bound(1), _Bound(1), _Bound(1)
        for k in range(65):
            total = total+coefficient*power
            if k:
                derivative = derivative-k*coefficient*previous
            coefficient = coefficient*(k+1)/(2*k+3)
            previous, power = power, power*delta
        absolute = delta.absolute()
        tail = power.absolute()/(1-absolute)
        derivative_tail = 65*previous.absolute()/(1-absolute)/(1-absolute)
        return (total+_Bound(tail.hi.copy_negate(), tail.hi),
                derivative+_Bound(derivative_tail.hi.copy_negate(), derivative_tail.hi))
    if cosine.hi >= 1 or cosine.lo <= -1:
        raise UncertifiedS3Restart("unresolved non-small logarithm domain")
    argument = ((1-cosine)/(1+cosine)).sqrt()
    for _ in range(4):
        argument = argument/(1+(1+argument.square()).sqrt())
    if argument.hi >= Decimal("0.5"):
        raise UncertifiedS3Restart("bounded arctangent reduction failed")
    squared, term, total = argument.square(), argument, _Bound(0)
    for k in range(65):
        total = total+term/(2*k+1)
        term = -term*squared
    tail = term.absolute()/131/(1-squared)
    angle = 32*(total+_Bound(tail.hi.copy_negate(), tail.hi))
    sine = (1-cosine.square()).sqrt()
    return angle/sine, -1/(sine*sine)+angle*cosine/(sine*sine*sine)


def _rotation_differential(q, dq):
    w, x, y, z = q
    dw, dx, dy, dz = dq
    return [[-4*(y*dy+z*dz), 2*(dx*y+x*dy-dw*z-w*dz), 2*(dx*z+x*dz+dw*y+w*dy)],
            [2*(dx*y+x*dy+dw*z+w*dz), -4*(x*dx+z*dz), 2*(dy*z+y*dz-dw*x-w*dx)],
            [2*(dx*z+x*dz-dw*y-w*dy), 2*(dy*z+y*dz+dw*x+w*dx), -4*(x*dx+y*dy)]]


def work_map(reference, physical, anchors, local, certificate):
    """Enclose the complete first pullback and each spatial chart inverse.

    This includes the differential uncertainty term, not just D.T delta_f.
    Every dense object is local (3x3 or the 5x5 bordered eigenproblem).
    """
    reference = np.asarray(reference);physical = np.asarray(physical);local = np.asarray(local)
    anchors = np.tile(np.eye(3), (3, 1, 1)) if anchors is None else np.asarray(anchors)
    r = [[_Bound(float(value)) for value in row] for row in reference]
    u = [[_Bound(float(value)) for value in row] for row in physical.reshape(3, 6)[:, :3]]
    rc = [[r[i][j]-sum(row[j] for row in r)/3 for j in range(3)] for i in range(3)]
    uc = [[u[i][j]-sum(row[j] for row in u)/3 for j in range(3)] for i in range(3)]
    scale2 = sum((value.square() for row in rc for value in row), _Bound(0))

    def davenport(c):
        trace = sum(c[i][i] for i in range(3))
        axial = [c[2][1]-c[1][2], c[0][2]-c[2][0], c[1][0]-c[0][1]]
        return [[trace]+axial]+[[axial[i]]+[c[i][j]+c[j][i]-trace*int(i == j)
                                          for j in range(3)] for i in range(3)]

    covariance = [[sum((rc[i][a]+uc[i][a])*rc[i][b] for i in range(3))/scale2
                   for b in range(3)] for a in range(3)]
    matrix = davenport(covariance)
    first_physical = _multiply(_exp(physical[3:6]), [[_Bound(float(v)) for v in row] for row in anchors[0]])
    q = _quaternion(_multiply(first_physical, _exp(-local[3:6])))
    radius = (_Bound(2).sqrt()*_Bound(certificate.spectral_residual[0])
              /_Bound(certificate.spectral_separation[0]))
    q = [value+_Bound(radius.hi.copy_negate(), radius.hi) for value in q]
    eigenvalue = _dot(q, [_dot(row, q) for row in matrix])
    bordered = [[eigenvalue*int(i == j)-matrix[i][j] for j in range(4)]+[q[i]] for i in range(4)]
    bordered.append(q+[_Bound(0)])
    inverse = _inverse(bordered)
    rotation = _rotation(q);rt = _transpose(rotation)
    differentials = [[[_Bound(0) for _ in range(3)] for _ in range(3)] for _ in range(18)]
    for node in range(3):
        for axis in range(3):
            dm = davenport([[rc[node][j]/scale2 if i == axis else _Bound(0) for j in range(3)]
                            for i in range(3)])
            rhs = [_dot(row, q) for row in dm]
            dq = [_dot(row[:4], rhs) for row in inverse[:4]]
            differentials[6*node+axis] = _rotation_differential(q, dq)
    differential = [[_Bound(0) for _ in range(18)] for _ in range(18)]
    chart_inverses = []
    for node in range(3):
        exp, dexp = _exp_differential(physical[6*node+3:6*node+6])
        anchor = [[_Bound(float(value)) for value in row] for row in anchors[node]]
        ri = _multiply(exp, anchor)
        local_frame = _multiply(rt, ri)
        cosine = (sum(local_frame[i][i] for i in range(3))-1)/2
        factor, factor_derivative = _log_differential_factor(cosine)
        axial = [(local_frame[2][1]-local_frame[1][2])/2,
                 (local_frame[0][2]-local_frame[2][0])/2,
                 (local_frame[1][0]-local_frame[0][1])/2]
        spatial_chart = [[_Bound(0) for _ in range(3)] for _ in range(3)]
        for axis in range(3):
            spatial = _multiply(dexp[axis], _transpose(exp))
            omega = [(spatial[2][1]-spatial[1][2])/2, (spatial[0][2]-spatial[2][0])/2,
                     (spatial[1][0]-spatial[0][1])/2]
            for row in range(3):spatial_chart[row][axis] = omega[row]
        chart_inverses.append(_transpose(_inverse(spatial_chart)))
        for column in range(18):
            dframe = _multiply(_transpose(differentials[column]), ri)
            if 6*node+3 <= column < 6*node+6:
                own = _multiply(rt, _multiply(dexp[column-(6*node+3)], anchor))
                dframe = [[dframe[i][j]+own[i][j] for j in range(3)] for i in range(3)]
            dc = sum(dframe[i][i] for i in range(3))/2
            da = [(dframe[2][1]-dframe[1][2])/2, (dframe[0][2]-dframe[2][0])/2,
                  (dframe[1][0]-dframe[0][1])/2]
            for axis in range(3):
                differential[6*node+3+axis][column] = factor*da[axis]+factor_derivative*dc*axial[axis]
            if column%6 < 3:
                input_node, input_axis = divmod(column, 6)
                for axis in range(3):
                    value = rt[axis][input_axis]*(_Bound(int(node == input_node))-_Bound(1)/3)
                    value = value+sum(differentials[column][j][axis]*(rc[node][j]+uc[node][j]) for j in range(3))
                    differential[6*node+axis][column] = value
    return differential, tuple(chart_inverses)


def _identity(size):
    return [[_Bound(int(i == j)) for j in range(size)] for i in range(size)]


def _exp(vector):
    """Rodrigues coefficients with directed arithmetic and analytic tail.

    Sixty-five terms suffice on the explicitly bounded |theta|<=4 domain.
    The absolute remaining series is bounded by its first omitted term /
    (1-r), where successive absolute term ratios are at most 16/(130*131).
    """
    vector = [_Bound(value) for value in vector]
    argument = _dot(vector, vector)
    if argument.hi > 16:
        raise UncertifiedS3Restart("portable SO3 witness exceeds bounded four-radian domain")
    coefficients = []
    for offset in (1, 2):
        term, total = _Bound(1)/math.factorial(offset), _Bound(0)
        for k in range(65):
            total = total + term
            term = -term * argument / ((2*k+offset+1)*(2*k+offset+2))
        tail = term.absolute() / (_Bound(1)-_Bound(16)/(130*131))
        coefficients.append(total + _Bound(tail.hi.copy_negate(), tail.hi))
    x, y, z = vector
    cross = [[_Bound(0), -z, y], [z, _Bound(0), -x], [-y, x, _Bound(0)]]
    cross2 = _multiply(cross, cross)
    return [[_Bound(int(i == j))+coefficients[0]*cross[i][j]+coefficients[1]*cross2[i][j]
             for j in range(3)] for i in range(3)]


def _quaternion(rotation):
    """A proper-rotation witness, with its projection defect checked separately."""
    diagonals = [1+rotation[0][0]+rotation[1][1]+rotation[2][2],
                 1+rotation[0][0]-rotation[1][1]-rotation[2][2],
                 1-rotation[0][0]+rotation[1][1]-rotation[2][2],
                 1-rotation[0][0]-rotation[1][1]+rotation[2][2]]
    pivot = max(range(4), key=lambda i: diagonals[i].lo)
    if diagonals[pivot].lo <= 0:
        raise UncertifiedS3Restart("proper quaternion witness is unresolved")
    q = [None]*4
    q[pivot] = diagonals[pivot].sqrt()/2
    denominator = 4*q[pivot]
    if pivot == 0:
        q[1:] = [(rotation[2][1]-rotation[1][2])/denominator,
                 (rotation[0][2]-rotation[2][0])/denominator,
                 (rotation[1][0]-rotation[0][1])/denominator]
    else:
        q[0] = ((rotation[2][1]-rotation[1][2]) if pivot == 1 else
                (rotation[0][2]-rotation[2][0]) if pivot == 2 else
                (rotation[1][0]-rotation[0][1]))/denominator
        for j in range(1, 4):
            if j != pivot:
                q[j] = (rotation[pivot-1][j-1]+rotation[j-1][pivot-1])/denominator
    length = _norm(q)
    return [entry/length for entry in q]


def _rotation(q):
    w, x, y, z = q
    return [[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
            [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
            [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]]


def _spectral_upper(matrix):
    """Enclose the second largest exact eigenvalue from a checked 4x4 witness."""
    midpoint = np.array([[float((entry.lo+entry.hi)/2) for entry in row] for row in matrix])
    values, vectors = np.linalg.eigh(midpoint)
    if not np.isfinite(values).all() or not np.isfinite(vectors).all():
        raise UncertifiedS3Restart("nonfinite spectral witness")
    v = [[_Bound(value) for value in row] for row in vectors]
    vt_v = _multiply(_transpose(v), v)
    orthogonal = _norm([vt_v[i][j]-int(i == j) for i in range(4) for j in range(4)])
    if orthogonal.hi >= 1:
        raise UncertifiedS3Restart("uncertified spectral witness orthogonality")
    distance = orthogonal / (1+(_Bound(1)-orthogonal).sqrt())
    residual = _multiply(matrix, v)
    residual = _norm([residual[i][j]-v[i][j]*values[j] for i in range(4) for j in range(4)])
    matrix_norm = _norm([entry for row in matrix for entry in row])
    eta = residual + (matrix_norm+float(max(abs(values))))*distance
    gap = _Bound(float(values[-1]))-_Bound(float(values[-2]))-2*eta
    floor = _Bound(1e-11)*max(Decimal.from_float(np.finfo(float).tiny),
                             Decimal.from_float(float(max(abs(values)))))
    if gap.lo <= floor.hi:
        raise UncertifiedS3Restart("uncertified simple largest Procrustes eigenvalue")
    return _Bound(float(values[-2]))+eta


@dataclass(frozen=True)
class AssociationCertificate:
    local_error: np.ndarray
    spectral_residual: tuple
    spectral_separation: tuple


def association(reference, physical, anchors, local):
    """Certify each archived nodal rotation; translations are independent checks.

    Rfit_i=Exp(theta_i) anchor_i Exp(-phi_i) is formed from archived inputs.
    No producer eigenpair, average of nodal fits, or echoed expected vector is
    used. Residual/separation bounds cover the unique real Procrustes fit.
    """
    reference, physical, local = map(lambda x: np.asarray(x, dtype=float),
                                      (reference, physical, local))
    if (reference.shape != (3, 3) or physical.shape != (18,) or local.shape != (18,)
            or not all(np.isfinite(x).all() for x in (reference, physical, local))):
        raise UncertifiedS3Restart("bounded finite native S3 association inputs required")
    anchors = np.tile(np.eye(3), (3, 1, 1)) if anchors is None else np.asarray(anchors)
    r = [[_Bound(value) for value in row] for row in reference]
    u = [[_Bound(value) for value in row] for row in physical.reshape(3, 6)[:, :3]]
    rc = [[r[i][j]-sum(row[j] for row in r)/3 for j in range(3)] for i in range(3)]
    uc = [[u[i][j]-sum(row[j] for row in u)/3 for j in range(3)] for i in range(3)]
    scale2 = sum((entry.square() for row in rc for entry in row), _Bound(0))
    covariance = [[sum((rc[i][a]+uc[i][a])*rc[i][b] for i in range(3))/scale2
                   for b in range(3)] for a in range(3)]
    trace = sum(covariance[i][i] for i in range(3))
    axial = [covariance[2][1]-covariance[1][2], covariance[0][2]-covariance[2][0],
             covariance[1][0]-covariance[0][1]]
    matrix = [[trace]+axial]+[[axial[i]]+[covariance[i][j]+covariance[j][i]-trace*int(i == j)
                                       for j in range(3)] for i in range(3)]
    second_upper = _spectral_upper(matrix)
    error = np.zeros(18); residuals, separations = [], []
    for node in range(3):
        phi = local[6*node+3:6*node+6]
        phi_length = _norm([_Bound(value) for value in phi])
        chart_limit = _Bound(Decimal("0.9"))*_Bound(_PI_LO, _PI_HI)
        if phi_length.hi >= chart_limit.lo:
            raise UncertifiedS3Restart("archived local rotation exceeds frozen relative chart")
        physical_rotation = _multiply(_exp(physical[6*node+3:6*node+6]),
                                      [[_Bound(value) for value in row] for row in anchors[node]])
        fit = _multiply(physical_rotation, _exp(-phi))
        quaternion = _quaternion(fit)
        rotation = _rotation(quaternion)
        mq = [_dot(row, quaternion) for row in matrix]
        eigenvalue = _dot(quaternion, mq)
        residual = _norm([mq[i]-eigenvalue*quaternion[i] for i in range(4)])
        separation = eigenvalue-second_upper
        if separation.lo <= 0:
            raise UncertifiedS3Restart("archived rotation is not certified in largest eigenspace")
        # Davis-Kahan residual bound, sign-aligned unit quaternion; the proper
        # rotation's operator distance is at most twice the quaternion distance.
        rotation_error = 2*_Bound(2).sqrt()*residual/_Bound(separation.lo)
        projection_error = _norm([fit[i][j]-rotation[i][j] for i in range(3) for j in range(3)])
        angular_error = 2*(rotation_error+projection_error)
        if angular_error.hi >= (chart_limit-_Bound(phi_length.hi)).lo:
            raise UncertifiedS3Restart("local logarithm uncertainty crosses frozen chart boundary")
        rt = _transpose(rotation)
        for axis in range(3):
            expected = _dot(rt[axis], uc[node])+sum((rt[axis][j]-int(axis == j))*rc[node][j]
                                                    for j in range(3))
            defect = (_Bound(local[6*node+axis])-expected).absolute()
            bound = defect+rotation_error*_norm([rc[node][j]+uc[node][j] for j in range(3)])
            error[6*node+axis] = bound.upper_float()
        error[6*node+3:6*node+6] = angular_error.upper_float()
        residuals.append(residual.upper_float())
        separations.append(float(np.nextafter(float(separation.lo), -math.inf)))
    error.setflags(write=False)
    return AssociationCertificate(error, tuple(residuals), tuple(separations))


def _rounded(value, operations):
    """IEEE binary64 operation-count enclosure; no dimensionful floor."""
    unit = _Bound(_UNIT_ROUNDOFF)
    gamma = operations*unit/(1-operations*unit)
    # IEEE round-to-nearest, including underflow: |fl(x)-x| <= u|x|+
    # half the minimum subnormal. This is a derived absolute rounding term,
    # not a dimensionful state/history tolerance or numerical floor.
    radius = gamma*value.absolute()+operations*(_Bound(_MIN_SUBNORMAL)/2)/(1-operations*unit)
    return value+_Bound(radius.hi.copy_negate(), radius.hi)


def _float_dot(coefficients, values):
    terms = [_Bound(a)*b for a, b in zip(coefficients, values)]
    exact = sum(terms, _Bound(0))
    unit = _Bound(_UNIT_ROUNDOFF);operations = 2*len(terms)
    radius = (operations*unit/(1-operations*unit)*sum((term.absolute() for term in terms), _Bound(0))
              +operations*(_Bound(_MIN_SUBNORMAL)/2)/(1-operations*unit))
    return exact+_Bound(radius.hi.copy_negate(), radius.hi)


def _float_sum(terms):
    terms = list(terms)
    unit = _Bound(_UNIT_ROUNDOFF)
    gamma = len(terms)*unit/(1-len(terms)*unit)
    radius = (gamma*sum((term.absolute() for term in terms), _Bound(0))
              +len(terms)*(_Bound(_MIN_SUBNORMAL)/2)/(1-len(terms)*unit))
    return sum(terms, _Bound(0))+_Bound(radius.hi.copy_negate(), radius.hi)


def _power(base, exponent):
    if base.lo <= 0 or exponent < 0:
        raise UncertifiedS3Restart("unsupported power-law certificate domain")
    # Decimal ln/exp are correctly rounded to nearest. Enclose each with its
    # adjacent working-precision values before subsequent directed operations.
    with localcontext() as context:
        context.prec = _PRECISION
        low, high = base.lo.ln(), base.hi.ln()
        logarithm = _Bound(context.next_minus(low), context.next_plus(high))
        product = logarithm*_Bound(exponent)
        low, high = product.lo.exp(), product.hi.exp()
        return _Bound(context.next_minus(low), context.next_plus(high))


def _flow(alpha, curve):
    """One supported hardening branch; uncertain corners fail explicitly."""
    alpha = _Bound(alpha)
    if alpha.lo < 0:
        raise UncertifiedS3Restart("negative plastic-history certificate domain")
    y1, y2 = _Bound(float(curve.eps_p_y1)), _Bound(float(curve.eps_p_y2))
    p, y, y_next = map(_Bound, (float(curve.sigma_prop), float(curve.sigma_yield), float(curve.sigma_yield_2)))
    if alpha.hi <= y1.lo:
        slope = (y-p)/y1
        flow = p+slope*alpha
    elif alpha.lo > y1.hi and alpha.hi <= y2.lo:
        slope = (y_next-y)/(y2-y1)
        flow = y+slope*(alpha-y1)
    elif alpha.lo > y2.hi:
        base = alpha+float(curve._power_offset)
        if base.lo <= Decimal.from_float(1e-12):
            raise UncertifiedS3Restart("power-law floor is unresolved in certificate")
        flow = float(curve.K)*_power(base, float(curve.n))
        slope = _Bound(float(curve.n))*flow/base
    else:
        raise UncertifiedS3Restart("hardening corner is unresolved in certificate")
    if slope.lo < 0 or flow.lo <= 0:
        raise UncertifiedS3Restart("positive monotone hardening certificate required")
    return flow


def _inside(values, bounds, label):
    for value, bound in zip(np.asarray(values).flat, np.asarray(bounds, dtype=object).flat):
        exact = Decimal.from_float(float(value))
        if not bound.lo <= exact <= bound.hi:
            raise UncertifiedS3Restart("S3 "+label+" is outside its mechanical certificate")


def _point(strain, parent_plastic, parent_alpha, saved, index, E, nu, curve):
    """Certify one unchanged elastic or yielded same-parent update.

    Plastic consistency is scalar and monotone on a certified hardening branch.
    Its actual residual / an analytic derivative lower bound determines root
    uncertainty; the frozen 1e-10 residual criterion is only an admission cap.
    """
    E, nu = _Bound(E), _Bound(nu)
    modulus = _rounded(E/_float_sum([_Bound(1), -_rounded(nu*nu, 1)]), 1)
    c = [[modulus, _rounded(modulus*nu, 1), _Bound(0)],
         [_rounded(modulus*nu, 1), modulus, _Bound(0)],
         [_Bound(0), _Bound(0), _rounded(E/_rounded(2*_float_sum([_Bound(1), nu]), 1), 1)]]
    trial = [_float_dot(row, [strain[i]-float(parent_plastic[i]) for i in range(3)]) for row in c]
    b1, b2, b3 = _float_sum(trial[:2]), _float_sum([trial[0], -trial[1]]), trial[2]
    initial_flow = _flow(_Bound(float(parent_alpha)), curve)
    f0 = b1.square()/12+b2.square()/4+b3.square()-initial_flow.square()/3
    threshold = _Bound(float(1e-10))*_Bound(max(initial_flow.square().hi, Decimal(1)))
    sigma_saved = np.asarray(saved["layer_stress"])[index]
    plastic_saved = np.asarray(saved["plastic_strain"])[index]
    alpha_saved = float(np.asarray(saved["alpha"])[index])
    if f0.hi <= threshold.lo:
        if alpha_saved != float(parent_alpha) or not np.array_equal(plastic_saved, parent_plastic):
            raise UncertifiedS3Restart("elastic S3 update changed its exact predecessor history")
        _inside(sigma_saved, trial, "elastic stress")
        return trial
    if f0.lo <= threshold.hi:
        raise UncertifiedS3Restart("S3 yield-branch margin is unresolved")
    if alpha_saved <= float(parent_alpha):
        raise UncertifiedS3Restart("yielded S3 update has no positive plastic increment")
    stress = [_Bound(float(value)) for value in sigma_saved]
    phi = (stress[0].square()-stress[0]*stress[1]+stress[1].square())/3+stress[2].square()
    if (phi/3).lo <= Decimal.from_float(1e-30):
        raise UncertifiedS3Restart("plastic rate floor is unresolved")
    rate = 2*(phi/3).sqrt()
    multiplier = (_Bound(alpha_saved)-float(parent_alpha))/rate
    ca = _rounded(E/_rounded(3*_float_sum([_Bound(1), -nu]), 1), 1)
    shear = _rounded(E/_rounded(2*_float_sum([_Bound(1), nu]), 1), 1)

    def evaluate(lam):
        da, db = 1+ca*lam, 1+2*shear*lam
        sa, sb, tau = b1/da, b2/db, b3/db
        result = [_float_sum([sa, sb])/2, _float_sum([sa, -sb])/2, tau]
        phi = sa.square()/12+sb.square()/4+tau.square()
        if (phi/3).lo <= Decimal.from_float(1e-30):
            raise UncertifiedS3Restart("plastic consistency-rate enclosure crosses floor")
        rate = 2*(phi/3).sqrt()
        alpha = float(parent_alpha)+lam*rate
        flow = _flow(alpha, curve)
        return phi-flow.square()/3, flow, result, alpha

    # Establish a finite root bracket. Doubling is certificate work only; no
    # histories or driver trials are evaluated or published.
    upper = max(multiplier.hi, (_Bound(1)/E).hi)
    for _ in range(48):
        result = evaluate(_Bound(upper))
        if result[0].hi < 0:
            break
        upper = (_Bound(upper)*2).hi
    else:
        raise UncertifiedS3Restart("plastic consistency root bracket is uncertified")
    # -F' >= -phi' since alpha'(lambda)>0 and H>=0. This lower
    # bound remains valid without subtracting near-equal derivative terms.
    bracket = _Bound(0, upper)
    da, db = 1+ca*bracket, 1+2*shear*bracket
    derivative = 2*(ca*b1.square()/(12*da*da*da)
                    +2*shear*(b2.square()/4+b3.square())/(db*db*db))
    if derivative.lo <= 0:
        raise UncertifiedS3Restart("plastic consistency derivative has no positive lower bound")
    # Certify the same monotone hardening branch over the entire root bracket.
    evaluate(bracket)
    residual, flow, _, _ = evaluate(multiplier)
    cap = _Bound(float(1e-10))*_Bound(max(flow.square().hi, Decimal(1)))
    if residual.absolute().hi > cap.lo:
        raise UncertifiedS3Restart("saved plastic state exceeds frozen local consistency criterion")
    radius = residual.absolute()/_Bound(derivative.lo)
    root = _Bound(max(Decimal(0), (_Bound(multiplier.lo)-radius).lo),
                  min(upper, (_Bound(multiplier.hi)+radius).hi))
    _, _, expected_stress, expected_alpha = evaluate(root)
    expected_stress = [_rounded(value, 16) for value in expected_stress]
    _inside(sigma_saved, expected_stress, "plastic stress")
    _inside([alpha_saved], [_rounded(expected_alpha, 16)], "plastic alpha")
    # Exact plane-stress compliance, same convention as the unchanged kernel.
    compliance = [[1/E, -nu/E, _Bound(0)], [-nu/E, 1/E, _Bound(0)],
                  [_Bound(0), _Bound(0), 2*(1+nu)/E]]
    expected_plastic = [strain[i]-_float_dot(compliance[i], expected_stress) for i in range(3)]
    _inside(plastic_saved, expected_plastic, "plastic strain")
    return expected_stress


def material(model, element, parent, saved, local_error):
    """Certify all fields from the fixed parent and return local force bounds."""
    from .e4_pl_s3_v2d_element import qualified_s3_lobatto_layers
    material = model.get_material(element.material_name)
    geometry = element._geometry(model.mesh)
    baseline = element._elastic_baseline_constitutive(material)
    operators = element._operators(geometry, baseline)
    bm, bk, bs = element._effective_station_operators(operators)
    transform = np.asarray(geometry["local_from_external"])
    components = element.compute_stiffness_components(model.mesh, material)
    phi_squared = float(components["phi_squared"])
    d = np.asarray(saved["committed_constitutive_u"], dtype=float)
    if not np.array_equal(d, saved["committed_total_u"]):
        raise UncertifiedS3Restart("portable S3 committed coordinate identities disagree")
    values = [_Bound(float(value)) for value in d]
    physical_values = [value+_Bound(-float(radius), float(radius))
                       for value, radius in zip(values, local_error)]
    local = [_float_dot(row, values) for row in transform]
    physical_local = [_float_dot(row, physical_values) for row in transform]
    epsilon = [[_float_dot(row, local) for row in station] for station in bm]
    curvature = [[_float_dot(row, local) for row in station] for station in bk]
    shear = [[_float_dot(row, local) for row in station] for station in bs]
    physical_epsilon = [[_float_dot(row, physical_local) for row in station] for station in bm]
    physical_curvature = [[_float_dot(row, physical_local) for row in station] for station in bk]
    physical_shear = [[_float_dot(row, physical_local) for row in station] for station in bs]
    order = tuple(int(v) for v in geometry["internal_order"])
    initial = np.asarray(parent["initial_generalized_prestrain"])[np.asarray(order)]
    initial_resultant = np.asarray(parent["initial_generalized_resultant"])[np.asarray(order)]
    if (not np.array_equal(saved["initial_generalized_prestrain"], parent["initial_generalized_prestrain"])
            or not np.array_equal(saved["initial_generalized_resultant"], parent["initial_generalized_resultant"])
            or saved["initial_field_provenance"] != parent["initial_field_provenance"]):
        raise UncertifiedS3Restart("portable S3 update changed exact initial-field identity")
    z, weights = qualified_s3_lobatto_layers(3, element.thickness)
    parent_plastic = np.asarray(parent["plastic_strain"]).reshape(3, 3, 3)
    parent_alpha = np.asarray(parent["alpha"]).reshape(3, 3)
    saved_internal = dict(saved)
    # Layer arrays use internal station order in the existing V2D contract.
    station_bounds, stress_bounds = [], []
    for station in range(3):
        generalized = epsilon[station]+curvature[station]+shear[station]
        _inside(np.asarray(saved["station_generalized_strain"])[order[station]], generalized,
                "generalized strain")
        stresses = []
        for layer in range(3):
            strain = [_float_sum([epsilon[station][axis], _rounded(float(z[layer])*curvature[station][axis], 1),
                                 -_Bound(float(initial[station, axis])),
                                 -_rounded(_Bound(float(z[layer]))*float(initial[station, axis+3]), 1)])
                      for axis in range(3)]
            physical_strain = [_float_sum([physical_epsilon[station][axis],
                                          _rounded(float(z[layer])*physical_curvature[station][axis], 1),
                                          -_Bound(float(initial[station, axis])),
                                          -_rounded(_Bound(float(z[layer]))*float(initial[station, axis+3]), 1)])
                               for axis in range(3)]
            index = 3*station+layer
            _inside(np.asarray(saved["layer_strain"])[index], strain, "layer strain")
            stresses.append(_point(physical_strain, parent_plastic[station, layer], parent_alpha[station, layer],
                                   saved_internal, index, float(baseline["E"]), float(baseline["nu"]),
                                   material.hardening_curve))
        membrane = [_float_dot(weights, [stresses[layer][axis] for layer in range(3)]) for axis in range(3)]
        bending = [_float_dot(weights, [float(z[layer])*stresses[layer][axis] for layer in range(3)])
                   for axis in range(3)]
        effective_shear = [_float_sum([physical_shear[station][axis], -_Bound(float(initial[station, axis+6]))])
                           for axis in range(2)]
        shear_resultant = [phi_squared*_float_dot(row, effective_shear) for row in np.asarray(baseline["H"])]
        resultant = [_float_sum([value, _Bound(float(initial_resultant[station, axis]))])
                     for axis, value in enumerate(membrane+bending+shear_resultant)]
        _inside(np.asarray(saved["station_generalized_resultant"])[order[station]], resultant,
                "generalized resultant")
        station_bounds.append(resultant);stress_bounds.append(stresses)
    force = [_Bound(0) for _ in range(18)]
    area = float(geometry["area"])/3
    for station in range(3):
        combined = np.vstack((bm[station], bk[station], bs[station]))
        for coordinate in range(18):
            force[coordinate] = force[coordinate]+area*_float_dot(combined[:, coordinate], station_bounds[station])
    force = [_float_dot(row, force) for row in transform.T]
    pl = np.asarray(components["pl"])
    force = [force[i]+_float_dot(pl[i], physical_values) for i in range(18)]
    # A componentwise operator envelope cannot hide an uncertain strain by
    # cancellation into a rigid/null mode. This is an additional conservative
    # value uncertainty, subsequently charged to the existing equilibrium cap.
    return tuple(force)


def replay(owner, trial, accepted, candidates, driver, residual, applied):
    """Charge full spatial pullback/material uncertainty to unchanged work cap."""
    count = len(owner._definition.shell.q4_elements)
    bounds = np.zeros(owner._K.shape[0])
    parents = owner._s3_restart_predecessors
    saved_certificates = owner._s3_restart_associations[0]
    for index, ((eid, element, slots, _), saved, candidate, parent, saved_certificate) in enumerate(zip(
            owner._shell_parts[count:], accepted[count:], candidates[count:], parents, saved_certificates)):
        reference = np.array([owner._shell_model.mesh.nodes[node].coords() for node in element.node_ids])
        anchors = None if trial.shell_anchors is None else trial.shell_anchors[slots[::6]//6]
        physical = trial.q[slots]
        candidate_certificate = association(reference, physical, anchors, candidate["committed_constitutive_u"])
        saved_force = material(owner._shell_model, element, parent, saved, saved_certificate.local_error)
        candidate_force = material(owner._shell_model, element, parent, candidate, candidate_certificate.local_error)
        force = []
        for a, b in zip(saved_force, candidate_force):
            low, high = max(a.lo, b.lo), min(a.hi, b.hi)
            if low > high:
                raise UncertifiedS3Restart("same-parent material force enclosures do not intersect")
            force.append(_Bound(low, high))
        differential, chart_inverses = work_map(reference, physical, anchors,
                                                 candidate["committed_constitutive_u"], candidate_certificate)
        spatial = [_dot(row, force) for row in _transpose(differential)]
        for node in range(3):
            start = 6*node+3
            spatial[start:start+3] = [_dot(row, spatial[start:start+3]) for row in chart_inverses[node]]
        observed = driver._s3_restart_receiver[eid]
        for slot, value, current in zip(slots, spatial, observed):
            radius = (value-_Bound(float(current))).absolute().upper_float()
            bounds[slot] = np.nextafter(bounds[slot]+radius, math.inf)
    # The registered metric is a work norm plus each actually loaded row.
    # Evaluate its worst-case interval value without a dimensionful work floor.
    free = owner._free
    worst = [_Bound(float(abs(residual[i])))+float(bounds[i]) for i in free]
    scale = [_Bound(float(value)) for value in owner._coordinate_scale[free]]
    loads = [_Bound(float(value)) for value in applied[free]]
    numerator = _norm([value*weight for value, weight in zip(worst, scale)])
    denominator = _norm([value*weight for value, weight in zip(loads, scale)])
    if denominator.lo <= 0:
        raise UncertifiedS3Restart("portable equilibrium has no positive resolved applied work")
    ratio = (numerator/_Bound(denominator.lo)).upper_float()
    for value, load in zip(worst, loads):
        if load.lo != 0:
            ratio = max(ratio, (value/load.absolute()).upper_float())
    if not math.isfinite(ratio) or ratio > 1e-8:
        raise UncertifiedS3Restart("portable S3 uncertainty exceeds original equilibrium margin")
    return ratio
