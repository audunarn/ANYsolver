"""Continuum reference checks; no native assembly or nonlinear solves."""
import ast
import inspect
import numpy as np
import pytest
from scipy.linalg import eigh
from docs.reference_cases import ge_beam3_curved_linear_ritz_reference as ref
from docs.reference_cases.ge_beam3_curved_moment_fixture import reference_section

MASS=np.diag([1.,1.,1.,.02,.01,.01])


def test_straight_axial_and_torsion_closed_form():
    k,m=ref.build(np.diag([16.,10.,12.,2.,4.,4.]),MASS,height=0.,degree=10,quadrature=32)
    for component,rigidity,density in ((0,16.,1.),(3,2.,.02)):
        indices=np.arange(component,len(k),6)
        roots=eigh(k[np.ix_(indices,indices)],m[np.ix_(indices,indices)],eigvals_only=True)
        expected=np.array([(np.pi*(2*i+1)/4)**2*rigidity/density for i in range(2)])
        np.testing.assert_allclose(roots[:2],expected,rtol=1e-9,atol=1e-9)


def test_free_curved_rigid_fields_and_six_nulls():
    degree=6; k,m=ref.build(reference_section(),MASS,degree=degree,quadrature=32,clamped=False)
    rigid=np.zeros((len(k),6)); rigid[:3,:3]=np.eye(3)
    # r0=(P1, (2h/3)(P0-P2),0); rigid v=omega cross r0.
    coefficients={0:np.array([0.,.1,0.]),1:np.array([1.,0.,0.]),2:np.array([0.,-.1,0.])}
    rigid[3:6,3:]=np.eye(3)
    for i,r in coefficients.items(): rigid[6*i:6*i+3,3:]=-ref.skew(r)
    assert np.max(abs(k@rigid))<1e-11
    assert np.linalg.matrix_rank(rigid)==6
    roots=eigh(k,m,eigvals_only=True)
    assert np.max(abs(roots[:6]))<1e-9 and roots[6]>1.
    np.linalg.cholesky(rigid.T@m@rigid)


def test_curved_coupled_profiles_converge_and_are_positive():
    coarse=ref.solve(reference_section(),MASS,degree=14,quadrature=64)
    fine=ref.solve(reference_section(),MASS,degree=18,quadrature=80)
    assert np.min(fine.eigenvalues)>0
    assert np.max(abs(coarse.eigenvalues/fine.eigenvalues-1))<1e-8
    assert not fine.production_qualified and not fine.modes.flags.writeable
    np.testing.assert_allclose(fine.modes.T@fine.mass@fine.modes,np.eye(6),atol=1e-11,rtol=1e-11)


@pytest.mark.parametrize('kwargs',[dict(degree=True),dict(degree=25),dict(quadrature=16),dict(height=float('nan')),dict(height=True),dict(clamped=1)])
def test_invalid_reference_scope_rejects(kwargs):
    with pytest.raises(ValueError): ref.build(reference_section(),MASS,**kwargs)


def test_no_native_mechanics_imports():
    tree=ast.parse(inspect.getsource(ref))
    modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert set(modules)=={'dataclasses','time','scipy.linalg','numpy.polynomial'}
