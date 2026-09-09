"""One-use centered-chord two-state comparison; research diagnostics only."""

import argparse
import math
import os
from pathlib import Path
import re
import sys
import threading

from docs.reference_cases import ge_beam3_curved_p5_control32_diagnostic as prior

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_wave as shared


BASE = 'b9b93afe07b05f6844c0c4e810965a9e450698de'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_centered_chord32_diagnostic'
SCHEMA = 'GE_BEAM3_P5_CENTERED_CHORD32_DIAGNOSTIC_V1'
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
OBSERVATION_ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-control32-20260906-765c2849b29f423199dc1e0eea37a9b7')
OBSERVATION = {
    'diagnostic.json': (2335, '046373a0827d2ccbcd4ebe9ef86d0700d44f7b7ffb1f9b853607e39123c2c10e'),
    'inputs.json': (2249, 'f03363fc6af96abe883c953175611fa5993412353e4ba0ae1c6ed36041d98b7f'),
    'control32/complete.json': (3232, '5a02e4ff446bc94a281a6f0d65d05681affc1a66fdecd4d1ace285d072ffe062'),
    'control32/initial.json': (1129420, '634a050e8be813abc34654ce78f02e5cbdaeeb0b52647b73883e40504a3d0ded'),
    'control32/progress.jsonl': (21279, 'f31a644ff92b4656999b991a804bfdafe53b3473ec941e9979778697549e35f3'),
    'control32/process-start.json': (372, '2194dceff95615b06573fb7d710216ed8105a61aaa686c096ad987bc467ed1f4'),
    'control32/process.json': (98, '54c421637f743384634aebb54cd2be84cadce85c60daaa3f7468140759f1ff95'),
    'control32/stdout.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'control32/stderr.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
}
FORCE_ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-force-accuracy32-20260906-36548b8a32f14e16bc114dc80e3b48ef')
FORCE = {
    'diagnostic.json': (3392, 'bbdf9d7b221b1ffaa50ea0ac0dae0c9da89ff060cfb690baeca95f67385c009c'),
    'inputs.json': (3510, 'b8907763d97e546c9bd603fdd6b2aff8ef12da332bffdbc7623860bb5d36b881'),
    'force-accuracy32/complete.json': (4658, 'd9da7bbe2d629c9bdd7c53a4c749e4d1fdfd5b3451283c8ce711c95ec0920c40'),
    'force-accuracy32/initial.json': (1135374, 'a223046766c5fdac047060d324a55e769ac2a487d3793a31285b98157265bc59'),
    'force-accuracy32/failed_last.json': (1185545, '5c64284e318acb894ff2251ce61b6ba2b2a6ce3db9ee432b814cae686dabe6ce'),
    'force-accuracy32/progress.jsonl': (27297, '9086b94a8b4904eec85d0df78e919d3ea52fc9c98ae81775b51eedad91f527dc'),
    'force-accuracy32/process-start.json': (387, 'dd45a53f6a82251ef6eb190e700483730b90f48441e8dac0e5c9d0236e995048'),
    'force-accuracy32/process.json': (99, '58ed2fd32cc75bacc1382949833c86b6677dd86cf0c0acb5bf0300f8e20ff2fa'),
    'force-accuracy32/stdout.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'force-accuracy32/stderr.log': (0, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
}
ALLOWED = {'docs/reference_cases/ge_beam3_curved_p5_centered_chord32_diagnostic.py',
           'tests/test_ge_beam3_curved_p5_centered_chord32_diagnostic.py',
           'docs/agent_plans/GE_BEAM3_CURVED_P5_CENTERED_CHORD32_PLAN.md'}
