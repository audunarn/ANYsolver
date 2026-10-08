from pathlib import Path
import hashlib,importlib.util,os,sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
m.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',BLIS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
kind=sys.argv[1]
if kind in ('build','fem-build'):
 m.ENV.pop('PYTHONPATH',None)
 command=[sys.executable,'-m','build','--wheel','--no-isolation','--outdir',str(ROOT/('fem-dist' if kind=='fem-build' else 'dist')),str(Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer') if kind=='fem-build' else REPO)]
elif kind in ('install','fem-install'):
 m.ENV.pop('PYTHONPATH',None);wheel,=(ROOT/('fem-dist' if kind=='fem-install' else 'dist')).glob('*.whl')
 target=ROOT/('fem-site' if kind=='fem-install' else 'site');assert not target.exists()
 command=[sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(target),str(wheel)]
elif kind in ('installed','consumer','example','consumer-source'):
 m.ENV['PYTHONPATH']=os.pathsep.join((str(ROOT/'site'),str(REPO),str(ROOT/'fem-site')))
 m.ENV['R8_MULTIH_HOST_KIND']=kind
 if kind=='consumer-source':m.ENV['PYTHONPATH']=os.pathsep.join((str(REPO/'src'),'C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src',str(REPO),str(REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1/site')))
 command=[sys.executable,'-u',str(ROOT/'probe-boundary-v1.py')]
else:raise ValueError('declared boundary action required')
m.supervise(command,kind+'-v1',2*1024**3)
