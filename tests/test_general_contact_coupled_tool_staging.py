"""Coupled tool seeds: independent response/work and whole-path safeguards."""
from dataclasses import replace
import json, os, time
from pathlib import Path
import numpy as np
import pytest
from anysolver import solve_static_nonlinear, validate_general_contact
from anysolver.general_contact.beam_hemisphere_coupled_tool import CoupledHemisphereToolManager, PROFILE
from test_general_contact_hemisphere_cylinder_motion import fixture, reference


def coupled_fixture(quadratic=False, **kwargs):
    model, definition, settings, load = fixture(quadratic, **kwargs)
    return model, definition, replace(settings, beam_end_cap_work='hemisphere_coupled_tool_dev'), load


def test_active_origin_restores_factor_and_hidden_crossing():
    model, definition, settings, _ = coupled_fixture()
    manager = CoupledHemisphereToolManager(model, definition, settings)
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    manager.set_path_factor(.3)
    assert not manager.coupled_load_seed_active_origin(u, .25)
    assert manager.path_factor == .3
    solved, *_ = reference(False, .75)
    for i, node in enumerate(sorted(model.mesh.nodes)):
        u[model.mesh.dof_manager.get_node_dofs(node)[0]] = solved[i]
    assert manager.coupled_load_seed_active_origin(u, .75)
    assert manager.path_factor == .3
    crossed = replace(definition, rigid_bodies=(replace(definition.rigid_bodies[0], path_translation=(.624,0.,0.)),))
    crossing = CoupledHemisphereToolManager(model, crossed, settings)
    assert not crossing.swept_increment_admissible(u, u, 0., 1.)
    assert crossing.path_factor == 0.
    assert validate_general_contact(model, definition, settings).profile == PROFILE
    assert not validate_general_contact(model, definition, settings, analysis_control='displacement').valid


@pytest.mark.parametrize('quadratic', (False, True))
def test_coupled_tool_independent_response_work_and_state_count(quadratic):
    model, definition, settings, load = coupled_fixture(quadratic)
    started = time.perf_counter()
    result = solve_static_nonlinear(model, load, contact=definition, contact_settings=settings,
        num_steps=4, max_iterations=20, tolerance=1e-10, emit_restart_checkpoint=True)
    elapsed = time.perf_counter()-started
    assert result.status == 'completed', result.failure_reason
    u, force, storage, reaction = reference(quadratic, 1.)
    dofs = [model.mesh.dof_manager.get_node_dofs(n)[0] for n in sorted(model.mesh.nodes)]
    np.testing.assert_allclose(result.displacements[dofs], u, rtol=1e-6, atol=1e-10)
    info = result.info['general_contact']
    assert info['profile'] == PROFILE and info['gap_tolerance_met']
    np.testing.assert_allclose(info['rigid_force'], (-force,0.,0.), rtol=1e-6, atol=1e-10)
    assert result.steps[-1].support_reactions['root'][0] == pytest.approx(reaction,rel=1e-6,abs=1e-10)
    previous = previous_force = work = 0.
    history = result.info['force_displacement_history']
    for step in history:
        factor = step['load_factor']; _, f, _, _ = reference(quadratic, factor)
        work += .5*(previous_force+f)*.004*(factor-previous)
        previous, previous_force = factor, f
    assert info['prescribed_actuator_work_trapezoid'] == pytest.approx(work,rel=1e-6,abs=1e-12)
    assert work == pytest.approx(storage,rel=2e-4,abs=1e-12)
    assert len(history) < 284  # Same four-target fixture, measured historical baseline.
    path = os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:
        Path(path).with_name('coupled_B'+('3' if quadratic else '2')+'.json').write_text(json.dumps({
            'elapsed_s':elapsed,'states':len(history),'info':info,'history':history,
            'independent_storage_J':storage,'independent_work_J':work},indent=2))


