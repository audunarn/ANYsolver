"""N24 external authority and coordinate-adapter tests, no scientific solve."""
from hashlib import sha256
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_spatial_seed24 as seed
from docs.reference_cases import ge_beam3_spatial_compare24 as compare

def test_original_n24_onset_hash():
    raw=seed.source_bytes();assert len(raw)==518339 and sha256(raw).hexdigest()==seed.SOURCE_SHA

def test_changed_onset_manifest(tmp_path):
    (tmp_path/'archive-manifest.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='manifest'):seed.source_bytes(tmp_path)

@pytest.mark.parametrize('case',tuple(compare.HASHES))
def test_coarse_reference_hashes(case):
    raw,value=compare.coarse(case)
    assert sha256(raw).hexdigest()==compare.HASHES[case] and value['case']==case

@pytest.mark.parametrize('cell',(1,6,12,13,18,24))
def test_n24_location_in_correct_macrocell(cell):
    assert compare.location(cell,0.)==pytest.approx(-1.+(2*cell-1)/24.,abs=1e-15)
    for xi in (-.9,-.1,.1,.9):
        value=compare.location(cell,xi)
        assert -1.+(cell-1)/12.<value<-1.+cell/12.

@pytest.mark.parametrize('cell,xi',((0,0.),(25,0.),(True,0.),(1,-1.),(24,1.),(1,0),(1,float('nan')),(1,float('inf'))))
def test_invalid_station_identity(cell,xi):
    with pytest.raises(ValueError):compare.location(cell,xi)

def test_compare_rejects_bad_input_hash(tmp_path):
    p=tmp_path/'packet.json';p.write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='hash'):compare.fields('endpoint',p,'0'*64)
