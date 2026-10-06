from pathlib import Path
import json, os, sys
import numpy, scipy, numba, llvmlite, psutil, anysolver, pytest
from threadpoolctl import threadpool_info
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
phase = os.environ['MATERIAL_PHASE']
CI = ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
dependencies = {m.__name__:dict(path=str(Path(m.__file__).resolve()), version=m.__version__)
                for m in (numpy, scipy, numba, llvmlite)}
(ROOT/('dependency-preflight-'+phase+'.json')).write_text(json.dumps(dependencies, indent=2))
for module, version in ((numpy, '2.5.3'), (scipy, '1.18.1'), (numba, '0.68.0'), (llvmlite, '0.50.0')):
    assert module.__version__ == version and Path(module.__file__).resolve().is_relative_to(CI.resolve()), dependencies
expected_solver = (ROOT/'installed-wheel-v1') if phase=='installed-partial-v1' else REPO/'src'
assert Path(anysolver.__file__).resolve().is_relative_to(expected_solver.resolve())
assert len(psutil.Process().cpu_affinity()) == 1
assert numba.config.DISABLE_JIT and numba.get_num_threads() == 1
assert all(p['num_threads'] == 1 for p in threadpool_info())
if phase=='installed-partial-v1':
    from examples.stiffened_shell_native_fibre_bl5_material import workflow
    result=workflow()
    modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
        if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)}
    assert all(Path(p).is_relative_to(expected_solver.resolve()) for p in modules.values())
    assert all(p['num_threads']==1 for p in threadpool_info())
    assert result['fibre_alpha_max']>0. and result['shell_alpha_max']==0.
    (ROOT/('result-'+phase+'.json')).write_text(json.dumps(result,indent=2))
    (ROOT/('runtime-'+phase+'.json')).write_text(json.dumps(dict(dependencies=dependencies,
        imports=modules,pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT)),indent=2))
    print(json.dumps(result))
    sys.exit(0)
if phase=='pending-comparison-v1':
    import pending_comparison
    result=pending_comparison.execute(ROOT)
    (ROOT/('runtime-'+phase+'.json')).write_text(json.dumps(dict(dependencies=dependencies,
        imports={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
            if (n=='anysolver' or n.startswith('anysolver.')) and getattr(m,'__file__',None)},
        pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT)),indent=2))
    print(json.dumps(dict(type=result['type'],accepted=len(result['observed']),checkpoint_unchanged=result['checkpoint_unchanged'])))
    sys.exit(0)
if phase=='rejected-trial-v1':
    import rejected_trial_probe
    result=rejected_trial_probe.execute(ROOT)
    print(json.dumps(dict(outcome=result['type'],evaluations=result['evaluations'],linear_relative=result.get('linear_weighted_relative'),
        derivative_errors=[dict(direction=r['direction'],errors=[x['relative'] for x in r['steps']]) for r in result.get('derivatives',())])))
    sys.exit(0)
if phase == 'axial-diagnostic-v1':
    from dataclasses import replace, asdict
    from anymaterial import DNVC208MaterialCurve
    from anysolver import stiffened_shell as ss
    from examples.stiffened_shell_native_fibre_bl5_material import definition, CONTROLS
    model = definition()
    curve = DNVC208MaterialCurve(1e5, 2e5, 3e5, .00001, .00002, 4e5, .002)
    model = replace(model, shell=replace(model.shell, j2_curve=curve))
    owner = ss.create_analysis(definition=model)
    observed = []
    try:
        actions = (ss.NodalAction('beam', 105, (5000., 0., 0., 0., 0., 0.)),)
        result = owner.solve(actions, (.1, .5, 1.), on_accepted=lambda r:observed.append(dict(factor=r.load_factor,
            shell=numpy.asarray(r.shell_layer_alpha).tolist(), beams=numpy.asarray(r.beam_station_accumulated).tolist())), **CONTROLS)
        (ROOT/'axial-result-v1.json').write_text(json.dumps(dict(status=result.status, observed=observed,
            equilibrium=result.free_equilibrium_ratio, gap=result.constraint_max), indent=2))
        (ROOT/'axial-prefix-v1.bin').write_bytes(owner.checkpoint())
    except BaseException as error:
        (ROOT/'axial-failure-v1.json').write_text(json.dumps(dict(type=type(error).__name__, message=str(error), observed=observed,
            attempts=[asdict(a) for a in getattr(error, 'attempts', ())]), indent=2))
        if owner._finite_driver is not None:
            (ROOT/'axial-failed-prefix-v1.bin').write_bytes(owner.checkpoint())
        raise
    finally:
        owner.close()
    sys.exit(0)
