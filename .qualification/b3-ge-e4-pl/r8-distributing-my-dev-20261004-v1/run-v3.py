"""One independent My comparison, using the unchanged installed artifact."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
OLD=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert sha(p)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
m.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',BLIS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPATH=str(OLD/'site')+os.pathsep+str(REPO))
kind=sys.argv[1]
if kind not in ('native','ccx','compare'):raise ValueError('one declared job required')
if kind in ('native','ccx','compare'):
 binding=json.loads((ROOT/'binding-v3.json').read_text(encoding='utf-8'))
 for rel,expected in binding['sources'].items():assert sha(REPO/rel)==expected
 for rel,expected in binding['drivers'].items():assert sha(ROOT/rel)==expected
 for rel,expected in binding['prior_inputs'].items():assert sha(REPO/rel)==expected
 assert sha(Path(binding['executable']))==binding['executable_sha256']
 assert sha(ROOT/'ccx/reference.inp')==binding['deck_sha256']
if kind=='ccx':
 m.ROOT=ROOT/'ccx';command=[binding['executable'],'-i','reference'];kind='execution'
else:command=[sys.executable,'-u',str(ROOT/'probe-v3.py'),kind]
m.supervise(command,kind+'-v3',2*1024**3)
