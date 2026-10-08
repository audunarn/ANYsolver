"""SOURCE_ONLY_UNRUN: exactly one saved near-turn g14 -> g15 replay.

Root's resource supervisor owns execution within the existing restart-check
authority. This probe grants none. run(folder) reads folder.parent/installed-v1,
writes only a new near-turn-prefix-checks.json in the supplied output directory,
and returns zero only after the assigned public recovery/checkpoint checks pass.
"""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from examples import stiffened_shell_native_capacity as case


BINDINGS = {
    14: dict(binary_sha256='f632e5fdac61c9c160949bab025c20a1f37b9becd27122dbc7b5130316dae69e',
             binary_bytes=50115,
             packet_sha256='c82662e7625084a10285e1da0755cff20745439c15181532014c42596f01bef0',
             packet_bytes=190768),
    15: dict(binary_sha256='0c4ed52276fe0d0a21c20ae034f05d86b2bf16eda7216697a1fd12e79adc8f35',
             binary_bytes=50410,
             packet_sha256='765f06accd324691121a92312c6da6a0915581924dd698395b9a09e9ef256e2d',
             packet_bytes=191114),
}
MODULE_BINDINGS = {
    'case': '9e88b6a44393e8b3ef779e1498ac5752602aa88b8f2744dfd10042caf5667794',
    'metric': 'f39f89da7dde5300a8b6d205024b67bf7a33389879c6af6e5bb3d0050e0bda55',
    'control': '6fd607cc82d7e8bd1b6f062fd665c9a72b568bb92be108a499324069c6fc8315',
}
EXPECTED_ACTIONS = [
    dict(domain='shell',node=9,wrench=[-2596.463001005903,0.,103.85852004023613,0.,0.,0.]),
    dict(domain='shell',node=18,wrench=[-5192.926002011806,0.,207.71704008047226,0.,0.,0.]),
    dict(domain='shell',node=27,wrench=[-2596.463001005903,0.,103.85852004023613,0.,0.,0.]),
    dict(domain='beam',node=109,wrench=[-6231.511202414168,0.,0.,0.,0.,0.]),
    dict(domain='beam',node=209,wrench=[-6231.511202414168,0.,0.,0.,0.,0.]),
]
OUTER_WEIGHTS = (1/128,)+(1/64,)*7+(1/128,)
CENTER_WEIGHTS = (1/64,)+(1/32,)*7+(1/64,)
EXPECTED_WEIGHTS = OUTER_WEIGHTS+CENTER_WEIGHTS+OUTER_WEIGHTS+CENTER_WEIGHTS*2


def module_bindings():
    modules = dict(case=case,metric=sys.modules[ss.NativeDirectorChordMetric.__module__],
                   control=sys.modules[ss.ArcLengthControl.__module__])
    proof = {}
    for name,module in modules.items():
        path = Path(module.__file__).resolve()
        digest = sha256(path.read_bytes()).hexdigest()
        assert digest == MODULE_BINDINGS[name], f'frozen {name} module changed'
        proof[name] = dict(path=str(path),sha256=digest)
    return proof


def saved_endpoint(folder,generation):
    """Bind bytes and complete owned packet; never use a scalar peak as state."""
    expected = BINDINGS[generation]
    raw = (folder/f'accepted-g{generation}.bin').read_bytes()
    metadata = (folder/f'accepted-g{generation}.json').read_bytes()
    assert len(raw) == expected['binary_bytes']
    assert sha256(raw).hexdigest() == expected['binary_sha256']
    assert len(metadata) == expected['packet_bytes']
    assert sha256(metadata).hexdigest() == expected['packet_sha256']
    packet = json.loads(metadata)
    assert packet['generation'] == generation
    assert packet['checkpoint_file'] == f'accepted-g{generation}.bin'
    assert packet['checkpoint_size_bytes'] == len(raw)
    assert packet['checkpoint_sha256'] == expected['binary_sha256']
    assert packet['accepted_status'] == 'accepted_prefix'
    assert packet['observation']['generation'] == generation
    assert packet['observation']['state']['generation'] == generation
    assert packet['observation']['state']['status'] == 'accepted_prefix'
    return raw,deepcopy(packet)


def unchanged(owner,raw,state):
    """Assigned public snapshot criterion; no internal identity assertion."""
    assert owner.checkpoint() == raw
    assert deepcopy(case._plain(owner.recover())) == state


def write_proof(folder,proof):
    target = folder/'near-turn-prefix-checks.json'
    temporary = target.with_name(target.name+'.part')
    if target.exists() or temporary.exists():
        raise RuntimeError('refusing to overwrite near-turn proof evidence')
    with temporary.open('xb') as stream:
        stream.write((json.dumps(proof,indent=2,allow_nan=False)+'\n').encode('utf-8'))
        stream.flush(); os.fsync(stream.fileno())
    temporary.replace(target)


