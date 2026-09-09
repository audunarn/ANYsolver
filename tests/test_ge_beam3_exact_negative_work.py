from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import pytest
from docs.reference_cases.ge_beam3_negative_factor_witness import negative_block,factor_witness
from docs.reference_cases.ge_beam3_negative_scaled_witness import witness
from docs.reference_cases.ge_beam3_exact_negative_work import verify


@pytest.mark.parametrize('block',([[-2]], [[0,2],[2,0]], [[3,2],[2,0]], [[2,4],[4,3]], [[0,2],[2,3]], [[-2,1],[1,-3]]))
def test_negative_block_direction(block):
    with localcontext() as c:
        c.prec=100;b=[[D(x) for x in row] for row in block];x=negative_block(b)
        assert x is not None and sum(x[i]*b[i][j]*x[j] for i in range(len(x)) for j in range(len(x)))<0


@pytest.mark.parametrize('n',(3,30))
def test_reverse_elimination_and_original_coordinate_exact_work(n):
    with localcontext() as c:
        c.prec=100
        a=[[D(0)]*n for _ in range(n)];d=[D(-2) if i==n//2 else D(3) for i in range(n)]
        for i in range(n):
            a[i][i]=d[i]+(d[i-1]/4 if i else 0)
            if i:a[i][i-1]=a[i-1][i]=d[i-1]/2
        scales=[D(10)**(3 if i%2 else -3) for i in range(n)]
        a=[[a[i][j]*scales[i]*scales[j] for j in range(n)] for i in range(n)]
        before=[row[:] for row in a];w=witness(a)
        assert a==before and w['negative']==1
        # Zero material factor isolates the supplied geometric quadratic form.
        result=verify([[0.]],[[0.]*n],[[float(x) for x in row] for row in a],tuple(range(n)),w['negative_direction'])
        assert result['exact_negative'] and int(result['total']['numerator'])<0
        assert F(result['total']['numerator'])/F(result['total']['denominator'])<0


def test_nonzero_material_and_raw_nonsymmetric_work():
    result=verify([[1.]],[[1.,0.]],[[-2.,.3],[.30000000000000004,1.]],(0,1),['1','0'])
    assert result['material']=={'numerator':'1','denominator':'1'}
    assert result['total']=={'numerator':'-1','denominator':'1'}
    assert result['raw_geometric_entries_unchanged'] and not result['inertia_algorithm_used']


@pytest.mark.parametrize('kind',('positive','zero','nan','huge','length','duplicate','fixed_map','factor','coefficient_type'))
def test_exact_checker_rejects_mutations(kind):
    left=[[1.]];right=[[1.,0.]];g=[[-2.,0.],[0.,1.]];free=(0,1);v=['1','0']
    if kind=='positive':v=['0','1']
    elif kind=='zero':v=['0','0']
    elif kind=='nan':v=['NaN','0']
    elif kind=='huge':v=['1E+10000000','0']
    elif kind=='length':v=['1']
    elif kind=='duplicate':free=(0,0)
    elif kind=='fixed_map':free=(1,);v=['1']
    elif kind=='factor':left=[[2.]]
    else:g[0][0]=-2
    with pytest.raises(ValueError):verify(left,right,g,free,v)


def test_all_positive_producer_fails_closed():
    with localcontext() as c:
        c.prec=100
        with pytest.raises(ValueError,match='no negative pivot'):factor_witness([[D(2),D(0)],[D(0),D(3)]])
