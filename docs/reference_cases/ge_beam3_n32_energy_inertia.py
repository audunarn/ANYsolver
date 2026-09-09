"""Front-aware successor energy-form audit; never modifies the raw captured tangent.

x^T H x = x^T (H+H^T)/2 x for every real x. Polarization defines the
symmetric energy representation; raw operator symmetry is separately reported.
No exact raw symmetry, interval enclosure or independent mechanics claim.
"""
from decimal import Decimal as D, localcontext
from math import isfinite
from time import monotonic
from fractions import Fraction
from docs.reference_cases.ge_beam3_n32_scaled_inertia import inertia


def exact_energy_matrix(matrix):
    """Rational identity test/reference helper, not the large-matrix solver."""
    n=len(matrix)
    if not 1<=n<=32 or any(len(row)!=n for row in matrix):raise ValueError('bounded rational matrix')
    return [[(Fraction(matrix[i][j])+Fraction(matrix[j][i]))/2 for j in range(n)] for i in range(n)]

def audit(left,right,geometric,kinetic,free,algebraic,shifts,*,digits=80):
    start=monotonic()
    def check():
        if monotonic()-start>120: raise ValueError('signed inertia audit deadline')
    if type(digits) is not int or digits not in (80,100): raise ValueError('registered precision')
    if any(type(a) is not list or not a for a in (left,right,geometric,kinetic)):
        raise ValueError('nonempty explicit matrices')
    n=len(geometric); link=len(right)
    if not 2<=n<=640 or not 1<=link<=640 or len(left)>12288 or len(kinetic)>12288:
        raise ValueError('bounded factor dimensions')
    for a,width in ((left,link),(right,n),(geometric,n),(kinetic,n)):
        if any(type(row) is not list or len(row)!=width or any(type(x) is not float or not isfinite(x) for x in row) for row in a):
            raise ValueError('finite rectangular binary64 factors')
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
        g=[[D.from_float(x) for x in row] for row in geometric]
        skew2=sum(((g[i][j]-g[j][i])**2 for i in range(n) for j in range(n)),D(0))
        norm2=sum((x*x for row in g for x in row),D(0))
        skew=skew2.sqrt()/max(D(1),norm2.sqrt())
        if skew>D('1e-11'):raise ValueError('raw geometric conservative symmetry guard')
        for i in range(n):
            for j in range(i,n):
                value=k[i][j]+(g[i][j]+g[j][i])/2
                k[i][j]=k[j][i]=value
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
                    trace_positive=True,mass_positive=True,certified_intervals=False,mechanics_reconstructed=False,
                    quadratic_form_preserved=True,raw_geometric_symmetric=(skew==0),
                    raw_skew_normalized=str(skew),symmetric_energy_representation=True)
