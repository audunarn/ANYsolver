from pathlib import Path
import hashlib,importlib.util,os,sys
raw=Path(__file__).resolve().parent
runner=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(runner.read_bytes()).hexdigest()=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('bounded',runner)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.ROOT=raw;module.ENV=os.environ.copy();module.ENV.pop('PYTHONOPTIMIZE',None)
module.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
    NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
site=raw.parent/'r8-native-arc-dev-20261005-v1/site-v1'
module.ENV['PYTHONPATH']=os.pathsep.join((str(site),str(raw.parents[2])))
module.supervise([sys.executable,'-u',str(raw/'interpret-v2.py')],'interpret-v2',2*1024**3)
