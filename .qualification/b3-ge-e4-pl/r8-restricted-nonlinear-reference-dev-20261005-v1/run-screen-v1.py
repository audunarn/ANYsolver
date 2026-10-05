from pathlib import Path
import importlib.util, hashlib, json
p=Path.home()/'AppData/Local/Temp/r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('supervisor',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=Path(__file__).resolve().parent
site=m.REPO/'.qualification/b3-ge-e4-pl/r8-native-turning-dev-20261005-v1/site-progress-v1'
wheel=m.REPO/'.qualification/b3-ge-e4-pl/r8-native-turning-dev-20261005-v1/solver-dist-progress-v1/anysolver-0.4.7-py3-none-any.whl'
m.ENV['PYTHONPATH']=str(site)
(m.ROOT/'artifact.json').write_text(json.dumps(dict(site=str(site),wheel=str(wheel),wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),runtime=str(m.RUNTIME),script_sha256=hashlib.sha256((m.REPO/'scripts/r8_e04_restricted_membrane.py').read_bytes()).hexdigest()),indent=2))
m.supervise([str(m.RUNTIME),str(m.REPO/'scripts/r8_e04_restricted_membrane.py'),'--opensees-site',str(m.EXTERNAL_SITE),'--output',str(m.ROOT/'screen-v1')],'complete-screen-v1',2*1024**3)
