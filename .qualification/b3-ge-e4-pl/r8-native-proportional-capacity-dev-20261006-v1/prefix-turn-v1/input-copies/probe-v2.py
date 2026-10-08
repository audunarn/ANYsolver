"""Prepared proportional screen: no launch without supervisor approval."""
from copy import deepcopy
from hashlib import sha256
import json, os
from pathlib import Path
import numpy as np
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from examples import stiffened_shell_native_capacity as case

def save(folder,name,value):
    (folder/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def durable(path,payload):
    temporary=path.with_name(path.name+'.part')
    if path.exists() or temporary.exists():
        raise RuntimeError('refusing to overwrite accepted prefix evidence')
    with temporary.open('wb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)

def run(folder):
    received=[]
    def stream_state(packet):
        raw=packet['checkpoint_bytes']; generation=packet['generation']
        assert type(raw) is bytes and type(generation) is int
        assert len(raw)==packet['checkpoint_size_bytes'] and sha256(raw).hexdigest()==packet['checkpoint_sha256']
        assert generation==3+len(received)
        state=deepcopy(packet); state.pop('checkpoint_bytes')
        state['checkpoint_file']=f'accepted-g{generation}.bin'
        metadata=(json.dumps(state,allow_nan=False)+'\n').encode()
        durable(folder/state['checkpoint_file'],raw)
        durable(folder/f'accepted-g{generation}.json',metadata)
        with (folder/'accepted-inventory.jsonl').open('ab') as output:
            output.write(metadata); output.flush(); os.fsync(output.fileno())
        received.append(state)
        print(json.dumps(dict(accepted_generation=generation,
            factor=packet['observation']['proportional_factor'],
            equilibrium=packet['observation']['state']['free_equilibrium_ratio'],
            gap=packet['observation']['state']['constraint_max'])),flush=True)

    fixture=Path(__file__).resolve().parent/'verified-force-prefix.bin'
    save(folder,'screen-started.json',dict(candidate='151cb3d4',origin_sha256=sha256(fixture.read_bytes()).hexdigest(),requested_arc_steps=12,force_seed_rerun=False))
    report=case.proportional_workflow(fixture,arc_steps=12,on_state=stream_state)
    for record in report['checkpoint_inventory']:
        raw=record.pop('checkpoint_bytes')
        path=folder/f'accepted-g{record["generation"]}.bin'
        assert path.read_bytes()==raw and sha256(raw).hexdigest()==record['sha256']
        record['checkpoint_file']=path.name
    save(folder,'screen-result.json',report)
    assert len(received)==len(report['observations'])==len(report['checkpoint_inventory'])
    assert [row['observation'] for row in received]==report['observations']
    assert case.proportional_turning_observations(report['observations'])==report['turning_candidates']
    force_scale=1.12*case.Specimen().estimate()['euler_clamped_free_n']
    rows=[]
    for observation in report['observations']:
        state=observation['state']; wrench=np.asarray(observation['global_wrench_residual'])
        row=dict(generation=observation['generation'],equilibrium=state['free_equilibrium_ratio'],constraint=state['constraint_max'],force=float(np.linalg.norm(wrench[:3])/force_scale),moment=float(np.linalg.norm(wrench[3:])/(2*force_scale)))
        rows.append(row)
    save(folder,'accepted-mechanics.json',dict(force_scale_n=force_scale,
        moment_scale_nm=2*force_scale,thresholds=dict(equilibrium=1e-8,constraint=1e-9,force=1e-8,moment=1e-8),observations=rows))
    assert all(np.isfinite(list(row.values())).all() and row['equilibrium']<=1e-8 and row['constraint']<=1e-9 and row['force']<=1e-8 and row['moment']<=1e-8 for row in rows)
    completed=report['status'] in ('bounded_no_turning_observed','turning_candidate_unvalidated')
    if not completed:
        save(folder,'screen-disposition.json',dict(status='NUMERICAL_ROUTE_NOT_COMPLETED',numerical_status=report['status'],accepted_arc_steps=report['accepted_arc_steps'],durable_prefixes=len(received),scientific_acceptance=False,automatic_retry=False))
        return 2
    assert report['accepted_arc_steps']==12 and len(received)==13
    actions=case.VERIFIED_FORCE_PREFIX_ACTIONS
    owner=ss.create_analysis(definition=case.definition())
    corrupted=None; fresh=None
    checks=dict(streamed_state_parity=True,accepted_arc_steps=12)
    try:
        # First accepted arc prefix; replay only already-observed endpoints.
        first=received[1]; raw=(folder/first['checkpoint_file']).read_bytes()
        owner.restore(raw)
        expected=first['observation']['state']
        assert owner.checkpoint()==raw and case._plain(owner.recover())==expected
        control=ss.ArcLengthControl('shell',18,2,
            case.metric_for(tuple(owner.preflight()['arc_metric_node_order']),case.Specimen()),.01,orientation=1)
        for wrong,changed in ((case.combine((-1.,actions)),control),(actions,ss.ArcLengthControl('shell',18,2,control.metric,.02,orientation=1))):
            try:
                owner.continue_arc_length(wrong,changed)
            except ValueError as error:
                checks.setdefault('refusals',[]).append(str(error))
            else:
                raise AssertionError('changed arc load/controller was accepted')
            assert owner.checkpoint()==raw and case._plain(owner.recover())==expected
        token=CancellationToken(); token.cancel('before proportional prefix step')
        try:
            owner.continue_arc_length(actions,control,cancellation_token=token)
        except SolveCancelled:
            pass
        else:
            raise AssertionError('pre-step cancellation did not propagate')
        assert owner.checkpoint()==raw and case._plain(owner.recover())==expected
        corrupted=ss.create_analysis(definition=case.definition())
        damaged=bytearray(raw); damaged[-1]^=1
        try:
            corrupted.restore(bytes(damaged))
        except ValueError as error:
            checks['corrupt_refusal']=str(error)
        else:
            raise AssertionError('fresh owner accepted corrupted prefix')
        try:
            corrupted.recover()
        except RuntimeError as error:
            assert 'no accepted' in str(error)
        else:
            raise AssertionError('corrupt restore partially accepted state')
        corrupted.restore(raw)
        assert corrupted.checkpoint()==raw and case._plain(corrupted.recover())==expected
        token=CancellationToken(); accepted=[]
        def cancel_after(result):
            accepted.append(result.generation); token.cancel('after proportional accepted prefix')
        try:
            owner.continue_arc_length(actions,control,steps=2,cancellation_token=token,on_accepted=cancel_after)
        except SolveCancelled:
            pass
        else:
            raise AssertionError('accepted-prefix cancellation did not propagate')
        assert accepted==[received[2]['generation']]
        second_raw=(folder/received[2]['checkpoint_file']).read_bytes()
        assert owner.checkpoint()==second_raw and case._plain(owner.recover())==received[2]['observation']['state']
        fresh=ss.create_analysis(definition=case.definition()); fresh.restore(second_raw)
        assert fresh.checkpoint()==second_raw and case._plain(fresh.recover())==received[2]['observation']['state']
        fresh.continue_arc_length(actions,control)
        assert fresh.checkpoint()==(folder/received[3]['checkpoint_file']).read_bytes()
        assert case._plain(fresh.recover())==received[3]['observation']['state']
        checks.update(full_public_recovery_equal=True,snapshot_bytes_equal=True,precancel_unchanged=True,accepted_cancel_restart_continue_equal=True)
        save(folder,'prefix-checks.json',checks)
    finally:
        owner.close()
        if corrupted is not None: corrupted.close()
        if fresh is not None: fresh.close()
    save(folder,'screen-disposition.json',dict(status='LIMITED_DEVELOPMENT_ROUTE_COMPLETED',numerical_status=report['status'],initial_elastic_screen=report['initial_elastic_screen'],turning_candidates=report['turning_candidates'],scientific_acceptance=False,instability_or_capacity_proved=False,automatic_retry=False))
    return 0