CASE = {'elements': 32, 'extent': 'ARCH_ONSET32', 'targets': [.1, .095],
        'iteration_limit': 16, 'backtracks': 10, 'mixed_evaluations_per_trial': 8192,
        'observation_limit_per_trial': 256, 'residual_limit': 1e-11,
        'total_local_force_budget': 1e-12, 'local_rotation_length': 2., 'local_force_scale': 1.,
        'assembly_schema': 'GE_BEAM3_P5_ASSEMBLY_CENTERED_CHORD_FORCE_ACCURACY_V1',
        'failure_snapshot': 'LAST_SUCCESSFUL_EVALUATION_NOT_COMMITTED',
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


def observation_inputs():
    for name, (size, digest) in OBSERVATION.items():
        data = shared.ordinary(OBSERVATION_ROOT/name)
        if len(data) != size or shared.sha(data) != digest:
            raise shared.RefinementError('preserved observation input hash mismatch')
    if set(p.relative_to(OBSERVATION_ROOT).as_posix() for p in OBSERVATION_ROOT.rglob('*') if p.is_file()) != set(OBSERVATION):
        raise shared.RefinementError('historical observation inventory changed')
    return {name: {'bytes': size, 'sha256': digest} for name, (size, digest) in OBSERVATION.items()}


def force_inputs():
    for name, (size, digest) in FORCE.items():
        data = shared.ordinary(FORCE_ROOT/name)
        if len(data) != size or shared.sha(data) != digest:
            raise shared.RefinementError('preserved force-accuracy input hash mismatch')
    if set(p.relative_to(FORCE_ROOT).as_posix() for p in FORCE_ROOT.rglob('*') if p.is_file()) != set(FORCE):
        raise shared.RefinementError('historical force-accuracy inventory changed')
    return {name: {'bytes': size, 'sha256': digest} for name, (size, digest) in FORCE.items()}


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
            'failed_inputs': failed_inputs(), 'observation_inputs': observation_inputs(), 'force_inputs': force_inputs()}


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
    if request_id in ('5b59e2613245422a922616891f8b003b', '5fbe008bfc7744079ed0e35d12dc72f1',
                      '69778aebc5d44cbd8f91e0426edc2232'):
        raise shared.RefinementError('historical request remains consumed regardless of pending ledger accounting')
    if any(p.name.endswith(request_id) and p.name != 'ge-beam3-centered-chord32-'+request_id
           for p in (manager/'claims').glob('*')):
        raise shared.RefinementError('request already claimed by another registered runner')
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
    from docs.reference_cases.ge_beam3_curved_p5_centered_chord import CenteredChordAssemblyHistoryProbe
    beam = CenteredChordAssemblyHistoryProbe(beam._references,
        [tuple(int(n) for n in row) for row in beam._maps], beam._sections,
        fixed_nodes=tuple(int(n) for n in beam._fixed), order=beam._order, extent=beam._extent)
    control = DisplacementControlledAssemblyProbe(beam, node=count)
    initial = control.trial(.1, observer=lambda event: observe({'state': 'INITIAL', 'event': event}))
    control.commit(initial)
    if digest(control.committed_model.replay()) != digest(initial.assembly.response):
        raise ValueError('initial diagnostic replay mismatch')
    bindings = {'initial': publish_raw('initial', asdict(initial))}
    before = digest(control.committed_model.committed)
    def save_failure(snapshot):
        from types import SimpleNamespace
        reconstructed = control.committed_model._reconstruct(SimpleNamespace(**snapshot))
        if digest(reconstructed) != digest(snapshot['response']):
            raise ValueError('failed last-evaluation replay mismatch')
        raw = dict(snapshot, replay_verified=True)
        raw['response'] = asdict(snapshot['response'])
        raw['origins'] = [[asdict(h) for h in origins] for origins in snapshot['origins']]
        bindings['failed_last'] = publish_raw('failed_last', raw)
    try:
        target = control.trial(.095, observer=lambda event: observe({'state': 'TARGET', 'event': event}),
                               failure_observer=save_failure)
    except DisplacementControlError as error:
        if control._pending is not None or digest(control.committed_model.committed) != before:
            raise ValueError('failed diagnostic trial changed committed state')
        failure = {'error_type': type(error).__name__, 'error': str(error),
                   'checkpoints': [asdict(c) for c in error.checkpoints], 'mixed_evaluations': error.evaluations}
        return {'elements': count, 'solver_outcome': 'FAILED', 'failure': failure, 'bindings': bindings,
                'failed_trial_uncommitted': True, 'failure_snapshot': 'failed_last' in bindings, 'initial_checkpoint_sha256': before,
                'production_qualified': False}
    control.commit(target)
    if digest(control.committed_model.replay()) != digest(target.assembly.response):
        raise ValueError('target diagnostic replay mismatch')
    bindings['target'] = publish_raw('target', asdict(target))
    return {'elements': count, 'solver_outcome': 'TARGET_CONVERGED', 'failure': None, 'bindings': bindings,
            'failed_trial_uncommitted': None, 'failure_snapshot': False, 'initial_checkpoint_sha256': before, 'production_qualified': False}


