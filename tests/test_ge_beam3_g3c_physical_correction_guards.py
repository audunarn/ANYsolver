"""Correction-only replay guards for immutable predecessor packets."""
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ge_beam3_g3c_physical_history_owner as history

ASSIGNMENT=None
INPUT_PACKETS=None
EXPECTED_RUNTIME_SHA256=None
RUNTIME_COMPATIBILITY=None
SCIENTIFIC_RECORDS=[]
p=history.packet


def input_packet():
    row=INPUT_PACKETS['origin']
    if type(row)is not dict or set(row)!={'path','bytes','sha256'}:raise ValueError('packet authority schema')
    path=Path(row['path'])
    if path.is_symlink() or not path.is_file():raise ValueError('packet regular file required')
    raw=path.read_bytes()
    if type(row['bytes'])is not int or len(raw)!=row['bytes'] or sha256(raw).hexdigest()!=row['sha256']:
        raise ValueError('packet external hash mismatch')
    return raw,row['sha256']


def compatible_resume(raw,digest):
    return history.resume(raw,digest,expected_runtime_sha256=EXPECTED_RUNTIME_SHA256,
                          runtime_compatibility=RUNTIME_COMPATIBILITY)


def test_physical_correction_preflight_guards():
    import pytest
    raw,digest=input_packet();calls=[]
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
            with pytest.raises(ValueError):compatible_resume(changed,sha256(changed).hexdigest())
    assert not calls
    SCIENTIFIC_RECORDS.append(dict(kind='successor_schema_negatives',input_sha256=digest,
                                   rejections=len(attacks),passed=True))


def test_physical_correction_mutation_assignment():
    import ge_beam3_g3c_rehearsal_mutations as mutations
    import ge_beam3_g3c_rehearsal_contract as inherited
    raw,digest=input_packet();probe=ASSIGNMENT
    if probe not in inherited.expected()['mutation_probes']:raise ValueError('unregistered mutation assignment')
    if probe['category']=='R10_NORMAL_SOURCE' or probe['member']=='changed_implementation_review':
        raise ValueError('source/review probes require shared-runner authority lane')
    changed,receipt=mutations.packet_attack(raw,probe['category'],probe['member'])
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
        try:compatible_resume(changed,receipt['after_sha256'])
        except ValueError as error:assert str(error)==receipt['expected_error'],(str(error),receipt['expected_error'])
        else:raise AssertionError('mutation accepted')
    if receipt['rejection']=='PREFLIGHT_BEFORE_CONSTRUCTION':
        with patch.object(history,'HistoryOwner',forbidden):execute()
    else:
        p.preflight(changed,receipt['after_sha256'],expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        execute()
    assert not calls
    SCIENTIFIC_RECORDS.append(dict(kind='mutation',assignment=probe,input_sha256=digest,
                                   receipt=receipt,passed=True))


def test_runtime_compatibility_negatives():
    """Inert exact-token guards; no packet or numerical owner is constructed."""
    import copy
    current=history.runtime_identity();base=RUNTIME_COMPATIBILITY
    history.validate_runtime_compatibility(base,EXPECTED_RUNTIME_SHA256,current)
    attacks=[]
    edits=(('predecessor','runtime_sha256','0'*64),('successor','commit','0'*40),
           ('successor','tree','0'*40),('successor','runtime_sha256','0'*64),
           ('successor','review_sha256','0'*64))
    for field,key,replacement in edits:
        changed=copy.deepcopy(base);changed[field][key]=replacement
        changed['self_sha256']=p.digest({k:v for k,v in changed.items()if k!='self_sha256'});attacks.append(changed)
    for key,replacement in (('mode','FOREIGN'),('unchanged_inputs_sha256','0'*64),
                            ('partition_recovery_sha256','0'*64),
                            ('partition_recovery_review_sha256','0'*64),
                            ('guard_segment_manifest_sha256','0'*64),
                            ('allowed_changed_paths',base['allowed_changed_paths'][:-1])):
        changed=copy.deepcopy(base);changed[key]=replacement
        changed['self_sha256']=p.digest({k:v for k,v in changed.items()if k!='self_sha256'});attacks.append(changed)
    changed=copy.deepcopy(base);changed['self_sha256']='0'*64;attacks.append(changed)
    for value in attacks:
        try:history.validate_runtime_compatibility(value,EXPECTED_RUNTIME_SHA256,current)
        except ValueError:pass
        else:raise AssertionError('runtime compatibility mutation accepted')
    SCIENTIFIC_RECORDS.append(dict(kind='runtime_compatibility_negatives',rejections=len(attacks),passed=True))


def test_runtime_compatibility_positive():
    """One real predecessor packet is replayed under the captured successor lease."""
    raw,digest=input_packet();before=bytes(raw)
    owner=compatible_resume(raw,digest);replayed=owner.checkpoint_bytes()
    assert raw==before and replayed!=raw
    assert history.compatible_checkpoint_equal(raw,replayed,EXPECTED_RUNTIME_SHA256,history.runtime_identity())
    SCIENTIFIC_RECORDS.append(dict(kind='runtime_compatibility_positive',input_sha256=digest,
        predecessor_runtime_sha256=EXPECTED_RUNTIME_SHA256,
        successor_runtime_sha256=history.runtime_identity(),
        replay_sha256=sha256(replayed).hexdigest(),passed=True))
