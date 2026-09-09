"""Independent loaded-state Hessian tests before any arch spectral wave."""
from decimal import Decimal as D,localcontext
import ast
import inspect
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_loaded_ritz_reference as ref


def exp(v):
    v=np.asarray(v); a=np.linalg.norm(v); s=ref.skew(v)
    return np.eye(3)+np.sinc(a/np.pi)*s+.5*np.sinc(a/(2*np.pi))**2*s@s


def decimal_energy(q,r,v0,kappa,c,direction,epsilon):
    """60-digit finite Exp-chart energy, not the analytic Hessian formula."""
    with localcontext() as context:
        context.prec=60
        convert=lambda a:[[D(float(x)) for x in row] for row in a]
        def multiply(a,b): return [[sum((x*y for x,y in zip(row,col)),D(0)) for col in zip(*b)] for row in a]
        def vector(a,v): return [sum((x*y for x,y in zip(row,v)),D(0)) for row in a]
        qt=list(map(list,zip(*convert(q)))); cd=convert(c)
        h=D(epsilon); vs,w,ws=[[D(float(x)) for x in chunk] for chunk in np.split(direction,3)]
        a,b,e=[h*x for x in w]
        cross=[[D(0),-e,b],[e,D(0),-a],[-b,a,D(0)]]
        ident=[[D(i==j) for j in range(3)] for i in range(3)]
        power=ident; negative_exp=[row[:] for row in ident]; right_j=[row[:] for row in ident]; factorial=D(1)
        for order in range(1,25):
            power=multiply(power,cross); factorial*=order
            for i in range(3):
                for j in range(3):
                    term=(-1)**order*power[i][j]/factorial
                    negative_exp[i][j]+=term; right_j[i][j]+=term/D(order+1)
        position=[D(float(x))+h*dx for x,dx in zip(r,vs)]
        gamma=[x-D(float(y)) for x,y in zip(vector(qt,vector(negative_exp,position)),v0)]
        curvature=[D(float(x))+y for x,y in zip(kappa,vector(qt,vector(right_j,[h*x for x in ws])))]
        strain=gamma+curvature
        return sum((x*y for x,y in zip(strain,vector(cd,strain))),D(0))/2


def test_full_second_variation_matches_high_precision_finite_potential():
    q=exp([1.2,-.7,.4]); r=np.array([1.1,.3,.1]); v0=np.array([1.,0.,0.]); curvature=np.array([.1,-.2,.3])
    factor=np.eye(6)+.03*np.arange(36).reshape(6,6); c=factor.T@factor
    gradient,hessian,material,geometric=ref.station_tangent(q,r,v0,curvature,c)
    assert np.linalg.norm(geometric)>.1
    np.testing.assert_allclose(hessian,material+geometric,atol=1e-11)
    directions=list(np.eye(9))+[(np.eye(9)[i]+np.eye(9)[j])/np.sqrt(2) for i in range(9) for j in range(i+1,9)]
    for direction in directions:
        energies=[decimal_energy(q,r,v0,curvature,c,direction,h) for h in ('-0.00001','0','0.00001')]
        with localcontext() as context:
            context.prec=60
            h=D('0.00001'); first=float((energies[2]-energies[0])/(2*h))
            second=float((energies[2]-2*energies[1]+energies[0])/(h*h))
        assert abs(first-gradient@direction)/max(1.,abs(first))<1e-7
        assert abs(second-direction@hessian@direction)/max(1.,abs(second))<1e-7


def test_station_second_variation_objectivity():
    q=exp([.5,.2,-.3]); r=np.array([1.1,.2,-.1]); c=np.diag([16.,10.,12.,2.,4.,5.]); kappa=[.1,.2,-.3]
    gradient,h,_,_=ref.station_tangent(q,r,[1.,0.,0.],kappa,c)
    common=exp([2.3,-.8,.4]); transform=np.kron(np.eye(3),common)
    other,hh,_,_=ref.station_tangent(common@q,common@r,[1.,0.,0.],kappa,c)
    np.testing.assert_allclose(other,transform@gradient,atol=1e-11,rtol=1e-11)
    np.testing.assert_allclose(hh,transform@h@transform.T,atol=1e-11,rtol=1e-11)


def test_tensile_and_compressive_geometric_work_has_correct_sign():
    c=np.diag([1000.,400.,400.,2.,4.,4.])
    for strain in (-.01,.01):
        _,_,_,g=ref.station_tangent(np.eye(3),[1+strain,0.,0.],[1.,0.,0.],[0.,0.,0.],c)
        direction=np.array([0.,1+strain,0.,0.,0.,1.,0.,0.,0.])
        assert abs(direction@g@direction-1000*strain*(1+strain))<1e-11


def test_unloaded_station_has_no_geometric_term():
    q=np.eye(3); c=np.diag([16.,10.,12.,2.,4.,4.])
    gradient,h,material,g=ref.station_tangent(q,[1.,0.,0.],[1.,0.,0.],[0.,0.,0.],c)
    np.testing.assert_array_equal(g,0.); np.testing.assert_array_equal(gradient,0.)
    np.testing.assert_array_equal(h,material)


def test_piecewise_basis_preserves_crown_continuity_and_end_clamps():
    for degree in (12,16):
        assert np.max(abs(ref.basis(-1.,degree)[0]))==0
        assert np.max(abs(ref.basis(1.,degree)[0]))==0
        value=ref.basis(0.,degree)[0]; assert value[0]==1 and np.max(abs(value[1:]))==0
        for t in (-.8,-.2,.2,.8):
            h=1e-6; difference=(ref.basis(t+h,degree)[0]-ref.basis(t-h,degree)[0])/(2*h)
            np.testing.assert_allclose(difference,ref.basis(t,degree)[1],atol=1e-7,rtol=1e-7)


def test_reference_imports_no_native_operators():
    tree=ast.parse(inspect.getsource(ref)); modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert set(modules)=={'dataclasses','time','scipy.linalg','numpy.polynomial'}


@pytest.mark.parametrize('kind',['improper','nonfinite','section','shape'])
def test_malformed_station_rejects(kind):
    q=np.eye(3); c=np.eye(6); r=[1.,0.,0.]
    if kind=='improper': q[0,0]=-1
    if kind=='nonfinite': r[0]=float('nan')
    if kind=='section': c[0,1]=1
    if kind=='shape': r=[1.]
    with pytest.raises(ValueError): ref.station_tangent(q,r,[1.,0.,0.],[0.,0.,0.],c)
