from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
repo=Path("C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001")
site=root/"site"
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=";".join(map(str,(site,repo,repo/"scripts",repo/"tests")))
m.supervise(["C:/Python/Python314/python.exe",str(root/"owner.py"),"--site",str(site),"--source",str(repo),"--wheel",str(root/"dist/anysolver-0.4.7-py3-none-any.whl"),"--wheel-sha","1bf7dabd8771e76ed09825fb66a89e3e48d513dbb0321989c41701096a679632","--registration",str(root/"register.json"),"--output-dir",str(root/"owner")],"owner-check",1024**3)
