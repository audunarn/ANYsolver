"""Independent classical finite-pad primal Ritz diagnostic, not native product.

The supported shell polynomial space is paired with its exact rectangular
area-pose map. Beam energy uses the continuous mapped pose, with only its
three physical root values constrained. No FE beam interpolation, mortar,
clipped host integration, point tie, or slope/root-tip clamp is used.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numpy.polynomial import legendre


E=210e9
NU=.3
THICKNESS=.07
AREA=.01
SHEAR_AREA=.008
INERTIA=8.333333333333333e-6
G=E/(2*(1+NU))
SECTION=np.diag((E*AREA,E*INERTIA,G*SHEAR_AREA))
PLANE=E/(1-NU**2)*np.array(((1.,NU,0.),(NU,1.,0.),
                            (0.,0.,(1-NU)/2)))
OFFSETS=((-.2,-.23),(.2,-.23),(.2,.23),(-.2,.23))
HALFWIDTH=.05
J=.2**2+.23**2+2*HALFWIDTH**2/3
YAW_LENGTH=.46
F0=1e6
L0=1.
U0=F0/(E*THICKNESS)
E0=F0*U0


@dataclass(frozen=True)
class QuadratureSettings:
    polynomial_order: int
    polynomial_degree_bound: int
    load_order: int
    comparison_load_order: int
    load_difference_inf_scaled: float
    pad_rule: str = 'independent_tensor_Gauss_on_four_physical_squares'


@dataclass(frozen=True)
class RitzOperators:
    n: int
    halfwidth: float
    shell_stiffness: np.ndarray
    beam_stiffness: np.ndarray
    load: np.ndarray
    root_constraint: np.ndarray
    tip_pose: np.ndarray
    quadrature: QuadratureSettings

    @property
    def dof_count(self) -> int:
        return 2*(self.n*self.n-1)


def _n(n: int) -> int:
    if type(n) is not int or not 2<=n<=24:
        raise ValueError('outside bounded polynomial Ritz degrees')
    return n


def _pad(halfwidth: float) -> None:
    if type(halfwidth) not in (float,int) or halfwidth!=HALFWIDTH:
        raise ValueError('the primal diagnostic has one fixed physical pad')


def _legendre(n: int, z: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    p=legendre.legvander(z,n)
    eye=np.eye(n+1)
    dp=np.stack([legendre.legval(z,legendre.legder(eye[i]))
                 for i in range(n+1)],axis=-1)
    ddp=np.stack([legendre.legval(z,legendre.legder(eye[i],m=2))
                  for i in range(n+1)],axis=-1)
    return p,dp,ddp


def basis(n: int, x: float | np.ndarray, y: float | np.ndarray
          ) -> tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    """Scalar phi, x/y gradients, xx derivative; i major, j minor.

    X=x-.5 and Y=2y. phi_ij=(1-X²) P_i(X) P_j(Y),
    i=0..n-2, j=0..n, exact support at x=-.5 and 1.5.
    At the algebra-only n=2 edge, mapped v'(0) lies in the root-pose
    row span; n>=3 restores an independent root derivative. This is a
    finite-space artifact, not an imposed fourth root condition.
    """
    _n(n)
    x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float))
    if (not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or
            np.any(x<-.5-1e-12) or np.any(x>1.5+1e-12) or
            np.any(y<-.5-1e-12) or np.any(y>.5+1e-12)):
        raise ValueError('Ritz basis outside physical panel')
    X=x-.5; Y=2*y
    px,dpx,ddpx=_legendre(n-2,X)
    py,dpy,_=_legendre(n,Y)
    fx=(1-X*X)[...,None]*px
    dfx=-2*X[...,None]*px+(1-X*X)[...,None]*dpx
    ddfx=-2*px-4*X[...,None]*dpx+(1-X*X)[...,None]*ddpx
    shape=x.shape+(n*n-1,)
    tensor=lambda a,b:np.einsum('...i,...j->...ij',a,b).reshape(shape)
    return (tensor(fx,py),tensor(dfx,py),
            tensor(fx,2*dpy),tensor(ddfx,py))


def _rule(order: int) -> tuple[np.ndarray,np.ndarray]:
    if type(order) is not int or not 3<=order<=64:
        raise ValueError('unsupported frozen Ritz quadrature order')
    return legendre.leggauss(order)


def pose_operators(n: int, s: float, halfwidth: float = HALFWIDTH, *,
                   quadrature_order: int | None = None
                   ) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    """Physical A(s), A'(s), A''(s) from independent fixed-pad moments."""
    _n(n); _pad(halfwidth)
    if not math.isfinite(s) or not 0<=s<=1:
        raise ValueError('station outside physical beam')
    order=n+1 if quadrature_order is None else quadrature_order
    if order not in (n+1,n+3):
        raise ValueError('pad rule must be exact n+1 or frozen n+3')
    roots,weights=_rule(order)
    m=n*n-1
    matrices=[np.zeros((3,2*m)) for _ in range(3)]
    for dx,dy in OFFSETS:
        xi=dx+halfwidth*roots[:,None]
        eta=dy+halfwidth*roots[None,:]
        xx=s+np.broadcast_to(xi,(order,order))
        yy=np.broadcast_to(eta,(order,order))
        offsets_x=np.broadcast_to(xi,(order,order))
        offsets_y=np.broadcast_to(eta,(order,order))
        fields=basis(n,xx,yy)
        w=weights[:,None]*weights[None,:]/16
        for matrix,phi in zip(matrices,(fields[0],fields[1],fields[3])):
            matrix[0,:m]+=np.einsum('ab,abk->k',w,phi)
            matrix[1,m:]+=np.einsum('ab,abk->k',w,phi)
            matrix[2,:m]-=np.einsum('ab,ab,abk->k',w,offsets_y,phi)/J
            matrix[2,m:]+=np.einsum('ab,ab,abk->k',w,offsets_x,phi)/J
    return tuple(matrices)


