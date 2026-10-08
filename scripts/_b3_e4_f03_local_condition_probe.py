"""Bounded synthetic exact-input condition certificates (N <= 64).

Every supplied finite binary64 entry is treated as an exact rational input.
Fraction products/sums make residual and comparison recurrences exact; only
public float bounds round outward, checked against those exact Fractions.
This dense research probe is not a sparse scientific admission method.
"""
from __future__ import annotations

from fractions import Fraction as F
import math

import numpy as np
from scipy import sparse


MAX_N=64
CONDITION_LIMIT=1e10
AMPLIFIED_BACKWARD_LIMIT=1e-8
Z=F(0);O=F(1)


def _matrix(value,name:str,n:int|None=None) -> tuple[tuple[F,...],...]:
    sparse_input=sparse.issparse(value)
    if sparse_input:
        if not isinstance(value,(sparse.csr_matrix,sparse.csc_matrix)):
            raise ValueError(f'{name} needs canonical CSR/CSC sparse storage')
    elif type(value) is not np.ndarray or value.ndim!=2:
        raise ValueError(f'{name} must be a finite float64 matrix')
    rows,cols=value.shape
    if rows<1 or cols<1 or rows>MAX_N or cols>MAX_N or (n is not None and (rows,cols)!=(n,n)):
        raise ValueError(f'{name} exceeds hard synthetic N<=64 shape cap')
    if value.dtype!=np.float64:
        raise ValueError(f'{name} must be a finite float64 matrix')
    if sparse_input:
        # A cached canonical flag is not a structural validator. Inspect
        # bounded buffers before any native sparse traversal, then own them.
        outer,inner=(rows,cols) if isinstance(value,sparse.csr_matrix) else (cols,rows)
        data,indices,pointer=value.data,value.indices,value.indptr
        if (any(type(a) is not np.ndarray or a.ndim!=1 for a in (data,indices,pointer)) or
                data.dtype!=np.float64 or indices.dtype not in (np.dtype('int32'),np.dtype('int64')) or
                pointer.dtype not in (np.dtype('int32'),np.dtype('int64')) or
                len(data)!=len(indices) or len(data)>rows*cols or len(pointer)!=outer+1):
            raise ValueError(f'{name} has invalid bounded sparse structure')
        data=data.copy();indices=indices.copy();pointer=pointer.copy()
        if (pointer[0]!=0 or pointer[-1]!=len(data) or np.any(pointer<0) or
                np.any(pointer>len(data)) or np.any(pointer[1:]<pointer[:-1]) or
                np.any(indices<0) or np.any(indices>=inner)):
            raise ValueError(f'{name} has invalid bounded sparse structure')
        for start,end in zip(pointer,pointer[1:]):
            segment=indices[start:end]
            if np.any(segment[1:]<=segment[:-1]):
                raise ValueError(f'{name} needs canonical CSR/CSC sparse storage')
        if not np.isfinite(data).all(): raise ValueError(f'{name} contains nonfinite input')
        # Direct bounded scatter avoids a second traversal of caller-owned
        # sparse metadata after validation. All indices above are checked.
        dense=np.zeros((rows,cols),dtype=np.float64)
        for major,(start,end) in enumerate(zip(pointer,pointer[1:])):
            if isinstance(value,sparse.csr_matrix): dense[major,indices[start:end]]=data[start:end]
            else: dense[indices[start:end],major]=data[start:end]
    else:
        dense=value.copy()
        if not np.isfinite(dense).all(): raise ValueError(f'{name} contains nonfinite input')
    return tuple(tuple(F.from_float(float(x)) for x in row) for row in dense)


def _vector(value,name:str,n:int) -> tuple[F,...]:
    if (type(value) is not np.ndarray or value.dtype!=np.float64 or
            value.shape!=(n,) or not np.all(np.isfinite(value))):
        raise ValueError(f'{name} must be a finite float64 length-N vector')
    return tuple(F.from_float(float(x)) for x in value)


def _upper(x:F) -> float:
    if x<0:raise ValueError('nonnegative exact bound required')
    try:v=float(x)
    except OverflowError as exc:raise ArithmeticError('bound overflows float64') from exc
    if not math.isfinite(v):raise ArithmeticError('bound overflows float64')
    if F.from_float(v)<x:v=math.nextafter(v,math.inf)
    if not math.isfinite(v) or F.from_float(v)<x:
        raise ArithmeticError('outward upper conversion failed')
    return v


def _lower(x:F) -> float:
    if x<0:raise ValueError('nonnegative exact bound required')
    try:v=float(x)
    except OverflowError as exc:raise ArithmeticError('bound overflows float64') from exc
    if not math.isfinite(v):raise ArithmeticError('bound overflows float64')
    if F.from_float(v)>x:v=math.nextafter(v,-math.inf)
    if v<0 or F.from_float(v)>x:
        raise ArithmeticError('outward lower conversion failed')
    return v


