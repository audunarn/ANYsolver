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
    ticks = [0.]
    monkeypatch.setattr(runner.time, 'monotonic', lambda: ticks[0])
    monkeypatch.setattr(runner.time, 'sleep', lambda _: ticks.__setitem__(0, 2.))
    terminated = []
    monkeypatch.setattr(runner, '_terminate_tree', terminated.append)
    assert runner.run(workers=1, timeout_seconds=1, development_targets=['tests/test_x.py']) == runner.TIMEOUT_EXIT_CODE
    assert terminated == [process]
    record = json.loads(next((tmp_path/'temp').glob('*/P01/resource.json')).read_text())
    assert record['status'] == 'timeout' and record['child_exit_codes'] == [-1]


def test_queue_enforces_process_ceiling_and_preserves_every_partition(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    partitions = (('one.py',), ('two.py',), ('three.py',), ('four.py',), ('five.py',))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: tuple(p[0] for p in partitions))
    monkeypatch.setattr(runner, 'execution_partitions', lambda *a: partitions)
    clock = [0.]
    monkeypatch.setattr(runner.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: clock.__setitem__(0, clock[0]+seconds))
    launched = []
    class Process:
        def __init__(self, command):
            assert sum(p.poll() is None for p in launched) < 2
            self.command, self.finish, self.returncode = command, clock[0]+.15, None
        def poll(self):
            if clock[0] >= self.finish: self.returncode = 0
            return self.returncode
    def launch(command, **kwargs):
        process = Process(command)
        launched.append(process)
        return process
    monkeypatch.setattr(runner.subprocess, 'Popen', launch)
    assert runner.run(workers=2, timeout_seconds=2) == 0
    assert [p.command[-1] for p in launched] == [p[0] for p in partitions]


def test_queued_work_cannot_launch_after_shared_deadline(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path/'temp'))
    monkeypatch.setattr(runner, 'merge_test_modules', lambda: ('one.py', 'two.py'))
    monkeypatch.setattr(runner, 'execution_partitions', lambda *a: (('one.py',), ('two.py',)))
    clock = [0.]
    monkeypatch.setattr(runner.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: clock.__setitem__(0, 2.))
    process = SimpleNamespace(poll=lambda: None, returncode=None)
    launched, terminated = [], []
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *a, **k: launched.append(a[0]) or process)
    monkeypatch.setattr(runner, '_terminate_tree', terminated.append)
    assert runner.run(workers=1, timeout_seconds=1) == runner.TIMEOUT_EXIT_CODE
    assert len(launched) == 1 and terminated == [process]


@pytest.mark.parametrize('dependency_filename', ['dependency.py', 'dependency.pyd'])
def test_cache_key_tracks_content_even_with_restored_times_and_dependency_versions(tmp_path, monkeypatch, dependency_filename):
    import os
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'src').mkdir()
    source = tmp_path/'src/kernel.py'
    source.write_text('x = 1\n')
    dependency_source = tmp_path/dependency_filename
    dependency_source.write_text('x = 1\n')
    version = ['1.0']
    distribution = SimpleNamespace(metadata={'Name': 'numba'}, locate_file=lambda name: tmp_path/name,
                                   read_text=lambda name: dependency_filename+',,\n' if name == 'RECORD' else None)
    class Distribution:
        metadata = distribution.metadata
        locate_file = staticmethod(distribution.locate_file)
        read_text = staticmethod(distribution.read_text)
        files = [Path(dependency_filename)]
        @property
        def version(self): return version[0]
    monkeypatch.setattr(runner.importlib.metadata, 'distributions', lambda: [Distribution()])
    environment = lambda: {'NUMBA_DISABLE_JIT': '0', 'NUMBA_NUM_THREADS': '1'}
    first = runner._development_cache(environment(), tmp_path/'cache')
    assert first == runner._development_cache(environment(), tmp_path/'cache')
    before = source.stat()
    source.write_text('x = 2\n')
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    changed = runner._development_cache(environment(), tmp_path/'cache')
    assert changed['key'] != first['key']
    version[0] = '2.0'
    assert runner._development_cache(environment(), tmp_path/'cache')['key'] != changed['key']
    before_dependency_change = runner._development_cache(environment(), tmp_path/'cache')
    dependency_source.write_text('x = 2\n')
    assert runner._development_cache(environment(), tmp_path/'cache')['key'] != before_dependency_change['key']
    modified = environment(); modified['NUMBA_CPU_NAME'] = 'generic'
    assert runner._development_cache(modified, tmp_path/'cache')['key'] != changed['key']