def _shell_stiffness(n: int, order: int) -> np.ndarray:
    roots,weights=_rule(order)
    xx=np.broadcast_to(.5+roots[:,None],(order,order))
    yy=np.broadcast_to(roots[None,:]/2,(order,order))
    _,dx,dy,_=basis(n,xx,yy)
    m=n*n-1; nd=2*m
    count=order*order
    b=np.zeros((count,3,nd))
    b[:,0,:m]=dx.reshape(count,m)
    b[:,1,m:]=dy.reshape(count,m)
    b[:,2,:m]=dy.reshape(count,m)
    b[:,2,m:]=dx.reshape(count,m)
    w=(weights[:,None]*weights[None,:]*.5*THICKNESS).reshape(count)
    # Dense operations belong only to the bounded independent Ritz oracle.
    weighted=np.einsum('q,ab,qbj->qaj',w,PLANE,b,optimize=True)
    return np.einsum('qai,qaj->ij',b,weighted,optimize=True)


def _beam_stiffness(n: int, order: int) -> np.ndarray:
    roots,weights=_rule(order)
    nd=2*(n*n-1)
    b=np.empty((order,3,nd))
    for k,s in enumerate((roots+1)/2):
        a,a1,_=pose_operators(n,float(s),quadrature_order=order)
        b[k,0]=a1[0]
        b[k,1]=a1[2]
        b[k,2]=a1[1]-a[2]
    weighted=np.einsum('q,ab,qbj->qaj',weights/2,SECTION,b,optimize=True)
    return np.einsum('qai,qaj->ij',b,weighted,optimize=True)


def _load(n: int, order: int, pad_order: int) -> np.ndarray:
    roots,weights=_rule(order)
    f=np.zeros(2*(n*n-1))
    for s,w in zip((roots+1)/2,weights/2):
        a,_,_=pose_operators(n,float(s),quadrature_order=pad_order)
        f+=w*F0*(1+.25*math.cos(2*math.pi*s))*a[1]
    return f


