from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from scripts import development_test_runtime as runtime
from scripts import run_portable_ci as runner


def test_portable_native_deadline_headroom_is_fixed_and_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv('ANYSOLVER_GE_BEAM3_DEADLINE_SCALE', '1000')
    environment = runner._worker_environment(tmp_path)
    assert environment['ANYSOLVER_GE_BEAM3_DEADLINE_SCALE'] == '4'
    assert environment['OPENBLAS_NUM_THREADS'] == '1'
    assert environment['MKL_NUM_THREADS'] == '1'
    # Preparing CI execution settings does not mutate the calling application.
    assert __import__('os').environ['ANYSOLVER_GE_BEAM3_DEADLINE_SCALE'] == '1000'


def test_explicit_selection_preserves_node_and_rejects_empty_missing_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    assert runner._development_targets(['tests/test_x.py::test_x[units-m]']) == ('tests/test_x.py::test_x[units-m]',)
    for targets in ([], ['tests/test_x.py::'], ['tests/test_x.py']*2, ['-k']):
        with pytest.raises(ValueError): runner._development_targets(targets)
    with pytest.raises(FileNotFoundError): runner._development_targets(['tests/test_missing.py'])
    (tmp_path/'other.py').write_text('')
    with pytest.raises(ValueError): runner._development_targets(['other.py'])


def test_development_does_not_collect_or_deselect_ci_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    def forbidden(*args, **kwargs): raise AssertionError('broad inventory/partition reached')
    monkeypatch.setattr(runner, 'merge_test_modules', forbidden)
    monkeypatch.setattr(runner, 'execution_partitions', forbidden)
    commands = []
    def launch(command, *, cwd, env, **kwargs):
        commands.append(command)
        assert cwd == tmp_path and env['NUMBA_DISABLE_JIT'] == '1'
        assert env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
        Path(env['ANYSOLVER_DEVELOPMENT_RECORD']).write_text('{}')
        return SimpleNamespace(poll=lambda: 0, returncode=0)
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    assert runner.run(workers=8, timeout_seconds=1, development_targets=['tests/test_x.py::test_x']) == 0
    assert len(commands) == 1 and commands[0][-1] == 'tests/test_x.py::test_x'
    assert not any(c.startswith('--deselect') for c in commands[0])


def test_missing_runtime_record_cannot_report_success(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *args, **kwargs:
                        SimpleNamespace(poll=lambda: 0, returncode=0))
    assert runner.run(workers=1, timeout_seconds=1, development_targets=['tests/test_x.py']) == 1


@pytest.mark.parametrize('code', [1, 2, 4, 5])
def test_child_non_success_is_never_accepted(tmp_path, monkeypatch, code):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *args, **kwargs:
                        SimpleNamespace(poll=lambda: code, returncode=code))
    assert runner.run(workers=1, timeout_seconds=1, development_targets=['tests/test_x.py']) == 1


def test_runtime_reports_observed_settings_and_rejects_wrong_source(tmp_path, monkeypatch):
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '1')
    monkeypatch.setenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', '1')
    numba = SimpleNamespace(config=SimpleNamespace(DISABLE_JIT=True, NUMBA_NUM_THREADS=1),
                            get_num_threads=lambda: 1)
    modules = {'anysolver': SimpleNamespace(__file__=str(tmp_path/'__init__.py')), 'numba': numba}
    result = runtime.runtime_record(modules, tmp_path, [{'user_api': 'blas', 'num_threads': 1}])
    assert not result['errors'] and result['jit_disabled'] is True and result['numba_threads'] == 1
    assert result['requested_threads'] == 1 and result['numba_max_threads'] == 1
    assert result['requested_jit_disabled'] is True
    assert runtime.runtime_record(modules, tmp_path/'other')['errors']
    assert runtime.runtime_record(modules, tmp_path, [{'user_api': 'blas', 'num_threads': 2}])['errors']
    numba.config.DISABLE_JIT = False
    assert runtime.runtime_record(modules, tmp_path)['errors']


