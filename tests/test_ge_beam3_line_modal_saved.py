"""Read-only closeout inspection: no nonlinear solve or eigensolve."""
from hashlib import sha256
from pathlib import Path
import subprocess
import pytest
from docs.reference_cases import ge_beam3_line_modal_comparison as comparison

ROOT=Path(__file__).resolve().parents[1]
EXTERNAL=comparison.BASE/'ge-beam3-line-modal-20260907-bc0ec7a'
REVISION='bc0ec7a9295a680563e67f363aeb451042840c49'
RESULT=ROOT/'docs/reference_cases/ge_beam3_line_modal_development_result.json'


def test_canonical_result_exactly_recomputes_without_new_solves(monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('closeout cannot run a solver')
    monkeypatch.setattr(comparison.equilibrium,'solve',forbidden)
    monkeypatch.setattr(comparison.modal,'solve',forbidden)
    raw=RESULT.read_bytes()
    assert len(raw)==5432 and sha256(raw).hexdigest()=='3598e9192722c5a1da21eb2e20d8a49e36d37b9f1e0767c0ae01359e794602eb'
    assert raw==(EXTERNAL/'comparison.json').read_bytes()==(EXTERNAL/'comparison.pending.json').read_bytes()
    assert raw==comparison.canonical(comparison.summary(EXTERNAL,REVISION))


@pytest.mark.parametrize('macros',[1,2,4])
def test_frozen_native_packets_remain_unchanged(macros):
    result=comparison.parse(RESULT.read_bytes())
    for name in (f'checkpoint-{macros}.json',f'native-{macros}.json'):
        path,size,digest=comparison.INPUTS[name]
        raw=(comparison.BASE/path).read_bytes()
        assert len(raw)==size and sha256(raw).hexdigest()==digest
        assert raw==(EXTERNAL/name).read_bytes()
    row=next(r for r in result['rows'] if r['macros']==macros)
    assert len(row['relative_frequency_errors'])==6
    assert row['native_negative_modes']==row['reference_negative_modes']==0
    assert row['reference_resolution_error']<1e-7


def test_research_extent_and_unqualified_scope():
    result=comparison.parse(RESULT.read_bytes())
    assert result['new_native_spectra']==result['new_native_nonlinear_solves']==0
    assert result['status']=='DEVELOPMENT_MODAL_COMPARISON_NOT_QUALIFICATION'
    assert result['independent_review']=='PENDING'
    assert not result['production_qualified'] and not result['buckling_factor_authorized']
    assert not result['clustered_mac_qualification']
    changed=subprocess.check_output(['git','diff','--name-only','f19d7d40e46f1c8bdb641de40d972e0cebb53d70','--'],cwd=ROOT,text=True,timeout=10).splitlines()
    assert changed and all(p.startswith(('docs/','tests/')) for p in changed)
