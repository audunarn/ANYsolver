"""Installed-artifact origins, byte identity, runtime and exact test receipts."""
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys

BUNDLE = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((BUNDLE / 'MANIFEST.json').read_text())


def inspect_runtime():
    assert platform.system() == 'Windows' and sys.version_info[:2] == (3, 12)
    assert os.environ['ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS'] == '0'
    assert not os.environ.get('BEAM_SHELL_VERIFIED_PREFIX_EVIDENCE')
    assert not os.environ.get('PYTEST_PLUGINS'), 'no source fixture-reuse plugin'
    prefix = Path(sys.prefix).resolve()
    modules = {name: importlib.import_module(name) for name in (
        'anysolver', 'anysolver_results', 'anymaterial', 'anygeometry', 'anymesher', 'anyfileio')}
    origins = {name: str(Path(module.__file__).resolve()) for name, module in modules.items()}
    assert all(Path(path).is_relative_to(prefix) for path in origins.values())
    assert importlib.metadata.version('ANYsolver') == MANIFEST['version']
    site = Path(modules['anysolver'].__file__).resolve().parent.parent
    for name, digest in MANIFEST['source_files'].items():
        assert hashlib.sha256((site / name).read_bytes()).hexdigest() == digest, name
    for name, digest in MANIFEST['files'].items():
        assert hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest() == digest, name
    pins = {}
    for line in (BUNDLE / 'requirements-tested.txt').read_text().splitlines():
        name, expected = line.split('==')
        actual = importlib.metadata.version(name)
        assert actual == expected, (name, actual, expected)
        pins[name] = actual
    import numba
    from threadpoolctl import threadpool_info
    pools = threadpool_info()
    assert numba.config.DISABLE_JIT and numba.get_num_threads() == 1
    assert all(pool['num_threads'] == 1 for pool in pools)
    solver_origins = {name: str(Path(module.__file__).resolve())
        for name, module in list(sys.modules.items())
        if (name == 'anysolver' or name.startswith('anysolver.')) and getattr(module, '__file__', None)}
    assert all(Path(path).is_relative_to(prefix) for path in solver_origins.values())
    return dict(python=sys.version, executable=sys.executable, prefix=str(prefix),
        private_origins=origins, solver_origins=solver_origins, pins=pins,
        payload_files_verified=len(MANIFEST['source_files']), jit_disabled=True,
        numerical_threads=1, effective_pools=pools, retired_programme=False)


def pytest_sessionstart(session):
    session._installed_start = inspect_runtime()


def pytest_collection_modifyitems(session, config, items):
    session._installed_nodes = [item.nodeid for item in items]


def pytest_sessionfinish(session, exitstatus):
    record = dict(status='PASS' if int(exitstatus) == 0 else 'FAIL',
        collected=session.testscollected, failed=session.testsfailed,
        exit_code=int(exitstatus), node_ids=getattr(session, '_installed_nodes', []))
    try:
        record['runtime'] = inspect_runtime()
    except Exception as exc:
        record['runtime_error'] = repr(exc)
        session.exitstatus = 1
        record.update(status='FAIL', exit_code=1)
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    record['outcomes'] = {key: len(rows) for key, rows in reporter.stats.items()
        if key in ('passed', 'failed', 'skipped', 'error', 'xfailed', 'xpassed')}
    Path(os.environ['BEAM_SHELL_INSTALLED_RECORD']).write_text(json.dumps(record, indent=2) + '\n')
