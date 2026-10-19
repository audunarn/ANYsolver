"""Independent fixed curved/cross-inertia vibration physics; no owner kernels.

The fixture construction below is the authenticated historical source recipe.
Quadrature/kinematics and elastic complementary minimization are independently
implemented from primitive fields; reported accounting is comparison data only.
"""
import math
from fractions import Fraction
import numpy as np

PHYSICAL = (0,1,2,6,7,8,12,13,14,18,19,20,21,22,23)
ALGEBRAIC = (3,4,5,9,10,11,15,16,17,*range(24,42))
FIXTURE_SOURCE_SHA256 = """426f673d40e82a4d554c3964dc9b51b4ca5638f180f3f985e4ba85c974ebc05d"""

def primitive_inputs():
    x=np.array((-1.,0.,1.));points=np.column_stack((x,.2*(1-x*x),np.zeros(3)))
    # Fixed approved binary64 orientation INPUTS; public operators remain computed.
    frames = np.array((
        ((float.fromhex('0x1.db614bfce6a6bp-1'), float.fromhex('0x0.0p+0'), float.fromhex('0x1.7c4dd663ebb89p-2')),
         (float.fromhex('0x1.7c4dd663ebb89p-2'), float.fromhex('0x0.0p+0'), float.fromhex('-0x1.db614bfce6a6bp-1')),
         (float.fromhex('0x0.0p+0'), float.fromhex('0x1.0000000000000p+0'), float.fromhex('0x0.0p+0'))),
        ((float.fromhex('0x1.0000000000000p+0'), float.fromhex('0x0.0p+0'), float.fromhex('-0x0.0p+0')),
         (float.fromhex('-0x0.0p+0'), float.fromhex('0x0.0p+0'), float.fromhex('-0x1.0000000000000p+0')),
         (float.fromhex('0x0.0p+0'), float.fromhex('0x1.0000000000000p+0'), float.fromhex('0x0.0p+0'))),
        ((float.fromhex('0x1.db614bfce6a6bp-1'), float.fromhex('0x0.0p+0'), float.fromhex('-0x1.7c4dd663ebb89p-2')),
         (float.fromhex('-0x1.7c4dd663ebb89p-2'), float.fromhex('0x0.0p+0'), float.fromhex('-0x1.db614bfce6a6bp-1')),
         (float.fromhex('0x0.0p+0'), float.fromhex('0x1.0000000000000p+0'), float.fromhex('0x0.0p+0'))),
    ))
    d=np.diag(np.sqrt((30000.,10000.,30000./3.5,2.,1.,1.5)))
    b=np.eye(6);b[0,3]=.02;b[1,5]=.03;f=b@d
    center=np.array((.035,-.025,.012));s=skew(center);shift=-2.7*(s@s)
    shift=np.triu(shift)+np.triu(shift,1).T
    mass=np.block([[2.7*np.eye(3),-2.7*s],[2.7*s,np.diag((.12,.17,.19))+shift]])
    return points,np.array(frames),f.T@f,mass


def skew(v):
    x,y,z=v;return np.array(((0.,-z,y),(z,0.,-x),(-y,x,0.)))


def rotation(v):
    angle=float(np.linalg.norm(v));k=skew(v)
    if angle==0.:return np.eye(3)
    return np.eye(3)+(math.sin(angle)/angle)*k+((1.-math.cos(angle))/(angle*angle))*(k@k)


def log_rotation(q):
    if q.shape!=(3,3)or np.linalg.norm(q.T@q-np.eye(3))>1e-9 or np.linalg.det(q)<=0:raise ValueError('proper independent SO3 frame required')
    v=np.array((q[2,1]-q[1,2],q[0,2]-q[2,0],q[1,0]-q[0,1]))/2.
    s=float(np.linalg.norm(v));a=math.atan2(s,(float(np.trace(q))-1.)/2.)
    if a>=math.pi-1e-5:raise ValueError('independent log excludes pi')
    return np.zeros(3)if s==0. else v*(a/s)


