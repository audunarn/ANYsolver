"""Bounded negative-direction producer; original inertia audits stay immutable."""
from decimal import Decimal as D
from docs.reference_cases.ge_beam3_front_aware_inertia import choose_pivots


def negative_block(block):
    if len(block)==1:
        return [D(1)] if block[0][0]<0 else None
    a,b,c=block[0][0],block[0][1],block[1][1]
    if a<0:return [D(1),D(0)]
    if c<0:return [D(0),D(1)]
    if a*c-b*b>=0:return None
    if a>0:return [-b/a,D(1)]
    return [-(c+1)/(2*b),D(1)]

def factor_witness(matrix, checkpoint=lambda: None):
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
        pivots = choose_pivots(a, floor, checkpoint)
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
    result = dict(negative=negative, positive=n-negative,
                pivot_sizes=[len(row[0]) for row in records],
                pivot_indices=[list(row[0]) for row in records],
                reconstruction_relative=str(error), max_front=width, updates=updates)


    selected=None
    for index,(pivots,block,columns,inverse_columns) in enumerate(records):
        y=negative_block(block)
        if y is not None:
            selected=(index,y);break
    if selected is None:raise ValueError('no negative pivot for witness')
    direction=[D(0)]*n
    for index in range(len(records)-1,-1,-1):
        checkpoint()
        pivots,block,columns,inverse_columns=records[index]
        y=selected[1] if index==selected[0] else [D(0)]*len(pivots)
        for j,p in enumerate(pivots):
            direction[p]=y[j]-sum((values[j]*direction[k] for k,values in inverse_columns.items()),D(0))
    value=sum((direction[i]*matrix[i][j]*direction[j] for i in range(n) for j in range(n)),D(0))
    if value>=0:raise ValueError('back-substitution did not produce negative work')
    return dict(**result,negative_direction=[str(x) for x in direction],
                selected_pivot=list(records[selected[0]][0]),decimal_directional_work=str(value))
