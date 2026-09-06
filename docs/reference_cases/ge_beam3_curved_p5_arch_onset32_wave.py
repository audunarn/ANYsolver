"""Explicit 32-element successor of the consumed 4/8/16 research wave.

One fresh resource request, one contained child, no retry. Historical output
is read-only background; no old worker is rerun or reclassified.
"""

import argparse
import os
from pathlib import Path
import re
import sys
import threading

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_wave as prior
from docs.reference_cases import ge_beam3_curved_p5_arch_onset_probe as probe


BASE = 'ef7964287245829b0112ae81179d314c5c2f00cb'
SCHEMA = 'GE_BEAM3_P5_ARCH_ONSET32_RESEARCH_V1'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_arch_onset32_wave'
PROFILE = 'ARCH_ONSET32'
MANAGER = prior.MANAGER
PREVIOUS = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-onset-20260906-4e2f54a71be94bb1ad3a0b5df77dad05/aggregate.json')
PREVIOUS_BINDING = (5160, 'dba974aa285ef1f25073fe3b539eeabdb6dc8627d96affae6abbcf1f8e62ed58')
ALLOWED = {
    'docs/reference_cases/ge_beam3_curved_p5_assembly_history_probe.py',
    'docs/reference_cases/ge_beam3_curved_p5_arch_refinement_case.py',
    'docs/reference_cases/ge_beam3_curved_p5_arch_stability_inspection.py',
    'docs/reference_cases/ge_beam3_curved_p5_arch_onset_probe.py',
    'docs/reference_cases/ge_beam3_curved_p5_arch_onset_wave.py',
    'docs/reference_cases/ge_beam3_curved_p5_arch_onset32_wave.py',
    'tests/test_ge_beam3_curved_p5_arch_onset32_extent.py',
    'tests/test_ge_beam3_curved_p5_arch_onset32_wave.py',
    'docs/agent_plans/GE_BEAM3_CURVED_P5_ARCH_ONSET32_PLAN.md',
}
CASE = dict(prior.CASE, meshes=[32], extent=PROFILE, nodes=65, free_dimension=378,
            stations_per_state=512, maximum_states=29, wave_seconds=900,
            previous_aggregate={'bytes': PREVIOUS_BINDING[0], 'sha256': PREVIOUS_BINDING[1]})


def previous():
    data = prior.ordinary(PREVIOUS)
    if len(data) != PREVIOUS_BINDING[0] or prior.sha(data) != PREVIOUS_BINDING[1]:
        raise prior.RefinementError('preserved onset aggregate byte/hash mismatch')
    record = prior.load(PREVIOUS)
    if (record['schema'] != prior.SCHEMA or record['production_qualified'] is not False or
            [r['elements'] for r in record['comparisons']] != [4, 8, 16]):
        raise prior.RefinementError('preserved onset result schema mismatch')
    return record


def authority(repo, commit):
    if not re.fullmatch('[0-9a-f]{40}', commit) or prior.git(repo, 'rev-parse', 'HEAD') != commit:
        raise prior.RefinementError('frozen onset32 commit mismatch')
    if prior.git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise prior.RefinementError('dirty onset32 inputs')
    if (prior.git(repo, 'rev-parse', 'HEAD^') != BASE or
            set(prior.git(repo, 'diff', '--name-only', BASE, commit).splitlines()) != ALLOWED):
        raise prior.RefinementError('exact onset32 parent/path set required')
    if (prior.git(prior.SIBLING, 'status', '--porcelain', '--untracked-files=all') or
            prior.git(prior.SIBLING, 'rev-parse', 'HEAD') != prior.SIBLING_COMMIT or
            prior.git(prior.SIBLING, 'rev-parse', 'HEAD^{tree}') != prior.SIBLING_TREE):
        raise prior.RefinementError('onset32 frozen sibling mismatch')
    environment = prior.environment()
    if prior.sha(prior.canonical(environment)) != prior.ENVIRONMENT_SHA:
        raise prior.RefinementError('onset32 frozen environment mismatch')
    prior.references();previous()
    return {'commit': commit, 'tree': prior.git(repo, 'rev-parse', 'HEAD^{tree}'),
            'case_sha256': prior.sha(prior.canonical(CASE)), 'environment': environment,
            'sibling_commit': prior.SIBLING_COMMIT, 'sibling_tree': prior.SIBLING_TREE,
            'references': {str(k): {'bytes': v[0], 'sha256': v[1]} for k, v in prior.ROOTS.items()},
            'previous_aggregate': CASE['previous_aggregate']}


def command(repo, commit, output):
    return f"& '{sys.executable}' -B -m {MODULE} --coordinate --commit {commit} --output '{Path(output)}'"