def test_cache_records_unused_editable_dependency_and_runtime_rejects_its_import(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    distribution = SimpleNamespace(metadata={'Name': 'numpy'}, version='1', locate_file=lambda _: tmp_path,
        files=None,
        read_text=lambda name: json.dumps({'url': (tmp_path/'external').as_uri(), 'dir_info': {'editable': True}})
        if name == 'direct_url.json' else 'numpy' if name == 'top_level.txt' else None)
    monkeypatch.setattr(runner.importlib.metadata, 'distributions', lambda: [distribution])
    cache = runner._development_cache({}, tmp_path/'cache')
    assert cache['enabled'] and cache['unbound_dependencies'][0]['name'] == 'numpy'
    assert not runtime.runtime_record({}, tmp_path, compilation_cache=cache)['errors']
    by_path = {'foreign_alias': SimpleNamespace(__file__=str(tmp_path/'external/submodule.py'))}
    result = runtime.runtime_record(by_path, tmp_path, compilation_cache=cache)
    assert result['unbound_dependency_imports'][0]['modules'] == ['foreign_alias']
    assert 'rerun with cold' in result['errors'][0]
    by_shim = {'numpy': SimpleNamespace(__file__=str(tmp_path/'site-packages/numpy.py'))}
    assert runtime.runtime_record(by_shim, tmp_path, compilation_cache=cache)['errors']
    assert not runtime.runtime_record(by_shim, tmp_path, compilation_cache={'enabled': False})['errors']


@pytest.mark.parametrize('has_inventory', [False, True])
def test_unbound_installed_package_guard_does_not_cover_shared_site(tmp_path, monkeypatch, has_inventory):
    monkeypatch.setattr(runner, 'ROOT', tmp_path/'checkout')
    (tmp_path/'checkout').mkdir()
    site = tmp_path/'site-packages'
    distribution = SimpleNamespace(metadata={'Name': 'UnrelatedNative'}, version='1',
        locate_file=lambda name: site/name,
        files=[Path('foreignnative/ext.pyd')] if has_inventory else None,
        read_text=lambda name: 'foreignnative' if name == 'top_level.txt' else 'foreignnative/ext.pyd,,\n'
        if name == 'RECORD' and has_inventory else None)
    monkeypatch.setattr(runner.importlib.metadata, 'distributions', lambda: [distribution])
    cache = runner._development_cache({}, tmp_path/'cache')
    assert cache['enabled'] and cache['dependency_bytes_hashed'] == 0
    assert cache['unbound_dependencies'][0]['name'] == 'UnrelatedNative'
    unrelated = {'numpy': SimpleNamespace(__file__=str(site/'numpy/__init__.py'))}
    assert not runtime.runtime_record(unrelated, tmp_path, compilation_cache=cache)['errors']
    alias = {'arbitrary_alias': SimpleNamespace(__file__=str(site/'foreignnative/ext.pyd'))}
    assert runtime.runtime_record(alias, tmp_path, compilation_cache=cache)['errors']
    shim = {'foreignnative': SimpleNamespace(__file__=str(tmp_path/'different-shim.py'))}
    assert runtime.runtime_record(shim, tmp_path, compilation_cache=cache)['errors']


def test_duplicate_distribution_instances_all_remain_content_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path/'checkout')
    (tmp_path/'checkout').mkdir()
    distributions = []
    for index in (1, 2):
        location = tmp_path/f'site{index}'
        location.mkdir(); (location/'kernel.pyd').write_bytes(b'first')
        distributions.append(SimpleNamespace(metadata={'Name': 'numpy'}, version='1',
            files=[Path('kernel.pyd')], locate_file=lambda name, location=location: location/name,
            read_text=lambda name: 'kernel.pyd,,\n' if name == 'RECORD' else None))
    monkeypatch.setattr(runner.importlib.metadata, 'distributions', lambda: distributions)
    first = runner._development_cache({}, tmp_path/'cache')
    (tmp_path/'site1/kernel.pyd').write_bytes(b'second')
    assert runner._development_cache({}, tmp_path/'cache')['key'] != first['key']


