"""Initializer authority/admission tests, not spatial mechanics evidence."""
import pytest
from docs.reference_cases import ge_beam3_spatial_equilibrium_probe as p

@pytest.mark.parametrize('value',(.003,-.003,.006,-.006))
def test_registered_amplitudes(value):assert p.amplitude(value)==value

@pytest.mark.parametrize('value',(0.,True,1,float('nan'),float('inf'),.01))
def test_unregistered_amplitudes(value):
    with pytest.raises(ValueError):p.amplitude(value)

def test_source_exact_hash_bound():
    raw=p.source_bytes();assert len(raw)==432367 and p.sha256(raw).hexdigest()==p.SOURCE_SHA

def test_changed_manifest_rejected(tmp_path):
    (tmp_path/'archive-manifest.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='manifest'):p.source_bytes(tmp_path)

def test_no_invented_history():
    p.require_elastic(({'plastic':[0.,0.]},),({'plastic':[0.,0.]},))
    with pytest.raises(ValueError,match='history'):
        p.require_elastic(({'plastic':[.1,0.]},),({'plastic':[0.,0.]},))
