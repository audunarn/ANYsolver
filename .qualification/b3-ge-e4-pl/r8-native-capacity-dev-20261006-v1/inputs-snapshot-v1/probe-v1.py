"""Prepared installed screen. Supervisor approval is mandatory before launch."""
from copy import deepcopy
from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from examples import stiffened_shell_native_capacity as case


def save(folder, name, value):
    (folder/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def run(folder):
    def streamed(observation):
        with (folder/'accepted-observations.jsonl').open('a') as stream:
            stream.write(json.dumps(observation, allow_nan=False)+'\n')

    report = case.workflow(arc_steps=12, on_observation=streamed)
    checkpoints = []
    for index, entry in enumerate(report['checkpoint_inventory']):
        raw = entry.pop('checkpoint_bytes')
        assert len(raw) == entry['size_bytes'] and sha256(raw).hexdigest() == entry['sha256']
        path = folder/f'checkpoint-{index}-g{entry["generation"]}.bin'
        path.write_bytes(raw)
        entry['path'] = str(path)
        checkpoints.append(raw)
    save(folder, 'screen-result.json', report)
    completed = report['status'] in ('bounded_no_turning_observed', 'turning_candidate_unvalidated')
    if not completed:
        save(folder, 'screen-disposition.json', dict(status='NUMERICAL_ROUTE_NOT_COMPLETED',
            numerical_status=report['status'], scientific_acceptance=False, automatic_retry=False))
        return 2

    # Frozen mechanical normalizations; these do not establish stability.
    estimate = case.Specimen().estimate()
    force_scale = 1.12*estimate['euler_clamped_free_n']
    moment_scale = force_scale*case.Specimen().length_m
    errors = []
    for observation in report['observations']:
        state = observation['state']
        wrench = np.asarray(observation['global_wrench_residual'])
        errors.append(dict(generation=observation['generation'],
            equilibrium=state['free_equilibrium_ratio'], constraint=state['constraint_max'],
            force=float(np.linalg.norm(wrench[:3])/force_scale),
            moment=float(np.linalg.norm(wrench[3:])/moment_scale)))
    save(folder, 'mechanical-observations.json', dict(force_scale_n=force_scale,
        moment_scale_nm=moment_scale, thresholds=dict(equilibrium=1e-8,
        constraint=1e-9, force=1e-8, moment=1e-8), observations=errors))
    assert all(np.isfinite([row[k] for k in ('equilibrium','constraint','force','moment')]).all()
        and row['equilibrium'] <= 1e-8 and row['constraint'] <= 1e-9
        and row['force'] <= 1e-8 and row['moment'] <= 1e-8 for row in errors)

    observations = report['observations']
    assert len(observations) == 17 and len(report['restart_checks']) == 1
    assert all(report['restart_checks'][0].values())
    with (folder/'accepted-observations.jsonl').open() as stream:
        restored_stream = [json.loads(line) for line in stream]
    assert restored_stream == observations
    assert case.turning_observations(restored_stream) == report['turning_candidates']
    direction = tuple(ss.NodalAction(row['domain'],row['node'],tuple(row['wrench']))
                      for row in report['arc_direction'])
    checks = dict(public_restart=report['restart_checks'][0], streamed_state_parity=True)
    owner = ss.create_analysis(definition=case.definition())
    fresh = None
    try:
        restored = owner.restore(checkpoints[0])
        assert restored.status == 'accepted_prefix' and owner.checkpoint() == checkpoints[0]
        assert case._plain(owner.recover()) == observations[5]['state']
        metric = case.metric_for(tuple(owner.preflight()['arc_metric_node_order']),case.Specimen())
        control = ss.ArcLengthControl('shell',18,2,metric,.01,orientation=-1)
        before = owner.checkpoint(); recovery = deepcopy(case._plain(owner.recover()))
        token = CancellationToken(); token.cancel('before capacity prefix continuation')
        try:
            owner.continue_arc_length(direction,control,cancellation_token=token)
        except SolveCancelled:
            pass
        else:
            raise AssertionError('pre-step cancellation was not propagated')
        assert owner.checkpoint() == before and case._plain(owner.recover()) == recovery
        damaged = bytearray(before); damaged[-1] ^= 1
        try:
            owner.restore(bytes(damaged))
        except ValueError as error:
            checks['corrupt_refusal'] = dict(type=type(error).__name__,message=str(error))
        else:
            raise AssertionError('corrupt checkpoint was restored')
        assert owner.checkpoint() == before and case._plain(owner.recover()) == recovery
        checks['precancel_unchanged'] = True
        token = CancellationToken(); accepted = []
        def cancel_after_prefix(result):
            accepted.append(result.generation)
            token.cancel('capacity accepted-prefix cancellation')
        try:
            owner.continue_arc_length(direction,control,steps=2,
                cancellation_token=token,on_accepted=cancel_after_prefix)
        except SolveCancelled:
            pass
        else:
            raise AssertionError('accepted-prefix cancellation was not propagated')
        assert accepted == [observations[6]['generation']]
        assert case._plain(owner.recover()) == observations[6]['state']
        prefix = owner.checkpoint(); (folder/'cancelled-accepted-prefix.bin').write_bytes(prefix)
        fresh = ss.create_analysis(definition=case.definition())
        fresh.restore(prefix)
        assert fresh.checkpoint() == prefix and case._plain(fresh.recover()) == observations[6]['state']
        fresh.continue_arc_length(direction,control)
        assert case._plain(fresh.recover()) == observations[7]['state']
        checks['cancelled_prefix_restart_continue'] = True
        save(folder,'prefix-checks.json',checks)
    finally:
        owner.close()
        if fresh is not None:
            fresh.close()
    save(folder,'screen-disposition.json',dict(status='LIMITED_DEVELOPMENT_ROUTE_COMPLETED',
        numerical_status=report['status'], initial_elastic_screen=report['initial_elastic_screen'],
        turning_candidates=report['turning_candidates'], scientific_acceptance=False,
        instability_or_capacity_proven=False, automatic_retry=False))
    return 0
