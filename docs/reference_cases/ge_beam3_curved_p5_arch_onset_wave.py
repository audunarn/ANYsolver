"""One-use, serial, contained P5 lateral-onset research wave.

This is integrity validation of discrete diagnostics, not an independently
authored mechanics oracle. No production qualification follows from any result.
"""

import argparse
import importlib.metadata
import math
import os
from pathlib import Path
import re
import stat
import sys
import threading
import time

from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import (
    canonical, sha, load, publish, git, run_child, THREAD_ENVIRONMENT, RefinementError,
)
from docs.reference_cases import ge_beam3_curved_p5_arch_onset_probe as probe


BASE = '3d7dd492180f4d6658d832d5a71ca7a4a028aadb'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_arch_onset_wave'
SCHEMA = 'GE_BEAM3_P5_ARCH_ONSET_WAVE_V1'
MANAGER = Path('C:/Github/.resource-manager')
REFERENCE = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-lateral-knot-20260906-e10841364c644b29b60f7c057c20a41e')
ROOTS = {1: (29126, '64c47952dacd030d81ec3a631744179c300c33052551e1ebe5c16a9e191019fc'),
         2: (29139, 'a7917c813953d181df20748c5e54179e0f84597585650b641fbd46b90e8f073c')}
SIBLING = Path('C:/Github/ANYfileIO')
SIBLING_COMMIT = 'b48ba51c7b79e6d64b3f99c1fb131b9b602e7e1d'
SIBLING_TREE = '29cb248a8d320607e21424c68625c4af6a949da1'
ENVIRONMENT_SHA = '2cd226a5cf78c9cc833dcbaf7e4cd0c8eab92dd8566af69412e13d346dc298f4'
ALLOWED = {'docs/reference_cases/ge_beam3_curved_p5_arch_onset_wave.py',
           'tests/test_ge_beam3_curved_p5_arch_onset_wave.py',
           'docs/agent_plans/GE_BEAM3_CURVED_P5_ARCH_ONSET_WAVE_PLAN.md'}
CASE = {'meshes': [4, 8, 16], 'drops': list(probe.DROPS), 'bisections': 16,
        'bracket_width': 1e-7, 'height': .1, 'span': 2., 'order': 8,
        'section_diagonal': [1000., 400., 400., .02, .01, .02],
        'physical_limit': 1e-11, 'max_iterations': 16, 'mixed_budget_per_element': 256,
        'child_seconds': 600, 'wave_seconds': 1800, 'inactivity_seconds': 300,
        'tree_memory_bytes': 24*(1 << 30), 'automatic_retry': False}


def ordinary(path):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise RefinementError('ordinary non-reparse input required')
    for parent in path.parents:
        if getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400 or parent.is_symlink():
            raise RefinementError('input has reparse ancestor')
    return path.read_bytes()


def environment():
    """Hash installed numerical files without importing their package code."""
    packages = {}
    for name in ('numpy', 'scipy'):
        distribution = importlib.metadata.distribution(name)
        files = []
        for item in sorted(distribution.files or (), key=str):
            if str(item).endswith('.pyc') or '__pycache__' in str(item):
                continue
            data = ordinary(distribution.locate_file(item))
            files.append({'path': str(item), 'bytes': len(data), 'sha256': sha(data)})
        if not files:
            raise RefinementError('complete installed distribution inventory required')
        packages[name] = {'version': distribution.version, 'files': len(files),
                          'inventory_sha256': sha(canonical(files))}
    return {'python': str(Path(sys.executable).resolve()), 'version': sys.version,
            'python_sha256': sha(ordinary(sys.executable)), 'packages': packages}


def references(folder=REFERENCE):
    made = {}
    for stride, (size, digest) in ROOTS.items():
        path = Path(folder)/f'root-stride-{stride}.json'
        data = ordinary(path)
        if len(data) != size or sha(data) != digest:
            raise RefinementError('frozen continuum endpoint hash mismatch')
        record = load(path)
        if (record['schema'] != 'GE_BEAM3_P5_KNOT_RESOLVED_LATERAL_REFERENCE_V1' or
                record['production_qualified'] is not False):
            raise RefinementError('continuum successor schema mismatch')
        made[str(stride)] = record
    return made


