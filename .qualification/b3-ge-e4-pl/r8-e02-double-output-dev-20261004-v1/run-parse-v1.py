from pathlib import Path
import hashlib, importlib.util, os, sys
ROOT = Path(__file__).resolve().parent
p = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
s = importlib.util.spec_from_file_location('bounded', p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
m.ROOT = ROOT; m.ENV = os.environ.copy(); m.ENV.pop('PYTHONOPTIMIZE', None)
m.ENV.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
    NUMBA_NUM_THREADS='1', NUMBA_DISABLE_JIT='1')
m.supervise([sys.executable, str(ROOT/'parse-v1.py')], 'parse-execution-v1', 2*1024**3)
