"""Bounded same-author Decimal audit from supplied station equations.

No production mechanics imports. Audits arithmetic on supplied binary64
section and quadrature data, not geometry accuracy or certified intervals.
"""
from decimal import Decimal as D, localcontext
from time import monotonic
from docs.reference_cases.ge_beam3_decimal_chain_audit import (
    product, transpose, select, subtract, cholesky, triangular_solve,
)


def zeros(n, m): return [[D(0)]*m for _ in range(n)]
def eye(n): return [[D(int(i == j)) for j in range(n)] for i in range(n)]
def solve(a, b):
    root = cholesky(a)
    return triangular_solve(transpose(root), triangular_solve(root, b, True), False)
def add(a, b): return [[x+y for x, y in zip(r, s)] for r, s in zip(a, b)]
def scaled(a, w): return [[w*x for x in row] for row in a]
def dot(a, b): return sum((x*y for x, y in zip(a, b)), D(0))
def vec(a, b): return [dot(row, b) for row in a]
def decimal(x):
    if type(x) is not float: raise ValueError('explicit float station data required')
    value = D.from_float(x)
    if not value.is_finite(): raise ValueError('finite station data required')
    return value


def audit(data, *, digits=80):
    started = monotonic()
    if type(digits) is not int or not 60 <= digits <= 100: raise ValueError('bounded audit precision')
    if not 1 <= len(data['stations']) <= 48: raise ValueError('bounded station count')
    def check():
        if monotonic()-started > 60: raise ValueError('cell arithmetic audit deadline')
    with localcontext() as context:
        context.prec = digits
        c = [[decimal(x) for x in row] for row in data['elastic']]
        direction = [decimal(x) for x in data['direction']]; ag = direction[:3]; ak = direction[3:]
        yield_force = decimal(data['yield_force']); hardening = decimal(data['hardening'])
        p = [decimal(x) for x in data['retained']]
        d_inv = solve(select(c, range(3, 6), range(3, 6)), eye(3))
        coupling = select(c, range(3), range(3, 6)); cross = product(coupling, d_inv)
        schur = subtract(select(c, range(3), range(3)), product(cross, transpose(coupling)))
        count = len(data['stations']); stations = []
        a = zeros(6, 6); b = zeros(6, 12); s = zeros(12, 12)
        dz = zeros(6, count); dm = zeros(12, count); f = zeros(count, count)
        weights = []; z0 = []; accumulated = []
        for index, row in enumerate(data['stations']):
            check(); cell = row['cell']; w = decimal(row['weight']); t = decimal(row['t'])
            if type(cell) is not int or cell not in (0, 1) or w <= 0: raise ValueError('valid station cell/weight')
            v = [[decimal(x) for x in r] for r in row['v']]
            n = zeros(3, 12)
            for i in range(3): n[i][6*cell+i] = 1-t; n[i][6*cell+3+i] = t
            low = row.get('origin_low', [0., 0.])
            weights.append(w); z0.append(decimal(row['origin'][0])+decimal(low[0]))
            accumulated.append(decimal(row['origin'][1])+decimal(low[1]))
            vv = product(transpose(v), schur)
            aa = scaled(product(vv, v), w)
            bb = scaled(product(product(transpose(v), cross), n), w)
            s = add(s, scaled(product(product(transpose(n), d_inv), n), w))
            zz = vec(vv, ag); mm = vec(transpose(n), [x+y for x, y in zip(vec(transpose(cross), ag), ak)])
            for i in range(3):
                for j in range(3): a[3*cell+i][3*cell+j] += aa[i][j]
                for j in range(12): b[3*cell+i][j] += bb[i][j]
                dz[3*cell+i][index] = w*zz[i]
            for i in range(12): dm[i][index] = w*mm[i]
            f[index][index] = w*dot(ag, vec(schur, ag))
            stations.append((cell, w, v, n, z0[-1], accumulated[-1]))
        ai = solve(a, eye(6)); aib = product(ai, b)
        c0 = [r+[-x for x in t] for r, t in zip(ai, aib)]
        bottom = add(s, product(transpose(b), aib))
        c0 += [[-x for x in r]+t for r, t in zip(transpose(aib), bottom)]
        g = [r+t for r, t in zip(product(transpose(dz), ai), subtract(transpose(dm), product(transpose(dz), aib)))]
        k = subtract(f, product(product(transpose(dz), ai), dz))
        q = [row[:] for row in k]
        for i in range(count): q[i][i] += weights[i]*hardening
        radius = [w*(yield_force+hardening*old) for w, old in zip(weights, accumulated)]
        drive = [x-y for x, y in zip(vec(g, p), vec(k, z0))]
        pattern = data['increment_pattern']; active = [i for i, x in enumerate(pattern) if x != 0.]
        delta = [D(0)]*count
        if active:
            rhs = [[drive[i]-radius[i]*(1 if pattern[i] > 0. else -1)] for i in active]
            answer = solve(select(q, active, active), rhs)
            for i, row in zip(active, answer): delta[i] = row[0]
        derivative = [x-y for x, y in zip(vec(q, delta), drive)]
        residual = max((abs(derivative[i]+radius[i]*(1 if delta[i] > 0 else -1)) if i in active
                        else max(abs(derivative[i])-radius[i], D(0))) for i in range(count))
        if any(delta[i]*decimal(float(pattern[i])) <= 0 for i in active) or residual > D('1e-35'):
            raise ValueError('supplied active pattern does not solve source-equation audit')
        gradient = [x+y for x, y in zip(vec(c0, p), vec(transpose(g), [x+y for x, y in zip(z0, delta)]))]

        def force_error(z):
            assembled = [D(0)]*6
            for cell, w, v, n, old_z, old_p in stations:
                check(); gamma = vec(v, z[3*cell:3*cell+3]); moment = vec(n, p[6:])
                eg = [x-old_z*y for x, y in zip(gamma, ag)]
                normal = [x+y for x, y in zip(vec(schur, eg), vec(cross, moment))]
                trial_drive = dot(ag, normal)+dot(ak, moment)
                increment = max(abs(trial_drive)-yield_force-hardening*old_p, D(0))/(dot(ag, vec(schur, ag))+hardening)
                history = old_z+(1 if trial_drive >= 0 else -1)*increment
                elastic_gamma = [x-history*y for x, y in zip(gamma, ag)]
                normal = [x+y for x, y in zip(vec(schur, elastic_gamma), vec(cross, moment))]
                for i, value in enumerate(vec(transpose(v), normal)): assembled[3*cell+i] += w*value
            return sum(((x-y)**2 for x, y in zip(assembled, p[:6])), D(0)).sqrt()
        previous = [decimal(x) for x in data['old_gradient'][:6]]
        rounded = [D.from_float(float(x)) for x in gradient[:6]]
        pair = [hi+D.from_float(float(x-hi)) for x, hi in zip(gradient[:6], rounded)]
        return dict(digits=digits, active_count=len(active), source_kkt=str(residual),
            old_gradient_source_force_error=str(force_error(previous)),
            source_solution_force_error=str(force_error(gradient[:6])),
            rounded_gradient_force_error=str(force_error(rounded)),
            paired_gradient_force_error=str(force_error(pair)),
            gradient=[str(x) for x in gradient], increments=[str(x) for x in delta],
            production_qualified=False)
