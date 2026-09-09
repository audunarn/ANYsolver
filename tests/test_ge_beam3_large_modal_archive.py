"""The frozen path-map archive is not an older entries-format manifest."""
from hashlib import sha256
import json
import pytest
from docs.reference_cases import ge_beam3_large_modal_owned_worker as worker


def fixture(tmp_path,monkeypatch,mutation=None):
    payload=b'{"example":1}\n';name='first/plus/output/modes.json';target=tmp_path/name
    target.parent.mkdir(parents=True);target.write_bytes(payload)
    h=sha256(payload).hexdigest();monkeypatch.setitem(worker.MODES,'plus',h)
    data={name:{'bytes':len(payload),'sha256':h}}
    if mutation=='length':data[name]['bytes']+=1
    if mutation=='boolean':data[name]['bytes']=True
    if mutation=='unknown':data[name]['extra']=1
    if mutation=='member-hash':data[name]['sha256']='0'*64
    raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    if mutation=='duplicate':raw=raw.replace(b'"bytes":',b'"bytes":12,"bytes":')
    if mutation=='nonfinite':raw=raw.replace(b'"bytes":14',b'"bytes":NaN')
    if mutation=='newline':raw+=b'\n'
    (tmp_path/'manifest.json').write_bytes(raw)
    monkeypatch.setattr(worker,'MANIFEST','0'*64 if mutation=='manifest-hash' else sha256(raw).hexdigest())
    if mutation=='payload':target.write_bytes(b'{"example":2}\n')
    return payload


def test_valid_path_map_manifest(tmp_path,monkeypatch):
    expected=fixture(tmp_path,monkeypatch)
    assert worker.numerical_source('plus',tmp_path)==expected


@pytest.mark.parametrize('mutation',('length','boolean','unknown','member-hash','manifest-hash','duplicate','newline','payload'))
def test_archive_mutations_rejected(tmp_path,monkeypatch,mutation):
    fixture(tmp_path,monkeypatch,mutation)
    with pytest.raises(ValueError):worker.numerical_source('plus',tmp_path)


def test_nonfinite_rejected(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch)
    p=tmp_path/'manifest.json';raw=p.read_bytes().replace(b'"bytes":14',b'"bytes":NaN')
    assert b'NaN' in raw
    p.write_bytes(raw);monkeypatch.setattr(worker,'MANIFEST',sha256(raw).hexdigest())
    with pytest.raises(ValueError):worker.numerical_source('plus',tmp_path)


@pytest.mark.parametrize('sign',('plus','minus'))
def test_actual_frozen_numerical_archive(sign):
    assert sha256(worker.numerical_source(sign)).hexdigest()==worker.MODES[sign]
