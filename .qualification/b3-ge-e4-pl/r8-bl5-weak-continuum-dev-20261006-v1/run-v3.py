from pathlib import Path
import hashlib,importlib.util,json,os,shutil
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert sha(BASE)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('bounded',BASE);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT=ROOT;s.ENV.pop('PYTHONOPTIMIZE',None);s.ENV.pop('OPENBLAS_CORETYPE',None)
s.ENV.update(NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1')
SITE=ROOT.parent/'r8-native-fibre-bl5-dev-20261005-v1/installed-s3-v1'
CI=ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
installed_binding=json.loads((SITE.parent/'installed-binding-s3-v1.json').read_text())
wheel=SITE.parent/'wheel-s3-v1'/installed_binding['wheel']
assert sha(wheel)==installed_binding['wheel_sha256']=='b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291'
expected=json.loads((SITE.parent/'installed-package-modules-s3-v1.json').read_text())
actual={str(p.relative_to(SITE)):sha(p) for p in (SITE/'anysolver').rglob('*.py')}
assert actual==expected,'installed artifact changed'
previous=ROOT.parent/'r8-bl5-released-reference-dev-20261005-v1'
derived=(previous/'ccx-v1/supervisor-function-v1.py').read_text().replace('effective OpenSees library-thread qualification unresolved','sampled thread starts and effective imported numerical pools; not peak/thread qualification')
(ROOT/'supervisor-function-v3.py').write_bytes(derived.encode('utf-8'))
exec(compile(derived,str(ROOT/'supervisor-function-v3.py'),'exec'),s.__dict__)

WMI=Path('C:/Python/Python314/DLLs/_wmi.pyd').resolve()
original_threads=s.threads
def classified_threads(proc):
    records=original_threads(proc)
    for record in records:
        record['original_numeric_or_unresolved']=record['numeric_or_unresolved']
        record['exact_WMI_support']=record['query_status']==0 and record['start_module'] is not None and Path(record['start_module']).resolve()==WMI
        if record['exact_WMI_support']: record['numeric_or_unresolved']=False
    return records
s.threads=classified_threads
(ROOT/'wmi-classification-v3.json').write_text(json.dumps(dict(scope='Root-adopted exact Python314 WMI query support thread; numeric/unresolved ceiling remains1',
    path=str(WMI),sha256=sha(WMI),primary_source='https://raw.githubusercontent.com/python/cpython/3.14/PC/_wmimodule.cpp',
    source_symbols='_query_thread, WMI COM query',raw_support_counts='Each immutable sample retains all original thread records and prior classifications'),indent=2)+'\n')

s.ENV['PYTHONPATH']=os.pathsep.join((str(SITE),str(CI),str(REPO)))
s.ENV['ANYSOLVER_WEAK_INSTALLED']=str(SITE);s.ENV['ANYSOLVER_WEAK_RAW']=str(ROOT/'results-v3')
(ROOT/'results-v3').mkdir(exist_ok=False)
s.ENV['ANYSOLVER_WEAK_REUSE']=str(ROOT/'reuse-v3.json')
s.ENV['ANYSOLVER_WEAK_SAVED_STRONG']=str(previous/'ccx-v1')
NATIVE=ROOT.parent/'r8-bl5-matched-native-dev-20261005-v1/calibration-v2.json'
s.ENV['ANYSOLVER_WEAK_SAVED_NATIVE']=str(NATIVE)
files=['scripts/r8_bl5_weak_continuum_reference.py','tests/test_r8_bl5_weak_continuum_reference.py','docs/reference_cases/stiffened_shell_bl5_weak_continuum_reference.md','scripts/r8_bl5_matched_native_reference.py',
       'scripts/r8_bl5_released_director_reference.py','scripts/r8_e02_double_output.py','scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_rigid_tip_reference.py']
for name,destination in ((files[0],'executed-script-v3.py'),(files[1],'executed-tests-v3.py')):
    assert not (ROOT/destination).exists();shutil.copyfile(REPO/name,ROOT/destination)
outputs={name:sha(previous/'ccx-v1'/name) for name in ('released.inp','released.frd','released.sta','stdout.log','stderr.log','execution-binding.json','parsed-v2.json')}
manifest=json.loads((previous/'ccx-v1/execution-binding.json').read_text())
assert all(outputs[name]==value for name,value in manifest['files'].items())
(ROOT/'binding-v3.json').write_text(json.dumps(dict(scope='Weak-P0 continuum: body/work controls, one strong reconstruction and one weak solve; no native/external rerun',
    source={name:sha(REPO/name) for name in files},runner_sha256=sha(__file__),entry_sha256=sha(ROOT/'entry-v3.py'),
    base_supervisor_sha256=sha(BASE),derived_supervisor_sha256=sha(ROOT/'supervisor-function-v3.py'),wheel_sha256=sha(wheel),
    installed_modules=actual,reuse_prerequisites_sha256=sha(ROOT/'reuse-v3.json'),saved_native_calibration_sha256=sha(NATIVE),existing_reference_outputs=outputs,existing_reference_model_sha256=manifest['model_sha256'],
    ci_dependencies={str(p.relative_to(CI)):sha(p) for p in CI.glob('*.dist-info/METADATA')}),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'entry-v3.py')],'focused-v3',2*1024**3)
