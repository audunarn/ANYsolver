"""Independent declared-plane retained half-cell bending/rotary-inertia oracle.

No production owner, material, residual, tangent, inertia or recovery imports.
This finite reference is a check, not an alternative public integration route.
"""
from fractions import Fraction as F
import math
import numpy as np

ELL=.5
EA=1.e5
GA=3.e4
EI=10.
RHO_A=2.
JX=.02
JY=.01
JZ=.01
AMP=2.**-20
PHASE_STEP=.05
ANGLE_LIMIT=1.e-3
ORIGIN=np.array((.25,-.5,.125))
FREE=np.array((1,2,3,4,6,7,8,9,10,11,12,13))
FORCE_SCALE=GA*AMP/ELL
MOMENT_SCALE=GA*AMP
MAX_ITERATIONS=20
MAX_BACKTRACKS=12


def bending_parts():
    full=np.zeros((9,9));inverse=EI/ELL*np.array(((4.,-2.),(-2.,4.)))
    for cell in range(4):
        b=np.zeros((2,9));b[0,cell]=-1.;b[0,5+cell]=1.
        b[1,cell+1]=1.;b[1,5+cell]=-1.
        full+=b.T@inverse@b
    theta_map=np.zeros((5,4))
    theta_map[1:]=-np.linalg.solve(full[1:5,1:5],full[1:5,5:])
    condensed=full[5:,5:]+full[5:,1:5]@theta_map[1:]
    return full,theta_map,condensed,inverse


def mass_matrix():
    nodal=np.zeros((5,5))
    for cell in range(4):
        nodal[np.ix_((cell,cell+1),(cell,cell+1))]+=RHO_A*ELL/6*np.array(((2.,1.),(1.,2.)))
    mass=np.zeros((14,14));mass[:5,:5]=nodal;mass[5:10,5:10]=nodal
    mass[10:,10:]=JZ*ELL*np.eye(4)
    return mass


def physical_mass_matrix(q):
    """All27 physical mass coordinates, independently rotated principal inertia."""
    if type(q) is not np.ndarray or q.shape!=(14,) or not np.isfinite(q).all():
        raise ValueError('finite declared planar pose required')
    nodal=mass_matrix()[:5,:5];mass=np.zeros((27,27))
    for i in range(5):
        for j in range(5):mass[3*i:3*i+3,3*j:3*j+3]=nodal[i,j]*np.eye(3)
    for cell,phi in enumerate(q[10:]):
        c=math.cos(float(phi));s=math.sin(float(phi))
        rotation=np.array(((c,-s,0.),(s,c,0.),(0.,0.,1.)))
        begin=15+3*cell
        mass[begin:begin+3,begin:begin+3]=ELL*rotation@np.diag((JX,JY,JZ))@rotation.T
    return mass


def storage(q):
    """Exact planar compatible elastic work and analytic first/second variations."""
    if type(q) is not np.ndarray or q.shape!=(14,) or q.dtype!=np.float64 or not np.isfinite(q).all():
        raise ValueError('finite14-coordinate declared plane required')
    full,theta_map,kphi,cinv=bending_parts();phi=q[10:];theta=theta_map@phi
    if max(np.max(np.abs(phi)),np.max(np.abs(theta)))>=ANGLE_LIMIT:
        raise ValueError('reference small-angle/log-branch validity exceeded')
    energy=.5*float(phi@kphi@phi);gradient=np.zeros(14);hessian=np.zeros((14,14))
    gradient[10:]=kphi@phi;hessian[10:,10:]=kphi
    forces=[];moments=[]
    for cell in range(4):
        c=math.cos(float(phi[cell]));s=math.sin(float(phi[cell]));j=10+cell
        du=q[cell+1]-q[cell];dy=q[6+cell]-q[5+cell]
        # Stable exact-equivalent chord strain; retain submicron axial response.
        zx=-2*ELL*math.sin(float(phi[cell])/2)**2+c*du+s*dy
        zy=-ELL*s-s*du+c*dy
        bx=np.zeros(14);by=np.zeros(14)
        dxmap=np.zeros(14);dymap=np.zeros(14)
        dxmap[cell]=-1.;dxmap[cell+1]=1.;dymap[5+cell]=-1.;dymap[6+cell]=1.
        bx[:]=c*dxmap+s*dymap;by[:]=-s*dxmap+c*dymap
        bx[j]=zy;by[j]=-(zx+ELL)
        hx=np.zeros((14,14));hy=np.zeros((14,14))
        hx[:,j]=-s*dxmap+c*dymap;hx[j,:]=hx[:,j];hx[j,j]=-(zx+ELL)
        hy[:,j]=-c*dxmap-s*dymap;hy[j,:]=hy[:,j];hy[j,j]=-zy
        n=EA/ELL*zx;v=GA/ELL*zy
        energy+=.5*(n*zx+v*zy);gradient+=n*bx+v*by
        hessian+=EA/ELL*np.outer(bx,bx)+GA/ELL*np.outer(by,by)+n*hx+v*hy
        forces.append((n,v,0.))
        ends=np.array((phi[cell]-theta[cell],theta[cell+1]-phi[cell]))
        moment=cinv@ends;moments.append(((0.,0.,moment[0]),(0.,0.,moment[1])))
    root_couple=float((full@np.r_[theta,phi])[0])
    if not np.isfinite(energy) or not np.isfinite(gradient).all() or not np.isfinite(hessian).all():
        raise ValueError('nonfinite independent work')
    return energy,gradient,hessian,dict(theta=theta,forces=np.array(forces),moments=np.array(moments),root_couple=root_couple)


