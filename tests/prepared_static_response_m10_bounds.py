"""Small-fixture rational enclosure diagnostic; never a production solve route."""
from fractions import Fraction as Q
import numpy as np
from scipy.linalg import lu

ZERO=Q(0); ONE=Q(1); UNIT=Q(1,2**53); TINY=Q(1,2**1074)

def rational(value):
    assert np.isfinite(value)
    return Q(float(value))

def vector(values):
    return [rational(x) for x in values]

def matrix(values):
    return [vector(row) for row in values]

def upward(value):
    f=float(value)
    return float(np.nextafter(f,np.inf)) if Q(f)<value else f

class ActionBound:
    """C is a positive triangular comparison action, never an inverse matrix."""
    def __init__(self, values, factor_candidate=None):
        self.A=matrix(values)
        p,l,u=lu(values) if factor_candidate is None else factor_candidate
        assert np.array_equal(l,np.tril(l)) and np.array_equal(u,np.triu(u))
        assert np.all(np.diag(l)!=0.) and np.all(np.diag(u)!=0.)
        assert np.array_equal(p@p.T,np.eye(len(p))) and set(np.unique(p))<=set((0.,1.))
        self.order=np.argmax(p.T,axis=1)
        self.L,self.U=matrix(l),matrix(u)
        n=len(values)
        self.rows=[sum((abs(self.A[self.order[i]][j]-sum((self.L[i][k]*self.U[k][j] for k in range(n)),ZERO)) for j in range(n)),ZERO) for i in range(n)]
        self.defect=self.apply(self.rows)
        self.eta=max(self.defect)
        self.accepted=self.eta<ONE

    def apply(self, rhs):
        n=len(rhs); y=[ZERO]*n; x=[ZERO]*n
        for i in range(n):
            y[i]=(rhs[i]+sum((abs(self.L[i][j])*y[j] for j in range(i)),ZERO))/abs(self.L[i][i])
        for i in reversed(range(n)):
            x[i]=(y[i]+sum((abs(self.U[i][j])*x[j] for j in range(i+1,n)),ZERO))/abs(self.U[i][i])
        return x

    def error(self, rhs, candidate):
        assert self.accepted
        rhs,x=vector(rhs),vector(candidate)
        residual=[abs(rhs[i]-sum((a*b for a,b in zip(self.A[i],x)),ZERO)) for i in self.order]
        first=self.apply(residual)
        radius=max(first)/(ONE-self.eta)
        return [v+d*radius for v,d in zip(first,self.defect)]

class SignedActionBound(ActionBound):
    """Exact signed solves of streamed defect columns; no inverse is stored."""
    def __init__(self, values, factor_candidate=None):
        super().__init__(values,factor_candidate)
        n=len(values)
        self.comparison_eta=self.eta
        self.defect=[ZERO]*n
        for j in range(n):
            column=[self.A[self.order[i]][j]-sum((self.L[i][k]*self.U[k][j] for k in range(n)),ZERO) for i in range(n)]
            action=self.signed_action(column)
            for i in range(n):
                self.defect[i]+=abs(action[i])
        self.eta=max(self.defect)
        self.accepted=self.eta<ONE

    def signed_action(self,rhs):
        n=len(rhs); y=[ZERO]*n; x=[ZERO]*n
        for i in range(n):
            y[i]=(rhs[i]-sum((self.L[i][j]*y[j] for j in range(i)),ZERO))/self.L[i][i]
        for i in reversed(range(n)):
            x[i]=(y[i]-sum((self.U[i][j]*x[j] for j in range(i+1,n)),ZERO))/self.U[i][i]
        return x

    def error(self,rhs,candidate):
        assert self.accepted
        rhs,x=vector(rhs),vector(candidate)
        residual=[rhs[i]-sum((a*b for a,b in zip(self.A[i],x)),ZERO) for i in self.order]
        first=[abs(value) for value in self.signed_action(residual)]
        radius=max(first)/(ONE-self.eta)
        return [v+d*radius for v,d in zip(first,self.defect)]

def rounded(interval):
    """Outward endpoints enclose one binary64 rounding, including subnormals."""
    lo,hi=interval
    a,b=float(lo),float(hi)
    assert np.isfinite(a) and np.isfinite(b)
    return Q(float(np.nextafter(a,-np.inf))),Q(float(np.nextafter(b,np.inf)))

def add(a,b): return rounded((a[0]+b[0],a[1]+b[1]))
def scale(a,b):
    b=rational(b); values=(a[0]*b,a[1]*b)
    return rounded((min(values),max(values)))
def divide(a,b):
    b=rational(b); values=(a[0]/b,a[1]/b)
    return rounded((min(values),max(values)))

def dot(row, intervals):
    """Conditional standard floating-point dot bound, arbitrary reduction order.

    At most 2*n rounded operations, finite intermediates, gradual underflow.
    These backend assumptions are explicit and not proved by this diagnostic.
    """
    lo=hi=magnitude=ZERO
    for a,(l,h) in zip(vector(row),intervals):
        lo+=min(a*l,a*h); hi+=max(a*l,a*h)
        magnitude+=abs(a)*max(abs(l),abs(h))
    count=2*len(row); gamma=count*UNIT/(ONE-count*UNIT)
    error=gamma*magnitude+count*TINY/(ONE-count*UNIT)
    return lo-error,hi+error

def matvec(values,intervals): return [dot(row,intervals) for row in values]

def contains(interval,value): return interval[0]<=rational(value)<=interval[1]

def strict_max_excluded(candidate, incumbent):
    return candidate[1]<incumbent[0]

def strict_min_excluded(candidate, incumbent):
    return candidate[0]>incumbent[1]

def square(a):
    lo,hi=a
    values=(lo*lo,hi*hi)
    exact=(ZERO if lo<=0<=hi else min(values),max(values))
    low,high=rounded(exact)
    return max(ZERO,low),high  # mathematical nonnegative square range

def root(a):
    import math
    lo,hi=a
    assert hi>=0
    lo=max(ZERO,lo)
    l,h=math.sqrt(float(lo)),math.sqrt(float(hi))
    while rational(l)**2>lo:l=float(np.nextafter(l,-np.inf))
    while rational(h)**2<hi:h=float(np.nextafter(h,np.inf))
    assert rational(l)**2<=lo and rational(h)**2>=hi
    # Also enclose the subsequent correctly rounded native sqrt result.
    return max(ZERO,rational(float(np.nextafter(l,-np.inf)))),rational(float(np.nextafter(h,np.inf)))

def shell_vm(fields):
    mx,my,mxy,bx,by,bxy,sxz,syz=fields
    surfaces=[]
    for sign in (1.,-1.):
        xx,yy,xy=(add(m,scale(b,sign)) for m,b in ((mx,bx),(my,by),(mxy,bxy)))
        normal=add(add(square(add(xx,scale(yy,-1.))),square(yy)),square(scale(xx,-1.)))
        shear=add(add(square(xy),square(syz)),square(sxz))
        surfaces.append(root(add(scale(normal,.5),scale(shear,3.))))
    return max(s[0] for s in surfaces),max(s[1] for s in surfaces)
