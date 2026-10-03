from pathlib import Path
import importlib.util,os,sys
ROOT=Path(__file__).resolve().parent
REPO=Path(r"C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
SITE=Path(os.environ['TEMP'])/'r8-bl5-projected-joint32-v2/site'
WHEEL=SITE.parent/'dist/anysolver-0.4.7-py3-none-any.whl'
SHA='1bf7dabd8771e76ed09825fb66a89e3e48d513dbb0321989c41701096a679632'
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ROOT=ROOT;m.ENV=os.environ.copy()
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTHONPATH':os.pathsep.join(map(str,(SITE,REPO,REPO/'scripts',REPO/'tests')))}.items():m.ENV[k]=v
case,stage=sys.argv[1:]
if case not in ('whole_half','whole_double'):raise ValueError(case)
folder=ROOT/case;folder.mkdir(exist_ok=True)
reg=folder/'registration-v1.json';owner=folder/'owner-v1'
base=[sys.executable,'-u']
if stage=='register':
 cmd=base+[str(REPO/'scripts/r8_bl5_projected_ratio_norm_dev.py'),'register','--case',case,'--output',str(reg)]
elif stage=='owner':
 cmd=base+[str(REPO/'scripts/r8_bl5_projected_ratio_owner_dev.py'),'--case',case,'--site',str(SITE),'--wheel',str(WHEEL),'--wheel-sha',SHA,'--source',str(REPO),'--registration',str(reg),'--output-dir',str(owner)]
elif stage=='norm':
 cmd=base+[str(REPO/'scripts/r8_bl5_projected_ratio_norm_dev.py'),'assess','--case',case,'--root',str(owner),'--registration',str(reg),'--wheel',str(WHEEL),'--output',str(folder/'norm-v1.json')]
elif stage=='kernel':
 cmd=base+[str(REPO/'scripts/r8_bl5_projected_ratio_kernel_dev.py'),'--root',str(owner),'--output',str(folder/'kernel-v1.json')]
else:raise ValueError(stage)
m.supervise(cmd,case+'-'+stage+'-v1',1024**3)