def test_focused_mode_cannot_replace_matrix_or_set_ci_runtime():
    with pytest.raises(ValueError):
        runner.run(workers=1, timeout_seconds=1, development_targets=[], matrix_shard_index=0)
    with pytest.raises(ValueError): runner.run(workers=1, timeout_seconds=1, jit='off')


def test_development_deadline_terminates_owned_process(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    process = SimpleNamespace(poll=lambda: None, returncode=-1)
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *args, **kwargs: process)
    ticks = iter((0., 0., 2., 2.))
    monkeypatch.setattr(runner.time, 'monotonic', lambda: next(ticks))
    terminated = []
    monkeypatch.setattr(runner, '_terminate_tree', terminated.append)
    assert runner.run(workers=1, timeout_seconds=1, development_targets=['tests/test_x.py']) == runner.TIMEOUT_EXIT_CODE
    assert terminated == [process]
    record = json.loads(next((tmp_path/'temp').glob('*/P01/resource.json')).read_text())
    assert record['status'] == 'timeout' and record['child_exit_codes'] == [-1]


def test_nested_matrix_preserves_parent_allocation_and_complete_coverage(monkeypatch):
    critical = tuple(runner.PORTABLE_CURRENT_S3_SUCCESSOR_MODULES)
    modules = (*critical, *(f"tests/test_general_{i}.py" for i in range(64)))
    monkeypatch.setattr(runner, '_module_weight', lambda module: 1)
    general = set(modules) - set(critical)
    all_general = []
    for parent in range(8):
        outer = runner.matrix_modules(modules, parent, 8)
        assigned = []
        for sub in range(4):
            selected = runner.matrix_modules(outer, sub, 4)
            assert set(critical) <= set(selected)
            assert set(selected) <= set(outer)
            assigned.extend(m for m in selected if m in general)
        assert len(assigned) == len(set(assigned))
        assert set(assigned) == set(outer) - set(critical)
        all_general.extend(assigned)
    assert len(all_general) == len(set(all_general)) == len(general)
    assert set(all_general) == general


@pytest.mark.parametrize('parent,inner', [
    ((None,None),(0,4)), ((0,8),(None,4)), ((0,8),(0,None)),
    ((0,8),(-1,4)), ((0,8),(4,4)), ((0,8),(0,0)),
    ((0,8),(True,4)), ((0,8),(0,True))])
def test_nested_matrix_rejects_invalid_configuration(monkeypatch, parent, inner):
    monkeypatch.setattr(runner, 'merge_test_modules',
                        lambda: (*runner.PORTABLE_CURRENT_S3_SUCCESSOR_MODULES,
                                 *(f'tests/test_general_{i}.py' for i in range(64))))
    monkeypatch.setattr(runner, '_module_weight', lambda module: 1)
    with pytest.raises(ValueError, match='matrix'):
        runner.run(workers=2, timeout_seconds=1,
                   matrix_shard_index=parent[0], matrix_shard_count=parent[1],
                   matrix_subshard_index=inner[0], matrix_subshard_count=inner[1])


def test_development_refuses_nested_ci_selection():
    with pytest.raises(ValueError, match='focused development'):
        runner.run(workers=2, timeout_seconds=1, development_targets=[],
                   matrix_subshard_index=0, matrix_subshard_count=4)


