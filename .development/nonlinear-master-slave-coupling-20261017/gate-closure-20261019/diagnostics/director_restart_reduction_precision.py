"""One exact half/negative restart reproduction; algebra references, no repair."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import inspect
import json
from pathlib import Path
import pickle
import sys

import numpy as np
from scipy import linalg

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('director_precision_private',
        REPO / 'tests/test_nonlinear_beam_shell_slice3_director_continuation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = module.base
    import anysolver.nonlinear_static as ns
    import anysolver.nonlinear_performance as performance

    half = base._half_case('interp')
    model, load, probe, grid = module._build('interp')
    base._add_tip_load(model, load, grid)
    supplied_u = half['result'].displacements.copy()
    supplied_h = copy.deepcopy(dict(half['result'].element_states))
    before_u, before_h = supplied_u.copy(), copy.deepcopy(supplied_h)
    origin = {}
    real_assemble = ns._assemble_nonlinear_system
    dc = performance._ORIGINAL_DISPLACEMENT_SOLVER or ns._solve_static_displacement_control
    dc_code = dc.__code__

    def observe(*values, **keywords):
        frame = inspect.currentframe().f_back
        try:
            while frame is not None and frame.f_code is not dc_code:
                frame = frame.f_back
            if not origin and frame is not None:
                assert keywords['tangent'] is False
                assert not frame.f_locals['steps'] and not frame.f_locals['snapshots']
                np.testing.assert_array_equal(values[1], frame.f_locals['initial_u'])
                base._assert_states_equal(values[2], before_h)
                origin.update(u=values[1].copy(), h=copy.deepcopy(values[2]),
                    q=frame.f_locals['q'].copy(), T=frame.f_locals['T'].copy(),
                    u0=frame.f_locals['u0'].copy())
        finally:
            del frame
        return real_assemble(*values, **keywords)

    ns._assemble_nonlinear_system = observe
    try:
        result = module.solve_static_nonlinear(model, load, control='displacement',
            displacement_control=module.DisplacementControl(node_id=probe, dof='uz',
                target_displacement=base.DC_TARGET), kinematics='corotational',
            num_steps=1, max_iterations=1, tolerance=base.DC_TOL,
            initial_displacements=supplied_u, initial_element_states=supplied_h,
            equilibrate_initial_state=False, record_increment_snapshots=True)
    finally:
        ns._assemble_nonlinear_system = real_assemble
    assert origin
    returned_h = copy.deepcopy(dict(result.element_states))
    case = dict(model=model, load=load, probe=probe, grid=grid, result=result, coupling='interp')
    oracle = base._equilibrium_oracle(case)
    mapping = oracle['mpc_map']
    T, u0 = origin['T'], origin['u0']
    linear = mapping.to_linear_displacement(before_u)
    rhs = linear - u0
    dense_q, _residuals, rank, singular = linalg.lstsq(T.toarray(), rhs,
        cond=None, lapack_driver='gelsd')
    dense_u = mapping.apply_kinematics(np.asarray(T @ dense_q + u0).reshape(-1))
    unit_rows = {}
    for row in range(T.shape[0]):
        start, stop = T.indptr[row:row+2]
        if stop-start == 1 and T.data[start] == 1.0:
            unit_rows.setdefault(int(T.indices[start]), row)
    unit_q = unit_u = None
    if len(unit_rows) == T.shape[1]:
        unit_q = rhs[[unit_rows[column] for column in range(T.shape[1])]]
        unit_u = mapping.apply_kinematics(np.asarray(T @ unit_q + u0).reshape(-1))

    # Complete solver/input/history/algebra raw evidence precedes any oracle gate.
    raw = dict(origin=origin, supplied_u=before_u, supplied_h=before_h,
        half_u=half['result'].displacements.copy(), half_load=float(half['result'].load_factor),
        returned_u=result.displacements.copy(), returned_h=returned_h,
        returned_load=float(result.load_factor), status=result.status, info=dict(result.info),
        steps=result.steps, snapshots=[dict(u=s.displacements.copy(),
            h=copy.deepcopy(dict(s.element_states)), load=float(s.load_factor)) for s in result.snapshots],
        linear=linear, dense_q=dense_q, dense_u=dense_u, unit_q=unit_q, unit_u=unit_u,
        unit_rows=unit_rows)
    with (args.output / 'raw.pkl').open('xb') as stream:
        pickle.dump(raw, stream)
    np.testing.assert_array_equal(supplied_u, before_u)
    base._assert_states_equal(supplied_h, before_h)
    base._assert_states_equal(origin['h'], before_h)
    try:
        base._assert_states_equal(returned_h, before_h)
        returned_history_identical = True
    except AssertionError:
        returned_history_identical = False

    def evaluate(name, u, h, lam):
        local_h = copy.deepcopy(h)
        local_before = copy.deepcopy(local_h)
        local_u = u.copy()
        force, _k, candidate = real_assemble(model, local_u, local_h, 5,
            tangent=False, kinematics='corotational', corotational_tangent='work_conjugate')
        base._assert_states_equal(local_h, local_before)
        np.testing.assert_array_equal(local_u, u)
        reduced = mapping.reduce_force(u, force-lam*oracle['F_prop'])
        reference = max(float(np.linalg.norm(mapping.reduce_force(u, lam*oracle['F_prop']))), 1.)
        checked = base._independent_equilibrium(case, displacements=u.copy(),
            load_factor=lam, element_states=copy.deepcopy(h))
        constraints = base.constraint_residual_summary(model, mapping.to_linear_displacement(u))
        replay = dict(name=name, u=u, h=h, force=force, reduced=reduced,
            candidate=copy.deepcopy(dict(candidate)), independent=checked, constraints=constraints)
        with (args.output / f'{name}.pkl').open('xb') as stream:
            pickle.dump(replay, stream)
        return dict(relative_residual=float(np.linalg.norm(reduced))/reference,
            independent_relative_residual=checked['relative_residual'],
            residual_norm=float(np.linalg.norm(reduced)), reference=reference,
            load=lam, constraint_status=constraints['status'],
            wrench_norm=float(np.linalg.norm(checked['balance'])),
            wrench_relative=float(np.linalg.norm(checked['balance'])) /
                max(float(np.linalg.norm(checked['applied_wrench'])), 1e-30),
            u_change_from_half_inf=float(np.max(np.abs(u-before_u))))

    variants = dict(original=before_u, projected=origin['u'], returned=result.displacements,
                    dense_reference=dense_u)
    if unit_u is not None:
        variants['unit_row_reference'] = unit_u
    records = {}
    for name, u in variants.items():
        for label, lam in (('half_load', float(half['result'].load_factor)),
                           ('recovered_load', float(result.load_factor))):
            records[f'{name}_{label}'] = evaluate(f'{name}_{label}', u, before_h, lam)
    records['returned_with_returned_history'] = evaluate('returned_with_returned_history',
        result.displacements, returned_h, float(result.load_factor))
    def projection_record(q):
        return dict(linear_residual_norm=float(np.linalg.norm(T @ q-rhs)),
            linear_residual_inf=float(np.max(np.abs(T @ q-rhs))),
            q_change_inf=float(np.max(np.abs(q-origin['q']))))
    report = dict(status=result.status, negative_steps=len(result.steps),
        adaptation=dict(result.info['displacement_control_adaptation']),
        original_half_status=half['result'].status,
        load_change=float(result.load_factor-half['result'].load_factor),
        caller_immutable=True, returned_history_identical=returned_history_identical,
        T_shape=list(T.shape), dense_rank=int(rank),
        dense_singular_min=float(singular[-1]), dense_singular_max=float(singular[0]),
        unit_rows_complete=unit_u is not None,
        projections=dict(production=projection_record(origin['q']),
                         dense=projection_record(dense_q)), variants=records,
        scope='Same histories/physical controls; algebra references only, no numerical repair adopted.')
    if unit_q is not None:
        report['projections']['unit_rows'] = projection_record(unit_q)
    (args.output / 'result.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
