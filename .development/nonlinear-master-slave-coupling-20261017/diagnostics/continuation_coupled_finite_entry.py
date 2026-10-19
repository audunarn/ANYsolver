"""One exact-source independent-stress finite-entry diagnostic, never production.

Unknown stresses are scaled by the physical elastic modulus.  The local rows
are exactly t-s_production(q,H)/E, including the existing finite entry/closure
rules.  Their algorithmic derivative is explicitly a modified-Newton matrix.
All global RHS solves, including sensitivity/confirmation, share the limit40.
"""
import argparse
import ast
import copy
import hashlib
import inspect
import json
import pickle
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.sparse import csr_matrix

from continuation_actual_finite_entry import (
    _build_ep_model, _add_tip_load, _independent_equilibrium, identical,
    material_observer, ns, co, DisplacementControl, solve_static_nonlinear,
    constraint_residual_summary, lobatto_layers, BeamElement, ShellElement,
    _beam_flow_scale, material_events,
)
from anysolver.plasticity import plane_stress_return_map
from anysolver.corotational import SO3MeanDomainError


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def digest_arrays(value):
    """Hash only cache numerical arrays, never callable/object identities."""
    result = {}
    def visit(item, key):
        if isinstance(item, np.ndarray):
            result[key] = hashlib.sha256(item.tobytes()).hexdigest()
        elif isinstance(item, dict):
            for k, v in sorted(item.items(), key=lambda p: str(p[0])):
                visit(v, key+'/'+str(k))
        elif isinstance(item, (list, tuple)):
            for i, v in enumerate(item):
                visit(v, key+'/'+str(i))
        elif hasattr(item, '__dict__'):
            for k, v in sorted(vars(item).items()):
                if isinstance(v, (np.ndarray, dict, list, tuple)):
                    visit(v, key+'/'+k)
        elif hasattr(type(item), '__slots__'):
            for k in type(item).__slots__:
                visit(getattr(item, k), key+'/'+k)
    visit(value, 'cache')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('capture')
    parser.add_argument('accepted')
    parser.add_argument('output')
    a = parser.parse_args()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    eps = np.finfo(float).eps
    capture = pickle.loads(Path(a.capture).read_bytes())
    cur = pickle.loads(Path(a.accepted).read_bytes())
    original_inputs = pickle.dumps((capture, cur))
    model, load, probe, grid = _build_ep_model('direct')
    _add_tip_load(model, load, grid)
    T, u0, F, Fc, row = (capture[k] for k in ('T', 'u0', 'F', 'F_const', 'row'))
    mapping = co.build_nonlinear_rotating_mpc_map(model, T)
    H = copy.deepcopy(cur['element_states'])
    H_before = copy.deepcopy(H)
    qc = ns._reduced_coordinates(T, u0, mapping.to_linear_displacement(cur['displacements']))
    lamc = float(cur['lam'])
    n = len(qc)
    work_scale, control_scale = 4000., .2
    solves, evaluations = 0, 0
    raw, records = {}, []
    layout = None
    cache_baseline = None

    def log(record):
        record = dict(record, elapsed=time.perf_counter()-started)
        records.append(record)
        with (out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(record, default=serial)+'\n')

    def cache_identity():
        return digest_arrays(dict(reference=co._corotational_cache(model),
            shell={int(eid): el._nonlinear_geometry(model.mesh)
                   for eid, el in model.mesh.elements.items() if isinstance(el, ShellElement)}))

    def assemble(q, lam, t=None, target=None, tangent=True, label='evaluation'):
        nonlocal layout, evaluations, cache_baseline
        evaluations += 1
        u = mapping.apply_kinematics(np.asarray(T@q+u0).reshape(-1))
        saved_u = u.copy()
        hc = copy.deepcopy(H)
        saved_h = copy.deepcopy(hc)
        fi, Kp, trial = ns._assemble_nonlinear_system(model, u, hc, 5,
            tangent=tangent, kinematics='corotational', corotational_tangent='work_conjugate')
        assert identical(hc, saved_h) and np.array_equal(u, saved_u)
        J = mapping.jacobian(u)
        references = co._corotational_cache(model)
        fp_delta = np.zeros_like(fi)
        kp_delta = np.zeros((len(u), len(u))) if tangent else None
        chunks, dimensions, metadata = [], [], []
        t_source, modulus, Bq_blocks, constitutive_blocks = [], [], [], []
        stress_replay_error, history_replay = 0., True
        offset = 0
        for eid, state in sorted(trial.items()):
            if not isinstance(state, dict) or 'alpha' not in state:
                continue
            el = model.mesh.elements[eid]
            material = model.get_material(el.material_name)
            E = float(material.elastic_modulus)
            dofs = np.asarray(el.get_dof_mapping(model.mesh), dtype=int)
            ue = u[dofs]
            reference = references[eid]
            ud, Rrig, deformed = co._corotational_deformation_state(reference, el, ue)
            rotations = ue.reshape(-1, 6)[:, 3:]
            D, U, G = co._pullback_jacobian_factors(reference, el, deformed, rotations, Rrig)
            Bco = D+U@G
            fixed = Bco@J[dofs, :].toarray()
            old = copy.deepcopy(H[eid])
            geometry = []
            if isinstance(el, ShellElement):
                cache = el._nonlinear_geometry(model.mesh)
                T0 = cache['T0']
                uloc = T0@ud
                z, weights = lobatto_layers(5, el.thickness)
                Bs, ws = [], []
                for gp in cache['gp']:
                    slopes = gp['Gw']@uloc
                    Bnl = np.vstack((slopes[0]*gp['Gw'][0], slopes[1]*gp['Gw'][1],
                        slopes[0]*gp['Gw'][1]+slopes[1]*gp['Gw'][0]))
                    for zi, wi in zip(z, weights):
                        Bs.append(gp['B_m']+Bnl+zi*gp['B_b'])
                        ws.append(float(gp['detw']*wi))
                        g0, g1 = gp['Gw']
                        geometry.append(np.asarray((np.outer(g0, g0), np.outer(g1, g1),
                            np.outer(g0, g1)+np.outer(g1, g0))))
                stress = np.asarray(state['layer_stress'])
                replay, Cp, ep, alpha = plane_stress_return_map(
                    np.asarray(state['layer_strain']).copy(), old['plastic_strain'].copy(),
                    old['alpha'].copy(), E, float(material.poisson_ratio),
                    material.hardening_curve, compute_tangent=tangent)
                kind = 'shell'
            elif isinstance(el, BeamElement):
                length, T0 = el._beam_frame_and_transform(el.get_node_coordinates(model.mesh))
                uloc = T0@ud
                config = el._fiber_plasticity_config(material)
                y, z, weights = el._fiber_section_grid(config)
                dv, dw = uloc[7]-uloc[1], uloc[8]-uloc[2]
                B = np.zeros((len(y), 1, 12))
                B[:, 0, 0], B[:, 0, 6] = -1/length, 1/length
                B[:, 0, 1], B[:, 0, 7] = -dv/length**2, dv/length**2
                B[:, 0, 2], B[:, 0, 8] = -dw/length**2, dw/length**2
                B[:, 0, 4], B[:, 0, 10] = -z/length, z/length
                B[:, 0, 5], B[:, 0, 11] = -y/length, y/length
                Bs, ws = list(B), list(length*weights)
                hess = np.zeros((1, 12, 12))
                for ai, bi in ((1, 7), (2, 8)):
                    hess[0, ai, ai] = hess[0, bi, bi] = 1/length**2
                    hess[0, ai, bi] = hess[0, bi, ai] = -1/length**2
                geometry = [hess]*len(y)
                stress = np.asarray(state['fiber_stress']).reshape(-1, 1)
                replay, Et, ep, alpha = el._uniaxial_return_map(
                    np.asarray(state['fiber_strain']).copy(), old, E,
                    config.material_curve, _beam_flow_scale(material, config.material_curve))
                replay = replay.reshape(-1, 1)
                Cp = Et.reshape(-1, 1, 1)
                kind = 'beam'
            else:
                raise ValueError('unsupported material-bearing element in diagnostic')
            stress_replay_error = max(stress_replay_error, float(np.max(abs(replay-stress))))
            history_replay &= np.array_equal(ep, state['plastic_strain']) and np.array_equal(alpha, state['alpha'])
            assert np.array_equal(replay, stress), 'canonical stress replay mismatch'
            assert history_replay, 'canonical history replay mismatch'
            source = stress.reshape(-1)/E
            dim = stress.size
            ti = source if t is None else t[offset:offset+dim]
            # This exact-zero representation preserves source force at local-row zero.
            delta = (E*(ti-source)).reshape(stress.shape)
            f_local = np.zeros(len(dofs))
            k_local = np.zeros((len(dofs), len(dofs))) if tangent else None
            wi_blocks, cp_blocks = [], []
            for point, (Bi, wi, geo) in enumerate(zip(Bs, ws, geometry)):
                f_local += wi*(Bi.T@delta[point])
                Bqi = Bi@T0@fixed
                wi_blocks.append(wi*Bqi.T*E)
                if tangent:
                    k_local += wi*(np.einsum('i,ijk->jk', delta[point], geo)-Bi.T@Cp[point]@Bi)
                    cp_blocks.append(Cp[point]@Bqi/E)
            f_ref = T0.T@f_local
            fp_delta[dofs] += Bco.T@f_ref
            if tangent:
                material_part, geometric_part = co._work_conjugate_corotational_tangent(
                    reference, el, deformed, rotations, Rrig, G, Bco,
                    f_ref, T0.T@k_local@T0)
                kp_delta[np.ix_(dofs, dofs)] += material_part+geometric_part
                constitutive_blocks.extend(cp_blocks)
            chunks.extend(wi_blocks)
            dimensions.append(dim)
            metadata.append(dict(element=int(eid), kind=kind, points=stress.shape[0], components=stress.shape[1], offset=offset, dimension=dim))
            t_source.append(source)
            modulus.extend([E]*dim)
            Bq_blocks.extend([Bi@T0@fixed for Bi in Bs])
            offset += dim
        if layout is None:
            layout = metadata
        assert metadata == layout
        ts = np.concatenate(t_source)
        t_eval = ts.copy() if t is None else t.copy()
        assert len(t_eval) == offset and np.all(np.isfinite(t_eval))
        rp = mapping.reduce_force(u, fi-Fc-lam*F)
        fc = fi+fp_delta
        re = mapping.reduce_force(u, fc-Fc-lam*F)
        control = float(row@u)
        local = t_eval-ts
        gc = 0. if target is None else (control-target)/control_scale
        residual = np.r_[re/work_scale, gc, local]
        matrix = None
        if tangent:
            kr = mapping.reduce_tangent(u, Kp+csr_matrix(kp_delta), fc-Fc-lam*F).toarray()
            cpq = np.vstack(constitutive_blocks)
            cross = np.column_stack(chunks)/work_scale
            g = np.asarray(row@J).reshape(-1)
            load_column = -mapping.reduce_force(u, F)/work_scale
            matrix = np.block([[kr/work_scale, load_column[:, None], cross],
                [g[None, :]/control_scale, np.zeros((1, 1+offset))],
                [-cpq, np.zeros((offset, 1)), np.eye(offset)]])
        reference_force = max(float(np.linalg.norm(mapping.reduce_force(u, Fc+max(abs(lam), 1.)*F))), 1.)
        value = dict(q=q.copy(), u=u.copy(), lam=float(lam), t=t_eval, ts=ts,
            trial=copy.deepcopy(dict(trial)), fi=fi.copy(), fc=fc, rp=rp, re=re,
            local=local, control=control, residual=residual, matrix=matrix,
            reference=reference_force, Bq=np.vstack(Bq_blocks), E=np.asarray(modulus),
            events=material_events(model, H, trial), stress_replay_error=stress_replay_error,
            history_replay=bool(history_replay))
        if cache_baseline is None:
            cache_baseline = cache_identity()
        assert cache_identity() == cache_baseline, 'reference/geometry cache mutation'
        assert identical(H, H_before) and np.array_equal(u, saved_u)
        return value

    def charged(A, rhs, label):
        nonlocal solves
        assert solves < 40
        solves += 1
        delta = np.linalg.solve(A, rhs)
        error = A@delta-rhs
        raw[label] = dict(matrix=A.copy(), rhs=rhs.copy(), delta=delta.copy(),
            error=error.copy(), global_solve=solves)
        log(dict(label=label, global_solve=solves, linear_error=float(np.linalg.norm(error))))
        return delta, error

    def physical_A(value):
        # Schur elimination at t=s_p/E must restore the actual production matrix.
        physical = value['matrix'][:n+1, :n+1].copy()
        physical[:, :n] += value['matrix'][:n+1, n+1:]@(-value['matrix'][n+1:, :n])
        return physical

    def envelope(value):
        upper = assemble(np.nextafter(value['q'], np.inf), value['lam'], tangent=False)
        lower = assemble(np.nextafter(value['q'], -np.inf), value['lam'], tangent=False)
        sums = 64*eps*np.asarray(abs(mapping.jacobian(value['u'])).T@(abs(value['fi'])+abs(Fc+value['lam']*F))).reshape(-1)
        return np.maximum.reduce((abs(upper['rp']-value['rp']), abs(lower['rp']-value['rp']), sums))

    def sensitivity(value, label):
        A = physical_A(value)
        delta, err = charged(A, np.r_[-value['rp']/work_scale, 0.], label)
        e = envelope(value)
        sigma = np.linalg.svd(A, compute_uv=False)[-1]
        radius = (np.linalg.norm(err)+np.linalg.norm(e)/work_scale+64*eps*np.linalg.norm(abs(A)@abs(delta)))/sigma
        return abs(delta[:n])+radius, dict(kind='local_linear_estimate_not_certified_nonlinear_enclosure',
            sigma_min=float(sigma), radius=float(radius), correction=delta.tolist(),
            force_envelope=float(np.linalg.norm(e))), e

    def converged(value, target):
        # Auxiliary strain consistency is roundoff-level, not an equilibrium tolerance.
        scale = abs(value['t'])+abs(value['ts'])+355e6/value['E']
        local_ok = np.all(abs(value['local']) <= 64*eps*scale)
        return bool(np.linalg.norm(value['rp']) <= 1e-8*value['reference']
            and np.linalg.norm(value['re']) <= 1e-8*value['reference']
            and abs(value['control']-target) <= 2e-9 and local_ok)

    def correct(label, target, q, lam, t, cap):
        value = assemble(q, lam, t, target, True)
        raw[label+'-initial'] = value
        while True:
            log(dict(label=label, global_solves=solves, production_R=float(np.linalg.norm(value['rp'])),
                extended_R=float(np.linalg.norm(value['re'])), constitutive_force=float(np.linalg.norm(value['re']-value['rp'])),
                local_strain=float(np.linalg.norm(value['local'])), control=value['control'], target=target,
                lam=value['lam'], merit=float(.5*np.dot(value['residual'], value['residual']))))
            raw[label+'-pending'] = value
            (out/(label+'-pending.pkl')).write_bytes(pickle.dumps(value))
            (out/(label+'-iterate-'+str(solves).zfill(4)+'.pkl')).write_bytes(pickle.dumps(value))
            if converged(value, target):
                return value, 'actual_equilibrium_and_local_consistency'
            if solves >= cap:
                return value, 'global_solve_budget'
            step, error = charged(value['matrix'], -value['residual'], label+'-solve-'+str(solves+1))
            phi = .5*np.dot(value['residual'], value['residual'])
            accepted = None
            for search in range(8):
                alpha = 2.**(-search)
                try:
                    candidate = assemble(value['q']+alpha*step[:n], value['lam']+alpha*step[n],
                        value['t']+alpha*step[n+1:], target, False)
                except SO3MeanDomainError as exc:
                    log(dict(label=label+'-trial', alpha=alpha, refusal=str(exc)))
                    continue
                phit = .5*np.dot(candidate['residual'], candidate['residual'])
                finite = np.isfinite(phit) and np.all(np.isfinite(candidate['rp']))
                log(dict(label=label+'-trial', alpha=alpha, merit=float(phit), finite=bool(finite),
                    production_R=float(np.linalg.norm(candidate['rp'])), control=candidate['control']))
                if finite and phit <= (1-1e-4*alpha)*phi:
                    accepted = candidate
                    break
            if accepted is None:
                return value, 'bounded_extended_merit_no_improvement'
            value = assemble(accepted['q'], accepted['lam'], accepted['t'], target, True)

    def save(report):
        assert pickle.dumps((capture, cur)) == original_inputs
        assert identical(H, H_before) and cache_identity() == cache_baseline
        report.update(global_solves=solves, evaluations=evaluations, caller_inputs_unchanged=True,
            reference_geometry_caches_unchanged=True, elapsed=time.perf_counter()-started,
            stress_layout=layout, no_material_or_class_patch=True, production_integrated=False)
        (out/'raw.pkl').write_bytes(pickle.dumps(raw))
        (out/'result.json').write_text(json.dumps(report, indent=2, default=serial))
        print(json.dumps({k: v for k, v in report.items() if not isinstance(v, (dict, list, np.ndarray))}, default=serial))

    def production_confirmation(value, target):
        """Normal public boundary, valid accepted input, private uncommitted seed."""
        nonlocal solves
        changes = []
        tree = ast.parse(inspect.getsource(ns._solve_static_displacement_control))
        class Specialize(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                if node.name == '_solve_static_displacement_control':
                    node.name = '_coupled_entry_confirmation'
                return self.generic_visit(node)
            def visit_Assign(self, node):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                for key, setting in (('target_scale', .2), ('max_control_cutbacks', 0)):
                    if key in names:
                        node.value = ast.Constant(setting)
                        changes.append(dict(name=key, value=setting))
                if names == ['states_new'] and isinstance(node.value, ast.Name) and node.value.id == 'committed_states':
                    changes.append(dict(name='uncommitted_seed_after_accepted_origin', value=True))
                    return [node, *ast.parse('assert T.shape == _diagnostic_T.shape and (T != _diagnostic_T).nnz == 0\nq = _diagnostic_q.copy()\nlam = _diagnostic_lam').body]
                return self.generic_visit(node)
        tree = ast.fix_missing_locations(Specialize().visit(tree))
        (out/'guarded-confirmation.py').write_text(ast.unparse(tree))
        scope = dict(ns.__dict__)
        real_factorize = ns.factorize
        scope.update(_diagnostic_q=value['q'].copy(), _diagnostic_lam=value['lam'], _diagnostic_T=T)
        def factorize(matrix, *args, **kwargs):
            handle = real_factorize(matrix, *args, **kwargs)
            class Handle:
                def __getattr__(self, key):
                    return getattr(handle, key)
                def solve(self, rhs):
                    nonlocal solves
                    assert solves < 40
                    solves += 1
                    delta = handle.solve(rhs)
                    raw['production-confirmation-solve-'+str(solves)] = dict(
                        matrix=matrix.copy(), rhs=np.asarray(rhs).copy(), delta=np.asarray(delta).copy())
                    log(dict(label='production-confirmation', global_solve=solves))
                    return delta
            return Handle()
        scope['factorize'] = factorize
        exec(compile(tree, str(out/'guarded-confirmation.py'), 'exec'), scope)
        original = ns._solve_static_displacement_control
        try:
            ns._solve_static_displacement_control = scope['_coupled_entry_confirmation']
            result = solve_static_nonlinear(model, load, control='displacement',
                displacement_control=DisplacementControl(node_id=probe, dof='uz', target_displacement=target),
                kinematics='corotational', corotational_tangent='work_conjugate', num_steps=1,
                max_iterations=40-solves, tolerance=1e-8, initial_displacements=cur['displacements'].copy(),
                initial_element_states=copy.deepcopy(H), equilibrate_initial_state=False,
                emit_restart_checkpoint=False, record_increment_snapshots=True)
        finally:
            ns._solve_static_displacement_control = original
        assert ns._solve_static_displacement_control is original
        raw['production-confirmation-result'] = dict(u=result.displacements.copy(),
            H=copy.deepcopy(dict(result.element_states)), lam=result.load_factor,
            status=result.status, reason=result.stop_reason, info=dict(result.info),
            snapshots=copy.deepcopy(result.snapshots), kernel_changes=changes)
        return result

    base = assemble(qc, lamc, target=float(row@cur['displacements']))
    raw['base'] = base
    # Exact source equivalence and Schur closure are checked BEFORE any candidate solve.
    actual_kr = mapping.reduce_tangent(base['u'], ns._assemble_nonlinear_system(model,
        base['u'].copy(), copy.deepcopy(H), 5, tangent=True, kinematics='corotational',
        corotational_tangent='work_conjugate')[1], base['fi']-Fc-lamc*F).toarray()
    closure = physical_A(base)[:n, :n]-actual_kr/work_scale
    closure_error = float(np.linalg.norm(closure)/max(np.linalg.norm(actual_kr/work_scale), 1e-30))
    force_closure = float(np.linalg.norm(base['re']-base['rp']))
    report = dict(diagnostic_only=True, original_target_acceptance=False,
        source_force_closure=force_closure, schur_tangent_relative_closure=closure_error,
        residual_definition='[re/4000, (c-target)/0.2, t-s_production/E]',
        derivative_status='modified Newton of stopped canonical map')
    if force_closure != 0. or closure_error > 1e-12:
        report.update(outcome='source_equivalence_failure')
        save(report)
        return
    # Structural rows at fixed independent stresses are smooth even when a
    # source return-map branch changes and cancels between the two force terms.
    # One predetermined fourth-order stencil; no fitted step/scale search.
    direction = np.r_[np.sin(np.arange(n)+1.), .1, np.cos(np.arange(len(base['ts']))+1.)]
    h = eps**.2
    points = [assemble(qc+m*h*direction[:n], lamc+m*h*direction[n],
        base['ts']+m*h*direction[n+1:], base['control'], False)['residual'][:n+1]
        for m in (2., 1., -1., -2.)]
    finite = (-points[0]+8*points[1]-8*points[2]+points[3])/(12*h)
    predicted = base['matrix'][:n+1]@direction
    extended_derivative_error = float(np.linalg.norm(finite-predicted)/np.linalg.norm(predicted))
    raw['independent-stress-structural-derivative'] = dict(step=h, direction=direction,
        finite=finite, predicted=predicted, relative_error=extended_derivative_error)
    report['independent_stress_structural_derivative_relative_error'] = extended_derivative_error
    if extended_derivative_error > 1e-7:
        report.update(outcome='independent_stress_structural_derivative_not_verified')
        save(report)
        return
    qbase_unc, base_unc, base_env = sensitivity(base, 'base-equilibrium-defect')
    raw['base-uncertainty'] = base_unc
    pre = material_observer(model, mapping, base['u'], H, base['trial'], qbase_unc)
    raw['base-observer'] = pre
    radius = max(2e-9, 1e-8, 64*abs(np.spacing(base['control'])))
    target = base['control']-4*radius
    post, status = correct('post-entry', target, qc, lamc, base['ts'], 38)
    report.update(post_status=status, post_production_R=float(np.linalg.norm(post['rp'])),
        post_relative_R=float(np.linalg.norm(post['rp'])/post['reference']),
        post_extended_R=float(np.linalg.norm(post['re'])), post_control=post['control'],
        diagnostic_target=target, base_uncertainty=base_unc)
    if status != 'actual_equilibrium_and_local_consistency':
        report.update(outcome='actual_post_entry_coupled_corrector_not_completed', post_entry_oracles_executed=False)
        save(report)
        return
    # Rebuild source-consistent stress state for the independent physical admission.
    source_post = assemble(post['q'], post['lam'], target=target, tangent=True)
    qpost_unc, post_unc, post_env = sensitivity(source_post, 'post-equilibrium-defect')
    obs = material_observer(model, mapping, source_post['u'], H, source_post['trial'], qpost_unc)
    raw['post-observer'] = obs
    signal = float(np.linalg.norm(obs['correction']))
    force_error = max(1e-8*post['reference'], float(np.linalg.norm(base_env)),
        float(np.linalg.norm(post_env)), float(np.linalg.norm(base['rp'])))
    positive, unresolved = [], []
    for old, witness in zip(pre['witnesses'], obs['witnesses']):
        au = 64*(abs(np.spacing(witness['alpha']))+abs(np.spacing(witness['alpha_old'])))
        if witness['alpha']-witness['alpha_old'] > au and witness['plastic_change'] > witness['plastic_ulp']:
            advance = float(np.max(abs(witness['strain']-old['strain'])))
            uncertainty = float(np.max(witness['strain_uncertainty']+old['strain_uncertainty']))
            item = dict(element=witness['element'], point=witness['point'], kind=witness['kind'],
                strain_advance=advance, strain_uncertainty=uncertainty, loading=witness['loading'],
                loading_uncertainty=witness['loading_uncertainty'], consistency=witness['consistency'])
            positive.append(item)
            if witness['loading'] <= witness['loading_uncertainty']+64*eps or advance <= 2*uncertainty or witness['consistency'] > witness['consistency_tolerance']:
                unresolved.append(item)
    case = dict(model=model, load=load, probe=probe, grid=grid, coupling='direct',
        result=SimpleNamespace(displacements=post['u'], load_factor=post['lam'], element_states=post['trial']))
    frozen_eq = _independent_equilibrium(case, displacements=post['u'], load_factor=post['lam'], element_states=H)
    returned_eq = _independent_equilibrium(case)
    constraints = constraint_residual_summary(model, mapping.to_linear_displacement(post['u']))
    wrench = lambda eq: np.linalg.norm(eq['balance']) <= 1e-6*max(np.linalg.norm(eq['applied_wrench']), 1e-30)
    direction = post['q']-qc
    dnorm = float(np.linalg.norm(direction, np.inf))
    strain_error = float('inf')
    if dnorm:
        h = eps**.2*max(1., float(np.linalg.norm(post['q'], np.inf)))/dnorm
        values = [assemble(post['q']+m*h*direction, post['lam'], tangent=False)['events'].strains
                  for m in (2., 1., -1., -2.)]
        finite = (-values[0]+8*values[1]-8*values[2]+values[3])/(12*h)
        exact = obs['strain_jacobian']@direction
        strain_error = float(np.linalg.norm(finite-exact)/max(np.linalg.norm(exact), np.finfo(float).tiny))
        raw['smooth-kinematic-strain-check'] = dict(step=h, finite=finite, predicted=exact, relative_error=strain_error)
    resolved = bool(base['control']-post['control'] > 2*radius
        and dnorm > 2*np.max(qbase_unc+qpost_unc) and signal > 2*force_error
        and np.linalg.norm(post['rp']) <= min(1e-8*post['reference'], signal/2)
        and positive and not unresolved and obs['stress_identity_pass']
        and obs['projected_stress_identity_error'] < force_error and strain_error <= 1e-7
        and frozen_eq['relative_residual'] <= 1e-7 and returned_eq['relative_residual'] <= 1e-7
        and wrench(frozen_eq) and wrench(returned_eq) and constraints['status'] == 'passed')
    report.update(outcome='resolved_actual_post_entry_equilibrium' if resolved else 'unresolved_actual_post_entry_signal_or_error',
        post_entry_oracles_executed=True, actual_advance=base['control']-post['control'],
        q_advance=dnorm, q_uncertainty=float(np.max(qbase_unc+qpost_unc)), post_uncertainty=post_unc,
        plastic_force_signal=signal, force_error_radius=force_error, positive_returned_points=positive,
        unresolved_returned_points=unresolved, frozen_relative_residual=frozen_eq['relative_residual'],
        returned_relative_residual=returned_eq['relative_residual'], frozen_wrench_pass=bool(wrench(frozen_eq)),
        returned_wrench_pass=bool(wrench(returned_eq)), constraints=constraints,
        strain_jacobian_relative_error=strain_error, stress_identity_pass=obs['stress_identity_pass'])
    if resolved:
        # Same frozen H11 and the SAME shared40; this private seed is never a restart.
        final, final_status = correct('original-first-target', float(capture['target']),
            post['q'], post['lam'], post['t'], 39)
        report.update(first_target_status=final_status, first_target_production_R=float(np.linalg.norm(final['rp'])),
            first_target_relative_R=float(np.linalg.norm(final['rp'])/final['reference']),
            first_target_control=final['control'], original_target_acceptance=False)
        if final_status == 'actual_equilibrium_and_local_consistency':
            confirmed = production_confirmation(final, float(capture['target']))
            case['result'] = confirmed
            eq_returned = _independent_equilibrium(case)
            eq_frozen = _independent_equilibrium(case, element_states=H)
            con = constraint_residual_summary(model, mapping.to_linear_displacement(confirmed.displacements))
            final_control = float(row@confirmed.displacements)
            confirmed_q = ns._reduced_coordinates(T, u0, mapping.to_linear_displacement(confirmed.displacements))
            physical = assemble(confirmed_q, float(confirmed.load_factor), target=float(capture['target']), tangent=False)
            accepted = bool(confirmed.status == 'completed'
                and abs(final_control-float(capture['target'])) <= 2e-9
                and np.linalg.norm(physical['rp']) <= 1e-8*physical['reference']
                and eq_frozen['relative_residual'] <= 1e-7 and eq_returned['relative_residual'] <= 1e-7
                and wrench(eq_frozen) and wrench(eq_returned) and con['status'] == 'passed')
            report.update(outcome='original_first_target_confirmed' if accepted else 'original_first_target_confirmation_failed',
                original_target_acceptance=accepted, confirmation_status=confirmed.status,
                confirmation_reason=confirmed.stop_reason, confirmation_control=final_control,
                confirmation_frozen_relative_R=eq_frozen['relative_residual'],
                confirmation_returned_relative_R=eq_returned['relative_residual'], confirmation_constraints=con,
                confirmation_frozen_wrench_pass=bool(wrench(eq_frozen)),
                confirmation_returned_wrench_pass=bool(wrench(eq_returned)))
    save(report)


if __name__ == '__main__':
    main()
