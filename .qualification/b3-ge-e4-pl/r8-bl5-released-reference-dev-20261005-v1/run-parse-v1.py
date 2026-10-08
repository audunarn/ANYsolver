from pathlib import Path
import hashlib,importlib.util,json,os
RAW=Path(__file__).resolve().parent; REPO=RAW.parents[2]; ROOT=RAW/'ccx-v1'
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('bounded_parse',BASE); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT=ROOT; s.ENV.pop('OPENBLAS_CORETYPE',None)
s.ENV['PYTHONPATH']=os.pathsep.join((str(REPO/'scripts'),str(REPO/'src'),str(REPO)))
source=(ROOT/'supervisor-function-v1.py').read_text()
exec(compile(source,str(ROOT/'supervisor-function-v1.py'),'exec'),s.__dict__)
files=['scripts/r8_bl5_released_director_reference.py','scripts/r8_e02_double_output.py','scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_rigid_tip_reference.py']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
(ROOT/'parse-source-binding-v1.json').write_text(json.dumps(dict(source={f:sha(REPO/f) for f in files},runner_sha256=sha(__file__),derived_supervisor_sha256=sha(ROOT/'supervisor-function-v1.py'),scope='Saved single-smoke output parsing; no external process/retry'),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe','-m','scripts.r8_bl5_released_director_reference','parse','--directory',str(ROOT),'--executable','C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe'],'parse-v1',2*1024**3)
