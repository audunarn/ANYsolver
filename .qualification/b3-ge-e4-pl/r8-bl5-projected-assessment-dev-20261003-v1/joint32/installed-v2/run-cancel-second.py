from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
repo=Path("C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
site=root/"site"
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=";".join(map(str,(site,repo,repo/"scripts",repo/"tests")))
m.ENV['PYTHONPATH']=str(root/'site')
m.supervise(['C:/Python/Python314/python.exe','-m','pytest','-q','-c',str(root/'pytest.ini'),str(root/'fixtures-v2/test_stiffened_shell_ge_experimental.py')+'::test_linear_refinement_failure_preserves_accepted_snapshot[cancel_second]'],'second-correction-cancellation',1024**3)
