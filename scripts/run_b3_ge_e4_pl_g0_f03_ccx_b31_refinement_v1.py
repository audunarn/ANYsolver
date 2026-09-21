"""Frozen exploratory B31/CPS refinement inventory, not F03 acceptance.

This external comparator has its own section and discrete collocation law.
Keep solver output for every attempted case, including failed executions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_b3_ge_e4_pl_g0_f03_ccx_b31_mixed import b31_deck
from probe_b3_ge_e4_pl_g0_f03_ccx_coupled_v1 import _trace
from probe_b3_ge_e4_pl_g0_f03_ccx_u1_smoke import EXPECTED_EXE_SHA256


CASES = tuple((topology, n, 2*n, load)
              for topology in ('Q4', 'S3-V2D')
              for load in ('smooth', 'sine')
              for n in (2, 4, 8))
DISPLACEMENT = re.compile(
    r'^\s*(\d+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s*$',
    re.MULTILINE)


def parse_displacements(data: str, model: dict):
    heading = 'displacements (vx,vy,vz) for set NALL'
    if data.count(heading) != 1:
        raise ValueError(f'expected exactly one displacement block, found {data.count(heading)}')
    remaining = data.split(heading, 1)[1]
    lines = remaining.splitlines()
    rows = {}
    started = False
    for line in lines:
        match = DISPLACEMENT.fullmatch(line)
        if match:
            node, x, y, z = match.groups()
            node = int(node)
            if node in rows:
                raise ValueError(f'duplicate original-node displacement {node}')
            rows[node] = (float(x), float(y), float(z))
            started = True
        elif started:
            break
    expected = model['shell_nodes'] + model['beam_nodes']
    if len(rows) != expected or set(rows) != set(range(1, expected+1)):
        raise ValueError(f'expected {expected} original-node displacements; got {len(rows)}')
    n_shell, n_beam = model['n_shell'], model['n_beam']
    first_beam = model['beam_node_ids'][0]
    gaps = []
    for i in range(1, n_beam+1):
        s = i/n_beam
        trace = _trace(s, n_shell, model['topology'])
        gaps.append([rows[first_beam+i][axis] -
                     sum(coefficient*rows[node][dof-1]
                         for (node,dof),coefficient in trace[axis].items())
                     for axis in (0, 1)])
    return {'tip_y_m': rows[first_beam+n_beam][1],
            'max_station_translation_gap_m': max(abs(g) for row in gaps for g in row),
            'station_translation_gaps_m': gaps,
            'shell_mid_y_m': rows[(n_shell+1)+(2*n_shell+1)][1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    exe = args.executable.resolve(strict=True)
    exe_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
    if exe_hash != EXPECTED_EXE_SHA256:
        raise ValueError('CalculiX executable identity mismatch')
    args.root.mkdir(parents=True, exist_ok=False)
    source_hashes = {
        'runner': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'deck_generator': hashlib.sha256(
            (Path(__file__).parent / 'probe_b3_ge_e4_pl_g0_f03_ccx_b31_mixed.py').read_bytes()
        ).hexdigest(),
        'trace_generator': hashlib.sha256(
            (Path(__file__).parent / 'probe_b3_ge_e4_pl_g0_f03_ccx_coupled_v1.py').read_bytes()
        ).hexdigest(),
    }
    manifest = {'purpose': 'EXPLORATORY_EXTERNAL_REFINEMENT_NOT_F03_ACCEPTANCE',
                'cases': CASES, 'source_sha256': source_hashes,
                'executable_sha256': exe_hash, 'openmp_threads': 1,
                'timeout_seconds_per_case': 120}
    (args.root / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n',
                                             encoding='utf-8')
    environment = os.environ.copy()
    environment['OMP_NUM_THREADS'] = '1'
    results = []
    for topology, n_shell, n_beam, load in CASES:
        name = f'{topology.lower()}-ns{n_shell}-nb{n_beam}-{load}'
        case = args.root / name
        case.mkdir(exist_ok=False)
        content, model = b31_deck(topology, n_shell, n_beam, load)
        content = content.replace('*NODE PRINT,NSET=Nall\nU\n',
                                  '*NODE PRINT,NSET=Nall\nU,RF\n')
        if '*NODE PRINT,NSET=Nall\nU,RF\n' not in content:
            raise AssertionError('nodal print card missing')
        (case / 'b31mixed.inp').write_text(content, encoding='ascii')
        record = dict(case=name, model=model,
                      deck_sha256=hashlib.sha256(content.encode('ascii')).hexdigest(),
                      executable_sha256=exe_hash)
        try:
            run = subprocess.run([str(exe), '-i', 'b31mixed'], cwd=case,
                                 env=environment, capture_output=True, text=True,
                                 timeout=120, check=False)
            (case / 'stdout.log').write_text(run.stdout, encoding='utf-8')
            (case / 'stderr.log').write_text(run.stderr, encoding='utf-8')
            record.update(exit_code=run.returncode, failure=None)
            if run.returncode == 0:
                record['observables'] = parse_displacements(
                    (case / 'b31mixed.dat').read_text(encoding='ascii'), model)
        except subprocess.TimeoutExpired as exc:
            (case / 'stdout.log').write_bytes(exc.stdout or b'')
            (case / 'stderr.log').write_bytes(exc.stderr or b'')
            record.update(exit_code=None, failure='TIMEOUT_120_SECONDS')
        except (ValueError, OSError) as exc:
            record.update(failure=f'OUTPUT_PARSE_ERROR: {exc}')
        record['files'] = sorted(p.name for p in case.iterdir())
        (case / 'result.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n',
                                          encoding='utf-8')
        results.append(record)
        print(json.dumps({'case': name, 'exit_code': record.get('exit_code'),
                          'failure': record.get('failure'),
                          'observables': record.get('observables')}, sort_keys=True),
              flush=True)
    (args.root / 'inventory.json').write_text(json.dumps(results, indent=2, sort_keys=True)+'\n',
                                               encoding='utf-8')
    return 0 if all(r.get('exit_code') == 0 and 'observables' in r for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
