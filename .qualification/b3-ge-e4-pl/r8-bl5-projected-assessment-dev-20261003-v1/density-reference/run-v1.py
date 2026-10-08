from pathlib import Path
import hashlib, importlib.util, os, sys
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
RUNTIME=Path(r'C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
SOURCE_PIN='87a76f7ecd69133da5a955c7a59b1c8b8467be26c23f9b84cf619f9a3a45554b'
SOURCE=REPO/'scripts/r8_bl5_density_reference_dev.py'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
if sha(SOURCE)!=SOURCE_PIN:raise ValueError('frozen caller required')
supervisor=ROOT.parent/'r8-bl5-affine-flexible-v1/run.py'
if sha(supervisor)!='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':raise ValueError('same supervisor required')
spec=importlib.util.spec_from_file_location('bounded',supervisor);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
for key,value in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
    'NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1',
    'NUMEXPR_NUM_THREADS':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONPATH':str(REPO)}.items():m.ENV[key]=value
mode=sys.argv[1]
if mode=='test':
    command=[sys.executable,'-m','pytest','-q',str(REPO/'tests/test_r8_bl5_density_reference_dev.py'),
             '-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')]
    m.supervise(command,'test-v1',1024**3)
elif mode in ('s4','s2'):
    command=[str(RUNTIME),'-u',str(SOURCE),'--supports',mode[1:],'--case','mz',
             '--site',r'C:/Python/Python314/Lib/site-packages','--output-dir',str(ROOT/(mode+'-v1'))]
    m.supervise(command,mode+'-case-v1',2*1024**3)
elif mode=='compare':
    m.supervise([sys.executable,'-u',str(ROOT/'comparison-v1.py')],'compare-v1',1024**3)
else:raise ValueError('one declared serial stage required')
