"""Manufactured saved-work verification; no physical equilibrium is solved."""
from dataclasses import replace
from fractions import Fraction as F
import numpy as np
import pytest
from scripts import _b3_e4_f03_saved_work_checks as w
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_action_enclosure as bound
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_spatial_contract as c

RB=rec.RecoveryBudget(assembly.AssemblyBudget(512,1,128*1024**2,8_000_000),
    1024,128,8_000_000,256*1024**2,1_000_000_000)
SB=support.SupportBudget(RB,1024,128,1_000_000_000,80_000_000,512*1024**2)
AB=bound.ActionBudget(64,128,65536,200_000_000,2_000_000,256*1024**2)
WB=w.WorkBudget(SB,AB,4096,30000,10**12,10**14,2*1024**3)


def _model():
    return grid.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),F(0),F(1,2)),1)


def _values(actions):
    return np.asarray([float(a.decimal_value()) for a in actions],dtype=np.float64)


def _numerical_virtual(value,rows):
    # Independent 48-point evaluation of the four signed physical terms.
    nodes,weights=np.polynomial.legendre.leggauss(48)
    tau=(nodes+1)/2;weights=weights/2
    terms=np.zeros(4)
    for a,b,row,stress,density in zip(value.cuts,value.cuts[1:],rows,
                                    value.resultants,value.interface.coefficients):
        h=float(b-a);s=float(a)+h*tau
        test=np.array([np.polynomial.polynomial.polyval(tau,np.array(p,float)) for p in row])
        dt=np.array([np.polynomial.polynomial.polyval(tau,
            np.arange(1,6)*np.array(p[1:],float))/h for p in row])
        nqm=np.array([np.polynomial.polynomial.polyval(tau,np.array(p,float)) for p in stress])
        mu=np.array([np.polynomial.polynomial.polyval(tau,np.array(p,float))+
                     float(amp)*np.cos(c.OMEGA*s) for p,amp in zip(density,value.interface.cosine)])
        terms[0]+=h*np.sum(weights*np.sum(mu*test,axis=0))
        terms[1]+=h*np.sum(weights*(nqm[0]*dt[0]+nqm[1]*(dt[1]-test[2])+nqm[2]*dt[2]))
        terms[2]+=h*np.sum(weights*c.F0*(1+.25*np.cos(c.OMEGA*s))*test[1])
    endpoint0=np.array([float(p[0]) for p in rows[0]])
    endpoint1=np.array([float(sum(p)) for p in rows[-1]])
    terms[0]+=np.array(value.interface.atoms[0],float)@endpoint0
    terms[0]+=np.array(value.interface.atoms[1],float)@endpoint1
    terms[3]=np.array(value.eta,float)@endpoint0
    return terms


def _saved(g,q):
    value=rec.recover(g,q,(F(0),)*3,RB)
    result=support.support_recovery(g,value,SB)
    terms=np.array([_numerical_virtual(value,rows) for _,rows in w.virtual_inventory(value.cuts,g.p)])
    terms=terms.reshape(3,-1,4)
    defects=terms[:,:,0]+terms[:,:,1]-terms[:,:,2]+terms[:,:,3]
    return w.SavedWork(g.p,value.cuts,result.lift_family,
        np.array([support.lift_pose(value.cuts,side,ch,g.p)
                  for side in ('left','right') for ch in range(3)],float),
        np.array(result.shell_work,float),_values(result.interface_work),
        _values(result.route1),_values(result.route2),
        _values((result.first_free_route1_residual,result.first_free_route2_residual)),
        _values((result.shift_route1_delta,result.shift_route2_delta)),terms,defects)


@pytest.fixture(scope='module')
def case():
    g=_model();q=(F(0),)*g.free_dofs
    return g,q,_saved(g,q)


@pytest.mark.parametrize('p',(1,2,3))
def test_full_continuous_basis_count_rank_endpoints_and_units(p):
    cuts=(F(0),F(2,7),F(1));ni=2;degree=p+2
    inventory=list(w.virtual_inventory(cuts,p))
    assert len(inventory)==3*(ni*degree+1)
    assert inventory[0][0]==(0,'vertex',0)
    assert inventory[ni][0]==(0,'vertex',ni)
    for channel in range(3):
        amplitude=c.Q_U0 if channel<2 else c.Q_U0/w.functional.ELL
        tests=inventory[channel*(ni*degree+1):(channel+1)*(ni*degree+1)]
        matrix=[]
        for key,rows in tests:
            assert sum(rows[0][channel])==rows[1][channel][0]
            for row in rows:
                assert all(not any(row[k]) for k in range(3) if k!=channel)
            samples=[rows[0][channel][0],sum(rows[-1][channel])]
            samples.append(sum(rows[0][channel]))
            for row in rows:
                samples.extend(sum(v*F(j,degree)**k for k,v in enumerate(row[channel]))
                               for j in range(1,degree))
            matrix.append([float(v/amplitude) for v in samples])
        assert np.linalg.matrix_rank(np.array(matrix))==ni*degree+1
        assert tests[0][1][0][channel][0]==amplitude
        assert sum(tests[ni][1][-1][channel])==amplitude


