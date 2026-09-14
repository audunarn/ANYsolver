"""Grouped formal history/prefix work unit; invoked only by the reviewed runner.

Grouping removes repeated interpreter setup.  Every prefix still creates a
fresh authenticated owner and genuinely continues the remaining command list.
This module never publishes an aggregate and is not a standalone authority.
"""
from hashlib import sha256
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ge_beam3_g3c_physical_history_owner as history

ASSIGNMENT=None
OUTPUT_DIRECTORY=None
INPUT_PACKETS=None
EXPECTED_RUNTIME_SHA256=None
COMMON_MANIFEST_PATH=None
COMMON_MANIFEST_BYTES=None
COMMON_MANIFEST_SHA256=None
FORMAL_SHARD_RECORD=None
p=history.packet


def exact(actual,expected):
    if type(actual)is not type(expected):return False
    if type(actual)is dict:
        return set(actual)==set(expected) and all(exact(actual[k],expected[k]) for k in actual)
    if type(actual)is list:
        return len(actual)==len(expected) and all(exact(a,b) for a,b in zip(actual,expected))
    return actual==expected


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode('ascii')


def packet(row):
    if type(row)is not dict or set(row)!={'path','bytes','sha256'}:raise ValueError('formal packet descriptor')
    path=Path(row['path'])
    if path.is_symlink() or not path.is_file() or not path.is_absolute():
        raise ValueError('formal packet regular file')
    raw=path.read_bytes()
    if type(row['bytes'])is not int or row['bytes']<=0 or len(raw)!=row['bytes']:
        raise ValueError('formal packet byte count')
    if type(row['sha256'])is not str or sha256(raw).hexdigest()!=row['sha256']:
        raise ValueError('formal packet hash')
    return raw


def store(raw,prefix):
    path=Path(OUTPUT_DIRECTORY)/f'prefix-{prefix:02d}.json'
    with path.open('xb')as stream:stream.write(raw)
    return dict(name=path.name,bytes=len(raw),sha256=sha256(raw).hexdigest(),prefix=prefix)


def registered_case(ordinal,row):
    matrix=history.history_matrix()
    if type(ordinal)is not int or type(ordinal)is bool or not 0<=ordinal<len(matrix):
        raise ValueError('formal case ordinal')
    if not exact(row,matrix[ordinal]):raise ValueError('formal case authority')
    if history.runtime_identity()!=EXPECTED_RUNTIME_SHA256:raise ValueError('formal runtime mismatch')
    return matrix[ordinal]


def common_identity():
    path=Path(COMMON_MANIFEST_PATH)
    if path.is_symlink() or not path.is_absolute() or not path.is_file():raise ValueError('formal common manifest file')
    raw=path.read_bytes()
    if (type(COMMON_MANIFEST_BYTES)is not int or type(COMMON_MANIFEST_BYTES)is bool
        or COMMON_MANIFEST_BYTES<=0 or len(raw)!=COMMON_MANIFEST_BYTES
        or type(COMMON_MANIFEST_SHA256)is not str or sha256(raw).hexdigest()!=COMMON_MANIFEST_SHA256):
        raise ValueError('formal common manifest identity')
    if history.runtime_identity()!=EXPECTED_RUNTIME_SHA256:raise ValueError('formal runtime changed')
    return COMMON_MANIFEST_SHA256


def accepted_transport(owner,row,final_raw):
    """Bind actual accepted diagnostics and independently expanded identities.

    Array-valued diagnostics stay external.  The formal evidence checker later
    compares them across the five registered variants; science retains hashes.
    """
    before=owner.checkpoint_bytes()
    if before!=final_raw:raise AssertionError('formal final owner mismatch')
    diagnostic=owner.accepted_pose_diagnostic_bytes()
    if owner.checkpoint_bytes()!=before:raise AssertionError('accepted diagnostic mutated owner')
    value=p.strict(diagnostic);state=p.strict(final_raw)['final_state']
    definition,expanded,programs=p.authorities()[1].expand_inert(
        row['graph'],row['variant'],row['common_motion'])
    if (value['kind']!='UNQUALIFIED_G3C_ACCEPTED_POSE_DIAGNOSTIC'
        or value['origin_sha256']!=p.digest(state)
        or value['state_committed']is not False
        or value['physical_recovery_complete']is not False
        or p.strict(final_raw)['definition']!=definition):
        raise AssertionError('accepted transport diagnostic authority')
    path=Path(OUTPUT_DIRECTORY)/'accepted-diagnostic.json'
    with path.open('xb')as stream:stream.write(diagnostic)
    return dict(accepted_diagnostic_sha256=sha256(diagnostic).hexdigest(),
        definition_sha256=p.digest(definition),expanded_sha256=p.digest(expanded),
        programs_sha256=p.digest(programs),final_state_sha256=p.digest(state),
        case_id=row['case_id'],graph=row['graph'],variant=row['variant'],
        force_scale=row['force_scale'],common_motion=row['common_motion'],
        immutable=True,passed=True)


