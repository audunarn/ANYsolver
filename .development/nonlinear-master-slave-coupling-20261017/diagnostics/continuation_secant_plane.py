"""One frozen-H11 secant-plane family seed; no accepted arc state or public API."""
import argparse
import ast
import copy
import inspect
import json
import pickle
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from continuation_actual_finite_entry import (
    _build_ep_model, _add_tip_load, _independent_equilibrium, identical,
    material_observer, ns, co, DisplacementControl, solve_static_nonlinear,
    constraint_residual_summary, lobatto_layers, _beam_flow_scale,
    plane_stress_elastic_matrix, material_events,
)
from anysolver.plasticity import _jit_hardening_modulus


def serial(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)): return value.item()
    raise TypeError(type(value).__name__)


def main():
    p = argparse.ArgumentParser()
    for name in ('capture', 'previous', 'current', 'output'): p.add_argument(name)
    args = p.parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter(); eps = np.finfo(float).eps
    cap, previous, current = [pickle.loads(Path(path).read_bytes()) for path in (args.capture, args.previous, args.current)]
    original = pickle.dumps((cap, previous, current))
    model, load, probe, grid = _build_ep_model('direct'); _add_tip_load(model, load, grid)
    T, u0, F, Fc, row = [cap[k] for k in ('T', 'u0', 'F', 'F_const', 'row')]
    mapping = co.build_nonlinear_rotating_mpc_map(model, T)
    q0, q1 = [ns._reduced_coordinates(T, u0, mapping.to_linear_displacement(s['displacements'])) for s in (previous, current)]
    x0, x1 = np.r_[q0, float(previous['lam'])], np.r_[q1, float(current['lam'])]
    v = x1-x0; ds = float(np.linalg.norm(v)); assert np.isfinite(ds) and ds > 0.
    t = v/ds; n = len(q1); H = copy.deepcopy(current['element_states']); savedH = copy.deepcopy(H)
    raw = dict(secant=dict(x_previous=x0, x_current=x1, v=v, t=t, ds=ds))
    solves = 0; evaluations = 0

    def log(value):
        with (out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(value, elapsed=time.perf_counter()-start), default=serial)+'\n')

    def observe(label, x, tangent=False):
        nonlocal evaluations
        evaluations += 1
        u = mapping.apply_kinematics(np.asarray(T@x[:n]+u0).reshape(-1)); savedu = u.copy()
        h = copy.deepcopy(H); h0 = copy.deepcopy(h)
        fi, K, trial = ns._assemble_nonlinear_system(model, u, h, 5, tangent=tangent,
            kinematics='corotational', corotational_tangent='work_conjugate')
        assert identical(h, h0) and np.array_equal(u, savedu) and identical(H, savedH)
        r = mapping.reduce_force(u, fi-Fc-x[-1]*F)
        plane = float(t@(x-x1)-ds)
        A = None
        if tangent:
            kr = mapping.reduce_tangent(u, K, fi-Fc-x[-1]*F).toarray()
            A = np.vstack((np.column_stack((kr/4000., -mapping.reduce_force(u, F)/4000.)), t))
        reference = max(float(np.linalg.norm(mapping.reduce_force(u, Fc+max(abs(x[-1]), 1.)*F))), 1.)
        value = dict(x=x.copy(), u=u.copy(), r=r.copy(), fi=fi.copy(), trial=copy.deepcopy(dict(trial)),
            events=material_events(model, H, trial), plane=plane, residual=np.r_[r/4000., plane],
            A=A, reference=reference, control=float(row@u))
        raw[label] = value
        return value

    def charged(A, rhs, label):
        nonlocal solves
        assert solves < 40
        solves += 1; delta = np.linalg.solve(A, rhs); error = A@delta-rhs
        raw[label] = dict(matrix=A.copy(), rhs=rhs.copy(), delta=delta.copy(), linear_error=error.copy(), global_solve=solves)
        log(dict(label=label, global_solve=solves, linear_error=float(np.linalg.norm(error))))
        return delta

    def local_stopping_estimate(value):
        """A-posteriori local source residual transport, not a certified bound."""
        observer = material_observer(model, mapping, value['u'], H, value['trial'], np.zeros(n))
        cursor = 0; total = 0.; points = []
        for witness in observer['witnesses']:
            eid, flat = witness['element'], witness['point']; el = model.mesh.elements[eid]
            mat = model.get_material(el.material_name); E = float(mat.elastic_modulus)
            state, old, kind = value['trial'][eid], H[eid], witness['kind']
            size = 3 if kind == 'shell' else 1; Bq = observer['strain_jacobian'][cursor:cursor+size]; cursor += size
            active = float(state['alpha'][flat]) > float(old['alpha'][flat]); estimate = residual = 0.; derivative = None
            if kind == 'shell':
                cache = el._nonlinear_geometry(model.mesh); gp, layer = divmod(flat, 5)
                _z, weights = lobatto_layers(5, el.thickness); weight = float(cache['gp'][gp]['detw']*weights[layer])
                if active:
                    curve = mat.hardening_curve; C = plane_stress_elastic_matrix(E, float(mat.poisson_ratio))
                    sigma = np.asarray(state['layer_stress'][flat]); trial = C@(state['layer_strain'][flat]-old['plastic_strain'][flat])
                    b = np.asarray([trial[0]+trial[1], trial[0]-trial[1], trial[2]])
                    phi2 = (sigma[0]**2-sigma[0]*sigma[1]+sigma[1]**2)/3+sigma[2]**2
                    g = 2*np.sqrt(max(phi2/3, 1e-30)); dl = (state['alpha'][flat]-old['alpha'][flat])/g
                    Y = float(curve.flow_stress(float(state['alpha'][flat])))
                    hard = float(_jit_hardening_modulus(np.asarray([state['alpha'][flat]]), float(curve.sigma_prop), float(curve.sigma_yield), float(curve.sigma_yield_2), float(curve.eps_p_y1), float(curve.eps_p_y2), float(curve.K), float(curve.n), float(curve._power_offset))[0])
                    G = E/(2*(1+mat.poisson_ratio)); ca = E/(3*(1-mat.poisson_ratio)); dA, dB = 1+ca*dl, 1+2*G*dl
                    dp = -2*(b[0]**2*ca/(12*dA**3)+2*G*(b[1]**2/4+b[2]**2)/dB**3)
                    dg = dp/(np.sqrt(3)*np.sqrt(max(phi2, 1e-30))); derivative = abs(dp-(2/3)*Y*hard*(g+dl*dg))
                    residual = abs(phi2-Y*Y/3)
                    stress_rate = np.asarray([-.5*ca*b[0]/dA**2-G*b[1]/dB**2, -.5*ca*b[0]/dA**2+G*b[1]/dB**2, -2*G*b[2]/dB**2])
                    estimate = float(np.linalg.norm(stress_rate)*residual/derivative) if derivative > 0 and np.isfinite(derivative) else float('inf')
            else:
                length, _ = el._beam_frame_and_transform(el.get_node_coordinates(model.mesh)); config = el._fiber_plasticity_config(mat)
                _y, _z, weights = el._fiber_section_grid(config); weight = float(length*weights[flat])
                if active:
                    Y = float(config.material_curve.flow_stress(float(state['alpha'][flat])))*_beam_flow_scale(mat, config.material_curve)
                    residual = abs(abs(state['fiber_stress'][flat])-Y); estimate = residual
            projected = float(weight*np.linalg.norm(Bq.T)*estimate); total += projected
            points.append(dict(element=eid, point=flat, active=active, consistency_residual=residual,
                consistency_derivative=derivative, stress_error_estimate=estimate, reduced_force_error_estimate=projected))
        return dict(kind='local_a_posteriori_estimate_not_certified_enclosure', force_error_estimate=total, points=points,
            stress_identity_pass=observer['stress_identity_pass'], projected_stress_identity_error=observer['projected_stress_identity_error'])

    def oracles(value):
        case = dict(model=model, load=load, probe=probe, grid=grid, coupling='direct',
            result=SimpleNamespace(displacements=value['u'], load_factor=value['x'][-1], element_states=value['trial']))
        frozen = _independent_equilibrium(case, element_states=H); returned = _independent_equilibrium(case)
        constraints = constraint_residual_summary(model, mapping.to_linear_displacement(value['u']))
        wrench = lambda eq: bool(np.linalg.norm(eq['balance']) <= 1e-6*max(np.linalg.norm(eq['applied_wrench']), 1e-30))
        changes, finite, nonzero = [], True, False
        for eid, state in sorted(value['trial'].items()):
            if not isinstance(state, dict) or 'alpha' not in state: continue
            a, olda = np.asarray(state['alpha']), np.asarray(H[eid]['alpha'])
            ep, oldep = np.asarray(state['plastic_strain']), np.asarray(H[eid]['plastic_strain'])
            finite &= np.all(np.isfinite(a)) and np.all(np.isfinite(ep)) and np.all(a >= olda-64*(abs(np.spacing(a))+abs(np.spacing(olda))))
            nonzero |= bool(np.any(a > 0.) and np.any(abs(ep) > 0.))
            changes.append(dict(element=int(eid), alpha_increase_max=float(np.max(a-olda)),
                plastic_strain_change_max=float(np.max(abs(ep-oldep))), newly_flowing_points=int(np.sum(a-olda > 64*(abs(np.spacing(a))+abs(np.spacing(olda)))))))
        floating = float(np.linalg.norm(64*eps*np.asarray(abs(mapping.jacobian(value['u'])).T@(abs(value['fi'])+abs(Fc+value['x'][-1]*F))).reshape(-1)))
        stopping = local_stopping_estimate(value)
        answer = dict(frozen_relative_R=frozen['relative_residual'], returned_relative_R=returned['relative_residual'],
            frozen_wrench_pass=wrench(frozen), returned_wrench_pass=wrench(returned), constraints=constraints,
            history_finite_monotone=bool(finite), actual_nonzero_plasticity=nonzero, additional_plasticity=changes,
            floating_force_error_estimate=floating, local_stopping_estimate=stopping)
        answer['passed'] = bool(frozen['relative_residual'] <= 1e-7 and returned['relative_residual'] <= 1e-7
            and wrench(frozen) and wrench(returned) and constraints['status'] == 'passed' and finite and nonzero
            and stopping['stress_identity_pass'])
        return answer

    def original_target(seed):
        """Preserve accepted rollback/H11; seed only inside private normal kernel."""
        nonlocal solves
        tree = ast.parse(inspect.getsource(ns._solve_static_displacement_control)); changes = []
        class Seed(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                if node.name == '_solve_static_displacement_control': node.name = '_secant_plane_seed_kernel'
                return self.generic_visit(node)
            def visit_Assign(self, node):
                names = [a.id for a in node.targets if isinstance(a, ast.Name)]
                for key, val in (('target_scale', .2), ('max_control_cutbacks', 0)):
                    if key in names: node.value = ast.Constant(val); changes.append(dict(name=key, value=val))
                if names == ['states_new'] and isinstance(node.value, ast.Name) and node.value.id == 'committed_states':
                    changes.append(dict(name='private_seed_after_accepted_origin', value=True))
                    return [node, *ast.parse('assert T.shape == _diagnostic_T.shape and (T != _diagnostic_T).nnz == 0\nq = _diagnostic_q.copy()\nlam = _diagnostic_lam').body]
                return self.generic_visit(node)
        tree = ast.fix_missing_locations(Seed().visit(tree)); (out/'guarded-target.py').write_text(ast.unparse(tree))
        scope = dict(ns.__dict__); real_factorize = ns.factorize
        scope.update(_diagnostic_T=T, _diagnostic_q=seed['x'][:n].copy(), _diagnostic_lam=float(seed['x'][-1]))
        def factorize(matrix, *a, **kw):
            frame = inspect.currentframe().f_back
            try: local = dict(frame.f_locals)
            finally: del frame
            handle = real_factorize(matrix, *a, **kw)
            class Handle:
                def __getattr__(self, key): return getattr(handle, key)
                def solve(self, rhs):
                    nonlocal solves
                    assert solves < 40; solves += 1; delta = handle.solve(rhs)
                    data = dict(q=local['q'].copy(), u=local['u'].copy(), H=copy.deepcopy(dict(local['committed_states'])),
                        lam=local['lam'], matrix=matrix.copy(), rhs=np.asarray(rhs).copy(), delta=np.asarray(delta).copy())
                    (out/('original-target-solve-'+str(solves).zfill(4)+'.pkl')).write_bytes(pickle.dumps(data))
                    log(dict(label='original-target-solve', global_solve=solves, residual=local.get('residual_norm')))
                    return delta
            return Handle()
        scope['factorize'] = factorize; exec(compile(tree, str(out/'guarded-target.py'), 'exec'), scope)
        original_kernel = ns._solve_static_displacement_control
        try:
            ns._solve_static_displacement_control = scope['_secant_plane_seed_kernel']
            result = solve_static_nonlinear(model, load, control='displacement',
                displacement_control=DisplacementControl(node_id=probe, dof='uz', target_displacement=float(cap['target'])),
                num_steps=1, max_iterations=40-solves, tolerance=1e-8, kinematics='corotational', corotational_tangent='work_conjugate',
                initial_displacements=current['displacements'].copy(), initial_element_states=copy.deepcopy(H),
                equilibrate_initial_state=False, emit_restart_checkpoint=False, record_increment_snapshots=True)
        finally: ns._solve_static_displacement_control = original_kernel
        assert ns._solve_static_displacement_control is original_kernel
        raw['original-target-result'] = dict(status=result.status, reason=result.stop_reason, info=dict(result.info),
            u=result.displacements.copy(), H=copy.deepcopy(dict(result.element_states)), lam=result.load_factor,
            snapshots=copy.deepcopy(result.snapshots), kernel_changes=changes)
        x = np.r_[ns._reduced_coordinates(T, u0, mapping.to_linear_displacement(result.displacements)), float(result.load_factor)]
        physical = observe('original-target-reconstructed', x)
        checks = oracles(physical)
        # Public returned histories are also reconstructed independently.
        case = dict(model=model, load=load, probe=probe, grid=grid, coupling='direct', result=result)
        returned = _independent_equilibrium(case)
        returned_wrench = bool(np.linalg.norm(returned['balance']) <= 1e-6*max(np.linalg.norm(returned['applied_wrench']), 1e-30))
        target_error = abs(physical['control']-float(cap['target']))
        return dict(status=result.status, reason=result.stop_reason, control=physical['control'], target_error=target_error,
            relative_R=float(np.linalg.norm(physical['r'])/physical['reference']), oracles=checks,
            public_returned_relative_R=returned['relative_residual'],
            public_returned_wrench_pass=returned_wrench,
            passed=bool(result.status == 'completed' and target_error <= 2e-9 and target_error <= 1e-8
                and np.linalg.norm(physical['r']) <= 1e-8*physical['reference'] and checks['passed']
                and returned['relative_residual'] <= 1e-7 and returned_wrench))

    def save(report):
        assert solves <= 40 and pickle.dumps((cap, previous, current)) == original and identical(H, savedH)
        report.update(global_solves=solves, evaluations=evaluations, caller_inputs_unchanged=True,
            no_history_committed=True, production_changed=False, elapsed=time.perf_counter()-start)
        (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report, indent=2, default=serial))
        print(json.dumps({k: v for k, v in report.items() if not isinstance(v, (dict, list, np.ndarray))}, default=serial))

    base = observe('base', x1, True)
    value = observe('secant-predictor', x1+v, True)
    status = 'plane_global_solve_budget'
    for correction in range(21):
        (out/('plane-iterate-'+str(solves).zfill(4)+'.pkl')).write_bytes(pickle.dumps(value))
        log(dict(label='plane-iterate', global_solve=solves, R=float(np.linalg.norm(value['r'])),
            reference=value['reference'], plane=value['plane'], control=value['control'], lam=float(value['x'][-1])))
        if np.linalg.norm(value['r']) <= 1e-8*value['reference'] and abs(value['plane']) <= 1e-8:
            status = 'actual_plane_root'; break
        if correction == 20: break
        step = charged(value['A'], -value['residual'], 'plane-solve-'+str(solves+1))
        merit = .5*np.dot(value['residual'], value['residual']); found = None
        for k in range(8):
            alpha = 2.**(-k)
            try: trial = observe('plane-trial-'+str(solves)+'-'+str(k), value['x']+alpha*step)
            except co.SO3MeanDomainError as exc:
                log(dict(label='plane-trial', alpha=alpha, refusal=str(exc))); continue
            phi = .5*np.dot(trial['residual'], trial['residual'])
            log(dict(label='plane-trial', alpha=alpha, merit=float(phi), R=float(np.linalg.norm(trial['r'])), plane=trial['plane']))
            if np.isfinite(phi) and phi <= (1-1e-4*alpha)*merit: found = trial; break
        if found is None: status = 'bounded_augmented_merit_no_improvement'; break
        value = observe('plane-current-'+str(solves), found['x'], True)
    raw['plane-final'] = value
    report = dict(diagnostic_only=True, outcome=status, original_target_acceptance=False,
        secant_length=ds, arc_plane_error=value['plane'], arc_production_R=float(np.linalg.norm(value['r'])),
        arc_relative_R=float(np.linalg.norm(value['r'])/value['reference']),
        arc_control=value['control'], arc_control_change=value['control']-base['control'],
        arc_lambda=float(value['x'][-1]), arc_lambda_change=float(value['x'][-1]-x1[-1]), plane_global_solves=solves)
    if status == 'actual_plane_root':
        checks = oracles(value); distance = float(np.linalg.norm(value['x']-x1))
        ulp = float(64*np.linalg.norm(np.spacing(x1)))
        report.update(arc_oracles=checks, state_distance=distance, state_64ULP=ulp)
        if checks['passed'] and distance > ulp:
            report['outcome'] = 'verified_family_seed_only'
            original_checks = original_target(value)
            report.update(original_target=original_checks, original_target_acceptance=original_checks['passed'],
                outcome='original_first_target_confirmed' if original_checks['passed'] else 'family_seed_original_target_failed')
        else: report['outcome'] = 'plane_root_oracles_or_distinctness_unresolved'
    save(report)


if __name__ == '__main__': main()
