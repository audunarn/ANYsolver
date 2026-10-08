"""Work-form and actual-role counterexamples for the sparse family caller."""
import copy
from fractions import Fraction
import hashlib

import numpy as np
import pytest
from scipy import sparse

from scripts import r8_bl5_sparse_envelope_kernel_dev as family
from scripts.r8_bl5_projected_envelope_norm_dev import all_cases, case_from_id


def fixture(case):
    ns,nodal=case.counts['shell_nodes'],case.counts['physical_dofs']
    typed=[dict(domain='shell',native_node=j+1,q_offset=6*j) for j in range(ns)]
    typed += [dict(domain='beam',native_node=101+j,q_offset=6*(ns+j)) for j in range(case.halfcells+1)]
    retained=[]
    for j in range(case.counts['members']):
        base=nodal+24*j
        retained.append(dict(member_index=j,retained_24_offset=base,
            cell_rotation_slots=list(range(base,base+6)),resultant_slots=list(range(base+6,base+24))))
    fixed=sorted({6*j*(case.nx+1)+axis for j in range(case.ny+1) for axis in range(6)}|set(range(6*ns,6*ns+5)))
    fixed=np.array(fixed);free=np.setdiff1d(np.arange(case.counts['full_q']),fixed)
    names=('shell_nodes','beam_nodes','physical_dofs','members','retained_cell_rotations',
        'retained_resultants','retained_dofs','full_q','multipliers')
    data=dict(fixture=case.fixture,layout=dict(counts={name:case.counts[name] for name in names},
        typed_physical_nodes=typed,retained_members=retained),supports=[dict(
        native_halfcells=list(range(j*case.span,(j+1)*case.span)),
        multiplier_rows=list(range(j*10,(j+1)*10))) for j in range(case.supports)])
    return data,free,fixed


@pytest.mark.parametrize('case',all_cases())
def test_all_registered_quarters_retain_native_roles_and_avoid_fixed_root(case):
    data,free,fixed=fixture(case)
    x,pp,blocks=family.partition(case,data,free,fixed)
    groups,pivots=family.support_pivots(case,data,x)
    assert len(x)==case.counts['physical_free']
    assert len(x)-sum(map(len,groups))==case.counts['kernel']
    assert not set(map(int,x))&set(map(int,pp))
    assert len(set(int(x[j]) for p in pivots for j in p))==case.counts['multipliers']
    assert all(len(block)==18 for block in blocks)
    assert case.counts['full_q']<=family.INPUT_BUDGET.max_order


@pytest.mark.parametrize('kind',('fixed_duplicate','retained_shift','typed_domain','missing_member','wrong_counts'))
def test_actual_inventory_defects_cannot_be_reinterpreted(kind):
    case=case_from_id('ns16_b8');data,free,fixed=fixture(case)
    if kind=='fixed_duplicate':fixed[1]=fixed[0]
    if kind=='retained_shift':data['layout']['retained_members'][0]['resultant_slots'][0]-=1
    if kind=='typed_domain':data['layout']['typed_physical_nodes'][-1]['domain']='shell'
    if kind=='missing_member':data['layout']['retained_members'].pop()
    if kind=='wrong_counts':data['layout']['counts']['members']-=1
    with pytest.raises(ValueError):family.partition(case,data,free,fixed)


def test_missing_support_or_fixed_quarter_cannot_create_smaller_kernel():
    case=case_from_id('ns16_b1_8');data,free,fixed=fixture(case)
    x,_,_=family.partition(case,data,free,fixed)
    short=copy.deepcopy(data);short['supports'][0]['native_halfcells'].pop()
    with pytest.raises(ValueError):family.support_pivots(case,short,x)
    quarter=6*(case.counts['shell_nodes']+1)
    with pytest.raises(ValueError):family.support_pivots(case,data,x[x!=quarter])


def test_local_negative_work_and_zero_positive_counterexamples():
    proof=family.negative_block_proof(-np.diag(np.arange(1.,19.)))
    assert proof['proof']['status']=='POSITIVE_SHIFTED_LOWER_COMPLETION'
    for matrix in (np.eye(18),np.zeros((18,18))):
        assert family.negative_block_proof(matrix)['proof']['status']!='POSITIVE_SHIFTED_LOWER_COMPLETION'


def test_stationary_uses_both_saved_coupling_sides_and_only_local_inverses():
    # A tiny nonsymmetry lies within the conservative saved-input budget.
    # Its two distinct work maps must survive the stationary pullback.
    k=np.zeros((20,20));k[:2,:2]=((3.,.2),(.2,4.))
    d=-np.diag(np.arange(1.,19.));k[2:,2:]=d
    k[0,2]=.3;k[1,3]=-.4;k[2,0]=.3+1e-12;k[3,1]=-.4-1e-12
    report={};s=family.stationary(sparse.csr_matrix(k),sparse.csr_matrix((1,20)),
        np.array([0,1]),[np.arange(2,20)],report)
    # Independent diagonal force-method evaluation with exact stored operands.
    for i,j in ((0,0),(1,1),(0,1),(1,0)):
        expected=Fraction(float(k[i,j]))-sum(Fraction(float(k[i,p]))*Fraction(float(k[p,j]))/Fraction(float(k[p,p])) for p in range(2,20))
        assert abs(Fraction(float(s[i,j]))-expected)<Fraction(1,10**14)
    assert len(report['local_negative_work'])==1
    assert report['local_stationary'][0]['neighbours']==2


