from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
STAGES={'16':('ns16_b1_4','ns16_b1_2','ns16_b1','ns16_b2','ns16_b4'),
        '32':('ns32_b1_4','ns32_b1_2','ns32_b1','ns32_b4','ns32_b8'),
        '64':('ns64_b1_8','ns64_b1_4','ns64_b1_2','ns64_b1','ns64_b2','ns64_b4','ns64_b8')}
if len(sys.argv)!=2 or sys.argv[1] not in STAGES:raise ValueError('one bounded registered stage required')
p=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
if hashlib.sha256(p.read_bytes()).hexdigest()!='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':raise ValueError('pinned supervisor required')
s=importlib.util.spec_from_file_location('bounded',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.ENV=os.environ.copy();m.ENV.pop('PYTHONOPTIMIZE',None)
for k,v in {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMBA_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1','VECLIB_MAXIMUM_THREADS':'1','BLIS_NUM_THREADS':'1','PYTHONPATH':str(REPO)}.items():m.ENV[k]=v
b=json.loads((ROOT/'bindings-batch-v1.json').read_text())
if hashlib.sha256((ROOT/'probe-batch-v1.py').read_bytes()).hexdigest()!=b['driver_sha256']:raise ValueError('reviewed batch driver differs')
stage=ROOT/f'stage-{sys.argv[1]}-v1.json'
if stage.exists():raise ValueError('fresh stage evidence required')
results=[];failure=None;current=None;stop_requested=False
try:
    for case in STAGES[sys.argv[1]]:
        current=case
        if (ROOT/'STOP').exists():
            stop_requested=True
            break
        folder=ROOT/'campaign-v1'/case
        folder.mkdir(parents=True,exist_ok=False)
        m.ROOT=folder
        m.supervise([sys.executable,'-u',str(ROOT/'probe-batch-v1.py'),case],'run-v1',2*1024**3)
        result=json.loads((folder/'kernel-v1.json').read_text())
        results.append({'case':case,'status':result['status']})
        if result['status']!='POSITIVE_ENVELOPE_MECHANICAL_KERNEL_DEVELOPMENT_ONLY':raise RuntimeError('stage stops on unresolved case '+case)
except BaseException as error:
    failure={'case':current,'type':type(error).__name__,'message':str(error)}
    raise
finally:
    stage.write_text(json.dumps({'cases':results,'failure':failure,'stop_requested':stop_requested,'complete':len(results)==len(STAGES[sys.argv[1]]) and failure is None and all(r['status']=='POSITIVE_ENVELOPE_MECHANICAL_KERNEL_DEVELOPMENT_ONLY' for r in results)},indent=2)+'\n',newline='\n')
