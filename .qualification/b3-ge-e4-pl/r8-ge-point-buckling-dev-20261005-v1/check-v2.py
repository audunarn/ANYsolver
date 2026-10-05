"""Fresh source/installed checks for review-driven test coverage additions."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys

root = Path(__file__).resolve().parent
repo = root.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mode = sys.argv[1]
assert mode in ('source', 'installed')
binding = json.loads((root/'binding-v1.json').read_text())
assert all(sha(repo/name) == digest for name, digest in binding['files'].items()
    if name.startswith('src/'))
test = repo/'tests/test_stiffened_shell_ge_point_buckling.py'
if mode == 'source':
    folder = root/'executed-source-v2'
    folder.mkdir(exist_ok=False)
    shutil.copyfile(test, folder/test.name)
    (root/'binding-v2.json').write_text(json.dumps(dict(test_sha256=sha(test),
        unchanged_product_binding_sha256=sha(root/'binding-v1.json'),
        scope='Review-driven failure and ownership coverage; same v1 product and wheel'), indent=2)+'\n')
else:
    assert sha(test) == json.loads((root/'binding-v2.json').read_text())['test_sha256']
    assert json.loads((root/'source-v2/execution.json').read_text())['exit_code'] == 0
    for name, digest in json.loads((root/'installed-result-v1.json').read_text())['sources'].items():
        assert sha(repo/'src'/name) == digest
        assert sha(root/'site-v1'/name) == digest
base = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert sha(base) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', base)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)
supervisor.ROOT = root
supervisor.ENV.pop('PYTHONOPTIMIZE', None)
supervisor.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1',
    PYTHONPATH=os.pathsep.join((str(repo/'src' if mode == 'source' else root/'site-v1'), str(repo))))
supervisor.supervise([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
    '--basetemp', str(root/('pytest-temp-'+mode+'-v2')),
    '--junitxml='+str(root/(mode+'-junit-v2.xml')), str(test)], mode+'-v2', 2*1024**3)