@pytest.mark.parametrize('failure', [False, True])
def test_ci_full_success_or_failed_child_stops_live_sibling(tmp_path, monkeypatch, failure):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('a.py','b.py'))
    monkeypatch.setattr(runner, 'execution_partitions', lambda *args: (('a.py',),('b.py',)))
    launched = []
    terminated = []
    def launch(*args, **kwargs):
        index = len(launched)
        values = iter((None, 1) if failure and index == 0 else
                      (None, None) if failure else (None, 0))
        process = SimpleNamespace(returncode=None)
        def poll():
            process.returncode = next(values, process.returncode)
            return process.returncode
        process.poll = poll
        launched.append(process)
        return process
    def terminate(process):
        if process.returncode is None:
            terminated.append(process)
            process.returncode = -15
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    monkeypatch.setattr(runner, '_terminate_tree', terminate)
    assert runner.run(workers=2, timeout_seconds=1) == int(failure)
    assert len(launched) == 2
    assert terminated == ([launched[1]] if failure else [])


def test_ci_does_not_launch_more_work_after_immediate_failure(tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('a.py','b.py'))
    monkeypatch.setattr(runner, 'execution_partitions', lambda *args: (('a.py',),('b.py',)))
    launched = []
    def launch(*args, **kwargs):
        process = SimpleNamespace(poll=lambda: 1, returncode=1)
        launched.append(process)
        return process
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    monkeypatch.setattr(runner, '_terminate_tree', lambda process: None)
    assert runner.run(workers=2, timeout_seconds=1) == 1
    assert len(launched) == 1


def test_ci_worker_stops_at_first_failure(tmp_path):
    assert '-x' in runner._worker_command(('tests/test_x.py',), tmp_path)


def test_runtime_record_requires_explicit_requested_profile(tmp_path, monkeypatch):
    monkeypatch.delenv('NUMBA_DISABLE_JIT', raising=False)
    monkeypatch.delenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', raising=False)
    numba = SimpleNamespace(config=SimpleNamespace(DISABLE_JIT=True, NUMBA_NUM_THREADS=1),
                            get_num_threads=lambda: 1)
    result = runtime.runtime_record({'numba': numba}, tmp_path)
    assert result['requested_threads'] is None and result['requested_jit_disabled'] is None
    assert any('requested runtime profile' in error for error in result['errors'])


def test_runtime_record_admits_bounded_profile_and_requires_restored_baseline(tmp_path, monkeypatch):
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '0')
    monkeypatch.setenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', '3')
    def numba_at(active, capacity):
        return SimpleNamespace(config=SimpleNamespace(DISABLE_JIT=False, NUMBA_NUM_THREADS=capacity),
                               get_num_threads=lambda: active)
    restored = {'numba': numba_at(1, 3)}
    assert not runtime.runtime_record(restored, tmp_path, [{'user_api': 'openmp', 'num_threads': 3}])['errors']
    assert not runtime.runtime_record(restored, tmp_path, [{'user_api': 'blas', 'num_threads': 1}])['errors']
    assert runtime.runtime_record(restored, tmp_path, [{'user_api': 'blas', 'num_threads': 3}])['errors']
    assert runtime.runtime_record({'numba': numba_at(3, 3)}, tmp_path)['errors']
    assert runtime.runtime_record({'numba': numba_at(1, 1)}, tmp_path)['errors']
    assert runtime.runtime_record(restored, tmp_path, [{'user_api': 'openmp', 'num_threads': 4}])['errors']
    monkeypatch.setenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', '1')
    assert runtime.runtime_record(restored, tmp_path, [{'user_api': 'openmp', 'num_threads': 3}])['errors']


def test_compiled_profile_refuses_unavailable_or_partial_numba(tmp_path, monkeypatch):
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '0')
    monkeypatch.setenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', '3')
    assert runtime.runtime_record({}, tmp_path)['errors']
    assert runtime.runtime_record({'numba': SimpleNamespace()}, tmp_path)['errors']
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '1')
    assert not runtime.runtime_record({}, tmp_path)['errors']


@pytest.mark.parametrize('pool', [{}, {'user_api': 'blas', 'num_threads': None},
                                 {'user_api': 'unknown', 'num_threads': 1}, None])
def test_runtime_refuses_unknown_or_unobserved_pools(tmp_path, monkeypatch, pool):
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '1')
    monkeypatch.setenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', '1')
    assert runtime.runtime_record({}, tmp_path, [pool])['errors']


