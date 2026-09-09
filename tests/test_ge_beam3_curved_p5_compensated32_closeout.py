"""Static inspection of the completed comparison; never reruns mechanics."""

from pathlib import Path
import pytest

from docs.reference_cases import ge_beam3_curved_p5_compensated32_diagnostic as d


ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-compensated32-20260906-530101a9fd6a4c1cbf864484571fc219')
FILES = {
    'diagnostic.json': (5854,'fc5e4f12b361c023b7b72c4f81aae0335770339f0c0374de931931a91c62d12f'),
    'inputs.json': (6024,'ef221acad6721d36bb02f8431f7619ac38772b8263742d6497d3de7ef15d5f41'),
    'compensated32/complete.json': (5967,'3fc422671ea4fd86f5f38f7f517f778213e9f35e5993e3be32f55ec7a2e06a66'),
    'compensated32/initial.json': (1159786,'10a13fd5ce0c5867fd86c87ebe4e7c10fe8d431122fefbe8cbc99acb3f62ca0f'),
    'compensated32/target.json': (1194913,'afc4d21eeacd3212f34a6cb2809f398510b079241aaadb0c624e048b9463db75'),
    'compensated32/process-start.json': (381,'a28b453438c43bed928622abc012718057a441101cf5452a52d48c1c5105cdad'),
    'compensated32/process.json': (100,'e8a016d13b99bf874af43846f814d67257f2c5f3e3e09affcdb6fdc81baafde6'),
    'compensated32/progress.jsonl': (5639,'d9a918428546f24ec4818646802a1f042382df46821149bd5751b942a29a8529'),
    'compensated32/stdout.log': (0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'compensated32/stderr.log': (0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
}


@pytest.fixture(scope='module')
def records():
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==set(FILES)
    for name,(size,sha) in FILES.items():
        data=d.shared.ordinary(ROOT/name)
        assert len(data)==size and d.shared.sha(data)==sha
    assert sum(size for size,_ in FILES.values())==2378664
    frozen=d.shared.load(ROOT/'inputs.json')['authority']
    assert frozen['commit']=='29b0d4e06ba4a1275411b3dd39b8843e6cb9c457'
    assert frozen['tree']=='8597be55bcb040b86d913f06b0034dba30ff4876'
    assert frozen['failed_inputs']==d.failed_inputs()
    assert frozen['observation_inputs']==d.observation_inputs()
    assert frozen['force_inputs']==d.force_inputs()
    assert frozen['centered_inputs']==d.centered_inputs()
    packet,groups=d.inspect(ROOT/'compensated32',frozen,'4d4cbecbbba445a4a9656976f1e2dee8',
        'c36880a0784e2b9224497a43829f60f00a299b82ece4f97d63aa86018a191acc')
    return packet,groups,d.shared.load(ROOT/'diagnostic.json'),d.shared.load(ROOT/'compensated32/target.json')


def test_actual_target_convergence_does_not_claim_qualification(records):
    packet,groups,diagnostic,target=records
    assert packet['result']['solver_outcome']==diagnostic['solver_outcome']=='TARGET_CONVERGED'
    assert diagnostic['disposition']=='RESEARCH_COMPENSATED_COORDINATE_COMPARISON_CAPTURED'
    assert packet['result']['production_qualified'] is diagnostic['production_qualified'] is False
    assert diagnostic['restriction']=='NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'
    assert {k:len(v) for k,v in groups.items()}=={'INITIAL':3,'TARGET':13}
    assert packet['result']['failure'] is None and packet['result']['failure_snapshot'] is False
    assert not (ROOT/'compensated32/failed_last.json').exists() and not (ROOT/'aggregate.json').exists()
    assert target['assembly']['residual_norm']==5.506791506773546e-12<=1e-11
    assert target['assembly']['iterations']==3 and target['assembly']['mixed_evaluations']==416


def test_accepted_coordinate_and_station_inventory_remains_bound(records):
    _,_,_,target=records;a=target['assembly']
    assert a['coordinate_schema']==d.COORDINATES
    assert len(a['positions'])==len(a['position_low'])==65
    assert a['positions'][32][1]==.095 and a['position_low'][32][1]==0.
    assert max(abs(v) for row in a['position_low'] for v in row)==5.540713562152415e-17
    assert len(a['response']['elements'])==32
    assert sum(len(e['stations']) for e in a['response']['elements'])==512
    assert sum(e['estimated_force_error'] for e in a['response']['elements'])<1e-12
    assert all(not s['response']['plastic_active'] for e in a['response']['elements'] for s in e['stations'])


def test_process_completed_within_resource_limits(records):
    process=d.shared.load(ROOT/'compensated32/process.json')
    assert process['exit_code']==0
    assert 0<process['wall_seconds']<600
    assert 0<process['cpu_100ns']/1e7<600
    assert 0<process['peak_tree_bytes']<24*(1<<30)
