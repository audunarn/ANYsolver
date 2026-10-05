"""Bounded all-user U1/US3 five-row feasibility, not BL5 qualification.

The port explicitly integrates nodal P1 traces. It is not the consistent U1
interior interpolation or the retained B3 half-cell trace. DAT precision can
check algebraic compatibility at its rounding floor, not programme tolerances.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import psutil

EXE_SHA = '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
NODES = {1: (F(0), F(0), F(0)), 2: (F(1), F(0), F(0)),
         3: (F(0), F(1, 5), F(0)),
         10: (F(0), F(0), F(27, 400)),
         11: (F(1, 2), F(0), F(27, 400)),
         12: (F(1), F(0), F(27, 400))}
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def rows():
    # Physical order: three translation rows, then two director rows.
    result = [dict() for _ in range(5)]
    for node, weight in ((10, F(1, 4)), (11, F(1, 2)), (12, F(1, 4))):
        for i in range(3): result[i][node, i+1] = weight
        result[0][node, 5] = -F(1, 20)*weight
        result[1][node, 4] = F(1, 20)*weight
        for i in range(2): result[3+i][node, 4+i] = weight
    for node in (1, 2):
        for i in range(3): result[i][node, i+1] = -F(1, 2)
        result[0][node, 5] = -F(7, 800)
        result[1][node, 4] = F(7, 800)
        for i in range(2): result[3+i][node, 4+i] = -F(1, 2)
    return result


def algebra_checks(constraints):
    # Exact linearized reference/rigid-motion check of these rows only.
    for axis in range(6):
        fields = {}
        for node, (x, y, z) in NODES.items():
            q = [F(0)]*6
            if axis < 3: q[axis] = F(1)
            else:
                rotation = [F(int(i == axis-3)) for i in range(3)]
                a, b, c = rotation
                q[:3] = (b*z-c*y, c*x-a*z, a*y-b*x)
                q[3:] = rotation
            fields[node] = q
        assert all(sum(coef*fields[n][d-1] for (n, d), coef in row.items()) == 0
                   for row in constraints)
    pivots = ((12, 4), (12, 5), (2, 1), (2, 2), (2, 3))
    ordered = [constraints[i] for i in (3, 4, 0, 1, 2)]
    block = [[row.get(p, F(0)) for p in pivots] for row in ordered]
    assert all(block[i][j] == 0 for i in range(5) for j in range(i+1, 5))
    determinant = math.prod(block[i][i] for i in range(5))
    assert determinant == -F(1, 128)
    yaw = {(n, 2): NODES[n][0] for n in (10, 11, 12)}
    yaw.update({(n, 6): F(1) for n in (10, 11, 12)})
    detected = [sum(coef*yaw.get(key, F(0)) for key, coef in row.items())
                for row in constraints]
    assert detected == [F(0), F(1, 2), F(0), F(0), F(0)]
    return ordered, pivots, str(determinant)


def deck():
    constraints = rows()
    ordered, pivots, determinant = algebra_checks(constraints)
    lines = ['** All-user nodal-P1 five-row feasibility; no native B3 oracle',
             '*USER ELEMENT,TYPE=U1,NODES=2,INTEGRATION POINTS=2,MAXDOF=6',
             '*USER ELEMENT,TYPE=US3,NODES=3,INTEGRATION POINTS=3,MAXDOF=6',
             '*NODE,NSET=AllNodes']
    for node, xyz in NODES.items():
        lines.append(str(node)+','+','.join(format(float(v), '.17g') for v in xyz))
    lines += ['*ELEMENT,TYPE=US3,ELSET=Panel', '1,1,2,3',
              '*ELEMENT,TYPE=U1,ELSET=Beam', '2,10,11', '3,11,12',
              '*MATERIAL,NAME=Elastic', '*ELASTIC', '210.e9,.3',
              '*USER SECTION,ELSET=Panel,MATERIAL=Elastic,CONSTANTS=1', '.035',
              '*BEAM SECTION,ELSET=Beam,MATERIAL=Elastic,SECTION=GENERAL',
              '.01,8.333333333333333e-6,0.,8.333333333333333e-6,.8',
              '0.,1.,0.', '*BOUNDARY', '1,1,6', '3,1,6', '10,1,5']
    for row, pivot in zip(ordered, pivots):
        terms = [(pivot, row[pivot])]+[(k, v) for k, v in sorted(row.items()) if k != pivot]
        lines += ['*EQUATION', str(len(terms))]
        for start in range(0, len(terms), 3):
            lines.append(','.join(f'{n},{d},{float(v):.17g}' for (n, d), v in terms[start:start+3]))
    lines += ['*STEP', '*STATIC', '*CLOAD', '12,4,1.',
              '*NODE PRINT,NSET=AllNodes', 'U', '*END STEP']
    metadata = dict(profile='BL5_U1_US3_NODAL_P1_CANARY_V1_DEV',
        purpose='ALL_USER_PREPROCESS_AND_DIRECTOR_OUTPUT_FEASIBILITY_ONLY',
        engineering='declared generalized U1 J=I22+I33, not a resolved square section',
        port='nodal P1 mean, five exact affine rows; no normal-spin restraint',
        root='shell nodes1/3 six restrained, beam10 only1..5 restrained',
        pivots=pivots, supported_constraint_rank=5, exact_pivot_determinant=determinant,
        constraints=[[[n,d,float(v)] for (n,d),v in sorted(row.items())] for row in constraints],
        beam_lower_arm_m=-.05, shell_upper_arm_m=.0175, beam_axis_z_m=.0675,
        requested_tip_moment_Nm=1., rows=36, production_qualified=False,
        exclusions=['native half-cell equivalence','physical torque accuracy',
                    'support-wrench recovery','F03 assessment','multiplier selection'])
    return '\n'.join(lines)+'\n', metadata


def parse(path, constraints):
    text = path.read_text()
    if text.count('displacements (') != 1:
        raise ValueError('one DAT displacement block required')
    values, radii = {}, {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 7 or not fields[0].isdigit(): continue
        node = int(fields[0])
        if node not in NODES: continue
        if node in values: raise ValueError('duplicate displacement row')
        values[node] = [float(v) for v in fields[1:]]
        # Half a printed decimal unit, plus a binary conversion allowance.
        node_radii = []
        for token in fields[1:]:
            match = re.fullmatch(r'[+-]?\d+\.(\d+)[Ee]([+-]?\d+)', token)
            if match is None: raise ValueError('unsupported DAT number layout')
            # Scientific formatting prints a nonzero value with a nonzero
            # mantissa. Zero does not mean an absolute 5e-7 output floor.
            radius = (0. if float(token) == 0. else
                      .5*10.**(int(match.group(2))-len(match.group(1))))
            node_radii.append(radius+2*math.ulp(float(token)))
        radii[node] = node_radii
    if set(values) != set(NODES) or not all(math.isfinite(v) for q in values.values() for v in q):
        raise ValueError('complete finite six-component displacements required')
    gaps = [math.fsum(float(v)*values[n][d-1] for (n,d),v in row.items()) for row in constraints]
    floors = [math.fsum(abs(float(v))*radii[n][d-1] for (n,d),v in row.items()) for row in constraints]
    compatible = all(abs(gap) <= floor for gap, floor in zip(gaps, floors))
    work = values[12][3]
    if not compatible or not work > 0.:
        raise ValueError('incompatible rounded rows or nonpositive applied work')
    return dict(displacements=values, gaps=gaps, rounding_floors=floors,
                dat_rounding_compatible=compatible, tip_rx_rad=work,
                applied_work_J=work, programme_tolerance_pass=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if SHA(args.executable) != EXE_SHA: raise ValueError('executable hash changed')
    args.output.mkdir(parents=True, exist_ok=False)
    text, metadata = deck()
    (args.output/'canary.inp').write_bytes(text.encode('ascii'))
    shutil.copy2(Path(__file__), args.output/'runner.py')
    metadata.update(executable=str(args.executable.resolve()), executable_sha256=EXE_SHA,
                    deck_sha256=SHA(args.output/'canary.inp'), runner_sha256=SHA(Path(__file__)))
    (args.output/'input.json').write_text(json.dumps(metadata, indent=2)+'\n')
    environment = os.environ.copy()
    settings = {k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
                              'CCX_NPROC_RESULTS','CCX_NPROC_EQUATION_SOLVER')}
    environment.update(settings)
    command = [str(args.executable.resolve()), '-i', 'canary']
    started, peak, threads, limit = time.monotonic(), 0, 0, None
    with (args.output/'stdout.log').open('x') as out, (args.output/'stderr.log').open('x') as err:
        process = subprocess.Popen(command, cwd=args.output, env=environment, stdout=out, stderr=err)
        owner = psutil.Process(process.pid)
        tree = [owner]
        try:
            while process.poll() is None:
                try:
                    tree = [owner]+owner.children(recursive=True)
                    peak = max(peak, sum(p.memory_info().rss for p in tree if p.is_running()))
                    threads = max(threads, sum(p.num_threads() for p in tree if p.is_running()))
                except psutil.NoSuchProcess: pass
                except psutil.AccessDenied: limit = 'resource observation denied'
                if time.monotonic()-started > 180: limit = 'time'
                if peak > 1024**3: limit = 'memory'
                if limit:
                    for p in reversed(tree):
                        try: p.kill()
                        except psutil.NoSuchProcess: pass
                    break
                time.sleep(.02)
            code = process.wait(timeout=10)
        finally:
            if process.poll() is None:
                for p in reversed(tree):
                    try: p.kill()
                    except psutil.NoSuchProcess: pass
    observed = peak > 0
    record = dict(command=command, exit_code=code, resource_limit=limit, environment=settings,
        elapsed_seconds=time.monotonic()-started, resource_observation_available=observed,
        sampled_peak_tree_bytes=peak if observed else None,
        sampled_process_tree_threads=threads if observed else None,
        timeout_seconds=180, memory_limit_bytes=1024**3)
    (args.output/'execution.json').write_text(json.dumps(record, indent=2)+'\n')
    if code or limit: raise RuntimeError('external execution failed; retained outputs')
    stdout = (args.output/'stdout.log').read_text()
    stderr = (args.output/'stderr.log').read_text()
    if (stderr.strip() or 'Job finished' not in stdout or
            re.search(r'\b(?:warning|error|fatal)\b', stdout+stderr, re.IGNORECASE)):
        raise RuntimeError('external solver completion failed; retained outputs')
    cpu_counts = [int(v) for v in re.findall(r'up to\s+(\d+)\s+cpu', stdout, re.IGNORECASE)]
    cpu_counts.extend(int(v) for v in re.findall(r'\bUsing\s+(\d+)\s+cpu', stdout, re.IGNORECASE))
    if not cpu_counts or max(cpu_counts) > 1: raise ValueError('effective numerical CPU report unavailable or exceeds one')
    completed = [line.split() for line in (args.output/'canary.sta').read_text().splitlines()
                 if line.strip() and line.strip()[0].isdigit()]
    if len(completed) != 1 or completed[0][:2] != ['1','1'] or float(completed[0][-1]) != 1.:
        raise ValueError('one completed static increment required')
    result = parse(args.output/'canary.dat', rows())
    result.update(effective_reported_cpu_counts=cpu_counts,
                  status='EXECUTED_ALL_USER_FEASIBILITY_ONLY', production_qualified=False)
    (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], applied_work_J=result['applied_work_J'],
                         elapsed_seconds=record['elapsed_seconds'],
                         peak=record['sampled_peak_tree_bytes'])))


if __name__ == '__main__': main()
