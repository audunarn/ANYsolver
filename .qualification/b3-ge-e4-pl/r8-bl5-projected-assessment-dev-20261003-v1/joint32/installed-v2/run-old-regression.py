from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parent
REPO=Path('C:\\Github\\ANYsolver\\.perf2-worktrees\\stiffened-main-reconcile-20261001')
spec=importlib.util.spec_from_file_location('bounded',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
m.ENV['PYTHONPATH']=str(ROOT.parent/'r8-bl5-projected-integration-v1/site')
m.supervise([sys.executable,'-m','pytest','-q','-c',str(ROOT/'pytest.ini'),str(ROOT/'fixtures/test_stiffened_shell_ge_experimental.py')+'::test_linear_refinement_recovers_a_roundoff_sized_response_error[0.2]'],'old-wheel-regression',1024**3)