@pytest.mark.parametrize('factor', (.25, .75))
def test_open_active_restart_and_incompatible_algorithm(factor):
    model, definition, settings, load = coupled_fixture()
    common = dict(contact=definition, contact_settings=settings, max_iterations=20,
                  tolerance=1e-10, emit_restart_checkpoint=True)
    prefix = solve_static_nonlinear(model, load, **common, num_steps=2, max_load_factor=factor)
    assert prefix.status == 'completed', prefix.failure_reason
    checkpoint = json.loads(json.dumps(prefix.to_restart_checkpoint(), allow_nan=False))
    fresh, _, _, _ = coupled_fixture()
    resumed = solve_static_nonlinear(fresh, load, **common, num_steps=2, restart_checkpoint=checkpoint)
    assert resumed.status == 'completed', resumed.failure_reason
    expected, *_ = reference(False, 1.)
    dofs = [fresh.mesh.dof_manager.get_node_dofs(n)[0] for n in sorted(fresh.mesh.nodes)]
    np.testing.assert_allclose(resumed.displacements[dofs], expected, rtol=1e-6, atol=1e-10)
    with pytest.raises(ValueError, match='restart|contract|incompatible'):
        solve_static_nonlinear(fresh, load, **{**common, 'contact_settings':replace(settings,
            beam_end_cap_work='hemisphere_support_dev')}, num_steps=2, restart_checkpoint=checkpoint)


@pytest.mark.parametrize('cancel', (False, True))
def test_seed_interruption_replays_fresh(cancel, monkeypatch):
    from anysolver import CancellationToken, SolveCancelled
    model, definition, settings, load = coupled_fixture()
    common = dict(contact=definition, contact_settings=settings, num_steps=4,
                  max_iterations=20, tolerance=1e-10)
    token = CancellationToken(); armed = [False]; raised = [False]
    original = CoupledHemisphereToolManager.evaluate
    def callback(event):
        if event.event_type == 'nonlinear_static_step' and event.metadata['load_factor'] >= .75:
            if cancel: token.cancel('owned coupled seed stop')
            else: armed[0] = True
    def fail(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if armed[0] and not raised[0]:
            raised[0] = True
            raise RuntimeError('owned coupled seed stop')
        return result
    with monkeypatch.context() as patch:
        if not cancel: patch.setattr(CoupledHemisphereToolManager, 'evaluate', fail)
        with pytest.raises(SolveCancelled if cancel else RuntimeError,match='owned coupled seed stop'):
            solve_static_nonlinear(model, load, **common, progress_callback=callback,cancellation_token=token)
    assert raised[0] or token.is_cancelled
    replay = solve_static_nonlinear(model, load, **common)
    fresh, _, _, _ = coupled_fixture()
    clean = solve_static_nonlinear(fresh, load, **common)
    assert replay.status == clean.status == 'completed'
    np.testing.assert_array_equal(replay.displacements, clean.displacements)


def test_origin_query_exception_restores_factor(monkeypatch):
    model, definition, settings, _ = coupled_fixture()
    manager = CoupledHemisphereToolManager(model, definition, settings)
    manager.set_path_factor(.3)
    def fail(*args, **kwargs): raise RuntimeError('origin query failure')
    monkeypatch.setattr(manager, 'evaluate', fail)
    with pytest.raises(RuntimeError, match='origin query failure'):
        manager.coupled_load_seed_active_origin(np.zeros(model.mesh.dof_manager.total_dofs), .75)
    assert manager.path_factor == .3


def test_certification_failure_never_accepts_seed(monkeypatch):
    model, definition, settings, load = coupled_fixture()
    queried = []
    original = CoupledHemisphereToolManager.coupled_load_seed_active_origin
    def origin(self, u, factor):
        active = original(self, u, factor)
        queried.append(active)
        return active
    swept = CoupledHemisphereToolManager.swept_increment_admissible
    def reject(self, start, end, first, last):
        if last > .75: return False
        return swept(self, start, end, first, last)
    monkeypatch.setattr(CoupledHemisphereToolManager, 'coupled_load_seed_active_origin', origin)
    monkeypatch.setattr(CoupledHemisphereToolManager, 'swept_increment_admissible', reject)
    result = solve_static_nonlinear(model, load, contact=definition, contact_settings=settings,
        num_steps=4, max_iterations=20, tolerance=1e-10)
    assert result.status != 'completed'
    assert result.failure_reason == 'contact_gap_exceeded'
    assert any(queried)
    assert max(row['load_factor'] for row in result.info['force_displacement_history']) <= .75


@pytest.mark.parametrize('quadratic', (False, True))
def test_balanced_complete_route_comparison(quadratic):
    rows = []; solutions = []
    for coupled in (False, True, True, False):
        model, definition, settings, load = coupled_fixture(quadratic) if coupled else fixture(quadratic)
        started = time.perf_counter()
        result = solve_static_nonlinear(model, load, contact=definition, contact_settings=settings,
            num_steps=4, max_iterations=20, tolerance=1e-10)
        elapsed = time.perf_counter()-started
        assert result.status == 'completed', result.failure_reason
        rows.append(dict(coupled=coupled,elapsed_s=elapsed,
            states=len(result.info['force_displacement_history']),
            newton_iterations=result.info['total_newton_iterations']))
        solutions.append(result.displacements)
    for solution in solutions[1:]:
        np.testing.assert_allclose(solution, solutions[0], rtol=1e-6, atol=1e-10)
    record = os.environ.get('CONTACT_APP_RESULT_RECORD')
    if record:
        Path(record).with_name('paired_B'+('3' if quadratic else '2')+'.json').write_text(json.dumps(rows,indent=2))


def test_iteration_callback_exception_restores_committed_tool_pose():
    from anysolver.general_contact.runtime import active_contact_manager
    model, definition, settings, load = coupled_fixture()
    last = [0.]; captured = []
    def progress(event):
        if event.event_type == 'nonlinear_static_step': last[0] = event.metadata['load_factor']
    def status(message):
        if last[0] >= .6:
            captured.append(active_contact_manager())
            raise RuntimeError('seed iteration observer failure')
    with pytest.raises(RuntimeError,match='seed iteration observer failure'):
        solve_static_nonlinear(model, load, contact=definition, contact_settings=settings,
            num_steps=4, max_iterations=20, tolerance=1e-10,
            progress_callback=progress,status_callback=status)
    assert captured and captured[0].path_factor == last[0]


@pytest.mark.parametrize('nonfinite', (False,True))
def test_failed_seed_linear_system_cannot_commit(nonfinite, monkeypatch):
    import anysolver.nonlinear_static as driver
    from types import SimpleNamespace
    model, definition, settings, load = coupled_fixture()
    origin = CoupledHemisphereToolManager.coupled_load_seed_active_origin
    real_factorize = driver.factorize
    active_factors = []; failed = []
    def query(self, u, factor):
        active = origin(self,u,factor)
        if active: active_factors.append(factor)
        return active
    def fail(K, *args, **kwargs):
        if active_factors:
            failed.append(True)
            return SimpleNamespace(status='ok' if nonfinite else 'failed',
                backend_name='injected',failure_reason='controlled singular seed',
                solve=lambda residual:np.full_like(residual,np.nan))
        return real_factorize(K,*args,**kwargs)
    monkeypatch.setattr(CoupledHemisphereToolManager,'coupled_load_seed_active_origin',query)
    monkeypatch.setattr(driver,'factorize',fail)
    result = solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
        num_steps=4,max_iterations=20,tolerance=1e-10)
    assert failed and result.status != 'completed'
    assert max(row['load_factor'] for row in result.info['force_displacement_history']) <= max(active_factors)



