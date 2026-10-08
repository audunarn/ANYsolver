from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('owned_supervisor',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT;m.ENV['PYTHONPATH']=str(ROOT/'site')
m.supervise([sys.executable,'-u',str(ROOT/'check-native-helper-affected.py')],'native-helper-affected',1024**3)


