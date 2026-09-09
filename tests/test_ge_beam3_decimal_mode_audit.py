"""Validate the separate Decimal eigenvector reconstruction on known pencils."""
from decimal import Decimal as D, localcontext
import ast
from pathlib import Path
import pytest
from docs.reference_cases.ge_beam3_decimal_mode_audit import factor_modes, product, transpose


@pytest.mark.parametrize('digits',[60,90])
def test_high_contrast_modes_and_massless_trace_satisfy_original_pencil(digits):
    # Dynamic exact Schur = diag(1,4); trace u2=-u0-2u1.
    f=[[1.,0.,0.],[0.,2.,0.],[1e12,2e12,1e12]]
    b=[[1.,0.,0.],[0.,1.,0.]]
    row=factor_modes(f,b,[0,1,2],[2],digits=digits)
    with localcontext() as context:
        context.prec=digits
        values=[D(x) for x in row['eigenvalues']]
        vectors=[[D(x) for x in r] for r in row['full_modes']]
        assert max(abs(x-y) for x,y in zip(values,[D(1),D(4)]))<D('1e-30')
        ff=[[D.from_float(x) for x in r] for r in f]
        bb=[[D.from_float(x) for x in r] for r in b]
        kv=product(transpose(ff),product(ff,vectors)); mv=product(transpose(bb),product(bb,vectors))
        assert max(abs(kv[i][j]-mv[i][j]*values[j]) for i in range(3) for j in range(2))<D('1e-30')
        gram=product(transpose(vectors),mv)
        assert max(abs(gram[i][j]-D(int(i==j))) for i in range(2) for j in range(2))<D('1e-30')


def test_rotated_exact_distinct_eigenvectors_and_nontrivial_kinetic_factor():
    # Columns [3/5,4/5], [-4/5,3/5] after inverse kinetic scaling.
    f=[[3.,8.],[-8.,12.]]; b=[[5.,0.],[0.,10.]]
    row=factor_modes(f,b,[0,1],[],digits=90)
    with localcontext() as context:
        context.prec=90
        values=[D(x) for x in row['eigenvalues']]
        v=[[D(x) for x in r] for r in row['full_modes']]
        expected=[[D(3)/25,-D(4)/25],[D(4)/50,D(3)/50]]
        assert abs(values[0]-1)<D('1e-60') and abs(values[1]-4)<D('1e-60')
        for j in range(2):
            sign=D(1) if v[0][j]*expected[0][j]>0 else D(-1)
            assert max(abs(v[i][j]-sign*expected[i][j]) for i in range(2))<D('1e-60')


def test_mode_audit_imports_only_decimal_and_time():
    path=Path(__file__).parents[1]/'docs/reference_cases/ge_beam3_decimal_mode_audit.py'
    tree=ast.parse(path.read_text())
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert set(imports)=={'decimal','time'}
    assert not any(isinstance(n,ast.Import) for n in ast.walk(tree))
