"""Current-rest continuum mass and modal trial matrices, no native mechanics."""
from time import monotonic
import numpy as np
from scipy.linalg import cholesky
from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
from docs.reference_cases.ge_beam3_spatial_continuum import matrix
from docs.reference_cases import ge_beam3_spatial_second_variation as form
from docs.reference_cases.ge_beam3_spatial_physical_pencil import spectrum


def density(r):
    r=np.asarray(r,dtype=float)
    if r.shape!=(3,3) or not np.isfinite(r).all() or np.max(abs(r.T@r-np.eye(3)))>1e-11 or np.linalg.det(r)<0:
        raise ValueError('proper physical inertia frame')
    result=np.zeros((6,6));result[:3,:3]=np.eye(3)
    result[3:,3:]=r@np.diag([3e-5,1e-5,2e-5])@r.T
    return result


def matrices(value,quadrature,order,check):
    if quadrature not in (64,128) or order!=32:raise ValueError('frozen modal integration/basis')
    poly=unpack(value['polynomial']);c=np.diag([1000.,400.,400.,.02,.01,.02]);inverse=1/np.diag(c)
    h=np.zeros((192,192));mass=np.zeros_like(h)
    points,weights=np.polynomial.legendre.leggauss(quadrature)
    for segment in range(4):
        for point,weight in zip(points,weights):
            check();u=(point+1)/2;x=-1.+.5*segment+.5*u;jac=float(np.sqrt(1+.04*x*x))
            y=poly(u)[13*segment:13*(segment+1)];r=matrix(y[3:7]);n=y[7:10];m=y[10:13]
            strain=inverse*np.r_[r.T@n,r.T@m];v=r@(np.r_[1.,0.,0.]+strain[:3])
            q,dq=form.variation_basis(x,jac,order);d,b,f=form.blocks(r,c,v,n,m)
            measure=weight*.25*jac
            h+=measure*(dq.T@d@dq+dq.T@b@q+q.T@b.T@dq+q.T@f@q)
            mass+=measure*(q.T@density(r)@q)
    for a in (h,mass):
        if np.max(abs(a-a.T))/(1+np.max(abs(a)))>1e-11:raise ValueError('integrated physical pencil symmetry')
    return h,mass


def solve(value,progress=lambda row:None,save=lambda row:None):
    started=monotonic()
    def check():
        if monotonic()-started>120:raise ValueError('continuum physical-spectrum 120-second bound')
    assembled={};rows=[]
    for quadrature,order in ((128,16),(128,24),(128,32),(64,32)):
        check()
        if quadrature not in assembled:assembled[quadrature]=matrices(value,quadrature,32,check)
        h,mass=assembled[quadrature];indices=np.concatenate([np.arange(i*32,i*32+order) for i in range(6)])
        a=h[np.ix_(indices,indices)];b=mass[np.ix_(indices,indices)]
        b=(b+b.T)/2;root=cholesky(b,lower=False)
        # Dense continuum trial Hessian represented as a geometric factor block;
        # this is a generic algebra wrapper, not a production factor capture.
        # The Cholesky factor's rounded entries are disclosed and independently
        # checked against the original quadrature mass before use.
        error=float(np.max(abs(root.T@root-b))/(1+np.max(abs(b))))
        if error>1e-11:raise ValueError('continuum kinetic factor agreement')
        packet=dict(left=[[0.]],right=[[0.]*(6*order)],geometric=a.tolist(),kinetic=root.tolist(),
            free_dofs=list(range(6*order)),algebraic_dofs=[])
        result=spectrum(packet,80,6,progress)
        row=dict(modes_per_component=order,quadrature=quadrature,result=result,kinetic_factor_error=error,
            raw_quadrature_hessian=a.tolist(),raw_quadrature_mass=b.tolist(),physical_mass_not_l2=True,
            continuum_trial_factor_rounding_disclosed=True)
        save(row);rows.append(row)
        progress(dict(stage='continuum-physical-profile-complete',order=order,quadrature=quadrature))
    return dict(profiles=rows,production_qualified=False,full_continuum_inertia_proved=False)


def rates(values):
    a=np.asarray(values,dtype=float)
    if a.shape!=(6,) or not np.isfinite(a).all() or np.any(a==0):raise ValueError('six resolved signed modal values')
    return np.sign(a)*np.sqrt(abs(a))


def validate_reference(result):
    rows=result['profiles']
    if [(r['quadrature'],r['modes_per_component']) for r in rows]!=[(128,16),(128,24),(128,32),(64,32)]:
        raise ValueError('complete frozen reference modal profiles')
    spectra=[rates(r['result']['eigenvalues']) for r in rows]
    if any(np.any(np.sign(a)!=np.sign(spectra[2])) for a in spectra):raise ValueError('reference mode sign disagreement')
    refinement=float(np.max(abs(spectra[1]/spectra[2]-1)))
    quadrature=float(np.max(abs(spectra[3]/spectra[2]-1)))
    if refinement>.005 or quadrature>1e-6:raise ValueError('reference refinement/quadrature not resolved')
    return refinement,quadrature