def test_runtime_initializes_active_baseline_without_reducing_capacity(monkeypatch):
    monkeypatch.setenv('NUMBA_DISABLE_JIT', '0')
    monkeypatch.setenv('ANYSOLVER_DEVELOPMENT_NUMBA_THREADS', '3')
    active = [3]
    fake = SimpleNamespace(config=SimpleNamespace(DISABLE_JIT=False, NUMBA_NUM_THREADS=3),
                           get_num_threads=lambda: active[0],
                           set_num_threads=lambda value: active.__setitem__(0, value))
    monkeypatch.setitem(runtime.sys.modules, 'numba', fake)
    monkeypatch.setattr(runtime, '_INITIAL_RUNTIME', None)
    monkeypatch.setattr(runtime, '_STARTUP_ERRORS', [])
    runtime.pytest_configure(None)
    assert runtime._INITIAL_RUNTIME['before_initialization']['numba_threads'] == 3
    assert runtime._INITIAL_RUNTIME['numba_threads'] == 1
    assert runtime._INITIAL_RUNTIME['numba_max_threads'] == 3
    assert not runtime._STARTUP_ERRORS


def test_real_runtime_rejects_a_leaked_active_thread_scope(tmp_path):
    import importlib.util
    import os
    import subprocess
    import sys
    if importlib.util.find_spec('numba') is None:
        pytest.skip('Numba is not installed')
    target = tmp_path/'test_leaked_scope.py'
    target.write_text('def test_leak():\n    import numba\n    numba.set_num_threads(3)\n')
    record = tmp_path/'runtime.json'
    env = {**os.environ, 'NUMBA_DISABLE_JIT': '0', 'NUMBA_NUM_THREADS': '3',
           'ANYSOLVER_DEVELOPMENT_NUMBA_THREADS': '3',
           'ANYSOLVER_DEVELOPMENT_SOURCE': str(runner.ROOT/'src'),
           'ANYSOLVER_DEVELOPMENT_RECORD': str(record),
           'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}
    child = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--noconftest',
                            '-p', 'no:cacheprovider', '-p', 'scripts.development_test_runtime', str(target)],
                           cwd=runner.ROOT, env=env, capture_output=True, text=True, timeout=30)
    assert child.returncode == 1, child.stdout + child.stderr
    payload = json.loads(record.read_text())
    assert payload['initial_runtime']['numba_threads'] == 1
    assert payload['numba_max_threads'] == payload['numba_threads'] == 3
    assert any('not restored' in error for error in payload['errors'])


def test_development_thread_profile_is_explicit_and_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    environments = []
    def launch(command, *, cwd, env, **kwargs):
        environments.append(env)
        Path(env['ANYSOLVER_DEVELOPMENT_RECORD']).write_text('{}')
        return SimpleNamespace(poll=lambda: 0, returncode=0)
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    assert runner.run(workers=1, timeout_seconds=1,
                      development_targets=['tests/test_x.py'], threads=3) == 0
    assert environments[0]['NUMBA_NUM_THREADS'] == '3'
    assert environments[0]['ANYSOLVER_DEVELOPMENT_NUMBA_THREADS'] == '3'
    selection = json.loads(next((tmp_path/'temp').glob('*/P01/selection.json')).read_text())
    assert selection['threads'] == 3
    assert runner.run(workers=1, timeout_seconds=1, development_targets=['tests/test_x.py']) == 0
    assert environments[1]['NUMBA_NUM_THREADS'] == '1'
    assert environments[1]['ANYSOLVER_DEVELOPMENT_NUMBA_THREADS'] == '1'
    for rejected in (0, 9, True, '2'):
        with pytest.raises(ValueError):
            runner.run(workers=1, timeout_seconds=1, development_targets=['tests/test_x.py'],
                       threads=rejected)
    with pytest.raises(ValueError):
        runner.run(workers=1, timeout_seconds=1, threads=2)


