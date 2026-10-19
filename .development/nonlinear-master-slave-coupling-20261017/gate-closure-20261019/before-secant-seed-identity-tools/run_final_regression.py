"""Exact historical standard selection plus Slice 1/2 and Slice 3 modules."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
PYTHON = REPO/'.venv/Scripts/python.exe'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--collect-only', action='store_true')
    ap.add_argument('--selection', choices=(
        'all', 'standard', 'standard-and-core', 'slice', 'slice-core', 'slice-core-fast',
        'coupling-fast', 'coupling-force', 'coupling-dc-direct',
        'coupling-dc-interpolated', 'coupling-restart-direct',
        'coupling-restart-interpolated', 'continuation-smoke',
        'continuation-full', 'continuation-restart', 'continuation-cancel',
        'continuation-smoke-full', 'continuation-restart-cancel'), default='all')
    args = ap.parse_args()
    historical = REPO/'.development/standard-edge-integration-20261016/integration-checks-20261016/selection.json'
    targets = json.loads(historical.read_text())['targets']
    if len(targets) != 22:
        raise SystemExit('Historical 22-module selection changed; inspect before running.')
    targets += ['tests/test_instance_dict_descriptor_layout.py',
                'tests/test_general_contact_native_deadline_scale.py',
                'tests/test_general_contact_native_replay_diagnostics.py',
                'tests/test_corotational_work_conjugate.py',
                'tests/test_nonlinear_beam_shell_coupling.py',
                'tests/test_nonlinear_beam_shell_slice3.py',
                'tests/test_nonlinear_beam_shell_slice3_continuation.py',
                'tests/test_nonlinear_beam_shell_slice3_batch.py',
                'tests/test_nonlinear_beam_shell_slice3_precision.py',
                'tests/test_beam_shell_connection_options.py',
                'tests/test_director_integrated_trace.py']
    if len(set(targets)) != 33 or any(not (REPO/t).is_file() for t in targets):
        raise SystemExit('Final selection must contain all 33 distinct modules.')
    all_targets = list(targets)
    if args.selection == 'standard':
        targets = targets[:25]
    elif args.selection == 'standard-and-core':
        targets = [t for t in targets if not t.endswith('_continuation.py')]
    elif args.selection == 'slice':
        targets = targets[25:]
    elif args.selection == 'slice-core':
        targets = [t for t in targets[25:] if not t.endswith('_continuation.py')]
    elif args.selection == 'slice-core-fast':
        targets = [t for t in targets[25:]
                   if not t.endswith('_continuation.py')
                   and not t.endswith('test_nonlinear_beam_shell_coupling.py')]
    elif args.selection.startswith('coupling-'):
        module = 'tests/test_nonlinear_beam_shell_coupling.py'
        cantilever = 'test_cantilever_stiffened_shell_finite_rotation_solve_and_wrench_balance'
        restart = 'test_coupled_corotational_split_restart_matches_uninterrupted'
        if args.selection == 'coupling-fast':
            names = [node.name for node in ast.parse((REPO/module).read_text()).body
                     if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
                     and node.name not in (cantilever, restart)]
        else:
            names = {
                'coupling-force': [cantilever+'[force-eccentric]', cantilever+'[force-interpolated]'],
                'coupling-dc-direct': [cantilever+'[displacement-eccentric]'],
                'coupling-dc-interpolated': [cantilever+'[displacement-interpolated]'],
                'coupling-restart-direct': [restart+'[eccentric]'],
                'coupling-restart-interpolated': [restart+'[interpolated]'],
            }[args.selection]
        targets = [module+'::'+name for name in names]
    elif args.selection.startswith('continuation-'):
        names = {
            'continuation-smoke': [
                'test_preyield_plastic_matches_elastic_control_exactly',
                'test_preyield_plastic_matches_distinct_linear_elastic_material',
                'test_dc_half_reaches_minus_0_10_with_plasticity',
                'test_dc_rejected_restart_input_refused_and_preserved',
                'test_dc_stopped_resume_snapshots_exclude_rejected_history'],
            'continuation-full': ['test_dc_full_target_plasticity_and_equilibrium'],
            'continuation-restart': ['test_dc_resume_reproduces_uninterrupted_run'],
            'continuation-cancel': [
                'test_dc_cancelled_resume_preserves_inputs_and_same_inputs_still_deliver'],
        }
        names['continuation-smoke-full'] = (
            names['continuation-smoke'] + names['continuation-full'])
        names['continuation-restart-cancel'] = (
            names['continuation-restart'] + names['continuation-cancel'])
        targets = ['tests/test_nonlinear_beam_shell_slice3_continuation.py::'+name
                   for name in names[args.selection]]
    selection = TASK/f'{args.name}-selection.json'
    if selection.exists():
        raise SystemExit('Selection evidence path already exists.')
    selection.write_text(json.dumps({
        'historical_selection': str(historical), 'selection': args.selection,
        'all_required_targets': all_targets, 'targets': targets,
        'selected_file_sha256': {t.partition('::')[0]: hashlib.sha256(
                                    (REPO/t.partition('::')[0]).read_bytes()).hexdigest()
                                 for t in targets},
        'development_only': True,
    }, indent=2)+'\n')
    if args.collect_only:
        command = [str(PYTHON), '-m', 'pytest', '--collect-only', '-q',
                   '-p', 'no:cacheprovider', *targets]
        timeout = '120'
    else:
        command = [str(PYTHON), 'scripts/run_portable_ci.py', '--development',
                   *targets, '--workers', '1', '--jit', 'off',
                   '--timeout-seconds', '600', '--memory-limit-mib', '2048']
        timeout = '600'
    outer = [str(PYTHON), str(TASK/'harness.py'), '--name', args.name,
             '--timeout', timeout, '--allow-reserve']
    for path in [Path(__file__), selection, historical, TASK/'authority.json',
                 TASK/'continuation-repair-authority.json',
                 REPO/'scripts/run_portable_ci.py',
                 REPO/'scripts/development_test_runtime.py',
                 *[REPO/t.partition('::')[0] for t in targets]]:
        outer += ['--hash-input', str(path)]
    environment = dict(os.environ)
    environment['RUNNER_TEMP'] = str(TASK/'portable-runs')
    raise SystemExit(subprocess.run(outer+['--']+command, cwd=REPO,
                                   env=environment, check=False).returncode)


if __name__ == '__main__':
    main()
