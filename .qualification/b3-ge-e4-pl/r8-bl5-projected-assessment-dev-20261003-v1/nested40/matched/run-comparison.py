from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=""
m.supervise(["C:/Python/Python314/python.exe",str(root/"comparison.py"),"--owner",str(root.parent/"r8-bl5-nested40-owner-v6/owner.json"),"--external",str(root/"external"),"--fixtures",str(root/"fixtures"),"--output",str(root/"comparison.json")],"comparison-check",1024**3)
