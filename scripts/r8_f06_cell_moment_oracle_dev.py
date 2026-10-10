"""Independent saved-state spatial cell-moment oracle; no production imports."""
from decimal import Decimal,localcontext
from pathlib import Path
import json,hashlib
D=Decimal

def decimal(value):
    return D.from_float(float(value))
def vector(values):return [decimal(v) for v in values]
def matrix(values):return [vector(row) for row in values]
def eye():return [[D(i==j) for j in range(3)] for i in range(3)]
def transpose(A):return [list(row) for row in zip(*A)]
def add(A,B):return [[a+b for a,b in zip(x,y)] for x,y in zip(A,B)]
def neg(A):return [[-v for v in row] for row in A]
def scale(A,v):return [[v*a for a in row] for row in A]
def mm(A,B):return [[sum(a*b for a,b in zip(row,col)) for col in zip(*B)] for row in A]
def mv(A,b):return [sum(a*v for a,v in zip(row,b)) for row in A]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def plus(a,b):return [x+y for x,y in zip(a,b)]
def minus(a,b):return [x-y for x,y in zip(a,b)]
def times(a,b):return [x*b for x in a]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def skew(a):return [[D(0),-a[2],a[1]],[a[2],D(0),-a[0]],[-a[1],a[0],D(0)]]
def cosine(L):return (sum(L[i][i] for i in range(3))-1)/2
def trace_direction(L):return sum(L[i][i] for i in range(3))/2
def axial(L):return [(L[2][1]-L[1][2])/2,(L[0][2]-L[2][0])/2,(L[1][0]-L[0][1])/2]

def log_terms(c,cubic=False):
    d=1-c
    assert abs(d)<D('.1'),'independent principal-log local series outside bound'
    f=D(1);first=D(0);second=D(0);a=D(1)
    if cubic:assert c>D('0.9999999'),'saved base is not on the native cubic-log branch'
    nmax=3 if cubic else 128
    for k in range(1,nmax+1):
        a*=D(k)/D(2*k+1)
        f+=a*d**k;first-=D(k)*a*(d**(k-1) if k>1 else D(1))
        if k>=2:second+=D(k*(k-1))*a*(d**(k-2) if k>2 else D(1))
    if not cubic:assert abs(a*d**nmax)<D('1e-80')
    return f,first,second

def exp(w):
    # Matrix series independently defines Exp, retaining products before any
    # absolute-frame rounding. Saved direction is not altered.
    A=skew(w);total=eye();term=eye()
    for k in range(1,129):
        term=scale(mm(term,A),D(1)/D(k));total=add(total,term)
    assert max(abs(v) for row in term for v in row)<D('1e-80')
    return total

def moment_rows(X,Q,U,p,direction,cubic=False):
    """Residual and exact first derivative of re-centered spatial cell rows."""
    residual=[];derivative=[];log_deltas=[]
    for cell,(left,right) in enumerate(((0,1),(1,2))):
        uc=U[cell];omega=direction[18+3*cell:21+3*cell];O=skew(omega)
        chord=minus(X[right],X[left]);dchord=minus(direction[6*right:6*right+3],direction[6*left:6*left+3])
        N=p[3*cell:3*cell+3];dN=direction[24+3*cell:27+3*cell];UN=mv(uc,N)
        r=cross(UN,chord)
        dr=plus(cross(plus(cross(omega,UN),mv(uc,dN)),chord),cross(UN,dchord))
        # Frozen fixture reference nodal triads are identity; that fact is
        # authenticated against the archived fixture source in registration.
        V=uc;VT=transpose(V)
        for endpoint,node in enumerate((left,right)):
            sign=D(-1 if endpoint==0 else 1);qn=Q[node];On=skew(direction[6*node+3:6*node+6])
            L=mm(VT,qn);dL=mm(mm(VT,add(neg(O),On)),qn)
            c=cosine(L);b=axial(L);dc=trace_direction(dL);db=axial(dL)
            f,fp,fpp=log_terms(c,cubic)
            mstart=6+6*cell+3*endpoint;M=p[mstart:mstart+3];dM=direction[24+mstart:27+mstart]
            for j in range(3):
                basis=[D(i==j) for i in range(3)];E=skew(basis)
                B=neg(mm(mm(VT,E),qn))
                dB=mm(mm(VT,add(mm(O,E),neg(mm(E,On)))),qn)
                cb=trace_direction(B);ab=axial(B);dcb=trace_direction(dB);dab=axial(dB)
                partial=plus(times(b,fp*cb),times(ab,f))
                variation=plus(plus(times(b,fpp*dc*cb+fp*dcb),times(db,fp*cb)),
                    plus(times(ab,fp*dc),times(dab,f)))
                r[j]+=sign*dot(M,partial)
                dr[j]+=sign*(dot(dM,partial)+dot(M,variation))
        residual.extend(r);derivative.extend(dr)
    return residual,derivative

