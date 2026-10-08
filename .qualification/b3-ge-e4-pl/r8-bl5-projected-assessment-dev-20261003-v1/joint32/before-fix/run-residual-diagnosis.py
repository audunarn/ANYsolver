from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
repo=Path("C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
site=root.parent/"r8-bl5-projected-integration-v1/site"
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=";".join(map(str,(site,repo,repo/"scripts",repo/"tests")))
m.supervise(["C:/Python/Python314/python.exe",str(root/"residual-diagnosis.py")],"residual-diagnosis-check",1024**3)
