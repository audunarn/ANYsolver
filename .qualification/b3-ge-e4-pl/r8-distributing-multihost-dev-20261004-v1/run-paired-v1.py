"""One serial bounded fixed-pad development job; no formal F03 authority."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
m.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',BLIS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
m.ENV['PYTHONPATH']=os.pathsep.join((str(ROOT/'site'),str(REPO)))
kind=sys.argv[1]
if kind in ('prepare','parse'):
 command=[sys.executable,'-u',str(ROOT/'probe-paired-v1.py'),kind]
elif kind=='native' and len(sys.argv)==4:
 nx,ny=map(int,sys.argv[2:]);assert (nx,ny) in ((10,4),(20,8),(40,16))
 kind=f'native-{nx}x{ny}'
 command=[sys.executable,'-u',str(ROOT/'probe-paired-v1.py'),'native',str(nx),str(ny)]
elif kind=='ccx' and len(sys.argv)==5:
 nx,ny=map(int,sys.argv[2:4]);name=sys.argv[4];assert (nx,ny) in ((10,4),(20,8),(40,16)) and name in ('Mx','Fy')
 ccx=Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
 assert hashlib.sha256(ccx.read_bytes()).hexdigest()=='27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
 case=ROOT/f'ccx-{nx}x{ny}-{name}-v1';binding=json.loads((ROOT/'paired-binding-v1.json').read_text())
 assert hashlib.sha256((case/'reference.inp').read_bytes()).hexdigest()==binding['cases'][f'{nx}x{ny}-{name}']['deck_sha256']
 m.ROOT=case;kind='execution'
 command=[str(ccx),'-i','reference']
else:raise ValueError('one declared paired job required')
m.supervise(command,kind+'-v1',2*1024**3)