def intended_moment_fd(data,h):
    X=[plus(vector(a),vector(b)) for a,b in zip(data['x'],data['low'])]
    Q=[matrix(v) for v in data['frames']];U=[matrix(v) for v in data['cells']]
    p=vector(data['p']);d=vector(data['direction']);hh=decimal(h);paired=[]
    for signed in (hh,-hh):
        xs=[plus(x,times(d[6*n:6*n+3],signed)) for n,x in enumerate(X)]
        qs=[mm(exp(times(d[6*n+3:6*n+6],signed)),q) for n,q in enumerate(Q)]
        us=[mm(exp(times(d[18+3*c:21+3*c],signed)),u) for c,u in enumerate(U)]
        ps=plus(p,times(d[24:],signed))
        paired.append(moment_rows(xs,qs,us,ps,d)[0])
    return [(a-b)/(2*hh) for a,b in zip(*paired)]

def run(out):
    import numpy as np
    saved=Path(__file__).resolve().parents[1]/'.development/r8-f06-quiet-caller-repair-20261009/source2/s3'
    out=Path(out);out.mkdir(parents=True,exist_ok=True);results=[]
    for side in ('before','after'):
        base=dict(np.load(saved/(side+'-base.npz')));fd=dict(np.load(saved/(side+'-fd-0.002.npz')))
        compatibility=np.asarray(fd['native_q_rows'],dtype=int)
        starts=[int(min(compatibility))+24*i-6 for i in range(2)]
        moment=np.concatenate([np.arange(start,start+6) for start in starts])
        retained=np.sort(np.r_[moment,compatibility]);assert len(retained)==48 and len(set(retained))==48
        independent=base['independent'][retained].copy()
        exact=fd['exact_path'][retained].copy();mom_residual=[];mom_derivative=[];mom_fd=[];cubic_delta=[]
        for member in range(2):
            data=dict(np.load(saved/(side+'-native-'+str(member)+'.npz')))
            material=json.loads((saved/(side+'-native-'+str(member)+'-material.json')).read_text())
            assert material['derivative_kind']=='CLASSICAL_SMOOTH_BRANCH'
            assert set(row['branch'] for row in material['stations'])=={'ELASTIC'}
            with localcontext() as ctx:
                ctx.prec=80
                X=[plus(vector(a),vector(b)) for a,b in zip(data['x'],data['low'])]
                Q=[matrix(v) for v in data['frames']];U=[matrix(v) for v in data['cells']]
                p=vector(data['p']);d=vector(data['direction'])
                r,dr=moment_rows(X,Q,U,p,d);rc,drc=moment_rows(X,Q,U,p,d,cubic=True)
                fdm=intended_moment_fd(data,.002)
            rows=np.arange(starts[member],starts[member]+6);positions=np.searchsorted(retained,rows)
            independent[positions]=np.array([float(v) for v in dr]);exact[positions]=np.array([float(v) for v in fdm])
            mom_residual.extend(float(v) for v in r);mom_derivative.extend(float(v) for v in dr);mom_fd.extend(float(v) for v in fdm)
            cubic_delta.extend(float(a-b) for a,b in zip(dr,drc))
            assert np.max(abs(np.array([float(v) for v in r])-data['residual'][18:24]))<1e-8
        scale=base['rowscale'][retained];pred=base['predicted'][retained];den=max(float(np.linalg.norm(pred*scale)),1e-10)
        metrics=dict(side=side,h=.002,rows=retained.tolist(),moment_rows=moment.tolist(),denominator=den,
            full48_independent_error=float(np.linalg.norm((independent-pred)*scale)/den),
            full48_intended_path_error=float(np.linalg.norm((exact-pred)*scale)/den),
            original_full48_raw_error=float(np.linalg.norm((fd['observed'][retained]-pred)*scale)/den),
            moment_independent_error=float(np.linalg.norm((np.array(mom_derivative)-base['predicted'][moment])*base['rowscale'][moment])/den),
            moment_fd_error=float(np.linalg.norm((np.array(mom_fd)-base['predicted'][moment])*base['rowscale'][moment])/den),
            cubic_log_derivative_delta=float(np.linalg.norm(np.array(cubic_delta)*base['rowscale'][moment])/den),
            independence='12 analytic scalar-log/cross-product rows plus36 previously independent saved compatibility rows',
            intended_path='48 rows complete; existing36 exact-path evidence reused, new12 intended path evaluated')
        np.savez(out/(side+'-full48.npz'),retained_rows=retained,moment_rows=moment,independent=independent,
            intended_path=exact,predicted=pred,scale=scale,moment_residual=np.array(mom_residual),
            original_raw_observed=fd['observed'][retained],cubic_delta=np.array(cubic_delta))
        (out/(side+'-metrics.json')).write_text(json.dumps(metrics,indent=2)+'\n');results.append(metrics)
    (out/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
    return results
