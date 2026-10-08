"""Manufactured equations only: no native/continuum specimen RHS."""
from decimal import Decimal as D, localcontext
import json
import numpy as np
import pytest
from scipy import sparse
from scripts import r8_bl5_body_port_twofold as candidate


@pytest.mark.parametrize('tiny',(1e-20,))
def test_quiet_physical_row_requires_retained_low_parts(tmp_path,tiny):
    # u are physical coordinates; p are retained conjugates. No retained loads.
    k=sparse.csr_matrix([[0.,0.,1.,1.],[0.,0.,1.,-1.],
                         [1.,1.,-1.,0.],[1.,-1.,0.,-1.]])
    load=np.array([1.,tiny,0.,0.]);sc=np.array([1.,1.,1e3,1e3])
    before=(k.data.copy(),load.copy(),sc.copy())
    result=candidate.solve_body_twofold(k,load,sc)
    (tmp_path/('quiet-'+str(tiny)+'.json')).write_text(json.dumps(result.report,indent=2))
    assert result.report['status']=='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED'
    assert D(result.report['equation_ratio'])<=D('1e-8')
    assert abs(result.report['ordinary_hi_only_CSR_residual'][1]/tiny)>=.99
    assert np.any(result.coordinates.low!=0.)
    # Independent original-equation contraction, not candidate.matrix_action.
    with localcontext() as context:
        context.prec=4096
        q=[D.from_float(float(h))+D.from_float(float(l)) for h,l in
           zip(result.coordinates.high,result.coordinates.low)]
        for i in range(4):
            residual=sum((D.from_float(float(k[i,j]))*q[j] for j in range(4)),D(0))-D.from_float(float(load[i]))
            assert residual==D(result.report['physical_residual'][i])
        work=sum((D.from_float(float(f))*v for f,v in zip(load,q)),D(0))
        assert work==D(result.report['paired_work_J'])
        hi_only=sum((D.from_float(float(f))*D.from_float(float(v)) for f,v in zip(load,result.coordinates.high)),D(0))
        assert work!=hi_only
        # Actual manufactured complementary material energy; never a negative block.
        energy=(q[2]**2+q[3]**2)/2
        assert abs(2*energy-work)/work<=D('1e-8')
    for old,new in zip(before,(k.data,load,sc)):np.testing.assert_array_equal(old,new)
    with pytest.raises(ValueError):result.coordinates.low[0]=1.
    with pytest.raises(ValueError):result.coordinates.high.setflags(write=True)


def gauge_system():
    k=sparse.block_diag([[[1.,-1.],[-1.,1.]]]*6,format='csr')
    rigid=np.zeros((12,6))
    for j in range(6):rigid[2*j:2*j+2,j]=1.
    return k,rigid


def test_original_indefinite_gauge_and_work(tmp_path):
    k,r=gauge_system();load=np.tile([1.,-1.],6)
    result=candidate.solve_body_twofold(k,load,np.ones(12),rigid=r)
    (tmp_path/'gauge.json').write_text(json.dumps(result.report,indent=2))
    assert result.report['status']=='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED'
    assert result.report['factorization_count']==1
    assert max(map(lambda x:abs(D(x)),result.report['gauge_pose']))<=D('1e-9')
    assert max(map(lambda x:abs(D(x)),result.report['gauge_covector']))<=D('1e-8')
    assert D(result.report['paired_work_J'])==D(6)
    assert D(result.report['internal_pairing_J'])==D(6)
    assert result.gauge_multipliers.high.shape==(6,)


def test_tiny_admitted_rigid_imbalance_never_replaces_physical_gate(tmp_path):
    k,r=gauge_system();load=np.zeros(12);load[:2]=[1e-10,0.]
    # Inside original 1e-8 rigid-work floor, but nonzero gauge force is not load.
    result=candidate.solve_body_twofold(k,load,np.ones(12),rigid=r)
    (tmp_path/'physical-vs-kkt.json').write_text(json.dumps(result.report,indent=2))
    assert result.report['status'].startswith('FAILED_')
    assert D(result.report['joint_KKT_ratio'])<=D('1e-8')
    assert D(result.report['equation_ratio'])>=D('.49')
    assert max(map(lambda x:abs(D(x)),result.report['gauge_covector']))<D('1e-8')


