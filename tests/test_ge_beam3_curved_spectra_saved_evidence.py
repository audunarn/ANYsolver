"""Read-only completed spectral artifact and kinetic-field inspection."""
from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_curved_reference_modes_probe as probe
from docs.reference_cases import ge_beam3_curved_reference_modes as comparison

ROOT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-curved-spectra-20260907-v2')
REVISION='a3c2e22156748dcca4f1b6269a707c8c32df828f'
SHA='f2966ad7afa6fcafb289b0ff72db7995d532fe5b1d65249ff235acd0e2ba64bf'


@pytest.fixture
def saved(monkeypatch):
    if not (ROOT/'comparison.json').is_file(): pytest.skip('External spectral development packets not installed')
    raw=probe.read(ROOT/'comparison.json'); assert sha256(raw).hexdigest()==SHA
    def forbidden(*args,**kwargs): raise AssertionError('no reference solve during evidence inspection')
    monkeypatch.setattr(comparison.ritz,'solve',forbidden)
    return raw,probe.validate(ROOT,raw,REVISION)


def test_reference_frequencies_and_mass_overlap_recompute_without_solves(saved):
    _,value=saved; _,refs=comparison.preserved_reference()
    for row in value['rows']:
        m=row['macros']; detail=probe.parse(probe.read(ROOT/f'modes-{m}.json'))
        for rule,key in ((4,'frozen_rule_field_comparison'),(16,'field_comparison')):
            regenerated=comparison.modal_overlap(m,detail['modes']['full_modes'],refs[-1],quadrature=rule)
            assert probe.canonical({k:v.tolist() for k,v in regenerated.items()})==probe.canonical(detail[key])
    rows=value['rows']
    errors=np.asarray([r['relative_frequency_errors'] for r in rows])
    assert np.all(errors[2]<errors[1]) and np.all(errors[1]<errors[0])
    assert max(rows[-1]['relative_frequency_errors'])<.02
    assert min(rows[-1]['diagonal_mac'])>.99
    assert value['new_reference_solves']==value['nonlinear_solves']==0 and not value['production_qualified']


@pytest.mark.parametrize('mutation',['summary','hash','checkpoint','native_modes','mass_field','reference','qualification','order'])
def test_spectral_evidence_mutations_reject(saved,tmp_path,mutation):
    _,value=saved
    for item in value['artifacts']: (tmp_path/item['path']).write_bytes((ROOT/item['path']).read_bytes())
    if mutation=='summary': value['rows'][0]['eigenvalues'][0]+=.1
    elif mutation=='hash': value['artifacts'][0]['sha256']='0'*64
    elif mutation=='qualification': value['production_qualified']=True
    elif mutation=='order': value['rows'].reverse()
    else:
        name={'checkpoint':'checkpoint-1.json','native_modes':'native-spectrum-1.json',
            'mass_field':'modes-1.json','reference':'reference-diagnostic.json'}[mutation]
        data=probe.parse(probe.read(tmp_path/name))
        if mutation=='checkpoint': data['completed_targets']=1
        if mutation=='native_modes': data['modes']['eigenvalues'][0]+=.1
        if mutation=='mass_field': data['field_comparison']['mac'][0][0]+=.1
        if mutation=='reference': data[0]['eigenvalues'][0]+=.1
        (tmp_path/name).write_bytes(probe.canonical(data))
    with pytest.raises(ValueError): probe.validate(tmp_path,probe.canonical(value),REVISION)