if phase in ('bending-onset-v1', 'prefix-recovery-v1', 'bending-continuation-v1') or phase.startswith('prefix-discriminator-'):
    from dataclasses import replace, asdict
    from anymaterial import DNVC208MaterialCurve
    from anysolver import stiffened_shell as ss
    from examples.stiffened_shell_native_fibre_bl5 import definition
    model = definition(yield_stress=1e5)
    curve = DNVC208MaterialCurve(1e6, 1.05e6, 1.1e6, .005, .01, 4e6, .2)
    model = replace(model, shell=replace(model.shell, j2_curve=curve), bl5_material_policy=ss.BL5_NATIVE_FIBRE_MATERIAL_V1)
    owner = ss.create_analysis(definition=model)
    observed = []
    def save_runtime():
        modules = {n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
                   if (n == 'anysolver' or n.startswith('anysolver.')) and getattr(m, '__file__', None)}
        (ROOT/('runtime-'+phase+'.json')).write_text(json.dumps(dict(dependencies=dependencies, imports=modules,
            pools=threadpool_info(), affinity=psutil.Process().cpu_affinity(), jit_disabled=bool(numba.config.DISABLE_JIT)), indent=2))
    def observe(result):
        observed.append(dict(factor=result.load_factor, equilibrium=result.free_equilibrium_ratio, gap=result.constraint_max,
            shell=numpy.asarray(result.shell_layer_alpha).tolist(), beams=numpy.asarray(result.beam_station_accumulated).tolist()))
        (ROOT/('observed-'+phase+'.json')).write_text(json.dumps(observed, indent=2))
        (ROOT/('latest-prefix-'+phase+'.bin')).write_bytes(owner.checkpoint())
    try:
        if phase.startswith('prefix-discriminator-'):
            from anysolver.control import CancellationToken, SolveCancelled
            from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
            from anysolver._ge_beam3_retained_fibre import RetainedFibreOperator
            from unittest.mock import patch
            raw = (ROOT/'failed-prefix-bending-continuation-v1.bin').read_bytes()
            prefix = owner.restore(raw)
            assert owner.checkpoint() == raw
            driver = owner._finite_driver; state = driver._state
            def evaluate(q):
                return driver._assemble(q, prefix.load_factor, driver._shell_predecessors,
                    driver._beam_predecessors, pattern=driver._pattern)
            def active(value):
                shell = tuple(tuple(numpy.asarray(c['alpha']) > numpy.asarray(o['alpha']))
                    for c,o in zip(value[4],driver._shell_predecessors))
                beams = []
                for c,o in zip(value[5],driver._beam_predecessors):
                    for a,b in zip(c.stations,o.stations):
                        if hasattr(a,'rows'):
                            beams.extend(float(x[2]+x[3]) > float(y[2]+y[3]) for x,y in zip(a.rows,b.rows))
                        else:
                            beams.append(sum(a.accumulated) > sum(b.accumulated))
                return shell, tuple(beams)
            base = evaluate(state); residual,tangent = base[:2]; branch = active(base)
            direction = numpy.zeros(len(residual))
            direction[:owner._shell_count:6] = numpy.linspace(0.,1e-4,len(owner._shell_ids))
            direction[3:owner._shell_count:6] = numpy.linspace(0.,2e-4,len(owner._shell_ids))
            direction[4:owner._shell_count:6] = numpy.linspace(0.,-3e-4,len(owner._shell_ids))
            for i in range(len(owner._beam_ids)):
                start=owner._shell_count+6*i
                direction[start+2] = .001*(i+1)
                direction[start+3:start+6] = (2e-4,-1e-4,3e-4)
            retained=owner._shell_count+driver._beam_nodal
            for i in range(len(owner._beam_parts)):
                start=retained+24*i
                direction[start:start+6] = (2e-4,-3e-4,1e-4,-2e-4,1e-4,3e-4)
                direction[start+6:start+24] = owner._coordinate_scale[start+6:start+24]*1e-6
            direction[owner._fixed] = 0.
            direction[len(state.q):] = numpy.linspace(1.,2.,len(state.multipliers))
            weights=numpy.r_[owner._coordinate_scale,numpy.ones(owner._C.shape[0])]
            expected=tangent@direction; errors=[]; masks=[]
            for h in (1e-4,1e-5,1e-6):
                positive=evaluate(driver._advance(state,direction,h))
                negative=evaluate(driver._advance(state,direction,-h))
                same=active(positive)==active(negative)==branch
                masks.append(same)
                error=float(numpy.linalg.norm(((positive[0]-negative[0])/(2*h)-expected)*weights)/max(numpy.linalg.norm(expected*weights),1.))
                errors.append(error)
            report=dict(factor=prefix.load_factor, shell_alpha_max=float(numpy.max(prefix.shell_layer_alpha)),
                fibre_alpha_max=float(numpy.max(prefix.beam_station_accumulated)), tangent_errors=errors, branch_consistent=masks,
                active_shell_points=int(sum(sum(row) for row in branch[0])),active_beam_points=int(sum(branch[1])),
                tolerance=1e-5, both_finer_pass=max(errors[1:])<=1e-5)
            (ROOT/(phase+'.json')).write_text(json.dumps(report,indent=2))
            assert all(masks) and max(errors[1:]) <= 1e-5, report
            assert owner.checkpoint() == raw
            token=CancellationToken();token.cancel('cancel accepted material continuation before trial')
            try:
                owner.solve((ss.NodalAction('beam',105,(0.,0.,500.,0.,0.,0.)),),(.65,),
                    max_iterations=24,max_backtracks=12,increment_control=ss.AdaptiveIncrementControl(4,64),cancellation_token=token)
            except SolveCancelled:
                pass
            else:
                raise AssertionError('cancellation failed')
            assert owner.checkpoint()==raw
            def refused(self):raise ValueError('captured retained fibre reference changed')
            with patch.object(RetainedFibreOperator,'guard',refused):
                try:evaluate(state)
                except ValueError:pass
                else:raise AssertionError('local mutation guard failed')
            assert owner.checkpoint()==raw
            try:prefix.beam_fibre_material[0].strain[0]+=1.
            except ValueError:pass
            else:raise AssertionError('mutable fibre recovery')
            try:owner.rebase_rotations(prefix.generation-1)
            except ValueError:pass
            else:raise AssertionError('stale generation accepted')
            fresh=ss.create_analysis(definition=model)
            try:
                restored=fresh.restore(raw)
                assert fresh.checkpoint()==raw
                for left,right in zip(prefix.beam_fibre_material,restored.beam_fibre_material):
                    numpy.testing.assert_array_equal(left.strain,right.strain)
                    numpy.testing.assert_array_equal(left.resultants,right.resultants)
            finally:fresh.close()
            report.update(checkpoint_unchanged=True, precancellation_atomic=True, local_guard_failure_atomic=True,
                          immutable_recovery=True, stale_generation_refused=True, fresh_restore_bytes_equal=True)
            (ROOT/(phase+'.json')).write_text(json.dumps(report,indent=2))
            sys.exit(0)
        if phase == 'prefix-recovery-v1':
            raw = (ROOT/'prefix-bending-onset-v1.bin').read_bytes()
            result = owner.restore(raw)
            assert owner.checkpoint() == raw
            stresses = []
            for record in result.shell_q4_material:
                sx, sy, txy = record.layer_stress.T
                mises = numpy.sqrt(sx*sx-sx*sy+sy*sy+3*txy*txy)
                stresses.append(dict(element=record.element_id, max_equivalent_pa=float(mises.max()),
                                     max_layer=int(mises.argmax()), stress=record.layer_stress.tolist(), alpha=record.alpha.tolist()))
            root_force = numpy.zeros(3); root_moment = numpy.zeros(3)
            for node in (1,5):
                i = owner._shell_index[node]
                wrench = result.support_reactions[6*i:6*i+6]
                point = owner._shell_xyz[i]+result.shell_displacement[6*i:6*i+3]
                root_force += wrench[:3]
                root_moment += wrench[3:]+numpy.cross(point,wrench[:3])
            interface_force = numpy.zeros(3); interface_moment = numpy.zeros(3)
            line = []
            for record in result.beam_shell_line_work:
                rows = record.integrated_spatial_gradient[:12].reshape(2,6)
                for j in range(2):
                    slot = int(record.physical_slots[6*j]); i = slot//6
                    point = owner._shell_xyz[i]+result.shell_displacement[slot:slot+3]
                    interface_force += rows[j,:3]
                    interface_moment += rows[j,3:]+numpy.cross(point,rows[j,:3])
                line.append(dict(slots=record.physical_slots.tolist(), measure=record.reference_measure_m,
                                 integrated_gradient=record.integrated_spatial_gradient.tolist()))
            fibres = [dict(element=r.element_id, station=r.station, xi=r.xi,
                           resultants=(r.resultants+r.resultants_low).tolist(),
                           fibres=[asdict(f) for f in r.fibres]) for r in result.beam_fibre_material]
            generalized = [dict(element=r.element_id if hasattr(r,'element_id') else None,
                                stations=[dict(branch=x.branch, accumulated=x.accumulated, resultants=(x.local_resultants+x.local_resultants_low).tolist())
                                          for x in r.stations]) for r in result.beam_generalized_material]
            (ROOT/'prefix-recovery-v1.json').write_text(json.dumps(dict(shell=stresses, root_force=root_force.tolist(),
                root_moment=root_moment.tolist(), interface_shell_force=interface_force.tolist(), interface_shell_moment=interface_moment.tolist(),
                line=line, fibres=fibres, generalized=generalized, checkpoint_bytes_unchanged=True), indent=2))
            sys.exit(0)
        targets = (.01, .1, .2)
        if phase == 'bending-continuation-v1':
            prefix = owner.restore((ROOT/'prefix-bending-onset-v1.bin').read_bytes())
            targets = (.65,)
            observed.append(dict(factor=prefix.load_factor, equilibrium=prefix.free_equilibrium_ratio, gap=prefix.constraint_max,
                shell=numpy.asarray(prefix.shell_layer_alpha).tolist(), beams=numpy.asarray(prefix.beam_station_accumulated).tolist()))
        actions = (ss.NodalAction('beam', 105, (0., 0., 500., 0., 0., 0.)),)
        result = owner.solve(actions, targets, max_iterations=24, max_backtracks=12,
            increment_control=ss.AdaptiveIncrementControl(4,64),
            on_accepted=observe)
        (ROOT/('result-'+phase+'.json')).write_text(json.dumps(dict(status=result.status, observed=observed), indent=2))
        (ROOT/('prefix-'+phase+'.bin')).write_bytes(owner.checkpoint())
    except BaseException as error:
        if isinstance(error, SystemExit) and error.code == 0:
            raise
        (ROOT/('failure-'+phase+'.json')).write_text(json.dumps(dict(type=type(error).__name__, message=str(error), observed=observed,
            attempts=[asdict(a) for a in getattr(error, 'attempts', ())]), indent=2))
        if owner._finite_driver is not None:
            (ROOT/('failed-prefix-'+phase+'.bin')).write_bytes(owner.checkpoint())
        raise
    finally:
        save_runtime()
        owner.close()
    sys.exit(0)