def test_nonlocal_resultants_and_direct_resultant_constraints_refuse_elimination():
    k=-np.eye(38);k[:2,:2]=np.eye(2);x=np.array([0,1])
    blocks=[np.arange(2,20),np.arange(20,38)]
    c=sparse.csr_matrix(([1.],([0],[2])),shape=(1,38))
    with pytest.raises(ValueError,match='constraints'):family.stationary(sparse.csr_matrix(k),c,x,blocks,{})
    k[2,20]=.1
    with pytest.raises(ValueError,match='nonlocal'):family.stationary(sparse.csr_matrix(k),sparse.csr_matrix((1,38)),x,blocks,{})


def test_local_sign_failure_keeps_its_actual_proof_before_predicate():
    k=np.eye(20);report={}
    with pytest.raises(ValueError,match='local negative'):
        family.stationary(sparse.csr_matrix(k),sparse.csr_matrix((1,20)),
            np.array([0,1]),[np.arange(2,20)],report)
    proof=next(iter(report['local_negative_work'].values()))['proof']
    assert proof['status']=='NONPOSITIVE_REPRESENTATIVE'
    assert len(proof['pivot_lower'])==len(proof['pivot_upper'])==1


def test_consistent_state_metadata_array_mutation_cannot_replace_frozen_pair(tmp_path):
    state=tmp_path/'state.json';array=tmp_path/'state.npz'
    state.write_text('original metadata');array.write_bytes(b'original array')
    canonical=[family.ROOT/'synthetic/state.json',family.ROOT/'synthetic/state.npz']
    records={p.relative_to(family.ROOT).as_posix():hashlib.sha256(a.read_bytes()).hexdigest()
        for p,a in zip(canonical,(state,array))}
    for p,a in zip(canonical,(state,array)):family.frozen_file(a,p,records)
    # Even mutually consistent replacement metadata and array are not original.
    array.write_bytes(b'replacement');state.write_text(hashlib.sha256(array.read_bytes()).hexdigest())
    for p,a in zip(canonical,(state,array)):
        with pytest.raises(ValueError,match='immutable'):family.frozen_file(a,p,records)


def test_historical_manifest_schemas_remain_distinct():
    assert family.previous_hash({'previous_manifest_sha256':'old'},8)=='old'
    assert family.previous_hash({'previous_manifest_sha256':'old'},6)=='old'
    v7=dict(schema='BL5_DEVELOPMENT_RAW_EXTENSION_V7',previous_manifest='raw-manifest-v6.json',previous_sha256='preserved')
    assert family.previous_hash(v7,7)=='preserved'
    for record in ({**v7,'schema':'invented'},{**v7,'previous_manifest':'replacement.json'}):
        with pytest.raises(ValueError):family.previous_hash(record,7)
    with pytest.raises(ValueError):family.previous_hash({},1)


def test_incidence_bound_covers_overlapping_nonsymmetric_and_cancelled_errors():
    supports=[np.array([0,1]),np.array([1,2]),np.array([0,1])]
    errors=[2.,3.,2.]
    upper,weights,counts=family.incidence_bound(3,supports,errors)
    # Nonsymmetric rank-one updates overlap. Third can cancel the first,
    # but its support/count/error must remain present in the certificate.
    first=np.array([[0.,2.,0.],[0.,0.,0.],[0.,0.,0.]])
    second=np.array([[0.,0.,0.],[0.,0.,3.],[0.,0.,0.]])
    third=-first
    e=first+second+third
    assert np.array_equal(e,second) and np.linalg.norm(e,2)<=upper and upper>=7.
    assert np.array_equal(counts,[2,3,1]) and np.all(weights>=[4.,7.,3.])
    disjoint,_,_=family.incidence_bound(4,[np.array([0,1]),np.array([2,3])],[2.,3.])
    assert 3.<=disjoint<3.00000000000001
    for invalid in (np.array([1,1]),np.array([-1]),np.array([3]),np.array([.5])):
        with pytest.raises(ValueError):family.incidence_bound(3,[invalid],[1.])
    for error in (-1.,float('nan'),float('inf')):
        with pytest.raises(ValueError):family.incidence_bound(3,[np.array([0])],[error])


def test_incidence_stationary_bound_encloses_exact_force_method_work():
    k=np.zeros((20,20));k[:2,:2]=((3.,.2),(.2,4.))
    k[2:,2:]=-np.diag(np.arange(1.,19.))
    k[0,2]=.3;k[1,3]=-.4;k[2,0]=.3+1e-12;k[3,1]=-.4-1e-12
    matrix=sparse.csr_matrix(k);x=np.array([0,1]);blocks=[np.arange(2,20)]
    shat=family.stationary(matrix,sparse.csr_matrix((1,20)),x,blocks,{})
    error,details,record=family.stationary_incidence_error(matrix,shat,np.ones(2),x,blocks)
    exact=[[Fraction(float(k[i,j]))-sum(Fraction(float(k[i,p]))*Fraction(float(k[p,j]))/Fraction(float(k[p,p]))
        for p in range(2,20)) for j in range(2)] for i in range(2)]
    for u in ((1,0),(0,1),(1,1),(1,-1)):
        work=sum(Fraction(u[i]*u[j])*(exact[i][j]-Fraction(float(shat[i,j]))) for i in range(2) for j in range(2))
        assert abs(work)<=Fraction(float(error))*sum(v*v for v in u)
    assert details[0]['physical_neighbours']==[0,1]
    assert np.array_equal(record['incidence_counts'],[1,1])
    assert record['assembly_gamma_original_block_count']==1
