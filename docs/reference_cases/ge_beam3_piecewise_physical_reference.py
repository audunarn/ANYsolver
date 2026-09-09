"""H1 piecewise-polynomial continuum reference; failed sine protocol unchanged."""
from time import monotonic
import numpy as np
from scipy.linalg import cholesky
from numpy.polynomial.legendre import legvander,legder,legval
from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
from docs.reference_cases.ge_beam3_spatial_continuum import matrix
from docs.reference_cases.ge_beam3_spatial_physical_reference import density,rates
from docs.reference_cases.ge_beam3_spatial_second_variation import blocks
from docs.reference_cases.ge_beam3_spatial_physical_pencil import spectrum

PROFILES=((128,4),(128,8),(128,12),(64,12))


def local_basis(segment,t,jac,order):
    if (type(segment) is not int or not 0<=segment<4 or type(order) is not int or not 1<=order<=16
            or not np.isfinite(t) or not -1<=t<=1 or not np.isfinite(jac) or jac<=0):
        raise ValueError('bounded local polynomial trial coordinates')
    width=3+4*order;v=np.zeros(width);d=np.zeros(width)
    # Four intervals of length1/2; dt/ds0=4/jac. Three shared interface hats.
    if segment>0:v[segment-1]=(1-t)/2;d[segment-1]=-2/jac
    if segment<3:v[segment]=(1+t)/2;d[segment]=2/jac
    p=legvander(t,order-1)[0]
    for k in range(order):
        derivative=0. if k==0 else legval(t,legder(np.eye(order)[k]))
        slot=3+segment*order+k
        v[slot]=(1-t*t)*p[k]
        d[slot]=4/jac*((1-t*t)*derivative-2*t*p[k])
    return np.kron(np.eye(6),v[None,:]),np.kron(np.eye(6),d[None,:])


def basis(x,jac,order):
    if not np.isfinite(x) or not -1<=x<=1:raise ValueError('reference domain')
    segment=min(int((x+1)*2),3);t=4*(x-(-1+.5*segment))-1
    return local_basis(segment,t,jac,order)


def indices(order,maximum=12):
    if type(order) is not int or order not in (4,8,12) or maximum!=12:raise ValueError('registered nested polynomial profile')
    scalar=[0,1,2]+[3+segment*maximum+k for segment in range(4) for k in range(order)]
    return np.array([component*(3+4*maximum)+i for component in range(6) for i in scalar])


def matrices(value,quadrature,check):
    if quadrature not in (64,128):raise ValueError('unchanged integration orders')
    poly=unpack(value['polynomial']);c=np.diag([1000.,400.,400.,.02,.01,.02]);inverse=1/np.diag(c)
    h=np.zeros((306,306));mass=np.zeros_like(h);points,weights=np.polynomial.legendre.leggauss(quadrature)
    for segment in range(4):
        for t,w in zip(points,weights):
            check();u=(t+1)/2;x=-1.+.5*segment+.5*u;jac=float(np.sqrt(1+.04*x*x))
            y=poly(u)[13*segment:13*(segment+1)];r=matrix(y[3:7]);n=y[7:10];m=y[10:13]
            strain=inverse*np.r_[r.T@n,r.T@m];velocity=r@(np.r_[1.,0.,0.]+strain[:3])
            q,dq=local_basis(segment,t,jac,12);d,b,f=blocks(r,c,velocity,n,m);measure=w*.25*jac
            h+=measure*(dq.T@d@dq+dq.T@b@q+q.T@b.T@dq+q.T@f@q)
            mass+=measure*(q.T@density(r)@q)
    for a in (h,mass):
        if np.max(abs(a-a.T))/(1+np.max(abs(a)))>1e-11:raise ValueError('polynomial pencil symmetry')
    return h,mass


def solve(value,progress=lambda row:None,save=lambda row:None):
    start=monotonic();assembled={};rows=[]
    def check():
        if monotonic()-start>120:raise ValueError('piecewise reference120second bound')
    for quadrature,order in PROFILES:
        check()
        if quadrature not in assembled:assembled[quadrature]=matrices(value,quadrature,check)
        h,mass=assembled[quadrature];slots=indices(order);a=h[np.ix_(slots,slots)];b=mass[np.ix_(slots,slots)]
        b=(b+b.T)/2;root=cholesky(b,lower=False)
        error=float(np.max(abs(root.T@root-b))/(1+np.max(abs(b))))
        if error>1e-11:raise ValueError('polynomial kinetic-factor identity')
        size=len(slots)
        packet=dict(left=[[0.]],right=[[0.]*size],geometric=a.tolist(),kinetic=root.tolist(),
            free_dofs=list(range(size)),algebraic_dofs=[])
        result=spectrum(packet,80,6,progress)
        row=dict(bubbles_per_segment=order,quadrature=quadrature,result=result,kinetic_factor_error=error,
            raw_quadrature_hessian=a.tolist(),raw_quadrature_mass=b.tolist(),physical_mass_not_l2=True,
            continuum_trial_factor_rounding_disclosed=True)
        save(row);rows.append(row);progress(dict(stage='piecewise-modal-profile-complete',order=order,quadrature=quadrature))
    check()
    return dict(profiles=rows,basis='FOUR_SEGMENT_H1_HATS_LEGENDRE_BUBBLES_V1',
        production_qualified=False,full_continuum_inertia_proved=False)


def validate(value):
    rows=value['profiles']
    if [(r['quadrature'],r['bubbles_per_segment']) for r in rows]!=list(PROFILES):raise ValueError('complete polynomial profiles')
    spectra=[rates(r['result']['eigenvalues']) for r in rows]
    if any(np.any(np.sign(a)!=np.sign(spectra[2])) for a in spectra):raise ValueError('polynomial mode sign disagreement')
    refinement=float(np.max(abs(spectra[1]/spectra[2]-1)));quadrature=float(np.max(abs(spectra[3]/spectra[2]-1)))
    if refinement>.005 or quadrature>1e-6:raise ValueError('polynomial reference refinement/quadrature unresolved')
    return refinement,quadrature
