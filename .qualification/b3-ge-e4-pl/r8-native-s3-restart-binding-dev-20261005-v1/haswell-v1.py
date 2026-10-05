"""One fresh Haswell fixed-coordinate discriminator, no coretype sweep."""
from pathlib import Path
import hashlib, importlib.util, json, os, sys
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded',BASE)
s = importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT = ROOT;s.ENV.pop('PYTHONOPTIMIZE',None)
s.ENV.update(NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1',OPENBLAS_CORETYPE='Haswell')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(ROOT/'ci-site-network-v2'),str(REPO/'src'),str(REPO)))
(ROOT/'haswell-binding-v1.json').write_text(json.dumps(dict(runner_sha256=sha(__file__),
    entry_sha256=sha(ROOT/'haswell-entry-v1.py'),supervisor_sha256=sha(BASE),
    source_binding_sha256=sha(ROOT/'backend-ci-binding-v2.json'),
    unforced_reference_sha256=sha(ROOT/'eigenvalue-witness-v1.json'),
    scope='One fixed-coordinate Haswell CPU-dispatch discriminator; no replay or changes'),indent=2)+'\n')
s.supervise([sys.executable,str(ROOT/'haswell-entry-v1.py')],'haswell-v1',2*1024**3)
