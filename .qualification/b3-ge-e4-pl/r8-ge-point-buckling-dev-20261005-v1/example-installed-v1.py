"""Serial installed public-example execution; development evidence only."""
from pathlib import Path
import hashlib, importlib.util, json, os, sys

root = Path(__file__).resolve().parent
repo = root.parents[2]
base = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(base) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
binding = json.loads((root/'binding-v1.json').read_text())
assert all(sha(repo/name) == digest for name, digest in binding['files'].items())
assert json.loads((root/'installed-result-v1.json').read_text())['pytest_exit'] == 0
spec = importlib.util.spec_from_file_location('bounded', base)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)
supervisor.ROOT = root
supervisor.ENV.pop('PYTHONOPTIMIZE', None)
supervisor.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1',
    PYTHONPATH=os.pathsep.join((str(root/'site-v1'), str(repo))))
script = repo/'scripts/r8_ge_point_buckling_dev.py'
(root/'example-binding-v1.json').write_text(json.dumps(dict(
    script_sha256=sha(script), source_binding_sha256=sha(root/'binding-v1.json'),
    artifacts_sha256=sha(root/'artifact-v1.json'), scope='Installed compression development example; not G4B acceptance'), indent=2)+'\n')
supervisor.supervise([sys.executable, str(script), '--output',
    str(root/'example-compression-installed-v1'), '--case', 'compression', '--count', '2'],
    'example-installed-v1', 2*1024**3)
