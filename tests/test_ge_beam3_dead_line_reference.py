"""Bounded independent continuum reference checks, not element qualification."""
import ast
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_dead_line_reference as ref


C=np.diag([16.,10.,12.,2.,4.,4.]).tolist()


@pytest.mark.parametrize('height',[0.,.15])
def test_zero_load_preserves_curved_stress_free_directors(height):
    t=np.linspace(-1.,1.,33)
    result=ref.solve(C,[0.,0.,0.],t.tolist(),height=height)
    np.testing.assert_allclose(result.positions,np.column_stack((t,height*(1-t*t),np.zeros(len(t)))),atol=1e-11)
    np.testing.assert_allclose(result.frames,ref.reference_frames(t,height),atol=1e-9)
    assert not np.any(result.strains) and result.strain_energy==0.


def test_exact_straight_axial_line_force_and_quadratic_displacement():
    t=np.linspace(-1.,1.,25); f=.3; s=t+1.; length=2.
    result=ref.solve(C,[f,0.,0.],t.tolist(),height=0.)
    u=f/16*(length*s-s*s/2)
    np.testing.assert_allclose(result.positions[:,0],t+u,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(result.positions[:,1:],0.,atol=1e-11)
    np.testing.assert_allclose(result.spatial_forces[:,0],f*(length-s),atol=1e-11)
    np.testing.assert_allclose(result.spatial_moments,0.,atol=1e-11)
    assert abs(result.strain_energy-f*f*length**3/(6*16))<1e-11


def test_coupled_curved_two_profile_agreement_force_balance_and_positive_energy():
    from docs.reference_cases.ge_beam3_curved_moment_fixture import reference_section
    points,weights=np.polynomial.legendre.leggauss(32)
    samples=np.r_[-1.,points,1.].tolist(); force=[.3,-.2,.1]
    a=ref.solve(reference_section().tolist(),force,samples,profile='BVP7')
    b=ref.solve(reference_section().tolist(),force,samples,profile='BVP9')
    for name in ('positions','frames','strains','resultants'):
        assert np.max(abs(getattr(a,name)-getattr(b,name)))<1e-7
    assert abs(a.strain_energy/b.strain_energy-1)<1e-7
    assert b.strain_energy>0 and b.orthogonality_error<2e-8
    length=ref.arclength_primitive(1.,.15)-ref.arclength_primitive(-1.,.15)
    np.testing.assert_allclose(b.spatial_forces[0],np.array(force)*length,atol=1e-11)
    # Independent integral of the distributed-force lever arm, compared with
    # the boundary value of moment; no native or continuum RHS call is reused.
    lever=b.positions[1:-1]-b.positions[0]
    expected=np.sum(weights[:,None]*np.sqrt(1+(.3*points)**2)[:,None]*np.cross(lever,force),axis=0)
    np.testing.assert_allclose(b.spatial_moments[0],expected,rtol=1e-8,atol=1e-9)
    assert b.mesh_nodes<=4097 and b.evaluations<=4000 and not b.production_qualified


@pytest.mark.parametrize('option',[{'max_seconds':0.},{'max_evaluations':0}])
def test_budget_failure_never_retries(option):
    with pytest.raises(RuntimeError,match='budget'): ref.solve(C,[.3,0.,0.],[-1.,1.],**option)


@pytest.mark.parametrize('mutation',['nonfinite','bool','order','section','profile','height'])
def test_invalid_authority_inputs_rejected(mutation):
    c=np.array(C); f=[.3,0.,0.]; x=[-1.,1.]; kw={}
    if mutation=='nonfinite': f[0]=float('nan')
    if mutation=='bool': f[0]=True
    if mutation=='order': x=[1.,-1.]
    if mutation=='section': c[0,0]=-1.
    if mutation=='profile': kw['profile']='UNBOUNDED'
    if mutation=='height': kw['height']=.3
    with pytest.raises((ValueError,np.linalg.LinAlgError)): ref.solve(c.tolist(),f,x,**kw)


def test_reference_has_no_producer_recovery_or_legacy_mechanics_imports():
    tree=ast.parse(Path(ref.__file__).read_text()); imports=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): imports.update(x.name.split('.')[0] for x in node.names)
        if isinstance(node,ast.ImportFrom): imports.add(node.module.split('.')[0])
    assert imports<={'dataclasses','time','numpy','scipy'}