def assemble(n: int, halfwidth: float = HALFWIDTH, *,
             polynomial_order: int | None = None,
             load_order: int = 48) -> RitzOperators:
    """Separate physical shell/beam matrices and consistent smooth load.

    Max tensor shell/beam strain-product degree is 2n per coordinate;
    n+1 Gauss points integrate it exactly. Pad yaw integrands have degree
    at most n+1 per coordinate. n+3 is an explicit overintegration check.
    Cosine loading is non-polynomial; frozen 48/64 results are both retained
    as a discrepancy, never used for outcome-selected quadrature retry.
    """
    _n(n); _pad(halfwidth)
    order=n+1 if polynomial_order is None else polynomial_order
    if order not in (n+1,n+3) or load_order not in (48,64):
        raise ValueError('outside frozen primal quadrature settings')
    ks=_shell_stiffness(n,order)
    kb=_beam_stiffness(n,order)
    f=_load(n,load_order,order)
    comparison_order=64 if load_order==48 else 48
    load_difference=float(np.max(np.abs(f-_load(n,comparison_order,order)))/F0)
    root=pose_operators(n,0.,quadrature_order=order)[0]
    tip=pose_operators(n,1.,quadrature_order=order)[0]
    for item in (ks,kb,f,root,tip):
        if not np.all(np.isfinite(item)):
            raise ValueError('nonfinite polynomial Ritz operator')
        item.flags.writeable=False
    settings=QuadratureSettings(order,2*n,load_order,comparison_order,
                                load_difference)
    return RitzOperators(n,halfwidth,ks,kb,f,root,tip,settings)


def _scaled_system(operators: RitzOperators
                   ) -> tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    k=operators.shell_stiffness+operators.beam_stiffness
    diagonal=np.diag(k)
    if np.any(diagonal<=0) or not np.all(np.isfinite(diagonal)):
        raise ValueError('nonpositive Ritz energy diagonal')
    d=U0/np.sqrt(U0*U0*diagonal/E0)
    root_scale=np.diag((1/U0,1/U0,YAW_LENGTH/U0))
    kbar=(d[:,None]*k*d[None,:])/E0
    cbar=root_scale@operators.root_constraint@np.diag(d)
    fbar=d*operators.load/E0
    matrix=np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]])
    rhs=np.r_[fbar,np.zeros(3)]
    return matrix,rhs,d,root_scale


def root_rank_diagnostics(operators: RitzOperators) -> dict:
    """Dimensionless three-root and independent root-slope singular values."""
    matrix,_,d,_=_scaled_system(operators)
    cbar=matrix[-3:,:-3]
    derivative=pose_operators(operators.n,0.,
        quadrature_order=operators.quadrature.polynomial_order)[1][1]
    slope_row=(L0/U0)*derivative*d
    roots=np.linalg.svd(cbar,compute_uv=False)
    stacked=np.linalg.svd(np.vstack((cbar,slope_row)),compute_uv=False)
    return {'root_singular_values':roots.tolist(),
            'root_slope_stacked_singular_values':stacked.tolist(),
            'root_slope_independence_ratio':float(stacked[-1]/stacked[0])}


