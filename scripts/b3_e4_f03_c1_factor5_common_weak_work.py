"""F5 stress-validated solid/native action on smooth common C1 trace modes.

Two linear hats span the entire terminal bond and are continuous through the
native B3 port cut. This is a physical low-order transfer diagnostic, not a
multiplier-space or G0B acceptance decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import wrench
from scripts.b3_e4_f03_torque_weak_work_split import _action


BASE = Path('.qualification/b3-ge-e4-pl')
FAMILIES = ('line_hybrid_p0_weighted', 'line_hybrid_p1_weighted',
            'line_hybrid_dual_p1_weighted')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hats(x: np.ndarray) -> np.ndarray:
    if np.min(x) < .9-1e-10 or np.max(x) > 1.+1e-10:
        raise ValueError('action outside the bonded interval')
    coordinate = (x-.9)/.1
    hats = np.column_stack((1.-coordinate, coordinate))
    if not np.allclose(hats.sum(axis=1), 1., rtol=0., atol=1e-12):
        raise ArithmeticError('continuous hat partition failed')
    return hats


def _project(x: np.ndarray, force: np.ndarray, *, shell: bool) -> np.ndarray:
    hats = _hats(x[:, 0])
    if shell:
        if force.shape != (len(x), 6) or not np.allclose(x[:, 2], 0.,
                                                         rtol=0., atol=1e-12):
            raise ValueError('native shell action layout changed')
        channels = np.column_stack((force[:, 1], force[:, 2],
                                    .0675*force[:, 1]+x[:, 1]*force[:, 2]
                                    +force[:, 3]))
    else:
        if force.shape != (len(x), 3) or not np.allclose(x[:, 2], .0175,
                                                         rtol=0., atol=1e-10):
            raise ValueError('solid bonded face layout changed')
        channels = np.column_stack((force[:, 1], force[:, 2],
                                    .05*force[:, 1]+x[:, 1]*force[:, 2]))
    return hats.T@channels


def _native_family(native: dict, family: str) -> tuple[np.ndarray, np.ndarray,
                                                        np.ndarray]:
    cases = native['results'][family]['cases']
    combined: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    reported = np.zeros(6)
    for name in ('tip_mx', 'tip_fz'):
        case = cases[name]
        reported += case['interface_shell_wrench_N_Nm']
        for row in case['active_shell_nodes']:
            index = int(row['node_row'])
            point = np.asarray(row['xyz_m'], dtype=float)
            action = np.asarray(row['force_moment_N_Nm'], dtype=float)
            if index not in combined:
                combined[index] = (point, action.copy())
            else:
                old_point, old_action = combined[index]
                if not np.allclose(point, old_point, rtol=0., atol=1e-12):
                    raise ValueError('native case node geometry changed')
                old_action += action
    x = np.array([combined[i][0] for i in sorted(combined)])
    force = np.array([combined[i][1] for i in sorted(combined)])
    if np.max(np.abs(x[:, 1])) > .05+1e-10:
        raise ValueError('native interface left bonded width')
    calculated = np.r_[force[:, :3].sum(axis=0),
                       (np.cross(x, force[:, :3])+force[:, 3:]).sum(axis=0)]
    if not np.allclose(calculated, reported, rtol=0., atol=1e-7):
        raise ArithmeticError('native combined shell wrench changed')
    return x, force, calculated


def evaluate(base: Path = BASE) -> dict:
    folder = (base/'f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1'
              /'solid-5-tip_mx')
    model_path = folder/'model.json'
    model = json.loads(model_path.read_text())
    if (model['element_family'] != 'C3D20R'
            or model['factor'] != 5
            or model['bond_interval_m'] != [.9, 1.]
            or model['bond_policy'] != 'terminal'
            or model['contact_policy'] != 'none'
            or model['boundary_policy'] != 'left_root'
            or model['bar_reference_profile'] !=
            'C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1'
            or model['plate_thickness_m'] != .035
            or model['bar_tip_axis_z_m'] != .0675
            or model['shared_interface_nodes'] != 181
            or not model['torque_with_opening_fz']
            or model['reverse_tip_fz']
            or model['tip_load_map'] != 'quadratic_face'):
        raise ValueError('saved F5 physical model changed')
    recovery_path = (base/'f03-c1-factor5-stress-force-recovery-dev-20260926-v1'
                     /'result.json')
    recovery = json.loads(recovery_path.read_text())
    if recovery['validation']['status'] != 'PASSED_SAVED_STATE_AND_WEAK_FORCE_CHECKS':
        raise ValueError('validated F5 stress action required')
    stress_stem = (base/'f03-c1-factor5-stiffener-ip-stress-dev-20260926-v1'
                   /'solid-5-tip_mx')
    xyz, solid_force, elements = _action(stress_stem, model)
    if len(elements['Stiffener']) != 3000:
        raise ValueError('F5 bar element inventory changed')
    seam = np.asarray(model['shared_interface_node_ids'], dtype=int)
    sx = xyz[seam]
    if np.max(np.abs(sx[:, 1])) > .05+1e-10:
        raise ValueError('solid action left bonded width')
    full_action = np.zeros_like(xyz)
    full_action[seam] = solid_force
    solid_wrench = wrench(full_action, xyz, seam)
    expected = recovery['reconstruction']['bar_on_plate_stress_wrench_N_Nm']
    if not np.allclose(solid_wrench, expected, rtol=0., atol=1e-7):
        raise ArithmeticError('validated F5 solid stress action changed')
    support = recovery['reconstruction']['bar_on_plate_support_wrench_N_Nm']
    if np.max(np.abs(solid_wrench-support)) > .001:
        raise ArithmeticError('F5 solid action lost independent support check')
    sp = _project(sx, solid_force, shell=False)
    first = ((sp[1, :2]-sp[0, :2])*.05).tolist()
    saved_first = recovery['reconstruction']['x_first_moment_about_095_m_Nm']
    if not np.allclose(first, saved_first[1:3], rtol=0., atol=1e-5):
        raise ArithmeticError('F5 weak-action first x moments changed')
    native_path = (base/'f03-c1-factor5-matched-tip-ports-dev-20260926-v2'
                   /'native-loaded.json')
    native_manifest_path = native_path.with_name('manifest.json')
    native_manifest = json.loads(native_manifest_path.read_text())
    if ('Q4 35mm shell x2/y4' not in native_manifest['native_model']
            or '+100 Nm Mx and -1000 N Fz' not in native_manifest['native_model']
            or 'left shell/root beam supports' not in native_manifest['native_model']):
        raise ValueError('native F5 geometry/load/support record changed')
    native = json.loads(native_path.read_text())
    if (native['beam_half_cells'] != 12 or native['bond_x_cells'] != 2
            or native['bond_y_cells'] != 4
            or native['plate_thickness_m'] != .035
            or native['e4_elements'] != 120
            or native['shell_nodes'] != 143):
        raise ValueError('native F5 comparator changed')
    candidates = {}
    for family in FAMILIES:
        nx, nf, native_wrench = _native_family(native, family)
        np_ = _project(nx, nf, shell=True)
        native_first = ((np_[1, :2]-np_[0, :2])*.05)
        candidates[family] = {
            'native_hat_action': np_.tolist(),
            'native_minus_solid_hat_action': (np_-sp).tolist(),
            'relative_l2_by_channel':
                (np.linalg.norm(np_-sp, axis=0) /
                 np.maximum(np.linalg.norm(sp, axis=0), 1e-12)).tolist(),
            'native_shell_wrench_N_Nm': native_wrench.tolist(),
            'native_first_x_moment_yz_Nm': native_first.tolist(),
            'native_minus_solid_first_x_moment_yz_Nm':
                (native_first-np.asarray(first)).tolist(),
            'active_shell_nodes': len(nx),
        }
    return {
        'classification': 'validated saved-F5 common continuous weak-action comparison; finite-grid physical diagnostic, not multiplier selection',
        'question': 'Does the F4 stationwise difference persist in low-order lateral, vertical, and physical twist transfer when the saved solid weak action is recovered from validated F5 integration-point stresses?',
        'outcome_rule': 'Persistent low-order differences require shell-side/connection attribution with same-action response; small differences would leave only one-sided retained-port modes. No single finite grid ranks P0/P1/dual.',
        'physical_case': 'C1 35mm plate/0.1m square bar, terminal x=.9–1m bond, no contact, left plate and bar-root supports, pre-opened -1000N Fz +100Nm Mx; native separate linear cases superposed',
        'virtual_fields': 'Two continuous linear x hats over .9–1m, Ty, Tz and rigid Twist about beam z=.0675m; on solid bottom δu=(0,.05,y), on E4 reference δq=(uy=.0675,uz=y,rx=1)',
        'units': ['N', 'N', 'Nm'],
        'solid_hat_action': sp.tolist(),
        'solid_first_x_moment_yz_Nm': first,
        'solid_wrench_N_Nm': solid_wrench.tolist(),
        'solid_minus_support_wrench_N_Nm':
            (solid_wrench-np.asarray(support)).tolist(),
        'native_candidates': candidates,
        'limitations': ['one saved F5 mesh and Q4/B3 versus Q20 solid idealization',
                        'smooth common fields do not test one-sided B3 half-cell port modes',
                        'pure torque is an algebraic influence of the pre-opened combined case',
                        'physical transfer and finite-grid rank do not establish uniform inf-sup stability'],
        'inputs_sha256': {str(p): _sha(p) for p in (model_path, recovery_path,
            stress_stem.with_suffix('.inp'), stress_stem.with_suffix('.dat'),
            native_path, native_manifest_path)},
        'source_sha256': {str(Path(__file__)): _sha(Path(__file__)),
                          'scripts/b3_e4_f03_torque_weak_work_split.py':
                              _sha(Path('scripts/b3_e4_f03_torque_weak_work_split.py'))},
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
