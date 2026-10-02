"""Development moving-front geometry for straight retained round surfaces.

The unnormalised plane gap is A(t,angle)+B(t)*xi. Its axial zero is
xi=-A/B, and stationary fronts satisfy A'B-AB'=0. These local values do
not certify complete root isolation or admit a quadrature panel by themselves.
"""
from dataclasses import dataclass
from math import cos,sin
import numpy as np
from .native_surface_path import material_path_pose
from .native_surface_support import _support_path,_base,segment_gap_slab_enclosure


@dataclass(frozen=True)
class AxialContactFront:
    a: float
    b: float
    a_rate: float
    b_rate: float
    a_acceleration: float
    b_acceleration: float
    plane_area: float

    def axial_coordinate(self):
        if self.b==0.:raise ValueError('axial front is singular; angular partition required')
        return self._finite(-self.a/self.b)

    @staticmethod
    def _finite(value):
        if not np.isfinite(value):raise ValueError('nonfinite axial front quotient or derivative')
        return value

    @property
    def stationary_numerator(self):return self._finite(self.a_rate*self.b-self.a*self.b_rate)

    @property
    def stationary_rate(self):return self._finite(self.a_acceleration*self.b-self.a*self.b_acceleration)


def axial_contact_front(field,cell,segment_index,time,angle):
    """Actual path coefficient derivatives; no finite differences or node sampling."""
    rule=field.patch.rule;lo,hi=rule.definition['xi_range']
    xis=(max(lo,-1.+cell),min(hi,float(cell)))
    # Exact field/reference/half-cell validation, also used by interval geometry.
    segment_gap_slab_enclosure(field,cell,xis,rule.definition['angle_range'],segment_index)
    if not np.isfinite(angle) or not rule.definition['angle_range'][0]<=angle<=rule.definition['angle_range'][1]:
        raise ValueError('front angle outside material selection')
    start,segments=_support_path(field,segment_index);segment=segments[0]
    pose=material_path_pose(start,segment.translations,segment.angular,segment.shell_increment,time)
    target=field.patch.target;corners=target.adapter.current_positions(pose.shell_displacement)
    target.physical_pose(pose.shell_displacement)
    velocities=np.asarray(target.adapter.work_map@segment.shell_increment).reshape(3,3)
    e1,e2=corners[1]-corners[0],corners[2]-corners[0]
    v1,v2=velocities[1]-velocities[0],velocities[2]-velocities[0]
    cross=np.cross(e1,e2);rate=np.cross(v1,e2)+np.cross(e1,v2);acceleration=2*np.cross(v1,v2)
    frame=pose.cell_rotations[cell]@field.patch.source.reference.nodal_triads[0]
    arm=rule.definition['radius']*(cos(angle)*frame[:,1]+sin(angle)*frame[:,2])
    omega=segment.angular[cell];arm_rate=np.cross(omega,arm);arm_acceleration=np.cross(omega,arm_rate)
    # xi=0 extrapolation is exact for either straight half-cell.
    base=_base(pose,cell,0.,corners[0])
    chord=_base(pose,cell,float(cell),corners[0])-_base(pose,cell,float(cell-1),corners[0])
    t=1. if cell==0 else 0.
    base_rate=(1-t)*segment.translations[cell]+t*segment.translations[cell+1]-velocities[0]
    chord_rate=segment.translations[cell+1]-segment.translations[cell]
    x=base+arm;xd=base_rate+arm_rate
    values=(cross@x,cross@chord,rate@x+cross@xd,rate@chord+cross@chord_rate,
        acceleration@x+2*rate@xd+cross@arm_acceleration,
        acceleration@chord+2*rate@chord_rate,np.linalg.norm(cross))
    if not np.all(np.isfinite(values)):raise ValueError('nonfinite axial front geometry')
    return AxialContactFront(*map(float,values))


