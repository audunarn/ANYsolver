from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("bounded",root.parent/"r8-bl5-affine-flexible-v1/run.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV["PYTHONPATH"]=""
for key in ("BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):m.ENV[key]="1"
for case in ("fy","mx","mz"):
 m.supervise([str(m.RUNTIME),str(root/"fixtures/r8_bl5_nested_projected_external_dev.py"),"--site",str(m.EXTERNAL_SITE),"--output-dir",str(root/"external"/case),"--case",case],case+"-check",8*1024**3)
