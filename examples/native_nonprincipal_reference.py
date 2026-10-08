"""Independent nonlinear spatial two-half-cell DEVELOPMENT reference.

No production imports. All15 physical coordinates, positive rotary inertia and
nonprincipal gyro terms remain. Only massless free nodal traces are eliminated
on the explicitly bounded isotropic elastic geodesic branch.
"""
import math
import numpy as np

LENGTH=1.;ELL=.5;RHO=2.;EA=128.;GA=32.;EI=2.
JDENSITY=np.array((.12,.17,.19))
POINTS=np.array(((-.5,0.,0.),(0.,0.,0.),(.5,0.,0.)))
OMEGA=np.array(((2.,3.,4.),(-1.,4.,2.)));DT=1./64;STEPS=4
RELATIVE_LIMIT=.5
SPIN_SCALE=math.sqrt(29.);ACC_SCALE=29.
ANGLE_SCALE=1.  # rad; temporal orientation error uses the SO3 angle.
TRANSLATION_VELOCITY_SCALE=LENGTH*SPIN_SCALE
FORCE_SCALE=RHO*LENGTH**2*ACC_SCALE
MOMENT_SCALE=float(max(JDENSITY))*LENGTH*ACC_SCALE


def skew(w):
    x,y,z=w;return np.array(((0.,-z,y),(z,0.,-x),(-y,x,0.)))


def exp(w):
    t=float(np.linalg.norm(w));s=skew(w)
    if t<1.e-4:
        t2=t*t;a=1-t2/6+t2*t2/120-t2**3/5040
        b=.5-t2/24+t2*t2/720-t2**3/40320
    else:a=math.sin(t)/t;b=2*(math.sin(t/2)/t)**2
    return np.eye(3)+a*s+b*(s@s)


def log(r):
    v=np.array((r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]))/2
    sn=float(np.linalg.norm(v));c=float((np.trace(r)-1)/2)
    if c<=0.:raise ValueError('reference relative rotation branch unresolved')
    angle=math.atan2(sn,c)
    if angle>=RELATIVE_LIMIT:raise ValueError('reference relative geodesic branch exceeded')
    if sn<1.e-8:return v*(1+sn*sn/6+3*sn**4/40)
    return (angle/sn)*v


def translation_mass():
    m=np.zeros((3,3))
    for left in (0,1):m[left:left+2,left:left+2]+=RHO*ELL/6*np.array(((2.,1.),(1.,2.)))
    return np.kron(m,np.eye(3))


def physical_mass(cells):
    m=np.zeros((15,15));m[:9,:9]=translation_mass()
    for c,u in enumerate(cells):m[9+3*c:12+3*c,9+3*c:12+3*c]=ELL*u@np.diag(JDENSITY)@u.T
    return m


def elastic(positions,cells):
    """Exact eliminated potential/physical gradient and recoverable traces."""
    gamma=log(cells[0].T@cells[1]);world=cells[0]@gamma
    frames=np.array([cells[0]@exp(a*gamma) for a in (-.25,.5,1.25)])
    energy=3*EI/(4*ELL)*float(gamma@gamma)
    force=np.zeros((3,3));torque=np.zeros((2,3));n=[]
    for c in (0,1):
        d=positions[c+1]-positions[c];u=cells[c]
        z=u.T@d-ELL*np.array((1.,0.,0.));body=np.array((EA,GA,GA))*z/ELL
        f=u@body;force[c]-=f;force[c+1]+=f;torque[c]-=np.cross(d,f)
        energy+=float(z@body)/2;n.append(body)
    torque[0]-=3*EI/(2*ELL)*world;torque[1]+=3*EI/(2*ELL)*world
    moments=np.array(((np.zeros(3),1.5*EI/ELL*gamma),(1.5*EI/ELL*gamma,np.zeros(3))))
    return energy,np.r_[force.ravel(),torque.ravel()],dict(frames=frames,forces=np.array(n),moments=moments,gamma=gamma)


def initial():
    x=POINTS.copy();u=np.tile(np.eye(3),(2,1,1))
    v=np.r_[np.cross(np.mean(OMEGA,axis=0),x).ravel(),OMEGA.ravel()]
    return x,u,v,acceleration(x,u,v)


