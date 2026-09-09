"""N32 capacity-only saved-factor pencil; historical 512/8192 kernel unchanged."""
from decimal import Decimal as D,localcontext
from math import isfinite
from time import monotonic


def matrix(value,width):
    if type(value) is not list or not 1<=len(value)<=12288 or any(type(row) is not list or len(row)!=width
            or any(type(v) is not float or not isfinite(v) for v in row) for row in value):
        raise ValueError('finite rectangular binary64 factor')
    return [{i:D.from_float(x) for i,x in enumerate(row) if x} for row in value]


def gram(rows,n,check):
    result=[[D(0)]*n for _ in range(n)]
    for row in rows:
        check();items=sorted(row.items())
        for k,(i,a) in enumerate(items):
            for j,b in items[k:]:result[i][j]+=a*b
    for i in range(n):
        for j in range(i):result[i][j]=result[j][i]
    return result


def trace_solve(a,b,check=lambda:None):
    """Positive LDL^T, exact sparse fill retained, all right-hand sides at once."""
    n=len(a)
    if not n or any(len(row)!=n for row in a) or len(b)!=n or not b[0] or any(len(row)!=len(b[0]) for row in b):
        raise ValueError('bounded trace system')
    if any(a[i][j]!=a[j][i] for i in range(n) for j in range(i)):raise ValueError('symmetric algebraic block')
    lower=[];diagonal=[]
    for i in range(n):
        check();row={}
        for j in range(i):
            value=a[i][j]-sum((row[k]*diagonal[k]*v for k,v in lower[j].items() if k in row),D(0))
            if value:row[j]=value/diagonal[j]
        pivot=a[i][i]-sum((v*v*diagonal[k] for k,v in row.items()),D(0))
        if not pivot.is_finite() or pivot<=0:raise ValueError('nonpositive algebraic trace stiffness')
        lower.append(row);diagonal.append(pivot)
    width=len(b[0]);y=[]
    for i in range(n):
        check();y.append([b[i][j]-sum((v*y[k][j] for k,v in lower[i].items()),D(0)) for j in range(width)])
    transpose=[[] for _ in range(n)]
    for i,row in enumerate(lower):
        for j,v in row.items():transpose[j].append((i,v))
    x=[[D(0)]*width for _ in range(n)]
    for i in reversed(range(n)):
        check();x[i]=[y[i][j]/diagonal[i]-sum((v*x[k][j] for k,v in transpose[i]),D(0)) for j in range(width)]
    error=D(0);scale=max(D(1),max(abs(v) for row in b for v in row))
    for i,row in enumerate(a):
        check();items=[(k,v) for k,v in enumerate(row) if v]
        error=max(error,max(abs(sum((v*x[k][j] for k,v in items),D(0))-b[i][j])/scale for j in range(width)))
    if error>D('1e-60'):raise ValueError('full original trace solve residual')
    return x,str(error),[str(v) for v in diagonal]


def assemble(packet,digits,check):
    if type(digits) is not int or digits not in (80,100):raise ValueError('registered Decimal precision')
    n=len(packet['geometric']);link=len(packet['right'])
    if not 2<=n<=640 or not 1<=link<=640:raise ValueError('bounded saved factor dimensions')
    ll=matrix(packet['left'],link);rr=matrix(packet['right'],n);bb=matrix(packet['kinetic'],n)
    g=matrix(packet['geometric'],n)
    if len(g)!=n:raise ValueError('square geometric stiffness')
    free=packet['free_dofs'];algebraic=packet['algebraic_dofs']
    for slots in (free,algebraic):
        if type(slots) is not list or len(set(slots))!=len(slots) or any(type(i) is not int or not 0<=i<n for i in slots):
            raise ValueError('exact saved coordinate sets')
    if not set(algebraic)<=set(free):raise ValueError('algebraic coordinates must be free')
    physical=[i for i in free if i not in algebraic]
    if not physical or any(row.get(i,D(0)) for row in bb for i in algebraic):raise ValueError('massless algebraic coordinates only')
    ff=[]
    for row in ll:
        check();expanded={}
        for j,a in row.items():
            for k,b in rr[j].items():expanded[k]=expanded.get(k,D(0))+a*b
        ff.append(expanded)
    k=gram(ff,n,check);mass=gram(bb,n,check)
    skew=D(0);gnorm=max(D(1),max((abs(v) for row in g for v in row.values()),default=D(0)))
    for i in range(n):
        check()
        for j in range(i,n):
            a,b=g[i].get(j,D(0)),g[j].get(i,D(0));skew=max(skew,abs(a-b)/gnorm)
            k[i][j]=k[j][i]=k[i][j]+(a+b)/2
    if skew>D('1e-11'):raise ValueError('raw geometric work symmetry')
    sub=lambda slots,columns:[[k[i][j] for j in columns] for i in slots]
    if algebraic:
        coupling=sub(algebraic,physical);x,error,pivots=trace_solve(sub(algebraic,algebraic),coupling,check)
    else:x=[];error='0';pivots=[];coupling=[]
    reduced=sub(physical,physical);size=len(physical)
    for i in range(size):
        check();column=[(a,row[i]) for a,row in enumerate(coupling) if row[i]]
        for j in range(size):reduced[i][j]-=sum((v*x[a][j] for a,v in column),D(0))
    norm=max(D(1),max(abs(v) for row in reduced for v in row));asym=D(0)
    for i in range(size):
        for j in range(i):
            asym=max(asym,abs(reduced[i][j]-reduced[j][i])/norm)
            reduced[i][j]=reduced[j][i]=(reduced[i][j]+reduced[j][i])/2
    if asym>D('1e-60'):raise ValueError('high-precision Schur symmetry')
    return dict(k=k,mass=mass,reduced=reduced,reduced_mass=[[mass[i][j] for j in physical] for i in physical],
        physical=physical,algebraic=algebraic,trace_map=x,trace_residual=error,trace_pivots=pivots,
        schur_skew=str(asym),geometric_skew=str(skew),free=free,digits=digits)


