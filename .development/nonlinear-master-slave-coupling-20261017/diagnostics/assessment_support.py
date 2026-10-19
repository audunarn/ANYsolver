"""Independent acceptance instrumentation, not an alternate product solver."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path

import numpy as np

from anysolver.assembly import build_constraint_transformation
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]


def identical(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, np.ndarray):
        return a.shape == b.shape and np.array_equal(a, b, equal_nan=True)
    if isinstance(a, Mapping):
        return a.keys() == b.keys() and all(identical(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(identical(x, y) for x, y in zip(a, b))
    return bool(a == b)


def source_identity():
    paths = [REPO / 'src/anysolver' / name for name in
             ('corotational.py', 'elements.py', 'mesh_gen.py',
              'nonlinear_static.py', 'nonlinear_performance.py', '_corotational_batch.py')]
    paths.extend(sorted(Path(__file__).parent.glob('*.py')))
    return {
        'head': subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'],
                                        text=True).strip(),
        'sha256': {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in paths},
    }


def identities_match(rows, script):
    """Reject mixed product/oracle candidates in retained assessment inputs."""
    paths = ['src/anysolver/'+name for name in
             ('corotational.py', 'elements.py', 'mesh_gen.py',
              'nonlinear_static.py', 'nonlinear_performance.py', '_corotational_batch.py')]
    prefix = str(Path(__file__).parent.relative_to(REPO)).replace('\\', '/')+'/'
    paths += [prefix+'assessment_support.py', prefix+script]
    if script == 'mesh_study.py':
        paths += [prefix+'convergence_study.py']
    fingerprints = [tuple(row.get('identity', {}).get('sha256', {}).get(p)
                          for p in paths) for row in rows]
    return bool(fingerprints and all(all(v is not None for v in fp)
                                    and fp == fingerprints[0] for fp in fingerprints))


def equilibrium(model, load, result, *, tolerance=1e-7, root_nodes=None):
    """Reassemble at the returned load and state; never evolve stored history."""
    u = np.asarray(result.displacements).copy()
    states_before = copy.deepcopy(result.element_states)
    states_input = copy.deepcopy(result.element_states)
    K, _ = assemble_stiffness_matrix(model)
    F, _ = assemble_load_vector(model, load)
    _, _, T, _, _, _ = build_constraint_transformation(K, F, model)
    mapping = build_nonlinear_rotating_mpc_map(model, T)
    fint, _, _ = _assemble_nonlinear_system(
        model, u.copy(), states_input, 5, tangent=False,
        kinematics='corotational', corotational_tangent='work_conjugate',
    )
    external = float(result.load_factor) * F
    reduce = (lambda v: mapping.reduce_force(u, v)) if mapping else (
        lambda v: np.asarray(T.T @ v).reshape(-1))
    residual = float(np.linalg.norm(reduce(external - fint)))
    reference = max(float(np.linalg.norm(reduce(external))), 1.0)
    immutable = (identical(states_before, result.element_states)
                 and identical(states_before, states_input)
                 and np.array_equal(u, result.displacements))
    constraints = result.info.get('constraint_postcheck', {})
    report = {
        'residual_norm': residual, 'reference_norm': reference,
        'relative_residual': residual / reference,
        'state_inputs_unchanged': bool(immutable),
        'constraint_postcheck': constraints,
        'passed': bool(residual / reference <= tolerance and immutable
                       and constraints.get('status') == 'passed'),
    }
    if root_nodes is not None:
        # Include all physical root nodes, not just the independent center-row
        # support DOFs: row ties do not appear in the product's named sum.
        imbalance = fint-external
        if mapping:
            imbalance = mapping.transfer_slave_imbalance_to_masters(u, imbalance)
        force, moment = np.zeros(3), np.zeros(3)
        for node_id in root_nodes:
            node = model.mesh.get_node(node_id)
            dofs = model.mesh.dof_manager.get_node_dofs(node_id)
            position = np.array([node.x, node.y, node.z])+u[dofs[:3]]
            if np.linalg.norm(u[dofs[3:]]) > 1e-12:
                raise ValueError('root-wrench check assumes the declared zero root rotations')
            f = imbalance[dofs[:3]]
            force += f
            moment += np.cross(position, f)+imbalance[dofs[3:]]
        report['physical_root_force_N'] = force.tolist()
        report['physical_root_moment_Nm'] = moment.tolist()
    return report


def write_result(record, path=None):
    payload = json.dumps(record, indent=2, allow_nan=False)
    if path:
        Path(path).write_text(payload + '\n', encoding='utf-8')
    print(payload, flush=True)


def tip_vector(model, displacement, node):
    d = model.mesh.dof_manager.get_node_dofs(node)
    return np.asarray(displacement[d[:3]], dtype=float), float(displacement[d[4]])