parse_observations = prior.parse_observations


def check_accuracy(response, count):
    expected = {'limit': CASE['total_local_force_budget']/count,
                'rotation_length': CASE['local_rotation_length'], 'force_scale': 1.}
    if set(response) != {'potential', 'residual', 'tangent', 'elements'}:
        raise ValueError('raw assembly response schema mismatch')
    elements = response['elements']
    if len(elements) != count or len(response['residual']) != 6*(2*count+1):
        raise ValueError('complete accuracy element inventory required')
    errors = []
    for element in elements:
        if (set(element) != {'potential', 'residual', 'tangent', 'local_rotations', 'moments', 'stations',
                'local_residual_norm', 'iterations', 'evaluations', 'accuracy_schema', 'force_accuracy', 'estimated_force_error'} or
                element.get('accuracy_schema') != CASE['assembly_schema'] or element.get('force_accuracy') != expected or
                any(type(v) is not float for v in element['force_accuracy'].values()) or
                type(element.get('estimated_force_error')) is not float or
                not 0 <= element['estimated_force_error'] <= expected['limit'] or
                not 0 <= element['local_residual_norm'] <= 1e-11 or len(element['residual']) != 18 or
                [(s['cell'], s['index']) for s in element['stations']] != [(c, i) for c in (0, 1) for i in range(8)]):
            raise ValueError('raw accuracy policy/estimate mismatch')
        errors.append(element['estimated_force_error'])
    if math.fsum(errors) > CASE['total_local_force_budget']:
        raise ValueError('aggregate estimated force error exceeds budget')


def check_snapshot(raw, count, initial, terminal):
    expected = {'schema', 'disposition', 'origin_epoch', 'target', 'positions', 'rotations', 'forces',
                'origins', 'response', 'residual_norm', 'mixed_evaluations', 'replay_verified'}
    if (set(raw) != expected or raw['schema'] != 'GE_BEAM3_P5_FAILED_LAST_EVALUATION_V1' or
            raw['disposition'] != 'UNCOMMITTED_DIAGNOSTIC_ONLY' or type(raw['origin_epoch']) is not int or raw['origin_epoch'] != 1 or
            raw['target'] != .095 or raw['replay_verified'] is not True or
            type(raw['mixed_evaluations']) is not int or not 0 < raw['mixed_evaluations'] <= terminal['mixed_evaluations']):
        raise ValueError('failed last-evaluation identity mismatch')
    histories = [[s['response']['history'] for s in e['stations']] for e in initial['assembly']['response']['elements']]
    if raw['origins'] != histories:
        raise ValueError('failed last-evaluation origin mismatch')
    n = 2*count+1
    if (len(raw['positions']) != n or len(raw['rotations']) != n or len(raw['forces']) != n or
            any(len(row) != 3 for row in raw['positions']+raw['forces']) or
            any(len(frame) != 3 or any(len(row) != 3 for row in frame) for frame in raw['rotations']) or
            len(raw['response']['residual']) != 6*n):
        raise ValueError('failed last-evaluation dimensions mismatch')
    if (raw['positions'][0] != initial['assembly']['positions'][0] or
            raw['positions'][-1] != initial['assembly']['positions'][-1] or
            raw['rotations'][0] != initial['assembly']['rotations'][0] or
            raw['rotations'][-1] != initial['assembly']['rotations'][-1] or
            raw['forces'][count][1] != raw['response']['residual'][6*count+1]):
        raise ValueError('failed last-evaluation clamp/reaction mismatch')
    check_accuracy(raw['response'], count)
    vector = []
    for i in range(1, n-1):
        vector.extend(raw['response']['residual'][6*i+j]-raw['forces'][i][j] for j in range(3))
        vector.extend(raw['response']['residual'][6*i+j]/2. for j in range(3, 6))
    norm = math.hypot(*vector)/max(1., math.hypot(*(v for row in raw['forces'] for v in row)))
    if (not math.isfinite(norm) or type(raw['residual_norm']) is not float or raw['residual_norm'] < 0 or
            abs(norm-raw['residual_norm']) > 1e-14*max(1e-300, norm)):
        raise ValueError('failed last-evaluation physical residual mismatch')


