"""Independent arithmetic of original signed factors; no beam imports.

Complete diagonal/off-diagonal pivot search, symmetric 1x1/2x2 Schur updates.
This is not a LAPACK implementation or a certified interval calculation.
"""
from decimal import Decimal as D, localcontext
from math import isfinite
from time import monotonic


def inertia(matrix, checkpoint=lambda:None):
    """Return negative count; reject unresolved/singular pivots, never clip."""
    a=[row[:] for row in matrix]; n=len(a)
    if not n or any(len(row)!=n for row in a) or any(not x.is_finite() for row in a for x in row):
        raise ValueError('finite square Decimal matrix required')
    if any(a[i][j]!=a[j][i] for i in range(n) for j in range(n)):
        raise ValueError('exact symmetric audit matrix')
    scale=max(D(1),max(abs(x) for row in a for x in row)); floor=scale*D('1e-50')
    count=0; blocks=[]
    while a:
        checkpoint(); n=len(a)
        i=max(range(n),key=lambda j:abs(a[j][j])); diagonal=abs(a[i][i])
        pair=max(((r,s) for r in range(n) for s in range(r+1,n)),
                 key=lambda p:abs(a[p[0]][p[1]]),default=(i,i))
        off=abs(a[pair[0]][pair[1]]) if n>1 else D(0)
        if max(diagonal,off)<=floor: raise ValueError('unresolved signed pivot')
        if diagonal>=off/D(2):
            pivot=a[i][i]
            if abs(pivot)<=floor: raise ValueError('unresolved scalar pivot')
            count+=int(pivot<0); blocks.append(1)
            rest=[j for j in range(n) if j!=i]; column=[a[j][i] for j in rest]
            next_a=[[D(0)]*len(rest) for _ in rest]
            for r,j in enumerate(rest):
                for s in range(r,len(rest)):
                    value=a[j][rest[s]]-column[r]*column[s]/pivot
                    next_a[r][s]=next_a[s][r]=value
        else:
            i,j=pair; aa,bb,cc=a[i][i],a[i][j],a[j][j]; det=aa*cc-bb*bb
            if abs(det)<=floor*max(abs(aa),abs(bb),abs(cc)):
                raise ValueError('unresolved block pivot')
            if det<0: count+=1
            elif aa+cc<0: count+=2
            blocks.append(2); rest=[k for k in range(n) if k not in (i,j)]
            x=[a[k][i] for k in rest]; y=[a[k][j] for k in rest]
            u=[(cc*v-bb*w)/det for v,w in zip(x,y)]
            v=[(aa*w-bb*z)/det for z,w in zip(x,y)]
            next_a=[[D(0)]*len(rest) for _ in rest]
            for r,k in enumerate(rest):
                for s in range(r,len(rest)):
                    value=a[k][rest[s]]-x[r]*u[s]-y[r]*v[s]
                    next_a[r][s]=next_a[s][r]=value
        a=next_a
    return dict(negative=count,positive=len(matrix)-count,pivot_sizes=blocks)


def audit(left,right,geometric,kinetic,free,algebraic,shifts,*,digits=80):
    start=monotonic()
    def check():
        if monotonic()-start>120: raise ValueError('signed inertia audit deadline')
    if type(digits) is not int or digits not in (80,100): raise ValueError('registered precision')
    if any(type(a) is not list or not a for a in (left,right,geometric,kinetic)):
        raise ValueError('nonempty explicit matrices')
    n=len(geometric); link=len(right)
    if not 2<=n<=256 or not 1<=link<=512 or len(left)>8192 or len(kinetic)>8192:
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
