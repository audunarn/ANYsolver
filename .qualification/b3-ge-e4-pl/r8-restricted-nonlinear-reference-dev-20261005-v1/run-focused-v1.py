from pathlib import Path
import importlib.util
p=Path.home()/'AppData/Local/Temp/r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('supervisor',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=Path(__file__).resolve().parent
m.ENV['PYTHONPATH']=str(m.REPO/'src')
m.supervise(['C:/Python/Python314/python.exe','-m','pytest',str(m.REPO/'tests/test_stiffened_shell_e04_restricted_membrane.py'),'-q','-p','no:cacheprovider'],'focused-source-v1',2*1024**3)