def test_ci_worker_writes_allocation_and_progress_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('a.py', 'b.py'))
    monkeypatch.setattr(runner, 'execution_partitions',
                        lambda modules, workers: (('a.py',), ('b.py',)))
    launched = []
    def launch(command, *, cwd, env, **kwargs):
        launched.append((command, env))
        return SimpleNamespace(poll=lambda: 0, returncode=0)
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    assert runner.run(workers=2, timeout_seconds=1) == 0
    assert all(command.count('scripts.ci_progress_runtime') == 1
               for command, _ in launched)
    selections = sorted(tmp_path.glob('anysolver-portable-ci-*/P*/selection.json'))
    assert len(selections) == 2
    records = [json.loads(path.read_text()) for path in selections]
    # The evidence mirrors the unchanged partition allocation exactly.
    assert [record['allocated_modules'] for record in records] == [['a.py'], ['b.py']]
    assert all(record['scope'] == 'ci allocation evidence only; not qualification'
               and record['timeout_seconds'] == 1 for record in records)
    for (command, env), path in zip(launched, selections):
        assert json.loads(path.read_text())['command'] == command
        assert Path(env['ANYSOLVER_CI_PROGRESS_RECORD']) == path.parent/'progress.json'


def test_ci_timeout_termination_evidence_identifies_current_node(tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('a.py',))
    monkeypatch.setattr(runner, 'execution_partitions', lambda modules, workers: (('a.py',),))
    process = SimpleNamespace(poll=lambda: None, returncode=None)
    def launch(command, *, cwd, env, **kwargs):
        Path(env['ANYSOLVER_CI_PROGRESS_RECORD']).write_text(json.dumps({
            'current_node': 'a.py::test_hung', 'completed': 3, 'collected': 5})+'\n')
        return process
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    ticks = iter((0., 0., 5., 5.))
    monkeypatch.setattr(runner.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(runner, '_terminate_tree', lambda worker: None)
    assert runner.run(workers=1, timeout_seconds=1) == runner.TIMEOUT_EXIT_CODE
    termination = json.loads(
        next(tmp_path.glob('anysolver-portable-ci-*/termination.json')).read_text())
    assert termination['status'] == 'timeout' and termination['elapsed_seconds'] == 5
    worker = termination['workers'][0]
    assert worker['worker'] == 'P01' and worker['allocated_modules'] == ['a.py']
    assert worker['exit_code'] is None
    assert worker['progress']['current_node'] == 'a.py::test_hung'


def test_ci_failed_worker_cancellation_writes_termination_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('a.py', 'b.py'))
    monkeypatch.setattr(runner, 'execution_partitions',
                        lambda modules, workers: (('a.py',), ('b.py',)))
    launched = []
    def launch(*args, **kwargs):
        process = SimpleNamespace(returncode=None)
        process.poll = lambda: 1
        process.returncode = 1
        launched.append(process)
        return process
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    monkeypatch.setattr(runner, '_terminate_tree', lambda worker: None)
    assert runner.run(workers=2, timeout_seconds=1) == 1
    assert len(launched) == 1
    termination = json.loads(
        next(tmp_path.glob('anysolver-portable-ci-*/termination.json')).read_text())
    assert termination['status'] == 'failed_worker'
    assert [worker['allocated_modules'] for worker in termination['workers']] == [['a.py']]


def test_development_records_stay_free_of_ci_progress_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_x.py').write_text('')
    commands = []
    def launch(command, *, cwd, env, **kwargs):
        commands.append((command, env))
        Path(env['ANYSOLVER_DEVELOPMENT_RECORD']).write_text('{}')
        return SimpleNamespace(poll=lambda: 0, returncode=0)
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    assert runner.run(workers=1, timeout_seconds=1,
                      development_targets=['tests/test_x.py']) == 0
    command, env = commands[0]
    assert 'scripts.ci_progress_runtime' not in command
    assert 'ANYSOLVER_CI_PROGRESS_RECORD' not in env


