"""Small analytic arithmetic cases, including negative physical eigenvalues."""
import ast
import inspect
import pytest
from docs.reference_cases import ge_beam3_decimal_signed_chain_audit as audit


def inputs():
    identity=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
    return identity,identity,[[0.,0.,0.],[0.,-2.,0.],[0.,0.,3.]],[[0.,1.,0.],[0.,0.,1.]],(0,1,2),(0,)


@pytest.mark.parametrize('digits',(80,100))
def test_negative_physical_mode_retained(digits):
    result=audit.roots(*inputs(),digits=digits)
    assert list(map(float,result['eigenvalues']))==[-1.,4.]
    assert result['trace_positive'] and result['mass_positive']
    assert not result['certified_intervals'] and not result['mechanics_reconstructed']


@pytest.mark.parametrize('mutation',('negative-trace','trace-mass','nonfinite','boolean','duplicate-dof','non-symmetric','digits'))
def test_reject(mutation):
    left,right,g,b,free,a=inputs();digits=80
    if mutation=='negative-trace':g[0][0]=-2.
    elif mutation=='trace-mass':b[0][0]=1e-30
    elif mutation=='nonfinite':g[0][0]=float('inf')
    elif mutation=='boolean':g[0][0]=False
    elif mutation=='duplicate-dof':free=(0,1,1,2)
    elif mutation=='non-symmetric':g[0][1]=1e-30
    else:digits=81
    with pytest.raises(ValueError):audit.roots(left,right,g,b,free,a,digits=digits)


def test_no_production_or_numerical_imports():
    for module in (audit, __import__('docs.reference_cases.ge_beam3_decimal_factor_audit',fromlist=['*'])):
        tree=ast.parse(inspect.getsource(module))
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        assert set(imports)<={'decimal','math','time','docs.reference_cases.ge_beam3_decimal_factor_audit'}
