from pathlib import Path
from hashlib import sha256
import json,os,sys
import numpy,scipy,numba,llvmlite,psutil,anysolver
from threadpoolctl import threadpool_info
RAW=Path(__file__).resolve().parent
REPO=RAW.parents[2]
CI=REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
FILES=('src/anysolver/_stiffened_shell_b2_physical_rigid_footprint.py','src/anysolver/_stiffened_shell_b2_reference_buckling.py','src/anysolver/_stiffened_shell_b2_q4_panel_experimental.py','src/anysolver/stiffened_shell.py','tests/test_stiffened_shell_b2_physical_rigid_footprint.py','examples/stiffened_shell_b2_physical_rigid_footprint.py','examples/stiffened_shell_b2_reference_buckling.py','tests/test_stiffened_shell_b2_reference_buckling.py','tests/test_stiffened_shell_b2_nodal_rigid_footprint.py')
record=dict(python=sys.executable,imports={m.__name__:m.__file__ for m in (numpy,scipy,numba,llvmlite,anysolver)},versions={m.__name__:m.__version__ for m in (numpy,scipy,numba,llvmlite)},threadpools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_disabled=bool(numba.config.DISABLE_JIT),numba_threads=numba.get_num_threads(),environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT')},unforced_backend={k:os.environ.get(k) for k in ('OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES')},source_bindings={f:sha256((REPO/f).read_bytes()).hexdigest() for f in FILES})
(RAW/'effective-runtime-v4.json').write_text(json.dumps(record,indent=2)+'\n')
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve()),record
assert record['affinity']==[0] and record['jit_disabled'] and record['numba_threads']==1,record
assert all(p['num_threads']==1 for p in record['threadpools']),record
assert all(v=='1' for v in record['environment'].values()) and not any(record['unforced_backend'].values()),record
assert Path(anysolver.__file__).resolve().is_relative_to((REPO/'src').resolve()),record
for f in FILES:
    target=RAW/'source-snapshot-v4'/f;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((REPO/f).read_bytes())
os.environ["B2_FOOTPRINT_EXAMPLE_RECORD"]=str(RAW/"example-workflow-v4.json")
import pytest
code=pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(RAW/'pytest-temp-v4'),'--junitxml='+str(RAW/'junit-v4.xml'),'-k','nonzero_director_multiplier or new_family_point_coexistence or full_physical_kkt_wrench',str(REPO/'tests/test_stiffened_shell_b2_physical_rigid_footprint.py'),str(REPO/'tests/test_stiffened_shell_b2_nodal_rigid_footprint.py')+'::test_full_physical_kkt_wrench_and_prescribed_work'])
record['post_threadpools']=threadpool_info();record['post_numba_threads']=numba.get_num_threads()
record['actual_anysolver_imports']={k:v.__file__ for k,v in sys.modules.items() if k.startswith('anysolver') and getattr(v,'__file__',None)}
(RAW/'effective-runtime-post-v4.json').write_text(json.dumps(record,indent=2)+'\n')
raise SystemExit(code)





