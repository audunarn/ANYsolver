"""Synthetic port-rank proofs; no physical reference equilibrium."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_root_rank as rank
from scripts import _b3_e4_f03_spatial_contract as c


def budget(**changes):
    return replace(rank.RankBudget(common.SparseBudget(256,4096,4,8_000_000),
                   100_000,100_000_000,160,800_000_000), **changes)


def ports(rows):
    scaling=np.array((1/c.U0,1/c.U0,.46/c.U0,c.L0/c.U0))
    physical=rows/scaling[:,None]
    return sparse.csr_matrix(physical[:3]),sparse.csr_matrix(physical[3:])


def verify(rows, **changes):
    root,slope=ports(rows)
    return rank.verify_root_rank(root,slope,np.ones(rows.shape[1]),budget=budget(**changes))


def test_independent_ports_match_small_svd_and_do_not_impose_slope():
    rows=np.array([[1.,.25,0.,0.,0.],[0.,2.,.5,0.,0.],
                   [0.,0.,3.,.2,0.],[0.,0.,0.,1.,.5]])
    result=verify(rows)
    assert result['status']=='PORT_RANK_PASSED'
    for key,count in [('root',3),('root_and_free_slope',4)]:
        singular=np.linalg.svd(result['scaled_rows'][:count],compute_uv=False)
        ratio=(singular[-1]/singular[0])**2
        proof=result[key]
        assert float(proof['ratio_squared_lower']) <= ratio <= float(proof['ratio_squared_upper'])
        assert proof['full_row_rank']
    assert result['work']['equilibrium_solves']==0
    assert result['work']['eigensolves']==0
    assert result['scope']=='SCALED_PORT_RANK_ONLY_NOT_TRACE_BINDING'


@pytest.mark.parametrize('dependent',('root','slope'))
def test_root_or_augmented_dependence_is_not_a_pass(dependent):
    rows=np.eye(4)
    if dependent=='root': rows[1]=rows[0]
    else: rows[3]=rows[0]
    result=verify(rows)
    assert result['status']=='HOLD'
    proof=result['root'] if dependent=='root' else result['root_and_free_slope']
    assert not proof['full_row_rank']
    if dependent=='slope': assert result['root']['status']=='PASSED'


@pytest.mark.parametrize('factor,status',[(F(999,1000),'HOLD'),(F(1),'PASSED'),(F(1001,1000),'PASSED')])
def test_exact_diagonal_threshold_is_inclusive(factor,status):
    # Exact Gram oracle isolates the frozen squared singular-ratio boundary.
    gram=((F(1),F(0),F(0)),(F(0),F(1),F(0)),
          (F(0),F(0),(rank.RATIO*factor)**2))
    proof=rank._ratio_proof(gram,rank._Exact(budget()),160)
    assert proof['status']==status
    assert proof['ratio_squared_lower']==proof['ratio_squared_upper']


@pytest.mark.parametrize('small,status',[(4e-10,'PORT_RANK_PASSED'),(1e-10,'HOLD')])
def test_nondiagonal_ill_conditioned_rows_are_resolved(small,status):
    rows=np.eye(4);rows[3]=rows[0];rows[3,3]=small
    result=verify(rows)
    assert result['status']==status
    assert result['root_and_free_slope']['steps']>1


def test_unresolved_enclosure_is_hold_without_claim_of_deficiency():
    rows=np.eye(4);rows[3]=rows[0];rows[3,3]=4e-10
    result=verify(rows,max_eigen_steps=1)
    proof=result['root_and_free_slope']
    assert result['status']=='HOLD' and proof['full_row_rank']
    assert 'unresolved' in proof['reason']


def test_sparse_format_coordinate_rescaling_and_owned_result():
    rows=np.eye(4,129);root,slope=ports(rows)
    d=np.full(129,2.)
    result=rank.verify_root_rank((root/2).tocsc(),(slope/2).tocsc(),d,budget=budget())
    original=verify(rows)
    assert result['exact_gram']==original['exact_gram']
    root.data[:]=0.;slope.data[:]=0.;d[:]=0.
    assert result['status']=='PORT_RANK_PASSED'
    assert result['work']['dense_square_order']==4
    with pytest.raises(ValueError): result['scaled_rows'][0,0]=0.
    with pytest.raises(ValueError): result['scaled_rows'].flags.writeable=True


@pytest.mark.parametrize('changes',[
    {'max_work_bytes':1},{'max_fraction_bits':1},{'max_total_bits':1}])
def test_resource_exhaustion_is_explicit(changes):
    with pytest.raises(ValueError,match='budget'):verify(2*np.eye(4),**changes)


def test_workspace_guard_precedes_dense_port_allocation(monkeypatch):
    root,slope=ports(np.eye(4))
    def forbidden(*args,**kwargs):raise AssertionError('port allocation before budget')
    monkeypatch.setattr(rank.np,'zeros',forbidden)
    with pytest.raises(ValueError,match='workspace'):
        rank.verify_root_rank(root,slope,np.ones(4),budget=budget(max_work_bytes=1))


def test_nonpositive_scaling_and_malformed_sparse_rejected():
    root,slope=ports(np.eye(4))
    with pytest.raises(ValueError,match='positive'):
        rank.verify_root_rank(root,slope,np.zeros(4),budget=budget())
    root.indices[0]=99
    with pytest.raises(ValueError):
        rank.verify_root_rank(root,slope,np.ones(4),budget=budget())


def test_underflowed_nonzero_scaling_is_not_a_zero_port():
    root,slope=ports(np.eye(4));root.data[0]=np.nextafter(0.,1.)
    with pytest.raises(ArithmeticError,match='underflowed'):
        rank.verify_root_rank(root,slope,np.full(4,1e-300),budget=budget())
