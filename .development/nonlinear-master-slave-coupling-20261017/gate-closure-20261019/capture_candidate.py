"""Write a unique, reproducible working-tree identity without Git mutations."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PHASE = Path(__file__).resolve().parent
TASK = PHASE.parent
REPO = TASK.parents[1]
PRODUCT = ['src/anysolver/'+name for name in
           ('corotational.py', 'elements.py', 'mesh_gen.py',
            'nonlinear_static.py', 'nonlinear_performance.py', '_corotational_batch.py', '_director_trace.py', '_nonlinear_events.py', '_nonlinear_seed.py')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def original_test_preservation():
    report = {}
    for name in ('test_corotational_work_conjugate.py', 'test_nonlinear_beam_shell_coupling.py'):
        def tests(path):
            return {node.name: ast.dump(node, include_attributes=False)
                    for node in ast.parse(path.read_text(encoding='utf-8')).body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name.startswith('test_')}
        original, current = tests(TASK/'patch'/name), tests(REPO/'tests'/name)
        report[name] = {test: current.get(test) == body for test, body in original.items()}
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('--additional-test', action='append', default=[])
    args = ap.parse_args()
    if Path(args.name).name != args.name:
        ap.error('name must be a single path component')
    folder = PHASE/'candidate-identities'/args.name
    folder.mkdir(parents=True, exist_ok=False)
    original = json.loads((TASK/'supervisor_initial_identity.json').read_text())
    historical = json.loads((REPO/'.development/standard-edge-integration-20261016/integration-checks-20261016/selection.json').read_text())['targets']
    tests = historical + [
        'tests/test_instance_dict_descriptor_layout.py',
        'tests/test_general_contact_native_deadline_scale.py',
        'tests/test_general_contact_native_replay_diagnostics.py',
        'tests/test_corotational_work_conjugate.py',
        'tests/test_nonlinear_beam_shell_coupling.py',
        'tests/test_nonlinear_beam_shell_slice3.py',
        'tests/test_nonlinear_beam_shell_slice3_continuation.py',
        'tests/test_nonlinear_beam_shell_slice3_batch.py',
        'tests/test_nonlinear_beam_shell_slice3_precision.py',
        'tests/test_beam_shell_connection_options.py',
        'tests/test_director_integrated_trace.py',
    ]
    for relative in args.additional_test:
        candidate = (REPO / relative).resolve()
        if (not candidate.is_relative_to(REPO / 'tests')
                or not candidate.is_file() or candidate.suffix != '.py'):
            ap.error('Additional tests must be existing Python files inside repository tests/')
        tests.append(candidate.relative_to(REPO).as_posix())
    status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=REPO, text=True)
    (folder/'tracked-status.txt').write_text(status)
    dirty = [line[3:] for line in status.splitlines()]
    paths = set(REPO/'src/anysolver'/p.relative_to(REPO/'src/anysolver')
                for p in (REPO/'src/anysolver').rglob('*.py'))
    paths.update(REPO/p for p in tests+dirty)
    paths.update(TASK.glob('*.py'))
    paths.update(PHASE.glob('*.py'))
    paths.update((PHASE/'diagnostics').glob('*.py'))
    paths.add(REPO/'docs/BEAM_SHELL_CONNECTION.md')
    paths.update((TASK/'diagnostics').glob('*.py'))
    paths.update(REPO/p for p in ['scripts/run_portable_ci.py', 'scripts/development_test_runtime.py'])
    hashes = {p.relative_to(REPO).as_posix(): sha(p) for p in sorted(paths) if p.is_file()}
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    protected = {p.relative_to(REPO).as_posix(): sha(p)
                 for p in [TASK/'patch'/name for name in
                           ('slices_1_3_tracked_changes.patch',
                            'test_corotational_work_conjugate.py',
                            'test_nonlinear_beam_shell_coupling.py')] if p.is_file()}
    snapshot_inputs = PRODUCT + [
        'tests/test_corotational_work_conjugate.py',
        'tests/test_nonlinear_beam_shell_coupling.py',
        'tests/test_nonlinear_beam_shell_slice3.py',
        'tests/test_nonlinear_beam_shell_slice3_continuation.py',
        'tests/test_nonlinear_beam_shell_slice3_batch.py',
        'tests/test_nonlinear_beam_shell_slice3_precision.py',
        'tests/test_beam_shell_connection_options.py',
        'tests/test_director_integrated_trace.py',
        'dependency-licenses.json',
    ]
    snapshot_inputs.extend(p for p in tests if p not in snapshot_inputs)
    snapshot_hashes = {}
    for relative in snapshot_inputs:
        destination = folder/'snapshot'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO/relative, destination)
        snapshot_hashes[relative] = sha(destination)
        if snapshot_hashes[relative] != hashes[relative]:
            raise RuntimeError(f'Input changed while capturing {relative}; retain this incomplete attempt.')
    record = {
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
        'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip(),
        'candidate_identity_sha256': identity,
        'working_source_and_selected_inputs_sha256': hashes,
        'protected_original_backup_sha256': protected,
        'original_slice12_tests_unchanged': all(hashes.get(p) == original['hashes'][p]
            for p in ('tests/test_corotational_work_conjugate.py',
                      'tests/test_nonlinear_beam_shell_coupling.py')),
        'original_slice12_test_function_ast_preserved': original_test_preservation(),
        'development_acceptance_only': True,
        'owned_snapshot_sha256': snapshot_hashes,
        'product_patch_scope': 'Tracked product diff; untracked private helper is preserved in snapshot.',
    }
    (folder/'candidate.json').write_text(json.dumps(record, indent=2)+'\n')
    (folder/'product.patch').write_bytes(subprocess.check_output(
        ['git', 'diff', '--binary', '--', *PRODUCT], cwd=REPO))
    print(json.dumps({'candidate_identity': identity, 'path': str(folder),
                      'source_inputs_hashed': len(hashes),
                      'original_slice12_tests_unchanged': record['original_slice12_tests_unchanged']}))


if __name__ == '__main__':
    main()
