from pathlib import Path
import importlib.util, hashlib, json
p=Path.home()/'AppData/Local/Temp/r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('supervisor',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=Path(__file__).resolve().parent
site=m.REPO/'.qualification/b3-ge-e4-pl/r8-native-turning-dev-20261005-v1/site-progress-v1'
script=m.REPO/'scripts/r8_e04_restricted_membrane.py'
native=m.ROOT/'native-screen-v2';external=m.ROOT/'external-screen-v2';comparison=m.ROOT/'comparison-v2'
(m.ROOT/'artifact-v2.json').write_text(json.dumps(dict(site=str(site),runtime_native='C:/Python/Python314/python.exe',runtime_external=str(m.RUNTIME),script_sha256=hashlib.sha256(script.read_bytes()).hexdigest()),indent=2))
m.ENV['PYTHONPATH']=str(site)
m.supervise(['C:/Python/Python314/python.exe',str(script),'--route','native','--output',str(native)],'native-execution-v2',2*1024**3)
m.ENV.pop('PYTHONPATH',None)
m.supervise([str(m.RUNTIME),str(script),'--route','external','--opensees-site',str(m.EXTERNAL_SITE),'--output',str(external)],'external-execution-v2',2*1024**3)
m.supervise(['C:/Python/Python314/python.exe',str(script),'--route','compare','--native-input',str(native/'native.json'),'--external-input',str(external/'external.json'),'--output',str(comparison)],'compare-execution-v2',2*1024**3)