def linear_operators():
    return mass_matrix(),storage(np.zeros(14))[2]


def initial_mode():
    """Lowest simple TRANSVERSE mode; fixed sign and displacement normalization."""
    mass,stiffness=linear_operators();ids=np.array((6,7,8,9,10,11,12,13))
    m=mass[np.ix_(ids,ids)];k=stiffness[np.ix_(ids,ids)]
    lower=np.linalg.cholesky(m);inverse=np.linalg.inv(lower)
    values,modes=np.linalg.eigh(inverse@k@inverse.T)
    if values[0]<=0. or (values[1]-values[0])/values[0]<=1.e-8:
        raise ValueError('positive simple lowest transverse eigenmode required')
    q=np.zeros(14);q[ids]=np.linalg.solve(lower.T,modes[:,0])
    if q[9]==0.:raise ValueError('nonzero modal tip/sign required')
    q*=math.copysign(AMP/np.max(np.abs(q[5:10])),float(q[9]))
    omega=math.sqrt(float(values[0]));ideal=PHASE_STEP/omega
    # Dyadic21-bit mantissa ensures the four accepted timestamp sums are exact.
    exponent=math.frexp(ideal)[1];quantum=math.ldexp(1.,exponent-21)
    dt=math.floor(ideal/quantum)*quantum
    if not 0.<dt<=ideal:raise ValueError('positive prospective dyadic dt required')
    energy=storage(q)[0]
    if energy<=0.:raise ValueError('positive declared initial elastic energy required')
    return dict(q=q,v=np.zeros(14),omega=omega,dt=dt,energy_scale=energy,
        coordinate_scale=np.r_[np.full(10,AMP),np.full(4,np.max(np.abs(q[10:])))],
        modal_relative_gap=float((values[1]-values[0])/values[0]),phase_per_step=omega*dt)


def acceleration(q):
    mass=mass_matrix();g=storage(q)[1];a=np.zeros(14)
    a[FREE]=np.linalg.solve(mass[np.ix_(FREE,FREE)],-g[FREE])
    return a


def step(q,v,h):
    """Bounded independent full nonlinear plane midpoint equilibrium."""
    storage(q)
    if type(v) is not np.ndarray or v.shape!=(14,) or v.dtype!=np.float64 or not np.isfinite(v).all():
        raise ValueError('finite14-coordinate reference velocity required')
    if q[0]!=0. or q[5]!=0. or v[0]!=0. or v[5]!=0.:raise ValueError('exact homogeneous root required')
    if not math.isfinite(h) or h<=0. or not math.isfinite(h*h) or h*h==0.:raise ValueError('finite positive reference time step required')
    mass=mass_matrix();a=acceleration(q);scale=np.r_[np.full(10,FORCE_SCALE),np.full(4,MOMENT_SCALE)]
    for iteration in range(MAX_ITERATIONS+1):
        stageq=q+.5*h*v+.25*h*h*a;energy,g,j,fields=storage(stageq)
        residual=mass@a+g;norm=float(np.max(np.abs(residual[FREE]/scale[FREE])))
        if norm<=1.e-12:break
        if iteration==MAX_ITERATIONS:raise ValueError('independent midpoint iteration limit')
        direction=np.zeros(14)
        direction[FREE]=np.linalg.solve((mass+.25*h*h*j)[np.ix_(FREE,FREE)],-residual[FREE])
        for cut in range(MAX_BACKTRACKS+1):
            proposed=a+math.ldexp(1.,-cut)*direction
            rt=mass@proposed+storage(q+.5*h*v+.25*h*h*proposed)[1]
            if np.max(np.abs(rt[FREE]/scale[FREE]))<norm:a=proposed;break
        else:raise ValueError('independent midpoint backtracking limit')
    endq=q+h*v+.5*h*h*a;endv=v+h*a;stagev=v+.5*h*a
    force=np.array((residual[0],residual[5],0.));couple=np.array((0.,0.,fields['root_couple']))
    moment=np.cross(ORIGIN,force)+couple
    return dict(q=endq,v=endv,a=acceleration(endq),stage_q=stageq,stage_v=stagev,stage_a=a,
        support_force=force,support_couple=couple,support_moment=moment,
        force_impulse=h*force,moment_impulse=h*moment,support_work=0.,iterations=iteration)