def test_ci_progress_plugin_is_optional_and_never_alters_the_session(tmp_path, monkeypatch):
    import importlib.util
    # CI loads the real module as a live plugin. Exercise a separate module
    # instance so this unit test cannot replace its running session counters.
    spec = importlib.util.spec_from_file_location('ci_progress_unit', runner.ROOT/'scripts/ci_progress_runtime.py')
    progress = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(progress)
    monkeypatch.delenv(progress.RECORD_ENV, raising=False)
    progress.pytest_configure(SimpleNamespace(args=['-q', 'tests/test_x.py']))
    progress.pytest_collection_finish(SimpleNamespace(items=[1, 2, 3]))
    progress.pytest_runtest_logstart('tests/test_x.py::test_a', None)
    progress.pytest_runtest_logreport(SimpleNamespace(when='setup', outcome='passed'))
    progress.pytest_runtest_logreport(SimpleNamespace(when='call', outcome='passed'))
    session = SimpleNamespace(exitstatus=0)
    progress.pytest_sessionfinish(session, 0)
    assert session.exitstatus == 0 and not list(tmp_path.iterdir())
    record = tmp_path/'progress.json'
    monkeypatch.setenv(progress.RECORD_ENV, str(record))
    progress.pytest_configure(SimpleNamespace(args=['-q', 'tests/test_x.py']))
    progress.pytest_collection_finish(SimpleNamespace(items=[1, 2, 3]))
    # Call finished but teardown still pending: not yet a completed lifecycle.
    progress.pytest_runtest_logstart('tests/test_x.py::test_a', None)
    progress.pytest_runtest_logreport(SimpleNamespace(when='setup', outcome='passed'))
    progress.pytest_runtest_logreport(SimpleNamespace(when='call', outcome='passed'))
    payload = json.loads(record.read_text())
    assert payload['started'] == 1 and payload['completed'] == 0
    assert payload['current_node'] == 'tests/test_x.py::test_a'
    assert payload['current_phase'] == 'teardown'
    assert payload['outcomes'] == {'passed': 1}
    progress.pytest_runtest_logreport(SimpleNamespace(when='teardown', outcome='passed'))
    progress.pytest_runtest_logfinish('tests/test_x.py::test_a', None)
    progress.pytest_runtest_logstart('tests/test_x.py::test_b', None)
    progress.pytest_runtest_logreport(SimpleNamespace(when='setup', outcome='skipped'))
    progress.pytest_runtest_logreport(SimpleNamespace(when='teardown', outcome='passed'))
    progress.pytest_runtest_logfinish('tests/test_x.py::test_b', None)
    session = SimpleNamespace(exitstatus=0)
    progress.pytest_sessionfinish(session, 2)
    assert session.exitstatus == 0
    payload = json.loads(record.read_text())
    assert payload['scope'] == 'ci progress evidence only; not qualification'
    assert payload['allocated_modules'] == ['tests/test_x.py']
    assert payload['collected'] == 3 and payload['started'] == 2
    assert payload['completed'] == 2 and payload['outcomes'] == {'passed': 1, 'skipped': 1}
    assert payload['current_node'] is None and payload['current_phase'] is None
    assert payload['pytest_exit_code'] == 2 and 'updated_utc' in payload


def test_ci_progress_plugin_records_a_real_pytest_child(tmp_path):
    import os
    import subprocess
    import sys
    target = tmp_path/'test_progress_child.py'
    target.write_text('def test_ok():\n    assert True\n')
    record = tmp_path/'progress.json'
    env = {**os.environ, 'ANYSOLVER_CI_PROGRESS_RECORD': str(record),
           'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}
    child = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--noconftest',
                            '-p', 'no:cacheprovider', '-p', 'scripts.ci_progress_runtime',
                            str(target)],
                           cwd=runner.ROOT, env=env, capture_output=True, text=True,
                           timeout=60)
    assert child.returncode == 0, child.stdout + child.stderr
    payload = json.loads(record.read_text())
    assert payload['allocated_modules'] == [str(target)]
    assert payload['current_node'] is None and payload['current_phase'] is None
    assert payload['outcomes'] == {'passed': 1} and payload['completed'] == 1
    assert payload['pytest_exit_code'] == 0


