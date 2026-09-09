"""Exact congruence examples and fail-closed signed-inertia arithmetic."""
from decimal import Decimal as D,localcontext
import ast
import inspect
import pytest
from docs.reference_cases import ge_beam3_decimal_inertia_audit as audit


@pytest.mark.parametrize('matrix,negative',(([[2,0],[0,3]],0),([[-2,0],[0,3]],1),
    ([[-2,0],[0,-3]],2),([[0,2],[2,0]],1),([[0,2,0],[2,0,0],[0,0,-3]],2)))
def test_signed_blocks(matrix,negative):
    with localcontext() as ctx:
        ctx.prec=80
        result=audit.inertia([[D(x) for x in row] for row in matrix])
    assert result['negative']==negative and sum(result['pivot_sizes'])==len(matrix)


@pytest.mark.parametrize('n',(7,31,210))
def test_congruence_not_just_diagonal(n):
    # Unit bidiagonal L and signed diagonal D: Sylvester inertia is exact.
    with localcontext() as ctx:
        ctx.prec=80; diagonal=[D(-1 if i%3==0 else 2) for i in range(n)]
        a=[[D(0)]*n for _ in range(n)]
        for i in range(n):
            a[i][i]=diagonal[i]+(diagonal[i-1]/16 if i else 0)
            if i:a[i][i-1]=a[i-1][i]=diagonal[i-1]/4
        assert audit.inertia(a)['negative']==sum(v<0 for v in diagonal)


@pytest.mark.parametrize('matrix',([[0,0],[0,1]],[[1,2],[0,1]],[[D('NaN'),0],[0,1]]))
def test_unresolved_and_malformed(matrix):
    with pytest.raises(ValueError):audit.inertia([[D(v) for v in row] for row in matrix])


def data():
    identity=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
    return identity,identity,[[0.,0.,0.],[0.,-2.,0.],[0.,0.,3.]],[[0.,1.,0.],[0.,0.,1.]],(0,1,2),(0,)


@pytest.mark.parametrize('digits',(80,100))
def test_original_chain_and_massless_inertia(digits):
    r=audit.audit(*data(),(-2.,0.,5.),digits=digits)
    assert [v['negative'] for v in r['rows']]==[0,1,2]
    assert r['physical_dimension']==2 and r['algebraic_dimension']==1
    assert not r['certified_intervals'] and not r['mechanics_reconstructed']


@pytest.mark.parametrize('kind',('negative-algebraic','algebraic-mass','duplicate','nan','bool','shift'))
def test_mutation(kind):
    l,r,g,b,f,a=data();shifts=(0.,)
    if kind=='negative-algebraic':g[0][0]=-2.
    elif kind=='algebraic-mass':b[0][0]=1e-30
    elif kind=='duplicate':f=(0,1,1,2)
    elif kind=='nan':g[0][0]=float('nan')
    elif kind=='bool':g[0][0]=False
    else:shifts=(True,)
    with pytest.raises(ValueError):audit.audit(l,r,g,b,f,a,shifts)


def test_arithmetic_has_no_production_import():
    tree=ast.parse(inspect.getsource(audit))
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert set(imports)=={'decimal','math','time'}
