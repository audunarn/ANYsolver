from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np,pytest
from threadpoolctl import threadpool_info
from anysolver import _stiffened_shell_distributing_pose as pose
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
assert Path(pose.__file__).resolve()==REPO/'src/anysolver/_stiffened_shell_distributing_pose.py'
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
files=['src/anysolver/_stiffened_shell_distributing_pose.py','tests/test_stiffened_shell_distributing_pose.py','src/anysolver/_stiffened_shell_distributing_footprint.py','src/anysolver/_ge_beam3_pose_joint.py','src/anysolver/_ge_beam3_mixed_ad.py','src/anysolver/_ge_beam3_p5/compensated_coordinates.py']
record=dict(scope='Private finite distributing pose/work feasibility, no owner/F03/qualification',source={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in files},imports=str(pose.__file__),pools=pools,jit_disabled=True)
out=ROOT/'runtime-v1.json';out.open('x').write(json.dumps(record,indent=2)+'\n');start=time.monotonic()
status=pytest.main(['-q',str(REPO/files[1]),'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-start)
out.write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(status)