def test_complete_saved_work_and_independent_gauss_terms(case):
    g,q,saved=case
    result=w.verify_work(g,q,(F(0),)*3,saved,budget=WB)
    assert result['status']=='PASSED'
    assert result['scope']==w.SCOPE
    assert result['diagnostics']['virtual_tests']==3*((len(g.station_cuts)-1)*3+1)
    assert result['diagnostics']['equilibrium_solves']==0
    assert result['diagnostics']['norm_evaluations']==0
    assert result['lift_chart_bit_parity']


@pytest.mark.parametrize('field',('edge_route1','virtual_defects','virtual_terms','lift_coefficients'))
def test_corrupted_saved_observation_rejected(case,field):
    g,q,saved=case
    bad=getattr(saved,field).copy();bad.flat[0]+=1
    result=w.verify_work(g,q,(F(0),)*3,replace(saved,**{field:bad}),budget=WB)
    assert result['status']=='FAILED'


def test_matching_saved_nonstationary_shift_still_fails():
    g=_model();q=(F(1,10**6),)+(F(0),)*(g.free_dofs-1)
    saved=_saved(g,q);result=w.verify_work(g,q,(F(0),)*3,saved,budget=WB)
    assert result['status']=='FAILED'
    assert result['comparisons']['first_free/saved/0']['status']=='PASSED'
    assert result['comparisons']['first_free/zero/0']['status']=='FAILED'
    assert all(v['status']=='PASSED' for name,v in result['comparisons'].items()
               if name.startswith('route_difference/'))


def test_owned_input_and_output_array_writeability(case,monkeypatch):
    g,q,saved=case
    original=saved.edge_route1.copy()
    owned=replace(saved,edge_route1=original);original[:]=999
    assert not np.array_equal(owned.edge_route1,original)
    with pytest.raises(ValueError):owned.edge_route1.setflags(write=True)
    before=w.verify_work(g,q,(F(0),)*3,owned,budget=WB)
    original[:]=-123
    after=w.verify_work(g,q,(F(0),)*3,owned,budget=WB)
    assert before['input_sha256']==after['input_sha256']


def test_preflight_and_malformed_inventory(case,monkeypatch):
    g,q,saved=case
    def forbidden(*args,**kwargs):raise AssertionError('recovery must not start')
    monkeypatch.setattr(rec,'recover',forbidden)
    for field in ('max_virtual_tests','max_comparisons','max_aggregate_operations',
                  'max_aggregate_bits','max_work_bytes'):
        with pytest.raises(ValueError,match='budget'):
            w.verify_work(g,q,(F(0),)*3,saved,budget=replace(WB,**{field:1}))
    for bad in (saved.virtual_terms.astype(np.float32),np.zeros((1,)),np.full(saved.virtual_terms.shape,np.nan)):
        with pytest.raises(ValueError,match='float64'):
            replace(saved,virtual_terms=bad)
    with pytest.raises(ValueError,match='identity'):replace(saved,lift_family='wrong')
    with pytest.raises(ValueError,match='partition'):replace(saved,cuts=(F(0),F(0),F(1)))


def test_failed_precedence_over_hold():
    assert w._status({'a':{'status':'HOLD_UNRESOLVED'},'b':{'status':'FAILED'}},True)=='FAILED'
    assert w._status({'a':{'status':'HOLD_UNRESOLVED'}},True)=='HOLD_UNRESOLVED'


def test_finiteness_validation_uses_owned_bytes(monkeypatch):
    original=np.arange(6,dtype=np.float64)
    isfinite=np.isfinite
    def mutate_during_validation(argument):
        original[:]=np.nan
        return isfinite(argument)
    monkeypatch.setattr(np,'isfinite',mutate_during_validation)
    owned=w._array(original,(6,))
    assert np.array_equal(owned,np.arange(6,dtype=np.float64))
    assert np.isnan(original).all()


def test_actual_underresolved_enclosures_remain_hold(case):
    g,q,saved=case
    result=w.verify_work(g,q,(F(0),)*3,saved,
                        budget=replace(WB,action_budget=replace(AB,order=0)))
    assert result['status']=='HOLD_UNRESOLVED'
    assert any(v['status']=='HOLD_UNRESOLVED' for v in result['comparisons'].values())
