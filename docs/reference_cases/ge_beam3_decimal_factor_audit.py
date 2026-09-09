"""Same-author independent-arithmetic audit of supplied binary64 factors.

Standard-library Decimal only. This does NOT reconstruct beam mechanics or
certify intervals. It answers whether low-mode errors already exist in the
supplied factors or are introduced by their binary64 reduction. No production
imports, clipping, empirical stabilization, or numerical mass floor.
"""
from decimal import Decimal as D, localcontext
from time import monotonic


def transpose(a): return list(map(list, zip(*a)))
def product(a,b):
    bt=transpose(b)
    return [[sum((x*y for x,y in zip(row,col)),D(0)) for col in bt] for row in a]
def gram(a): return product(transpose(a),a)
def subtract(a,b): return [[x-y for x,y in zip(r,s)] for r,s in zip(a,b)]
def select(a,rows,cols): return [[a[i][j] for j in cols] for i in rows]


def cholesky(a):
    n=len(a); lower=[[D(0)]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            x=a[i][j]-sum((lower[i][k]*lower[j][k] for k in range(j)),D(0))
            if i==j:
                if x<=0: raise ValueError('nonpositive audit Cholesky pivot')
                lower[i][j]=x.sqrt()
            else: lower[i][j]=x/lower[j][j]
    return lower


def triangular_solve(a,b,lower):
    n=len(a); result=[[D(0)]*len(b[0]) for _ in range(n)]
    for i in (range(n) if lower else range(n-1,-1,-1)):
        for j in range(len(b[0])):
            result[i][j]=(b[i][j]-sum((a[i][k]*result[k][j]
                for k in (range(i) if lower else range(i+1,n))),D(0)))/a[i][i]
    return result


def symmetric_roots(a,digits,checkpoint):
    a=[row[:] for row in a]; n=len(a); threshold=D(10)**(-(digits-20))
    for sweep in range(100):
        checkpoint()
        maximum=max(abs(a[i][j]) for i in range(n) for j in range(i+1,n))
        if maximum<=threshold: return sorted(a[i][i] for i in range(n))
        for i in range(n):
            for j in range(i+1,n):
                if a[i][j]==0: continue
                tau=(a[j][j]-a[i][i])/(2*a[i][j])
                t=(D(1) if tau>=0 else D(-1))/(abs(tau)+(1+tau*tau).sqrt())
                c=1/(1+t*t).sqrt(); s=t*c; off=a[i][j]
                a[i][i]-=t*off; a[j][j]+=t*off; a[i][j]=a[j][i]=D(0)
                for k in range(n):
                    if k in (i,j): continue
                    x,y=a[k][i],a[k][j]
                    a[k][i]=a[i][k]=c*x-s*y; a[k][j]=a[j][k]=s*x+c*y
    raise ValueError('audit Jacobi sweep bound')


def factor_roots(elastic,kinetic,free,algebraic,*,digits=80):
    """Exact float conversion followed by bounded high-precision arithmetic."""
    started=monotonic()
    def checkpoint():
        if monotonic()-started>120: raise ValueError('audit deadline')
    if type(digits) is not int or not 60<=digits<=100: raise ValueError('bounded audit precision')
    if not elastic or not kinetic or len(elastic)>512 or len(kinetic)>512: raise ValueError('bounded audit rows')
    n=len(elastic[0])
    if not 1<=n<=48 or any(len(row)!=n for row in elastic+kinetic): raise ValueError('bounded audit columns')
    if any(type(x) is not float for row in elastic+kinetic for x in row): raise ValueError('binary64 float data required')
    physical=[i for i in free if i not in algebraic]
    if (not 2<=len(physical)<=30 or len(set(free))!=len(free) or len(set(algebraic))!=len(algebraic)
            or not set(algebraic)<=set(free) or any(type(i) is not int or not 0<=i<n for i in free)):
        raise ValueError('bounded exact audit DOFs')
    if any(row[j]!=0 for row in kinetic for j in algebraic): raise ValueError('massless trace required')
    with localcontext() as context:
        context.prec=digits
        f=[[D.from_float(x) for x in row] for row in elastic]
        b=[[D.from_float(x) for x in row] for row in kinetic]
        if any(not x.is_finite() for row in f+b for x in row): raise ValueError('finite audit factors')
        k=gram(f); m=gram(b); checkpoint()
        kpp=select(k,physical,physical)
        if algebraic:
            kaa=select(k,algebraic,algebraic); kap=select(k,algebraic,physical)
            root=cholesky(kaa)
            eliminate=triangular_solve(transpose(root),triangular_solve(root,kap,True),False)
            kpp=subtract(kpp,product(transpose(kap),eliminate))
        lm=cholesky(select(m,physical,physical))
        first=triangular_solve(lm,kpp,True)
        normalized=transpose(triangular_solve(lm,transpose(first),True))
        return tuple(str(x) for x in symmetric_roots(normalized,digits,checkpoint))
