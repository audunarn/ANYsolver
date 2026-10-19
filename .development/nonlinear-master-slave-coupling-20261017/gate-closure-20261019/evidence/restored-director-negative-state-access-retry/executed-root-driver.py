"""Verify two new refusal/rollback cases without repeating failed continuation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

PHASE = Path(__file__).resolve().parents[1]
REPO = PHASE.parents[2]
PYTHON = REPO / '.venv/Scripts/python.exe'
MODULE = 'tests/test_nonlinear_beam_shell_slice3_director_continuation.py'
COMMON = 'tests/test_nonlinear_beam_shell_slice3_continuation.py'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    baseline = PHASE / 'revised-endpoint-final-collection-selection.json'
    previous = json.loads(baseline.read_text())
    targets = [MODULE + '::' + name for name in (
        'test_director_incompatible_restart_refused_without_input_mutation',
        'test_director_stopped_negative_run_excludes_rejected_history',
    )]
    selection = PHASE / f'{args.name}-selection.json'
    with selection.open('x', encoding='utf-8') as stream:
        json.dump(dict(
            historical_selection=str(baseline),
            all_required_targets=previous['all_required_targets'] + [MODULE],
            targets=targets,
            selected_file_sha256={MODULE: hashlib.sha256((REPO / MODULE).read_bytes()).hexdigest()},
            dependency_file_sha256={COMMON: hashlib.sha256((REPO / COMMON).read_bytes()).hexdigest()},
            development_only=True,
            purpose='New negative refusal/rollback coverage only; full director target remains failed and restart/cancellation qualification is not inferred.'
        ), stream, indent=2)
    command = [str(PYTHON), str(PHASE / 'harness.py'), '--name', args.name,
               '--timeout', '120']
    for path in (Path(__file__), selection, baseline, REPO / MODULE,
                 REPO / COMMON,
                 PHASE / 'director-option-scientific-candidate-authority.json',
                 PHASE / 'rejected-increment-seed-authority.json',
                 REPO / 'scripts/run_portable_ci.py',
                 REPO / 'scripts/development_test_runtime.py'):
        command += ['--hash-input', str(path)]
    command += ['--', str(PYTHON), 'scripts/run_portable_ci.py', '--development',
                *targets, '--workers', '1', '--jit', 'off',
                '--timeout-seconds', '110', '--memory-limit-mib', '2048']
    environment = dict(os.environ)
    environment['RUNNER_TEMP'] = str(PHASE / 'portable-runs')
    raise SystemExit(subprocess.run(command, cwd=REPO, env=environment,
                                   check=False).returncode)


if __name__ == '__main__':
    main()
