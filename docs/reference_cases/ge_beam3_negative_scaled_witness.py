"""Positive diagonal congruence before bounded front-aware inertia.

No pivot modification or entry removal. Coordinate scales are finite positive
Decimals, so their approximation does not change the congruence identity.
Roundtrip and reconstruction error are checked in original coordinates too.
"""
from decimal import Decimal as D
from docs.reference_cases.ge_beam3_negative_factor_witness import factor_witness as unscaled


def witness(matrix, checkpoint=lambda:None):
    n=len(matrix)
    if not 1<=n<=512 or any(len(row)!=n for row in matrix):raise ValueError('bounded square matrix')
    if any(type(x) is not D or not x.is_finite() for row in matrix for x in row):raise ValueError('finite Decimal matrix')
    if any(matrix[i][j]!=matrix[j][i] for i in range(n) for j in range(i)):raise ValueError('exact symmetric energy matrix')
    scales=[]
    for i,row in enumerate(matrix):
        checkpoint()
        magnitude=abs(row[i]) or max(abs(x) for x in row)
        if not magnitude:raise ValueError('unresolved zero coordinate')
        scale=D(1)/magnitude.sqrt()
        if not scale.is_finite() or scale<=0:raise ValueError('positive finite congruence scale')
        scales.append(scale)
    transformed=[[D(0)]*n for _ in range(n)]
    source_norm=max(D(1),max(abs(x) for row in matrix for x in row))
    roundtrip=D(0)
    for i in range(n):
        checkpoint()
        for j in range(i,n):
            factor=scales[i]*scales[j]
            value=matrix[i][j]*factor
            transformed[i][j]=transformed[j][i]=value
            roundtrip=max(roundtrip,abs(value/factor-matrix[i][j])/source_norm)
    result=unscaled(transformed,checkpoint)
    transformed_norm=max(D(1),max(abs(x) for row in transformed for x in row))
    error_bound=(D(result['reconstruction_relative'])*transformed_norm/min(scales)**2/source_norm+roundtrip)
    if error_bound>D('1e-60'):raise ValueError('original-coordinate reconstruction bound')
    original=[D(x)*scale for x,scale in zip(result.pop('negative_direction'),scales)]
    peak=max(range(n),key=lambda i:(abs(original[i]),-i))
    normalizer=original[peak]
    direction=[x/normalizer for x in original]
    return dict(**result,negative_direction=[str(x) for x in direction],positive_diagonal_congruence=True,
                coordinate_scales=[str(x) for x in scales],
                original_reconstruction_bound=str(error_bound),coordinate_roundtrip_relative=str(roundtrip))
