"""Independent primal KKT return map; imports no ANYsolver/beam mechanics."""
from decimal import Decimal as D,localcontext
from time import monotonic


def linear(a,b):
    n=len(a);x=[list(r)+list(v) for r,v in zip(a,b)];m=len(b[0])
    for k in range(n):
        p=max(range(k,n),key=lambda i:abs(x[i][k]))
        if not x[p][k]:raise ValueError('oracle singular system')
        x[k],x[p]=x[p],x[k];pivot=x[k][k];x[k]=[v/pivot for v in x[k]]
        for i in range(n):
            if i!=k:
                factor=x[i][k];x[i]=[v-factor*w for v,w in zip(x[i],x[k])]
    return [r[n:n+m] for r in x]


def mv(a,v):return [sum(x*y for x,y in zip(r,v)) for r in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))


def strain_return(elastic,metric,strain,plastic=None,accumulated=(0.,0.)):
    start=monotonic()
    def check():
        if monotonic()-start>15.:raise RuntimeError('independent section oracle deadline')
    with localcontext() as ctx:
        ctx.prec=96
        c=[[D.from_float(float(v)) for v in r] for r in elastic];m=[[D.from_float(float(v)) for v in r] for r in metric]
        e=list(map(lambda v:D.from_float(float(v)),strain));z0=[D(0)]*6 if plastic is None else [sum(D.from_float(float(v)) for v in r) for r in plastic]
        p0=sum(D.from_float(float(v)) for v in accumulated)
        # Y/H are passed separately through the explicit data envelope below.
        return c,m,e,z0,p0,check


def response(data):
    c,m,e,z0,p0,check=strain_return(data['elastic'],data['metric'],data['strain'],data.get('plastic'),data.get('accumulated',(0.,0.)))
    with localcontext() as ctx:
        ctx.prec=96;y=D.from_float(float(data['yield_force']));h=D.from_float(float(data['hardening']))
        inverse=linear(c,[[D(i==j) for j in range(6)] for i in range(6)])
        target=[a-b for a,b in zip(e,z0)];trial=mv(c,target);q=dot(trial,mv(m,trial)).sqrt();radius=y+h*p0
        if q<=radius:
            stress=trial;lam=D(0);z=z0;consistent=c;branch='ELASTIC'
        else:
            x=[v*radius/q for v in trial]+[D(0)]
            def equations(x):
                stress=x[:6];lam=x[6];ms=mv(m,stress);q=dot(stress,ms).sqrt();normal=[v/q for v in ms]
                r=[a+lam*b-t for a,b,t in zip(mv(inverse,stress),normal,target)]+[q-radius-h*lam]
                a=[[inverse[i][j]+lam*(m[i][j]-normal[i]*normal[j])/q for j in range(6)]+[normal[i]] for i in range(6)]
                a.append(normal+[-h])
                return r,a,normal
            def merit(r):return sum((v/(1+abs(t)))**2 for v,t in zip(r,target+[radius]))
            for iteration in range(40):
                check();r,a,n=equations(x)
                if max(abs(v) for v in r)<=D('1e-65')*max(D(1),*(abs(v) for v in target),radius):break
                step=[v[0] for v in linear(a,[[-v] for v in r])];old=merit(r)
                for cut in range(32):
                    alpha=D(2)**(-cut);candidate=[v+alpha*d for v,d in zip(x,step)]
                    if candidate[6]<0:continue
                    rc,_,_=equations(candidate)
                    if merit(rc)<old:x=candidate;break
                else:raise RuntimeError('independent section KKT line search')
            else:raise RuntimeError('independent section KKT iteration limit')
            stress=x[:6];lam=x[6];_,a,n=equations(x);z=[v+lam*w for v,w in zip(z0,n)]
            rhs=[[D(i==j) for j in range(6)] for i in range(7)]
            consistent=linear(a,rhs)[:6];branch='PLASTIC'
        p=p0+lam;elastic_energy=dot(stress,mv(inverse,stress))/2
        energy=elastic_energy+h*(p*p-p0*p0)/2+y*lam
        result=dict(stress=list(map(float,stress)),plastic=list(map(float,z)),accumulated=float(p),increment=float(lam),
            tangent=[[float(v) for v in r] for r in consistent],potential=float(energy),
            stored_energy=float(elastic_energy+h*p*p/2),dissipation=float(y*lam),branch=branch)
        check();return result