def account(q,v):
    mass=mass_matrix();nodal=mass[:5,:5];energy=storage(q)[0]
    px=float(np.ones(5)@nodal@v[:5]);py=float(np.ones(5)@nodal@v[5:10])
    x=ORIGIN[0]+ELL*np.arange(5)+q[:5];y=ORIGIN[1]+q[5:10]
    hz=float(x@nodal@v[5:10]-y@nodal@v[:5]+JZ*ELL*np.sum(v[10:]))
    kinetic=.5*float(v@mass@v)
    return dict(elastic_energy=energy,kinetic_energy=kinetic,total_energy=energy+kinetic,
        linear_momentum=np.array((px,py,0.)),angular_momentum=np.array((-ORIGIN[2]*py,ORIGIN[2]*px,hz)))


def semidiscrete_exact(t,mode):
    omega=mode['omega'];q=mode['q']
    return q*math.cos(omega*t),-omega*q*math.sin(omega*t),-omega**2*q*math.cos(omega*t)


def linear_midpoint_exact(count,mode):
    angle=count*2*math.atan(.5*mode['omega']*mode['dt']);q=mode['q'];omega=mode['omega']
    return q*math.cos(angle),-omega*q*math.sin(angle),-omega**2*q*math.cos(angle)


def _inverse_exact(matrix):
    """Fixed small exact rational inverse; no native/recovery dependency."""
    n=len(matrix);work=[list(row)+[F(int(i==j)) for j in range(n)] for i,row in enumerate(matrix)]
    for i in range(n):
        pivot=next((j for j in range(i,n) if work[j][i]),None)
        if pivot is None:raise ValueError('singular exact reference block')
        work[i],work[pivot]=work[pivot],work[i];value=work[i][i]
        work[i]=[x/value for x in work[i]]
        for j in range(n):
            if j!=i:
                value=work[j][i];work[j]=[x-value*y for x,y in zip(work[j],work[i])]
    return [row[n:] for row in work]


def _rational_operators():
    ell,ea,ga,ei,rho,jz=map(F,(ELL,EA,GA,EI,RHO_A,JZ))
    kb=[[F(0) for _ in range(9)] for _ in range(9)]
    cinv=[[4*ei/ell,-2*ei/ell],[-2*ei/ell,4*ei/ell]]
    for cell in range(4):
        rows=({cell:F(-1),5+cell:F(1)},{cell+1:F(1),5+cell:F(-1)})
        for a in range(2):
            for b in range(2):
                for i,x in rows[a].items():
                    for j,y in rows[b].items():kb[i][j]+=x*cinv[a][b]*y
    tt=_inverse_exact([[kb[i][j] for j in range(1,5)] for i in range(1,5)])
    mapping=[[F(0)]*4]+[[-sum(tt[i][j]*kb[j+1][k+5] for j in range(4)) for k in range(4)] for i in range(4)]
    kphi=[[kb[i+5][j+5]+sum(kb[i+5][a+1]*mapping[a+1][j] for a in range(4)) for j in range(4)] for i in range(4)]
    mass=[[F(0) for _ in range(14)] for _ in range(14)]
    stiffness=[[F(0) for _ in range(14)] for _ in range(14)]
    for cell in range(4):
        for offset in (0,5):
            for i in range(2):
                for j in range(2):mass[offset+cell+i][offset+cell+j]+=rho*ell*F(2 if i==j else 1,6)
        mass[10+cell][10+cell]=jz*ell
        rows=({cell:F(-1),cell+1:F(1)},
              {5+cell:F(-1),6+cell:F(1),10+cell:-ell})
        for row,coefficient in zip(rows,(ea/ell,ga/ell)):
            for i,x in row.items():
                for j,y in row.items():stiffness[i][j]+=coefficient*x*y
    for i in range(4):
        for j in range(4):stiffness[i+10][j+10]+=kphi[i][j]
    return mass,stiffness,kphi,mapping


def _sqrt_upper(value):
    if value<0:raise ValueError('nonnegative rational square required')
    result=math.sqrt(float(value))
    if not math.isfinite(result):raise ValueError('finite bound required')
    while F(result)*F(result)<value:result=math.nextafter(result,math.inf)
    return F(result)


