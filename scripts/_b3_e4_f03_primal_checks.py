"""Bounded numerical checks for the independent classical primal Ritz model.

One canonical solve is paired with a distinct integration assembly. Saved
arrays suffice to recompute every numerical and recovery diagnostic without
reassembly or an equilibrium solve. This is not a physical convergence gate.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.polynomial import legendre

import _b3_e4_f03_primal_ritz as ritz
import _b3_e4_f03_primal_functional as functional


STATIONS=np.arange(9,dtype=float)/8
BANDS=np.array(((0.,.25),(.25,.5),(.5,.75),(.75,1.),
                (0.,1/32),(1/32,1/16),(15/16,31/32),(31/32,1.)))
LIMITS={
    'operator_skew_relative':1e-12,
    'integration_energy_relative':1e-11,
    'integration_root_relative':1e-11,
    'integration_load_relative':1e-11,
    'station_pose_relative':1e-11,
    'root_rank_violation':0.,
    'root_slope_rank_violation':0.,
    'primal_positive_violation':0.,
    'scaled_kkt_condition_2':1e10,
    'condition_times_backward_error':1e-8,
    'stationarity_scaled':1e-10,
    'root_compatibility_scaled':1e-10,
    'energy_identity_scaled':1e-10,
    'perturbation_alpha_violation':0.,
    'perturbation_bound_violation':0.,
    'edge_route_difference_scaled':1e-8,
    'edge_lift_shift_scaled':1e-8,
    'global_balance_scaled':1e-8,
    'virtual_work_scaled':1e-10,
    'density_recovery_scaled':1e-10,
    'band_quadrature_scaled':1e-10,
    'functional_norm_resolution_violation':0.,
    'functional_norm_nonnegative_violation':0.,
    'functional_norm_nonfinite_violation':0.,
    'load_quadrature_scaled':1e-11,
    'scaling_D_parity_relative':1e-12,
    'saved_action_parity_scaled':1e-11,
    'root_partition_scaled':1e-11,
    'tip_partition_scaled':1e-11,
}


def expected_shapes(n: int) -> dict[str,tuple[int,...]]:
    """Exact all-float64 saved evidence inventory for a bounded degree."""
    if type(n) is not int or not 2<=n<=24:
        raise ValueError('outside bounded primal evidence degree')
    d=2*(n*n-1)
    return {
        'K_shell':(d,d),'K_beam':(d,d),'f':(d,),'C_root':(3,d),'A_tip':(3,d),
        'K_shell_plus':(d,d),'K_beam_plus':(d,d),'f_plus':(d,),
        'C_root_plus':(3,d),'A_tip_plus':(3,d),
        'station_A':(9,3,d),'station_A1':(9,3,d),'station_A2':(9,3,d),
        'station_A_plus':(9,3,d),'station_A1_plus':(9,3,d),
        'station_A2_plus':(9,3,d),
        'projection_A':(n+1,3,d),
        'D':(d,),'z':(d+3,),'H_z':(d+3,),
        'q':(d,),'eta':(3,),
        'b_coefficients':(n+1,3),'density_coefficients':(n+1,3),
        'cosine':(3,),'atoms':(2,3),
        'lift_shell':(6,d),'lift_beam':(6,d),'lift_load':(6,),
        'lift_root':(6,3),'lift_tip':(6,3),
        'lift_pose48':(6,48,3),'lift_pose64':(6,64,3),
        'edge_route1':(2,3),'edge_route2':(2,3),
        'band_analytic':(8,3),'band48':(8,3),'band64':(8,3),
        'line_band_analytic':(8,3),
        'norms_squared':(2,),
        'norms_squared_valid':(2,),
        'norm_channels_squared':(2,3),
        'virtual_work_defects':(3,n+3),
    }


def _validate(arrays: dict,n: int) -> None:
    shapes=expected_shapes(n)
    if not isinstance(arrays,dict) or set(arrays)!=set(shapes):
        raise ValueError('incorrect primal saved array inventory')
    values=[]
    for name,shape in shapes.items():
        value=arrays[name]
        if (not isinstance(value,np.ndarray) or value.dtype!=np.float64 or
                value.shape!=shape or
                (name not in ('norms_squared','norm_channels_squared') and
                 not np.all(np.isfinite(value))) or
                (name in ('norms_squared','norm_channels_squared') and
                 np.any(np.isinf(value)))):
            raise ValueError(f'invalid primal saved array {name}')
        values.append(value)
    valid=arrays['norms_squared_valid']
    if not np.all((valid==0)|(valid==1)):
        raise ValueError('invalid primal saved norm validity flags')
    for order in range(2):
        scalar=arrays['norms_squared'][order]
        channels=arrays['norm_channels_squared'][order]
        if (valid[order]==1 and
                (not np.isfinite(scalar) or not np.all(np.isfinite(channels)))):
            raise ValueError('finite primal norm marked unavailable')
        if valid[order]==0 and not np.isnan(scalar):
            raise ValueError('unavailable primal norm lacks NaN marker')
    if any(np.shares_memory(a,b) for i,a in enumerate(values) for b in values[i+1:]):
        raise ValueError('aliased primal saved arrays')


def _project_b(n: int,q: np.ndarray,
               projection: np.ndarray) -> np.ndarray:
    roots,weights=legendre.leggauss(n+1)
    samples=projection@q
    coefficients=(legendre.legvander(roots,n).T*weights)@samples
    coefficients*=((2*np.arange(n+1)+1)/2)[:,None]
    return coefficients


def _derived_density(n: int,bcoef: np.ndarray
                     ) -> np.ndarray:
    coefficients=np.zeros((n+1,3))
    def derivative(channel: int, degree: int) -> np.ndarray:
        return (2**degree)*legendre.legder(bcoef[:,channel],m=degree)
    def add(channel: int, value: np.ndarray, scale: float) -> None:
        coefficients[:len(value),channel]+=scale*value
    add(0,derivative(0,2),ritz.E*ritz.AREA)
    add(1,derivative(1,2),ritz.G*ritz.SHEAR_AREA)
    add(1,derivative(2,1),-ritz.G*ritz.SHEAR_AREA)
    coefficients[0,1]+=ritz.F0
    add(2,derivative(2,2),ritz.E*ritz.INERTIA)
    add(2,derivative(1,1),ritz.G*ritz.SHEAR_AREA)
    add(2,bcoef[:,2],-ritz.G*ritz.SHEAR_AREA)
    return coefficients


def _section_from_b(bcoef: np.ndarray,s: float) -> np.ndarray:
    t=2*s-1
    b=legendre.legval(t,bcoef)
    db=np.stack([2*legendre.legval(t,legendre.legder(bcoef[:,i]))
                 for i in range(3)])
    return np.array((ritz.E*ritz.AREA*db[0],
                     ritz.G*ritz.SHEAR_AREA*(db[1]-b[2]),
                     ritz.E*ritz.INERTIA*db[2]))


def _lift_actions(n: int, polynomial_order: int,load_order: int
                  ) -> tuple[np.ndarray,...]:
    nd=2*(n*n-1);m=n*n-1
    roots,weights=legendre.leggauss(polynomial_order)
    xx=np.broadcast_to(.5+roots[:,None],(polynomial_order,polynomial_order))
    yy=np.broadcast_to(roots[None,:]/2,(polynomial_order,polynomial_order))
    _,dx,dy,_=ritz.basis(n,xx,yy)
    b=np.zeros((polynomial_order,polynomial_order,3,nd))
    b[:,:,0,:m]=dx
    b[:,:,1,m:]=dy
    b[:,:,2,:m]=dy
    b[:,:,2,m:]=dx
    shell_weights=(.5*ritz.THICKNESS*weights[:,None]*weights[None,:])
    beam_roots,beam_weights=legendre.leggauss(polynomial_order)
    load_roots,load_weights=legendre.leggauss(load_order)
    shell_rows=np.zeros((6,nd)); beam_rows=np.zeros((6,nd))
    load_rows=np.zeros(6); root=np.zeros((6,3)); tip=np.zeros((6,3))
    poses={order:np.zeros((6,order,3)) for order in (48,64)}
    for side in (0,1):
        for channel in range(3):
            row=3*side+channel
            _,zx,zy=ritz._lift(side,channel,xx,yy)
            eps=np.stack((zx[...,0],zy[...,1],zy[...,0]+zx[...,1]),axis=-1)
            shell_rows[row]=np.einsum('ij,ijk,kl,ijlm->m',
                shell_weights,eps,ritz.PLANE,b,optimize=True)
            for s,w in zip((beam_roots+1)/2,beam_weights/2):
                a,a1,_=ritz.pose_operators(n,float(s),
                    quadrature_order=polynomial_order)
                strain=np.stack((a1[0],a1[2],a1[1]-a[2]))
                z,dz=ritz._lift_pose(side,channel,float(s))
                zstrain=np.array((dz[0],dz[2],dz[1]-z[2]))
                beam_rows[row]+=w*zstrain@ritz.SECTION@strain
            for s,w in zip((load_roots+1)/2,load_weights/2):
                z,_=ritz._lift_pose(side,channel,float(s))
                load_rows[row]+=w*ritz.F0*(1+.25*math.cos(2*math.pi*s))*z[1]
            root[row]=ritz._lift_pose(side,channel,0.)[0]
            tip[row]=ritz._lift_pose(side,channel,1.)[0]
            for order in poses:
                xr,_=legendre.leggauss(order)
                poses[order][row]=[ritz._lift_pose(side,channel,float((x+1)/2))[0]
                                   for x in xr]
    return shell_rows,beam_rows,load_rows,root,tip,poses[48],poses[64]


def _virtual_work(n: int,bcoef: np.ndarray,func: functional.Functional,
                  eta: np.ndarray) -> np.ndarray:
    roots,weights=legendre.leggauss(48)
    stations=(roots+1)/2
    b=legendre.legval(roots,bcoef).T
    db=np.stack([2*legendre.legval(roots,legendre.legder(bcoef[:,i]))
                 for i in range(3)],axis=-1)
    nqm=np.stack((ritz.E*ritz.AREA*db[:,0],
                  ritz.G*ritz.SHEAR_AREA*(db[:,1]-b[:,2]),
                  ritz.E*ritz.INERTIA*db[:,2]),axis=-1)
    density=func.density(stations)
    defects=np.zeros((3,n+3))
    for channel in range(3):
        amplitude=ritz.U0 if channel!=2 else ritz.U0/ritz.YAW_LENGTH
        for degree in range(n+3):
            polynomial=np.zeros(degree+1);polynomial[-1]=1.
            w=amplitude*legendre.legval(roots,polynomial)
            dw=2*amplitude*legendre.legval(roots,legendre.legder(polynomial))
            w0=amplitude*(-1.)**degree; w1=amplitude
            left=np.sum(weights/2*density[:,channel]*w)
            left+=func.atoms[0,channel]*w0+func.atoms[1,channel]*w1
            right=eta[channel]*w0
            if channel==0:
                right+=np.sum(weights/2*nqm[:,0]*dw)
            elif channel==1:
                right+=np.sum(weights/2*(nqm[:,1]*dw-
                    ritz.F0*(1+.25*np.cos(2*np.pi*stations))*w))
            else:
                right+=np.sum(weights/2*(nqm[:,2]*dw-nqm[:,1]*w))
            defects[channel,degree]=left+right
    return defects


def _route2(func: functional.Functional, lift_pose: np.ndarray,
            lift_root: np.ndarray,lift_tip: np.ndarray) -> np.ndarray:
    roots,weights=legendre.leggauss(lift_pose.shape[1])
    density=func.density((roots+1)/2)
    work=np.einsum('i,ic,kic->k',weights/2,density,lift_pose)
    return work+lift_root@func.atoms[0]+lift_tip@func.atoms[1]


def _signed_norm(func: functional.Functional, order: int
                 ) -> tuple[float,np.ndarray,float]:
    """Preserve signed channels, marking only unmeasurable values unavailable."""
    try:
        channels=functional.green_inner(func,func,order=order)
    except functional.NonfiniteGreenResponse:
        return float('nan'),np.full(3,np.nan),0.
    channels=np.asarray(channels,dtype=np.float64)
    if channels.shape!=(3,):
        raise ValueError('invalid Green channel shape')
    if not np.all(np.isfinite(channels)):
        return float('nan'),np.where(np.isfinite(channels),channels,np.nan),0.
    with np.errstate(over='ignore'):
        total=float(np.sum(channels))
    if not np.isfinite(total):
        return float('nan'),channels,0.
    return total,channels,1.


def evaluate_case(n: int) -> tuple[dict,dict[str,np.ndarray]]:
    """Two frozen assemblies, exactly one canonical equilibrium solve."""
    expected_shapes(n)
    primary=ritz.assemble(n,polynomial_order=n+1,load_order=48)
    cross=ritz.assemble(n,polynomial_order=n+3,load_order=64)
    _,state=ritz.solve(primary)
    q,eta=state['q'],state['eta']
    h,rhs,d,r=ritz._scaled_system(primary)
    z=np.r_[q/d,eta/(ritz.E0*np.diag(r))]
    arrays={
        'K_shell':primary.shell_stiffness.copy(),
        'K_beam':primary.beam_stiffness.copy(),
        'f':primary.load.copy(),'C_root':primary.root_constraint.copy(),
        'A_tip':primary.tip_pose.copy(),
        'K_shell_plus':cross.shell_stiffness.copy(),
        'K_beam_plus':cross.beam_stiffness.copy(),
        'f_plus':cross.load.copy(),'C_root_plus':cross.root_constraint.copy(),
        'A_tip_plus':cross.tip_pose.copy(),
        'D':d.copy(),'z':z.copy(),'H_z':h@z,
        'q':q.copy(),'eta':eta.copy(),
    }
    for name,order in (('',n+1),('_plus',n+3)):
        poses=[ritz.pose_operators(n,float(s),quadrature_order=order)
               for s in STATIONS]
        for k,key in enumerate(('station_A','station_A1','station_A2')):
            arrays[key+name]=np.stack([p[k] for p in poses])
    gauss,_=legendre.leggauss(n+1)
    arrays['projection_A']=np.stack([ritz.pose_operators(n,float((x+1)/2),
        quadrature_order=n+1)[0] for x in gauss])
    bcoef=_project_b(n,q,arrays['projection_A'])
    density_samples=ritz.recover_interface(n,q,eta,(gauss+1)/2)['density']
    cosine=np.array((0.,.25*ritz.F0,0.))
    recovered=ritz.recover_interface(n,q,eta,np.array((0.,1.)))
    func=functional.from_gauss_density(n,density_samples,cosine,
        np.stack((recovered['root_atom'],recovered['tip_atom'])))
    arrays.update({'b_coefficients':bcoef.copy(),
                   'density_coefficients':func.coefficients.copy(),
                   'cosine':cosine.copy(),'atoms':func.atoms.copy()})
    shell_lift,beam_lift,load_lift,root_lift,tip_lift,pose48,pose64=(
        _lift_actions(n,n+1,48))
    arrays.update({'lift_shell':shell_lift,'lift_beam':beam_lift,
                   'lift_load':load_lift,'lift_root':root_lift,
                   'lift_tip':tip_lift,'lift_pose48':pose48,
                   'lift_pose64':pose64})
    edge1=(shell_lift@q+beam_lift@q-load_lift+root_lift@eta).reshape(2,3)
    edge2=(shell_lift@q-_route2(func,pose48,root_lift,tip_lift)).reshape(2,3)
    arrays['edge_route1']=edge1;arrays['edge_route2']=edge2
    line=functional.Functional(func.coefficients,func.cosine,np.zeros((2,3)))
    arrays['band_analytic']=np.stack([functional.band_wrench_analytic(func,*band)
                                      for band in BANDS])
    arrays['band48']=np.stack([functional.band_wrench(func,*band,order=48)
                               for band in BANDS])
    arrays['band64']=np.stack([functional.band_wrench(func,*band,order=64)
                               for band in BANDS])
    arrays['line_band_analytic']=np.stack([
        functional.band_wrench_analytic(line,*band) for band in BANDS])
    norms=(_signed_norm(func,48),_signed_norm(func,64))
    arrays['norms_squared']=np.array([item[0] for item in norms])
    arrays['norm_channels_squared']=np.stack([item[1] for item in norms])
    arrays['norms_squared_valid']=np.array([item[2] for item in norms])
    arrays['virtual_work_defects']=_virtual_work(n,bcoef,func,eta)
    _validate(arrays,n)
    return verify_saved(arrays,n),arrays


def _relative_difference(a: np.ndarray,b: np.ndarray) -> float:
    norm=float(np.linalg.norm(a))
    difference=float(np.linalg.norm(a-b))
    return difference/norm if norm>0 else difference


def verify_saved(arrays: dict,n: int) -> dict:
    """Audit only supplied bounded arrays, with no operator assembly/solve."""
    _validate(arrays,n)
    ks,kb,f,c=(arrays[name] for name in ('K_shell','K_beam','f','C_root'))
    ks2,kb2,f2,c2=(arrays[name] for name in
                   ('K_shell_plus','K_beam_plus','f_plus','C_root_plus'))
    q,eta,d,z=(arrays[name] for name in ('q','eta','D','z'))
    k=ks+kb;k2=ks2+kb2
    diagonal=np.diag(k)
    if np.any(diagonal<=0) or np.any(d<=0):
        raise ValueError('nonpositive saved Ritz primal diagonal or scaling D')
    required_d=np.sqrt(ritz.E0/diagonal)
    if not np.all(np.isfinite(required_d)) or np.any(required_d<=0):
        raise ValueError('invalid saved Ritz stiffness-derived scaling D')
    d_parity=float(np.max(np.abs(d/required_d-1.)))
    r=np.diag((1/ritz.U0,1/ritz.U0,ritz.YAW_LENGTH/ritz.U0))
    kbar=d[:,None]*k*d[None,:]/ritz.E0
    cbar=r@c@np.diag(d)
    fbar=d*f/ritz.E0
    h=np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]])
    rhs=np.r_[fbar,np.zeros(3)]
    kbar2=d[:,None]*k2*d[None,:]/ritz.E0
    cbar2=r@c2@np.diag(d)
    fbar2=d*f2/ritz.E0
    h2=np.block([[kbar2,cbar2.T],[cbar2,np.zeros((3,3))]])
    rhs2=np.r_[fbar2,np.zeros(3)]
    sv=np.linalg.svd(h,compute_uv=False)
    root_sv=np.linalg.svd(cbar,compute_uv=False)
    slope=(ritz.L0/ritz.U0)*arrays['station_A1'][0,1]*d
    slope_sv=np.linalg.svd(np.vstack((cbar,slope)),compute_uv=False)
    positive=0.
    skew=max(float(np.linalg.norm(m-m.T)/
                   (np.linalg.norm(m) if np.linalg.norm(m)>0 else 1.))
             for block in (ks,kb,k,ks2,kb2,k2)
             for m in ((d[:,None]*block*d[None,:])/ritz.E0,))
    if skew>LIMITS['operator_skew_relative']:
        positive=1.
    else:
        try:
            np.linalg.cholesky(kbar)
        except np.linalg.LinAlgError:
            positive=1.
    integration=max(_relative_difference(d[:,None]*a*d[None,:]/ritz.E0,
                                          d[:,None]*b*d[None,:]/ritz.E0)
                    for a,b in ((ks,ks2),(kb,kb2),(k,k2)))
    root_difference=float(np.linalg.norm(cbar-cbar2)/max(1.,np.linalg.norm(cbar)))
    load_difference=float(np.max(np.abs(fbar-fbar2))/
                          max(1.,float(np.max(np.abs(fbar)))))
    station_error=0.
    for key in ('station_A','station_A1','station_A2'):
        power=('station_A','station_A1','station_A2').index(key)
        for a,b in zip(arrays[key],arrays[key+'_plus']):
            p=(ritz.L0**power)*r@a@np.diag(d)
            pp=(ritz.L0**power)*r@b@np.diag(d)
            station_error=max(station_error,float(np.linalg.norm(p-pp)/
                                                 max(1.,np.linalg.norm(p))))
    cond=float(sv[0]/sv[-1])
    residual=h@z-rhs
    backward=float(np.linalg.norm(residual)/
                   (sv[0]*np.linalg.norm(z)+np.linalg.norm(rhs)))
    sigma=float(sv[-1]);hdiff=float(np.linalg.norm(h2-h))
    bdiff=float(np.linalg.norm(rhs2-rhs))
    alpha=hdiff/sigma
    delta=(hdiff*np.linalg.norm(z)+bdiff)/(sigma*np.linalg.norm(z))
    amplification=float(delta/(1-alpha)) if alpha<1 else None
    u_shell=float(.5*q@ks@q);u_beam=float(.5*q@kb@q)
    work=float(f@q)
    bcoef=arrays['b_coefficients']
    projection_error=float(np.max(np.abs(
        _project_b(n,q,arrays['projection_A'])-bcoef))/ritz.U0)
    derivative_error=0.
    for degree,key in ((0,'station_A'),(1,'station_A1'),
                       (2,'station_A2')):
        polynomials=np.stack([legendre.legval(2*STATIONS-1,
            legendre.legder(bcoef[:,channel],m=degree))*2**degree
            for channel in range(3)],axis=-1)
        observed=arrays[key]@q
        scaled_reference=(ritz.L0**degree)*(polynomials@r.T)
        scaled_observed=(ritz.L0**degree)*(observed@r.T)
        derivative_error=max(derivative_error,float(np.max(np.abs(
            scaled_observed-scaled_reference))/max(1.,float(np.max(
            np.abs(scaled_observed))),float(np.max(np.abs(scaled_reference))))))
    derived=_derived_density(n,bcoef)
    cosine=np.array((0.,.25*ritz.F0,0.))
    root_resultant=_section_from_b(bcoef,0.)
    tip_resultant=_section_from_b(bcoef,1.)
    atom_derived=np.stack((root_resultant-eta,-tip_resultant))
    func=functional.Functional(arrays['density_coefficients'],
                                arrays['cosine'],arrays['atoms'])
    density_error=max(float(np.max(np.abs(derived-func.coefficients))),
                      float(np.max(np.abs(atom_derived-func.atoms))),
                      float(np.max(np.abs(cosine-func.cosine))))/ritz.F0
    route1=(arrays['lift_shell']@q+arrays['lift_beam']@q-
            arrays['lift_load']+arrays['lift_root']@eta).reshape(2,3)
    route2=(arrays['lift_shell']@q-
            _route2(func,arrays['lift_pose48'],arrays['lift_root'],
                    arrays['lift_tip'])).reshape(2,3)
    route2_64=(arrays['lift_shell']@q-
               _route2(func,arrays['lift_pose64'],arrays['lift_root'],
                       arrays['lift_tip'])).reshape(2,3)
    edge_error=max(np.max(np.abs(route1-route2)),
                   np.max(np.abs(route1-route2_64)),
                   np.max(np.abs(route1-arrays['edge_route1'])),
                   np.max(np.abs(route2-arrays['edge_route2'])))/ritz.F0
    balance=route1.sum(axis=0)-eta+np.array((0.,ritz.F0,.5*ritz.F0))
    shift=float(abs((k@q+c.T@eta-f)[0])/ritz.F0)
    virtual=_virtual_work(n,bcoef,func,eta)
    virtual_error=max(float(np.max(np.abs(virtual))),
                      float(np.max(np.abs(virtual-arrays['virtual_work_defects']))))/ritz.E0
    analytic=np.stack([functional.band_wrench_analytic(func,*band)
                       for band in BANDS])
    band48=np.stack([functional.band_wrench(func,*band,order=48)
                     for band in BANDS])
    band64=np.stack([functional.band_wrench(func,*band,order=64)
                     for band in BANDS])
    line=functional.Functional(func.coefficients,func.cosine,np.zeros((2,3)))
    line_analytic=np.stack([functional.band_wrench_analytic(line,*band)
                            for band in BANDS])
    band_error=max(np.max(np.abs(analytic-band48)),
                   np.max(np.abs(analytic-band64)),
                   np.max(np.abs(analytic-arrays['band_analytic'])),
                   np.max(np.abs(band48-arrays['band48'])),
                   np.max(np.abs(band64-arrays['band64'])),
                   np.max(np.abs(line_analytic-arrays['line_band_analytic'])))/ritz.F0
    q48,channels48,valid48=_signed_norm(func,48)
    q64,channels64,valid64=_signed_norm(func,64)
    valid=(valid48,valid64)
    if not np.array_equal(arrays['norms_squared_valid'],valid):
        raise ValueError('saved Green norm validity differs from recomputation')
    if not np.array_equal(arrays['norms_squared'],(q48,q64),equal_nan=True):
        raise ValueError('saved Green norm totals differ from recomputation')
    if not np.array_equal(arrays['norm_channels_squared'],
                          np.stack((channels48,channels64)),equal_nan=True):
        raise ValueError('saved Green norm channels differ from recomputation')
    norm_nonfinite=not all(valid)
    norm_negative=bool(np.any(channels48<0) or np.any(channels64<0) or
                       q48<0 or q64<0)
    norm_resolution=(abs(q48-q64)/max(abs(q48),abs(q64),1000.**2)
                     if not norm_nonfinite else None)
    action_error=max(projection_error,derivative_error,
                     float(np.max(np.abs(q-d*z[:-3])/ritz.U0)),
                     float(np.max(np.abs(eta-ritz.E0*r@z[-3:]))/ritz.F0),
                     float(np.max(np.abs(h@z-arrays['H_z']))),
                     float(np.max(np.abs(c-arrays['station_A'][0]))*
                           np.max(d)/ritz.U0),
                     float(np.max(np.abs(arrays['A_tip']-arrays['station_A'][-1]))*
                           np.max(d)/ritz.U0),
                     float(np.max(np.abs(c2-arrays['station_A_plus'][0]))*
                           np.max(d)/ritz.U0),
                     float(np.max(np.abs(arrays['A_tip_plus']-
                           arrays['station_A_plus'][-1]))*
                           np.max(d)/ritz.U0),
                     float(np.max(np.abs(arrays['A_tip']@q-
                            arrays['station_A'][-1]@q))/ritz.U0))
    checks={
        'operator_skew_relative':skew,
        'integration_energy_relative':integration,
        'integration_root_relative':root_difference,
        'integration_load_relative':load_difference,
        'station_pose_relative':station_error,
        'root_rank_violation':float(root_sv[-1]/root_sv[0]<1e-10),
        'root_slope_rank_violation':float(slope_sv[-1]/slope_sv[0]<1e-10),
        'primal_positive_violation':positive,
        'scaled_kkt_condition_2':cond,
        'condition_times_backward_error':cond*backward,
        'stationarity_scaled':float(np.max(np.abs(residual[:-3]))/
                                    max(1.,float(np.max(np.abs(fbar))))),
        'root_compatibility_scaled':float(np.max(np.abs(r@c@q))),
        'energy_identity_scaled':float(abs(2*(u_shell+u_beam)-work)/
                                       max(ritz.E0,2*abs(u_shell+u_beam),abs(work))),
        'perturbation_alpha_violation':float(alpha>=1),
        'perturbation_bound_violation':float(
            amplification is None or amplification>1e-6),
        'edge_route_difference_scaled':float(edge_error),
        'edge_lift_shift_scaled':shift,
        'global_balance_scaled':float(np.max(np.abs(balance))/ritz.F0),
        'virtual_work_scaled':virtual_error,
        'density_recovery_scaled':density_error,
        'band_quadrature_scaled':float(band_error),
        'functional_norm_resolution_violation':float(
            norm_resolution is None or norm_resolution>1e-10),
        'functional_norm_nonnegative_violation':float(norm_negative),
        'functional_norm_nonfinite_violation':float(norm_nonfinite),
        'load_quadrature_scaled':load_difference,
        'scaling_D_parity_relative':d_parity,
        'saved_action_parity_scaled':action_error,
        'root_partition_scaled':float(np.max(np.abs(
            -root_resultant+func.atoms[0]+eta))/ritz.F0),
        'tip_partition_scaled':float(np.max(np.abs(
            tip_resultant+func.atoms[1]))/ritz.F0),
    }
    observables={
        'root_reaction':(-eta).tolist(),
        'left_edge_wrench':route1[0].tolist(),
        'right_edge_wrench':route1[1].tolist(),
        'tip_pose_scaled':(np.diag((1.,1.,ritz.YAW_LENGTH))@
                           arrays['A_tip']@q).tolist(),
        'shell_energy_j':u_shell,'beam_energy_j':u_beam,
        'total_energy_j':u_shell+u_beam,'external_work_j':work,
        'root_elastic':(-root_resultant).tolist(),
        'root_section_resultant':root_resultant.tolist(),
        'root_atom':func.atoms[0].tolist(),
        'tip_elastic':tip_resultant.tolist(),
        'tip_atom':func.atoms[1].tolist(),
        'line_band_wrenches':line_analytic.tolist(),
        'total_band_wrenches':analytic.tolist(),
        'full_functional_norm_N':(None if norm_negative or norm_nonfinite else
                                  float(math.sqrt(q64))),
    }
    details={'kkt_min_singular_value':sigma,
             'root_singular_values':root_sv.tolist(),
             'root_slope_stacked_singular_values':slope_sv.tolist(),
             'perturbation_alpha':alpha,'perturbation_delta':delta,
             'perturbation_bound':amplification,
             'norm_channels48_squared':[float(v) if np.isfinite(v) else None
                                        for v in channels48],
             'norm_channels64_squared':[float(v) if np.isfinite(v) else None
                                        for v in channels64],
             'functional_norm_resolution':norm_resolution,
             'perturbation_residual_plus':float(np.linalg.norm(h2@z-rhs2)),
             'solve_backward_error':backward,
             'norm_squared_48':q48 if valid48 else None,
             'norm_squared_64':q64 if valid64 else None,
             'action_error_scaled':action_error,
             'load_difference_inf_scaled':load_difference}
    if set(checks)!=set(LIMITS):
        raise ValueError('incomplete bounded primal checks')
    return {'checks':checks,'observables':observables,'details':details}