def stationary_front_slab(field,cell,segment_index,angle,left,right,*,include_a=False,angle_bounds=None):
    """Padded binary64 Taylor bounds for B, N and N' on one time slab.

    C is quadratic, the chord is affine, and the material arm has constant
    angular speed. Product-rule norm bounds give |A'''| and |B'''|. They imply
    |N''| <= |A'''B|+|A''B'|+|A'B''|+|AB'''|. No sampled extrema are used.
    """
    if not 0<=left<=right<=1:raise ValueError('ordered front time slab required')
    angular_width=0.
    if angle_bounds is not None:
        lo,hi=map(float,angle_bounds);domain=field.patch.rule.definition['angle_range']
        if not np.isfinite(lo+hi) or not domain[0]<=lo<=angle<=hi<=domain[1]:
            raise ValueError('stationary angular slab outside material selection')
        angular_width=max(angle-lo,hi-angle)
    start,segments=_support_path(field,segment_index);segment=segments[0]
    target=field.patch.target;middle=(left+right)/2;h=(right-left)/2
    value=axial_contact_front(field,cell,segment_index,middle,angle)
    poses=[material_path_pose(start,segment.translations,segment.angular,segment.shell_increment,t) for t in (left,right)]
    corners=[target.adapter.current_positions(p.shell_displacement) for p in poses]
    velocities=np.asarray(target.adapter.work_map@segment.shell_increment).reshape(3,3)
    da,db=velocities[1]-velocities[0],velocities[2]-velocities[0]
    edges=[(y[1]-y[0],y[2]-y[0]) for y in corners]
    a0,b0=edges[0];a1,b1=edges[1]
    controls=(np.cross(a0,b0),.5*(np.cross(a0,b1)+np.cross(a1,b0)),np.cross(a1,b1))
    reference=target.adapter.reference_positions
    refcross=np.cross(reference[1]-reference[0],reference[2]-reference[0]);refnormal=refcross/np.linalg.norm(refcross)
    c=max(np.linalg.norm(v) for v in controls)
    if min(float(refnormal@v) for v in controls)<=512*np.finfo(float).eps*max(1.,c):
        raise ValueError('stationary front target area unresolved')
    cd=max(np.linalg.norm(np.cross(da,b)+np.cross(a,db)) for a,b in edges)
    cdd=2*np.linalg.norm(np.cross(da,db))
    t=1. if cell==0 else 0.
    velocity=(1-t)*segment.translations[cell]+t*segment.translations[cell+1]-velocities[0]
    chord_velocity=segment.translations[cell+1]-segment.translations[cell]
    omega=np.linalg.norm(segment.angular[cell]);radius=field.patch.rule.definition['radius']
    a3=3*cdd*(np.linalg.norm(velocity)+omega*radius)+3*cd*omega**2*radius+c*omega**3*radius
    b3=3*cdd*np.linalg.norm(chord_velocity)
    xnorm=max(np.linalg.norm(_base(p,cell,0.,y[0])) for p,y in zip(poses,corners))+radius
    dnorm=max(np.linalg.norm(_base(p,cell,float(cell),y[0])-_base(p,cell,float(cell-1),y[0])) for p,y in zip(poses,corners))
    xrate=np.linalg.norm(velocity)+omega*radius;drate=np.linalg.norm(chord_velocity)
    coefficient_scale=max(1.,c*xnorm,c*dnorm,cd*xnorm+c*xrate,cd*dnorm+c*drate,
        cdd*xnorm+2*cd*xrate+c*omega**2*radius,cdd*dnorm+2*cd*drate,
        *(float(np.max(np.abs(y))) for y in corners))
    coefficient_error=512*np.finfo(float).eps*coefficient_scale
    a3+=coefficient_error;b3+=coefficient_error
    a2=abs(value.a_acceleration)+a3*h;b2=abs(value.b_acceleration)+b3*h
    a1bound=abs(value.a_rate)+a2*h;b1bound=abs(value.b_rate)+b2*h
    a_bound=abs(value.a)+a1bound*h;b_bound=abs(value.b)+b1bound*h
    n2=a3*b_bound+a2*b1bound+a1bound*b2+a_bound*b3
    scale=max(1.,c,cd,cdd,a_bound,b_bound,a1bound,b1bound,a2,b2,n2,
        *(float(np.max(np.abs(y))) for y in corners))
    pad=max(coefficient_error,512*np.finfo(float).eps*scale)
    # Propagate coefficient uncertainty and product-rounding BEFORE cancellation.
    nerror=pad*(a1bound+b_bound+a_bound+b1bound)+2*pad*pad
    nerror+=512*np.finfo(float).eps*(a1bound*b_bound+a_bound*b1bound)
    nderror=pad*(a2+b_bound+a_bound+b2)+2*pad*pad
    nderror+=512*np.finfo(float).eps*(a2*b_bound+a_bound*b2)
    n=value.stationary_numerator;nd=value.stationary_rate
    bwidth=abs(value.b_rate)*h+.5*b2*h*h+pad
    nwidth=(abs(nd)+nderror)*h+.5*n2*h*h+nerror
    ndwidth=n2*h+nderror
    # B has no angular dependence. Differentiate only the round-section arm;
    # the following norm bounds hold over the entire time and angular slab.
    a_theta=c*radius
    arate_theta=(cd+c*omega)*radius
    aacc_theta=(cdd+2*cd*omega+c*omega**2)*radius
    nwidth+=(arate_theta*(b_bound+pad)+a_theta*(b1bound+pad))*angular_width
    ndwidth+=(aacc_theta*(b_bound+pad)+a_theta*(b2+pad))*angular_width
    result=(value.b-bwidth,value.b+bwidth,n-nwidth,n+nwidth,nd-ndwidth,nd+ndwidth)
    if not np.all(np.isfinite(result)):raise ValueError('nonfinite stationary front bounds')
    if include_a:
        awidth=abs(value.a_rate)*h+.5*a2*h*h+pad+a_theta*angular_width
        return (*result,value.a-awidth,value.a+awidth)
    return result