def _float_upper(value):
    result=float(value)
    if not math.isfinite(result):raise ValueError('finite reference bound required')
    if F(result)<value:result=math.nextafter(result,math.inf)
    return result


def linear_remainder_bound(mode,steps=4):
    """Conditional mathematical nonlinear/rest-linear midpoint error bound.

    Exact rational matrix arithmetic and trig inequalities; all reference/native
    stages must separately satisfy the returned energy box and planar chart.
    This is not a floating-point interval certificate for native SO3 arithmetic.
    The 2% energy box is prospective, not fitted to observed trajectories.
    """
    if type(steps) is not int or not 0<=steps<=4:raise ValueError('fixed four-step reference budget')
    mass,stiffness,kphi,mapping=_rational_operators();q=list(map(F,mode['q']))
    ell,ea,ga=map(F,(ELL,EA,GA));initial=sum(q[i+10]*kphi[i][j]*q[j+10]/2 for i in range(4) for j in range(4))
    for c in range(4):
        u=abs(q[c+1]-q[c]);w=abs(q[c+6]-q[c+5]);p=abs(q[c+10])
        zx=u+p*p*(ell+u)/2+p*w
        zy=abs(q[c+6]-q[c+5]-ell*q[c+10])+p*u+p*p*w/2+ell*p**3/6
        initial+=(ea*zx*zx+ga*zy*zy)/(2*ell)
    box=F(102,100)*initial;kp_inverse=_inverse_exact(kphi)
    p=max(_sqrt_upper(2*box*kp_inverse[i][i]) for i in range(4))
    theta=p*max(sum(abs(x) for x in row) for row in mapping)
    if max(p,theta)>=F(ANGLE_LIMIT):raise ValueError('prospective energy box exceeds small-angle branch')
    a=_sqrt_upper(2*box*ell/ea);b=_sqrt_upper(2*box*ell/ga)
    u=a+ell*p*p/2+p*b;w=p*(ell+a)+b
    dx=p*p*(ell+u)/2+p*w;dy=p*u+p*p*w/2+ell*p**3/6
    rx=ea/ell*dx+ea/ell*a*p*p/2+ga/ell*b*p
    rw=ea/ell*a*p+ga/ell*dy+ga/ell*b*p*p/2
    rp=(ea+ga)/ell*a*b+ga*dy
    residual=[F(0)]*14
    for c in range(4):
        for node in (c,c+1):residual[node]+=rx;residual[5+node]+=rw
        residual[10+c]+=rp
    # The binary modal eigenvector/omega is not an exact rational eigenpair.
    # Its sinusoidal/cayley path has a forcing defect bounded by this exact
    # rest Kq-omega^2 Mq, since every modal stage amplitude has modulus<=1.
    omega2=F(mode['omega'])**2
    eigen_residual=[sum((stiffness[i][j]-omega2*mass[i][j])*q[j] for j in range(14)) for i in range(14)]
    for i in FREE:residual[int(i)]+=abs(eigen_residual[int(i)])
    dq=[F(0)]*14;dv=[F(0)]*14;da=[F(0)]*14;horizon=steps*F(mode['dt'])
    # Separate axial/transverse invariant blocks avoid spurious axial noise
    # amplification by the soft bending inverse.
    for ids in ((1,2,3,4),(6,7,8,9,10,11,12,13)):
        mi=_inverse_exact([[mass[i][j] for j in ids] for i in ids])
        ki=_inverse_exact([[stiffness[i][j] for j in ids] for i in ids])
        noise=_sqrt_upper(sum(residual[i]*abs(mi[a][b])*residual[j] for a,i in enumerate(ids) for b,j in enumerate(ids)))
        for a,i in enumerate(ids):
            dq[i]=horizon*noise*_sqrt_upper(ki[a][a]);dv[i]=horizon*noise*_sqrt_upper(mi[a][a])
        for a,i in enumerate(ids):
            da[i]=sum(abs(mi[a][b])*(residual[j]+sum(abs(stiffness[j][k])*dq[k] for k in ids)) for b,j in enumerate(ids))
    return dict(energy_box=_float_upper(box),angle_box=_float_upper(max(p,theta)),
        q=np.array([_float_upper(x) for x in dq]),v=np.array([_float_upper(x) for x in dv]),
        eigen_residual_upper=np.array([_float_upper(abs(x)) for x in eigen_residual]),
        a=np.array([_float_upper(x) for x in da]),semantics='CONDITIONAL_EXACT_REAL_MIDPOINT_PERTURBATION_BOUND')
