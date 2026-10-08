"""Manufactured saved trace/operator identities; no physical equilibrium."""
from bisect import bisect_right
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_trace_binding as t
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_root_rank as rank
from scripts import _b3_e4_f03_spatial_contract as c

TB=assembly.AssemblyBudget(512,2_000_000,64*1024**2,8_000_000)
BUDGET=t.TraceBindingBudget(common.SparseBudget(512,4096,3,16*1024**2),
                           TB,100_000,16384,40_000_000,1024**3)


@pytest.fixture(scope='module')
def fixture():
    g=grid.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),F(0),F(1,2)),2)
    q=[];nx=len(g.x_nodes);nc=nx*len(g.y_nodes)
    for index in g.free_to_full:
        channel,node=divmod(int(index),nc);j,i=divmod(node,nx)
        x,y=g.x_nodes[i],g.y_nodes[j]
        q.append(float((1-(x-F(1,2))**2)*(F(2+channel,10**6)+F(3-channel,10**6)*y)))
    q=np.array(q);d=np.full(g.free_dofs,c.U0)
    traces={};samples=[]
    for s,order,side in t.KEYS:
        k=min(bisect_right(g.station_cuts,s)-1,len(g.station_cuts)-2)
        if side=='left' and k>0 and s==g.station_cuts[k]:k-=1
        if k not in traces:traces[k]=assembly.trace_interval(g,k,TB)
        tr=traces[k];exact=tr.evaluate_exact((s-tr.left)/(tr.right-tr.left),order)
        values=np.array(exact,dtype=float)
        operator=sparse.coo_matrix((values.ravel(),
            (np.repeat(np.arange(3),len(tr.indices)),np.tile(tr.indices,3))),
            shape=(3,g.free_dofs)).tocsr()
        operator.eliminate_zeros()
        samples.append(t.SavedPort(s,order,side,operator,operator@q))
    root=samples[0].operator.copy();tip=samples[8].operator.copy()
    slope=samples[9].operator[1:2].copy()
    return g,q,d,tuple(samples),root,tip,slope


def check(data,budget=BUDGET):return t.verify_trace_binding(*data,budget=budget)


def test_full_trace_inventory_and_analytic_manufactured_actions(fixture):
    result=check(fixture)
    assert result['status']=='TRACE_BINDING_PASSED'
    assert result['work']['station_operators']==27
    assert result['work']['exact_intervals_extracted']<=9
    assert result['work']['equilibrium_solves']==0
    # Independent closed polynomial for the first translation and derivatives.
    xx=c.Q_DX**2+c.Q_A**2/3
    for sample in fixture[3]:
        s=sample.station;u=s-F(1,2)
        exact=(F(2,10**6)*(1-u*u-xx),-2*F(2,10**6)*u,-2*F(2,10**6))[sample.order]
        assert sample.action[0]==pytest.approx(float(exact),rel=1e-13,abs=1e-20)


def test_bound_extracted_root_and_free_slope_pass_exact_rank(fixture):
    assert check(fixture)['status']=='TRACE_BINDING_PASSED'
    rb=rank.RankBudget(BUDGET.sparse_budget,16384,40_000_000,160,256*1024**2)
    result=rank.verify_root_rank(fixture[4],fixture[6],fixture[2],budget=rb)
    assert result['status']=='PORT_RANK_PASSED'
    assert result['root']['full_row_rank'] and result['root_and_free_slope']['full_row_rank']
    assert result['work']['equilibrium_solves']==0


@pytest.mark.parametrize('field',('operator','action'))
def test_stale_operator_or_saved_action_detected(fixture,field):
    data=list(fixture);samples=list(data[3]);old=samples[13]
    if field=='operator':
        changed=old.operator.copy();changed.data[0]+=.01
        samples[13]=replace(old,operator=changed)
    else:
        changed=old.action.copy();changed[0]+=1e-6
        samples[13]=replace(old,action=changed)
    data[3]=tuple(samples)
    result=check(data)
    assert result['status']=='HOLD'
    assert any('port 13' in s for s in result['failures'])


@pytest.mark.parametrize('index,name',[(4,'root'),(5,'tip'),(6,'free_slope')])
def test_endpoint_operators_cannot_be_substituted(fixture,index,name):
    data=list(fixture);data[index]=data[index].copy();data[index].data[0]+=.01
    result=check(data)
    assert result['status']=='HOLD'
    assert any(name in s for s in result['failures'])


def test_opposite_small_endpoint_biases_do_not_hide_direct_disagreement(fixture):
    data=list(fixture);samples=list(data[3]);root=data[4].copy()
    opposite=samples[0].operator.copy();opposite.data[0]-=6e-12;root.data[0]+=6e-12
    samples[0]=replace(samples[0],operator=opposite);data[3]=samples;data[4]=root
    result=check(data)
    assert result['endpoints']['root']['exact_operator_scaled_upper']<1e-11
    assert result['endpoints']['root']['saved_station_operator_scaled_upper']>1e-11
    assert result['status']=='HOLD'
    assert 'root: saved station operator mismatch' in result['failures']


@pytest.mark.parametrize('change',('missing','side','order','inexact_station'))
def test_complete_exact_fixed_observation_contract_required(fixture,change):
    data=list(fixture);samples=list(data[3])
    if change=='missing':samples.pop()
    elif change=='side':samples[8]=replace(samples[8],side='right')
    elif change=='order':samples[0]=replace(samples[0],order=True)
    else:samples[0]=replace(samples[0],station=0.)
    data[3]=samples
    with pytest.raises(ValueError,match='inventory'):check(data)


def test_csc_parity_owned_results_and_input_identity(fixture):
    data=list(fixture)
    data[3]=tuple(replace(s,operator=s.operator.tocsc(),action=s.action.copy()) for s in data[3])
    original=check(fixture);copied=check(data)
    assert copied['checks']==original['checks'] and copied['endpoints']==original['endpoints']
    snapshot=copied['input_sha256']['saved_actions']
    data[3][0].action[:]=0.
    assert copied['input_sha256']['saved_actions']==snapshot
    assert snapshot!=check(data)['input_sha256']['saved_actions']


@pytest.mark.parametrize('change',[
    {'max_input_nnz':1},{'max_work_bytes':1},{'max_fraction_bits':1},{'max_total_bits':1}])
def test_explicit_resource_limits(fixture,change):
    with pytest.raises(ValueError,match='budget'):check(fixture,replace(BUDGET,**change))


def test_workspace_guard_precedes_trace_extraction(fixture,monkeypatch):
    def forbidden(*args,**kwargs):pytest.fail('trace extraction before preflight')
    monkeypatch.setattr(assembly,'trace_interval',forbidden)
    with pytest.raises(ValueError,match='workspace'):check(fixture,replace(BUDGET,max_work_bytes=1))


def test_caller_sample_list_mutation_cannot_shorten_owned_inventory(fixture,monkeypatch):
    data=list(fixture);data[3]=list(data[3]);original=assembly.trace_interval
    def mutate(*args,**kwargs):
        data[3].clear()
        return original(*args,**kwargs)
    monkeypatch.setattr(assembly,'trace_interval',mutate)
    result=check(data)
    assert result['status']=='TRACE_BINDING_PASSED'
    assert len(result['checks'])==27


def test_malformed_sparse_buffers_are_not_traversed(fixture):
    data=list(fixture);data[4]=data[4].copy();data[4].indices[0]=data[0].free_dofs
    with pytest.raises(ValueError,match='index'):check(data)