@dataclass(frozen=True)
class StationaryAngularCover:
    field_identity: str
    cell: int
    segment_index: int
    angle_bounds: tuple
    branches: tuple

    def __iter__(self):return iter(self.branches)
    def __len__(self):return len(self.branches)
    def __bool__(self):return bool(self.branches)


def stationary_front_angular_cover(field,cell,segment_index,angle_bounds,*,budget):
    """Certify stationary-root branches over an entire angular interval.

    Each returned time bracket contains exactly one simple stationary root for
    every angle. All remaining time slabs exclude roots. Angular bands where
    roots enter/leave a time endpoint remain explicit non-success and require
    boundary partitioning. This does not itself admit friction integration.
    """
    from .native_surface_support import SupportIntervalBudget
    if type(budget) is not SupportIntervalBudget:raise TypeError('shared support budget required')
    lo,hi=map(float,angle_bounds);angle=(lo+hi)/2
    pending=[(0.,1.)];branches=[];cache={}
    def enclosure(left,right):
        if (left,right) not in cache:
            if not budget.consume():raise MemoryError('stationary angular cover interval cap exhausted')
            cache[left,right]=stationary_front_slab(field,cell,segment_index,angle,left,right,
                angle_bounds=(lo,hi))
        return cache[left,right]
    while pending:
        left,right=pending.pop();bl,bu,nl,nu,dl,du=enclosure(left,right)
        if bl>0 or bu<0:
            if nl>0 or nu<0:continue
            if dl>0 or du<0:
                endpoint=[enclosure(t,t)[2:4] for t in (left,right)]
                signs=[1 if low>0 else -1 if high<0 else 0 for low,high in endpoint]
                if 0 in signs:raise ValueError('stationary root angular endpoint transition unresolved')
                if signs[0]!=signs[1]:branches.append((left,right))
                continue
        middle=(left+right)/2
        if not left<middle<right:raise ValueError('stationary angular cover temporal resolution exhausted')
        pending.extend(((middle,right),(left,middle)))
    return StationaryAngularCover(field.identity,cell,segment_index,(lo,hi),tuple(sorted(branches)))


@dataclass(frozen=True)
class IsolatedStationaryFront:
    fraction: float
    axial_coordinate: float
    time_bracket: tuple
    axial_interval: tuple
    numerator_residual: float


