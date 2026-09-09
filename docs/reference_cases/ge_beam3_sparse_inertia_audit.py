"""Bounded full-coupling Decimal congruence audit; no mechanics imports.

Sparse Schur updates with scalar or 2x2 symmetric pivots, no entry dropping.
This is not LAPACK, a certified interval bound, or an independent author review.
Reconstruction and a second precision are mandatory at the caller.
"""
from decimal import Decimal as D
from decimal import localcontext
from math import isfinite
from time import monotonic

def audit(left,right,geometric,kinetic,free,algebraic,shifts,*,digits=80):
    start=monotonic()
    def check():
        if monotonic()-start>120: raise ValueError('signed inertia audit deadline')
    if type(digits) is not int or digits not in (80,100): raise ValueError('registered precision')
    if any(type(a) is not list or not a for a in (left,right,geometric,kinetic)):
        raise ValueError('nonempty explicit matrices')
    n=len(geometric); link=len(right)
    if not 2<=n<=512 or not 1<=link<=512 or len(left)>8192 or len(kinetic)>8192:
        raise ValueError('bounded factor dimensions')
    for a,width in ((left,link),(right,n),(geometric,n),(kinetic,n)):
        if any(type(row) is not list or len(row)!=width or any(type(x) is not float or not isfinite(x) for x in row) for row in a):
            raise ValueError('finite rectangular binary64 factors')
    if any(geometric[i][j]!=geometric[j][i] for i in range(n) for j in range(n)):
        raise ValueError('symmetric geometric factor')
    for slots in (free,algebraic):
        if type(slots) is not tuple or len(set(slots))!=len(slots) or any(type(i) is not int or not 0<=i<n for i in slots):
            raise ValueError('complete exact DOF sets')
    physical=tuple(i for i in free if i not in algebraic)
    if not physical or not set(algebraic)<=set(free): raise ValueError('physical/algebraic split')
    if any(row[j]!=0. for row in kinetic for j in algebraic): raise ValueError('massless algebraic coordinates')
    if type(shifts) is not tuple or not 1<=len(shifts)<=25 or any(type(x) is not float or not isfinite(x) for x in shifts):
        raise ValueError('bounded explicit binary64 shifts')
    with localcontext() as ctx:
        ctx.prec=digits
        def sparse(a): return [{i:D.from_float(x) for i,x in enumerate(row) if x!=0.} for row in a]
        ll,rr,bb=map(sparse,(left,right,kinetic)); ff=[]
        for row in ll:
            check(); out={}
            for j,value in row.items():
                for k,v in rr[j].items():out[k]=out.get(k,D(0))+value*v
            ff.append(out)
        def gram(rows):
            result=[[D(0)]*n for _ in range(n)]
            for row in rows:
                check(); entries=sorted(row.items())
                for index,(i,x) in enumerate(entries):
                    for j,y in entries[index:]:
                        result[i][j]+=x*y
            for i in range(n):
                for j in range(i):result[i][j]=result[j][i]
            return result
        k=gram(ff);m=gram(bb)
        for i in range(n):
            for j in range(n):k[i][j]+=D.from_float(geometric[i][j])
        def sub(a,slots):return [[a[i][j] for j in slots] for i in slots]
        if algebraic and inertia(sub(k,algebraic),check)['negative']:
            raise ValueError('unstable algebraic stiffness cannot be dropped')
        if inertia(sub(m,physical),check)['negative']:raise ValueError('nonpositive physical mass')
        rows=[]
        for shift in shifts:
            check(); lam=D.from_float(shift)
            result=inertia([[k[i][j]-lam*m[i][j] for j in free] for i in free],check)
            rows.append(dict(shift=shift,**result))
        check()
        return dict(digits=digits,rows=rows,physical_dimension=len(physical),algebraic_dimension=len(algebraic),
                    trace_positive=True,mass_positive=True,certified_intervals=False,mechanics_reconstructed=False)


