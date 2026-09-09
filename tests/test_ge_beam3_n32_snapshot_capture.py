import ast
from pathlib import Path
import pytest
from docs.reference_cases import ge_beam3_n32_snapshot_capture as worker
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes

@pytest.mark.parametrize('sign',('plus','minus'))
def test_preserved_issued_prefixes(sign):
    inputs,v=worker.sources(sign)
    assert set(inputs)=={'seed-input.json','checkpoint.json','recovery.json'}
    assert len(v['operators'])==32 and strict_bytes(inputs['checkpoint.json'])['records']==[]

def test_archive_manifest_and_sign_reject(tmp_path):
    (tmp_path/'manifest.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='manifest'):worker.sources('plus',tmp_path)
    with pytest.raises(ValueError,match='sign'):worker.sources('unknown',tmp_path)

def test_positive_equivalence_and_mutation():
    raw=worker.member(worker.ARCHIVE,worker.MANIFEST,'wave/plus-a/output/packet.json',worker.POSITIVE_PACKET)
    p=strict_bytes(raw)['packet'];assert len(worker.positive_equivalence(p))==64
    p['completed_targets']=1
    with pytest.raises(ValueError,match='packet changed'):worker.positive_equivalence(p)

def test_capture_has_no_solve_or_owner_context_and_explicit_policy():
    tree=ast.parse(Path(worker.__file__).read_text())
    calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call)]
    attributes=[x.func.attr for x in calls if isinstance(x.func,ast.Attribute)]
    assert 'Context' not in attributes and not any(x=='solve' or x.startswith('solve_') for x in attributes)
    prepares=[x for x in calls if isinstance(x.func,ast.Attribute) and x.func.attr=='prepare']
    assert len(prepares)==1
    assert any(k.arg=='compliance_guard_policy' and isinstance(k.value,ast.Name) and k.value.id=='GUARD_POLICY' for k in prepares[0].keywords)
