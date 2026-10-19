"""Collect the frozen historical selection plus the separate director tests."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--additional-module', action='append', default=[])
    parser.add_argument('--require-historical-tests-unchanged', action='store_true')
    args = parser.parse_args()
    baseline = PHASE / 'revised-endpoint-final-collection-selection.json'
    previous = json.loads(baseline.read_text())
    targets = previous['all_required_targets'] + [
        'tests/test_nonlinear_beam_shell_slice3_director_continuation.py',
        *args.additional_module,
    ]
    if len(targets) != len(set(targets)):
        raise SystemExit('Duplicate collection modules')
    hashes = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
              for p in targets}
    changed = [p for p, h in previous['selected_file_sha256'].items()
               if hashes[p] != h]
    if changed and args.require_historical_tests_unchanged:
        raise SystemExit('Historical selected tests changed; reassess before reuse')
    selection = PHASE / f'{args.name}-selection.json'
    with selection.open('x', encoding='utf-8') as stream:
        json.dump(dict(historical_selection=str(baseline),
                       all_required_targets=targets, targets=targets,
                       selected_file_sha256=hashes,
                       historical_test_inputs_changed=changed,
                       historical_pass_reuse_automatically_authorized=False,
                       development_only=True),
                  stream, indent=2)
    command = [str(PYTHON), str(PHASE / 'harness.py'), '--name', args.name,
               '--timeout', '120']
    for path in [Path(__file__), baseline, selection,
                 PHASE / 'director-option-scientific-candidate-authority.json',
                 *[REPO / p for p in targets]]:
        command += ['--hash-input', str(path)]
    command += ['--', str(PYTHON), '-m', 'pytest', '--collect-only', '-q',
                '-p', 'no:cacheprovider', *targets]
    environment = dict(os.environ)
    environment['RUNNER_TEMP'] = str(PHASE / 'portable-runs')
    raise SystemExit(subprocess.run(command, cwd=REPO, env=environment,
                                   check=False).returncode)


if __name__ == '__main__':
    main()
