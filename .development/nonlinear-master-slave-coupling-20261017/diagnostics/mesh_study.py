"""One bounded mesh case per process; combine retained JSON with --summarize."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from anysolver import solve_static_nonlinear
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix

from assessment_support import equilibrium, identities_match, source_identity, tip_vector, write_result
from convergence_study import MESHES, build

MESHES = dict(MESHES, P4=(32, 8, 48))
SMALL = ['R1', 'R2', 'R3', 'R4']
FINITE = ['M1', 'M2', 'M3', 'M4', 'P1', 'P2', 'P3', 'P4']


def run_case(name):
    total_force = -12000.0 if name.startswith('R') else -140000.0
    model, load, probe = build(*MESHES[name], total_fz=total_force)
    K, _ = assemble_stiffness_matrix(model)
    F, _ = assemble_load_vector(model, load)
    kr, fr, T, u0, _, _ = build_constraint_transformation(K, F, model)
    linear_u = np.asarray(T @ spsolve(kr.tocsc(), fr) + u0).reshape(-1)
    lin_tip, lin_ry = tip_vector(model, linear_u, probe)
    result = solve_static_nonlinear(
        model, load, kinematics='corotational',
        corotational_tangent='work_conjugate', num_steps=4,
        max_iterations=25, tolerance=1e-8,
    )
    tip, ry = tip_vector(model, result.displacements, probe)
    checked = equilibrium(model, load, result)
    reached = (result.status == 'completed'
               and abs(float(result.load_factor) - 1.0) <= 1e-12)
    return {
        'case': name, 'kind': 'mesh', 'mesh': list(MESHES[name]),
        'total_fz_N': total_force,
        'controls': {'num_steps': 4, 'max_iterations': 25, 'tolerance': 1e-8,
                     'kinematics': 'corotational', 'tangent': 'work_conjugate'},
        'status': result.status, 'load_factor': result.load_factor,
        'stop_reason': result.stop_reason, 'steps': len(result.steps),
        'tip_u_m': tip.tolist(), 'tip_ry_rad': ry,
        'linear_tip_u_m': lin_tip.tolist(), 'linear_tip_ry_rad': lin_ry,
        'linear_uz_at_12kN_m': float(lin_tip[2] * 12000.0 / abs(total_force)),
        'linear_relative_gap': float(abs(tip[2] - lin_tip[2]) / abs(lin_tip[2])),
        'equilibrium': checked, 'passed': bool(reached and checked['passed']),
        'identity': source_identity(),
    }


def summarize(paths):
    rows = {}
    for path in paths:
        row = json.loads(Path(path).read_text())
        if row.get('kind') != 'mesh':
            continue
        if row['case'] in rows:
            raise ValueError(f'duplicate selected mesh case {row["case"]}')
        rows[row['case']] = row
    checks = {'same_product_and_oracle_identity': identities_match(rows.values(), 'mesh_study.py')}
    required = SMALL + FINITE
    checks['all_requested_cases_present'] = all(n in rows for n in required)
    checks['all_complete_and_equilibrated'] = (
        checks['all_requested_cases_present'] and all(rows[n]['passed'] for n in required))
    checks['R4_linear_gap_at_most_2p3_percent'] = (
        'R4' in rows and rows['R4']['linear_relative_gap'] <= .023)
    measures = {}
    for field, component in [('uz', 2), ('ry', None)]:
        def value(name):
            r = rows[name]
            return r['tip_u_m'][component] if component is not None else r['tip_ry_rad']
        for route in ['M', 'P']:
            if route+'3' in rows and route+'4' in rows:
                change = abs(value(route+'4') - value(route+'3')) / abs(value(route+'4'))
                measures[f'{route}3_to_{route}4_{field}'] = change
                checks[f'{route}_last_{field}_change_below_1_percent'] = change < .01
        if 'M4' in rows and 'P4' in rows:
            gap = abs(value('M4')-value('P4')) / max(abs(value('M4')), abs(value('P4')))
            measures[f'M4_P4_{field}_gap'] = gap
            checks[f'M4_P4_{field}_gap_below_0p5_percent'] = gap < .005
    sequences = {}
    for route in ['R', 'M', 'P']:
        available = [route+str(i) for i in range(1, 5) if route+str(i) in rows]
        values = [rows[n]['tip_u_m'][2] for n in available]
        differences = np.diff(values)
        sequences[route] = {
            'cases': available, 'uz_m': values,
            'nonmonotonic': bool(len(differences)>1 and np.any(differences>0)
                                 and np.any(differences<0)),
        }
    return {'kind': 'mesh_summary', 'checks': checks, 'measures': measures,
            'sequences': sequences, 'passed': bool(checks and all(checks.values()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('case', nargs='?', choices=SMALL+FINITE)
    ap.add_argument('--output')
    ap.add_argument('--summarize', nargs='+')
    args = ap.parse_args()
    if args.summarize:
        record = summarize(args.summarize)
    elif args.case:
        record = run_case(args.case)
    else:
        ap.error('a case or --summarize is required')
    write_result(record, args.output)


if __name__ == '__main__':
    main()
