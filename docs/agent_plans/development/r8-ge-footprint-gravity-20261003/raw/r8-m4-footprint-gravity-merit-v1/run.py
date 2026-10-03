from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
OLD=ROOT.parent/'r8-bl5-affine-flexible-v1/run.py'
s=importlib.util.spec_from_file_location('owned',OLD);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.ROOT=ROOT
m.ENV['PYTHONPATH']=str(REPO/'src')
m.supervise([sys.executable,'-m','pytest','-q',str(REPO/'tests/test_stiffened_shell_ge_footprint_gravity.py')+'::test_admitted_gravity_balance_and_selected_recovery[False]',str(REPO/'tests/test_stiffened_shell_ge_footprint_gravity.py')+'::test_full_actual_update_tangent_and_conservative_body_work','--basetemp',str(ROOT/'pytest-temp')],'focused-run',1024**3)
