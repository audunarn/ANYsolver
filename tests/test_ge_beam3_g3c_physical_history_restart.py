"""Fresh authenticated successor replay; assignment supplied by reviewed runner."""
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ge_beam3_g3c_physical_history_owner as history

ASSIGNMENT=None
OUTPUT_DIRECTORY=None
INPUT_PACKETS=None
EXPECTED_RUNTIME_SHA256=None
SCIENTIFIC_RECORDS=[]
p=history.packet


def input_packet(name):
    row=INPUT_PACKETS[name]
    if type(row)is not dict or set(row)!={'path','bytes','sha256'}:raise ValueError('packet authority schema')
    path=Path(row['path'])
    if path.is_symlink() or not path.is_file():raise ValueError('packet regular file required')
    raw=path.read_bytes()
    if type(row['bytes'])is not int or len(raw)!=row['bytes'] or sha256(raw).hexdigest()!=row['sha256']:
        raise ValueError('packet external hash mismatch')
    return raw,row['sha256']


def store(raw,prefix):
    path=Path(OUTPUT_DIRECTORY)/f'prefix-{prefix:02d}.json'
    with path.open('xb')as stream:stream.write(raw)
    return dict(name=path.name,bytes=len(raw),sha256=sha256(raw).hexdigest(),prefix=prefix)


def test_physical_history_assignment():
    import numpy as np
    from test_ge_beam3_g3c_physical_owner import directional,native_checks
    if ASSIGNMENT not in sum((history.work_inventory(lane)for lane in ('smoke','rehearsal','formal')),[]):
        raise ValueError('unregistered history assignment')
    if history.runtime_identity()!=EXPECTED_RUNTIME_SHA256:raise ValueError('lease runtime mismatch')
    row=ASSIGNMENT['case'];commands=history.commands(row['common_motion'],row['force_scale'])
    if ASSIGNMENT['kind']=='prefix':
        raw,digest=input_packet('prefix');final,_=input_packet('final')
        parsed=p.preflight(raw,digest,expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        value=p.strict(raw)
        assert parsed.epoch==ASSIGNMENT['prefix']
        assert value['definition']['fixture_id']==row['graph'] and value['definition']['variant']==row['variant']
        assert value['definition']['common_motion']==row['common_motion']
        owner=history.resume(raw,digest,expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        for command in commands[ASSIGNMENT['prefix']:]:owner.solve(command)
        assert owner.checkpoint_bytes()==final
        SCIENTIFIC_RECORDS.append(dict(kind='prefix',case_id=row['case_id'],prefix=ASSIGNMENT['prefix'],input_sha256=digest,final_sha256=sha256(final).hexdigest(),passed=True))
        return
    owner=history.HistoryOwner(row['graph'],row['variant'],row['common_motion'])
    raw=owner.checkpoint_bytes();previous=p.strict(raw)['final_state'];files=[store(raw,0)]
    directional_errors=None
    for index,command in enumerate(commands[:ASSIGNMENT['stages']],1):
        if command['kind']=='LOAD_STAGE' and command['root_stage']==0:
            directional_errors=directional(owner,command)
        result=owner.solve(command);raw=owner.checkpoint_bytes();current=p.strict(raw)['final_state']
        assert result['epoch']==index and np.linalg.norm(result['residual'])<=1e-11
        assert current['previous_sha256']==p.digest(previous)
        native_checks(previous,current)
        diagnostic=p.strict(owner.accepted_pose_diagnostic_bytes())
        assert diagnostic['state_committed']is False and diagnostic['origin_sha256']==p.digest(current)
        assert np.linalg.norm(diagnostic['residual'])<=1e-11 and owner.checkpoint_bytes()==raw
        p.preflight(raw,sha256(raw).hexdigest(),expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        files.append(store(raw,index));previous=current
        print('PHYSICAL HISTORY checkpoint',row['case_id'],index,flush=True)
    if directional_errors is None:raise AssertionError('missing registered KKT directional probe')
    SCIENTIFIC_RECORDS.append(dict(kind='history',case_id=row['case_id'],events=ASSIGNMENT['stages'],
        directional_errors=directional_errors,packets=files,passed=True))


def test_physical_preflight_guards():
    import pytest
    raw,digest=input_packet('origin');value=p.strict(raw);calls=[]
    def forbidden(*args,**kwargs):calls.append(True);raise AssertionError('numerical construction before preflight')
    attacks=[]
    old=p.strict(raw);old['schema']='GE_BEAM3_G3C_GRAPH_RESTART_V1';attacks.append(p.canonical(old))
    for target in ('definition','state','adapter'):
        altered=p.strict(raw)
        if target=='definition':altered['definition']['schema']='GE_BEAM3_G3C_GRAPH_DEFINITION_V1'
        elif target=='state':altered['final_state']['schema']='GE_BEAM3_G3C_MIXED_ELASTIC_STATE_V1'
        else:altered['final_state']['adapter_rows'][0]['schema']='GE_BEAM3_G3C_ADAPTER_ENVELOPE_V1'
        attacks.append(p.canonical(altered))
    with patch.object(history,'HistoryOwner',forbidden):
        for changed in attacks:
            with pytest.raises(ValueError):history.resume(changed,sha256(changed).hexdigest(),expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
    assert not calls
    SCIENTIFIC_RECORDS.append(dict(kind='successor_schema_negatives',input_sha256=digest,rejections=len(attacks),passed=True))


def test_physical_mutation_assignment():
    import ge_beam3_g3c_rehearsal_mutations as mutations
    import ge_beam3_g3c_rehearsal_contract as inherited
    raw,digest=input_packet('origin');probe=ASSIGNMENT
    if probe not in inherited.expected()['mutation_probes']:raise ValueError('unregistered mutation assignment')
    if probe['category']=='R10_NORMAL_SOURCE' or probe['member']=='changed_implementation_review':
        raise ValueError('source/review probes require shared-runner authority lane')
    changed,receipt=mutations.packet_attack(raw,probe['category'],probe['member'])
    # Preserve the actual inherited attack, but enforce successor admission.
    # Old identities now fail before all construction; beam candidate bytes
    # cannot stand in for a material state because these operators are elastic.
    if probe['category']=='R06_OLD_SCHEMA' or (probe['category'],probe['member'])==('R08_POLICY_FIXTURE','wrong_owner_policy'):
        receipt['expected_error']='physical successor checkpoint required before construction'
    if (probe['category'],probe['member'])==('R03_UNKNOWN_KEYS','adapter'):
        receipt['expected_error']='exact adapter_'+p.strict(raw)['final_state']['adapter_rows'][0]['family']+' schema'
    if (probe['category'],probe['member'])==('R23_ADAPTER_DIAGNOSTIC','candidate_sha'):
        receipt['expected_error']='beam material candidate must be null'
        receipt['rejection']='PREFLIGHT_BEFORE_CONSTRUCTION'
    assert changed!=raw
    calls=[]
    def forbidden(*args,**kwargs):calls.append(True);raise AssertionError('preflight constructed owner')
    def execute():
        try:history.resume(changed,receipt['after_sha256'],expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        except ValueError as error:
            assert str(error)==receipt['expected_error'],(str(error),receipt['expected_error'])
        else:raise AssertionError('mutation accepted')
    if receipt['rejection']=='PREFLIGHT_BEFORE_CONSTRUCTION':
        with patch.object(history,'HistoryOwner',forbidden):execute()
    else:
        p.preflight(changed,receipt['after_sha256'],expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        execute()
    assert not calls
    SCIENTIFIC_RECORDS.append(dict(kind='mutation',assignment=probe,input_sha256=digest,receipt=receipt,passed=True))
