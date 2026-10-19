"""Fixed-step native derivative audit at one saved TRF terminal; no root solves."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[4]
TASK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / 'src'), str(TASK / 'diagnostics')]
import continuation_actual_finite_entry as source_observer
from anysolver._nonlinear_events import material_events
from anysolver.plasticity import _jit_hardening_modulus, lobatto_layers


def read(path):
    with path.open('rb') as stream:
        return pickle.load(stream)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = [args.trf / 'baseline-input.pkl', args.trf / 'terminal.pkl',
              *sorted(args.trf.glob('probe-????.pkl'))]
    hashes = {str(path): digest(path) for path in inputs}
    baseline = read(inputs[0])
    terminal = read(inputs[1])
    probes = [read(path) for path in inputs[2:]]
    x = terminal['evaluation']['x'].copy()
    H = copy.deepcopy(baseline['H0'])
    H_before = copy.deepcopy(H)
    # Unbounded TRF accepts strictly decreasing unmodified squared-residual
    # cost. Reconstruct its last accepted displacement from retained probes.
    accepted = [probes[0]]
    cost = lambda point: .5*float(point['residual'] @ point['residual'])
    for point in probes[1:]:
        if cost(point) < cost(accepted[-1]):
            accepted.append(point)
    assert len(accepted) >= 2
    np.testing.assert_array_equal(accepted[-1]['x'], x)
    raw_direction = x-accepted[-2]['x']
    assert np.linalg.norm(raw_direction, ord=np.inf) > 0
    directions = dict(last_accepted_trf_step=raw_direction/np.linalg.norm(raw_direction, ord=np.inf))
    independent = np.r_[(-1.)**np.arange(x.size-1), .5]
    independent /= np.linalg.norm(independent, ord=np.inf)
    directions['deterministic_coupled'] = independent

    spec = importlib.util.spec_from_file_location('director_derivative_private',
        REPO / 'tests/test_nonlinear_beam_shell_slice3_director_continuation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = module.base
    import anysolver.nonlinear_static as ns
    model, load, probe, grid = module._build('interp')
    base._add_tip_load(model, load, grid)
    T, u0, F, target = (baseline[key] for key in ('T', 'u0', 'external', 'target'))
    mapping = base.build_nonlinear_rotating_mpc_map(model, T)
    assert mapping is not None and mapping.active
    row = module.DisplacementControl(node_id=probe, dof='uz',
        target_displacement=target).full_row(model)
    eps = np.finfo(float).eps
    raw = {}
    assembly_attempts = 0

    def dump(name, value):
        with (args.output / name).open('xb') as stream:
            pickle.dump(value, stream, protocol=5)

    def local_stopping(u, trial):
        """Measured consistency residual -> local stress/alpha error estimates.

        This is a local a-posteriori transport, not an interval certificate.
        Source entry, closure thresholds and returned stresses are unchanged.
        """
        observer = source_observer.material_observer(model, mapping, u, H, trial,
            64*np.abs(np.spacing(x[:-1])))
        cursor, force_error = 0, 0.
        points = []
        for witness in observer['witnesses']:
            eid, point = witness['element'], witness['point']
            element = model.mesh.elements[eid]
            material = model.get_material(element.material_name)
            E, nu = float(material.elastic_modulus), float(material.poisson_ratio)
            state, old = trial[eid], H[eid]
            shell = witness['kind'] == 'shell'
            size = 3 if shell else 1
            Bq = observer['strain_jacobian'][cursor:cursor+size]
            cursor += size
            active = float(state['alpha'][point]) > float(old['alpha'][point])
            error, alpha_error, consistency = 0., 0., 0.
            if shell:
                geometry = element._nonlinear_geometry(model.mesh)
                gp, layer = divmod(point, 5)
                _, weights = lobatto_layers(5, element.thickness)
                weight = float(geometry['gp'][gp]['detw']*weights[layer])
                if active:
                    C = source_observer.plane_stress_elastic_matrix(E, nu)
                    sigma = np.asarray(state['layer_stress'][point])
                    trial_sigma = C @ (np.asarray(state['layer_strain'][point])-
                                       np.asarray(old['plastic_strain'][point]))
                    b = np.array([trial_sigma[0]+trial_sigma[1],
                                  trial_sigma[0]-trial_sigma[1], trial_sigma[2]])
                    phi2 = (sigma[0]**2-sigma[0]*sigma[1]+sigma[1]**2)/3+sigma[2]**2
                    g = 2*np.sqrt(max(phi2/3, 1e-30))
                    dl = (state['alpha'][point]-old['alpha'][point])/g
                    curve = material.hardening_curve
                    Y = float(curve.flow_stress(float(state['alpha'][point])))
                    hard = float(_jit_hardening_modulus(np.array([state['alpha'][point]]),
                        float(curve.sigma_prop), float(curve.sigma_yield),
                        float(curve.sigma_yield_2), float(curve.eps_p_y1),
                        float(curve.eps_p_y2), float(curve.K), float(curve.n),
                        float(curve._power_offset))[0])
                    G, ca = E/(2*(1+nu)), E/(3*(1-nu))
                    dA, dB = 1+ca*dl, 1+2*G*dl
                    dp = -2*(b[0]**2*ca/(12*dA**3)+
                             2*G*(b[1]**2/4+b[2]**2)/dB**3)
                    dg = dp/(np.sqrt(3)*np.sqrt(max(phi2, 1e-30)))
                    slope = abs(dp-(2/3)*Y*hard*(g+dl*dg))
                    consistency = abs(phi2-Y*Y/3)
                    stress_slope = np.array([-.5*ca*b[0]/dA**2-G*b[1]/dB**2,
                        -.5*ca*b[0]/dA**2+G*b[1]/dB**2, -2*G*b[2]/dB**2])
                    dl_error = consistency/slope if slope > 0 and np.isfinite(slope) else float('inf')
                    error = float(np.linalg.norm(stress_slope)*dl_error)
                    alpha_error = float(abs(g+dl*dg)*dl_error)
            else:
                length, _ = element._beam_frame_and_transform(element.get_node_coordinates(model.mesh))
                config = element._fiber_plasticity_config(material)
                _, _, weights = element._fiber_section_grid(config)
                weight = float(length*weights[point])
                if active:
                    curve = config.material_curve
                    Y = float(curve.flow_stress(float(state['alpha'][point])))*source_observer._beam_flow_scale(material, curve)
                    consistency = abs(abs(state['fiber_stress'][point])-Y)
                    error = consistency
                    # E+H>=E for this actual monotone S355 branch.
                    alpha_error = consistency/E
            projected = float(weight*np.linalg.norm(Bq.T)*error)
            force_error += projected
            points.append(dict(element=eid, point=point, kind=witness['kind'], active=active,
                consistency_residual=consistency, local_stress_error=error,
                local_alpha_error=alpha_error, reduced_force_error=projected,
                loading_roundoff=float(witness['loading_uncertainty'])))
        return force_error/4000., points

    def observe(label, xp, tangent=False):
        nonlocal assembly_attempts
        dump(label+'-input.pkl', dict(x=xp.copy(), H=copy.deepcopy(H)))
        history = copy.deepcopy(H)
        u = mapping.apply_kinematics(np.asarray(T @ xp[:-1]+u0).reshape(-1))
        before_u = u.copy()
        assembly_attempts += 1
        force, K, trial = ns._assemble_nonlinear_system(model, u, history, 5,
            tangent=tangent, kinematics='corotational', corotational_tangent='work_conjugate')
        base._assert_states_equal(history, H)
        base._assert_states_equal(H, H_before)
        np.testing.assert_array_equal(u, before_u)
        imbalance = force-xp[-1]*F
        r = np.r_[mapping.reduce_force(u, imbalance)/4000., float(row @ u-target)]
        events = material_events(model, H, trial)
        assert events is not None
        J = mapping.jacobian(u)
        force_float_error = float(np.linalg.norm(64*eps*np.asarray(
            abs(J).T @ (abs(force)+abs(xp[-1]*F))).reshape(-1)))/4000.
        control_float_error = float(64*eps*max(np.sum(abs(row)*abs(u)), abs(target), 1.))
        float_error = float(np.hypot(force_float_error, control_float_error))
        local_error, points = local_stopping(u, trial)
        indicator_uncertainty = 64*eps*np.maximum(1., abs(events.values))
        indicator_cursor = 0
        for eid, state in sorted(trial.items()):
            if not isinstance(state, Mapping) or 'alpha' not in state:
                continue
            group = [point for point in points if point['element'] == eid]
            count = np.asarray(state['alpha']).size
            assert len(group) == count
            indicator_uncertainty[indicator_cursor:indicator_cursor+count] = np.maximum(
                indicator_uncertainty[indicator_cursor:indicator_cursor+count],
                [point['loading_roundoff'] for point in group])
            indicator_cursor += count
            element = model.mesh.elements[eid]
            material = model.get_material(element.material_name)
            curve = (element._fiber_plasticity_config(material).material_curve
                     if group[0]['kind'] == 'beam' else material.hardening_curve)
            for boundary in (curve.eps_p_y1, curve.eps_p_y2):
                local_alpha = np.array([point['local_alpha_error'] for point in group])
                local_alpha += 64*abs(np.spacing(np.asarray(state['alpha']).reshape(-1)))
                indicator_uncertainty[indicator_cursor:indicator_cursor+count] = np.maximum(
                    indicator_uncertainty[indicator_cursor:indicator_cursor+count], local_alpha/boundary)
                indicator_cursor += count
        assert indicator_cursor == events.values.size
        A = None
        if tangent:
            A = np.zeros((x.size, x.size))
            A[:-1, :-1] = mapping.reduce_tangent(u, K, imbalance).toarray()/4000.
            A[:-1, -1] = -mapping.reduce_force(u, F)/4000.
            A[-1, :-1] = np.asarray(row @ J).reshape(-1)
        value = dict(x=xp.copy(), u=u.copy(), H=copy.deepcopy(H), trial=copy.deepcopy(dict(trial)),
            residual=r, A=A, events=events, local_error=local_error,
            float_error=float_error, local_points=points,
            force_float_error=force_float_error, control_float_error=control_float_error,
            indicator_uncertainty=indicator_uncertainty)
        dump(label+'.pkl', value)
        raw[label] = value
        return value

    center = observe('center', x, tangent=True)
    A = center['A']
    singular = np.linalg.svd(A, compute_uv=False)
    report = dict(diagnostic_only=True, global_rhs_solves=0,
        actual_trf_previous_x=accepted[-2]['x'].tolist(), terminal_x=x.tolist(),
        source_reconstruction_residual_inf=float(np.max(abs(center['residual']-terminal['evaluation']['residual']))),
        source_reconstruction_tangent_inf=float(np.max(abs(A-terminal['evaluation']['native_jacobian']))),
        fixed_scaling=dict(force=4000., translation=1., rotation=1., load_factor=1.),
        scaled_singular_values=singular.tolist(),
        scaled_condition=float(singular[0]/singular[-1]), directions={},
        uncertainty_scope='Local measured material-consistency transport and floating envelope, not certified interval bounds.')
    for name, direction in directions.items():
        h = eps**(1/3)*max(1., float(np.max(abs(x))))/float(np.max(abs(direction)))
        points = {factor: observe(name+'-'+str(factor), x+factor*h*direction)
                  for factor in (1., .5, -.5, -1.)}
        predicted = A @ direction
        full = (points[1.]['residual']-points[-1.]['residual'])/(2*h)
        half = (points[.5]['residual']-points[-.5]['residual'])/h
        local = sum(points[f]['local_error'] for f in (.5, -.5))/h
        rounding = sum(points[f]['float_error'] for f in (.5, -.5))/h
        truncation = float(np.linalg.norm(half-full)/3)
        representation = sum(float(np.linalg.norm(abs(A) @ abs(
            points[f]['x']-x-f*h*direction))) for f in (.5, -.5))/h
        action_roundoff = 64*eps*float(np.linalg.norm(abs(A)@abs(direction)))
        uncertainty = local+rounding+truncation+representation+action_roundoff
        difference = float(np.linalg.norm(half-predicted))
        magnitude = float(np.linalg.norm(predicted))
        threshold = 1e-7*magnitude
        common = all(np.array_equal(v['events'].signature, center['events'].signature)
                     for v in points.values())
        common_flow = all([p['active'] for p in v['local_points']] ==
                          [p['active'] for p in center['local_points']] for v in points.values())
        resolved = all(np.all(abs(v['events'].values) > v['indicator_uncertainty'])
                       for v in [center, *points.values()])
        representable = all(not np.array_equal(v['x'], x) for v in points.values())
        status = 'unresolved_branch_switch_or_margin' if not (common and common_flow and resolved and representable) else (
            'passed_prospective_1e_7_directional_diagnostic' if difference+uncertainty <= threshold else (
            'candidate_native_tangent_defect' if uncertainty <= threshold and difference > threshold+uncertainty
            else 'unresolved_derivative_signal_or_uncertainty'))
        report['directions'][name] = dict(status=status, direction=direction.tolist(), h=float(h),
            common_branch=common, common_positive_return_mask=common_flow,
            strict_64eps_and_local_indicator_margins=resolved, representable=representable,
            predicted_norm=magnitude, difference=difference, uncertainty=uncertainty,
            threshold=threshold, local_stopping=local, floating_force_envelope=rounding,
            truncation=truncation, operator_action_roundoff=action_roundoff,
            representation_error_estimate=representation,
            force_difference=float(np.linalg.norm((half-predicted)[:-1])),
            control_difference=float(abs((half-predicted)[-1])),
            operator_scaled_error=difference/max(float(np.linalg.norm(A, 2)*np.linalg.norm(direction)), np.finfo(float).tiny),
            changed_signature_indices={str(f): np.flatnonzero(v['events'].signature != center['events'].signature).tolist()
                                       for f, v in points.items()})
        dump(name+'-derivative.pkl', dict(predicted=predicted, full=full, half=half))
    assert hashes == {str(path): digest(path) for path in inputs}
    base._assert_states_equal(H, H_before)
    report.update(assembly_attempts=assembly_attempts, inputs_unchanged=True)
    (args.output / 'result.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