def gyro(cells,v):
    out=np.zeros(15)
    for c,u in enumerate(cells):
        w=v[9+3*c:12+3*c];j=ELL*u@np.diag(JDENSITY)@u.T
        out[9+3*c:12+3*c]=np.cross(w,j@w)
    return out


def acceleration(x,u,v):
    return np.linalg.solve(physical_mass(u),-elastic(x,u)[1]-gyro(u,v))


def displaced(x,u,d):
    return x+d[:9].reshape(3,3),np.array([exp(d[9+3*c:12+3*c])@u[c] for c in (0,1)])


def account(x,u,v):
    m=translation_mass();linear=(m@v[:9]).reshape(3,3)
    angular=np.sum(np.cross(x,linear),axis=0)
    for c,r in enumerate(u):angular+=ELL*r@np.diag(JDENSITY)@r.T@v[9+3*c:12+3*c]
    strain=elastic(x,u)[0];kinetic=float(v@physical_mass(u)@v)/2
    return dict(elastic_energy=strain,kinetic_energy=kinetic,total_energy=strain+kinetic,
                linear_momentum=np.sum(linear,axis=0),angular_momentum=angular)


def rotation_angle(r):
    axial=np.array((r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]))/2
    return math.atan2(float(np.linalg.norm(axial)),float((np.trace(r)-1)/2))


def temporal_errors(x,u,v,expected):
    """Dimensionless response rows with separate physical-unit scales."""
    return dict(position=float(np.max(np.abs(x-expected['x'])))/LENGTH,
        rotation=max(rotation_angle(u[c]@expected['u'][c].T) for c in (0,1))/ANGLE_SCALE,
        nodal_velocity=float(np.max(np.abs(v[:9]-expected['v'][:9])))/TRANSLATION_VELOCITY_SCALE,
        cell_omega=float(np.max(np.abs(v[9:]-expected['v'][9:])))/SPIN_SCALE)


def step(x,u,v,h,*,difference=2.**-16):
    """Independent physical midpoint; FD is bounded reference Newton only."""
    if not 0<h<=DT or not math.isfinite(h):raise ValueError('reference step bound')
    a=acceleration(x,u,v);scales=np.r_[np.full(9,FORCE_SCALE),np.full(6,MOMENT_SCALE)]
    ascale=np.r_[np.full(9,LENGTH*ACC_SCALE),np.full(6,ACC_SCALE)]
    def evaluate(am):
        xm,um=displaced(x,u,.5*h*v+.25*h*h*am);vm=v+.5*h*am
        residual=physical_mass(um)@am+elastic(xm,um)[1]+gyro(um,vm)
        return residual/scales,(xm,um,vm)
    for iteration in range(24):
        r,stage=evaluate(a)
        if np.max(np.abs(r))<=1.e-12:break
        jac=np.column_stack([(evaluate(a+difference*ascale[k]*np.eye(15)[k])[0]-
                              evaluate(a-difference*ascale[k]*np.eye(15)[k])[0])/(2*difference)
                              for k in range(15)])
        change=ascale*np.linalg.solve(jac,-r)
        for cut in range(12):
            trial=a+2.**-cut*change
            if np.linalg.norm(evaluate(trial)[0])<np.linalg.norm(r):a=trial;break
        else:raise ValueError('independent midpoint line search unresolved')
    else:raise ValueError('independent midpoint iteration budget')
    xn,un=displaced(x,u,h*v+.5*h*h*a);vn=v+h*a
    return dict(x=xn,u=un,v=vn,a=acceleration(xn,un,vn),stage_x=stage[0],
                stage_u=stage[1],stage_v=stage[2],stage_a=a,iterations=iteration,residual=float(np.max(np.abs(r))))


def trajectory(steps=STEPS,h=DT):
    x,u,v,a=initial();rows=[dict(x=x,u=u,v=v,a=a)]
    for _ in range(steps):
        row=step(x,u,v,h);rows.append(row);x,u,v=row['x'],row['u'],row['v']
    return rows