def test_compilation_cache_keeps_bytecode_cold_and_per_invocation(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner.importlib.metadata, 'distributions', lambda: [])
    environment = runner._worker_environment(tmp_path/'invocation')
    original_prefix = environment['PYTHONPYCACHEPREFIX']
    cache = runner._development_cache(environment, tmp_path/'cache')
    assert cache['enabled'] and cache['watched_root'] == str(tmp_path)
    assert environment['PYTHONDONTWRITEBYTECODE'] == '1'
    assert environment['PYTHONPYCACHEPREFIX'] == original_prefix
    assert environment['NUMBA_CACHE_DIR'] != str(tmp_path/'invocation/numba-cache')


def test_cache_runtime_resolves_origins_once_and_rejects_unwatched_repository_helpers(tmp_path, monkeypatch):
    original_resolve = Path.resolve
    calls = []
    def recorded_resolve(path, *args, **kwargs):
        calls.append(str(path))
        return original_resolve(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'resolve', recorded_resolve)
    modules = {'helper': SimpleNamespace(__file__=str(tmp_path/'checkout/docs/helper.py')),
               'stdlib': SimpleNamespace(__file__=str(tmp_path/'python/lib/helper.py'))}
    cache = {'enabled': True, 'watched_root': str(tmp_path/'checkout'), 'unbound_dependencies': [
        {'name': f'Unused{i}', 'root': str(tmp_path/f'external{i}'), 'top_levels': [f'unused{i}']}
        for i in range(5)]}
    result = runtime.runtime_record(modules, tmp_path/'checkout/src/anysolver', compilation_cache=cache)
    assert len(calls) == len(modules)
    assert len(result['errors']) == 1 and 'outside watched source: helper;' in result['errors'][0]
    assert not runtime.runtime_record(modules, tmp_path/'checkout/src/anysolver',
                                     compilation_cache={'enabled': False})['errors']


def test_cache_does_not_read_protected_sources(tmp_path, monkeypatch):
    import os
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner.importlib.metadata, 'distributions', lambda: [])
    protected = tmp_path/'scripts/US3-modal-canary'
    protected.mkdir(parents=True)
    (protected/'secret.py').write_text('one')
    (tmp_path/'scripts/b3_e4_f03_c1_fy_supported_reference.py').write_text('one')
    original_walk, original_read = os.walk, Path.read_bytes
    def guarded_walk(*args, **kwargs):
        for folder, directories, files in original_walk(*args, **kwargs):
            assert 'us3-modal-canary' not in {part.casefold() for part in Path(folder).parts}
            yield folder, directories, files
    def guarded_read(path):
        assert 'us3-modal-canary' not in {part.casefold() for part in path.parts}
        assert path.name != 'b3_e4_f03_c1_fy_supported_reference.py'
        return original_read(path)
    monkeypatch.setattr(runner.os, 'walk', guarded_walk)
    monkeypatch.setattr(Path, 'read_bytes', guarded_read)
    first = runner._development_cache({}, tmp_path/'cache')
    (protected/'secret.py').write_text('two')
    (tmp_path/'scripts/b3_e4_f03_c1_fy_supported_reference.py').write_text('two')
    assert runner._development_cache({}, tmp_path/'cache')['key'] == first['key']


