"""Compare saved C1 solid/native bond action on continuous physical traces.

The three x-hat virtual fields are common across the B3 half-cell cut, so
their work uses the validated *total* weak solid bond action. This does not
partition sided bond work or select a multiplier space.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import (
    element_forces, read_deck, recover, wrench,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


BASE = Path('.qualification/b3-ge-e4-pl')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hats(x: np.ndarray) -> np.ndarray:
    stations = np.array((.9, .95, 1.))
    if np.min(x) < .9-1e-10 or np.max(x) > 1.+1e-10:
        raise ValueError('bond action outside registered interval')
    values = np.column_stack(tuple(np.maximum(0., 1.-np.abs(x-s)/.05)
                                   for s in stations))
    if not np.allclose(values.sum(axis=1), 1., rtol=0., atol=1e-10):
        raise ArithmeticError('continuous hat partition failed')
    return values


def _solid_action(folder: Path) -> tuple[np.ndarray, np.ndarray,
                                          np.ndarray, dict]:
    stem = folder/'solid-4-tip_mx'
    model_path = folder/'model.json'
    paths = (stem.with_suffix('.inp'), stem.with_suffix('.frd'),
             stem.with_suffix('.dat'), model_path)
    model = json.loads(model_path.read_text())
    if (model['element_family'] != 'C3D20R'
            or model['bond_policy'] != 'terminal'
            or model['contact_policy'] != 'none'
            or model['boundary_policy'] != 'left_root'
            or model['bond_interval_m'] != [.9, 1.]
            or model['bar_reference_profile'] !=
            'C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1'
            or model['shared_interface_nodes'] != 121
            or model['plate_thickness_m'] != .035
            or model['bar_clearance_um'] != 2
            or model['bar_tip_axis_z_m'] != .0675
            or model['factor'] != 4
            or model['shear'] != 'tip_mx'
            or not model['torque_with_opening_fz']
            or model['reverse_tip_fz']
            or model['tip_load_map'] != 'quadratic_face'):
        raise ValueError('saved F4 physical case changed')
    x, domains = read_deck(paths[0])
    if len(domains['Stiffener']) != 1280:
        raise ValueError('saved F4 bar element inventory changed')
    u_map = _read_frd_u(paths[1])
    if set(u_map) != set(range(1, len(x))):
        raise ValueError('saved F4 nodal response incomplete')
    u = np.array([[0., 0., 0.]]+[u_map[i] for i in range(1, len(x))])
    load = np.zeros_like(x)
    for key, force in model['applied_nodal_forces_N'].items():
        load[int(key)] = force
    load_wrench = wrench(load, x, np.arange(1, len(x)))
    if not np.allclose(load_wrench, (0., 0., -1000., 100., 1000., 0.),
                       rtol=0., atol=1e-8):
        raise ValueError('saved F4 applied load changed')
    if (not np.allclose(x[model['plate_boundary_node_ids'], 0], -.5,
                        rtol=0., atol=1e-10)
            or not np.allclose(x[model['beam_root_node_ids'], 0], 0.,
                               rtol=0., atol=1e-10)):
        raise ValueError('saved F4 support geometry changed')
    bar_internal = np.zeros_like(x)
    plate_internal = np.zeros_like(x)
    conn = domains['Stiffener']
    for start in range(0, len(conn), 128):
        ids = conn[start:start+128]
        forces, _ = element_forces(x[ids], u[ids])
        np.add.at(bar_internal, ids.ravel(), forces.reshape(-1, 3))
    conn_plate = domains['Plate']
    for start in range(0, len(conn_plate), 128):
        ids = conn_plate[start:start+128]
        forces, _ = element_forces(x[ids], u[ids])
        np.add.at(plate_internal, ids.ravel(), forces.reshape(-1, 3))
    seam = np.asarray(model['shared_interface_node_ids'], dtype=int)
    if (not np.allclose(x[seam, 2], .0175, rtol=0., atol=1e-10)
            or np.max(np.abs(x[seam, 1])) > .05+1e-10):
        raise ValueError('saved F4 bonded surface changed')
    # f_internal(bar)-f_applied(bar) is plate-on-bar. Negate for bar-on-plate.
    action = -(bar_internal-load)[seam]
    plate_action = plate_internal[seam]
    printed = recover(folder)['bond']['bar_on_plate_from_printed_support_N_Nm']
    weak_wrench = wrench(-(bar_internal-load), x, seam)
    return x[seam], action, plate_action, {
        'weak_bar_on_plate_wrench_N_Nm': weak_wrench.tolist(),
        'printed_support_bar_on_plate_wrench_N_Nm': printed,
        'weak_minus_printed_wrench_N_Nm':
            (weak_wrench-np.asarray(printed)).tolist(),
        'plate_side_internal_wrench_N_Nm':
            wrench(plate_internal, x, seam).tolist(),
        'seam_side_mismatch_rms_N':
            float(np.sqrt(np.mean((action-plate_action)**2))),
        'seam_side_mismatch_max_N':
            float(np.max(np.abs(action-plate_action))),
        'applied_wrench_about_origin_N_Nm': load_wrench.tolist(),
        'inputs_sha256': {str(p): _sha(p) for p in paths},
    }


def _native_action(results_path: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    manifest_path = results_path.with_name('manifest.json')
    manifest = json.loads(manifest_path.read_text())
    if (manifest['shell_patch_cells_per_side'] != 4
            or manifest['beam_half_cells'] != 12
            or manifest['loads'] != ['+100 Nm tip Mx', '-1000 N tip Fz']
            or manifest['supports'] != 'full left E4 edge and B3 root'
            or manifest['intervals'] != [[.9, .95], [.95, 1.]]):
        raise ValueError('native physical comparator changed')
    root = json.loads(results_path.read_text())['response']
    if (root['patch_cells_per_side'] != 4
            or root['plate_thickness_m'] != .035
            or root['beam_half_cells'] != 12
            or root['e4_elements'] != 140
            or root['shell_nodes'] != 165):
        raise ValueError('native Q4 four-cell comparison changed')
    cases = root['results']['line_hybrid_two_intervals']['cases']
    assembled: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for name in ('tip_mx', 'tip_fz'):
        case = cases[name]
        for row in case['active_shell_nodes']:
            node = int(row['node_row'])
            xyz = np.asarray(row['xyz_m'], dtype=float)
            force = np.asarray(row['force_moment_N_Nm'], dtype=float)
            if node not in assembled:
                assembled[node] = (xyz, force.copy())
            else:
                old_x, old_f = assembled[node]
                if not np.allclose(old_x, xyz, rtol=0., atol=1e-12):
                    raise ValueError('native source node geometry differs')
                old_f += force
    coords = np.array([assembled[k][0] for k in sorted(assembled)])
    actions = np.array([assembled[k][1] for k in sorted(assembled)])
    if not np.allclose(coords[:, 2], 0., rtol=0., atol=1e-12):
        raise ValueError('native shell reference surface changed')
    if np.max(np.abs(coords[:, 1])) > .05+1e-10:
        raise ValueError('native interface action left bonded width')
    physical_wrench = np.r_[actions[:, :3].sum(axis=0),
                             (np.cross(coords, actions[:, :3])+
                              actions[:, 3:]).sum(axis=0)]
    reported = sum((np.asarray(cases[name]['interface_shell_wrench_N_Nm'])
                    for name in ('tip_mx', 'tip_fz')))
    if not np.allclose(physical_wrench, reported, rtol=0., atol=1e-7):
        raise ArithmeticError('active native shell action lost a wrench')
    return coords, actions, {
        'combined_interface_shell_wrench_N_Nm': physical_wrench.tolist(),
        'active_shell_nodes': len(coords),
        'input_sha256': _sha(results_path),
        'manifest_sha256': _sha(manifest_path),
    }


def evaluate(base: Path = BASE) -> dict:
    solid_folder = (base/'f03-ccx-c1-preopen-combined-factor4-dev-20260926-v1'
                    /'solid-4-tip_mx')
    native_path = (base/'f03-c1-hybrid-shell4-two-interval-dev-20260926-v1'
                   /'results.json')
    sx, sf, pf, solid = _solid_action(solid_folder)
    nx, nf, native = _native_action(native_path)
    sh, nh = _hats(sx[:, 0]), _hats(nx[:, 0])
    solid_work = np.column_stack((sf[:, 1], sf[:, 2],
                                  .05*sf[:, 1]+sx[:, 1]*sf[:, 2]))
    plate_work = np.column_stack((pf[:, 1], pf[:, 2],
                                  .05*pf[:, 1]+sx[:, 1]*pf[:, 2]))
    native_work = np.column_stack((nf[:, 1], nf[:, 2],
                                   .0675*nf[:, 1]+nx[:, 1]*nf[:, 2]+nf[:, 3]))
    sp = sh.T@solid_work
    pp = sh.T@plate_work
    np_ = nh.T@native_work
    if (abs(sp[:, 0].sum()-solid['weak_bar_on_plate_wrench_N_Nm'][1]) > 1e-7
            or abs(np_[:, 0].sum()-native['combined_interface_shell_wrench_N_Nm'][1]) > 1e-7):
        raise ArithmeticError('common trace lost lateral force')
    return {
        'classification': 'saved F4 total weak-action common-continuous-trace comparison; no sided work or multiplier-space selection',
        'question': 'Do physically matched solid and native interface actions agree on three continuous longitudinal hats for lateral force, vertical force, and physical twist?',
        'outcome_rule': 'Material common-mode mismatch directs revision of pose/transfer or shell idealization; agreement leaves discontinuous B3 port modes unresolved and requires a justified sided lift before space selection.',
        'physical_case': 'C1 35mm plate/0.1m square bar, terminal x=.9–1m bond, no contact, left plate/root bar fixed, pre-opened -1000N Fz +100Nm Mx; native superposition of separately solved linear cases',
        'virtual_fields': 'Three continuous x hats at .9/.95/1m; Ty=unit y translation, Tz=unit z translation, Twist=rigid x rotation about bar axis z=.0675m. Solid bottom displacement (0,.05,y); E4 reference DOFs (uy=.0675,uz=y,rx=1) give the same top-surface field.',
        'units': ['N', 'N', 'Nm'],
        'solid_hat_action': sp.tolist(),
        'solid_plate_side_hat_action': pp.tolist(),
        'solid_side_hat_discrepancy': (sp-pp).tolist(),
        'native_hat_action': np_.tolist(),
        'native_minus_solid_hat_action': (np_-sp).tolist(),
        'native_minus_solid_channel_relative_l2':
            (np.linalg.norm(np_-sp, axis=0) /
             np.maximum(np.linalg.norm(sp, axis=0), 1e-12)).tolist(),
        'solid_side_discrepancy_over_native_difference_l2':
            (np.linalg.norm(sp-pp, axis=0) /
             np.maximum(np.linalg.norm(np_-sp, axis=0), 1e-12)).tolist(),
        'solid': solid,
        'native': native,
        'limitations': ['solid weak nodal actions derive from rounded FRD displacements; printed support provides the independent integrated wrench check',
                        'Q20 and Q4 response are different physical discretizations at one mesh level',
                        'common continuous fields do not probe the independent B3 half-cell port jump'],
        'source_sha256': {str(Path(__file__)): _sha(Path(__file__)),
                          'scripts/b3_e4_f03_c3d20r_bond_force_recovery.py': _sha(Path('scripts/b3_e4_f03_c3d20r_bond_force_recovery.py')),
                          'scripts/b3_e4_f03_solid_bond_pose_projection.py': _sha(Path('scripts/b3_e4_f03_solid_bond_pose_projection.py'))},
    }


def main() -> None:
    import argparse
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