def authority(repo, commit):
    if not re.fullmatch('[0-9a-f]{40}', commit) or git(repo, 'rev-parse', 'HEAD') != commit:
        raise RefinementError('frozen onset commit mismatch')
    if git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise RefinementError('dirty onset input')
    if (git(repo, 'rev-parse', 'HEAD^') != BASE or
            set(git(repo, 'diff', '--name-only', BASE, commit).splitlines()) != ALLOWED):
        raise RefinementError('exact onset parent/path set required')
    if (git(SIBLING, 'status', '--porcelain', '--untracked-files=all') or
            git(SIBLING, 'rev-parse', 'HEAD') != SIBLING_COMMIT or
            git(SIBLING, 'rev-parse', 'HEAD^{tree}') != SIBLING_TREE):
        raise RefinementError('frozen sibling mismatch')
    env = environment()
    if sha(canonical(env)) != ENVIRONMENT_SHA:
        raise RefinementError('frozen numerical environment mismatch')
    references()
    return {'commit': commit, 'tree': git(repo, 'rev-parse', 'HEAD^{tree}'),
            'case_sha256': sha(canonical(CASE)), 'environment': env,
            'sibling_commit': SIBLING_COMMIT, 'sibling_tree': SIBLING_TREE,
            'references': {str(k): {'bytes': v[0], 'sha256': v[1]} for k, v in ROOTS.items()}}


def command(repo, commit, output):
    return f"& '{sys.executable}' -B -m {MODULE} --coordinate --commit {commit} --output '{Path(output)}'"