def test_physical_formal_shard_assignment():
    global FORMAL_SHARD_RECORD
    if ASSIGNMENT is None:
        import pytest
        pytest.skip('formal shard requires reviewed runner lease')
    from test_ge_beam3_g3c_physical_owner import directional,native_checks
    if type(ASSIGNMENT)is not dict:raise ValueError('formal shard assignment')
    kind=ASSIGNMENT.get('kind');ordinal=ASSIGNMENT.get('case_ordinal')
    row=registered_case(ordinal,ASSIGNMENT.get('case'))
    commands=history.commands(row['common_motion'],row['force_scale'])
    if kind=='history-producer':
        if set(ASSIGNMENT)!={'kind','case_ordinal','case','history_assignment_index'}:
            raise ValueError('formal producer schema')
        if ASSIGNMENT['history_assignment_index']!=ordinal or INPUT_PACKETS!={}:raise ValueError('formal producer association')
        owner=history.HistoryOwner(row['graph'],row['variant'],row['common_motion'])
        raw=owner.checkpoint_bytes();previous=p.strict(raw)['final_state'];files=[store(raw,0)]
        directional_errors=None
        for index,command in enumerate(commands,1):
            if command['kind']=='LOAD_STAGE' and command['root_stage']==0:
                directional_errors=directional(owner,command)
            result=owner.solve(command);raw=owner.checkpoint_bytes();current=p.strict(raw)['final_state']
            if result['epoch']!=index:raise AssertionError('formal accepted epoch')
            import numpy as np
            if np.linalg.norm(result['residual'])>1e-11:raise AssertionError('formal accepted residual')
            if current['previous_sha256']!=p.digest(previous):raise AssertionError('formal state chain')
            native_checks(previous,current)
            diagnostic=p.strict(owner.accepted_pose_diagnostic_bytes())
            if (diagnostic['state_committed']is not False or diagnostic['origin_sha256']!=p.digest(current)
                or np.linalg.norm(diagnostic['residual'])>1e-11 or owner.checkpoint_bytes()!=raw):
                raise AssertionError('formal accepted-pose check')
            p.preflight(raw,sha256(raw).hexdigest(),expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
            files.append(store(raw,index));previous=current
            print('PHYSICAL FORMAL history',row['case_id'],index,flush=True)
        if directional_errors is None:raise AssertionError('formal directional probe')
        FORMAL_SHARD_RECORD=dict(kind=kind,case_ordinal=ordinal,
            history_assignment_index=ASSIGNMENT['history_assignment_index'],
            history=dict(kind='history',case_id=row['case_id'],events=row['accepted_stages'],
                directional_errors=directional_errors,packets=files,passed=True),
            transport=accepted_transport(owner,row,raw),passed=True)
        return
    if kind!='prefix-range':raise ValueError('formal shard kind')
    if set(ASSIGNMENT)!={'kind','case_ordinal','case','prefix_start','prefix_stop','assignment_indexes'}:
        raise ValueError('formal prefix-range schema')
    start=ASSIGNMENT['prefix_start'];stop=ASSIGNMENT['prefix_stop'];indexes=ASSIGNMENT['assignment_indexes']
    if (type(start)is not int or type(start)is bool or type(stop)is not int or type(stop)is bool
        or not 0<=start<stop<=row['accepted_stages']+1
        or type(indexes)is not list or len(indexes)!=stop-start
        or set(INPUT_PACKETS)!={f'prefix-{i:02d}' for i in range(start,stop)}|{'final'}):
        raise ValueError('formal prefix-range authority')
    expected_assignment=dict(kind='prefix-range',case_ordinal=ordinal,case=row,
        prefix_start=start,prefix_stop=stop,assignment_indexes=list(indexes))
    frozen_assignment_sha256=sha256(canonical(ASSIGNMENT)).hexdigest()
    final=packet(INPUT_PACKETS['final']);final_sha=sha256(final).hexdigest();records=[];fresh_owners=0
    for offset,prefix in enumerate(range(start,stop)):
        common_identity()
        if (sha256(canonical(ASSIGNMENT)).hexdigest()!=frozen_assignment_sha256
            or not exact(ASSIGNMENT,expected_assignment)):
            raise ValueError('formal prefix assignment changed')
        raw=packet(INPUT_PACKETS[f'prefix-{prefix:02d}']);digest=sha256(raw).hexdigest()
        parsed=p.preflight(raw,digest,expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        if parsed.epoch!=prefix:raise AssertionError('formal prefix epoch')
        owner=history.resume(raw,digest,expected_runtime_sha256=EXPECTED_RUNTIME_SHA256)
        fresh_owners+=1
        for command in commands[prefix:]:owner.solve(command)
        if owner.checkpoint_bytes()!=final:raise AssertionError('formal prefix continuation')
        records.append(dict(assignment_index=indexes[offset],record=dict(kind='prefix',
            case_id=row['case_id'],prefix=prefix,input_sha256=digest,
            final_sha256=final_sha,passed=True)))
        print('PHYSICAL FORMAL prefix',row['case_id'],prefix,flush=True)
        del owner
        common_identity()
        if (sha256(canonical(ASSIGNMENT)).hexdigest()!=frozen_assignment_sha256
            or not exact(ASSIGNMENT,expected_assignment)):
            raise ValueError('formal prefix assignment changed')
    FORMAL_SHARD_RECORD=dict(kind=kind,case_ordinal=ordinal,prefix_start=start,prefix_stop=stop,
        assignment_indexes=indexes,records=records,fresh_owners=fresh_owners,passed=True)
