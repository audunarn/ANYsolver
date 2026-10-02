"""Bounded US3 modal-output feasibility; not a spectral qualification run.

One virgin plate, no beams, attachment, prestress, refinement or native accuracy
comparison. Printed eigenvalues and full six-coordinate modal fields establish
only whether the retained external route supplies the required observables.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil

EXE_SHA = '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
SUPERVISOR_SHA = '5837645ddf40e591451cbd58f8975ce8f026cb908e750044b848c8c04dcae5d4'
HEADER = re.compile(r'^\s*E I G E N V A L U E\s+N U M B E R\s+(\d+)\s*$', re.M)
TABLE_ROW = re.compile(r'^\s*(\d+)\s+((?:[-+\d.EeDd]+\s+){3}[-+\d.EeDd]+)\s*$')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(output: Path):
    output.mkdir(parents=True, exist_ok=False)
    nx, ny = 16, 4
    nodes = {1+j*(nx+1)+i: (i/nx, .2*j/ny, 0.)
             for j in range(ny+1) for i in range(nx+1)}
    triangles = []
    for j in range(ny):
        for i in range(nx):
            a = 1+j*(nx+1)+i
            b, d, c = a+1, a+nx+1, a+nx+2
            triangles.extend(((a, b, c), (a, c, d)))
    roots = [n for n, p in nodes.items() if p[0] == 0.]
    lines = ['** Virgin supported plate: US3 modal observable canary only',
             '*USER ELEMENT,TYPE=US3,NODES=3,INTEGRATION POINTS=3,MAXDOF=6',
             '*NODE,NSET=AllNodes']
    lines += [str(n)+','+','.join(format(x, '.17g') for x in p) for n, p in nodes.items()]
    lines += ['*ELEMENT,TYPE=US3,ELSET=Panel']
    lines += [str(i)+','+','.join(map(str, tri)) for i, tri in enumerate(triangles, 1)]
    lines += ['*MATERIAL,NAME=Elastic', '*ELASTIC', '210.e9,.3', '*DENSITY', '7850.',
              '*USER SECTION,ELSET=Panel,MATERIAL=Elastic,CONSTANTS=1', '.035', '*BOUNDARY']
    lines += [f'{n},1,6,0.' for n in roots]
    lines += ['*STEP', '*FREQUENCY', '6', '*NODE PRINT,NSET=AllNodes,GLOBAL=YES', 'U', '*END STEP']
    deck = output/'plate-modes.inp'
    deck.write_bytes(('\n'.join(lines)+'\n').encode('ascii'))
    identity = dict(classification='Level A modal-output route feasibility only',
        nx=nx, ny=ny, nodes=len(nodes), elements=len(triangles), physical_rows=6*len(nodes),
        roots=roots, node_ids=list(nodes), requested_modes=6, dimensions_m=[1., .2],
        E_Pa=210.e9, nu=.3, thickness_m=.035, density_kg_m3=7850.,
        supports='all six coordinates at x=0', beam_count=0, attachment_count=0,
        inertia='US3 consistent translation and director rotation; massless normal spin',
        reference_limit='retained source hardcodes ARPACK tol1e-2; output alone does not certify eigen-residual',
        deck_sha256=sha(deck), runner_sha256=sha(Path(__file__)))
    (output/'identity.json').write_text(json.dumps(identity, indent=2)+'\n')
    shutil.copy2(Path(__file__), output/'executed-runner.py')


def number(token):
    d = Decimal(token.replace('D', 'E').replace('d', 'E'))
    if not d.is_finite():
        raise ValueError('nonfinite printed number')
    value = float(d)
    error = float(Decimal(5).scaleb(d.as_tuple().exponent-1))
    if not math.isfinite(value) or not math.isfinite(error) or error <= 0:
        raise ValueError('nonfinite or unrepresentable printed number')
    return value, math.nextafter(error+2*math.ulp(value), math.inf)


def parse(output: Path):
    import numpy as np
    identity = json.loads((output/'identity.json').read_text())
    if sha(output/'plate-modes.inp') != identity['deck_sha256']:
        raise ValueError('executed model changed')
    execution = json.loads((output/'run/execution.json').read_text())
    if execution['exit_code'] != 0 or execution['resource_limit'] is not None:
        raise ValueError('failed or resource-aborted execution cannot publish modes')
    logs = '\n'.join((output/'run'/name).read_text(errors='replace') for name in ('stdout.log', 'stderr.log'))
    if re.search(r'\*\s*(ERROR|WARNING)|ARPACK\s+error|\bFATAL\b', logs, re.I):
        raise ValueError('external error/warning; exit status alone is insufficient')
    dat = (output/'plate-modes.dat').read_text(errors='strict')
    blocks = list(HEADER.finditer(dat))
    if [int(h.group(1)) for h in blocks] != list(range(1, 7)):
        raise ValueError('six uniquely ordered eigenvalue-number headers required')
    table = []
    for line in dat[:blocks[0].start()].splitlines():
        match = TABLE_ROW.fullmatch(line)
        if match:
            table.append((int(match.group(1)), [number(v) for v in match.group(2).split()]))
    if [n for n, values in table] != list(range(1, 7)):
        raise ValueError('complete six-mode eigenvalue/frequency inventory required')
    ids, roots = identity['node_ids'], identity['roots']
    fields, errors, frequencies = [], [], []
    for index, (n, values) in enumerate(table):
        lam, omega, hz, imag = values
        if lam[0] <= 0. or omega[0] <= 0. or hz[0] <= 0. or imag[0] != 0.:
            raise ValueError('positive real finite frequencies required')
        if abs(omega[0]/(2*math.pi)-hz[0]) > omega[1]/(2*math.pi)+hz[1]:
            raise ValueError('printed frequency units inconsistent')
        if abs(math.sqrt(lam[0])-omega[0]) > lam[1]/math.sqrt(lam[0])+omega[1]:
            raise ValueError('printed eigenvalue/frequency inconsistent')
        end = blocks[index+1].start() if index < 5 else len(dat)
        block = dat[blocks[index].end():end]
        header = re.search(r'^\s*displacements\s+\([^\n]*\)\s+for set ALLNODES[^\n]*$', block, re.I|re.M)
        if header is None:
            raise ValueError('modal displacement block missing')
        rows = {}
        for line in block[header.end():].splitlines():
            words = line.split()
            if not words: continue
            if len(words) != 7 or not words[0].isdigit():
                raise ValueError('unexpected or incomplete six-coordinate nodal row')
            node = int(words[0])
            if node not in ids or node in rows:
                raise ValueError('unknown or duplicate modal node')
            rows[node] = [number(w) for w in words[1:]]
        if set(rows) != set(ids):
            raise ValueError('incomplete modal node inventory')
        u = np.array([[v for v, e in rows[node]] for node in ids])
        e = np.array([[e for v, e in rows[node]] for node in ids])
        if np.linalg.norm(u) == 0. or any(np.any(u[ids.index(node)] != 0.) for node in roots):
            raise ValueError('zero mode or violated homogeneous root support')
        fields.append(u); errors.append(e); frequencies.append(hz[0])
    np.savez_compressed(output/'reference-modes.npz', node_ids=ids, modes=fields,
                        printed_errors=errors, eigenvalues=[v[0][0] for n,v in table], frequencies_hz=frequencies)
    result = dict(status='COMPLETED_DEVELOPMENT_ROUTE_ONLY', modes=6, nodes=len(ids),
                  dofs_per_node=6, frequencies_hz=frequencies, reference_eigen_residual='NOT_VERIFIED',
                  native_comparison='NOT_EXECUTED', qualification=False,
                  translation_norm_by_mode=[float(np.linalg.norm(u[:, :3])) for u in fields],
                  director_rotation_norm_by_mode=[float(np.linalg.norm(u[:, 3:5])) for u in fields],
                  normal_spin_norm_by_mode=[float(np.linalg.norm(u[:, 5])) for u in fields],
                  activity_interpretation='separate coordinate observations in external normalization; not mixed-unit norms or accuracy thresholds',
                  dat_sha256=sha(output/'plate-modes.dat'), fields_sha256=sha(output/'reference-modes.npz'))
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def run(output: Path, executable: Path, supervisor: Path):
    if sha(executable) != EXE_SHA or sha(supervisor) != SUPERVISOR_SHA:
        raise ValueError('retained executable/supervisor identity changed')
    spec = importlib.util.spec_from_file_location('owned_supervisor', supervisor)
    service = importlib.util.module_from_spec(spec); spec.loader.exec_module(service)
    identity = json.loads((output/'identity.json').read_text())
    if sha(output/'plate-modes.inp') != identity['deck_sha256']:
        raise ValueError('prepared model changed before execution')
    shutil.copy2(Path(__file__), output/'run-runner.py')
    identity.update(executable=str(executable), executable_sha256=EXE_SHA,
                    supervisor_sha256=SUPERVISOR_SHA, environment=service.ENV,
                    executed_runner_sha256=sha(Path(__file__)))
    (output/'execution-identity.json').write_text(json.dumps(identity, indent=2)+'\n')
    outcome = service.supervised([str(executable), '-i', str(output/'plate-modes')], output/'run')
    if outcome['exit_code'] != 0 or outcome['resource_limit'] is not None:
        raise RuntimeError('external execution failed; raw evidence retained')
    return parse(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'parse'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--supervisor', type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare': prepare(args.output)
    elif args.mode == 'parse': print(json.dumps(parse(args.output)))
    else:
        if args.executable is None or args.supervisor is None: parser.error('executable and supervisor required')
        print(json.dumps(run(args.output, args.executable, args.supervisor)))
