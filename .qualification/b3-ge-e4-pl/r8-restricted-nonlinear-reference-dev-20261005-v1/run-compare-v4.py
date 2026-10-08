from pathlib import Path
import importlib.util
p=Path.home()/'AppData/Local/Temp/r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('supervisor',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=Path(__file__).resolve().parent
script=m.REPO/'scripts/r8_e04_restricted_membrane.py'
m.supervise(['C:/Python/Python314/python.exe',str(script),'--route','compare','--native-input',str(m.ROOT/'native-screen-v3/native.json'),'--external-input',str(m.ROOT/'external-screen-v3/external.json'),'--output',str(m.ROOT/'comparison-v4')],'compare-execution-v4',2*1024**3)
