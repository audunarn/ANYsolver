"""Separate spatial rod BVP; no ANYsolver/discrete mechanics imports.

Material strain and spatial balance basis: Bali et al. DOI10.1002/nme.6994,
equations6,7,10,11,15-17. Quaternion/multisegment collocation is derived here,
not the paper's discretization or independent authorship review.
"""
from time import monotonic
import numpy as np
from scipy.integrate import solve_bvp
from scipy.spatial.transform import Rotation

C=np.array([1000.,400.,400.,.02,.01,.02])
BREAKS=np.array([-1.,-.5,0.,.5,1.])

def product(a,b):
    a,b=np.asarray(a),np.asarray(b)
    return np.concatenate(((a[0]*b[0]-np.sum(a[1:]*b[1:],axis=0))[None],
        a[0]*b[1:]+b[0]*a[1:]+np.cross(a[1:],b[1:],axis=0)),axis=0)

def matrix(q):
    w,x,y,z=q
    return np.array([[w*w+x*x-y*y-z*z,2*(x*y-w*z),2*(x*z+w*y)],
        [2*(x*y+w*z),w*w-x*x+y*y-z*z,2*(y*z-w*x)],
        [2*(x*z-w*y),2*(y*z+w*x),w*w-x*x-y*y+z*z]])

def reference(x):
    x=np.asarray(x);theta=np.arctan(-.2*x);c=np.cos(theta/2)/np.sqrt(2.);s=np.sin(theta/2)/np.sqrt(2.)
    return np.array([x,.1*(1-x*x),np.zeros_like(x)]),np.array([c,c,s,s])

def equations(x,y):
    """[position3, scalar-first quaternion4, spatial force3, moment3], d/dX."""
    d=matrix(y[3:7]);force=np.einsum('ijn, in->jn',d,y[7:10]);moment=np.einsum('ijn,in->jn',d,y[10:13])
    v=force/C[:3,None];v[0]+=1.
    jac=np.sqrt(1+.04*x*x)
    k=moment/C[3:,None];k[1]+=-.2/jac**3
    velocity=np.einsum('ijn,jn->in',d,v)
    qdot=.5*product(y[3:7],np.concatenate((np.zeros((1,len(x))),k)))
    return jac*np.vstack((velocity,qdot,np.zeros_like(force),-np.cross(velocity,y[7:10],axis=0)))

def boundary(a,b,parameter,amplitude):
    a=a.reshape(4,13);b=b.reshape(4,13)
    left,ql=reference(np.array([-1.]));right,qr=reference(np.array([1.]))
    conjugate=qr[:,0]*np.array([1.,-1.,-1.,-1.])
    out=[a[0,:3]-left[:,0],a[0,3:7]-ql[:,0],b[-1,:3]-right[:,0],product(conjugate,b[-1,3:7])[1:]]
    for i in range(3):
        jump=a[i+1]-b[i]
        if i==1:jump[7:10]-=np.array([0.,parameter[0],0.])
        out.append(jump)
    out.append(np.array([b[0,2]-amplitude]))
    return np.concatenate(out)

def initial_guess(record,u):
    """Saved discrete fields initialize Newton only; none define the ODE."""
    mechanical=record['mechanical'];node_x=np.linspace(-1.,1.,41)
    positions=np.array(mechanical['positions'])+np.array(mechanical['position_low'])
    xyzw=Rotation.from_matrix(np.array(mechanical['nodal_frames'])).as_quat()
    quaternions=xyzw[:,[3,0,1,2]]
    for i in range(1,len(quaternions)):
        if quaternions[i]@quaternions[i-1]<0:quaternions[i]*=-1
    stations=[]
    for element in record['recovery']:
        eid=element['element_id']
        for row in element['stations']:
            x=-1.+(eid-1)*.1+.05*(row['xi']+1.)
            stress=np.array(row['resultants'])+np.array(row['resultants_low']);frame=np.array(row['current_frame'])
            stations.append((x,frame@stress[:3],frame@stress[3:]))
    result=[]
    for lo,hi in zip(BREAKS[:-1],BREAKS[1:]):
        x=lo+(hi-lo)*u;y=np.zeros((13,len(u)))
        for j in range(3):y[j]=np.interp(x,node_x,positions[:,j])
        for j in range(4):y[3+j]=np.interp(x,node_x,quaternions[:,j])
        y[3:7]/=np.linalg.norm(y[3:7],axis=0)
        # One-sided force data avoid smoothing the crown point-force jump.
        selected=[s for s in stations if (s[0]<0)==(hi<=0)]
        sx=np.array([s[0] for s in selected])
        for j in range(3):
            y[7+j]=np.interp(x,sx,[s[1][j] for s in selected])
            y[10+j]=np.interp(x,sx,[s[2][j] for s in selected])
        result.append(y)
    return np.vstack(result)

