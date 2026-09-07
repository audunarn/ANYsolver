"""Independent-algorithm reference checks, not independent authorship."""
import ast
import inspect
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_curved_moment_reference as ref
from docs.reference_cases import ge_beam3_curved_moment_fixture as fixture


def diagonal(): return np.diag([16.,10.,12.,2.,4.,4.])


def test_stress_free_parabola_and_material_directors():
    t=np.linspace(-1.,1.,25)
    value=ref.solve(fixture.reference_section(),[0.,0.,0.],t.tolist())
    np.testing.assert_allclose(value.positions,np.column_stack((t,.15*(1-t*t),0*t)),atol=1e-11,rtol=1e-11)
    np.testing.assert_allclose(value.frames,np.array([ref.reference_frame(x,.15) for x in t]),atol=1e-11,rtol=1e-11)
    np.testing.assert_array_equal(value.strains,0.)
    assert value.strain_energy==0. and not value.production_qualified


def test_straight_pure_torsion_and_bending_match_closed_form():
    t=np.linspace(-1.,1.,17); q0=ref.reference_frame(-1.,0.)
    torsion=ref.solve(diagonal(),[.6,0.,0.],t.tolist(),height=0.)
    angle=.3*(t+1.)
    expected=np.array([[[1.,0.,0.],[0.,np.cos(a),-np.sin(a)],[0.,np.sin(a),np.cos(a)]] for a in angle])@q0
    np.testing.assert_allclose(torsion.frames,expected,atol=1e-11,rtol=1e-11)
    np.testing.assert_allclose(torsion.positions,np.column_stack((t,0*t,0*t)),atol=1e-11)
    bending=ref.solve(diagonal(),[0.,0.,.8],t.tolist(),height=0.)
    expected=np.column_stack((-1+np.sin(.2*(t+1))/.2,(1-np.cos(.2*(t+1)))/.2,0*t))
    np.testing.assert_allclose(bending.positions,expected,atol=1e-11,rtol=1e-11)
    assert abs(bending.strain_energy-.16)<1e-11


def test_coupled_noncommuting_curved_reference_profiles_and_work():
    t=np.linspace(-1.,1.,41).tolist(); c=fixture.reference_section()
    fine=ref.solve(c,fixture.MOMENT,t); coarse=ref.solve(c,fixture.MOMENT,t,profile='IVP9')
    assert max(np.max(abs(fine.positions-coarse.positions)),np.max(abs(fine.frames-coarse.frames)))<1e-7
    np.testing.assert_allclose(fine.strains@c.T,fine.resultants,atol=1e-11,rtol=1e-11)
    np.testing.assert_allclose(np.einsum('nij,nj->ni',fine.frames,fine.resultants[:,3:]),
        np.tile(fixture.MOMENT,(len(t),1)),atol=1e-11,rtol=1e-11)
    assert fine.strain_energy>0 and fine.evaluations<=4000
    assert not fine.frames.flags.writeable


@pytest.mark.parametrize('change',['samples','boolean','moment','section','height','profile','budget'])
def test_invalid_or_exhausted_reference_fails_without_retry(change):
    c=diagonal(); moment=[.6,0.,0.]; samples=[-1.,0.,1.]; kw={}
    if change=='samples': samples=[-1.,.5,0.,1.]
    if change=='boolean': moment=[True,0.,0.]
    if change=='moment': moment=[float('inf'),0.,0.]
    if change=='section': c[0,0]=-1.
    if change=='height': kw['height']=True
    if change=='profile': kw['profile']='adaptive-unbounded'
    if change=='budget': kw['max_evaluations']=0
    with pytest.raises((ValueError,RuntimeError,np.linalg.LinAlgError)): ref.solve(c,moment,samples,**kw)


def test_reference_imports_no_native_or_legacy_mechanics():
    imports=[n for n in ast.walk(ast.parse(inspect.getsource(ref))) if isinstance(n,(ast.Import,ast.ImportFrom))]
    names=[n.module if isinstance(n,ast.ImportFrom) else a.name for n in imports for a in (n.names if isinstance(n,ast.Import) else [None])]
    assert set(names)=={'dataclasses','time','numpy','scipy.integrate'}


def test_fixture_section_is_coupled_spd_and_refinement_preserves_global_parabola():
    c=fixture.reference_section(); assert np.linalg.eigvalsh(c)[0]>0
    assert c[0,1]!=0. and c[2,4]!=0. and c[3,5]!=0.
    for count in (1,2,4):
        made=fixture.model(count)
        assert len(made.mesh.nodes)==2*count+1
        for element in made.mesh.elements.values():
            for xi in (-.7,.1,.8):
                x,y,z=element.operator.reference.position(xi)
                assert abs(y-.15*(1-x*x))<1e-14 and z==0.