def lease(repo, commit, output, *, manager=None):
    manager = MANAGER if manager is None else Path(manager)
    owner = load(manager/'active-lock/owner.json', strict=False)
    request_id = owner.get('request_id')
    if not isinstance(request_id, str) or not re.fullmatch('[0-9a-f]{32}', request_id):
        raise RefinementError('active onset resource lease required')
    path = manager/'requests'/(request_id+'.json')
    request = load(path, strict=False)
    for value in (request, owner):
        if (value.get('request_id') != request_id or
                value.get('command') != command(repo, commit, output) or
                Path(value.get('repository', '')).resolve() != Path(repo).resolve()):
            raise RefinementError('exact onset command/lease mismatch')
    rows = [[v.strip() for v in line.split('|')[1:-1]] for line in
            (manager/'ledger.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('|')]
    if [r[2] for r in rows if len(r) > 2 and r[1] == request_id] != ['APPROVED']:
        raise RefinementError('one unconsumed administrator approval required')
    return request_id, sha(path.read_bytes())


def worker(repo, commit, output, count):
    frozen = authority(repo, commit)
    request_id, request_sha = lease(repo, commit, output)
    if count not in probe.MESHES:
        raise RefinementError('registered worker mesh required')
    folder = output/f'elements-{count:02}'
    with (folder/'progress.jsonl').open('xb') as stream:
        def progress(phase, label):
            stream.write(canonical({'phase': phase, 'id': label}));stream.flush()
        result = probe.records(count=count, progress=progress,
                               publish_raw=lambda label, raw: publish(folder/(label+'.json'), raw))
        if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha):
            raise RefinementError('authority changed in onset worker')
        publish(folder/'complete.json', {'schema': SCHEMA, 'authority': frozen,
                'request_id': request_id, 'request_sha256': request_sha, 'result': result})
        progress('COMPLETION', None)


def check_raw(raw, sample, count):
    """Recompute spectra and physical state checks, not element mechanics."""
    import numpy as np
    from docs.reference_cases.ge_beam3_curved_p5_arch_stability_inspection import classify_matrix
    if (set(raw) != {'id', 'origin_id', 'elements', 'sample', 'state_errors', 'trial', 'spectra', 'production_qualified'} or
            raw['production_qualified'] is not False or raw['elements'] != count or
            raw['id'] != sample['id'] or raw['origin_id'] != sample['origin_id'] or
            raw['sample'] != {k: v for k, v in sample.items() if k not in ('id', 'origin_id', 'sign')}):
        raise RefinementError('raw onset identity/sample mismatch')
    trial = raw['trial'];assembly = trial['assembly'];response = assembly['response']
    nodes = 2*count+1
    def array(value, shape):
        made = np.asarray(value, dtype=float)
        if made.shape != shape or not np.isfinite(made).all():
            raise RefinementError('finite raw array shape required')
        return made
    x = array(assembly['positions'], (nodes, 3));q = array(assembly['rotations'], (nodes, 3, 3))
    f = array(assembly['forces'], (nodes, 3));r = array(response['residual'], (6*nodes,)).reshape(nodes, 6)
    h = array(response['tangent'], (6*nodes, 6*nodes))
    expected = np.zeros_like(f);expected[count, 1] = -sample['load']
    residual = r.copy();residual[:, :3] -= expected
    scaled = residual[1:-1].copy();scaled[:, 3:] /= 2.
    norm = float(np.linalg.norm(scaled))/max(1., float(np.linalg.norm(expected)))
    s = np.diag([1., 1., -1.])
    checks = {'equilibrium': norm, 'position_planarity': float(np.max(np.abs(x[:, 2]))),
              'rotation_planarity': float(np.max(np.abs(q-s@q@s))),
              'rotation_orthogonality': float(np.max(np.abs(q.transpose(0, 2, 1)@q-np.eye(3)))),
              'rotation_determinant': float(np.max(np.abs(np.linalg.det(q)-1))),
              'fixed_positions': float(np.max(np.abs(x[[0, -1]]-[[-1., 0., 0.], [1., 0., 0.]]))),
              'fixed_rotations': float(np.max(np.abs(q[[0, -1]]-np.eye(3)))),
              'load_pattern': float(np.max(np.abs(f-expected)))}
    if (set(raw['state_errors']) != set(checks) or any(v > probe.LIMIT for v in checks.values()) or
            any(abs(raw['state_errors'][k]-v) > 1e-14 for k, v in checks.items())):
        raise RefinementError('raw physical-state checks disagree')
    if (trial['control_dof'] != 6*count+1 or trial['target'] != .1-sample['drop'] or
            x[count, 1] != trial['target'] or not 0 <= assembly['residual_norm'] <= probe.LIMIT or
            abs(assembly['residual_norm']-norm) > 1e-14 or
            type(assembly['iterations']) is not int or not 0 <= assembly['iterations'] <= 16 or
            type(assembly['mixed_evaluations']) is not int or not 0 <= assembly['mixed_evaluations'] <= 256*count or
            not math.isfinite(trial['reaction_derivative']) or len(response['elements']) != count or
            any(len(e['stations']) != 16 for e in response['elements']) or
            len(assembly['origins']) != count or
            any(len(group) != 16 or any(s != {'accumulated': 0., 'plastic_coordinate': 0.} for s in group)
                for group in assembly['origins']) or
            any(s['response']['plastic_active'] or s['response']['history'] != {'accumulated': 0., 'plastic_coordinate': 0.}
                for e in response['elements'] for s in e['stations'])):
        raise RefinementError('raw target/budget/station/history mismatch')
    reconstructed = classify_matrix(h, nodes=nodes)
    if canonical(reconstructed) != canonical(raw['spectra']):
        raise RefinementError('raw tangent/spectral reconstruction mismatch')
    odd = reconstructed['out_of_plane']
    if (sample['lowest'] != odd['values'][0] or sample['uncertainty'] != odd['uncertainty_band'] or
            sample['negative'] != odd['negative'] or sample['unresolved'] != odd['unresolved']):
        raise RefinementError('raw spectral summary mismatch')


def inspect_worker(folder, count, frozen, request_id, request_sha):
    packet = load(folder/'complete.json')
    if (set(packet) != {'schema', 'authority', 'request_id', 'request_sha256', 'result'} or
            packet['schema'] != SCHEMA or packet['authority'] != frozen or
            packet['request_id'] != request_id or packet['request_sha256'] != request_sha):
        raise RefinementError('onset worker identity mismatch')
    result = packet['result'];samples = result['samples'];bindings = result['raw_bindings']
    if not len(probe.DROPS) <= len(samples) <= len(probe.DROPS)+probe.MAX_BISECTIONS:
        raise RefinementError('onset sample budget mismatch')
    if len(bindings) != len(samples) or set(bindings) != {r['id'] for r in samples}:
        raise RefinementError('exact raw inventory required')
    visited = {};cursor = iter(samples)
    def evaluate(label, drop, origin):
        sample = next(cursor)
        if sample['id'] != label or sample['origin_id'] != origin or sample['drop'] != drop:
            raise RefinementError('onset search/origin graph mismatch')
        binding = bindings[label]
        if (set(binding) != {'name', 'bytes', 'sha256'} or binding['name'] != label+'.json' or
                type(binding['bytes']) is not int or binding['bytes'] <= 0):
            raise RefinementError('onset raw binding schema mismatch')
        path = folder/binding['name'];data = ordinary(path)
        if len(data) != binding['bytes'] or sha(data) != binding['sha256']:
            raise RefinementError('onset raw hash mismatch')
        raw = load(path);check_raw(raw, sample, count)
        epoch = 0 if origin is None else visited[origin]+1
        if (type(raw['trial']['origin_epoch']) is not int or type(raw['trial']['assembly']['origin_epoch']) is not int or
                raw['trial']['origin_epoch'] != epoch or raw['trial']['assembly']['origin_epoch'] != epoch):
            raise RefinementError('onset accepted origin epoch mismatch')
        visited[label] = epoch
        return raw['sample']
    rebuilt = probe.locate(evaluate)
    rebuilt.update(elements=count, raw_bindings=bindings)
    if next(cursor, None) is not None or canonical(rebuilt) != canonical(result):
        raise RefinementError('onset adjudication/coverage mismatch')
    allowed = set(bindings[k]['name'] for k in bindings) | {
        'complete.json', 'progress.jsonl', 'stdout.log', 'stderr.log', 'process-start.json', 'process.json'}
    if any(p.name not in allowed or not p.is_file() for p in folder.iterdir()):
        raise RefinementError('unregistered worker file')
    return packet


def adjudicate(packets, roots):
    if [p['result']['elements'] for p in packets] != list(probe.MESHES):
        raise RefinementError('all three ordered onset meshes required')
    comparisons = []
    for packet in packets:
        result = packet['result'];indexed = {r['id']: r for r in result['samples']}
        item = {'elements': result['elements'], 'disposition': result['disposition'], 'comparison': None}
        if result['bracket'] is not None:
            left, right = (indexed[result['bracket'][k]] for k in ('left_id', 'right_id'))
            item['comparison'] = {'discrete_drop_endpoints': [left['drop'], right['drop']],
                'discrete_load_at_endpoints': [left['load'], right['load']],
                'continuum': {stride: {side: {'drop': value['result'][side]['displacement'],
                    'load': value['result'][side]['load'],
                    'discrete_endpoint_relative_drop_errors': [r['drop']/value['result'][side]['displacement']-1 for r in (left, right)],
                    'discrete_endpoint_relative_load_errors': [r['load']/value['result'][side]['load']-1 for r in (left, right)]}
                    for side in ('left', 'right')} for stride, value in roots.items()}}
        comparisons.append(item)
    return {'schema': SCHEMA, 'disposition': 'RESEARCH_ONSET_DIAGNOSTICS_COMPLETE',
            'production_qualified': False, 'restriction': probe.RESTRICTION,
            'first_critical_point_proven': False, 'accuracy_qualified': False,
            'comparisons': comparisons}


def _coordinate(repo, commit, output, started):
    frozen = authority(repo, commit);request_id, request_sha = lease(repo, commit, output)
    if (output.exists() or output.is_symlink() or output.resolve().is_relative_to(repo.resolve()) or
            output.resolve().is_relative_to(REFERENCE.resolve())):
        raise RefinementError('fresh external onset output required')
    (MANAGER/'claims'/('ge-beam3-onset-'+request_id)).mkdir()
    output.mkdir(parents=True, exist_ok=False)
    publish(output/'inputs.json', {'authority': frozen, 'case': CASE,
                                 'request_id': request_id, 'request_sha256': request_sha})
    packets, processes = [], []
    env = dict(os.environ, **THREAD_ENVIRONMENT, PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
    env['PYTHONPATH'] = str(repo/'src')+os.pathsep+str(SIBLING/'src')
    try:
        for count in probe.MESHES:
            remaining = 1740-(time.monotonic()-started)
            if remaining <= 0: raise RefinementError('onset wave budget exhausted')
            folder = output/f'elements-{count:02}';folder.mkdir()
            line = [sys.executable, '-B', '-m', MODULE, '--worker', str(count), '--commit', commit, '--output', str(output)]
            process = run_child(line, folder, repo, env, timeout=min(600., remaining),
                                inactivity=300., memory=24*(1 << 30))
            processes.append(process);publish(folder/'process.json', process)
            if process['exit_code'] != 0: raise RefinementError('onset worker failed; no retry')
            packets.append(inspect_worker(folder, count, frozen, request_id, request_sha))
        if authority(repo, commit) != frozen or lease(repo, commit, output) != (request_id, request_sha):
            raise RefinementError('onset final authority mismatch')
        result = adjudicate(packets, references())
        result.update(authority=frozen, request_id=request_id, request_sha256=request_sha,
                      worker_hashes=[sha((output/f'elements-{n:02}'/'complete.json').read_bytes()) for n in probe.MESHES])
        publish(output/'aggregate.json', result)
        return result
    except BaseException as exc:
        publish(output/'blocked-diagnostic.json', {'schema': SCHEMA, 'production_qualified': False,
            'request_id': request_id, 'error_type': type(exc).__name__, 'error': str(exc), 'processes': processes})
        raise


def coordinate(repo, commit, output):
    started = time.monotonic();finished = threading.Event()
    def stop():
        if not finished.wait(1780.): os._exit(124)
    threading.Thread(target=stop, daemon=True).start()
    try: return _coordinate(repo, commit, output, started)
    finally: finished.set()


def main():
    parser = argparse.ArgumentParser();modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--coordinate', action='store_true');modes.add_argument('--worker', type=int, choices=probe.MESHES)
    parser.add_argument('--commit', required=True);parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args();repo = Path(__file__).resolve().parents[2]
    # Bind single-thread numerics in the validator as well as child processes.
    for key, value in THREAD_ENVIRONMENT.items(): os.environ[key] = value
    if args.coordinate:
        print(canonical(coordinate(repo, args.commit, args.output.resolve())).decode(), end='')
    else: worker(repo, args.commit, args.output.resolve(), args.worker)


if __name__ == '__main__': main()