def test_protected_development_target_is_denied_before_path_inspection(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    def denied_resolve(*args, **kwargs):
        raise AssertionError('protected path was inspected')
    monkeypatch.setattr(Path, 'resolve', denied_resolve)
    with pytest.raises(ValueError, match='protected'):
        runner._development_targets(['tests/US3-modal-canary/not-even-present.py'])


@pytest.mark.parametrize('directory', ['src', 'src/linked'])
def test_cache_refuses_source_directory_aliases_before_descent(tmp_path, monkeypatch, directory):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'src/linked').mkdir(parents=True)
    original_is_symlink = Path.is_symlink
    def simulated_alias(path):
        return path == tmp_path/directory or original_is_symlink(path)
    monkeypatch.setattr(Path, 'is_symlink', simulated_alias)
    with pytest.raises(RuntimeError, match='source directory symlinks'):
        runner._development_cache({}, tmp_path/'cache')


def test_profiles_are_explicit_exact_and_reject_empty_unknown(tmp_path, monkeypatch):
    actual = runner._profile_targets('contact-smoke')
    assert actual == ('tests/test_fe_solver_contact.py::test_sphere_contact_load_resultant_and_nodal_distribution',
                      'tests/test_general_contact_beam_chain_consistent.py::test_capability_does_not_admit_development_or_foreign_geometry')
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'scripts').mkdir()
    (tmp_path/'scripts/development_test_profiles.json').write_text('{"empty": []}')
    with pytest.raises(ValueError, match='unknown'): runner._profile_targets('missing')
    with pytest.raises(ValueError, match='nonempty'): runner._profile_targets('empty')
    with pytest.raises(ValueError, match='targets or a profile'):
        runner.run(workers=1, timeout_seconds=1, development_targets=[], development_profile='empty')


def test_node_timings_preserve_failed_setup_and_teardown_outcomes(monkeypatch):
    with monkeypatch.context() as isolated:
        isolated.setattr(runtime, "_timings", {})
        runtime.pytest_sessionstart(None)
        runtime.pytest_collection(None)
        runtime.pytest_collectreport(SimpleNamespace(nodeid='test_x.py', outcome='passed'))
        runtime.pytest_collection_finish(None)
        for phase, outcome in [('setup', 'failed'), ('teardown', 'passed')]:
            runtime.pytest_runtest_logreport(SimpleNamespace(nodeid='test_x.py::test_x', when=phase,
                                                           outcome=outcome, duration=.25))
        assert runtime._timings['collection_seconds'] >= 0
        assert [(row['phase'], row['outcome'], row['duration_seconds']) for row in runtime._timings['nodes']] == [
            ('setup', 'failed', .25), ('teardown', 'passed', .25)]


def test_current_inventory_is_disjoint_complete_and_fails_future_unknown(tmp_path, monkeypatch):
    record = runner._current_development_inventory()
    assert 'tests/test_performance_contact_chain_comparison.py' in record['performance']
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'scripts').mkdir(); (tmp_path/'tests').mkdir()
    record = {'schema': 'anysolver.development-test-intent.v1', 'portable': [], 'performance': [], 'extended': []}
    (tmp_path/'scripts/development_test_inventory.json').write_text(json.dumps(record))
    assert runner._current_development_inventory() == record
    (tmp_path/'tests/test_general_contact_new.py').write_text('')
    with pytest.raises(RuntimeError, match='incomplete'): runner._current_development_inventory()


def test_current_performance_intent_excludes_new_plain_name_only_from_ci(tmp_path, monkeypatch):
    name = 'tests/test_general_contact_plain.py'
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'tests').mkdir(); (tmp_path/name).write_text('')
    monkeypatch.setattr(runner, '_ge_beam3_inventory', lambda: {})
    monkeypatch.setattr(runner, '_current_development_inventory', lambda: {
        'portable': ['tests/test_regular.py'], 'performance': [name], 'extended': []})
    monkeypatch.setattr(runner, 'inventory', lambda: {
        'quick': ['tests/test_regular.py', name], 'additive': [], 'functional': []})
    monkeypatch.setattr(runner, 'POST_CLOSEOUT_HISTORICAL_MODULES', ())
    monkeypatch.setattr(runner, 'PORTABLE_CURRENT_S3_SUCCESSOR_MODULES', ())
    assert runner.merge_test_modules() == ('tests/test_regular.py',)
    assert runner._development_targets([name]) == (name,)