def inertia(matrix, checkpoint=lambda: None):
    n = len(matrix)
    if not 1 <= n <= 512 or any(len(row) != n for row in matrix):
        raise ValueError('bounded square audit matrix')
    if any(type(x) is not D or not x.is_finite() for row in matrix for x in row):
        raise ValueError('finite Decimal entries required')
    if any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(i)):
        raise ValueError('exact symmetric audit matrix')
    a = {i: {j: v for j, v in enumerate(row) if v} for i, row in enumerate(matrix)}
    scale = max(D(1), max(abs(x) for row in matrix for x in row))
    floor = scale * D('1e-50')
    negative = updates = width = 0
    records = []
    while a:
        checkpoint()
        i = min(a, key=lambda k: (len(a[k]), k))
        neighbours = [j for j in a[i] if j != i]
        j = max(neighbours, key=lambda k: (abs(a[i][k]), -k), default=i)
        off = abs(a[i].get(j, D(0))) if j != i else D(0)
        aa = a[i].get(i, D(0))
        if max(abs(aa), off) <= floor:
            raise ValueError('unresolved signed pivot')
        if abs(aa) >= off / 2:
            pivots = (i,)
        elif abs(a[j].get(j, D(0))) >= off / 2:
            pivots = (j,)
        else:
            pivots = (i, j)
        surround = sorted(set().union(*(a[k] for k in pivots)) - set(pivots))
        width = max(width, len(surround))
        if width > 96:
            raise ValueError('sparse fill width bound')
        block = [[a[k].get(l, D(0)) for l in pivots] for k in pivots]
        columns = {k: [a[k].get(p, D(0)) for p in pivots] for k in surround}
        if len(pivots) == 1:
            pivot = block[0][0]
            if abs(pivot) <= floor:
                raise ValueError('unresolved scalar pivot')
            negative += int(pivot < 0)
            inverse_columns = {k: [v[0] / pivot] for k, v in columns.items()}
        else:
            aa, bb, cc = block[0][0], block[0][1], block[1][1]
            det = aa * cc - bb * bb
            if abs(det) <= floor * max(abs(aa), abs(bb), abs(cc)):
                raise ValueError('unresolved block pivot')
            negative += 1 if det < 0 else 2 if aa + cc < 0 else 0
            inverse_columns = {k: [(cc*x-bb*y)/det, (aa*y-bb*x)/det]
                               for k, (x, y) in columns.items()}
        for r, k in enumerate(surround):
            for l in surround[r:]:
                updates += 1
                if updates > 2_000_000:
                    raise ValueError('sparse arithmetic work bound')
                delta = sum((x*y for x, y in zip(columns[k], inverse_columns[l])), D(0))
                value = a[k].get(l, D(0)) - delta
                if abs(value) > scale * D('1e12'):
                    raise ValueError('sparse pivot growth bound')
                if value:
                    a[k][l] = a[l][k] = value
                else:
                    a[k].pop(l, None); a[l].pop(k, None)
        records.append((pivots, block, columns, inverse_columns))
        for k in surround:
            for p in pivots:
                a[k].pop(p, None)
        for p in pivots:
            del a[p]
    # Reverse every Schur update, including all original off-diagonal entries.
    recovered = [[D(0)] * n for _ in range(n)]
    for pivots, block, columns, inverse_columns in reversed(records):
        checkpoint()
        for r, k in enumerate(pivots):
            for s, l in enumerate(pivots):
                recovered[k][l] = block[r][s]
        for k, values in columns.items():
            for p, v in zip(pivots, values):
                recovered[k][p] = recovered[p][k] = v
        surround = sorted(columns)
        for r, k in enumerate(surround):
            for l in surround[r:]:
                value = recovered[k][l] + sum((x*y for x, y in zip(columns[k], inverse_columns[l])), D(0))
                recovered[k][l] = recovered[l][k] = value
    error = max(abs(recovered[i][j]-matrix[i][j]) for i in range(n) for j in range(n))/scale
    if error > D('1e-60'):
        raise ValueError('sparse full-matrix reconstruction failed')
    return dict(negative=negative, positive=n-negative,
                pivot_sizes=[len(row[0]) for row in records],
                reconstruction_relative=str(error), max_front=width, updates=updates)