def test_seed_force_pose_requires_exterior_centreline():
    model, definition, settings, _ = coupled_fixture(motion=(.2,0.,0.))
    manager = CoupledHemisphereToolManager(model, definition, settings)
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    manager.set_path_factor(.3)
    assert manager.coupled_load_seed_pose_admissible(u, .01)
    assert not manager.coupled_load_seed_pose_admissible(u, .5)
    assert manager.path_factor == .3


def test_precommit_tool_work_exception_restores_origin(monkeypatch):
    model, definition, settings, load = coupled_fixture()
    original = CoupledHemisphereToolManager.tool_work_increment
    captured = []; factors = []
    def fail(self, start, end, first, last):
        if first >= .6:
            captured.append(self); factors.append(first)
            raise RuntimeError('coupled precommit work failure')
        return original(self,start,end,first,last)
    monkeypatch.setattr(CoupledHemisphereToolManager,'tool_work_increment',fail)
    with pytest.raises(RuntimeError,match='coupled precommit work failure'):
        solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
            num_steps=4,max_iterations=20,tolerance=1e-10)
    assert captured and captured[0].path_factor == factors[0]



@pytest.mark.parametrize('policy', ('always','armijo'))
def test_coupled_seed_preserves_globalization_and_rejected_paths(policy, monkeypatch):
    model, definition, settings, load = coupled_fixture()
    original = CoupledHemisphereToolManager.swept_increment_admissible
    rejected = []
    def sweep(self, start, end, first, last):
        # Reject one full physical-origin/seed proposal; the outer driver must
        # cut back, not let line search or another route bypass this certificate.
        if (first > .6 and last > first and not rejected
                and np.linalg.norm(end-start) > 1e-5):
            rejected.append((first,last))
            return False
        return original(self,start,end,first,last)
    monkeypatch.setattr(CoupledHemisphereToolManager,'swept_increment_admissible',sweep)
    result = solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
        num_steps=4,max_iterations=20,tolerance=1e-10,convergence_settings={'line_search':policy})
    assert rejected and result.status == 'completed', result.failure_reason
    expected, *_ = reference(False,1.)
    dofs=[model.mesh.dof_manager.get_node_dofs(n)[0] for n in sorted(model.mesh.nodes)]
    np.testing.assert_allclose(result.displacements[dofs],expected,rtol=1e-6,atol=1e-10)


