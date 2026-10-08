from pathlib import Path
import hashlib, importlib.util, json, os, shutil
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('bounded',BASE)
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT=ROOT; s.ENV.pop('PYTHONOPTIMIZE',None)
s.ENV.update(NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH']=os.pathsep.join((str(REPO/'scripts'),str(REPO/'src'),str(REPO)))
s.ENV['ANYSOLVER_DEVELOPMENT_SOURCE']=str(REPO/'src')
s.ENV['ANYSOLVER_DEVELOPMENT_RECORD']=str(ROOT/'runtime-v3.json')
files=['scripts/r8_e01_native_polar_work.py','tests/test_r8_e01_native_polar_work.py','scripts/r8_e01_objective_polar_trace.py','tests/test_r8_e01_objective_polar_trace.py','scripts/r8_e01_material_frame_work.py','src/anysolver/_stiffened_shell_l1_local_experimental.py','src/anysolver/_ge_beam3_mixed_ad.py','src/anysolver/_ge_beam3_retained_generalized_state.py','src/anysolver/_ge_beam3_centered_reference.py','src/anysolver/_ge_beam3_p5/compensated_coordinates.py','src/anysolver/corotational.py','src/anysolver/_ge_beam3_p5/algebra.py','docs/reference_cases/stiffened_shell_e01_material_frame_work.md']
for file,name in [('scripts/r8_e01_native_polar_work.py','executed-native-script-v3.py'),('tests/test_r8_e01_native_polar_work.py','executed-native-tests-v3.py'),('scripts/r8_e01_objective_polar_trace.py','executed-polar-script-v3.py')]:
    assert not (ROOT/name).exists(); shutil.copyfile(REPO/file,ROOT/name)
(ROOT/'binding-v3.json').write_text(json.dumps(dict(source={f:sha(REPO/f) for f in files},supervisor_sha256=sha(BASE),runner_sha256=sha(__file__),scope='Local native33 projected-polar proposal; no structural/external solve'),indent=2)+'\n')
command=['C:/Python/Python314/python.exe','-m','pytest','-q','-p','no:cacheprovider','-p','development_test_runtime','--basetemp',str(ROOT/'pytest-temp-v3'),'--junitxml='+str(ROOT/'junit-v3.xml'),str(REPO/'tests/test_r8_e01_native_polar_work.py')]
s.supervise(command,'focused-v3',2*1024**3)