def left_log_inverse(phi):
    t=float(np.linalg.norm(phi));w=skew(phi)
    if t<1.e-3:a=1/12+t*t/720+t**4/30240
    else:a=(1-(t/2)/math.tan(t/2))/(t*t)
    return np.eye(3)-w/2+a*(w@w)


def full_trace_work(positions,cells,frames):
    """Independent unreduced elastic work; 9 nodal trace torque components."""
    energy=0.;trace=np.zeros((3,3));celltorque=np.zeros((2,3));moments=[]
    for c in (0,1):
        phi=[log(cells[c].T@frames[c]),log(cells[c].T@frames[c+1])]
        b0,b1=-phi[0],phi[1]
        m0=EI/ELL*(4*b0-2*b1);m1=EI/ELL*(-2*b0+4*b1)
        energy+=(float(b0@m0)+float(b1@m1))/2
        for n,ph,m,sign in ((c,phi[0],m0,-1),(c+1,phi[1],m1,1)):
            value=cells[c]@left_log_inverse(ph).T@(sign*m)
            trace[n]+=value;celltorque[c]-=value
        moments.append((m0,m1))
    return energy,trace,celltorque,np.array(moments)


def semidiscrete(steps=STEPS,h=DT,*,subdivisions=64):
    """Independent RK4 ODE reference, not a closed-form Euler-top solution.

    Full rotation matrices evolve by Rdot=skew(omega)R without projection.
    Fine/coarse reference convergence and orthogonality are explicit validity
    controls; this is not a rigorous continuous-time error enclosure.
    """
    if type(subdivisions) is not int or not 8<=subdivisions<=256:raise ValueError('reference subdivision budget')
    x,u,v,_=initial();y=np.r_[x.ravel(),u.ravel(),v]
    def unpack(value):return value[:9].reshape(3,3),value[9:27].reshape(2,3,3),value[27:]
    def derivative(value):
        xx,rr,vv=unpack(value)
        rd=np.array([skew(vv[9+3*c:12+3*c])@rr[c] for c in (0,1)])
        return np.r_[vv[:9],rd.ravel(),acceleration(xx,rr,vv)]
    rows=[];dh=h/subdivisions
    for index in range(steps+1):
        xx,rr,vv=unpack(y)
        if max(np.linalg.norm(r.T@r-np.eye(3),ord=np.inf) for r in rr)>1.e-9:
            raise ValueError('unprojected independent RK4 rotation validity exceeded')
        rows.append(dict(x=xx.copy(),u=rr.copy(),v=vv.copy(),a=acceleration(xx,rr,vv)))
        if index==steps:break
        for _ in range(subdivisions):
            k1=derivative(y);k2=derivative(y+dh*k1/2);k3=derivative(y+dh*k2/2);k4=derivative(y+dh*k3)
            y=y+dh*(k1+2*k2+2*k3+k4)/6
    return rows


def chart_gradient(positions,cells,increment):
    x,u=displaced(positions,cells,increment);force=elastic(x,u)[1].copy()
    for c in (0,1):
        phi=increment[9+3*c:12+3*c];t=float(np.linalg.norm(phi));w=skew(phi)
        if t<1.e-4:a=.5-t*t/24+t**4/720;b=1/6-t*t/120+t**4/5040
        else:a=2*(math.sin(t/2)/t)**2;b=(t-math.sin(t))/t**3
        jl=np.eye(3)+a*w+b*(w@w)
        force[9+3*c:12+3*c]=jl.T@force[9+3*c:12+3*c]
    return force


def discrete_angular_increment(xm,um,vm,am,h):
    """Exact angular increment of the declared numerical midpoint update.

    Includes SO3 integration defect, not fictitious external/support impulse.
    """
    force=(translation_mass()@am[:9]).reshape(3,3)
    orbital=h*np.sum(np.cross(xm,force),axis=0);spin=np.zeros(3)
    for c,u in enumerate(um):
        w=vm[9+3*c:12+3*c];alpha=am[9+3*c:12+3*c];j=ELL*u@np.diag(JDENSITY)@u.T
        plus=exp(h*w/2);minus=exp(-h*w/2)
        spin+=plus@j@plus.T@(w+h*alpha/2)-minus@j@minus.T@(w-h*alpha/2)
    return orbital+spin
