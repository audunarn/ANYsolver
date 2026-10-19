"""Reviewed cylindrical composite-strip oracle; one FE assessment per process.

The oracle below is derived from section virtual work, not production forces,
assembly or MPC operators. See analytical_derivation.md and the independent
supervisor_reference_review.md. Only the terminal dead-load state is an arc.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from anysolver import BoundaryCondition, FEModel, LoadCase, create_shell_element, solve_static_nonlinear
from anysolver.elements import BeamElement, CoupledBeamShellElement
from anysolver.mesh_gen import InterpolatedBeamShellMPCElement

from assessment_support import equilibrium, identities_match, source_identity, tip_vector, write_result

L, W, THICKNESS, B, H, E = 1.0, .1, .001, .01, .002, 210e9
BASE_LEVELS = (8, 16, 32)
EXTRA_LEVELS = (64, 128, 256)


def oracle(eccentricity, angle_degrees):
    """Independent engineering-strain/reference-curvature rod solution."""
    phi = math.radians(angle_degrees)
    k = phi / L
    As, Ab = W * THICKNESS, B * H
    Is, Ib = W * THICKNESS**3 / 12, B * H**3 / 12
    zbar = Ab * eccentricity / (As + Ab)
    rigidity = E * (Is + Ib + As * Ab / (As + Ab) * eccentricity**2)
    Ns = -E * As * zbar * k
    Nb = -Ns
    tangent = np.array([math.cos(phi), 0., -math.sin(phi)])
    radii = {'shell': 1/k-zbar, 'beam': 1/k+eccentricity-zbar}
    tips = {name: [radius*math.sin(phi)-L, 0., radius*(math.cos(phi)-1)]
            for name, radius in radii.items()}
    strains = [abs(k * (z-zbar)) for z in
               (-THICKNESS/2, THICKNESS/2, eccentricity-H/2, eccentricity+H/2)]
    return {
        'L': L, 'W': W, 't': THICKNESS, 'beam_b': B, 'beam_h': H, 'E': E, 'nu': 0.,
        'eccentricity': eccentricity, 'angle_degrees': angle_degrees,
        'phi': phi, 'curvature_per_reference_length': k,
        'As': As, 'Ab': Ab, 'Is': Is, 'Ib': Ib,
        'neutral_axis_z': zbar, 'rigidity_Nm2': rigidity,
        'radius_m': radii, 'tip_u_m': tips,
        'Ns_N': Ns, 'Nb_N': Nb,
        'shell_force_N': (Ns*tangent).tolist(), 'beam_force_N': (Nb*tangent).tolist(),
        'shell_centroid_My_Nm': E*Is*k, 'beam_centroid_My_Nm': E*Ib*k,
        'total_terminal_My_Nm': rigidity*k, 'max_material_strain': max(strains),
    }


def rectangle_torsion_constant():
    # Saint-Venant rectangular-section series, wide side B >= H. Torsion is
    # excluded by the stated planar benchmark constraints and is not an oracle.
    terms = sum(math.tanh(n*math.pi*B/(2*H))/n**5 for n in range(1, 100, 2))
    return B*H**3/3 - 64*H**4/math.pi**5 * terms


def build_model(nx, coupling, ref):
    if nx not in BASE_LEVELS + EXTRA_LEVELS:
        raise ValueError('unregistered mesh level')
    nb = nx if coupling == 'matching' else 3*nx//2
    e = ref['eccentricity']
    model = FEModel(f'arc_{coupling}_{nx}_{e}_{ref["angle_degrees"]}')
    model.add_material('elastic', E, 0., density=7850.)
    grid = {}
    for ix in range(nx+1):
        for iy in range(3):
            node = 1 + 3*ix + iy
            grid[ix, iy] = node
            model.add_node(node, L*ix/nx, -W/2+W*iy/2, 0.)
    for ix in range(nx):
        for iy in range(2):
            eid = 1+2*ix+iy
            model.add_element(eid, create_shell_element(
                eid, [grid[ix, iy], grid[ix+1, iy], grid[ix+1, iy+1], grid[ix, iy+1]],
                'elastic', thickness=THICKNESS))
    # Exact cylindrical plane-section row constraints, not a penalty.
    dofs = model.mesh.dof_manager.get_node_dofs
    for ix in range(nx+1):
        master = dofs(grid[ix, 1])
        for iy in (0, 2):
            slave = dofs(grid[ix, iy])
            for component in (0, 2, 4):
                model.add_constraint_equation(
                    terms=((int(slave[component]), 1.), (int(master[component]), -1.)),
                    dependent_dof=int(slave[component]), rhs=0.,
                    source_id=f'cylinder_row_{ix}_{iy}_{component}')
    beam_nodes = []
    for ib in range(nb+1):
        x = L*ib/nb
        node, eid = 10000+ib, 20000+ib
        beam_nodes.append(node)
        model.add_node(node, x, 0., e)
        sx = x*nx/L
        ix = min(int(math.floor(sx)), nx-1)
        xi = sx-ix
        pairs = [(grid[ix, 1], 1-xi), (grid[ix+1, 1], xi)]
        pairs = [(n, w) for n, w in pairs if w > 1e-12]
        if len(pairs) == 1:
            element = CoupledBeamShellElement(eid, node, pairs[0][0], 'elastic',
                                             eccentricity=np.array([0., 0., e]))
        else:
            element = InterpolatedBeamShellMPCElement(
                eid, node, [n for n, w in pairs], np.array([w for n, w in pairs]),
                eccentricity=np.array([0., 0., e]))
        model.add_element(eid, element)
    section = {'area': ref['Ab'], 'Iy': ref['Ib'], 'Iz': H*B**3/12,
               'J': rectangle_torsion_constant(), 'b': B, 'h': H}
    for ib in range(nb):
        model.add_element(30000+ib, BeamElement(
            30000+ib, beam_nodes[ib:ib+2], 'elastic', dict(section)))
    model.add_boundary_condition(BoundaryCondition(
        'planarity', list(grid.values()), {'uy': 0., 'rx': 0., 'rz': 0.}))
    model.add_boundary_condition(BoundaryCondition(
        'root', [grid[0, 1]], {'ux': 0., 'uz': 0., 'ry': 0.}))
    model.apply_boundary_conditions()
    load = LoadCase('terminal_constituent_resultants')
    for iy, weight in enumerate((.25, .5, .25)):
        load.add_nodal_load(grid[nx, iy],
                            forces=np.asarray(ref['shell_force_N'])*weight,
                            moments=(0., ref['shell_centroid_My_Nm']*weight, 0.))
    load.add_nodal_load(beam_nodes[-1], forces=ref['beam_force_N'],
                        moments=(0., ref['beam_centroid_My_Nm'], 0.))
    model.add_load_case(load)
    return (model, load, {'shell': grid[nx, 1], 'beam': beam_nodes[-1]}, nb,
            [grid[0, iy] for iy in range(3)]+[beam_nodes[0]])


def run_case(nx, coupling, eccentricity, angle):
    ref = oracle(eccentricity, angle)
    if ref['max_material_strain'] > .003:
        raise ValueError('outside the prospectively declared small-strain domain')
    model, load, probes, nb, root_nodes = build_model(nx, coupling, ref)
    result = solve_static_nonlinear(
        model, load, kinematics='corotational', corotational_tangent='work_conjugate',
        num_steps=12, max_iterations=40, tolerance=1e-8,
    )
    measured, errors = {}, {}
    for name, node in probes.items():
        displacement, ry = tip_vector(model, result.displacements, node)
        target = np.asarray(ref['tip_u_m'][name])
        measured[name] = {'u_m': displacement.tolist(), 'ry_rad': ry}
        errors[name] = {
            'u_relative': float(np.linalg.norm(displacement-target)/np.linalg.norm(target)),
            'ry_relative': abs(ry-ref['phi'])/abs(ref['phi']),
            'ux_relative': abs(float(displacement[0]-target[0]))/abs(float(target[0])),
            'uz_relative': abs(float(displacement[2]-target[2]))/abs(float(target[2])),
        }
    checked = equilibrium(model, load, result, root_nodes=root_nodes)
    reached = (result.status == 'completed' and abs(result.load_factor-1.) <= 1e-12)
    # Check independently that the actual terminal force couple and intrinsic
    # moments give the intended physical spatial moment at the returned state.
    ds = np.asarray(measured['shell']['u_m'])
    db = np.asarray(measured['beam']['u_m'])
    separation = db-ds+np.array([0., 0., eccentricity])
    actual_M = np.cross(separation, np.asarray(ref['beam_force_N']))
    actual_M[1] += ref['shell_centroid_My_Nm']+ref['beam_centroid_My_Nm']
    actual_M *= float(result.load_factor)
    root = np.asarray(result.steps[-1].support_reactions.get('root', [0.]*6)) if result.steps else np.zeros(6)
    physical_M = np.asarray(checked['physical_root_moment_Nm'])
    moment_balance = abs(float(physical_M[1]+actual_M[1]))/max(abs(float(actual_M[1])), 1.)
    return {
        'kind': 'analytical_arc', 'nx': nx, 'ny': 2, 'n_beam': nb,
        'coupling': coupling, 'eccentricity': eccentricity, 'angle_degrees': angle,
        'oracle': ref, 'measured': measured, 'errors': errors,
        'status': result.status, 'load_factor': result.load_factor,
        'stop_reason': result.stop_reason, 'steps': len(result.steps),
        'equilibrium': checked, 'actual_terminal_moment_Nm': actual_M.tolist(),
        'raw_named_center_support_reaction': root.tolist(),
        'physical_root_My_balance_relative': moment_balance,
        'complete_and_equilibrated': bool(reached and checked['passed']),
        'accuracy_passed': bool(all(r['u_relative'] <= .01 and r['ry_relative'] <= .01
                                    for r in errors.values())),
        'identity': source_identity(),
        'constraints': 'common ux,uz,ry per x-row; uy,rx,rz zero; root row clamped',
        'loading': 'constituent final-tangent dead forces; centroid My; terminal assessment only',
        'controls': {'num_steps': 12, 'max_iterations': 40, 'tolerance': 1e-8,
                     'tangent': 'work_conjugate'},
    }


def summarize(paths):
    groups = {}
    for path in paths:
        row = json.loads(Path(path).read_text())
        if row.get('kind') != 'analytical_arc':
            continue
        key = (row['coupling'], row['eccentricity'], row['angle_degrees'])
        if row['nx'] in groups.setdefault(key, {}):
            raise ValueError(f'duplicate candidate for {key}, nx{row["nx"]}')
        groups[key][row['nx']] = row
    output = []
    for coupling in ('matching', 'nonmatching'):
        for e in (0., .002):
            for angle in (30., 60.):
                levels = groups.get((coupling, e, angle), {})
                ordered = sorted(levels)
                checks = {'base_levels_present': all(n in levels for n in BASE_LEVELS),
                          'all_assessed_cases_complete': bool(levels) and all(
                              r['complete_and_equilibrated'] for r in levels.values())}
                registered = list(BASE_LEVELS+EXTRA_LEVELS)
                checks['registered_refinement_prefix'] = ordered == registered[:len(ordered)]
                def principal_error(row):
                    return max(v for r in row['errors'].values()
                               for k, v in r.items() if k in ('u_relative', 'ry_relative'))
                def change_between(coarse, fine):
                    out = {}
                    for tip in ('shell', 'beam'):
                        a, b = coarse['measured'][tip], fine['measured'][tip]
                        out[tip] = {
                            'u': float(np.linalg.norm(np.asarray(a['u_m'])-b['u_m']) /
                                       np.linalg.norm(b['u_m'])),
                            'ry': abs(a['ry_rad']-b['ry_rad'])/abs(b['ry_rad']),
                        }
                    return out
                extension_eligible = True
                for index in range(3, len(ordered)):
                    old, prev = levels[ordered[index-2]], levels[ordered[index-1]]
                    old_changes = change_between(old, prev)
                    extension_eligible &= (
                        old['complete_and_equilibrated'] and prev['complete_and_equilibrated']
                        and principal_error(prev) < principal_error(old)
                        and any(v > .0025 for r in old_changes.values() for v in r.values()))
                checks['extensions_prospectively_eligible'] = bool(extension_eligible)
                changes = {}
                if len(ordered) >= 2:
                    coarse, fine = levels[ordered[-2]], levels[ordered[-1]]
                    checks['finest_accuracy_at_most_1_percent'] = fine['accuracy_passed']
                    changes = change_between(coarse, fine)
                    checks['last_refinement_at_most_0p25_percent'] = all(
                        v <= .0025 for r in changes.values() for v in r.values())
                else:
                    checks['finest_accuracy_at_most_1_percent'] = False
                    checks['last_refinement_at_most_0p25_percent'] = False
                output.append({'coupling': coupling, 'eccentricity': e,
                               'angle_degrees': angle, 'levels': ordered,
                               'checks': checks, 'last_changes': changes,
                               'passed': all(checks.values())})
    same_identity = identities_match([r for levels in groups.values() for r in levels.values()],
                                    'arc_reference.py')
    return {'kind': 'analytical_summary', 'groups': output,
            'same_product_and_oracle_identity': same_identity,
            'passed': same_identity and all(r['passed'] for r in output)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nx', type=int, choices=BASE_LEVELS+EXTRA_LEVELS)
    ap.add_argument('--coupling', choices=('matching', 'nonmatching'))
    ap.add_argument('--eccentricity', type=float, choices=(0., .002))
    ap.add_argument('--angle', type=float, choices=(30., 60.))
    ap.add_argument('--output')
    ap.add_argument('--summarize', nargs='+')
    args = ap.parse_args()
    if args.summarize:
        record = summarize(args.summarize)
    else:
        if any(v is None for v in (args.nx, args.coupling, args.eccentricity, args.angle)):
            ap.error('all case inputs are required')
        record = run_case(args.nx, args.coupling, args.eccentricity, args.angle)
    write_result(record, args.output)


if __name__ == '__main__':
    main()