def solve(operators: RitzOperators) -> tuple[dict,dict[str,np.ndarray]]:
    """Bounded diagnostic KKT solve; no production or registered authority."""
    matrix,rhs,d,root_scale=_scaled_system(operators)
    primal=matrix[:-3,:-3]
    for name,block in (('shell',operators.shell_stiffness),
                       ('beam',operators.beam_stiffness),
                       ('total',operators.shell_stiffness+operators.beam_stiffness)):
        scaled=(d[:,None]*block*d[None,:])/E0
        norm=float(np.linalg.norm(scaled))
        if (not np.all(np.isfinite(scaled)) or
                np.linalg.norm(scaled-scaled.T)>
                1e-12*(norm if norm>0 else 1.)):
            raise ValueError(f'asymmetric scaled Ritz {name} stiffness')
    np.linalg.cholesky(primal)
    primal_spectrum=np.linalg.eigvalsh(primal)
    singulars=np.linalg.svd(matrix,compute_uv=False)
    root_singulars=np.linalg.svd(matrix[-3:,:-3],compute_uv=False)
    root_rank=root_rank_diagnostics(operators)
    if root_singulars[-1]<=1e-10*root_singulars[0]:
        raise ValueError('Ritz root map lacks three independent conditions')
    solution=np.linalg.solve(matrix,rhs)
    q=d*solution[:-3]
    eta=E0*root_scale@solution[-3:]
    k=operators.shell_stiffness+operators.beam_stiffness
    residual=k@q+operators.root_constraint.T@eta-operators.load
    energy=float(.5*q@k@q)
    external=float(operators.load@q)
    metrics={
        'n':operators.n,
        'shell_energy_j':float(.5*q@operators.shell_stiffness@q),
        'beam_energy_j':float(.5*q@operators.beam_stiffness@q),
        'external_work_j':external,
        'energy_identity_scaled':abs(2*energy-external)/E0,
        'augmented_energy_identity_scaled':abs(2*energy-external+
                                              eta@operators.root_constraint@q)/E0,
        'equilibrium_scaled':float(np.max(np.abs(d*residual/E0))),
        'root_compatibility_scaled':float(np.max(np.abs(root_scale@
                                                  operators.root_constraint@q))),
        'root_rank_singular_values':root_singulars.tolist(),
        'root_slope_stacked_singular_values':root_rank[
            'root_slope_stacked_singular_values'],
        'root_slope_independence_ratio':root_rank[
            'root_slope_independence_ratio'],
        'scaled_primal_min_eigenvalue':float(primal_spectrum[0]),
        'scaled_primal_max_eigenvalue':float(primal_spectrum[-1]),
        'scaled_kkt_min_singular_value':float(singulars[-1]),
        'scaled_kkt_condition_2':float(singulars[0]/singulars[-1]),
        'tip_pose_physical':(operators.tip_pose@q).tolist(),
        'tip_pose_scaled_m':(np.diag((1.,1.,YAW_LENGTH))@
                             operators.tip_pose@q).tolist(),
        'root_reaction_physical':(-eta).tolist(),
        'quadrature':operators.quadrature.__dict__.copy(),
    }
    if not np.all(np.isfinite(solution)) or not np.all(np.isfinite(list(
            (energy,external,metrics['equilibrium_scaled'],
             metrics['scaled_kkt_condition_2'])))):
        raise ValueError('nonfinite polynomial Ritz solution')
    return metrics,{'q':q.copy(),'eta':eta.copy()}


def recover_interface(n: int, q: np.ndarray, eta: np.ndarray,
                      stations: np.ndarray) -> dict[str,np.ndarray]:
    """Physical beam-side density, endpoint atoms and support reaction.

    eta is the unscaled physical three-component root multiplier. The
    density is (N',Q'+load,M'+Q). Tip and root atoms are distinct measures.
    """
    _n(n)
    nd=2*(n*n-1)
    q=np.asarray(q); eta=np.asarray(eta); stations=np.asarray(stations)
    if (q.shape!=(nd,) or eta.shape!=(3,) or stations.ndim!=1 or
            not np.all(np.isfinite(q)) or not np.all(np.isfinite(eta)) or
            not np.all(np.isfinite(stations)) or np.any(stations<0) or
            np.any(stations>1)):
        raise ValueError('invalid Ritz physical recovery state')
    def section(s: float) -> tuple[np.ndarray,np.ndarray]:
        a,a1,a2=pose_operators(n,s)
        b=a@q; db=a1@q; ddb=a2@q
        nqm=np.array((E*AREA*db[0],G*SHEAR_AREA*(db[1]-b[2]),
                      E*INERTIA*db[2]))
        density=np.array((E*AREA*ddb[0],
                          G*SHEAR_AREA*(ddb[1]-db[2])+
                          F0*(1+.25*math.cos(2*math.pi*s)),
                          E*INERTIA*ddb[2]+nqm[1]))
        return nqm,density
    root,_=section(0.); tip,_=section(1.)
    density=np.stack([section(float(s))[1] for s in stations])
    return {'density':density,'root_atom':root-eta,
            'tip_atom':-tip,'root_reaction':-eta.copy(),
            'root_elastic':-root,'root_section_resultant':root.copy(),
            'tip_elastic':tip}


def _lift(side: int, channel: int, x: np.ndarray,y: np.ndarray
          ) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    """Left/right edge interpolation of origin rigid virtual motions."""
    x,y=np.broadcast_arrays(x,y)
    if side not in (0,1) or channel not in (0,1,2):
        raise ValueError('invalid edge virtual lift')
    weight=(1.5-x)/2 if side==0 else (x+.5)/2
    wx=-.5 if side==0 else .5
    r=np.zeros(x.shape+(2,))
    rx=np.zeros_like(r); ry=np.zeros_like(r)
    if channel==0:
        r[...,0]=1.
    elif channel==1:
        r[...,1]=1.
    else:
        r[...,0]=-y; r[...,1]=x
        rx[...,1]=1.; ry[...,0]=-1.
    return (weight[...,None]*r,
            wx*r+weight[...,None]*rx,
            weight[...,None]*ry)


