from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np,pytest
from threadpoolctl import threadpool_info
from anysolver import _stiffened_shell_ge_distributing_finite as pose
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
assert Path(pose.__file__).resolve()==REPO/'src/anysolver/_stiffened_shell_ge_distributing_finite.py'
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
files=['src/anysolver/_stiffened_shell_ge_distributing_finite.py','tests/test_stiffened_shell_ge_distributing_finite_public.py','tests/test_stiffened_shell_ge_distributing_finite.py','tests/test_stiffened_shell_distributing_pose.py','src/anysolver/stiffened_shell.py','src/anysolver/_stiffened_shell_ge_checkpoint_binary.py','src/anysolver/_stiffened_shell_ge_body_load.py','src/anysolver/_stiffened_shell_ge_distributed_load.py','src/anysolver/_stiffened_shell_ge_pressure_load.py','src/anysolver/_stiffened_shell_ge_reference_modal.py','src/anysolver/_stiffened_shell_distributing_pose.py','src/anysolver/_stiffened_shell_ge_experimental.py','src/anysolver/_stiffened_shell_ge_finite_experimental.py','src/anysolver/_stiffened_shell_rotation_charts.py','src/anysolver/_stiffened_shell_distributing_footprint.py','src/anysolver/_ge_beam3_pose_joint.py','src/anysolver/_ge_beam3_mixed_ad.py','src/anysolver/_ge_beam3_p5/compensated_coordinates.py']
record=dict(scope='Experimental finite owner record/force/recovery/binary restart source integration; no F03/scientific qualification',source={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in files},imports=str(pose.__file__),pools=pools,jit_disabled=True)
out=ROOT/'runtime-v2.json';out.open('x').write(json.dumps(record,indent=2)+'\n');start=time.monotonic()
status=pytest.main(['-q',str(REPO/files[1]),str(REPO/files[2]),str(REPO/files[3]),*[str(REPO/'tests'/p) for p in ('test_stiffened_shell_distributing_footprint.py','test_stiffened_shell_ge_distributing_reference.py','test_stiffened_shell_ge_distributing_owner.py')],*[str(REPO/'tests/test_stiffened_shell_ge_finite_experimental.py')+'::'+n for n in ('test_finite_point_panel_accepts_two_complete_elastic_increments','test_binary_checkpoint_restores_finite_prefix_and_continues','test_rejected_and_cancelled_finite_trials_keep_accepted_prefix','test_generalized_beam_unload_reload_preserves_history_across_restart','test_q4_shell_and_beam_yield_atomically_and_restart')],'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v2')])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-start)
out.write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(status)
