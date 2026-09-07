"""Inspect preserved packets without new native or continuum solves."""
from hashlib import sha256
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_curved_moment_probe as probe
from docs.reference_cases import ge_beam3_curved_moment_reference as reference

EXTERNAL=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-curved-moment-20260907-v1')
REVISION='05beb51cb1da177b3b474d19b132719811f5c43e'
DIGEST='8e128fc1bcefbbbf06735ff40894b1afc41fcc00b70d8674dca436d34f016b43'


@pytest.fixture
def saved(monkeypatch):
    if not (EXTERNAL/'comparison.json').is_file():
        pytest.skip('External development packet unavailable; not qualification')
    raw=probe.read(EXTERNAL/'comparison.json')
    assert sha256(raw).hexdigest()==DIGEST
    data=probe.parse(raw)
    assert data['revision']==REVISION
    for item in data['artifacts']:
        packet=probe.read(EXTERNAL/item['path'])
        assert len(packet)==item['bytes'] and sha256(packet).hexdigest()==item['sha256']
    def forbidden(*args,**kwargs): raise AssertionError('new continuum solve forbidden during inspection')
    monkeypatch.setattr(reference,'solve',forbidden)
    return raw,data


def test_saved_summary_recomputes_all_nine_records_without_solves(saved):
    raw,data=saved
    assert probe.canonical(probe.summary(EXTERNAL,REVISION))==raw
    assert sum(row['metrics']['stations'] for row in data['rows'])==168
    assert not data['production_qualified'] and not data['conservative_spectral_authority']
    for target in (.25,.5,1.):
        rows=[r['metrics'] for r in data['rows'] if r['target']==target]
        for key in ('nodal_position_max_absolute_error','nodal_frame_max_absolute_error',
                'strain_energy_norm_relative_error','integrated_energy_relative_error',
                'recovered_frame_max_absolute_error','spatial_force_max_absolute_error','spatial_moment_max_relative_error'):
            assert rows[2][key]<rows[1][key]<rows[0][key]


@pytest.mark.parametrize('mutation',['field','input','reference','order','checkpoint','status','summary'])
def test_saved_packet_mutations_cannot_reproduce_accepted_summary(saved,tmp_path,mutation):
    raw,data=saved
    for item in data['artifacts']:
        (tmp_path/item['path']).write_bytes((EXTERNAL/item['path']).read_bytes())
    name='fields-diagnostic.json'
    if mutation=='checkpoint': name='checkpoint-1.json'
    if mutation=='status': name='native-status-1.json'
    changed=probe.parse(probe.read(tmp_path/name))
    if mutation=='field': changed['recoveries'][0]['fields'][0]['stations'][0]['strain'][0]+=.1
    if mutation=='input': changed['references'][0]['value']['section'][0][0]+=.1
    if mutation=='reference': changed['references'][0]['value']['positions'][0][0]+=.1
    if mutation=='order': changed['recoveries'].reverse()
    if mutation=='checkpoint': changed['records'][0]['metrics'][0]=.1
    if mutation=='status': changed['status']='failed'
    if mutation=='summary':
        data['rows'][0]['metrics']['native_integrated_energy']+=.1
        raw=probe.canonical(data)
    (tmp_path/name).write_bytes(probe.canonical(changed))
    try:
        result=probe.canonical(probe.summary(tmp_path,REVISION))
    except ValueError:
        return
    assert result!=raw
