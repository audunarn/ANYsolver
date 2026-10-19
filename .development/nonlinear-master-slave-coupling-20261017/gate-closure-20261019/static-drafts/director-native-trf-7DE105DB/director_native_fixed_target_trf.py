"""One actual frozen-history director root discriminant; no production changes."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import pickle
import sys
from types import SimpleNamespace

import numpy as np
from scipy.optimize import least_squares

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'src'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alpha_progress(candidate, original):
    rows = {}
    for eid, state in candidate.items():
        if isinstance(state, dict) and 'alpha' in state:
            change = np.asarray(state['alpha']) - np.asarray(original[eid]['alpha'])
            rows[str(eid)] = dict(increased_points=int(np.count_nonzero(change > 0)),
                decreased_points=int(np.count_nonzero(change < 0)),
                maximum_increase=float(np.max(change)), minimum_change=float(np.min(change)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    input_hash = digest(args.accepted)
    with args.accepted.open('rb') as stream:
        saved = pickle.load(stream)
    original_u = np.array(saved['displacements'], copy=True)
    H0 = copy.deepcopy(saved['element_states'])
    H0_before = copy.deepcopy(H0)
    initial_lambda = float(saved['lam'])
    spec = importlib.util.spec_from_file_location('director_trf_private',
        REPO / 'tests/test_nonlinear_beam_shell_slice3_director_continuation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = module.base
    import anysolver.nonlinear_static as ns
    from anysolver.corotational import SO3MeanDomainError
    from anysolver.plasticity import PlaneStressConvergenceError
    model, load, probe, grid = module._build('interp')
    base._add_tip_load(model, load, grid)
    K0, _ = base.assemble_stiffness_matrix(model)
    external, _ = base.assemble_load_vector(model, load)
    _, _, T, u0, _, _ = base.build_constraint_transformation(K0, external, model)
    mapping = base.build_nonlinear_rotating_mpc_map(model, T)
    assert mapping is not None and mapping.active
    assert sum(e.director_trace_geometry is not None for e in mapping.entries) == 2
    external = np.asarray(external, dtype=float)
    linear = mapping.to_linear_displacement(original_u)
    q0 = ns._reduced_coordinates(T, u0, linear)
    x0 = np.r_[q0, initial_lambda]
    target = -11.0 / 60.0
    row = module.DisplacementControl(node_id=probe, dof='uz',
        target_displacement=target).full_row(model)
    diagnostic_view = SimpleNamespace(displacements=original_u,
        element_states=H0, load_factor=initial_lambda)
    case = dict(model=model, load=load, probe=probe, grid=grid,
        result=diagnostic_view, coupling='interp',
        _oracle=dict(mpc_map=mapping, F_prop=external))
    cache = {}
    counts = dict(fun_requests=0, jac_requests=0, native_evaluations=0,
                  trf_svd_calls=0, independent_oracle_calls=0)
    events_path = args.output / 'events.jsonl'

    def event(payload):
        with events_path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(payload, allow_nan=False) + '\n')

    def dump(name, value):
        with (args.output / name).open('xb') as stream:
            pickle.dump(value, stream, protocol=5)

    def independent(u, states, lam):
        counts['independent_oracle_calls'] += 1
        checked = base._independent_equilibrium(case, displacements=u.copy(),
            element_states=copy.deepcopy(states), load_factor=float(lam))
        constraint = base.constraint_residual_summary(model,
            mapping.to_linear_displacement(u))
        return dict(relative_residual=checked['relative_residual'],
            constraint_status=constraint['status'],
            wrench_relative=float(np.linalg.norm(checked['balance'])) /
                max(float(np.linalg.norm(checked['applied_wrench'])), 1e-30),
            control_error=float(row @ u-target))

    def evaluate(x):
        x = np.asarray(x, dtype=float)
        key = x.tobytes()
        if key in cache:
            return cache[key]
        if len(cache) >= 40:
            raise RuntimeError('predeclared maximum40 distinct native evaluations exceeded')
        index = counts['native_evaluations'] + 1
        dump(f'probe-{index:04d}-input.pkl', dict(x=x.copy(), H0=copy.deepcopy(H0)))
        u = mapping.apply_kinematics(np.asarray(T @ x[:-1] + u0).reshape(-1))
        u_before = u.copy()
        history = copy.deepcopy(H0)
        force, tangent, candidate = ns._assemble_nonlinear_system(model, u, history, 5,
            tangent=True, kinematics='corotational', corotational_tangent='work_conjugate')
        base._assert_states_equal(history, H0)
        base._assert_states_equal(H0, H0_before)
        np.testing.assert_array_equal(u, u_before)
        full_residual = force - float(x[-1])*external
        reduced = mapping.reduce_force(u, full_residual)
        J = mapping.jacobian(u)
        reduced_tangent = mapping.reduce_tangent(u, tangent, full_residual)
        native_jacobian = np.zeros((x.size, x.size))
        native_jacobian[:-1, :-1] = reduced_tangent.toarray()/4000.
        native_jacobian[:-1, -1] = -mapping.reduce_force(u, external)/4000.
        native_jacobian[-1, :-1] = np.asarray(row @ J).reshape(-1)
        control_error = float(row @ u-target)
        residual = np.r_[reduced/4000., control_error]
        reference = max(float(np.linalg.norm(mapping.reduce_force(u, float(x[-1])*external))), 1.)
        candidate = copy.deepcopy(dict(candidate))
        value = dict(x=x.copy(), u=u.copy(), H0=copy.deepcopy(H0),
            candidate_H=candidate, force=np.asarray(force).copy(), reduced=reduced.copy(),
            residual=residual, native_jacobian=native_jacobian,
            relative_residual=float(np.linalg.norm(reduced))/reference,
            reference=reference, control_error=control_error,
            alpha_progress=alpha_progress(candidate, H0))
        dump(f'probe-{index:04d}.pkl', value)
        counts['native_evaluations'] = index
        cache[key] = value
        event(dict(kind='actual_native_evaluation', index=index,
            relative_residual=value['relative_residual'], control_error=control_error,
            lambda_value=float(x[-1]), alpha_progress=value['alpha_progress']))
        return value

    # The baseline physical oracle is independent of the production tangent.
    dump('baseline-input.pkl', dict(saved=saved, x0=x0, T=T, u0=u0,
        original_u=original_u, H0=H0, external=external, target=target))
    baseline = independent(original_u, H0, initial_lambda)
    initial = evaluate(x0)
    dump('baseline.pkl', dict(independent=baseline, evaluation=initial))
    np.testing.assert_allclose(initial['u'], original_u, rtol=1e-14, atol=1e-15)
    assert baseline['relative_residual'] <= 1e-7
    assert baseline['constraint_status'] == 'passed'
    assert baseline['wrench_relative'] <= 1e-6

    def fun(x):
        counts['fun_requests'] += 1
        if counts['fun_requests'] > 40:
            raise RuntimeError('predeclared maximum40 TRF function requests exceeded')
        return evaluate(x)['residual'].copy()

    def jac(x):
        counts['jac_requests'] += 1
        return evaluate(x)['native_jacobian'].copy()

    trf_module = importlib.import_module('scipy.optimize._lsq.trf')
    original_svd = trf_module.svd

    def counted_svd(*values, **keywords):
        counts['trf_svd_calls'] += 1
        return original_svd(*values, **keywords)

    trf_module.svd = counted_svd
    try:
        solved = least_squares(fun, x0, jac=jac, method='trf', tr_solver='exact',
            x_scale=np.ones_like(x0), loss='linear', max_nfev=40,
            ftol=1e-8, xtol=1e-8, gtol=1e-8)
    except (SO3MeanDomainError, PlaneStressConvergenceError) as error:
        # A refused actual native point stops this one diagnostic. No penalty,
        # clipping, branch substitution, or next-start attempt is introduced.
        base._assert_states_equal(H0, H0_before)
        assert digest(args.accepted) == input_hash
        refusal = dict(kind='typed_native_non_success', error_type=type(error).__name__,
            error=str(error), counts=counts, baseline=baseline,
            caller_inputs_immutable=True, physical_root_oracles_pass=False,
            production_completion_claim=False)
        (args.output / 'result.json').write_text(json.dumps(refusal, indent=2, allow_nan=False))
        print(json.dumps(refusal, indent=2, allow_nan=False), flush=True)
        return
    finally:
        trf_module.svd = original_svd
    terminal = evaluate(solved.x)
    # Terminal and every native probe survive any later physical admission failure.
    dump('terminal.pkl', dict(scipy_result=solved, evaluation=terminal, counts=counts.copy()))
    frozen = independent(terminal['u'], H0, solved.x[-1])
    returned = independent(terminal['u'], terminal['candidate_H'], solved.x[-1])
    base._assert_states_equal(H0, H0_before)
    np.testing.assert_array_equal(original_u, saved['displacements'])
    assert digest(args.accepted) == input_hash
    physical = (terminal['relative_residual'] <= 1e-8
        and frozen['relative_residual'] <= 1e-7 and returned['relative_residual'] <= 1e-7
        and abs(terminal['control_error']) <= 2e-9
        and abs(frozen['control_error']) <= 1e-8
        and frozen['constraint_status'] == returned['constraint_status'] == 'passed'
        and frozen['wrench_relative'] <= 1e-6 and returned['wrench_relative'] <= 1e-6)
    report = dict(kind='actual_native_fixed_target_trf_diagnostic',
        accepted_input=str(args.accepted), accepted_sha256=input_hash,
        target=target, initial_lambda=initial_lambda, terminal_lambda=float(solved.x[-1]),
        scipy_success=bool(solved.success), scipy_status=int(solved.status),
        scipy_message=str(solved.message), scipy_nfev=int(solved.nfev),
        scipy_njev=int(solved.njev), scipy_cost=float(solved.cost),
        scipy_optimality=float(solved.optimality), counts=counts,
        baseline=baseline, terminal_native_relative_residual=terminal['relative_residual'],
        terminal_frozen_history=frozen, terminal_returned_history=returned,
        alpha_progress=terminal['alpha_progress'], caller_inputs_immutable=True,
        physical_root_oracles_pass=bool(physical), production_completion_claim=False,
        derivative_scope='Actual native production tangent; no finite-difference or branch modification.',
        scaling=dict(force=4000., translation=1., rotation=1., load_factor=1.),
        interpretation='Single-start diagnostic only. Negative is not nonexistence or collapse; positive is not public Newton-control acceptance.')
    (args.output / 'result.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