def _sqrt_out(x:F,upper:bool) -> float:
    if x<0:raise ValueError('negative squared norm')
    try:v=math.sqrt(float(x))
    except OverflowError as exc:raise ArithmeticError('square root overflows float64') from exc
    if not math.isfinite(v):raise ArithmeticError('square root overflows float64')
    exact=F.from_float(v)**2
    if upper and exact<x:v=math.nextafter(v,math.inf)
    if not upper and exact>x:v=math.nextafter(v,-math.inf)
    if (not math.isfinite(v) or v<0 or
        ((F.from_float(v)**2<x) if upper else (F.from_float(v)**2>x))):
        raise ArithmeticError('outward square-root conversion failed')
    return v


def _induced(A:tuple[tuple[F,...],...]) -> tuple[F,F]:
    rows=len(A);cols=len(A[0])
    return (max(sum((abs(A[i][j]) for i in range(rows)),Z)
                for j in range(cols)),
            max(sum((abs(v) for v in row),Z) for row in A))


def _matmul(A,B):
    n=len(A);m=len(B[0]);inner=len(B)
    return tuple(tuple(sum((A[i][k]*B[k][j] for k in range(inner)),Z)
                       for j in range(m)) for i in range(n))


def _difference(A,B):
    return tuple(tuple(x-y for x,y in zip(row,brow))
                 for row,brow in zip(A,B))


def _identity(n):
    return tuple(tuple(O if i==j else Z for j in range(n)) for i in range(n))


def _permutation(indices,n,name):
    if (type(indices) not in (tuple,list) or len(indices)!=n or
            any(type(i) is not int for i in indices) or
            set(indices)!=set(range(n))):
        raise ValueError(f'{name} must be a complete permutation')
    return tuple(indices)


def _triangular_comparison(T,lower:bool,rhs:tuple[F,...],transpose:bool=False):
    n=len(T)
    order=range(n) if lower!=transpose else range(n-1,-1,-1)
    result=[Z]*n
    for i in order:
        pivot=abs(T[i][i])
        if pivot==0:raise ZeroDivisionError('triangular comparison has zero pivot')
        terms=(abs(T[j][i])*result[j] if transpose else abs(T[i][j])*result[j]
               for j in range(n) if (j<i if lower!=transpose else j>i))
        result[i]=(rhs[i]+sum(terms,Z))/pivot
    return tuple(result)


def _backward(H,b,z) -> dict:
    if (b is None)!=(z is None):raise ValueError('b and z must both be supplied')
    if b is None:return {'backward_error_upper':None,
                          'amplified_backward_upper':None,
                          'backward_gate':None}
    n=len(H);b=_vector(b,'b',n);z=_vector(z,'z',n)
    residual=tuple(sum((H[i][j]*z[j] for j in range(n)),Z)-b[i]
                   for i in range(n))
    r2=sum((x*x for x in residual),Z)
    z2=sum((x*x for x in z),Z);b2=sum((x*x for x in b),Z)
    h2=max((sum((x*x for x in row),Z) for row in H),default=Z)
    h2=max(h2,*(sum((H[i][j]**2 for i in range(n)),Z) for j in range(n)))
    h_lower=_sqrt_out(h2,False)
    z_lower=_sqrt_out(z2,False);b_lower=_sqrt_out(b2,False)
    denom=_lower(F.from_float(h_lower)*F.from_float(z_lower)+F.from_float(b_lower))
    if denom<=0:raise ArithmeticError('zero backward denominator lower bound')
    residual_upper=_sqrt_out(r2,True)
    bound=_upper(F.from_float(residual_upper)/F.from_float(denom))
    return {'residual_2_upper':residual_upper,'h2_lower':h_lower,
            'z2_lower':z_lower,'b2_lower':b_lower,
            'backward_denominator_lower':denom,
            'backward_error_upper':bound}


def _finish(method,H,b1,bi,raw,work,b,z):
    h1,hi=_induced(H)
    inverse=_sqrt_out(b1*bi,True)
    condition=_sqrt_out(h1*hi*b1*bi,True)
    backward=_backward(H,b,z)
    amp=(None if backward['backward_error_upper'] is None else
         _upper(F.from_float(condition)*F.from_float(backward['backward_error_upper'])))
    condition_gate=condition<=CONDITION_LIMIT
    backward_gate=None if amp is None else amp<=AMPLIFIED_BACKWARD_LIMIT
    status=('HOLD' if not condition_gate or backward_gate is False else
            ('CONDITION_BOUND_ONLY' if backward_gate is None else
             'CERTIFIED_WITHIN_LIMIT'))
    return {'method':method,
            'status':status,
            'reason':None if status!='HOLD'
                     else ('condition upper exceeds fixed limit' if not condition_gate
                           else 'amplified backward upper exceeds fixed limit'),
            'bounds':{'h1_upper':_upper(h1),'hi_upper':_upper(hi),
                      'b1_upper':_upper(b1),'bi_upper':_upper(bi),
                      'inverse_2_upper':inverse,'condition_2_upper':condition,
                      **backward,'amplified_backward_upper':amp,
                      'condition_gate':condition_gate,'backward_gate':backward_gate},
            'exact':{'h1':h1,'hi':hi,'b1':b1,'bi':bi,**raw},
            'work':work}


