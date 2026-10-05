"""One serial supervised eigensolver witness; no product or fixture mutation."""
from pathlib import Path
import hashlib, importlib.util, os, sys
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT = ROOT; s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(REPO/'src'), str(REPO)))
s.supervise([sys.executable,str(ROOT/'eigenvalue-witness-v1.py')], 'diagnostic-v1', 2*1024**3)