def lease(repo, commit, output, *, manager=None):
    manager = MANAGER if manager is None else Path(manager)
    owner = prior.load(manager/'active-lock/owner.json', strict=False)
    request_id = owner.get('request_id')
    if not isinstance(request_id, str) or not re.fullmatch('[0-9a-f]{32}', request_id):
        raise prior.RefinementError('onset32 active resource lease required')
    path = manager/'requests'/(request_id+'.json');request = prior.load(path, strict=False)
    for value in (owner, request):
        if (value.get('request_id') != request_id or value.get('command') != command(repo, commit, output) or
                Path(value.get('repository', '')).resolve() != Path(repo).resolve()):
            raise prior.RefinementError('exact onset32 command/lease mismatch')
    rows = [[v.strip() for v in line.split('|')[1:-1]] for line in
            (manager/'ledger.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('|')]
    if [r[2] for r in rows if len(r) > 2 and r[1] == request_id] != ['APPROVED']:
        raise prior.RefinementError('one unconsumed onset32 approval required')
    return request_id, prior.sha(path.read_bytes())


def worker(repo, commit, output):
    frozen = authority(repo, commit);request_id, request_sha = lease(repo, commit, output)
    folder = output/'elements-32'
    with (folder/'progress.jsonl').open('xb') as stream:
        def progress(phase, label):
            stream.write(prior.canonical({'phase': phase, 'id': label}));stream.flush()
        result = probe.records(count=32, extent=PROFILE, progress=progress,
                               publish_raw=lambda label, raw: prior.publish(folder/(label+'.json'), raw))
        if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha):
            raise prior.RefinementError('onset32 worker authority changed')
        prior.publish(folder/'complete.json', {'schema': SCHEMA, 'authority': frozen,
            'request_id': request_id, 'request_sha256': request_sha, 'result': result})
        progress('COMPLETION', None)


def compare(packet, roots, historical):
    result = packet['result']
    if result['elements'] != 32:
        raise prior.RefinementError('one exact 32-element result required')
    row = {'elements': 32, 'disposition': result['disposition'], 'comparison': None}
    if result['bracket'] is not None:
        indexed = {r['id']: r for r in result['samples']}
        ends = [indexed[result['bracket'][k]] for k in ('left_id', 'right_id')]
        row['comparison'] = {'discrete_drop_endpoints': [r['drop'] for r in ends],
            'discrete_load_at_endpoints': [r['load'] for r in ends],
            'continuum': {stride: {side: {'drop': value['result'][side]['displacement'],
                'load': value['result'][side]['load'],
                'discrete_endpoint_relative_drop_errors': [r['drop']/value['result'][side]['displacement']-1 for r in ends],
                'discrete_endpoint_relative_load_errors': [r['load']/value['result'][side]['load']-1 for r in ends]}
                for side in ('left', 'right')} for stride, value in roots.items()}}
    return {'schema': SCHEMA, 'disposition': 'RESEARCH_ONSET32_DIAGNOSTICS_COMPLETE',
            'production_qualified': False, 'accuracy_qualified': False, 'first_critical_point_proven': False,
            'restriction': probe.RESTRICTION, 'current': row,
            'historical_comparisons': historical['comparisons'], 'historical_recomputed': False}


def _coordinate(repo, commit, output):
    frozen = authority(repo, commit);request_id, request_sha = lease(repo, commit, output)
    if (output.exists() or output.is_symlink() or output.resolve().is_relative_to(repo.resolve()) or
            output.resolve().is_relative_to(prior.REFERENCE.resolve()) or
            output.resolve().is_relative_to(PREVIOUS.parent.resolve())):
        raise prior.RefinementError('fresh external onset32 output required')
    (MANAGER/'claims'/('ge-beam3-onset32-'+request_id)).mkdir()
    output.mkdir(parents=True, exist_ok=False)
    prior.publish(output/'inputs.json', {'authority': frozen, 'case': CASE,
                                        'request_id': request_id, 'request_sha256': request_sha})
    folder = output/'elements-32';folder.mkdir();process = None
    try:
        env = dict(os.environ, **prior.THREAD_ENVIRONMENT, PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
        env['PYTHONPATH'] = str(repo/'src')+os.pathsep+str(prior.SIBLING/'src')
        line = [sys.executable, '-B', '-m', MODULE, '--worker', '--commit', commit, '--output', str(output)]
        process = prior.run_child(line, folder, repo, env, timeout=600., inactivity=300., memory=24*(1 << 30))
        prior.publish(folder/'process.json', process)
        if process['exit_code'] != 0: raise prior.RefinementError('onset32 worker failed; no retry')
        packet = prior.inspect_worker(folder, 32, frozen, request_id, request_sha, extent=PROFILE, schema=SCHEMA)
        if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha):
            raise prior.RefinementError('onset32 final authority mismatch')
        result = compare(packet, prior.references(), previous())
        result.update(authority=frozen, request_id=request_id, request_sha256=request_sha,
                      worker_sha256=prior.sha((folder/'complete.json').read_bytes()))
        prior.publish(output/'aggregate.json', result)
        return result
    except BaseException as exc:
        prior.publish(output/'blocked-diagnostic.json', {'schema': SCHEMA, 'production_qualified': False,
            'request_id': request_id, 'error_type': type(exc).__name__, 'error': str(exc), 'process': process})
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
    for key, value in prior.THREAD_ENVIRONMENT.items(): os.environ[key] = value
    if args.coordinate: print(prior.canonical(coordinate(repo, args.commit, args.output.resolve())).decode(), end='')
    else: worker(repo, args.commit, args.output.resolve())


if __name__ == '__main__': main()