def inspect(folder, frozen, request_id, request_sha, *, count=32):
    packet = shared.load(folder/'complete.json')
    if (set(packet) != {'schema', 'authority', 'request_id', 'request_sha256', 'result'} or
            packet['schema'] != SCHEMA or packet['authority'] != frozen or packet['request_id'] != request_id or packet['request_sha256'] != request_sha):
        raise ValueError('diagnostic packet identity mismatch')
    result = packet['result'];groups = parse_observations(folder/'progress.jsonl', count=count)
    if (set(result) != {'elements', 'solver_outcome', 'failure', 'bindings', 'failed_trial_uncommitted', 'failure_snapshot', 'initial_checkpoint_sha256', 'production_qualified'} or
            result['elements'] != count or result['production_qualified'] is not False):
        raise ValueError('diagnostic result schema mismatch')
    outcome = 'FAILED' if groups['TARGET'][-1]['phase'] == 'FAILURE' else 'TARGET_CONVERGED'
    if result['solver_outcome'] != outcome: raise ValueError('solver outcome differs from observations')
    if type(result['failure_snapshot']) is not bool or outcome != 'FAILED' and result['failure_snapshot']:
        raise ValueError('failure snapshot disposition mismatch')
    expected = {'initial'} if outcome == 'FAILED' else {'initial', 'target'}
    if result['failure_snapshot']: expected.add('failed_last')
    if set(result['bindings']) != expected: raise ValueError('no fabricated absent target trial allowed')
    for name, binding in result['bindings'].items():
        if set(binding) != {'name', 'bytes', 'sha256'} or binding['name'] != name+'.json': raise ValueError('raw trial binding mismatch')
        path = folder/binding['name'];data = shared.ordinary(path)
        if len(data) != binding['bytes'] or shared.sha(data) != binding['sha256']: raise ValueError('raw trial hash mismatch')
        trial = shared.load(path)
        if name == 'failed_last':
            check_snapshot(trial, count, shared.load(folder/'initial.json'), groups['TARGET'][-1]);continue
        check_accuracy(trial['assembly']['response'], count)
        state = 'INITIAL' if name == 'initial' else 'TARGET'
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
        if events and not result['failure_snapshot']:
            raise ValueError('observed successful evaluation requires failure snapshot')
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
    folder = output/'centered-chord32'
    with (folder/'progress.jsonl').open('xb') as stream:
        def observe(row): stream.write(shared.canonical(row));stream.flush()
        result = capture(count=32, observe=observe, publish_raw=lambda name, raw: shared.publish(folder/(name+'.json'), raw))
    if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha):
        raise ValueError('observation authority changed')
    shared.publish(folder/'complete.json', {'schema': SCHEMA, 'authority': frozen, 'request_id': request_id,
                                         'request_sha256': request_sha, 'result': result})


def _coordinate(repo, commit, output):
    frozen = authority(repo, commit);request_id, request_sha = lease(repo, commit, output)
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(repo.resolve()) or output.resolve().is_relative_to(FAILED_ROOT.resolve()) or output.resolve().is_relative_to(OBSERVATION_ROOT.resolve()) or output.resolve().is_relative_to(FORCE_ROOT.resolve()):
        raise ValueError('fresh external observation output required')
    (MANAGER/'claims'/('ge-beam3-centered-chord32-'+request_id)).mkdir();output.mkdir(parents=True, exist_ok=False)
    shared.publish(output/'inputs.json', {'authority': frozen, 'case': CASE, 'request_id': request_id, 'request_sha256': request_sha})
    folder = output/'centered-chord32';folder.mkdir();process = None
    try:
        env = dict(os.environ, **shared.THREAD_ENVIRONMENT, PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
        env['PYTHONPATH'] = str(repo/'src')+os.pathsep+str(shared.SIBLING/'src')
        line = [sys.executable, '-B', '-m', MODULE, '--worker', '--commit', commit, '--output', str(output)]
        process = shared.run_child(line, folder, repo, env, timeout=600., inactivity=300., memory=24*(1 << 30))
        shared.publish(folder/'process.json', process)
        if process['exit_code'] != 0: raise ValueError('observation worker failed; no retry')
        packet, groups = inspect(folder, frozen, request_id, request_sha)
        if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha): raise ValueError('final observation authority mismatch')
        result = {'schema': SCHEMA, 'disposition': 'RESEARCH_CENTERED_CHORD_COMPARISON_CAPTURED',
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