def solve(record,profile='BVP7',progress=lambda row:None):
    if profile not in ('BVP7','BVP9') or record.get('amplitude') not in (-.006,-.003,.003,.006):
        raise ValueError('registered spatial reference profile/amplitude')
    tol,cap=(1e-7,1025) if profile=='BVP7' else (1e-9,4097)
    start=monotonic();calls=0
    def consume():
        nonlocal calls
        calls+=1
        if calls>2000 or monotonic()-start>60:raise RuntimeError('spatial reference callback/time bound')
        if calls%100==0:progress(dict(stage='continuum-callback',callbacks=calls))
    def fun(u,y,p):
        consume();result=[]
        for i,(lo,hi) in enumerate(zip(BREAKS[:-1],BREAKS[1:])):
            result.append((hi-lo)*equations(lo+(hi-lo)*u,y[13*i:13*(i+1)]))
        return np.vstack(result)
    def bc(a,b,p):consume();return boundary(a,b,p,record['amplitude'])
    u=np.linspace(0.,1.,33);guess=initial_guess(record,u)
    progress(dict(stage='spatial-continuum-start',profile=profile))
    result=solve_bvp(fun,bc,u,guess,p=np.array([record['load']]),tol=tol,bc_tol=1e-11,max_nodes=cap)
    if not result.success or not np.isfinite(result.y).all():raise RuntimeError('spatial continuum failed: '+result.message)
    bc_error=float(np.max(abs(boundary(result.y[:,0],result.y[:,-1],result.p,record['amplitude']))))
    sample=np.linspace(0.,1.,257);values=result.sol(sample);derivative=result.sol(sample,1);expected=fun(sample,values,result.p)
    ode_error=float(np.max(abs(derivative-expected)/(1+abs(expected))))
    norm_error=max(float(np.max(abs(np.sum(values[13*i+3:13*i+7]**2,axis=0)-1.))) for i in range(4))
    if bc_error>1e-11 or ode_error>10*tol or norm_error>10*tol:raise RuntimeError('spatial continuum consistency')
    progress(dict(stage='spatial-continuum-complete',profile=profile,load=float(result.p[0]),nodes=len(result.x),callbacks=calls))
    return result,dict(profile=profile,load=float(result.p[0]),nodes=len(result.x),iterations=result.niter,
        callbacks=calls,boundary_error=bc_error,differential_error=ode_error,quaternion_norm_error=norm_error)

def sample(result,x):
    x=np.asarray(x)
    if x.ndim!=1 or len(x)>4097 or not np.isfinite(x).all() or np.any(x<-1.) or np.any(x>1.):raise ValueError('bounded sampling domain')
    segment=np.minimum(np.searchsorted(BREAKS,x,side='right')-1,3)
    values=np.zeros((13,len(x)))
    for i,(lo,hi) in enumerate(zip(BREAKS[:-1],BREAKS[1:])):
        mask=segment==i
        values[:,mask]=result.sol((x[mask]-lo)/(hi-lo))[13*i:13*(i+1)]
    frames=matrix(values[3:7]);n=np.einsum('ijn,in->jn',frames,values[7:10]);m=np.einsum('ijn,in->jn',frames,values[10:13])
    return values,frames,np.vstack((n,m))

def energy(result,order):
    if order not in (64,128):raise ValueError('registered energy quadrature')
    points,weights=np.polynomial.legendre.leggauss(order);total=0.
    for lo,hi in zip(BREAKS[:-1],BREAKS[1:]):
        x=(lo+hi)/2+(hi-lo)*points/2;_,_,stress=sample(result,x)
        total+=float(np.sum(weights*(hi-lo)/2*np.sqrt(1+.04*x*x)*.5*np.sum(stress*stress/C[:,None],axis=0)))
    return total
