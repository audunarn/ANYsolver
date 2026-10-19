"""Select registered independent assessments; each solve uses the task harness.

No automatic refinements, retries or simultaneous children. An incomplete solve
stops the selected batch for inspection. Coarse analytical accuracy is reported
and assessed only against the registered final-refinement criteria.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[1]
PYTHON = REPO / '.venv/Scripts/python.exe'
DIAGNOSTICS = TASK / 'diagnostics'


def registered():
    rows = {}
    for name in ['R1', 'R2', 'R3', 'R4', 'M1', 'M2', 'M3', 'M4',
                 'P1', 'P2', 'P3', 'P4']:
        rows['mesh-'+name] = ['mesh_study.py', name]
    for nx in (8, 16, 32, 64, 128, 256):
        for coupling in ('matching', 'nonmatching'):
            for e in (0, .002):
                for angle in (30, 60):
                    name = f'arc-{coupling}-e{e:g}-a{angle}-n{nx}'
                    rows[name] = ['arc_reference.py', '--nx', str(nx),
                                  '--coupling', coupling, '--eccentricity', str(e),
                                  '--angle', str(angle)]
    return rows


def product_identity():
    return {name: hashlib.sha256((REPO/'src/anysolver'/name).read_bytes()).hexdigest()
            for name in ('corotational.py', 'elements.py', 'mesh_gen.py',
                         'nonlinear_static.py', 'nonlinear_performance.py', '_corotational_batch.py')}


def validate_extension(name, prefix, identity):
    if not name.startswith('arc-'):
        return
    group, level_text = name.rsplit('-n', 1)
    level = int(level_text)
    levels = (8, 16, 32, 64, 128, 256)
    index = levels.index(level)
    if index < 3:
        return
    prior = []
    for n in levels[:index]:
        path = TASK/'evidence'/f'{prefix}-{group}-n{n}'/'result.json'
        if not path.is_file():
            raise SystemExit(f'Extension requires prior retained level {path}.')
        row = json.loads(path.read_text())
        for filename, digest in identity.items():
            if row['identity']['sha256'].get('src/anysolver/'+filename) != digest:
                raise SystemExit('Extension requires prior levels on this product identity.')
        if not row['complete_and_equilibrated']:
            raise SystemExit('Incomplete prior level: extension is not authorized.')
        prior.append(row)
    old, prev = prior[-2:]
    error = lambda row: max(v for r in row['errors'].values() for k, v in r.items()
                            if k in ('u_relative', 'ry_relative'))
    if error(prev) >= error(old):
        raise SystemExit('Analytical error is not decreasing: extension is not authorized.')
    changes = []
    for tip in ('shell', 'beam'):
        a, b = old['measured'][tip], prev['measured'][tip]
        changes += [math.dist(a['u_m'], b['u_m']) / math.hypot(*b['u_m']),
                    abs(a['ry_rad']-b['ry_rad'])/abs(b['ry_rad'])]
    if max(changes) <= .0025:
        raise SystemExit('Refinement criterion already met: extension is not authorized.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--select', nargs='+', required=True)
    ap.add_argument('--prefix', default='assessment')
    ap.add_argument('--final-verification', action='store_true',
                    help='Use the original reserve only for a frozen final candidate.')
    ap.add_argument('--hold-seconds', type=float, default=900.0,
                    help='Keep this much of the original allowance for remaining integrated checks.')
    ap.add_argument('--diagnostic-bound-record', type=Path,
                    help='Prospective named analytical timeout exceptions, validated by the harness.')
    args = ap.parse_args()
    cases = registered()
    if len(set(args.select)) != len(args.select) or any(n not in cases for n in args.select):
        ap.error('select unique registered case IDs')
    if (TASK/'running.lock').exists():
        raise SystemExit('Numerical child already owned by another run; no launch.')
    original = product_identity()
    bounds = (json.loads(args.diagnostic_bound_record.read_text())
              if args.diagnostic_bound_record else None)
    for name in args.select:
        if product_identity() != original:
            raise SystemExit('Product identity changed during assessment batch.')
        validate_extension(name, args.prefix, original)
        attempt = f'{args.prefix}-{name}'
        out = TASK/'evidence'/attempt/'result.json'
        entry = cases[name]
        ledger = json.loads((TASK/'budget.json').read_text())
        remaining = float(ledger['allowance_seconds']) - float(ledger['used_seconds'])
        if args.hold_seconds < 0 or (not args.final_verification and args.hold_seconds < 900):
            raise SystemExit('Cannot consume the final reserve outside final verification.')
        named_bound = (bounds.get('attempts', {}).get(attempt)
                       if bounds and name.startswith('arc-') else None)
        timeout = min(float(named_bound or 120.0), remaining - args.hold_seconds - 1.0)
        if timeout < 10.0:
            raise SystemExit('Remaining original budget held for integrated checks; no new case launched.')
        command = [str(PYTHON), str(TASK/'harness.py'), '--name', attempt,
                   '--timeout', str(timeout)]
        if named_bound is not None:
            command += ['--diagnostic-bound-record', str(args.diagnostic_bound_record)]
        if args.final_verification:
            command += ['--allow-reserve']
        for path in [Path(__file__), *sorted(DIAGNOSTICS.glob('*.py')),
                     TASK/'analytical_derivation.md']:
            command += ['--hash-input', str(path)]
        command += ['--', str(PYTHON), str(DIAGNOSTICS/entry[0]),
                    *entry[1:], '--output', str(out)]
        print(f'Launching {attempt}', flush=True)
        child = subprocess.run(command, cwd=REPO, check=False)
        if child.returncode or not out.exists():
            raise SystemExit(f'Assessment {attempt} failed; inspect retained evidence.')
        if product_identity() != original:
            raise SystemExit(f'Assessment {attempt} input changed; not acceptance evidence.')
        row = json.loads(out.read_text(encoding='utf-8'))
        complete = row['passed'] if row['kind'] == 'mesh' else row['complete_and_equilibrated']
        print(json.dumps({'attempt': attempt, 'status': row['status'],
                          'load_factor': row['load_factor'],
                          'complete_and_equilibrated': complete,
                          'relative_residual': row['equilibrium']['relative_residual']}), flush=True)
        if not complete:
            raise SystemExit(f'Assessment {attempt} incomplete; inspect before further solves.')


if __name__ == '__main__':
    main()