def test_ci_progress_plugin_classifies_real_pytest_lifecycle_outcomes(tmp_path):
    import os
    import subprocess
    import sys
    target = tmp_path/'test_progress_lifecycle.py'
    target.write_text(
        'import pytest\n'
        '\n'
        'def test_pass():\n'
        '    assert True\n'
        '\n'
        '@pytest.mark.skip(reason="setup skip")\n'
        'def test_setup_skip():\n'
        '    assert True\n'
        '\n'
        '@pytest.fixture\n'
        'def broken_setup():\n'
        '    raise RuntimeError("setup failure")\n'
        '\n'
        'def test_setup_fail(broken_setup):\n'
        '    assert True\n'
        '\n'
        '@pytest.fixture\n'
        'def broken_teardown():\n'
        '    yield\n'
        '    raise RuntimeError("teardown failure")\n'
        '\n'
        'def test_teardown_fail(broken_teardown):\n'
        '    assert True\n')
    record = tmp_path/'progress.json'
    env = {**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}
    base = [sys.executable, '-m', 'pytest', '-q', '--noconftest',
            '-p', 'no:cacheprovider', str(target)]
    plain = subprocess.run(base, cwd=runner.ROOT, env=env, capture_output=True,
                           text=True, timeout=60)
    env['ANYSOLVER_CI_PROGRESS_RECORD'] = str(record)
    with_plugin = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', '--noconftest',
         '-p', 'no:cacheprovider', '-p', 'scripts.ci_progress_runtime', str(target)],
        cwd=runner.ROOT, env=env, capture_output=True, text=True, timeout=60)
    # The plugin never changes the session outcome or its reported summary.
    assert with_plugin.returncode == plain.returncode != 0
    for text in (plain.stdout, with_plugin.stdout):
        assert '2 passed' in text and '1 skipped' in text and '2 errors' in text
    payload = json.loads(record.read_text())
    assert payload['started'] == 4 and payload['completed'] == 4
    assert payload['current_node'] is None and payload['current_phase'] is None
    assert payload['outcomes'] == {'passed': 2, 'skipped': 1,
                                   'setup_error': 1, 'teardown_error': 1}
    assert payload['pytest_exit_code'] == with_plugin.returncode


def test_ci_parent_interruption_records_termination_and_reraises(tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('a.py',))
    monkeypatch.setattr(runner, 'execution_partitions',
                        lambda modules, workers: (('a.py',),))
    def hung():
        raise KeyboardInterrupt
    process = SimpleNamespace(poll=hung, returncode=None)
    def launch(command, *, cwd, env, **kwargs):
        Path(env['ANYSOLVER_CI_PROGRESS_RECORD']).write_text(json.dumps({
            'current_node': 'a.py::test_current', 'current_phase': 'call'})+'\n')
        return process
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    terminated = []
    monkeypatch.setattr(runner, '_terminate_tree',
                        lambda worker: terminated.append(worker))
    with pytest.raises(KeyboardInterrupt):
        runner.run(workers=1, timeout_seconds=1)
    assert terminated == [process]
    termination = json.loads(
        next(tmp_path.glob('anysolver-portable-ci-*/termination.json')).read_text())
    assert termination['status'] == 'interrupted:KeyboardInterrupt'
    worker = termination['workers'][0]
    assert worker['worker'] == 'P01' and worker['exit_code'] is None
    assert worker['progress']['current_node'] == 'a.py::test_current'
