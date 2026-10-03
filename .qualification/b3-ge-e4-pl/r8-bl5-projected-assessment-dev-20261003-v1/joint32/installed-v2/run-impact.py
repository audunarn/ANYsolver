from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
repo=Path("C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
site=root/"site"
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=";".join(map(str,(site,repo,repo/"scripts",repo/"tests")))
m.ENV['PYTHONPATH']=str(root/'site')+';'+str(repo)
m.supervise(['C:/Python/Python314/python.exe','-m','pytest','-q','-c',str(root/'pytest.ini'),str(root/'fixtures-v3/test_stiffened_shell_nodal_rigid_footprint.py')+'::test_linear_physical_wrench_reference_restart_and_selection',str(root/'fixtures-v3/test_stiffened_shell_curved_reference_seam.py')+'::test_explicit_curved_point_owner_reference_finite_restart[True-100.0]'],'installed-impact',1024**3)
