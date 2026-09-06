"""Small numerical algebra tests, never a nonlinear beam/path execution."""

import ast
import copy
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_stability_inspection as inspect


def synthetic_state():
    """Synthetic reflection-invariant matrix, explicitly not mechanics evidence."""
    n=33
    matrix=np.diag(np.tile([2.,3.,4.,5.,6.,7.],n))
    x=np.column_stack((np.linspace(-1.,1.,n),np.zeros(n),np.zeros(n)))
    force=np.zeros((n,3));force[16,1]=-1.
    residual=np.zeros((n,6));residual[:,:3]=force
    row={'step':0,'crown_drop':.1,'load':1.,'current_load_slope':1.,'raw':{'sha256':'d'*64}}
    raw={'trial':{'assembly_trial':{'positions':x,'rotations':np.tile(np.eye(3),(n,1,1)),
              'forces':force,'response':{'residual':residual.ravel(),'tangent':matrix}}}}
    return row,raw


def test_polar_axial_reflection_split_and_scale():
    a=np.diag(np.arange(1.,19.))
    result=inspect.classify_matrix(a,nodes=3,span=2.)
    assert result['free_dimension']==6 and result['in_plane_dimension']==3
    assert np.array_equal(result['in_plane']['values'],[3.,7.,8.]) # rz/4, ux, uy
    assert np.array_equal(result['out_of_plane']['values'],[2.5,2.75,9.]) # rx/4, ry/4, uz
    assert result['reflection_error']==0 and result['full']['negative']==0
    mode=result['out_of_plane']['lowest_nodal_increment']
    assert np.count_nonzero(mode)==1 and mode[1,3]==.5
    assert np.count_nonzero(mode[[0,2]])==0


def test_numerical_inertia_is_congruence_invariant_without_mass_claim():
    a=np.eye(30);a[8,8]=-2.;a[11,11]=-3.
    for span in (.1,1.,2.,10.):
        result=inspect.classify_matrix(a,nodes=5,span=span)
        assert result['full']['negative']==2
        assert result['in_plane']['negative']==result['out_of_plane']['negative']==1
        assert result['full']['unresolved']==0


def test_near_zero_mode_is_unresolved_not_qualified_positive():
    result=inspect.spectral(np.diag([1.,1e-16,-1e-16,-2.]))
    assert (result['positive'],result['negative'],result['unresolved'])==(1,1,2)
    assert result['eigen_residual']<1e-11


@pytest.mark.parametrize('mutation',['coupling','asymmetry','nonfinite','dimension','size'])
def test_invalid_matrices_rejected(mutation):
    a=np.eye(18)
    if mutation=='coupling': a[6,8]=a[8,6]=.01
    if mutation=='asymmetry': a[6,7]=.01
    if mutation=='nonfinite': a[7,7]=np.nan
    if mutation=='dimension': a=np.eye(17)
    if mutation=='size':
        with pytest.raises(inspect.RefinementError): inspect.classify_matrix(np.eye(204),nodes=34)
        return
    with pytest.raises(inspect.RefinementError): inspect.classify_matrix(a,nodes=3)


def test_small_cross_block_contributes_to_uncertainty():
    a=np.eye(18);a[6,6]=a[8,8]=1e-13;a[6,8]=a[8,6]=1e-12
    result=inspect.classify_matrix(a,nodes=3)
    assert result['reflection_error']<1e-11 and result['coupling_norm']==1e-12
    assert result['in_plane']['unresolved']>=1 and result['out_of_plane']['unresolved']>=1


def test_loaded_equilibrium_subtracts_dead_force():
    row,raw=synthetic_state()
    result=inspect.inspect_state(row,raw)
    assert result['state_errors']['free_equilibrium']==0
    assert result['full']['positive']==186


@pytest.mark.parametrize('mutation',['equilibrium','planarity','frame','support','load','improper'])
def test_state_mutations_rejected(mutation):
    row,raw=synthetic_state();trial=raw['trial']['assembly_trial']
    if mutation=='equilibrium': trial['response']['residual'][10]+=.01
    if mutation=='planarity': trial['positions'][10,2]=.01
    if mutation=='frame': trial['rotations'][10,0,2]=.01
    if mutation=='support': trial['positions'][0,0]=0.
    if mutation=='load': trial['forces'][10,0]=.01
    if mutation=='improper': trial['rotations'][10]=-np.eye(3)
    with pytest.raises(inspect.RefinementError): inspect.inspect_state(row,raw)


def test_summary_preserves_lateral_instability_and_uncertainty():
    row,raw=synthetic_state();one=inspect.inspect_state(row,raw)
    records=[dict(copy.deepcopy(one),step=i) for i in range(8)]
    records[6]['in_plane']['negative']=1;records[7]['out_of_plane']['negative']=1
    summary=inspect.summarize(records)
    assert summary['first_in_plane_negative_step']==6
    assert summary['first_out_of_plane_negative_step']==7
    assert summary['disposition']=='SAMPLED_OUT_OF_PLANE_INSTABILITY_PRESENT'
    assert not summary['production_qualified'] and not summary['natural_frequencies_computed']
    records[0]['out_of_plane']['unresolved']=1
    assert inspect.summarize(records)['disposition']=='UNRESOLVED_SAMPLED_NUMERICAL_INERTIA'
    with pytest.raises(inspect.RefinementError): inspect.summarize(records[::-1])


def test_hash_guard_and_deadline_before_numpy_or_matrix_evaluation(monkeypatch,tmp_path):
    (tmp_path/'aggregate.json').write_bytes(b'{}\n')
    def forbidden(*args): raise AssertionError('matrix evaluation before authority')
    monkeypatch.setattr(inspect,'inspect_state',forbidden)
    with pytest.raises(inspect.RefinementError,match='hash'): inspect.inspect(tmp_path)
    with pytest.raises(inspect.RefinementError,match='deadline'): inspect.inspect(tmp_path,max_seconds=0)


def test_inspector_has_no_mechanics_imports():
    tree=ast.parse(Path(inspect.__file__).read_text())
    modules=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): modules.extend(a.name for a in node.names)
        if isinstance(node,ast.ImportFrom): modules.append(node.module)
    assert set(modules)=={'argparse','pathlib','time','numpy',
                         'docs.reference_cases.ge_beam3_curved_p5_arch_refinement_wave'}
    top=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert not any('numpy' in ast.unparse(n) for n in top)


def test_evidence_serialization_is_repeatable():
    row,raw=synthetic_state()
    assert inspect.canonical(inspect.inspect_state(row,raw))==inspect.canonical(inspect.inspect_state(row,raw))
