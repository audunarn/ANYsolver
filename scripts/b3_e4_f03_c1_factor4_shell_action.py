"""Replay saved C1 F4 solid/native bond actions through matched E4 alone.

This is a bounded shell-idealization discriminator using existing linear
physical fields. It is not a coupled-law acceptance or a new external solve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_c1_common_weak_work import _native_action, _solid_action
from scripts.b3_e4_f03_factor5_shell_action import (
    _generalized_wrench, _project_solid_action, _solve_shell, _top_response,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_saved_six_gap_replay import _lookup
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


BASE = Path('.qualification/b3-ge-e4-pl')
STATIONS = (.9, .95, 1.)
Y = (-.05, -.025, 0., .025, .05)
Y_WEIGHTS = np.array((.125, .25, .25, .25, .125))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _native_case_loads(path: Path, shell_nodes: np.ndarray) -> tuple[dict, dict]:
    cases = json.loads(path.read_text())['response']['results'][
        'line_hybrid_two_intervals']['cases']
    loads = {}
    for name in ('tip_mx', 'tip_fz'):
        force = np.zeros((len(shell_nodes), 6))
        for row in cases[name]['active_shell_nodes']:
            node = int(row['node_row'])
            if not np.allclose(row['xyz_m'], shell_nodes[node],
                               rtol=0., atol=1e-12):
                raise ValueError('native shell row coordinates changed')
            force[node] = row['force_moment_N_Nm']
        if not np.allclose(_generalized_wrench(force, shell_nodes),
                           cases[name]['interface_shell_wrench_N_Nm'],
                           rtol=0., atol=1e-7):
            raise ArithmeticError('native shell load lost a wrench')
        loads[name] = force
    return cases, loads


def evaluate(base: Path = BASE) -> dict:
    solid_folder = (base/'f03-ccx-c1-preopen-combined-factor4-dev-20260926-v1'
                    /'solid-4-tip_mx')
    native_path = (base/'f03-c1-hybrid-shell4-two-interval-dev-20260926-v1'
                   /'results.json')
    sx, sf, pf, solid_meta = _solid_action(solid_folder)
    _, _, native_meta = _native_action(native_path)
    xs, ys = local_grid(4, transverse_cells=4)
    shell_nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    if len(shell_nodes) != 165:
        raise ValueError('matched Q4 four-cell shell node layout changed')
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    fixed = {6*j*len(xs)+axis for j in range(len(ys)) for axis in range(6)}
    free = np.array([i for i in range(len(tangent)) if i not in fixed])
    factor = linalg.lu_factor(tangent[np.ix_(free, free)], check_finite=True)
    cases, native_loads = _native_case_loads(native_path, shell_nodes)
    parity = {}
    for name, load in native_loads.items():
        _, shell = _solve_shell(tangent, physical, load, free, factor)
        parity[name] = {
            'interface_work_error_J': float(shell['applied_final_state_work_j']-
                                              cases[name]['interface_shell_work_j']),
            'physical_work_error_J': float(shell['physical_shell_work_j']-
                                             cases[name]['physical_shell_work_j']),
            'free_relative_residual': shell['free_relative_residual'],
        }
        if (abs(parity[name]['interface_work_error_J']) > 1e-7
                or abs(parity[name]['physical_work_error_J']) > 1e-7):
            raise ArithmeticError('E4 native-action shell replay failed')
    # The projection helper indexes a full coordinate array; provide an
    # exact compact copy of the 121 bonded face coordinates and actions.
    compact_x = np.vstack((np.zeros(3), sx))
    compact_ids = np.arange(1, len(sx)+1)
    projected = _project_solid_action(compact_x, compact_ids, sf, xs, ys)
    plate_projected = _project_solid_action(compact_x, compact_ids,
                                            pf, xs, ys)
    projected_wrench = _generalized_wrench(projected, shell_nodes)
    weak_wrench = np.asarray(solid_meta['weak_bar_on_plate_wrench_N_Nm'])
    if not np.allclose(projected_wrench, weak_wrench,
                       rtol=0., atol=1e-7):
        raise ArithmeticError('F4 top-surface projection lost bond wrench')
    combined_native = native_loads['tip_mx']+native_loads['tip_fz']
    states = {}
    diagnostics = {}
    for name, load in (('solid_action', projected),
                       ('solid_plate_side_action', plate_projected),
                       ('native_action', combined_native)):
        state, shell = _solve_shell(tangent, physical, load, free, factor)
        diagnostics[name] = {
            'free_relative_residual': shell['free_relative_residual'],
            'applied_final_state_work_j': shell['applied_final_state_work_j'],
            'physical_shell_work_j': shell['physical_shell_work_j'],
            'numerical_shell_work_j': shell['numerical_shell_work_j'],
            'support_wrench_N_Nm':
                _generalized_wrench(shell['support_rows'], shell_nodes).tolist(),
        }
        states[name] = state
    full_x, _ = read_deck(solid_folder/'solid-4-tip_mx.inp')
    u = _read_frd_u(solid_folder/'solid-4-tip_mx.frd')
    lookup = _lookup({i: full_x[i] for i in range(1, len(full_x))})
    stations = {}
    for x in STATIONS:
        solid_face = np.array([u[lookup(x, y, .0175)]
                               for y in Y])
        e4_faces = {name: np.array([_top_response(state, xs, ys, x, y)
                                    for y in Y])
                    for name, state in states.items()}
        solid_mean = np.average(solid_face, axis=0, weights=Y_WEIGHTS)
        solid_slope = float((solid_face[-1, 2]-solid_face[0, 2])/.1)
        stations[str(round(x*1000))] = {
            'solid_face_mean_m': solid_mean.tolist(),
            'solid_face_slope_z_y_rad': solid_slope,
            'shell_routes': {
                name: {
                    'face_mean_m': np.average(face, axis=0,
                                               weights=Y_WEIGHTS).tolist(),
                    'minus_solid_face_rms_m': float(np.sqrt(np.mean(
                        np.sum((face-solid_face)**2, axis=1)))),
                    'slope_z_y_rad': float((face[-1, 2]-face[0, 2])/.1),
                    'slope_minus_solid_rad': float(
                        (face[-1, 2]-face[0, 2])/.1-solid_slope),
                } for name, face in e4_faces.items()
            },
        }
    return {
        'classification': 'saved-F4 solid-bond-action replay through matched E4 Q4 shell; diagnostic only, no G0B acceptance',
        'status': 'CAUSAL_ALLOCATION_UNRESOLVED_BY_F4_FORCE_RECOVERY',
        'question': 'Does the matched E4 shell under the same saved solid weak bond action reproduce solid plate-face motion, or explain the native common-mode transfer difference?',
        'outcome_rule': 'A causal comparison requires sufficiently accurate solid weak-action recovery. Here the F4 reconstructed Fz and opposite-side disagreement are material, so retain the replay as sensitivity evidence and use the previously validated F5 same-action comparison for shell-side interpretation. No multiplier is selected.',
        'geometry': 'C1 F4 pre-opened combined 35mm plate/0.1m square bar, terminal x=.9–1m bond, no contact, left plate/bar-root supports, -1000N Fz +100Nm Mx; matched E4 Q4 x4/y4 shell',
        'top_surface_work_map': 'E4 δu_top=(δux+.0175δry,δuy-.0175δrx,δuz) m; same solid bond nodal action pulled back to Q4 coordinates',
        'solid_weak_wrench_N_Nm': weak_wrench.tolist(),
        'solid_recovery': solid_meta,
        'native_source': native_meta,
        'projected_e4_wrench_N_Nm': projected_wrench.tolist(),
        'solid_plate_side_e4_wrench_N_Nm':
            _generalized_wrench(plate_projected, shell_nodes).tolist(),
        'native_case_shell_replay': parity,
        'shell_diagnostics': diagnostics,
        'station_faces': stations,
        'limitations': ['one saved F4 physical level and different shell/solid kinematics',
                        'reconstructed solid weak Fz differs from independent printed support by about 1.96 N; this is material for the observed shell face gap',
                        'plate-side internal action is only an error-sensitivity diagnostic; rounded FRD residual makes it unsuitable as a bond load oracle',
                        'the pre-opened combined load is physical; pure torque is only a linear influence',
                        'solid weak action is not a pointwise traction density',
                        'shell-only response does not qualify coupled six-channel or sided port work'],
        'inputs_sha256': {
            str(native_path): _sha(native_path),
            str(solid_folder/'solid-4-tip_mx.inp'):
                _sha(solid_folder/'solid-4-tip_mx.inp'),
            str(solid_folder/'solid-4-tip_mx.frd'):
                _sha(solid_folder/'solid-4-tip_mx.frd'),
            str(solid_folder/'model.json'): _sha(solid_folder/'model.json'),
        },
        'source_sha256': {str(Path(__file__)): _sha(Path(__file__)),
                          'scripts/b3_e4_f03_c1_common_weak_work.py':
                              _sha(Path('scripts/b3_e4_f03_c1_common_weak_work.py')),
                          'scripts/b3_e4_f03_factor5_shell_action.py':
                              _sha(Path('scripts/b3_e4_f03_factor5_shell_action.py'))},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    payload = json.dumps(evaluate(), indent=2, sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == '__main__':
    main()