def _lift_pose(side: int, channel: int, s: float, order: int = 3
               ) -> tuple[np.ndarray,np.ndarray]:
    roots,weights=_rule(order)
    value=np.zeros(3); derivative=np.zeros(3)
    for dx,dy in OFFSETS:
        xi=dx+HALFWIDTH*roots[:,None]
        eta=dy+HALFWIDTH*roots[None,:]
        x=s+np.broadcast_to(xi,(order,order))
        y=np.broadcast_to(eta,(order,order))
        xi=np.broadcast_to(xi,(order,order))
        z,zx,_=_lift(side,channel,x,y)
        w=weights[:,None]*weights[None,:]/16
        for result,field in ((value,z),(derivative,zx)):
            result[0]+=np.einsum('ab,ab->',w,field[...,0])
            result[1]+=np.einsum('ab,ab->',w,field[...,1])
            result[2]+=np.einsum('ab,ab,ab->',w,xi,field[...,1])/J
            result[2]-=np.einsum('ab,ab,ab->',w,y,field[...,0])/J
    return value,derivative


def recover_support_wrenches(operators: RitzOperators, q: np.ndarray,
                             eta: np.ndarray) -> np.ndarray:
    """Physical left/right panel edge reactions in origin (Fx,Fy,Mz).

    For each edge, use the explicit nonadmissible lift weight times the
    three origin rigid modes (1,0), (0,1), (-y,x). Restore its work as
    as(q,z)+ab(Aq,Az)-lb(Az)+eta·Az(0). This is the panel reaction under
    the declared c=b-Au sign, not a total-balance residual allocation.
    """
    if (not isinstance(operators,RitzOperators) or
            q.shape!=(operators.dof_count,) or eta.shape!=(3,) or
            not np.all(np.isfinite(q)) or not np.all(np.isfinite(eta))):
        raise ValueError('invalid Ritz edge recovery state')
    n=operators.n; order=operators.quadrature.polynomial_order
    roots,weights=_rule(order)
    xx=np.broadcast_to(.5+roots[:,None],(order,order))
    yy=np.broadcast_to(roots[None,:]/2,(order,order))
    _,dx,dy,_=basis(n,xx,yy)
    m=n*n-1
    ux=q[:m]; uy=q[m:]
    eps=np.stack((dx@ux,dy@uy,dy@ux+dx@uy),axis=-1)
    shell_weights=.5*THICKNESS*weights[:,None]*weights[None,:]
    shell_stress=np.einsum('ab,...b->...a',PLANE,eps)
    beam_roots,beam_weights=_rule(order)
    load_roots,load_weights=_rule(operators.quadrature.load_order)
    reactions=np.zeros((2,3))
    for side in (0,1):
        for channel in range(3):
            _,zx,zy=_lift(side,channel,xx,yy)
            eps_z=np.stack((zx[...,0],zy[...,1],
                            zy[...,0]+zx[...,1]),axis=-1)
            shell_work=float(np.einsum('ab,abc,abc->',shell_weights,
                                       shell_stress,eps_z))
            beam_work=0.
            for s,w in zip((beam_roots+1)/2,beam_weights/2):
                a,a1,_=pose_operators(n,float(s),quadrature_order=order)
                b=a@q; db=a1@q
                z,dz=_lift_pose(side,channel,float(s))
                strain_b=np.array((db[0],db[2],db[1]-b[2]))
                strain_z=np.array((dz[0],dz[2],dz[1]-z[2]))
                beam_work+=float(w*strain_b@SECTION@strain_z)
            load_work=0.
            for s,w in zip((load_roots+1)/2,load_weights/2):
                z,_=_lift_pose(side,channel,float(s))
                load_work+=float(w*F0*(1+.25*math.cos(2*math.pi*s))*z[1])
            root_z,_=_lift_pose(side,channel,0.)
            reactions[side,channel]=shell_work+beam_work-load_work+eta@root_z
    if not np.all(np.isfinite(reactions)):
        raise ValueError('nonfinite edge reaction recovery')
    return reactions