def action(a,v):return [sum((x*y for x,y in zip(row,v) if x),D(0)) for row in a]
def dot(a,b):return sum((x*y for x,y in zip(a,b)),D(0))


def spectrum(packet,digits,count,progress=lambda row:None):
    import numpy as np
    from scipy.linalg import eigh,solve
    start=monotonic()
    def check():
        if monotonic()-start>120:raise ValueError('physical saved-spectrum 120-second bound')
    if type(count) is not int or not 1<=count<=10:raise ValueError('bounded requested physical spectrum')
    with localcontext() as context:
        context.prec=digits;data=assemble(packet,digits,check)
        k=data['reduced'];m=data['reduced_mass'];size=len(k)
        if count>size:raise ValueError('mode count exceeds physical coordinates')
        progress(dict(stage='physical-trace-schur-complete',physical=size,algebraic=len(data['algebraic'])))
        kf=np.array(k,dtype=float);mf=np.array(m,dtype=float)
        values,vectors=eigh(kf,mf,subset_by_index=(0,count-1),driver='gvx')
        final=[];full=[];metrics=[]
        for index in range(count):
            check();v=vectors[:,index].copy()
            # Fixed four Newton eigenpair corrections. The binary64 bordered
            # solve is a correction preconditioner; residuals and Rayleigh work
            # are recomputed from the original Decimal pencil every time.
            for iteration in range(4):
                check();vd=list(map(D.from_float,v));mv=action(m,vd);kv=action(k,vd)
                lam=dot(vd,kv)/dot(vd,mv);res=[a-lam*b for a,b in zip(kv,mv)]
                shifted=np.array([[float(a-lam*b) for a,b in zip(kr,mr)] for kr,mr in zip(k,m)])
                normal=np.array(mv,dtype=float)
                bordered=np.block([[shifted,-normal[:,None]],[normal[None,:],np.zeros((1,1))]])
                correction=solve(bordered,np.r_[-np.array(res,dtype=float),0.],assume_a='gen')
                v+=correction[:-1]
                norm=dot(list(map(D.from_float,v)),action(m,list(map(D.from_float,v)))).sqrt()
                v=np.array([float(D.from_float(a)/norm) for a in v])
            if v[int(np.argmax(abs(v)))]<0:v=-v
            vd=list(map(D.from_float,v));mv=action(m,vd);kv=action(k,vd);lam=dot(vd,kv)/dot(vd,mv)
            x=[D(0)]*len(data['k'])
            for i,a in zip(data['physical'],vd):x[i]=a
            for i,row in zip(data['algebraic'],data['trace_map']):x[i]=-dot(row,vd)
            # Output-rounded full physical vector, audited in original factors.
            xf=[float(a) for a in x];xd=list(map(D.from_float,xf))
            full_k=action(data['k'],xd);full_m=action(data['mass'],xd)
            residual=[full_k[i]-lam*full_m[i] for i in data['free']]
            norm=lambda v:dot(v,v).sqrt()
            scale=max(D(1),norm([full_k[i] for i in data['free']]),abs(lam)*norm([full_m[i] for i in data['free']]))
            error=norm(residual)/scale
            if error>D('1e-11'):raise ValueError('original full-vector physical spectral residual: '+str(error))
            final.append(float(lam));full.append(xf);metrics.append(float(error))
            progress(dict(stage='physical-eigenpair-complete',index=index,eigenvalue=float(lam),residual=float(error)))
        # Original-coordinate modal work, not only a reduced rounded matrix.
        modes=[list(map(D.from_float,v)) for v in full];orth=D(0);ritz=D(0)
        for i,a in enumerate(modes):
            for j,b in enumerate(modes):
                check();mass_entry=dot(a,action(data['mass'],b));work=dot(a,action(data['k'],b))
                orth=max(orth,abs(mass_entry-D(i==j)))
                ritz=max(ritz,abs(work-D.from_float(final[j])*mass_entry)/max(D(1),(abs(D.from_float(final[i])*D.from_float(final[j]))).sqrt()))
        if orth>D('1e-11') or ritz>D('1e-11'):raise ValueError('original physical mass/Ritz identity')
        if any(a>=b for a,b in zip(final,final[1:])):raise ValueError('ordered distinct requested modes required')
        return dict(digits=digits,eigenvalues=final,full_modes=full,original_residuals=metrics,
            mass_orthogonality=float(orth),original_ritz_error=float(ritz),trace_residual=data['trace_residual'],
            trace_pivots=data['trace_pivots'],schur_skew=data['schur_skew'],raw_geometric_skew=data['geometric_skew'],
            physical_dimension=size,algebraic_dimension=len(data['algebraic']),negative_modes_retained=True,
            original_factors_used=True,physical_current_rest_mass=True,production_qualified=False,interval_certified=False)
