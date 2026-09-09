"""Complete small rehearsal and read-only mutation checks; no qualification."""
from copy import deepcopy
from hashlib import sha256
import json
import pytest
from docs.reference_cases import ge_beam3_dead_line_comparison as compare
from docs.reference_cases import ge_beam3_dead_line_probe as probe
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical


@pytest.fixture(scope='module')
def rehearsal(tmp_path_factory):
    root=tmp_path_factory.mktemp('dead-line-rehearsal'); events=[]
    def save(name,raw):
        with (root/name).open('xb') as stream: stream.write(raw)
    rows,detail=compare.build(save,events.append)
    save('fields-diagnostic.json',canonical(detail))
    packets={m:json.loads((root/f'checkpoint-{m}.json').read_bytes()) for m in compare.MACROS}
    save('rows.json',canonical(rows))
    return root,rows,detail,packets,events


def test_complete_small_reference_and_native_rehearsal(rehearsal):
    root,rows,detail,packets,events=rehearsal
    assert [(r['macros'],r['target']) for r in rows]==[(m,t) for m in (1,2,4) for t in (.25,.5,1.)]
    assert len(detail['references'])==6 and len(rows)==9
    assert sum(r['metrics']['stations'] for r in rows)==168
    assert all(max(packet['records'][-1]['metrics'])<=1e-11 for packet in packets.values())
    assert [e['macros'] for e in events if e['stage']=='NATIVE']==[1,2,4]
    summary=probe.summary(root,'0'*40)
    assert canonical(summary['rows'])==canonical(rows)
    assert summary['production_qualified'] is False and summary['independent_review']=='PENDING'
    assert len(summary['artifacts'])==8


@pytest.mark.parametrize('mutation',['force','section','profile','reference_residual','recovery','location','ordering','load_axes','load_measure','internal_work','targets'])
def test_mutations_rejected_even_when_checkpoint_seal_is_recomputed(rehearsal,mutation):
    _,_,detail,packets,_=rehearsal
    detail=deepcopy(detail); packets=deepcopy(packets)
    if mutation=='force': detail['references'][0]['value']['force'][0]+=.01
    if mutation=='section': detail['references'][0]['value']['section'][0][0]+=.01
    if mutation=='profile': detail['references'][0]['value']['profile']='BVP9'
    if mutation=='reference_residual': detail['references'][0]['value']['differential_error']=.1
    if mutation=='recovery': detail['recoveries'][0]['fields'][0]['stations'][0]['strain'][0]+=.01
    if mutation=='location': detail['recoveries'][0]['locations'][0]+=.001
    if mutation=='ordering': detail['recoveries'].reverse()
    if mutation=='load_axes': packets[1]['program']['line_forces']['axes']='FOLLOWER'
    if mutation=='load_measure': packets[1]['program']['line_forces']['measure']='CURRENT_ARCLENGTH'
    if mutation=='internal_work': packets[1]['program']['line_forces']['internal_load_work_retained']=False
    if mutation=='targets': packets[1]['program']['targets'][0]=.2
    for packet in packets.values():
        packet['checkpoint_sha256']=sha256(canonical({k:v for k,v in packet.items() if k!='checkpoint_sha256'})).hexdigest()
    with pytest.raises(ValueError): compare.recompute(detail,packets)


def test_summary_rejects_missing_raw_failure_or_reference_change(rehearsal,tmp_path):
    root,_,_,_,_=rehearsal
    for name in probe.ARTIFACTS: (tmp_path/name).write_bytes((root/name).read_bytes())
    (tmp_path/'native-status-1.json').write_bytes(canonical(dict(status='failed',failure='test')))
    with pytest.raises(ValueError): probe.summary(tmp_path,'0'*40)
    (tmp_path/'native-status-1.json').write_bytes((root/'native-status-1.json').read_bytes())
    (tmp_path/'reference-diagnostic.json').write_bytes(canonical([]))
    with pytest.raises(ValueError): probe.summary(tmp_path,'0'*40)
