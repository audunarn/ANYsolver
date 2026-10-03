from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
repo=Path("C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=str(repo)+";"+str(repo/"scripts")
m.supervise(["C:/Python/Python314/python.exe",str(root/"norm.py"),"register","--output",str(root/"register.json")],"register-check",1024**3)
