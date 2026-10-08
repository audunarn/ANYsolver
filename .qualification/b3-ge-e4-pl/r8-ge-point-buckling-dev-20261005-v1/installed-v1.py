from pathlib import Path
import hashlib, importlib.metadata, json, os, sys
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer
raw = Path(__file__).resolve().parent
repo = raw.parents[2]
site = raw/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT'] == '1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads'] == 1 for p in threadpool_info())
sources = {}
for source in (repo/'src/anysolver').rglob('*.py'):
    name = source.relative_to(repo/'src').as_posix()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert hashlib.sha256((site/name).read_bytes()).hexdigest() == digest, name
    sources[name] = digest
artifacts = json.loads((raw/'artifact-v1.json').read_text())['artifacts']
for item in artifacts.values():
    assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest() == item['sha256']
dependencies = {}
for name in ('numpy', 'scipy', 'anysolver', 'anyfem', 'anymaterial'):
    try:
        dependencies[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        dependencies[name] = 'not installed as distribution'
record = dict(status='IN_PROGRESS', artifacts=artifacts, sources=sources,
    solver_site=str(Path(ss.__file__).resolve()), consumer_site=str(Path(consumer.__file__).resolve()),
    dependencies=dependencies, pools=threadpool_info(), qualified=False)
def save():
    (raw/'installed-result-v1.json').write_text(json.dumps(record, indent=2)+'\n')
save()
status = pytest.main(['-q', '-p', 'no:cacheprovider', '--basetemp', str(raw/'pytest-temp-installed-v1'),
    str(repo/'tests/test_stiffened_shell_ge_point_buckling.py'),
    str(repo/'tests/test_stiffened_shell_q4_algorithmic_pullback.py'),
    '--junitxml='+str(raw/'installed-junit-v1.xml')])
record.update(pytest_exit=status, status='FAILED_TESTS' if status else 'PASSED_INSTALLED_DEVELOPMENT_NOT_QUALIFIED')
save()
raise SystemExit(status)
