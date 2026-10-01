from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from scripts import development_test_runtime as runtime
from scripts import run_portable_ci as runner


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
    numba = SimpleNamespace(config=SimpleNamespace(DISABLE_JIT=True), get_num_threads=lambda: 1)
    modules = {'anysolver': SimpleNamespace(__file__=str(tmp_path/'__init__.py')), 'numba': numba}
    result = runtime.runtime_record(modules, tmp_path, [{'num_threads': 1}])
    assert not result['errors'] and result['jit_disabled'] is True and result['numba_threads'] == 1
    assert runtime.runtime_record(modules, tmp_path/'other')['errors']
    assert runtime.runtime_record(modules, tmp_path, [{'num_threads': 2}])['errors']
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
