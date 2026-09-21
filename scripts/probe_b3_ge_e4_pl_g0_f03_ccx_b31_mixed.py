"""Bounded external CPS/B31 feasibility probe; not an F03 qualification.

The B31 rectangular-section beam has a different section/shear idealization
from the native B3-GE and U1 generalized section. The four-sample nodal ties
are collocation equations, not the required continuous exact-multiplier law.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from probe_b3_ge_e4_pl_g0_f03_ccx_coupled_v1 import deck
from probe_b3_ge_e4_pl_g0_f03_ccx_u1_smoke import EXPECTED_EXE_SHA256


def b31_deck(topology: str, n_shell: int, n_beam: int, load: str):
    content, model = deck(topology, n_shell, n_beam, load)
    old_element = '*ELEMENT,TYPE=U1,ELSET=Ebeam'
    old_user = '*USER ELEMENT,TYPE=U1,NODES=2,INTEGRATION POINTS=2,MAXDOF=6\n'
    old_section = ('*BEAM SECTION,ELSET=Ebeam,MATERIAL=Steel,SECTION=GENERAL\n'
                   '.01,8.333333333333333e-6,0.,8.333333333333333e-6,.8\n')
    for old in (old_element, old_user, old_section):
        if content.count(old) != 1:
            raise AssertionError(f'Expected exactly one source card: {old!r}')
    content = content.replace(old_element, '*ELEMENT,TYPE=B31,ELSET=Ebeam')
    content = content.replace(old_user, '')
    content = content.replace(old_section,
                              '*BEAM SECTION,ELSET=Ebeam,MATERIAL=Steel,SECTION=RECT\n'
                              '.1,.1\n')
    content = content.replace('** Experimental four-sample collocation:',
                              '** Distinct rectangular B31/CPS feasibility:')
    model.update(beam_type='B31', section='RECT_0.1m_by_0.1m',
                 section_direction_1=(0., 1., 0.),
                 independent_physical_idealization=True)
    if '*BEAM SECTION,ELSET=Ebeam,MATERIAL=Steel,SECTION=RECT\n.1,.1\n0.,1.,0.\n' not in content:
        raise AssertionError('Rectangular section orientation was not preserved')
    return content, model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--topology', choices=('Q4', 'S3-V2D'), default='Q4')
    parser.add_argument('--n-shell', type=int, default=2)
    parser.add_argument('--n-beam', type=int, default=4)
    parser.add_argument('--load', choices=('smooth', 'sine'), default='smooth')
    args = parser.parse_args()
    if not 1 <= args.n_shell <= 64 or not 2 <= args.n_beam <= 64:
        raise ValueError('bounded exploratory mesh inventory required')
    exe = args.executable.resolve(strict=True)
    exe_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
    if exe_hash != EXPECTED_EXE_SHA256:
        raise ValueError('CalculiX executable identity mismatch')
    content, model = b31_deck(args.topology, args.n_shell, args.n_beam, args.load)
    args.root.mkdir(parents=True, exist_ok=False)
    (args.root / 'b31mixed.inp').write_text(content, encoding='ascii')
    environment = os.environ.copy()
    environment['OMP_NUM_THREADS'] = '1'
    try:
        run = subprocess.run([str(exe), '-i', 'b31mixed'], cwd=args.root,
                             env=environment, capture_output=True, text=True,
                             timeout=120, check=False)
        (args.root / 'stdout.log').write_text(run.stdout, encoding='utf-8')
        (args.root / 'stderr.log').write_text(run.stderr, encoding='utf-8')
        status = {'exit_code': run.returncode, 'failure': None}
    except subprocess.TimeoutExpired as exc:
        (args.root / 'stdout.log').write_bytes(exc.stdout or b'')
        (args.root / 'stderr.log').write_bytes(exc.stderr or b'')
        status = {'exit_code': None, 'failure': 'TIMEOUT_120_SECONDS'}
    record = {'purpose': 'UNREGISTERED_B31_CPS_EXECUTION_FEASIBILITY',
              'executable_sha256': exe_hash,
              'deck_sha256': hashlib.sha256(content.encode('ascii')).hexdigest(),
              'model': model, **status,
              'files': sorted(path.name for path in args.root.iterdir())}
    (args.root / 'result.json').write_text(json.dumps(record, sort_keys=True, indent=2)+'\n',
                                           encoding='utf-8')
    print(json.dumps(record, sort_keys=True))
    return 0 if status['exit_code'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