def inverse_left_log(v):
    a=float(np.linalg.norm(v));k=skew(v)
    c=1./12.+a*a/720.+a**4/30240. if a<1e-3 else (1.-.5*a/math.tan(.5*a))/(a*a)
    return np.eye(3)-.5*k+c*(k@k)


def stations(order):
    """Planar Q2 exact tangent/zero-roll frame, reference arc measure and lift."""
    q,w=np.polynomial.legendre.leggauss(order)
    for cell in (0,1):
        for point,weight in zip(q,w):
            t=float((point+1.)/2.);xi=cell-1.+t
            tangent=np.array((1.,-.4*xi,0.));jac=float(np.linalg.norm(tangent));tangent/=jac
            second=np.array((0.,0.,1.));frame=np.column_stack((tangent,second,np.cross(tangent,second)))
            offset=np.array((0.,-.2*t*(t-1.),0.))
            yield cell,t,frame,offset,float(weight*jac/2.),jac


def kinetic(state,velocity,acceleration=None):
    """Reference-measure T, P, H and Euler-Lagrange inertia from physical fields.

    v=I*v_nodes+omega cross U*lift, Q=U*R0, (p,h)=Q*C6*Q.T*(v,omega).
    Nodal inertia=N*pdot; cell inertia=lift cross pdot+hdot+v cross p.
    """
    _,_,_,mass=primitive_inputs();high=np.asarray(state['positions']);low=np.asarray(state['position_low'])
    cells=np.asarray(state['cell_rotations'])[0];v=np.asarray(velocity);a=np.zeros(24)if acceleration is None else np.asarray(acceleration)
    total=0.;linear=np.zeros(3);angular=np.zeros(3);inertia=np.zeros(42)
    for c,t,frame,offset,weight,_ in stations(24):
        u=cells[c];q=u@frame;lift=u@offset;omega=v[18+3*c:21+3*c];alpha=a[18+3*c:21+3*c]
        field=(1-t)*v[6*c:6*c+3]+t*v[6*(c+1):6*(c+1)+3]+np.cross(omega,lift)
        afield=(1-t)*a[6*c:6*c+3]+t*a[6*(c+1):6*(c+1)+3]+np.cross(alpha,lift)+np.cross(omega,np.cross(omega,lift))
        body=np.r_[q.T@field,q.T@omega];mom=mass@body;p=q@mom[:3];h=q@mom[3:]
        bd=np.r_[q.T@(afield-np.cross(omega,field)),q.T@alpha];md=mass@bd
        pd=q@md[:3]+np.cross(omega,p);hd=q@md[3:]+np.cross(omega,h)
        x=high[c]+low[c]+t*((high[c+1]-high[c])+(low[c+1]-low[c]))+lift
        total+=.5*weight*float(body@mom);linear+=weight*p;angular+=weight*(np.cross(x,p)+h)
        inertia[6*c:6*c+3]+=weight*(1-t)*pd;inertia[6*(c+1):6*(c+1)+3]+=weight*t*pd
        inertia[18+3*c:21+3*c]+=weight*(np.cross(lift,pd)+hd+np.cross(field,p))
    if not np.isfinite(np.r_[total,linear,angular,inertia]).all():raise ValueError('finite independent kinetic fields required')
    return dict(T=total,P=linear,H=angular,inertia=inertia)



def _represented_chord_and_strain(u,high,low,points,left,right):
    """Round each exact represented-input contraction once, not O(1)-O(1).

    This is independent rational arithmetic, not the owner's effective SO3 or
    compensated geometry routine. High/low coordinate parts remain separate
    until after all products/cancellations. No missing input bits are recovered.
    """
    chord=[Fraction(float(high[right,j]))+Fraction(float(low[right,j]))-
           Fraction(float(high[left,j]))-Fraction(float(low[left,j]))for j in range(3)]
    reference=[Fraction(float(points[right,j]))-Fraction(float(points[left,j]))for j in range(3)]
    strain=[float(sum((Fraction(float(u[j,i]))*chord[j]for j in range(3)),Fraction(0))-reference[i])for i in range(3)]
    return np.array([float(x)for x in chord]),np.array(strain)


