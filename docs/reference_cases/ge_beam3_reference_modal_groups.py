"""Reference-only frequency-band groups and physical subspace comparison."""
import numpy as np
from scipy.linalg import solve_triangular

POLICY='GE_BEAM3_REFERENCE_BAND_COMPLETE_MODAL_GROUPS_V1'
FREQUENCY_ERROR=.02
MINIMUM_CORRELATION=.95

def reference_groups(frequencies):
    omega=np.array(frequencies,dtype=float,copy=True)
    if omega.shape!=(10,) or not np.isfinite(omega).all() or np.any(omega<=0) or np.any(np.diff(omega)<=0):
        raise ValueError('ten positive increasing reference frequencies including guard modes')
    bands=np.column_stack(((1-FREQUENCY_ERROR)*omega,(1+FREQUENCY_ERROR)*omega))
    groups=[];start=0;right=float(bands[0,1])
    for i in range(1,len(omega)+1):
        if i<len(omega) and bands[i,0]<=right:
            right=max(right,float(bands[i,1]));continue
        groups.append(tuple(range(start,i)))
        if i>=6:
            if i==len(omega):raise ValueError('reference modal group is truncated at window boundary')
            return tuple(groups),bands
        start=i;right=float(bands[i,1])
    raise AssertionError('unreachable modal group')

def principal_correlations(left,cross,right):
    left=np.array(left,dtype=float,copy=True);cross=np.array(cross,dtype=float,copy=True)
    right=np.array(right,dtype=float,copy=True)
    if left.ndim!=2 or not 1<=len(left)<=9 or left.shape!=(len(left),len(left)) or cross.shape!=left.shape or right.shape!=left.shape:
        raise ValueError('matching nonempty complete-group Gram matrices')
    for a in (left,cross,right):
        if not np.isfinite(a).all():raise ValueError('finite modal Gram data')
    for a in (left,right):
        if np.linalg.norm(a-a.T)>1e-11*max(1.,np.linalg.norm(a)):raise ValueError('symmetric modal Gram data')
    l=np.linalg.cholesky(left);r=np.linalg.cholesky(right)
    normalized=solve_triangular(l,cross,lower=True)
    normalized=solve_triangular(r,normalized.T,lower=True).T
    squared=np.linalg.svd(normalized,compute_uv=False)**2
    if not np.isfinite(squared).all() or np.max(squared)>1+1e-10:
        raise ValueError('invalid complete-group correlation')
    return squared
