"""Read-only completed evidence checks; no mechanics or eigensolves rerun."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_loaded_arch_spectra_probe as probe

OUTPUT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-loaded-spectra-20260907-v2')
OLD=OUTPUT.with_name('ge-beam3-loaded-spectra-20260907-v1')
REVISION='1a3c4cc6cfb26ac3412b1f03a94bf657f4c27bf0'
SHA='c0a4a321eeba0de537282b4f20c951bf4678c9c50143663562b223eb8e7eca54'


@pytest.fixture
def saved():
    if not OUTPUT.exists(): pytest.skip('external development evidence unavailable')
    raw=(OUTPUT/'comparison.json').read_bytes()
    assert len(raw)==3689 and sha256(raw).hexdigest()==SHA
    return raw,probe.validate(OUTPUT,raw,REVISION)


def test_complete_hash_dag_and_committed_copy(saved):
    raw,value=saved
    assert (probe.ROOT/'docs/reference_cases/ge_beam3_loaded_spectra_development_result.json').read_bytes()==raw
    assert value['native_nonlinear_solves']==0 and value['new_native_spectra']==2
    assert len(value['artifacts'])==11 and not value['production_qualified']


def test_failed_run_common_artifacts_unchanged(saved):
    _,value=saved
    common=[a['path'] for a in value['artifacts'] if a['path']!='native-4.json']
    assert len(common)==10
    for name in common: assert (OLD/name).read_bytes()==(OUTPUT/name).read_bytes()
    assert not (OLD/'comparison.json').exists() and not (OLD/'comparison.pending.json').exists()
    assert not (OLD/'native-4.json').exists()


def test_signed_stability_not_accuracy_qualification(saved):
    _,value=saved
    first,last=value['rows']
    assert first['native_negative_modes']==first['continuum_negative_modes']==0
    assert last['native_negative_modes']==last['continuum_negative_modes']==2
    assert first['continuum_load_slope']>0>last['continuum_load_slope']
    assert max(last['eigenvalue_relative_errors'])>.2  # openly retain coarse discrepancy
    assert value['buckling_factor_authorized'] is False and value['independent_review']=='PENDING'


def test_reference_matrices_and_spectral_residuals(saved):
    for cursor in (1,4):
        for degree in (12,16):
            p=probe.parse(probe.read(OUTPUT/f'ritz-{cursor}-{degree}.json'))
            h=np.asarray(p['stiffness']); m=np.asarray(p['mass']); v=np.asarray(p['modes']); lam=np.asarray(p['eigenvalues'])
            assert np.array_equal(h,h.T) and np.array_equal(m,m.T)
            assert np.linalg.norm(v.T@m@v-np.eye(6))<1e-8
            material=np.asarray(p['material']); geometric=np.asarray(p['geometric'])
            scale=np.maximum(1.,np.maximum(np.linalg.norm(material@v,axis=0),
                np.maximum(np.linalg.norm(geometric@v,axis=0),np.linalg.norm((m@v)*lam,axis=0))))
            assert np.max(np.linalg.norm(h@v-(m@v)*lam,axis=0)/scale)<1e-8


@pytest.mark.parametrize('mutation',['status','revision','qualification','buckling','input','artifact','negative','eigenvalue'])
def test_mutated_summary_cannot_validate(saved,mutation):
    value=deepcopy(saved[1])
    if mutation=='status': value['status']='PASS'
    elif mutation=='revision': value['revision']='0'*40
    elif mutation=='qualification': value['production_qualified']=True
    elif mutation=='buckling': value['buckling_factor_authorized']=True
    elif mutation=='input': value['input_sha256']='0'*64
    elif mutation=='artifact': value['artifacts'][0]['sha256']='0'*64
    elif mutation=='negative': value['rows'][1]['native_negative_modes']=0
    else: value['rows'][0]['native_eigenvalues'][0]+=1.
    with pytest.raises(ValueError): probe.validate(OUTPUT,probe.canonical(value),REVISION)


def test_mutated_raw_packet_hash_is_rejected(saved,monkeypatch):
    original=probe.read
    def read(path):
        raw=original(path)
        if path.name=='native-4.json':
            value=probe.parse(raw); value['modes']['eigenvalues'][0]+=1.; return probe.canonical(value)
        return raw
    monkeypatch.setattr(probe,'read',read)
    with pytest.raises(ValueError,match='hash DAG'): probe.validate(OUTPUT,saved[0],REVISION)
