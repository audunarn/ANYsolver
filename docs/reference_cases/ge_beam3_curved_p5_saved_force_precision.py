"""Independent elastic translational-force audit of an immutable saved state.

Standard library only. No production/reference mechanics, AD, local stationarity
solve, global Newton step or qualification verdict. Decimal precision agreement
is a diagnostic, not an interval error bound or an exact-equilibrium proof.
"""

from decimal import Decimal as D, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path


ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-centered-chord32-20260906-e919f22758c948f5b22dbfcbd0b1fd3a/centered-chord32')
INPUTS = {
    'initial.json': (1157002, 'ae047a650282ba7f6870bf7b471372e85a6b2bbd831aec00d5eb4807c09e8cfa'),
    'failed_last.json': (1185851, '08329f11b7d7dd17566446f02da922fa008a9eb84ce7c709b264b4f293ab4422'),
}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate key')
        result[key] = value
    return result


def canonical(record):
    return json.dumps(record, allow_nan=False, sort_keys=True, separators=(',', ':')).encode()+b'\n'


def saved_inputs():
    records = {}
    for name, (size, digest) in INPUTS.items():
        data = (ROOT/name).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('immutable saved state mismatch')
        record = json.loads(data, object_pairs_hook=_pairs)
        if canonical(record) != data: raise ValueError('noncanonical saved state')
        records[name] = record
    initial, failed = records['initial.json'], records['failed_last.json']
    if (initial['target'] != .1 or failed['target'] != .095 or
            failed['disposition'] != 'UNCOMMITTED_DIAGNOSTIC_ONLY' or
            failed['replay_verified'] is not True or len(failed['response']['elements']) != 32):
        raise ValueError('registered state extent required')
    return initial['assembly']['positions'], failed


def dec(value):
    if type(value) is float: return D.from_float(value)
    return D(value)


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), D(0))


def transpose(a):
    return [list(row) for row in zip(*a)]


def matvec(a, x):
    return [dot(row, x) for row in a]


def gauss8():
    """Independently solve P8=0; same eight-point rule, not new quadrature."""
    positive = []
    for guess in ('0.18', '0.53', '0.80', '0.96'):
        x = D(guess)
        for _ in range(30):
            previous, current = D(1), x
            for n in range(2, 9):
                previous, current = current, ((2*n-1)*x*current-(n-1)*previous)/n
            derivative = 8*(x*current-previous)/(x*x-1)
            next_x = x-current/derivative
            if next_x == x or abs(next_x-x) < D(10)**(-localcontext_precision()+5):
                x = next_x;break
            x = next_x
        else: raise ValueError('bounded Gauss root iteration failed')
        # Recompute the derivative at the returned root.
        previous, current = D(1), x
        for n in range(2, 9):
            previous, current = current, ((2*n-1)*x*current-(n-1)*previous)/n
        derivative = 8*(x*current-previous)/(x*x-1)
        positive.append((x, 2/((1-x*x)*derivative*derivative)))
    return sorted([(-x, w) for x, w in positive]+positive)


def localcontext_precision():
    from decimal import getcontext
    return getcontext().prec


def half_force(reference, actual, u, cell, rule):
    """Derivative of the elastic axial/shear potential, rotations held fixed.

    F = integral[(400 I)/j + 600 a a^T/j^3] dxi on one half cell.
    z = U^T (xR-xL) - (XR-XL); endpoint forces are [-U F z, +U F z].
    Isotropic shear in the two transverse material directions makes roll
    irrelevant. This ideal orthonormal metric does not copy rounded frame code.
    """
    left, right = cell, cell+1
    chord = [actual[right][i]-actual[left][i] for i in range(3)]
    base = [reference[right][i]-reference[left][i] for i in range(3)]
    z = [value-base[i] for i, value in enumerate(matvec(transpose(u), chord))]
    material = [D(0)]*3
    for point, weight in rule:
        xi = cell-1+(point+1)/2
        shape_derivative = [xi-D('.5'), -2*xi, xi+D('.5')]
        a = [dot(shape_derivative, [node[i] for node in reference]) for i in range(3)]
        j2 = dot(a, a)
        if j2 <= 0: raise ValueError('positive reference metric required')
        j = j2.sqrt();az = dot(a, z)
        for i in range(3):
            material[i] += weight/2*(400*z[i]/j+600*a[i]*az/(j*j2))
    return matvec(u, material)


