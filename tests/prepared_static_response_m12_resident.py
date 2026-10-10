"""Conditional resident-SuperLU solve enclosure, never a production solve route."""
import hashlib
import numpy as np
from scipy.sparse.linalg import SuperLU
from prepared_static_response_m10_bounds import (
    Q,ZERO,ONE,UNIT,TINY,rational,matrix,rounded,scale,upward)

class ResidentRefusal(ValueError):pass

def triangular_center_error(T,b,eb,lower):
    """Assumes |T*yhat-bhat| <= g*(|T|*|yhat|+|bhat|)+a.

    This relation for native supernodal gstrs is a declared prerequisite.
    """
    n=len(T);count=2*n+2
    if count*UNIT>=ONE:raise ResidentRefusal('arithmetic_count')
    g=count*UNIT/(ONE-count*UNIT)
    center=[ZERO]*n;error=[ZERO]*n
    order=range(n) if lower else reversed(range(n))
    for i in order:
        prior=range(i) if lower else range(i+1,n)
        if T[i][i]==0:raise ResidentRefusal('zero_diagonal')
        center[i]=(b[i]-sum((T[i][j]*center[j] for j in prior),ZERO))/T[i][i]
    h=[]
    for i in range(n):
        magnitude=sum((abs(t)*abs(x) for t,x in zip(T[i],center)),ZERO)
        # A subnormal quotient's absolute error is multiplied by |Tii| in
        # the row residual. An unscaled count*mu allowance is insufficient.
        a=count*TINY*(ONE+abs(T[i][i]))/(ONE-count*UNIT)
        h.append((ONE+g)*eb[i]+g*(magnitude+abs(b[i]))+a)
    order=range(n) if lower else reversed(range(n))
    for i in order:
        # Stream one signed transpose solve T.T*w=e_i. Its absolute values
        # are an inverse row action; no global inverse is constructed/stored.
        w=[ZERO]*n
        for k in (reversed(range(n)) if lower else range(n)):
            known=range(k+1,n) if lower else range(k)
            w[k]=((ONE if k==i else ZERO)-sum((T[j][k]*w[j] for j in known),ZERO))/T[k][k]
        J=[abs(value) for value in w]
        K=[sum((J[k]*abs(T[k][j]) for k in range(n)),ZERO) for j in range(n)]
        assert K[i]==ONE
        prior=range(i) if lower else range(i+1,n)
        error[i]=(sum((j*v for j,v in zip(J,h)),ZERO)+g*sum((K[j]*error[j] for j in prior),ZERO))/(ONE-g)
        if abs(center[i])+error[i]>rational(np.finfo(float).max):
            raise ResidentRefusal('triangular_enclosure_overflow')
    return center,error

class ResidentSolveBound:
    def __init__(self,solver,operator,scaling,*,backend_name='scipy_superlu'):
        if backend_name!='scipy_superlu' or type(solver) is not SuperLU:
            raise ResidentRefusal('resident_SuperLU_only')
        A=operator.toarray() if hasattr(operator,'toarray') else np.asarray(operator)
        d=np.asarray(scaling)
        if A.dtype!=np.float64 or d.dtype!=np.float64 or A.shape!=(len(d),len(d)):
            raise ResidentRefusal('binary64_shape')
        if not np.all(np.isfinite(A)) or not np.all(np.isfinite(d)) or np.any(d<=0):
            raise ResidentRefusal('nonfinite_or_nonpositive_scaling')
        L,U=solver.L.toarray(),solver.U.toarray()
        pr,pc=solver.perm_r.copy(),solver.perm_c.copy();n=len(d)
        if sorted(pr.tolist())!=list(range(n)) or sorted(pc.tolist())!=list(range(n)):
            raise ResidentRefusal('permutations')
        if not np.array_equal(L,np.tril(L)) or not np.array_equal(U,np.triu(U)):
            raise ResidentRefusal('triangular_export')
        if not np.all(np.isfinite(L)) or not np.all(np.isfinite(U)) or np.any(np.diag(L)==0) or np.any(np.diag(U)==0):
            raise ResidentRefusal('factor_values')
        self.L,self.U=matrix(L),matrix(U)
        self.pr,self.pc=pr,pc;self.roworder=np.argsort(pr);self.colorder=np.argsort(pc)
        self.scaling=d.copy()
        digest=hashlib.sha256()
        for value in (A,d,L,U,pr,pc):digest.update(value.tobytes())
        self.identity=digest.hexdigest()
        rationalA=matrix(A)
        self.defect=max(sum((abs(rationalA[self.roworder[i]][self.colorder[j]]-sum((self.L[i][k]*self.U[k][j] for k in range(n)),ZERO)) for j in range(n)),ZERO) for i in range(n))
        self.metadata={'resident_factor_sha256':self.identity,'size':n,'nontrivial_row_permutation':bool(np.any(pr!=np.arange(n))),'nontrivial_column_permutation':bool(np.any(pc!=np.arange(n))),'factor_defect_inf_upper':upward(self.defect),'conditional_triangular_operation_count':2*n+2,'error_bound_method':'streamed_signed_transpose_row_actions','scaling_min':float(d.min()),'scaling_max':float(d.max()),'factor_export_to_native_supernode_equivalence':'UNQUALIFIED'}

    def enclose(self,rhs):
        b=np.asarray(rhs)
        if b.dtype!=np.float64 or b.shape!=self.scaling.shape or not np.all(np.isfinite(b)):
            raise ResidentRefusal('rhs')
        intervals=[]
        for s,x in zip(self.scaling,b):
            try:interval=rounded((rational(s)*rational(x),)*2)
            except (OverflowError,AssertionError):raise ResidentRefusal('scaling_overflow')
            intervals.append(interval)
        centers=[(lo+hi)/2 for lo,hi in intervals]
        errors=[(hi-lo)/2 for lo,hi in intervals]
        yc,ey=triangular_center_error(self.L,[centers[i] for i in self.roworder],[errors[i] for i in self.roworder],True)
        zc,ez=triangular_center_error(self.U,yc,ey,False)
        result=[]
        for i,s in enumerate(self.scaling):
            j=self.pc[i]
            try:result.append(scale((zc[j]-ez[j],zc[j]+ez[j]),s))
            except (OverflowError,AssertionError):raise ResidentRefusal('solution_enclosure_overflow')
        return result
