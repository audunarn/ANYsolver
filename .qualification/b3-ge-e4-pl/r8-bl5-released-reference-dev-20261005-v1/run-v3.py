from pathlib import Path
import hashlib, importlib.util, json, os, shutil
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('bounded',BASE)
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT=ROOT; s.ENV.pop('PYTHONOPTIMIZE',None); s.ENV.pop('OPENBLAS_CORETYPE',None)
s.ENV.update(NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH']=os.pathsep.join((str(REPO/'scripts'),str(REPO/'src'),str(REPO)))
s.ENV['ANYSOLVER_DEVELOPMENT_SOURCE']=str(REPO/'src')
s.ENV['ANYSOLVER_DEVELOPMENT_RECORD']=str(ROOT/'runtime-v3.json')
s.ENV['ANYSOLVER_RELEASED_SAVED_SMOKE']=str(ROOT/'ccx-v1')
derived=(ROOT/'ccx-v1/supervisor-function-v1.py').read_text().replace('effective OpenSees library-thread qualification unresolved','effective library-thread qualification not established; sampled source controls only')
exec(compile(derived,str(ROOT/'offline-supervisor-v3.py'),'exec'),s.__dict__)
(ROOT/'offline-supervisor-v3.py').write_bytes(derived.encode('utf-8'))
files=['scripts/r8_bl5_released_director_reference.py','tests/test_r8_bl5_released_director_reference.py','docs/reference_cases/stiffened_shell_bl5_released_reference.md','scripts/r8_e02_double_output.py','scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_rigid_tip_reference.py','scripts/development_test_runtime.py']
for file,name in [('scripts/r8_bl5_released_director_reference.py','executed-reference-script-v3.py'),('tests/test_r8_bl5_released_director_reference.py','executed-reference-tests-v3.py')]:
    assert not (ROOT/name).exists(); shutil.copyfile(REPO/file,ROOT/name)
(ROOT/'binding-v3.json').write_text(json.dumps(dict(source={f:sha(REPO/f) for f in files},supervisor_sha256=sha(BASE),runner_sha256=sha(__file__),scope='Affected parser/action bookkeeping + saved exact CCX output; no external retry or accuracy',saved_outputs={f:sha(ROOT/'ccx-v1'/f) for f in ['released.inp','released.frd','released.sta','stdout.log','stderr.log','execution-binding.json']},derived_supervisor_sha256=sha(ROOT/'offline-supervisor-v3.py')),indent=2)+'\n')
command=['C:/Python/Python314/python.exe','-m','pytest','-q','-k','root_RF or actual_saved or parser or effective_runtime','-p','no:cacheprovider','-p','development_test_runtime','--basetemp',str(ROOT/'pytest-temp-v3'),'--junitxml='+str(ROOT/'junit-v3.xml'),str(REPO/'tests/test_r8_bl5_released_director_reference.py')]
s.supervise(command,'focused-v3',2*1024**3)