def test_seed_counts_inside_existing_iteration_limit(monkeypatch):
    model, definition, settings, load = coupled_fixture()
    query = CoupledHemisphereToolManager.coupled_load_seed_active_origin
    active = []
    def observed(self,u,factor):
        value=query(self,u,factor)
        if value: active.append(factor)
        return value
    monkeypatch.setattr(CoupledHemisphereToolManager,'coupled_load_seed_active_origin',observed)
    result=solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
        num_steps=4,max_iterations=3,tolerance=1e-10)
    assert active, 'fixture must actually enter the active-origin seed route'
    assert result.info['convergence_adaptation']
    assert all(row['iterations']<=3 for row in result.info['convergence_adaptation'])


def test_seed_pose_respects_both_exterior_radius_domains():
    model,definition,settings,_=coupled_fixture(motion=(.124,0.,0.))
    definition=replace(definition,
        surfaces=(replace(definition.surfaces[0],beam_radius=.1),),
        rigid_bodies=(replace(definition.rigid_bodies[0],radius=.01),))
    manager=CoupledHemisphereToolManager(model,definition,settings)
    u=np.zeros(model.mesh.dof_manager.total_dofs)
    # Endpoint rho=.05 exceeds obstacle radius .01 but lies inside beam radius .1.
    assert not manager.coupled_load_seed_pose_admissible(u,.5)
    assert manager.path_factor==0.



@pytest.mark.parametrize('policy', ('always','armijo'))
def test_backtracked_seed_scale_is_certified_before_evaluation(policy,monkeypatch):
    model,definition,settings,load=coupled_fixture()
    query=CoupledHemisphereToolManager.coupled_load_seed_active_origin
    evaluate=CoupledHemisphereToolManager.evaluate
    swept=CoupledHemisphereToolManager.swept_increment_admissible
    injected=[False];rejected_scaled=[];injection=[]
    def active(self,u,factor):
        return query(self,u,factor)
    def force(self,u,**kwargs):
        import inspect
        result=evaluate(self,u,**kwargs)
        if not injected[0]:
            frame=inspect.currentframe().f_back
            while frame is not None and frame.f_code.co_name != '_newton_increment':
                frame=frame.f_back
            # Fault only the full line-search seed candidate, never an origin
            # query, initial linearization, path query or tool-work evaluation.
            if (frame is not None and frame.f_locals.get('coupled_seed_iteration')
                    and frame.f_locals.get('trial') == 0
                    and np.linalg.norm(u-frame.f_locals['origin_u']) > 4e-5):
                f,K,r=result;f=f.copy()
                f[model.mesh.dof_manager.get_node_dofs(1)[0]]+=1e10
                injected[0]=True
                injection.append({k:frame.f_locals.get(k) for k in ('line_search_mode','iteration','trial','coupled_seed_iteration','residual_norm')})
                return f,K,r
        return result
    def certificate(self,start,end,first,last):
        valid=swept(self,start,end,first,last)
        if injected[0] and not valid and np.linalg.norm(end-start)>0.:
            rejected_scaled.append((first,last))
        return valid
    monkeypatch.setattr(CoupledHemisphereToolManager,'coupled_load_seed_active_origin',active)
    monkeypatch.setattr(CoupledHemisphereToolManager,'evaluate',force)
    monkeypatch.setattr(CoupledHemisphereToolManager,'swept_increment_admissible',certificate)
    result=solve_static_nonlinear(model,load,contact=definition,contact_settings=settings,
        num_steps=4,max_iterations=20,tolerance=1e-10,convergence_settings={'line_search':policy})
    assert injected[0] and rejected_scaled and result.status=='completed',injection
    expected,*_=reference(False,1.)
    dofs=[model.mesh.dof_manager.get_node_dofs(n)[0] for n in sorted(model.mesh.nodes)]
    np.testing.assert_allclose(result.displacements[dofs],expected,rtol=1e-6,atol=1e-10)



def test_existing_public_example_explicit_seed_option():
    from examples.general_contact_hemisphere_cylinder_motion import run
    result=run(coupled_load_seed=True)
    assert result.status=='completed' and result.info['general_contact']['profile']==PROFILE
    assert len(result.info['force_displacement_history'])==16