def independent_translations(reference, failed, precision):
    if type(precision) is not int or precision not in (60, 90):
        raise ValueError('registered 60/90-digit precision required')
    with localcontext() as ctx:
        ctx.prec = precision
        rule = gauss8()
        coordinates = [[dec(v) for v in row] for row in reference]
        actual = [[dec(v) for v in row] for row in failed['positions']]
        force = [[D(0)]*3 for _ in actual]
        for index, element in enumerate(failed['response']['elements']):
            # The saved case must remain the uncoupled, wholly elastic probe.
            for station in element['stations']:
                response = station['response']
                if (response['plastic_active'] is not False or
                        response['history'] != {'plastic_coordinate': 0., 'accumulated': 0.} or
                        any(response['tangent'][i][j] != (1000. if i == 0 else 400.)*(i == j)
                            for i in range(3) for j in range(3)) or
                        any(response['tangent'][i][j] != 0. for i in range(3) for j in range(3, 6))):
                    raise ValueError('uncoupled elastic section required')
            for cell in (0, 1):
                u = [[dec(v) for v in row] for row in element['local_rotations'][cell]]
                f = half_force(coordinates[2*index:2*index+3], actual[2*index:2*index+3], u, cell, rule)
                for i in range(3):
                    force[2*index+cell][i] -= f[i]
                    force[2*index+cell+1][i] += f[i]
        return force


def exact_saved_scatter(failed):
    """Exact Fraction addition of existing binary64 element translations."""
    force = [[Fraction(0)]*3 for _ in failed['positions']]
    for index, element in enumerate(failed['response']['elements']):
        for node in range(3):
            for i in range(3):
                force[2*index+node][i] += Fraction.from_float(element['residual'][6*node+i])
    return force


def free_norm(force):
    with localcontext() as ctx:
        ctx.prec = 80
        values = [dec(v) if not isinstance(v, Fraction) else D(v.numerator)/D(v.denominator)
                  for node, row in enumerate(force) if 0 < node < 64
                  for i, v in enumerate(row) if not (node == 32 and i == 1)]
        return dot(values, values).sqrt()


def audit():
    reference, failed = saved_inputs()
    low = independent_translations(reference, failed, 60)
    high = independent_translations(reference, failed, 90)
    scatter = exact_saved_scatter(failed)
    stored = [[dec(failed['response']['residual'][6*n+i]) for i in range(3)] for n in range(65)]
    with localcontext() as ctx:
        ctx.prec = 90
        scatter_decimal = [[D(v.numerator)/D(v.denominator) for v in row] for row in scatter]
        differences = lambda a, b: max(abs(x-y) for ar, br in zip(a, b) for x, y in zip(ar, br))
        return {'schema': 'GE_BEAM3_P5_SAVED_TRANSLATION_PRECISION_AUDIT_V1',
            'production_qualified': False, 'independent_equilibrium_proof': False,
            'scope': 'SAVED_ELASTIC_TRANSLATIONS_ONLY_NO_SOLVE',
            'stored_translation_norm': str(free_norm(stored)),
            'exact_scatter_translation_norm': str(free_norm(scatter)),
            'independent_60_translation_norm': str(free_norm(low)),
            'independent_90_translation_norm': str(free_norm(high)),
            'max_scatter_rounding': str(differences(scatter_decimal, stored)),
            'max_independent_stored_difference': str(differences(high, stored)),
            'max_60_90_difference': str(differences(high, low))}


if __name__ == '__main__':
    print(canonical(audit()).decode(), end='')
