"""One-use supervised independent classical primal Ritz reference sequence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from numbers import Real
import os
from pathlib import Path
import sys
import time
import zipfile

import b3_e4_f03_area_feasibility as supervisor

ROOT = Path(__file__).resolve().parents[1]
LEVELS = (4, 8, 12, 16, 24)
CASES = {f'n{n:02d}': {'degree': n, 'primal_count': 2*(n*n-1)} for n in LEVELS}
MAX_SECONDS = 900
MAX_RSS_BYTES = 8*1024**3
LAUNCH_CUTOFF_SECONDS = 3600
KIND = 'experimental-independent-classical-primal-ritz-v1'
SCOPE = 'bounded classical primal reference only; no native qualification, family selection or G0B closure'
SOURCES = ('b3_e4_f03_primal_ritz.py', '_b3_e4_f03_primal_ritz.py',
           '_b3_e4_f03_primal_checks.py', '_b3_e4_f03_primal_functional.py',
           '_b3_e4_f03_primal_archive.py', '_b3_e4_f03_primal_trends.py',
           'b3_e4_f03_area_feasibility.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def contract():
    from _b3_e4_f03_primal_checks import LIMITS
    return {'kind': KIND, 'cases': CASES, 'scope': SCOPE,
            'identity': supervisor._identity(),
            'threads': {name: '1' for name in supervisor.THREADS},
            'limits': {'seconds_per_case': MAX_SECONDS, 'rss_bytes_per_case': MAX_RSS_BYTES,
                       'launch_cutoff_seconds': LAUNCH_CUTOFF_SECONDS, 'numerical': LIMITS},
            'physical_model': {'halfwidth_m': .05, 'ell_m': .46,
                'basis': '(1-X^2) P_i(X) P_j(Y), i=0..n-2,j=0..n; both displacement components',
                'canonical_quadrature': {'polynomial': 'n+1', 'load': 48},
                'crosscheck_quadrature': {'polynomial': 'n+3', 'load': 64},
                'full_dual_quadrature': [48, 64], 'root_constraints': 3,
                'equilibrium_solves_per_case': 1, 'assembly_descriptions_per_case': 2},
            'terminal': ['FAILED_EVIDENCE', 'FAILED_EXECUTION', 'FAILED_NUMERICAL_SCREEN',
                         'UNRESOLVED_RITZ_REFERENCE', 'PASSED_BOUNDED_PRIMAL_REFERENCE']}


def register(root):
    if not supervisor._clean():
        raise ValueError('commit candidate before reference registration')
    root.relative_to(ROOT/'.qualification/b3-ge-e4-pl')
    manifest = contract()
    manifest['created_utc'] = datetime.now(timezone.utc).isoformat()
    root.mkdir(parents=True, exist_ok=False)
    supervisor._json_new(root/'registration.json', manifest)
    with (root/'registration.sha256').open('x', encoding='ascii') as stream:
        stream.write(sha(root/'registration.json')+'\n')


def registered(root):
    supervisor._registration_hash(root)
    manifest = read(root/'registration.json')
    saved_contract = {k: v for k, v in manifest.items() if k != 'created_utc'}
    if (set(manifest) != set(contract()) | {'created_utc'} or saved_contract != contract()
            or not datetime.fromisoformat(manifest['created_utc']).tzinfo):
        raise ValueError('reference source, environment, inventory or contract changed')
    return manifest


def observable_event(directory, name, spec, capture_state):
    if capture_state is not False or spec != CASES[name]:
        raise ValueError('unregistered reference event inventory')
    return {'phase': 'observables', 'case': name,
            'sha256': sha(directory/'observables.json'),
            'arrays_sha256': sha(directory/'arrays.npz'),
            'child_started_sha256': sha(directory/'child_started.json')}


def child(root, name):
    manifest = registered(root)
    if name not in CASES or any(os.environ.get(k) != '1' for k in supervisor.THREADS):
        raise ValueError('unregistered child or numerical thread setting')
    directory = root/name
    # Written exclusively before any scientific construction or evaluation.
    # Registration may import constants; it cannot execute a case.
    supervisor._json_new(directory/'child_started.json', {'case': name,
        'registration_sha256': supervisor._registration_hash(root), 'pid': os.getpid(),
        'started_unix_seconds': time.time()})
    import numpy as np
    from threadpoolctl import threadpool_info
    import _b3_e4_f03_primal_checks as checks
    import _b3_e4_f03_primal_archive as archive
    pools = threadpool_info()
    if not pools or any(pool['num_threads'] != 1 for pool in pools):
        raise ValueError('reference numerical pools must be single-threaded')
    print(json.dumps({'phase': 'identity', 'case': name, 'identity': manifest['identity'],
        'registration_sha256': supervisor._registration_hash(root), 'threadpools': pools}), flush=True)
    n = CASES[name]['degree']
    metrics, arrays = checks.evaluate_case(n)
    with (directory/'arrays.npz').open('xb') as stream:
        np.savez_compressed(stream, **archive.pack(arrays, n))
    restored = archive.unpack(directory/'arrays.npz', n)
    verified = checks.verify_saved(restored, n)
    bind_metrics(metrics, verified)
    supervisor._json_new(directory/'observables.json', {'metrics': verified,
        'equilibrium_solves': 1, 'assembly_descriptions': 2, 'scope': SCOPE})
    print(json.dumps(observable_event(directory, name, CASES[name], False)), flush=True)


def bind_metrics(first, second, path='metrics'):
    """Compare pure recomputation without hiding inventory or boolean changes."""
    if isinstance(second, dict):
        if not isinstance(first, dict) or set(first) != set(second):
            raise ValueError(f'recomputed reference metric inventory changed: {path}')
        for name in second:
            bind_metrics(first[name], second[name], path+'/'+str(name))
    elif isinstance(second, list):
        if not isinstance(first, list) or len(first) != len(second):
            raise ValueError(f'recomputed reference metric shape changed: {path}')
        for i, (a, b) in enumerate(zip(first, second)):
            bind_metrics(a, b, path+'/'+str(i))
    elif isinstance(second, Real) and not isinstance(second, bool):
        if (not isinstance(first, Real) or isinstance(first, bool) or not math.isfinite(first)
                or not math.isfinite(second) or not math.isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)):
            raise ValueError(f'reference metric differs from saved actions: {path}')
    elif type(first) is not type(second) or first != second:
        raise ValueError(f'reference metric value changed: {path}')


def verify_case(root, name, manifest):
    import _b3_e4_f03_primal_archive as archive
    import _b3_e4_f03_primal_checks as checks
    directory = root/name
    receipt = read(directory/'supervision.json')
    digest = supervisor._registration_hash(root)
    expected_receipt = {'reason', 'exit_code', 'elapsed_seconds', 'sampled_peak_rss_bytes',
                        'phases', 'registration_sha256', 'failure', 'observables_sha256'}
    if set(receipt) != expected_receipt:
        raise ValueError('reference receipt schema mismatch')
    if receipt['registration_sha256'] != digest:
        raise ValueError('reference receipt registration mismatch')
    if receipt['reason'] == 'completed' and (receipt['failure'] is not None or
                                            type(receipt['exit_code']) is not int or receipt['exit_code'] != 0):
        raise ValueError('contradictory completed reference receipt')
    if receipt['reason'] != 'completed' or receipt['exit_code'] != 0:
        return {'status': 'FAILED_EXECUTION', 'receipt': receipt}, None
    event = observable_event(directory, name, CASES[name], False)
    started = read(directory/'child_started.json')
    if (set(started) != {'case', 'registration_sha256', 'pid', 'started_unix_seconds'}
            or started['case'] != name or started['registration_sha256'] != digest
            or type(started['pid']) is not int or started['pid'] <= 0
            or type(started['started_unix_seconds']) not in (int, float)
            or not math.isfinite(started['started_unix_seconds'])):
        raise ValueError('reference child authority mismatch')
    events = [json.loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines()]
    if (receipt['phases'] != ['identity', 'observables']
            or receipt['observables_sha256'] != event['sha256']
            or not 0 <= receipt['elapsed_seconds'] <= MAX_SECONDS
            or not 0 <= receipt['sampled_peak_rss_bytes'] <= MAX_RSS_BYTES
            or len(events) != 2 or not all(isinstance(e, dict) for e in events)
            or events[0].get('identity') != manifest['identity']
            or events[0].get('phase') != 'identity' or events[0].get('case') != name
            or events[0].get('registration_sha256') != digest
            or not events[0].get('threadpools')
            or any(p.get('num_threads') != 1 for p in events[0]['threadpools'])
            or events[1] != event):
        raise ValueError('reference identity, artifacts or resource receipt mismatch')
    arrays = archive.unpack(directory/'arrays.npz', CASES[name]['degree'])
    metrics = checks.verify_saved(arrays, CASES[name]['degree'])
    data = read(directory/'observables.json')
    if (set(data) != {'metrics', 'equilibrium_solves', 'assembly_descriptions', 'scope'}
            or data['equilibrium_solves'] != 1 or data['assembly_descriptions'] != 2 or data['scope'] != SCOPE):
        raise ValueError('reference work or scope contract changed')
    bind_metrics(data['metrics'], metrics)
    values = metrics['checks']
    if (set(values) != set(checks.LIMITS) or
            any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values.values())):
        raise ValueError('invalid reference numerical check inventory')
    failed = {k: {'value': values[k], 'limit': limit}
              for k, limit in checks.LIMITS.items() if values[k] > limit}
    return {'status': 'FAILED_NUMERICAL_SCREEN' if failed else 'PASSED_NUMERICAL_SCREEN',
            'failed_checks': failed, 'metrics': metrics}, arrays


def adjudicate(root):
    from _b3_e4_f03_primal_trends import assess_sequence
    manifest = registered(root)
    if any(not (root/name/'supervision.json').is_file() for name in CASES):
        raise ValueError('complete five-case receipt inventory required before adjudication')
    decisions, saved = {}, {}
    for name in CASES:
        try:
            decisions[name], arrays = verify_case(root, name, manifest)
            if arrays is not None:
                saved[CASES[name]['degree']] = arrays
        except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, EOFError, zipfile.BadZipFile) as exc:
            decisions[name] = {'status': 'FAILED_EVIDENCE', 'reason': f'{type(exc).__name__}: {exc}'}
    status = next((candidate for candidate in ('FAILED_EVIDENCE', 'FAILED_EXECUTION', 'FAILED_NUMERICAL_SCREEN')
        if any(row['status'] == candidate for row in decisions.values())), None)
    trends = None
    if status is None:
        trends = assess_sequence(saved, {CASES[name]['degree']: row['metrics'] for name, row in decisions.items()})
        status = trends['status']
    supervisor._json_new(root/'adjudication.json', {'registration_sha256': supervisor._registration_hash(root),
        'identity': manifest['identity'], 'status': status, 'cases': decisions, 'trends': trends, 'scope': SCOPE})
    print(json.dumps({'status': status, 'cases': {name: row['status'] for name, row in decisions.items()}}, sort_keys=True))
    return status == 'PASSED_BOUNDED_PRIMAL_REFERENCE'


def configure():
    supervisor.ROOT = ROOT
    supervisor.CASES = CASES
    supervisor.RUNNER = Path(__file__).resolve()
    supervisor.SOURCES = tuple(ROOT/'scripts'/name for name in SOURCES)+(
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_PRIMAL_RITZ_PROTOCOL.md',
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_CONTINUOUS_PRIMAL_REFERENCE.md')
    supervisor.CAPTURE_STATE = False
    supervisor.MAX_SECONDS = MAX_SECONDS
    supervisor.MAX_RSS_BYTES = MAX_RSS_BYTES
    supervisor._registered = registered
    supervisor._observable_event = observable_event


def run_once(root):
    register(root)
    start = time.monotonic()
    completed = []
    try:
        for name in CASES:
            if time.monotonic()-start > LAUNCH_CUTOFF_SECONDS:
                raise TimeoutError('reference launch cutoff; remaining evidence incomplete')
            ok = supervisor.execute(root, name)
            completed.append({'case': name, 'execution_completed': ok})
            if not ok:
                receipt = read(root/name/'supervision.json')
                if receipt.get('reason') == 'supervisor_failure' and (receipt.get('failure') or '').startswith(
                        ('KeyboardInterrupt:', 'SystemExit:', 'GeneratorExit:')):
                    raise KeyboardInterrupt('preserved supervised cancellation')
        return adjudicate(root)
    finally:
        supervisor._json_new(root/'orchestration.json', {'registration_sha256': supervisor._registration_hash(root),
            'cases': completed, 'inventory_complete': len(completed) == len(CASES),
            'elapsed_seconds': time.monotonic()-start,
            'supervisor_thread_caps': {k: os.environ.get(k) for k in supervisor.THREADS}})


def main():
    if any(os.environ.get(k) != '1' for k in supervisor.THREADS):
        raise ValueError('all supervisor and child thread caps must equal one')
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ('run-all', 'register', 'execute', 'adjudicate', 'child'):
        group.add_argument('--'+flag, action='store_true')
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--case', choices=CASES)
    args = parser.parse_args()
    if (args.execute or args.child) != bool(args.case):
        parser.error('--case required only for execute or child')
    configure()
    root = args.root.resolve()
    if args.run_all:
        return 0 if run_once(root) else 1
    if args.register:
        register(root)
        return 0
    if args.execute:
        return 0 if supervisor.execute(root, args.case) else 1
    if args.adjudicate:
        return 0 if adjudicate(root) else 1
    child(root, args.case)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
