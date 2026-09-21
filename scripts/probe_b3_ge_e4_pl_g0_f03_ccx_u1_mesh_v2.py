"""Exploratory U1 cantilever refinement, not mixed F03 qualification.

Each mesh has its own exclusive output directory. A successful process exit
is reported separately from comparison with the analytical tip response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_b3_ge_e4_pl_g0_f03_ccx_u1_smoke import EXPECTED_EXE_SHA256


YOUNG = 210e9
POISSON = .3
AREA = .01
INERTIA = 8.333333333333333e-6
SHEAR_FACTOR = .8
FORCE = 1000.
ANALYTIC_TIP = FORCE/(3*YOUNG*INERTIA) + FORCE/(SHEAR_FACTOR*YOUNG/(2*(1+POISSON))*AREA)
ANALYTIC_ROTATION = FORCE/(2*YOUNG*INERTIA)


def deck(count):
    nodes = '\n'.join(f'{i+1},{i/count:.17g},0.,0.' for i in range(count+1))
    elements = '\n'.join(f'{i+1},{i+1},{i+2}' for i in range(count))
    return f"""** Exploratory U1 cantilever refinement, not a coupled F03 reference
*NODE,NSET=Nall
{nodes}
*ELEMENT,TYPE=U1,ELSET=Eall
{elements}
*USER ELEMENT,TYPE=U1,NODES=2,INTEGRATION POINTS=2,MAXDOF=6
*BOUNDARY
1,1,6
*MATERIAL,NAME=EL
*ELASTIC
{YOUNG:.17g},{POISSON:.17g}
*BEAM SECTION,ELSET=Eall,MATERIAL=EL,SECTION=GENERAL
{AREA:.17g},{INERTIA:.17g},0.,{INERTIA:.17g},{SHEAR_FACTOR:.17g}
0.,1.,0.
*STEP
*STATIC
*CLOAD
{count+1},2,{FORCE:.17g}
*NODE PRINT,NSET=Nall
U
*END STEP
"""


def tip_from_dat(path, terminal):
    content = path.read_text(encoding='utf-8', errors='replace')
    section = content.split('displacements (v(i),i=1..ndof)', 1)[1]
    pattern = re.compile(r'^\s*'+str(terminal)+r'\s+([+-]?\d\.\d+E[+-]\d+\s+){5}'
                         r'([+-]?\d\.\d+E[+-]\d+)\s*$', re.MULTILINE)
    match = pattern.search(section)
    if match is None:
        raise ValueError('terminal six-component displacement row absent')
    components = [float(value) for value in match.group(0).split()[1:]]
    return components[1], components[5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    identity = hashlib.sha256(executable.read_bytes()).hexdigest()
    if identity != EXPECTED_EXE_SHA256:
        raise ValueError('CalculiX executable identity mismatch')
    args.root.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment['OMP_NUM_THREADS'] = '1'
    records = []
    for count in (1,2,4,8,16):
        case = args.root/f'u1-{count:02d}'
        case.mkdir(exist_ok=False)
        (case/'cantilever.inp').write_text(deck(count), encoding='ascii')
        try:
            process = subprocess.run([str(executable), '-i', 'cantilever'],
                                     cwd=case, env=environment, capture_output=True,
                                     text=True, timeout=120, check=False)
            (case/'stdout.log').write_text(process.stdout, encoding='utf-8')
            (case/'stderr.log').write_text(process.stderr, encoding='utf-8')
            exit_code = process.returncode
            failure = None
        except subprocess.TimeoutExpired as exc:
            (case/'stdout.log').write_bytes(exc.stdout or b'')
            (case/'stderr.log').write_bytes(exc.stderr or b'')
            exit_code = None
            failure = 'TIMEOUT_120_SECONDS'
        tip_y, tip_rz = (None, None)
        if exit_code == 0:
            try:
                tip_y, tip_rz = tip_from_dat(case/'cantilever.dat', count+1)
            except (ValueError, OSError, IndexError) as exc:
                failure = f'{type(exc).__name__}: {exc}'
        row = dict(elements=count, exit_code=exit_code, failure=failure,
                   tip_y_m=tip_y, tip_rz_rad=tip_rz,
                   analytic_tip_y_m=ANALYTIC_TIP, analytic_tip_rz_rad=ANALYTIC_ROTATION,
                   tip_y_relative_error=None if tip_y is None else abs(tip_y/ANALYTIC_TIP-1),
                   tip_rz_relative_error=None if tip_rz is None else abs(tip_rz/ANALYTIC_ROTATION-1),
                   files=sorted(path.name for path in case.iterdir()))
        records.append(row)
        (case/'result.json').write_text(json.dumps(row, indent=2, sort_keys=True)+'\n',
                                        encoding='utf-8')
        print(json.dumps(row, sort_keys=True), flush=True)
    summary = dict(purpose='UNREGISTERED_U1_REFINEMENT_NOT_F03_ACCEPTANCE',
                   executable=str(executable), executable_sha256=identity,
                   results=records)
    (args.root/'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n',
                                          encoding='utf-8')
    return 0 if all(row['exit_code'] == 0 and row['failure'] is None for row in records) else 1


if __name__ == '__main__':
    raise SystemExit(main())
