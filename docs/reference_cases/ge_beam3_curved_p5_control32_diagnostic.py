"""One-use observation of two fixed controller states, not onset qualification."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import threading

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_wave as shared
from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import _pairs, _constant


BASE = 'b62298ebabca682c284754e46474c4d8ca3c3441'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_control32_diagnostic'
SCHEMA = 'GE_BEAM3_P5_CONTROL32_OBSERVATION_V1'
MANAGER = shared.MANAGER
FAILED_ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-onset32-20260906-93c594cb16aa430babae3a3fc62e2e2f')
FAILED = {
    'blocked-diagnostic.json': (309, '82cf372ae545a55848b77cab06060adc313331b4df5f4032c9fbd9f0c9247524'),
    'elements-32/grid-00.json': (1155343, 'c28606ac3e4a85af82915cfee610753a5b7364f850894cdda628efc8d4179770'),
    'elements-32/process-start.json': (368, '580bb0f65cf934924bd14329e1554f9a8074895fee0144b794cd527d992a684d'),
    'elements-32/process.json': (99, '2f0acd6a5a7487161230c2724a7d618644be3265ad9fed5f0a3ee8607adebd14'),
    'elements-32/progress.jsonl': (157, '8d69532ca5d4d20a5e6c8aef0c63df2f883e4afbe4e0385f58e14249c985772d'),
    'elements-32/stderr.log': (3053, '4a3803f303bd02bad78c0eb62bcd5e097e521882d1d3a7c8193a00b90c93d1a0'),
    'elements-32/stdout.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'inputs.json': (1909, '4f996b603bfd47cc58e0c15d16b7dbf0d522d52c69be88b1d0a5c589e6e06111'),
}
ALLOWED = {'docs/reference_cases/ge_beam3_curved_p5_displacement_control_probe.py',
           'docs/reference_cases/ge_beam3_curved_p5_control32_diagnostic.py',
           'tests/test_ge_beam3_curved_p5_control_observation.py',
           'tests/test_ge_beam3_curved_p5_control32_diagnostic.py',
           'docs/agent_plans/GE_BEAM3_CURVED_P5_CONTROL32_DIAGNOSTIC_PLAN.md'}
CASE = {'elements': 32, 'extent': 'ARCH_ONSET32', 'targets': [.1, .095],
        'iteration_limit': 16, 'backtracks': 10, 'mixed_evaluations_per_trial': 8192,
        'observation_limit_per_trial': 256, 'residual_limit': 1e-11,
        'child_seconds': 600, 'coordinator_seconds': 890, 'memory_bytes': 24*(1 << 30),
        'inactivity_seconds': 300, 'automatic_retry': False, 'production_qualified': False}


def failed_inputs():
    for name, (size, digest) in FAILED.items():
        data = shared.ordinary(FAILED_ROOT/name)
        if len(data) != size or shared.sha(data) != digest:
            raise shared.RefinementError('preserved failed input hash mismatch')
    if (FAILED_ROOT/'aggregate.json').exists() or (FAILED_ROOT/'elements-32/complete.json').exists():
        raise shared.RefinementError('failed attempt gained unregistered evidence')
    return {name: {'bytes': size, 'sha256': digest} for name, (size, digest) in FAILED.items()}


def authority(repo, commit):
    if not re.fullmatch('[0-9a-f]{40}', commit) or shared.git(repo, 'rev-parse', 'HEAD') != commit:
        raise shared.RefinementError('frozen observation commit mismatch')
    if shared.git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise shared.RefinementError('dirty observation inputs')
    if (shared.git(repo, 'rev-parse', 'HEAD^') != BASE or
            set(shared.git(repo, 'diff', '--name-only', BASE, commit).splitlines()) != ALLOWED):
        raise shared.RefinementError('exact observation parent/extent required')
    if (shared.git(shared.SIBLING, 'status', '--porcelain', '--untracked-files=all') or
            shared.git(shared.SIBLING, 'rev-parse', 'HEAD') != shared.SIBLING_COMMIT or
            shared.git(shared.SIBLING, 'rev-parse', 'HEAD^{tree}') != shared.SIBLING_TREE):
        raise shared.RefinementError('observation sibling mismatch')
    env = shared.environment()
    if shared.sha(shared.canonical(env)) != shared.ENVIRONMENT_SHA:
        raise shared.RefinementError('observation environment mismatch')
    return {'commit': commit, 'tree': shared.git(repo, 'rev-parse', 'HEAD^{tree}'),
            'case_sha256': shared.sha(shared.canonical(CASE)), 'environment': env,
            'sibling_commit': shared.SIBLING_COMMIT, 'sibling_tree': shared.SIBLING_TREE,
            'failed_inputs': failed_inputs()}


def command(repo, commit, output):
    return f"& '{sys.executable}' -B -m {MODULE} --coordinate --commit {commit} --output '{Path(output)}'"


def lease(repo, commit, output, *, manager=None):
    manager = MANAGER if manager is None else Path(manager)
    owner = shared.load(manager/'active-lock/owner.json', strict=False)
    request_id = owner.get('request_id')
    if not isinstance(request_id, str) or not re.fullmatch('[0-9a-f]{32}', request_id):
        raise shared.RefinementError('active observation lease required')
    path = manager/'requests'/(request_id+'.json');request = shared.load(path, strict=False)
    for value in (owner, request):
        if (value.get('request_id') != request_id or value.get('command') != command(repo, commit, output) or
                Path(value.get('repository', '')).resolve() != Path(repo).resolve()):
            raise shared.RefinementError('exact observation command/lease required')
    rows = [[v.strip() for v in line.split('|')[1:-1]] for line in
            (manager/'ledger.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('|')]
    if [r[2] for r in rows if len(r) > 2 and r[1] == request_id] != ['APPROVED']:
        raise shared.RefinementError('one unconsumed observation approval required')
    return request_id, shared.sha(path.read_bytes())


def capture(*, count, observe, publish_raw):
    """Two-element mode exists only for small disposable correctness tests."""
    if type(count) is not int or count not in (2, 32):
        raise ValueError('registered observation element count required')
    from dataclasses import asdict
    from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
    from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import DisplacementControlledAssemblyProbe, DisplacementControlError
    from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
    beam, _ = make_beam(count, extent='ARCH_ONSET32')
    control = DisplacementControlledAssemblyProbe(beam, node=count)
    initial = control.trial(.1, observer=lambda event: observe({'state': 'INITIAL', 'event': event}))
    control.commit(initial)
    if digest(control.committed_model.replay()) != digest(initial.assembly.response):
        raise ValueError('initial diagnostic replay mismatch')
    bindings = {'initial': publish_raw('initial', asdict(initial))}
    before = digest(control.committed_model.committed)
    try:
        target = control.trial(.095, observer=lambda event: observe({'state': 'TARGET', 'event': event}))
    except DisplacementControlError as error:
        if control._pending is not None or digest(control.committed_model.committed) != before:
            raise ValueError('failed diagnostic trial changed committed state')
        failure = {'error_type': type(error).__name__, 'error': str(error),
                   'checkpoints': [asdict(c) for c in error.checkpoints], 'mixed_evaluations': error.evaluations}
        return {'elements': count, 'solver_outcome': 'FAILED', 'failure': failure, 'bindings': bindings,
                'failed_trial_uncommitted': True, 'initial_checkpoint_sha256': before,
                'production_qualified': False}
    control.commit(target)
    if digest(control.committed_model.replay()) != digest(target.assembly.response):
        raise ValueError('target diagnostic replay mismatch')
    bindings['target'] = publish_raw('target', asdict(target))
    return {'elements': count, 'solver_outcome': 'TARGET_CONVERGED', 'failure': None, 'bindings': bindings,
            'failed_trial_uncommitted': None, 'initial_checkpoint_sha256': before, 'production_qualified': False}


DETAILS = {'translation_residual', 'rotation_residual', 'largest_residual', 'largest_residual_dof', 'local_residual_max', 'potential'}
METRICS = {'INITIALIZATION': {'target', 'origin_epoch'}, 'PREDICTOR': {'condition_2', 'linear_residual', 'translation_increment_max', 'rotation_increment_max'},
    'CORRECTION': {'condition_2', 'linear_residual', 'translation_increment_max', 'rotation_increment_max'},
    'ITERATION': {'residual', 'reaction'} | DETAILS,
    'CANDIDATE': {'residual', 'accepted', 'position_change_max', 'rotation_matrix_change_max'} | DETAILS,
    'CANDIDATE_REJECTED': {'error_type', 'error'}, 'CONVERGED': {'residual'}, 'FAILURE': {'error_type', 'error'}}


def parse_observations(path, *, count=32):
    data = shared.ordinary(path)
    if len(data) > 2*(1 << 20): raise ValueError('bounded observation log required')
    groups = {'INITIAL': [], 'TARGET': []};rows = data.splitlines(keepends=True);seen_target = False
    if not 2 <= len(rows) <= 512: raise ValueError('bounded observation count required')
    for line in rows:
        row = json.loads(line, object_pairs_hook=_pairs, parse_constant=_constant)
        if shared.canonical(row) != line or set(row) != {'state', 'event'} or row['state'] not in groups:
            raise ValueError('canonical observation envelope required')
        state = row['state'];event = row['event'];group = groups[state]
        if state == 'TARGET': seen_target = True
        elif seen_target: raise ValueError('interleaved observation states')
        if (set(event) != {'sequence', 'phase', 'iteration', 'backtrack', 'mixed_evaluations', 'metrics'} or
                type(event['sequence']) is not int or event['sequence'] != len(group) or len(group) >= 256 or
                event['phase'] not in METRICS or set(event['metrics']) != METRICS[event['phase']] or
                type(event['mixed_evaluations']) is not int or not 0 <= event['mixed_evaluations'] <= 256*count):
            raise ValueError('observation schema/order/budget mismatch')
        for key, limit in (('iteration', 16), ('backtrack', 9)):
            if event[key] is not None and (type(event[key]) is not int or not 0 <= event[key] <= limit):
                raise ValueError('observation iteration bound mismatch')
        if group and event['mixed_evaluations'] < group[-1]['mixed_evaluations']:
            raise ValueError('observation evaluation count decreased')
        m = event['metrics']
        if any(type(v) not in (int, float, bool, str) or type(v) is float and not math.isfinite(v) for v in m.values()):
            raise ValueError('finite scalar observation metrics required')
        for key, value in m.items():
            if key in ('error_type', 'error'):
                if type(value) is not str or len(value) > 240: raise ValueError('bounded typed rejection required')
            elif key == 'accepted':
                if type(value) is not bool: raise ValueError('boolean candidate decision required')
            elif key in ('origin_epoch', 'largest_residual_dof'):
                if type(value) is not int or value < 0: raise ValueError('integer observation identity required')
            elif type(value) not in (int, float): raise ValueError('numeric observation metric required')
        if event['phase'] in ('ITERATION', 'CANDIDATE'):
            if abs(math.hypot(m['translation_residual'], m['rotation_residual'])-m['residual']) > 1e-14*max(1e-300, m['residual']):
                raise ValueError('physical residual components disagree')
        if event['phase'] == 'CANDIDATE' and type(m['accepted']) is not bool:
            raise ValueError('explicit candidate disposition required')
        group.append(event)
    for state, group in groups.items():
        if not group or group[0]['phase'] != 'INITIALIZATION': raise ValueError('both initialized states required')
        expected = .1 if state == 'INITIAL' else .095
        if group[0]['metrics'] != {'target': expected, 'origin_epoch': 0 if state == 'INITIAL' else 1}:
            raise ValueError('registered target/origin required')
        iterations = [e for e in group if e['phase'] == 'ITERATION']
        if [e['iteration'] for e in iterations] != list(range(len(iterations))):
            raise ValueError('consecutive observed iterations required')
        for i, event in enumerate(group):
            if event['phase'] in ('CONVERGED', 'FAILURE') and i != len(group)-1:
                raise ValueError('observation after terminal event')
            if event['phase'] == 'CANDIDATE':
                origin = next((e for e in reversed(group[:i]) if e['phase'] == 'ITERATION'), None)
                if origin is None or event['iteration'] != origin['iteration'] or event['metrics']['accepted'] != (event['metrics']['residual'] < origin['metrics']['residual']):
                    raise ValueError('candidate acceptance differs from physical norm rule')
        for current in iterations:
            index = group.index(current)
            later = group[index+1:]
            terminal = next((i for i, e in enumerate(later) if e['phase'] in ('ITERATION', 'FAILURE', 'CONVERGED')), len(later))
            segment = later[:terminal]
            candidates = [e for e in segment if e['phase'] in ('CANDIDATE', 'CANDIDATE_REJECTED')]
            if ([e['backtrack'] for e in candidates] != list(range(len(candidates))) or
                    any(e['iteration'] != current['iteration'] for e in segment) or
                    any(e['phase'] not in ('CORRECTION', 'CANDIDATE', 'CANDIDATE_REJECTED') for e in segment) or
                    sum(e['phase'] == 'CORRECTION' for e in segment) > 1):
                raise ValueError('candidate/correction sequence mismatch')
            if candidates and (not segment or segment[0]['phase'] != 'CORRECTION'):
                raise ValueError('candidate without observed correction')
            accepted = [e for e in candidates if e['phase'] == 'CANDIDATE' and e['metrics']['accepted']]
            if accepted and (len(accepted) != 1 or accepted[0] is not candidates[-1]):
                raise ValueError('candidate attempted after accepted correction')
            if terminal < len(later) and later[terminal]['phase'] == 'ITERATION':
                if not accepted or later[terminal]['metrics']['residual'] != accepted[0]['metrics']['residual']:
                    raise ValueError('accepted candidate not retained at next iteration')
            if terminal < len(later) and later[terminal]['phase'] == 'CONVERGED':
                if segment or current['metrics']['residual'] > 1e-11 or later[terminal]['metrics']['residual'] != current['metrics']['residual']:
                    raise ValueError('convergence differs from physical residual rule')
    if groups['INITIAL'][-1]['phase'] != 'CONVERGED' or groups['TARGET'][-1]['phase'] not in ('CONVERGED', 'FAILURE'):
        raise ValueError('complete diagnostic terminal observations required')
    return groups


def inspect(folder, frozen, request_id, request_sha, *, count=32):
    packet = shared.load(folder/'complete.json')
    if (set(packet) != {'schema', 'authority', 'request_id', 'request_sha256', 'result'} or
            packet['schema'] != SCHEMA or packet['authority'] != frozen or packet['request_id'] != request_id or packet['request_sha256'] != request_sha):
        raise ValueError('diagnostic packet identity mismatch')
    result = packet['result'];groups = parse_observations(folder/'progress.jsonl', count=count)
    if (set(result) != {'elements', 'solver_outcome', 'failure', 'bindings', 'failed_trial_uncommitted', 'initial_checkpoint_sha256', 'production_qualified'} or
            result['elements'] != count or result['production_qualified'] is not False):
        raise ValueError('diagnostic result schema mismatch')
    outcome = 'FAILED' if groups['TARGET'][-1]['phase'] == 'FAILURE' else 'TARGET_CONVERGED'
    if result['solver_outcome'] != outcome: raise ValueError('solver outcome differs from observations')
    expected = {'initial'} if outcome == 'FAILED' else {'initial', 'target'}
    if set(result['bindings']) != expected: raise ValueError('no fabricated absent target trial allowed')
    for name, binding in result['bindings'].items():
        if set(binding) != {'name', 'bytes', 'sha256'} or binding['name'] != name+'.json': raise ValueError('raw trial binding mismatch')
        path = folder/binding['name'];data = shared.ordinary(path)
        if len(data) != binding['bytes'] or shared.sha(data) != binding['sha256']: raise ValueError('raw trial hash mismatch')
        trial = shared.load(path);state = 'INITIAL' if name == 'initial' else 'TARGET'
        if trial['target'] != (.1 if name == 'initial' else .095) or trial['assembly']['residual_norm'] != groups[state][-1]['metrics']['residual']:
            raise ValueError('raw trial/observation mismatch')
        if name == 'initial':
            a = trial['assembly']
            checkpoint = {'epoch': 1, 'positions': a['positions'], 'rotations': a['rotations'], 'forces': a['forces'],
                'histories': [[s['response']['history'] for s in e['stations']] for e in a['response']['elements']]}
            if shared.sha(shared.canonical(checkpoint)[:-1]) != result['initial_checkpoint_sha256']:
                raise ValueError('initial checkpoint digest differs from raw state')
    if outcome == 'FAILED':
        failure = result['failure'];events = [e for e in groups['TARGET'] if e['phase'] == 'ITERATION']
        checks = [{'iteration': e['iteration'], 'mixed_evaluations': e['mixed_evaluations'],
                   'residual': e['metrics']['residual'], 'reaction': e['metrics']['reaction']} for e in events]
        if (result['failed_trial_uncommitted'] is not True or set(failure) != {'error_type', 'error', 'checkpoints', 'mixed_evaluations'} or
                failure['checkpoints'] != checks or failure['mixed_evaluations'] != groups['TARGET'][-1]['mixed_evaluations'] or
                failure['error_type'] != 'DisplacementControlError' or
                failure['error'] != 'controlled trial failed without commit: '+groups['TARGET'][-1]['metrics']['error']):
            raise ValueError('failure checkpoint summary mismatch')
    elif result['failure'] is not None or result['failed_trial_uncommitted'] is not None:
        raise ValueError('converged diagnostic carries fabricated failure')
    allowed = {name+'.json' for name in expected} | {'complete.json', 'progress.jsonl', 'stdout.log', 'stderr.log', 'process-start.json', 'process.json'}
    if any(p.name not in allowed or not p.is_file() for p in folder.iterdir()): raise ValueError('unregistered diagnostic file')
    return packet, groups


def worker(repo, commit, output):
    frozen = authority(repo, commit);request_id, request_sha = lease(repo, commit, output)
    folder = output/'control32'
    with (folder/'progress.jsonl').open('xb') as stream:
        def observe(row): stream.write(shared.canonical(row));stream.flush()
        result = capture(count=32, observe=observe, publish_raw=lambda name, raw: shared.publish(folder/(name+'.json'), raw))
    if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha):
        raise ValueError('observation authority changed')
    shared.publish(folder/'complete.json', {'schema': SCHEMA, 'authority': frozen, 'request_id': request_id,
                                         'request_sha256': request_sha, 'result': result})


def _coordinate(repo, commit, output):
    frozen = authority(repo, commit);request_id, request_sha = lease(repo, commit, output)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(repo.resolve()) or output.resolve().is_relative_to(FAILED_ROOT.resolve()):
        raise ValueError('fresh external observation output required')
    (MANAGER/'claims'/('ge-beam3-control32-'+request_id)).mkdir();output.mkdir(parents=True, exist_ok=False)
    shared.publish(output/'inputs.json', {'authority': frozen, 'case': CASE, 'request_id': request_id, 'request_sha256': request_sha})
    folder = output/'control32';folder.mkdir();process = None
    try:
        env = dict(os.environ, **shared.THREAD_ENVIRONMENT, PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
        env['PYTHONPATH'] = str(repo/'src')+os.pathsep+str(shared.SIBLING/'src')
        line = [sys.executable, '-B', '-m', MODULE, '--worker', '--commit', commit, '--output', str(output)]
        process = shared.run_child(line, folder, repo, env, timeout=600., inactivity=300., memory=24*(1 << 30))
        shared.publish(folder/'process.json', process)
        if process['exit_code'] != 0: raise ValueError('observation worker failed; no retry')
        packet, groups = inspect(folder, frozen, request_id, request_sha)
        if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha): raise ValueError('final observation authority mismatch')
        result = {'schema': SCHEMA, 'disposition': 'RESEARCH_CONTROLLER_OBSERVATIONS_CAPTURED',
            'solver_outcome': packet['result']['solver_outcome'], 'production_qualified': False,
            'restriction': 'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED', 'authority': frozen,
            'request_id': request_id, 'request_sha256': request_sha,
            'worker_sha256': shared.sha((folder/'complete.json').read_bytes()),
            'observations_sha256': shared.sha((folder/'progress.jsonl').read_bytes()),
            'observation_counts': {name: len(value) for name, value in groups.items()}}
        shared.publish(output/'diagnostic.json', result)
        return result
    except BaseException as error:
        shared.publish(output/'blocked-diagnostic.json', {'schema': SCHEMA, 'production_qualified': False,
            'request_id': request_id, 'error_type': type(error).__name__, 'error': str(error), 'process': process})
        raise


def coordinate(repo, commit, output):
    finished = threading.Event()
    def stop():
        if not finished.wait(890.): os._exit(124)
    threading.Thread(target=stop, daemon=True).start()
    try: return _coordinate(repo, commit, output)
    finally: finished.set()


def main():
    parser = argparse.ArgumentParser();mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--coordinate', action='store_true');mode.add_argument('--worker', action='store_true')
    parser.add_argument('--commit', required=True);parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args();repo = Path(__file__).resolve().parents[2]
    for key, value in shared.THREAD_ENVIRONMENT.items(): os.environ[key] = value
    if args.coordinate: print(shared.canonical(coordinate(repo, args.commit, args.output.resolve())).decode(), end='')
    else: worker(repo, args.commit, args.output.resolve())


if __name__ == '__main__': main()
