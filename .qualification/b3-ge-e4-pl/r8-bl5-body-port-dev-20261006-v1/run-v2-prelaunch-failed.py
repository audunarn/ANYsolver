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
derived=(previous/'ccx-v1/supervisor-function-v2.py').read_text().replace('effective OpenSees library-thread qualification unresolved','sampled thread starts and effective imported numerical pools; not peak/thread qualification')
(ROOT/'supervisor-function-v2.py').write_bytes(derived.encode('utf-8'))
exec(compile(derived,str(ROOT/'supervisor-function-v2.py'),'exec'),s.__dict__)

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
(ROOT/'wmi-classification-v2.json').write_text(json.dumps(dict(scope='Exact prior Python314 WMI support classification, numerical/unresolved ceiling remains1',
    path=str(WMI),sha256=sha(WMI),primary_source='https://raw.githubusercontent.com/python/cpython/3.14/PC/_wmimodule.cpp',
    source_symbols='_query_thread; COM/WMI query',raw_total_support_counts='All immutable sampled records retained'),indent=2)+'\n')
s.ENV['PYTHONPATH']=os.pathsep.join((str(SITE),str(CI),str(REPO)))
s.ENV['ANYSOLVER_PORT_INSTALLED']=str(SITE)
s.ENV['ANYSOLVER_PORT_SAVED']=str(ROOT.parent/'r8-bl5-weak-continuum-dev-20261006-v1')
s.ENV['ANYSOLVER_PORT_REUSE']=str(ROOT/'reuse-v2.json')
s.ENV['ANYSOLVER_PORT_RAW']=str(ROOT/'results-v2');(ROOT/'results-v2').mkdir(exist_ok=False)
import ast,xml.etree.ElementTree as ET
def functions(path):
    text=Path(path).read_text();tree=ast.parse(text)
    return {node.name:ast.get_source_segment(text,node) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
old=functions(ROOT/'executed-tests-v1.py');new=functions(REPO/'tests/test_r8_bl5_body_port_probe.py')
passed=['test_saved_identity_and_body_work','test_immutable_input_refusal','test_exact_specimen_and_density_units',
    'test_opposite_sign_common_supported_work','test_six_mode_balance_before_gauge']
junit=ET.parse(ROOT/'junit-v1.xml')
actual_passes={n.attrib['name'] for n in junit.iter('testcase') if not list(n)}
assert set(passed)<=actual_passes
assert all(old[name]==new[name] for name in passed)
old_tool=functions(ROOT/'executed-script-v1.py');new_tool=functions(REPO/'scripts/r8_bl5_body_port_probe.py')
assert all(old_tool[name]==new_tool[name] for name in ('load_saved','continuum_fields','native_rigid_fields','shell_rigid_fields','require_balanced'))
assert new_tool['prepare'].replace('        full_native_physical_load_covector=loads.tolist(),\n','')==old_tool['prepare']
(ROOT/'reuse-v2.json').write_text(json.dumps(dict(state='EXACT_PASSED_PREREQUISITE_FUNCTIONS_REUSED',
    checked=['saved','identity','geometry','sign','balance'],prior_junit_sha256=sha(ROOT/'junit-v1.xml'),
    prior_binding_sha256=sha(ROOT/'binding-v1.json'),
    prerequisite_function_sha256={name:hashlib.sha256(old[name].encode()).hexdigest() for name in passed},
    delta='Only prepare output gains full load covector; saved inputs/compiler/common-work/balance unchanged. Body residual arithmetic and added cancellation control are affected.'),indent=2)+'\n')
files=['scripts/r8_bl5_body_port_probe.py','tests/test_r8_bl5_body_port_probe.py','docs/reference_cases/stiffened_shell_bl5_body_port_probe.md',
    'scripts/r8_bl5_matched_native_reference.py','scripts/r8_bl5_weak_continuum_reference.py','scripts/r8_bl5_released_director_reference.py',
    'scripts/r8_e02_double_output.py','scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_rigid_tip_reference.py']
for name,destination in ((files[0],'executed-script-v2.py'),(files[1],'executed-tests-v2.py')):
    assert not (ROOT/destination).exists();shutil.copyfile(REPO/name,ROOT/destination)
saved=Path(s.ENV['ANYSOLVER_PORT_SAVED'])
inputs={name:sha(saved/name) for name in ('input-v1.json','operators-v1.npz','results-v3/weak-v1.json','binding-v3.json','integration-binding.json')}
(ROOT/'binding-v2.json').write_text(json.dumps(dict(scope='Saved-density body-port development discriminator, at most TWO uncoupled native body RHS; no coupled calibration/external replay',
    historical_applicability='fdd5c9dd; changing product working source NOT imported or represented as trusted installed source',
    source={name:sha(REPO/name) for name in files},runner_sha256=sha(__file__),entry_sha256=sha(ROOT/'entry-v2.py'),
    base_supervisor_sha256=sha(BASE),derived_supervisor_sha256=sha(ROOT/'supervisor-function-v2.py'),
    wheel_sha256=sha(wheel),installed_modules=actual,saved_continuum=inputs,
    reused_prerequisites_sha256=sha(ROOT/'reuse-v2.json'),
    ci_dependencies={str(p.relative_to(CI)):sha(p) for p in CI.glob('*.dist-info/METADATA')},
    criteria=dict(equilibrium_work_wrench=1e-8,material_compatibility_gauge=1e-9,work_floor_J=1e-12,
        force_floor_N=1.,moment_floor_Nm=1.,reference_length_m=1.),
    resource=dict(timeout_s=600,process_tree_bytes=2*1024**3,affinity=1,effective_pools=1,JIT='off',backend='unforced')),
    indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'entry-v2.py')],'focused-v2',2*1024**3)