def _relative_frame(u,r0,vertex):
    """Correctly rounded entries of (U R0).T Q from represented primitives."""
    return np.array([[float(sum((Fraction(float(u[j,i]))*Fraction(float(r0[i,a]))*
        Fraction(float(vertex[j,b]))for i in range(3)for j in range(3)),Fraction(0)))
        for b in range(3)]for a in range(3)])


def elastic(state):
    """Independent constrained complementary minimum at original4 stations/cell.

    Min sum(w/2*[n,m].T*S*[n,m]) subject sum(w*V.T*n)=F.
    Q=sum(w*V.T*Snn^-1*V), c=sum(w*V.T*Snn^-1*Snm*m), lambda=Q^-1(F+c).
    """
    points,frames,stiffness,_=primitive_inputs();s=np.linalg.inv(stiffness);snn_inv=np.linalg.inv(s[:3,:3])
    x=np.asarray(state['positions']);low=np.asarray(state['position_low']);u=np.asarray(state['cell_rotations'])[0]
    vertices=np.asarray(state['nodal_frames']);p=np.asarray(state['resultants'])[0]
    psi=0.;work=0.;residual=np.zeros(42);k=np.zeros(18);dpsi=np.zeros(18)
    for cell in (0,1):
        force=p[3*cell:3*cell+3];ml=p[6+6*cell:9+6*cell];mr=p[9+6*cell:12+6*cell]
        chord,z=_represented_chord_and_strain(u[cell],x,low,points,cell,cell+1)
        k[3*cell:3*cell+3]=z;Q=np.zeros((3,3));rhs=np.zeros(3);rows=[]
        for c,t,frame,offset,weight,jac in stations(4):
            if c!=cell:continue
            v=frame.T/jac;m=(1-t)*ml+t*mr
            Q+=weight*(v.T@snn_inv@v);rhs+=weight*(v.T@snn_inv@s[:3,3:]@m);rows.append((t,weight,v,m))
        lam=np.linalg.solve(Q,force+rhs);dpsi[3*cell:3*cell+3]=lam
        for t,weight,v,m in rows:
            n=snn_inv@(v@lam-s[:3,3:]@m);stress=np.r_[n,m]
            if np.linalg.norm(stress)>=1e6:raise ValueError('independent virgin elastic audit domain required')
            psi+=.5*weight*float(stress@s@stress)
            curvature=s[3:,:3]@n+s[3:,3:]@m
            dpsi[6+6*cell:9+6*cell]+=weight*(1-t)*curvature
            dpsi[9+6*cell:12+6*cell]+=weight*t*curvature
        uf=u[cell]@force;residual[6*cell:6*cell+3]-=uf;residual[6*(cell+1):6*(cell+1)+3]+=uf
        cell_torque=-np.cross(chord,uf)
        for node,m,sign,sl in [(cell,ml,-1.,slice(6+6*cell,9+6*cell)),(cell+1,mr,1.,slice(9+6*cell,12+6*cell))]:
            base=u[cell]@frames[node];ell=log_rotation(_relative_frame(u[cell],frames[node],vertices[node]));k[sl]=sign*ell
            torque=sign*base@(inverse_left_log(ell).T@m)
            residual[6*node+3:6*node+6]+=torque;cell_torque-=torque
        residual[18+3*cell:21+3*cell]=cell_torque
    residual[24:]=k-dpsi
    work=float(sum((Fraction(float(a))*Fraction(float(b))for a,b in zip(p,k)),Fraction(0)))
    return dict(Psi=float(psi),Pi=work-float(psi),witness=work-2.*float(psi),compatibility=k-dpsi,residual=residual)
