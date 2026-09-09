"""Bounded saved-input experiment; raw historical arrays remain immutable."""
import json
from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases.ge_beam3_paired_mode_experiment import paired_expansion, experiment
from test_ge_beam3_schur_line_program import save

BASE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-returned-mode-capture-18845e1-20260908')
MANIFEST='63A4A9AAA366B87F24E33D21E530970C8096BE5711A5FC6EC4E5DA0087E546E6'


def test_low_expansion_not_discarded(tmp_path):
    high,low=paired_expansion(np.array([[1.,2.**-54],[1.,0.]]),np.ones((2,1)))
    assert np.array_equal(high,np.ones((2,1)))
    assert np.array_equal(low,np.array([[2.**-54],[0.]]))
    save(tmp_path/'paired-expansion.json',dict(high=high,low=low))


@pytest.mark.parametrize('index',(0,1))
def test_saved_modes(index,tmp_path):
    manifest_raw=(BASE/'archive-manifest.json').read_bytes()
    assert len(manifest_raw)==2013 and sha256(manifest_raw).hexdigest().upper()==MANIFEST
    manifest=json.loads(manifest_raw)
    paths=sorted((BASE/'runs/capture/pytest').rglob('prevalidation.json'))
    assert len(paths)==2
    path=paths[index];raw=path.read_bytes()
    assert [len(raw),sha256(raw).hexdigest().upper()]==manifest[path.relative_to(BASE).as_posix()]
    parsed=json.loads(raw)
    data={key:np.array(value) for key,value in parsed.items() if key!='failure'}
    before={key:value.tobytes() for key,value in data.items()}
    print(dict(stage='saved-factor-reorthogonalization',case=index),flush=True)
    result=experiment(data)
    save(tmp_path/'paired-diagnostic.json',result)
    print({name:{key:value for key,value in result[name].items() if key not in ('energy','kinetic_gram')}
           for name in ('paired','rounded_only')},flush=True)
    assert all(data[key].tobytes()==value for key,value in before.items())
    assert path.read_bytes()==raw
    assert result['eigenvalues'].tobytes()==data['values'].tobytes()
    assert result['paired']['mass_error']<=1e-11
    assert result['paired']['original_ritz_error']<=1e-11
    assert not result['production_qualified']
