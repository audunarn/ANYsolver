from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parent
REPO=Path('C:\\Github\\ANYsolver\\.perf2-worktrees\\stiffened-main-reconcile-20261001')
spec=importlib.util.spec_from_file_location('bounded',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
mode=sys.argv[1]
if mode=='focused':
 m.ENV['PYTHONPATH']=str(REPO/'src')
 m.supervise([sys.executable,'-m','pytest','-q',str(REPO/'tests/test_stiffened_shell_ge_experimental.py'),'-k','linear_load_cases or linear_refinement'],'focused',1024**3)
elif mode=='build':
 m.supervise([sys.executable,'-m','build','--wheel','--no-isolation','--outdir',str(ROOT/'dist'),str(REPO)],'build',1024**3)
elif mode=='install':
 wheel=next((ROOT/'dist').glob('*.whl'))
 m.supervise([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(ROOT/'site'),str(wheel)],'install',1024**3)

elif mode=='installed':
 m.ENV['PYTHONPATH']=str(ROOT/'site')
 m.supervise([sys.executable,str(ROOT/'check-installed.py')],'installed',1024**3)
elif mode=='installed-affected':
 m.ENV['PYTHONPATH']=str(ROOT/'site')+';'+str(REPO)
 m.supervise([sys.executable,str(ROOT/'check-installed-missing-helpers.py')],'installed-affected',1024**3)
