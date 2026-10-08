"""Small assembly-only archive and independent matrix-action checks."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_attribution_evidence as evidence
import _b3_e4_f03_variational_attribution as attribution
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_independent_beam as beam


def _small_actions(family):
    mesh=(1,2,1,2)
    p=attribution.nested_q4_prolongation(*mesh[:3])
    qm=np.zeros(p.shape[1])
    coarse=shell.panel(1,2,'Q4')
    fine=shell.panel(2,4,'Q4')
    rng=np.random.default_rng(91)
    qm+=rng.normal(size=len(qm))*1e-5
    qm[np.r_[coarse.supported,coarse.dof_count+beam.root_dofs(1)]]=0.
    qf=np.asarray(p@qm).copy()
    qf[2*fine.n_s+2]+=2e-8  # An interior shell coordinate.
    rows=3*(2*mesh[3]+1+(2 if family=='enriched' else 0))
    lam=np.linspace(-1.,1.,rows)*1000
    metrics,actions=attribution.attribute_saved_states(
        *mesh,family,qm,qf,lam)
    return mesh,metrics,actions


@pytest.mark.parametrize('family',('P1','hybrid','enriched'))
def test_saved_operator_recomputation_and_owned_archive(tmp_path,family):
    mesh,original,actions=_small_actions(family)
    payload=evidence.pack_actions(actions,middle_mesh=mesh,family=family)
    archive=tmp_path/'actions.npz'
    np.savez_compressed(archive,**payload)
    recovered=evidence.unpack_actions(archive,middle_mesh=mesh,family=family)
    report=evidence.verify_actions(recovered,middle_mesh=mesh,family=family)
    checks=report['checks']
    assert set(checks)==set(evidence.LIMITS)
    for name in ('action_parity_scaled','support_preservation_max_abs',
                 'scaled_pullback_relative_fro','scaled_load_pullback_relative_inf',
                 'shell_energy_preservation_scaled','beam_energy_preservation_scaled',
                 'load_work_preservation_scaled','identity_defect_scaled',
                 'offgrid_field_scaled','offgrid_strain_scaled'):
        assert checks[name]<=evidence.LIMITS[name]
    assert checks['fine_free_equilibrium_scaled']>evidence.LIMITS[
        'fine_free_equilibrium_scaled']  # Unsolved artificial state.
    for name,value in report['attribution'].items():
        if name in original:
            if isinstance(value,(int,float)):
                assert value==pytest.approx(original[name],rel=1e-10,abs=1e-10)
            else:
                assert value==original[name]
    for name in ('P','K_coarse','K_fine','C_fine'):
        assert recovered[name] is not actions[name]
        difference=(recovered[name]-actions[name]).tocsr()
        assert np.max(np.abs(difference.data),initial=0.)<1e-12
    for name in evidence._VECTORS:
        assert recovered[name] is not actions[name]
        np.testing.assert_array_equal(recovered[name],actions[name])
    actions['q_middle'][0]=np.nan
    assert np.all(np.isfinite(recovered['q_middle']))
    payload['q_middle'][0]=np.nan
    assert np.all(np.isfinite(recovered['q_middle']))


def test_corruption_inventory_size_case_and_alias_rejected(tmp_path,monkeypatch):
    mesh,_,actions=_small_actions('P1')
    payload=evidence.pack_actions(actions,middle_mesh=mesh,family='P1')
    changed={name:value.copy() for name,value in payload.items()}
    changed['K_fine.data'][0]+=1.
    with pytest.raises(ValueError,match='digest'):
        evidence.unpack_actions(changed,middle_mesh=mesh,family='P1')
    changed={name:value.copy() for name,value in payload.items()}
    changed['P.indptr'][1]=-1
    changed['__digest']=evidence._digest({k:v for k,v in changed.items()
                                           if k!='__digest'})
    with pytest.raises(ValueError,match='CSR'):
        evidence.unpack_actions(changed,middle_mesh=mesh,family='P1')
    changed={name:value.copy() for name,value in payload.items()}
    changed['P.indptr']=changed['P.indptr'][:,None]
    changed['__digest']=evidence._digest({k:v for k,v in changed.items()
                                           if k!='__digest'})
    with pytest.raises(ValueError,match='CSR'):
        evidence.unpack_actions(changed,middle_mesh=mesh,family='P1')
    with pytest.raises(ValueError,match='case/schema'):
        evidence.unpack_actions(payload,middle_mesh=(2,2,1,2),family='P1')
    aliased=actions.copy(); aliased['q_fine']=aliased['prolonged_q']
    with pytest.raises(ValueError,match='aliased'):
        evidence.pack_actions(aliased,middle_mesh=mesh,family='P1')
    with pytest.raises(ValueError,match='inventory'):
        evidence.unpack_actions({**payload,'unexpected':np.array([1])},
                                middle_mesh=mesh,family='P1')
    archive=tmp_path/'actions.npz'
    np.savez_compressed(archive,**payload)
    monkeypatch.setattr(evidence,'MAX_UNCOMPRESSED_BYTES',1)
    def forbid_decompress(*args,**kwargs):
        raise AssertionError('decompressed before ZIP size preflight')
    monkeypatch.setattr(evidence.np,'load',forbid_decompress)
    with pytest.raises(ValueError,match='ZIP inventory or size'):
        evidence.unpack_actions(archive,middle_mesh=mesh,family='P1')


def test_verify_detects_saved_action_or_support_mutation():
    mesh,_,actions=_small_actions('hybrid')
    bad=actions.copy(); bad['prolonged_q']=bad['prolonged_q'].copy()
    bad['prolonged_q'][0]+=1e-5
    report=evidence.verify_actions(bad,middle_mesh=mesh,family='hybrid')
    assert report['checks']['action_parity_scaled']>evidence.LIMITS[
        'action_parity_scaled']
    assert report['checks']['support_preservation_max_abs']>0.