def stationary_front_partition(field,cell,segment_index,angle,*,maximum_intervals=128,maximum_axial_uncertainty=None,budget=None,angular_cover=None):
    """Complete bounded time isolation, returning endpoint and stationary fronts.

    Singular B or unresolved multiple stationary roots cause explicit non-success.
    This partitions one fixed angle only; angular integration remains separate.
    """
    from scipy.optimize import brentq
    if type(maximum_intervals) is not int or maximum_intervals<1:
        raise ValueError('positive stationary-front interval cap required')
    if maximum_axial_uncertainty is not None and (not np.isfinite(maximum_axial_uncertainty) or maximum_axial_uncertainty<=0):
        raise ValueError('positive dimensionless axial uncertainty required')
    if budget is not None:
        from .native_surface_support import SupportIntervalBudget
        if type(budget) is not SupportIntervalBudget:raise TypeError('shared support budget required')
    cache={}
    def at(t):
        if t not in cache:cache[t]=axial_contact_front(field,cell,segment_index,t,angle)
        return cache[t]
    if angular_cover is not None:
        if (type(angular_cover) is not StationaryAngularCover or angular_cover.field_identity!=field.identity
                or angular_cover.cell!=cell or angular_cover.segment_index!=segment_index
                or not angular_cover.angle_bounds[0]<=angle<=angular_cover.angle_bounds[1]):
            raise ValueError('stationary angular cover identity mismatch')
        pending=list(angular_cover.branches)
    else:pending=[(0.,1.)]
    roots={};count=0;slabs={}
    def enclose(left,right):
        nonlocal count
        key=(left,right)
        if key not in slabs:
            if count>=maximum_intervals:raise MemoryError('stationary-front interval cap exhausted')
            if budget is not None and not budget.consume():raise MemoryError('stationary-front shared interval cap exhausted')
            count+=1
            slabs[key]=stationary_front_slab(field,cell,segment_index,angle,left,right,include_a=True)
        return slabs[key]
    while pending:
        left,right=pending.pop()
        bl,bu,nl,nu,dl,du,_,_=enclose(left,right)
        if bl>0. or bu<0.:
            if nl>0. or nu<0.:continue
            if dl>0. or du<0.:
                ends=[enclose(t,t)[2:4] for t in (left,right)]
                signs=[1 if low>0 else -1 if high<0 else 0 for low,high in ends]
                if 0 in signs:
                    raise ValueError('stationary front endpoint sign unresolved')
                if signs[0]!=signs[1]:
                    root=brentq(lambda t:at(t).stationary_numerator,left,right,
                        xtol=4*np.finfo(float).eps,rtol=4*np.finfo(float).eps,maxiter=64)
                    value=at(root)
                    root_bounds=enclose(root,root)
                    rlo,rhi=root_bounds[2:4]
                    time_error=max(abs(rlo),abs(rhi))/min(abs(dl),abs(du))
                    lower=max(left,float(np.nextafter(root-time_error,-np.inf)))
                    upper=min(right,float(np.nextafter(root+time_error,np.inf)))
                    bounds=enclose(lower,upper)
                    denominator=bounds[:2]
                    if denominator[0]<=0<=denominator[1]:
                        raise ValueError('stationary front denominator uncertainty unresolved')
                    # Correlated front motion: H'=-N/B^2. Separately enclosing
                    # A/B over time destroys cancellation near a stationary front.
                    point_b=(max(root_bounds[0],denominator[0],bl),min(root_bounds[1],denominator[1],bu))
                    if point_b[0]>point_b[1] or point_b[0]<=0<=point_b[1]:
                        raise ValueError('stationary front denominator intersection unresolved')
                    ratios=[-a/b for a in root_bounds[6:] for b in point_b]
                    motion_error=max(abs(bounds[2]),abs(bounds[3]))/min(abs(bl),abs(bu))**2*max(root-lower,upper-root)
                    interval=(float(np.nextafter(min(ratios)-motion_error,-np.inf)),
                        float(np.nextafter(max(ratios)+motion_error,np.inf)))
                    if not np.all(np.isfinite(interval)):
                        raise ValueError('stationary front coordinate uncertainty overflow')
                    if maximum_axial_uncertainty is not None and interval[1]-interval[0]>maximum_axial_uncertainty:
                        raise ValueError('stationary front axial uncertainty exceeds budget')
                    roots[float(root)]=IsolatedStationaryFront(float(root),value.axial_coordinate(),
                        (lower,upper),interval,value.stationary_numerator)
                # Strict monotonicity plus certified equal endpoint signs excludes roots.
                continue
        middle=(left+right)/2
        if not left<middle<right:raise ValueError('stationary-front time resolution exhausted')
        pending.extend(((middle,right),(left,middle)))
    fractions=tuple(sorted({0.,1.,*roots}))
    endpoints=[]
    for t in (0.,1.):
        bounds=enclose(t,t)
        if bounds[0]<=0<=bounds[1]:raise ValueError('endpoint front denominator unresolved')
        ratios=[-a/b for a in bounds[6:] for b in bounds[:2]]
        interval=(float(np.nextafter(min(ratios),-np.inf)),float(np.nextafter(max(ratios),np.inf)))
        if not np.all(np.isfinite(interval)):raise ValueError('endpoint front uncertainty overflow')
        if maximum_axial_uncertainty is not None and interval[1]-interval[0]>maximum_axial_uncertainty:
            raise ValueError('endpoint front axial uncertainty exceeds budget')
        endpoints.append(IsolatedStationaryFront(t,at(t).axial_coordinate(),(t,t),interval,at(t).stationary_numerator))
    return tuple((t,at(t).axial_coordinate()) for t in fractions),count,tuple(roots[t] for t in sorted(roots)),tuple(endpoints)
