"""Disposable U1 generalized-section execution check, not an F03 reference.

Preserves a single cantilever deck, complete solver output and analytic target
in an exclusive directory. The output is exploratory and never substitutes
for a preregistered coupled external comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


EXPECTED_EXE_SHA256 = "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"
DECK = """** Exploratory generalized U1 cantilever: no mixed shell or line attachment
*NODE,NSET=Nall
1,0.,0.,0.
2,1.,0.,0.
*ELEMENT,TYPE=U1,ELSET=Eall
1,1,2
*USER ELEMENT,TYPE=U1,NODES=2,INTEGRATION POINTS=2,MAXDOF=6
*BOUNDARY
1,1,6
*MATERIAL,NAME=EL
*ELASTIC
210.e9,.3
*BEAM SECTION,ELSET=Eall,MATERIAL=EL,SECTION=GENERAL
.01,8.333333333333333e-6,0.,8.333333333333333e-6,.8
0.,1.,0.
*STEP
*STATIC
*CLOAD
2,2,1000.
*NODE PRINT,NSET=Nall
U
RF
*EL PRINT,ELSET=Eall
S
*END STEP
"""


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
    (args.root/'u1smoke.inp').write_text(DECK, encoding='ascii')
    environment = os.environ.copy()
    environment['OMP_NUM_THREADS'] = '1'
    try:
        run = subprocess.run([str(exe), '-i', 'u1smoke'], cwd=args.root,
                             env=environment, capture_output=True, text=True,
                             timeout=120, check=False)
        exit_code = run.returncode
        (args.root/'stdout.log').write_text(run.stdout, encoding='utf-8')
        (args.root/'stderr.log').write_text(run.stderr, encoding='utf-8')
        failure = None
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        (args.root/'stdout.log').write_bytes(exc.stdout or b'')
        (args.root/'stderr.log').write_bytes(exc.stderr or b'')
        failure = 'TIMEOUT_120_SECONDS'
    young, poisson, area, inertia, shear_factor, force, length = (
        210e9, .3, .01, 8.333333333333333e-6, .8, 1000., 1.)
    shear = young/(2*(1+poisson))
    record = dict(purpose='UNREGISTERED_U1_EXECUTION_SMOKE_NOT_F03_ACCEPTANCE',
                  executable=str(exe), executable_sha256=exe_hash,
                  command=[str(exe), '-i', 'u1smoke'],
                  exit_code=exit_code, failure=failure,
                  analytic_tip_y_m=(force*length**3/(3*young*inertia)
                                    +force*length/(shear_factor*shear*area)),
                  analytic_tip_rz_rad=force*length**2/(2*young*inertia),
                  files=sorted(path.name for path in args.root.iterdir()))
    (args.root/'result.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n',
                                         encoding='utf-8')
    print(json.dumps(record, sort_keys=True))
    return 0 if exit_code == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