def test_fixed_support_covector_uses_represented_solution():
    k=sparse.csr_matrix([[1.,-1.],[-1.,2.]])
    result=candidate.solve_body_twofold(k,[0.,1.],[1.,1.],fixed=(0,))
    assert result.report['status']=='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED'
    q=result.coordinates.decimal_values()[1]
    assert D(result.report['support_covector']['0'])==-q
    assert D(result.report['paired_work_J'])==q
    assert abs(q-D('.5'))<=D('1e-8')
    assert result.coordinates.high[0]==result.coordinates.low[0]==0.


def test_invalid_input_and_factorization_fail_closed():
    k,r=gauge_system()
    with pytest.raises(ValueError):candidate.solve_body_twofold(k,np.ones(12),np.ones(12),rigid=r)
    with pytest.raises(ValueError):candidate.solve_body_twofold(k,np.zeros(12),np.ones(12),fixed=(0,0))
    with pytest.raises(ValueError):candidate.solve_body_twofold(k,np.zeros(12),np.zeros(12))
    with pytest.raises(ValueError):candidate.solve_body_twofold(k,np.full(12,np.nan),np.ones(12))
    with pytest.raises(ValueError):candidate.solve_body_twofold(k.toarray(),np.zeros(12),np.ones(12))
    r[:,1]=r[:,0]
    result=candidate.solve_body_twofold(k,np.zeros(12),np.ones(12),rigid=r)
    assert result.report['status']=='FAILED_FACTORIZATION'


def test_nonfinite_and_stagnating_corrections_have_explicit_status(monkeypatch):
    class Fake:
        def __init__(self,value):self.value=value
        def solve(self,rhs):return np.full(len(rhs),self.value)
    k=sparse.eye(2,format='csr')
    monkeypatch.setattr(candidate,'splu',lambda _:Fake(np.nan))
    result=candidate.solve_body_twofold(k,[1.,1.],[1.,1.])
    assert result.report['status']=='FAILED_NONFINITE'
    monkeypatch.setattr(candidate,'splu',lambda _:Fake(0.))
    result=candidate.solve_body_twofold(k,[1.,1.],[1.,1.])
    assert result.report['status']=='FAILED_STAGNATION' and D(result.report['equation_ratio'])==1


def test_extreme_dyadic_quiet_row_retains_low_parts(tmp_path):
    k=sparse.csr_matrix([[0.,0.,1.,1.],[0.,0.,1.,-1.],[1.,1.,-1.,0.],[1.,-1.,0.,-1.]])
    result=candidate.solve_body_twofold(k,[1.,1e-200,0.,0.],[1.,1.,1e3,1e3])
    (tmp_path/'extreme-resolution.json').write_text(json.dumps(result.report,indent=2))
    assert result.report['status']=='DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED'
    assert D(result.report['equation_ratio'])<=D('1e-8')


def test_three_scale_representation_limit_fails_closed(tmp_path):
    b=np.array([[1.,1.,1.],[1.,-1.,0.],[0.,1.,-1.]])
    k=sparse.bmat([[None,sparse.csr_matrix(b)],[sparse.csr_matrix(b.T),-sparse.eye(3)]],format='csr')
    result=candidate.solve_body_twofold(k,[1.,1e-20,1e-40,0.,0.,0.],np.ones(6))
    (tmp_path/'three-scale-limit.json').write_text(json.dumps(result.report,indent=2))
    assert result.report['status'].startswith('FAILED_')
    assert D(result.report['equation_ratio'])>D('1e-8')


def test_subnormal_residual_cannot_false_pass(monkeypatch):
    class Fake:
        def solve(self,rhs):return np.array([np.nextafter(0.,1.)])
    monkeypatch.setattr(candidate,'splu',lambda _:Fake())
    result=candidate.solve_body_twofold(sparse.csr_matrix([[.6]]),[np.nextafter(0.,1.)],[1.],max_corrections=0)
    assert result.report['status'].startswith('FAILED_')
    assert D(result.report['equation_ratio'])>D('.1')
    assert float(D(result.report['physical_residual'][0]))==0.


def test_unexpected_linear_solve_exception_propagates(monkeypatch):
    class Fake:
        def solve(self,rhs):raise RuntimeError('injected programming exception')
    monkeypatch.setattr(candidate,'splu',lambda _:Fake())
    with pytest.raises(RuntimeError,match='injected programming'):
        candidate.solve_body_twofold(sparse.eye(2,format='csr'),[1.,1.],[1.,1.])
