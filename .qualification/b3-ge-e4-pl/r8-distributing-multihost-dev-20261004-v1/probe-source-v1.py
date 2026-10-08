from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np,pytest,anysolver
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
assert Path(anysolver.__file__).resolve().is_relative_to(REPO/'src')
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
files=['src/anysolver/_stiffened_shell_distributing_footprint.py','src/anysolver/_stiffened_shell_ge_distributing_reference.py','tests/test_stiffened_shell_distributing_footprint.py','tests/test_stiffened_shell_ge_distributing_reference.py','tests/test_stiffened_shell_ge_distributing_owner.py','scripts/r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_feasibility.py']
pools=threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
record=dict(scope='reference-linear multi-host source integration, not qualification',inputs={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in files},pools=pools,imported_anysolver=str(anysolver.__file__))
path=ROOT/'source-runtime-v1.json'
path.open('x').write(json.dumps(record,indent=2)+'\n')
start=time.monotonic()
status=pytest.main(['-q',*[str(REPO/p) for p in files[2:5]],'-p','no:cacheprovider','--basetemp',str(ROOT/'source-pytest-v1')])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-start)
path.write_text(json.dumps(record,indent=2)+'\n')
raise SystemExit(status)
