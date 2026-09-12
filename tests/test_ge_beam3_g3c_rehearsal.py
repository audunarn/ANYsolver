"""Authentic numerical tests: reviewed bounded runner supplies the only context."""
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ge_beam3_g3c_history_owner as history
import ge_beam3_g3c_rehearsal_mutations as mutations
import ge_beam3_g3c_rehearsal_packets as packets
import run_ge_beam3_g3c_rehearsal as runner
from test_ge_beam3_g3c_history_smoke import native_stage

p=history.packet


def history_run(context):
    row=context['assignment']['case']; out=context['out']; lease=context['lease']
    owner=history.HistoryOwner(row['graph'],row['variant'],row['common_motion'])
    _,source=p.authorities(); graph=source.expand(row['graph'],row['variant'],row['common_motion'])[1]['graph']
    raw=owner.checkpoint_bytes(); previous=p.strict(raw)['final_state']
    rows=[packets.store(out/'packets',raw,row['case_id'],0,lease['runtime_sha256'])]
    commands=mutations.design.inherited.commands(row['common_motion'],row['force_scale'])
    for index,command in enumerate(commands,1):
        result=owner.solve(command); raw=owner.checkpoint_bytes(); current=p.strict(raw)['final_state']
        assert result['epoch']==index and np.linalg.norm(result['residual'])<=1e-11
        assert current['previous_sha256']==p.digest(previous)
        native_stage(previous,current,graph)
        diagnostic=p.strict(owner.accepted_pose_diagnostic_bytes())
        assert diagnostic['state_committed'] is False and diagnostic['origin_sha256']==p.digest(current)
        assert np.linalg.norm(diagnostic['residual'])<=1e-11
        assert owner.checkpoint_bytes()==raw
        rows.append(packets.store(out/'packets',raw,row['case_id'],index,lease['runtime_sha256']))
        previous=current
        print('G3C CHECKPOINT stored authentic prefix '+str(index),flush=True)
    value=packets.manifest(p.digest(lease),row['case_id'],row['accepted_stages'],lease['runtime_sha256'],rows)
    packets.verify_directory(out/'packets',value,p.digest(lease),row['case_id'],row['accepted_stages'],lease['runtime_sha256'])
    packets.exclusive(out/'artifacts.json',p.canonical(value))


def expected_rejection(call,expected):
    try: call()
    except ValueError as error:
        assert str(error)==expected, ('wrong rejection',str(error),expected)
        return
    raise AssertionError('mutation was accepted')


def negative_run(context):
    raw,digest=context['origin']; lease=context['lease']; out=context['out']; assignment=context['assignment']
    runtime=lease['runtime_sha256']; files={}; results=[]
    def save(name,data):
        packets.exclusive(out/'packets'/name,data); files[name]=packets.fingerprint(data)
    if assignment['kind']=='positive':
        restored=history.resume(raw,digest,expected_runtime_sha256=runtime)
        assert restored.checkpoint_bytes()==raw
        save('positive-replay.json',restored.checkpoint_bytes())
        results.append(dict(passed=True,kind='GENUINE_ORIGIN_REPLAY',origin=assignment['origin'],input_sha256=digest))
    for index,probe in enumerate(assignment['probes']):
        category,member=probe['category'],probe['member']; phase=probe['rejection']
        calls=[]
        def forbidden(*args,**kwargs): calls.append(True); raise AssertionError('preflight constructed an owner')
        if category=='R10_NORMAL_SOURCE':
            _,source=p.authorities()
            target=p.ROOT/(p.DEFINITION if member=='mocked_source_hash' else 'docs/reference_cases/ge_beam3_g3c_fixtures_v1.json')
            original=target.read_bytes(); changed=original+b'\n# negative read fixture\n'
            actual_read=Path.read_bytes
            def changed_read(path): return changed if path.absolute()==target.absolute() else actual_read(path)
            save(f'attack-{index:03d}.bin',changed)
            expected='external runtime mismatch' if member=='mocked_source_hash' else 'frozen authority changed: docs/reference_cases/ge_beam3_g3c_fixtures_v1.json'
            with patch.object(Path,'read_bytes',changed_read), patch.object(history,'HistoryOwner',forbidden):
                expected_rejection(lambda:history.resume(raw,digest,expected_runtime_sha256=runtime),expected)
            record=dict(category=category,member=member,rejection=phase,expected_error=expected,
                        before_sha256=sha256(original).hexdigest(),after_sha256=sha256(changed).hexdigest(),source_path=str(target))
        elif member=='changed_implementation_review':
            original=p.canonical(lease['implementation_review']); value=p.strict(original)
            value['subject_commit']='0'*40; changed=p.canonical(value)
            save(f'attack-{index:03d}.json',changed)
            with patch.object(history,'HistoryOwner',forbidden):
                expected_rejection(lambda:runner.verify_review(changed,lease['review_sha256'],lease['candidate'],lease['inputs']),
                                   'implementation review hash mismatch')
            record=dict(category=category,member=member,rejection=phase,expected_error='implementation review hash mismatch',
                        before_sha256=sha256(original).hexdigest(),after_sha256=sha256(changed).hexdigest())
        else:
            changed,record=mutations.packet_attack(raw,category,member)
            save(f'attack-{index:03d}.bin',changed)
            if phase=='PREFLIGHT_BEFORE_CONSTRUCTION':
                with patch.object(history,'HistoryOwner',forbidden):
                    expected_rejection(lambda:history.resume(changed,record['after_sha256'],expected_runtime_sha256=runtime),record['expected_error'])
            else:
                p.preflight(changed,record['after_sha256'],expected_runtime_sha256=runtime)
                expected_rejection(lambda:history.resume(changed,record['after_sha256'],expected_runtime_sha256=runtime),record['expected_error'])
        assert not calls
        results.append(dict(record,passed=True,origin=assignment['origin'],input_sha256=digest))
        print('G3C CHECKPOINT mutation '+category+' '+member+' rejected at '+phase,flush=True)
    value=dict(kind='G3C_REHEARSAL_ATTACK_DIAGNOSTICS',lease_sha256=p.digest(lease),assignment=assignment,files=files,results=results)
    packets.exclusive(out/'artifacts.json',p.canonical(value))


def test_registered_rehearsal(rehearsal_context):
    context=rehearsal_context
    (context['out']/'packets').mkdir()
    if context['assignment']['kind']=='history': history_run(context)
    else: negative_run(context)