def run(folder):
    output = Path(folder).resolve()
    inputs = output.parent/'installed-v1'
    assert output.is_dir() and inputs.is_dir() and output != inputs
    modules_before = module_bindings()
    raw14,packet14 = saved_endpoint(inputs,14)
    raw15,packet15 = saved_endpoint(inputs,15)
    expected14 = deepcopy(packet14['observation']['state'])
    expected15 = deepcopy(packet15['observation']['state'])
    actions = case.VERIFIED_FORCE_PREFIX_ACTIONS
    assert case._plain(actions) == EXPECTED_ACTIONS
    proof = dict(status='SOURCE_PROBE_RUNNING',scientific_acceptance=False,
        instability_or_capacity_proved=False,internal_identity_atomicity_proved=False,
        assigned_criterion='complete_public_recovery_and_checkpoint_bytes',
        input_bindings=deepcopy(BINDINGS),module_bindings=modules_before,
        replay=dict(from_generation=14,to_generation=15,requested_steps=1),refusals=[])
    owner = ss.create_analysis(definition=case.definition())
    try:
        preflight = owner.preflight()
        assert preflight['identity'] == case.VERIFIED_FORCE_PREFIX_MODEL
        restored = owner.restore(raw14)
        assert restored.status == 'accepted_prefix' and restored.generation == 14
        unchanged(owner,raw14,expected14)
        proof['restore_g14_full_public_recovery_equal'] = True
        proof['restore_g14_checkpoint_bytes_equal'] = True
        order = tuple(preflight['arc_metric_node_order'])
        metric = case.metric_for(order,case.Specimen())
        assert type(metric) is ss.NativeDirectorChordMetric
        assert metric.shell_nodes == 27 and metric.length == 2.
        assert np.array_equal(metric.weights,np.array(EXPECTED_WEIGHTS))
        control = ss.ArcLengthControl('shell',18,2,metric,.01,orientation=1)
        assert (control.max_cutbacks,control.max_attempts,control.max_iterations,
                control.max_backtracks) == (4,5,20,12)
        proof['frozen_actions_and_metric_equal'] = True
        for name,wrong,changed in (
            ('wrong_direction',case.combine((-1.,actions)),control),
            ('changed_radius',actions,replace(control,radius=.02))):
            try:
                owner.continue_arc_length(wrong,changed,steps=1)
            except ValueError as error:
                message = str(error)
                assert 'arc controller/load/metric differs from accepted history' in message
            else:
                raise AssertionError(f'{name} did not refuse')
            unchanged(owner,raw14,expected14)
            proof['refusals'].append(dict(kind=name,error_type='ValueError',message=message,
                full_public_recovery_unchanged=True,checkpoint_bytes_unchanged=True))
        token = CancellationToken(); token.cancel('before saved near-turn replay')
        try:
            owner.continue_arc_length(actions,control,steps=1,cancellation_token=token)
        except SolveCancelled as error:
            assert error.stage == 'stiffened-shell.arc.step'
            proof['precancel'] = dict(error_type=type(error).__name__,stage=error.stage,
                                     reason=error.reason)
        else:
            raise AssertionError('pre-step cancellation did not propagate')
        unchanged(owner,raw14,expected14)
        proof['precancel'].update(full_public_recovery_unchanged=True,checkpoint_bytes_unchanged=True)
        accepted = []
        def record(result):
            assert result.generation == 15 and result.status == 'accepted_prefix'
            unchanged(owner,raw15,expected15)
            assert deepcopy(case._plain(result)) == expected15
            accepted.append(result.generation)
        result = owner.continue_arc_length(actions,control,steps=1,on_accepted=record)
        assert result.status == 'completed' and result.generation == 15
        assert accepted == [15]
        unchanged(owner,raw15,expected15)
        proof['replay'].update(actual_accepted_generations=accepted,completed_return_status=result.status,
            recovered_status=owner.recover().status,full_public_recovery_equal=True,
            checkpoint_bytes_equal=True)
        for generation,raw,packet in ((14,raw14,packet14),(15,raw15,packet15)):
            observation = packet['observation']
            amplitude = observation['state']['amplitude']
            assert observation['proportional_factor'] == .5+amplitude
            actual = np.asarray(observation['state']['applied_dead_load'])
            full = case.declared_load_vector(actions,order,len(actual))
            assert np.array_equal(actual,.5*full+amplitude*full)
            proof.setdefault('saved_endpoint_observations',[]).append(dict(generation=generation,
                proportional_factor=observation['proportional_factor'],tip_z_m=observation['tip_z_m'],
                checkpoint_sha256=sha256(raw).hexdigest(),public_affine_load_equal=True))
    finally:
        owner.close()
    # Read only the same two endpoints again; retain all historical evidence.
    for generation,raw,packet in ((14,raw14,packet14),(15,raw15,packet15)):
        repeated_raw,repeated_packet = saved_endpoint(inputs,generation)
        assert repeated_raw == raw and repeated_packet == packet
    assert module_bindings() == modules_before
    proof.update(status='ASSIGNED_NEAR_TURN_PUBLIC_PREFIX_CHECKS_PASSED',
                 saved_inputs_unchanged=True,frozen_modules_unchanged=True)
    write_proof(output,proof)
    return 0


if __name__ == '__main__':
    raise SystemExit('SOURCE_ONLY_UNRUN: root resource supervisor must authorize and launch run(folder)')
