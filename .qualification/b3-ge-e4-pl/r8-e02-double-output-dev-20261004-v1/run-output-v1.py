from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parent
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b=json.loads((ROOT/'binding.json').read_text());exe=Path(b['executable'])
assert hashlib.sha256(exe.read_bytes()).hexdigest()==b['executable_sha256']
assert hashlib.sha256((ROOT/'ccx/reference.inp').read_bytes()).hexdigest()==b['deck_sha256']
m.ROOT=ROOT/'ccx';m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
m.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',CCX_NPROC_RESULTS='1',CCX_NPROC_EQUATION_SOLVER='1')
m.supervise([str(exe),'-i','reference'],'execution-v1',2*1024**3)
