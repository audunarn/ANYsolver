"""Bounded cut-flux check for the saved C1 F4 pre-opened solid reference.

This checks whether a cut at x=.95 m can separate the *weak* shared-node
bond action into left/right work. It does not infer an exact Cauchy traction
from the saved reduced-integration solution or qualify a native line space.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import (
    _CORNERS, _EDGES, element_forces, read_deck, shape20, wrench,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


CUT = .95
ROOT = Path('.qualification/b3-ge-e4-pl')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _face_flux(x: np.ndarray, u: np.ndarray, sign: int,
               young: float = 210e9, poisson: float = .3,
               order: int = 3, axis: int = 0) -> np.ndarray:
    """Consistent Q20 face action from its own displacement-derived stress."""
    points, weights = np.polynomial.legendre.leggauss(order)
    mu = young/(2*(1+poisson))
    lame = young*poisson/((1+poisson)*(1-2*poisson))
    force = np.zeros((20, 3))
    tangent_axes = ((1, 2), (2, 0), (0, 1))[axis]
    for j, y in enumerate(points):
        for k, z in enumerate(points):
            local = np.zeros(3)
            local[axis] = sign
            local[tangent_axes[0]] = y
            local[tangent_axes[1]] = z
            n, dn = shape20(local)
            jac = x.T @ dn
            det = np.linalg.det(jac)
            if not np.isfinite(det) or det <= 0:
                raise ValueError('invalid face Jacobian')
            grad = dn @ np.linalg.inv(jac)
            du = u.T @ grad
            eps = .5*(du+du.T)
            stress = 2*mu*eps+lame*np.trace(eps)*np.eye(3)
            area = sign*np.cross(jac[:, tangent_axes[0]],
                                 jac[:, tangent_axes[1]])
            force += weights[j]*weights[k]*n[:, None]*(stress @ area)
    return force


def _patch() -> dict:
    """Two-block constant-stress patch: cut forces must cancel exactly."""
    a = np.array(((.001, .002, -.003), (.004, -.002, .001),
                  (.002, .003, .0005)))
    corners = np.vstack((_CORNERS,
                         [(_CORNERS[i]+_CORNERS[j])/2 for i, j in _EDGES]))
    elements = []
    for center in (-.5, .5):
        x = corners*np.array((.5, .5, .5))+np.array((center, 0., 0.))
        u = x @ a.T + np.array((.3, -.2, .1))
        elements.append((x, u))
    f = [element_forces(x[None], u[None], young=1000,
                        poisson=.25)[0][0] for x, u in elements]
    cut = [_face_flux(x, u, sign, young=1000, poisson=.25)
           for (x, u), sign in zip(elements, (1, -1))]
    cut_resultant = sum((c.sum(axis=0) for c in cut))
    cut_work = sum(float(np.sum(c*u)) for c, (_, u) in zip(cut, elements))
    stress = 800*.5*(a+a.T)+400*np.trace(a)*np.eye(3)
    expected = stress[:, 0]
    boundary = [sum((_face_flux(x, u, sign, young=1000, poisson=.25,
                                axis=axis) for axis in range(3)
                    for sign in (-1, 1)), np.zeros((20, 3)))
                for x, u in elements]
    errors = {
        'cut_action_cancellation_N': float(np.linalg.norm(cut_resultant)),
        'cut_work_cancellation_J': abs(cut_work),
        'left_resultant_error_N': float(np.linalg.norm(cut[0].sum(axis=0)-expected)),
        'right_resultant_error_N': float(np.linalg.norm(cut[1].sum(axis=0)+expected)),
        'left_volume_global_resultant_N': float(np.linalg.norm(f[0].sum(axis=0))),
        'left_basis_volume_boundary_max_N': float(np.max(np.abs(f[0]-boundary[0]))),
        'right_basis_volume_boundary_max_N': float(np.max(np.abs(f[1]-boundary[1]))),
    }
    if max(errors.values()) > 1e-10:
        raise AssertionError(f'cut-flux constant-stress patch failed: {errors}')
    return errors


def evaluate(base: Path = ROOT) -> dict:
    folder = base / 'f03-ccx-c1-preopen-combined-factor4-dev-20260926-v1/solid-4-tip_mx'
    stem = folder / 'solid-4-tip_mx'
    paths = (stem.with_suffix('.inp'), stem.with_suffix('.frd'), folder/'model.json')
    model = json.loads(paths[2].read_text())
    if (model['element_family'] != 'C3D20R'
            or model['bond_policy'] != 'terminal' or model['contact_policy'] != 'none'
            or model['boundary_policy'] != 'left_root'
            or model['bond_interval_m'] != [.9, 1.]
            or model['factor'] != 4 or model['shear'] != 'tip_mx'
            or model['tip_load_map'] != 'quadratic_face'
            or not model['torque_with_opening_fz']
            or model['reverse_tip_fz']
            or model['shared_interface_nodes'] != 121
            or model['plate_thickness_m'] != .035
            or model['bar_reference_profile'] != 'C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1'):
        raise ValueError('saved pre-opened C1 F4 model changed')
    x, domains = read_deck(paths[0])
    applied = np.zeros_like(x)
    for node, force in model['applied_nodal_forces_N'].items():
        applied[int(node)] = force
    total_wrench = wrench(applied, x, np.arange(1, len(x)))
    if not np.allclose(total_wrench, (0., 0., -1000., 100., 1000., 0.),
                       rtol=0., atol=1e-8):
        raise ValueError('F4 applied wrench changed')
    if (not np.allclose(x[model['plate_boundary_node_ids'], 0], -.5,
                        rtol=0., atol=1e-10)
            or not np.allclose(x[model['beam_root_node_ids'], 0], 0.,
                               rtol=0., atol=1e-10)):
        raise ValueError('F4 support geometry changed')
    if len(domains['Stiffener']) != 1280:
        raise ValueError('F4 bar element inventory changed')
    fields = _read_frd_u(paths[1])
    if set(fields) != set(range(1, len(x))):
        raise ValueError('incomplete saved F4 displacements')
    u = np.array([[0., 0., 0.]]+[fields[i] for i in range(1, len(x))])
    conn = domains['Stiffener']
    xx = x[conn, 0]
    left = np.flatnonzero(np.isclose(xx.max(axis=1), CUT, atol=1e-10)
                          & (xx.min(axis=1) < CUT-1e-10))
    right = np.flatnonzero(np.isclose(xx.min(axis=1), CUT, atol=1e-10)
                           & (xx.max(axis=1) > CUT+1e-10))
    if len(left) != 64 or len(right) != 64:
        raise ValueError('F4 cut must have 64 elements on each side')
    cut_actions = []
    high_order_actions = []
    cut_volume = []
    cut_ids = np.unique(conn[np.r_[left, right]].ravel())
    cut_ids = cut_ids[np.isclose(x[cut_ids, 0], CUT, atol=1e-10)]
    seam = np.asarray(model['shared_interface_node_ids'], dtype=int)
    seam_cut = np.intersect1d(cut_ids, seam)
    if len(seam_cut) != 17:
        raise ValueError('F4 seam cut must have 17 nodes')
    for indices, sign in ((left, 1), (right, -1)):
        action = np.zeros_like(x)
        high_order = np.zeros_like(x)
        volume = np.zeros_like(x)
        for i in indices:
            nodes = conn[i]
            np.add.at(action, nodes, _face_flux(x[nodes], u[nodes], sign))
            np.add.at(high_order, nodes, _face_flux(x[nodes], u[nodes], sign,
                                                     order=5))
            fi, _ = element_forces(x[nodes][None], u[nodes][None])
            np.add.at(volume, nodes, fi[0])
        cut_actions.append(action)
        high_order_actions.append(high_order)
        cut_volume.append(volume)
    c0, c1 = cut_actions
    mismatch = c0+c1
    resultant_scale = max(np.linalg.norm(c0[cut_ids].sum(axis=0)),
                          np.linalg.norm(c1[cut_ids].sum(axis=0)), 1.)
    work_scale = max(abs(np.sum(c0[cut_ids]*u[cut_ids])),
                     abs(np.sum(c1[cut_ids]*u[cut_ids])), 1e-12)
    quadrature_difference = [float(np.linalg.norm((low-high)[cut_ids]) /
                             max(np.linalg.norm(high[cut_ids]), 1e-12))
                             for low, high in zip(cut_actions, high_order_actions)]
    return {
        'classification': 'saved-F4 reduced-integration Q20 face-stress cut diagnostic; not exact bond partition or native-line qualification',
        'decision_question': 'Do displacement-derived opposing cut face actions cancel sufficiently to justify a bounded sided weak-work reconstruction?',
        'outcome_rule': 'If cut action or work mismatch is material, no exact sided comparison follows from these saved fields; if small, next derive the discrete side identity and error bound before comparing native ports.',
        'patch': _patch(),
        'geometry': 'C1 35mm plate/square bar, terminal x=.9–1m shared bond, no contact outside, pre-opened -1000N Fz +100Nm Mx combined load; cut x=.95m',
        'applied_wrench_about_origin_N_Nm': total_wrench.tolist(),
        'inventory': {'left_cut_elements': len(left), 'right_cut_elements': len(right),
                      'cut_nodes': len(cut_ids), 'seam_cut_nodes': len(seam_cut)},
        'cut': {
            'left_wrench_N_Nm': wrench(c0, x, cut_ids).tolist(),
            'right_wrench_N_Nm': wrench(c1, x, cut_ids).tolist(),
            'mismatch_wrench_N_Nm': wrench(mismatch, x, cut_ids).tolist(),
            'nodal_mismatch_rms_N': float(np.sqrt(np.mean(mismatch[cut_ids]**2))),
            'nodal_mismatch_max_N': float(np.max(np.abs(mismatch[cut_ids]))),
            'resultant_mismatch_relative': float(np.linalg.norm(mismatch[cut_ids].sum(axis=0))/resultant_scale),
            'left_displacement_work_J': float(np.sum(c0[cut_ids]*u[cut_ids])),
            'right_displacement_work_J': float(np.sum(c1[cut_ids]*u[cut_ids])),
            'displacement_work_mismatch_relative': float(abs(np.sum(mismatch[cut_ids]*u[cut_ids]))/work_scale),
            'face_3_to_5_point_action_relative_difference': quadrature_difference,
            'seam_cut_left_volume_minus_flux_wrench_N_Nm': wrench(cut_volume[0]-c0, x, seam_cut).tolist(),
            'seam_cut_right_volume_minus_flux_wrench_N_Nm': wrench(cut_volume[1]-c1, x, seam_cut).tolist(),
        },
        'limitations': ['face stress is evaluated from saved rounded nodal displacements, not an equilibrated traction field',
                        'the patch verifies the constant-stress cut sign and work identity only',
                        'no left/right bond action or B3 port work is claimed'],
        'inputs_sha256': {str(p): _sha(p) for p in paths},
        'source_sha256': {str(Path(__file__)): _sha(Path(__file__)),
                          'scripts/b3_e4_f03_c3d20r_bond_force_recovery.py': _sha(Path('scripts/b3_e4_f03_c3d20r_bond_force_recovery.py'))},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = evaluate()
    payload = json.dumps(result, indent=2, sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == '__main__':
    main()
