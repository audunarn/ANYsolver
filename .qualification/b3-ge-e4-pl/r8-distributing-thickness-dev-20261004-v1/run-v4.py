"""One bounded orthogonal diagnostic pair; no formal qualification execution."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
m.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',BLIS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
m.ENV['PYTHONPATH']=str(REPO)
kind=sys.argv[1]
if kind=='parse':
 binding=json.loads((ROOT/'binding-v4.json').read_text(encoding='utf-8'))
 for rel,expected in binding['drivers'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected
 assert hashlib.sha256(Path(binding['prior_comparison']).read_bytes()).hexdigest()==binding['prior_comparison_sha256']

 command=[sys.executable,'-u',str(ROOT/'probe-v4.py'),kind]
elif kind=='ccx' and len(sys.argv)==3 and sys.argv[2] in ('Mx','Fy'):
 name=sys.argv[2];binding=json.loads((ROOT/'binding-v4.json').read_text(encoding='utf-8'))

 for rel,expected in binding['drivers'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected
 assert hashlib.sha256(Path(binding['prior_comparison']).read_bytes()).hexdigest()==binding['prior_comparison_sha256']
 for rel,expected in binding['sources'].items():assert hashlib.sha256((REPO/rel).read_bytes()).hexdigest()==expected
 ccx=Path(binding['executable']);assert hashlib.sha256(ccx.read_bytes()).hexdigest()==binding['executable_sha256']
 case=ROOT/('ccx-'+name+'-v1');assert hashlib.sha256((case/'reference.inp').read_bytes()).hexdigest()==binding['cases'][name]['deck_sha256']
 assert binding['cases'][name]['rows']<=100000 and binding['cases'][name]['elements']==2560
 m.ROOT=case;kind='execution';command=[str(ccx),'-i','reference']
else:raise ValueError('declared single diagnostic job required')
m.supervise(command,kind+'-v4',2*1024**3)