class Record:
    def pytest_sessionfinish(self, session, exitstatus):
        modules = {n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items()
                   if (n == 'anysolver' or n.startswith('anysolver.')) and getattr(m, '__file__', None)}
        record = dict(exit_code=int(exitstatus), collected=session.testscollected, failed=session.testsfailed,
                      dependencies=dependencies,
                      pools=threadpool_info(), imports=modules, affinity=psutil.Process().cpu_affinity(),
                      jit_disabled=bool(numba.config.DISABLE_JIT), numba_threads=numba.get_num_threads())
        (ROOT/('runtime-'+phase+'.json')).write_text(json.dumps(record, indent=2)+'\n')
        assert all(Path(p).is_relative_to((REPO/'src').resolve()) for p in modules.values())
        assert all(p['num_threads'] == 1 for p in record['pools'])
args = ['-q', '-p', 'no:cacheprovider', '--basetemp', str(ROOT/('pytest-'+phase)),
        '--junitxml='+str(ROOT/('junit-'+phase+'.xml')), str(REPO/'tests/test_stiffened_shell_native_fibre_bl5_material.py')]
if phase.startswith('admission-'):
    args += ['-k', 'policy_admission or policy_restore']
elif phase == 'partial-atomic-v1':
    args += ['-k', 'partial_material_trial']
elif phase == 'lifecycle-v1':
    args += ['-k', 'lifecycle']
elif phase == 'impact-v1':
    args[-1:] = [str(REPO/p) for p in (
        'tests/test_stiffened_shell_native_fibre_bl5_material.py::test_public_partial_fibre_workflow',
        'tests/test_stiffened_shell_native_fibre_bl5.py::test_true_yield_refusal_and_ownership_error_not_domain_or_retry',
        'tests/test_stiffened_shell_bl5_material.py::test_selected_bl5_pre_yield_snapshot_and_legacy_isolation',
        'tests/test_stiffened_shell_ge_finite_experimental.py::test_finite_point_panel_accepts_two_complete_elastic_increments')]
elif phase == 'impact-v2':
    args[-1:] = [str(REPO/p) for p in (
        'tests/test_stiffened_shell_bl5_material.py::test_bl5_generalized_yield_reject_rebase_reverse_and_restart',
        'tests/test_stiffened_shell_ge_finite_experimental.py::test_q4_shell_and_beam_yield_atomically_and_restart')]
raise SystemExit(pytest.main(args, plugins=[Record()]))