def certificate_a(H:np.ndarray,*,inverse_columns:np.ndarray|None=None,
                  b:np.ndarray|None=None,z:np.ndarray|None=None) -> dict:
    """All-column Neumann certificate; N synthetic RHS solves if Y omitted."""
    Hq=_matrix(H,'H');n=len(Hq)
    if n!=len(Hq[0]):raise ValueError('H must be square')
    if inverse_columns is None:
        try:Y=np.linalg.solve(np.array(Hq,dtype=np.float64),
                              np.eye(n,dtype=np.float64))
        except np.linalg.LinAlgError:
            return {'method':'A','status':'HOLD','reason':'singular inverse-column solve',
                    'bounds':{},'exact':{},
                    'work':{'dimension':n,'inverse_columns':n,'rhs_solves':n,
                            'exact_product_terms':0}}
        rhs_solves=n
    else:
        Y=inverse_columns;rhs_solves=0
    Yq=_matrix(Y,'all inverse columns',n)
    E=_difference(_identity(n),_matmul(Hq,Yq))
    y1,yi=_induced(Yq);e1,ei=_induced(E)
    raw={'y1':y1,'yi':yi,'e1':e1,'ei':ei}
    work={'dimension':n,'inverse_columns':n,'rhs_solves':rhs_solves,
          'exact_product_terms':n**3,'residual_entries':n*n}
    if e1>=1 or ei>=1:
        return {'method':'A','status':'HOLD','reason':'inverse residual not contractive',
                'bounds':{'y1_upper':_upper(y1),'yi_upper':_upper(yi),
                          'e1_upper':_upper(e1),'ei_upper':_upper(ei)},
                'exact':raw,'work':work}
    result=_finish('A',Hq,y1/(1-e1),yi/(1-ei),raw,work,b,z)
    result['bounds'].update({'y1_upper':_upper(y1),'yi_upper':_upper(yi),
                             'e1_upper':_upper(e1),'ei_upper':_upper(ei)})
    return result


def certificate_b(H:np.ndarray,L:np.ndarray,U:np.ndarray,*,
                  row_perm:tuple[int,...]|None=None,
                  col_perm:tuple[int,...]|None=None,
                  b:np.ndarray|None=None,z:np.ndarray|None=None) -> dict:
    """Exact synthetic LU residual and positive triangular comparisons."""
    Hq=_matrix(H,'H');n=len(Hq)
    if n!=len(Hq[0]):raise ValueError('H must be square')
    Lq=_matrix(L,'L',n);Uq=_matrix(U,'U',n)
    rows=_permutation(tuple(range(n)) if row_perm is None else row_perm,n,'row_perm')
    cols=_permutation(tuple(range(n)) if col_perm is None else col_perm,n,'col_perm')
    if any(Lq[i][j]!=0 for i in range(n) for j in range(i+1,n)) or any(
            Uq[i][j]!=0 for i in range(n) for j in range(i)):
        raise ValueError('declared triangular factors contain opposite entries')
    work={'dimension':n,'factor_product_terms':n**3,
          'factor_residual_entries':n*n,'comparison_rows':4*n,
          'rhs_solves':0}
    if any(Lq[i][i]==0 or Uq[i][i]==0 for i in range(n)):
        return {'method':'B','status':'HOLD','reason':'zero triangular pivot',
                'bounds':{},'exact':{},'work':work}
    target=tuple(tuple(Hq[rows[i]][cols[j]] for j in range(n)) for i in range(n))
    R=_difference(target,_matmul(Lq,Uq))
    r1,ri=_induced(R)
    ones=(O,)*n
    v=_triangular_comparison(Lq,True,ones)
    w=_triangular_comparison(Uq,False,v)
    nuinf=max(w)
    v=_triangular_comparison(Uq,False,ones,transpose=True)
    w=_triangular_comparison(Lq,True,v,transpose=True)
    nu1=max(w)
    raw={'nu1':nu1,'nuinf':nuinf,'r1':r1,'ri':ri}
    if nu1*r1>=1 or nuinf*ri>=1:
        return {'method':'B','status':'HOLD','reason':'factor residual not contractive',
                'bounds':{'nu1_upper':_upper(nu1),'nuinf_upper':_upper(nuinf),
                          'r1_upper':_upper(r1),'ri_upper':_upper(ri)},
                'exact':raw,'work':work}
    result=_finish('B',Hq,nu1/(1-nu1*r1),nuinf/(1-nuinf*ri),raw,work,b,z)
    result['bounds'].update({'nu1_upper':_upper(nu1),'nuinf_upper':_upper(nuinf),
                             'r1_upper':_upper(r1),'ri_upper':_upper(ri)})
    return result


def dense_singular_values(H:np.ndarray) -> tuple[float,float,float]:
    """Diagnostic SVD of capped synthetic H; never a certificate ingredient."""
    Hq=_matrix(H,'H')
    if H.shape[0]!=H.shape[1]:raise ValueError('synthetic H must be square')
    singular=np.linalg.svd(np.array(Hq,dtype=np.float64),
                           compute_uv=False)
    return float(singular[0]),float(singular[-1]),float(singular[0]/singular[-1])
