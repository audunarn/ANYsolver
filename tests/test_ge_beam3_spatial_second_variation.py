import ast
from pathlib import Path
import numpy as np
import pytest
from scipy.linalg import expm,expm_frechet
from docs.reference_cases import ge_beam3_spatial_second_variation as form


def data(seed):
    rng=np.random.default_rng(seed);r=expm(form.skew(rng.normal(size=3)))
    a=rng.normal(size=(6,6));c=a.T@a+np.eye(6)
    strain=rng.normal(size=6)*.1;stress=c@strain
    v=r@(np.array([1.,0.,0.])+strain[:3]);n=r@stress[:3];m=r@stress[3:]
    return rng,r,c,strain,v,n,m


def potential(t,r,c,e,v,q,dq):
    # Matrix exponential/Frechet derivative reconstruct the perturbed strains
    # directly; no analytic Hessian, virtual strain or Jacobi blocks are used.
    f,fs=expm_frechet(t*form.skew(q[3:]),t*form.skew(dq[3:]))
    spin=f.T@fs;axl=np.array([spin[2,1],spin[0,2],spin[1,0]])
    changed=np.r_[r.T@f.T@(v+t*dq[:3])-np.array([1.,0.,0.]),e[3:]+r.T@axl]
    return .5*changed@c@changed


@pytest.mark.parametrize('seed',range(8))
def test_variational_density_coupled_and_noncommuting(seed):
    rng,r,c,e,v,n,m=data(seed);q=rng.normal(size=6);dq=rng.normal(size=6)
    d,b,f=form.blocks(r,c,v,n,m)
    expected=form.direct_density(r,c,v,n,m,q,dq)
    actual=dq@d@dq+2*dq@b@q+q@f@q
    assert abs(actual-expected)/(1+abs(expected))<1e-11
    approximations=[]
    for h in (.001,.0005):
        approximations.append((potential(h,r,c,e,v,q,dq)-2*potential(0.,r,c,e,v,q,dq)
                               +potential(-h,r,c,e,v,q,dq))/h**2)
    richardson=(4*approximations[1]-approximations[0])/3
    assert abs(richardson-expected)/(1+abs(expected))<1e-7


@pytest.mark.parametrize('seed',range(8))
def test_hamiltonian_work_and_objectivity(seed):
    rng,r,c,e,v,n,m=data(seed);q=rng.normal(size=6);dq=rng.normal(size=6)
    d,b,f=form.blocks(r,c,v,n,m);h=form.generator(r,c,v,n,m)
    j=np.block([[np.zeros((6,6)),np.eye(6)],[-np.eye(6),np.zeros((6,6))]])
    assert np.max(abs(h.T@j+j@h))/(1+np.max(abs(h)))<1e-11
    p=d@dq+b@q
    np.testing.assert_allclose((h@np.r_[q,p])[:6],dq,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose((h@np.r_[q,p])[6:],b.T@dq+f@q,rtol=1e-11,atol=1e-11)
    rotation=expm(form.skew(rng.normal(size=3)));s=np.kron(np.eye(2),rotation)
    rotated=form.blocks(rotation@r,c,rotation@v,rotation@n,rotation@m)
    for old,new in zip((d,b,f),rotated):np.testing.assert_allclose(new,s@old@s.T,rtol=1e-11,atol=1e-11)


def test_canonical_momentum_not_raw_spatial_moment():
    rng,r,c,e,v,n,m=data(17);q=rng.normal(size=6);dq=rng.normal(size=6)
    d,b,f=form.blocks(r,c,v,n,m)
    strain=np.r_[r.T@(dq[:3]-np.cross(q[3:],v)),r.T@dq[3:]]
    ds=c@strain;dn=np.cross(q[3:],n)+r@ds[:3];dm=np.cross(q[3:],m)+r@ds[3:]
    expected=np.r_[dn,dm+.5*np.cross(m,q[3:])]
    np.testing.assert_allclose(d@dq+b@q,expected,rtol=1e-11,atol=1e-11)
    assert np.linalg.norm(expected[3:]-dm)>1e-3


def test_reference_linear_limit():
    c=np.diag([1000.,400.,400.,.02,.01,.02]);v=np.array([1.,0.,0.]);zero=np.zeros(3)
    h=form.generator(np.eye(3),c,v,zero,zero)
    a=np.zeros((6,6));a[:3,3:]=-form.skew(v)
    expected=np.block([[a,np.diag(1/np.diag(c))],[np.zeros((6,6)),-a.T]])
    np.testing.assert_allclose(h,expected,rtol=1e-11,atol=1e-11)


@pytest.mark.parametrize('kind',('frame','orientation','section','positive','vector','nan'))
def test_input_mutations(kind):
    _,r,c,e,v,n,m=data(1)
    if kind=='frame':r[0,0]+=.1
    elif kind=='orientation':r[:,0]*=-1
    elif kind=='section':c[0,1]+=.1
    elif kind=='positive':c=-c
    elif kind=='vector':v=v[:2]
    else:n[0]=float('nan')
    with pytest.raises((ValueError,np.linalg.LinAlgError)):form.blocks(r,c,v,n,m)


def test_full_spatial_clamped_basis_and_derivative():
    for end in (-1.,1.):assert not form.variation_basis(end,1.,24)[0].any()
    x=.17;jac=np.sqrt(1+.04*x*x);q,dq=form.variation_basis(x,jac,8)
    h=1e-6;numerical=(form.variation_basis(x+h,jac,8)[0]-form.variation_basis(x-h,jac,8)[0])/(2*h*jac)
    np.testing.assert_allclose(dq,numerical,rtol=1e-7,atol=1e-7)
    assert q.shape==(6,48) and np.linalg.matrix_rank(q)==6
    with pytest.raises(ValueError):form.variation_basis(x,1.,33)


def test_no_beam_or_dynamic_imports():
    tree=ast.parse(Path(form.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):assert all(n.name=='numpy' for n in node.names)
        if isinstance(node,ast.ImportFrom):raise AssertionError('only numpy import allowed')
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ('eval','exec','__import__')


def test_saved_endpoint_authority_and_strict_json(tmp_path):
    from docs.reference_cases import ge_beam3_spatial_ritz_worker as worker
    for sign in ('plus','minus'):
        v=worker.source(sign)
        assert abs(v['reference']['amplitude'])==.0065
    for raw in (b'{"a":1,"a":2}\n',b'{"a":NaN}\n',b'{ "a":1}\n'):
        with pytest.raises(ValueError):worker.strict(raw)
    (tmp_path/'manifest.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError):worker.source('plus',tmp_path)
    with pytest.raises(ValueError):worker.source('other')
