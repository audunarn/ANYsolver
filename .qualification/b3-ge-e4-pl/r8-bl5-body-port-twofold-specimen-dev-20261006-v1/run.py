from pathlib import Path
import hashlib,importlib.util,json,os,shutil
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=ROOT.parent/'r8-bl5-released-reference-dev-20261005-v1/original-supervisor.py'
fn=ROOT.parent/'r8-bl5-weak-continuum-dev-20261006-v1/supervisor-function-v3.py'
assert sha(base)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
assert sha(fn)=='3ce31bbf4a9b92686aba826b38ae18d77c4df012e50a35c4dfb956fac69a6f6c'
spec=importlib.util.spec_from_file_location('bounded',base);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT=ROOT;s.ENV=os.environ.copy()
for key in ('PYTHONOPTIMIZE','OPENBLAS_CORETYPE'):s.ENV.pop(key,None)
s.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1')
exec(compile(fn.read_text(),str(fn),'exec'),s.__dict__)
WMI=Path('C:/Python/Python314/DLLs/_wmi.pyd').resolve();old=s.threads

def classified(proc):
    rows=old(proc)
    for row in rows:
        row['original_numeric_or_unresolved']=row['numeric_or_unresolved']
        row['exact_WMI_support']=row['query_status']==0 and row['start_module'] is not None and Path(row['start_module']).resolve()==WMI
        if row['exact_WMI_support']:row['numeric_or_unresolved']=False
    return rows
s.threads=classified
SITE=ROOT.parent/'r8-native-fibre-bl5-dev-20261005-v1/installed-s3-v1'
CI=ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
expected=json.loads((SITE.parent/'installed-package-modules-s3-v1.json').read_text())
actual={str(p.relative_to(SITE)):sha(p) for p in (SITE/'anysolver').rglob('*.py')}
assert actual==expected
binding=json.loads((SITE.parent/'installed-binding-s3-v1.json').read_text());wheel=SITE.parent/'wheel-s3-v1'/binding['wheel']
assert sha(wheel)=='b3d5f572797f3c2954d1bf9dc1c6b4293da14c5812e543dbde7f314a60207291'
s.ENV['PYTHONPATH']=os.pathsep.join((str(SITE),str(CI),str(REPO)))
s.ENV['ANYSOLVER_PORT_INSTALLED']=str(SITE)
s.ENV['ANYSOLVER_PORT_SAVED']=str(ROOT.parent/'r8-bl5-weak-continuum-dev-20261006-v1')
names=['scripts/r8_bl5_body_port_twofold_workflow.py','tests/test_r8_bl5_body_port_twofold_workflow.py','docs/reference_cases/stiffened_shell_bl5_body_port_twofold_workflow.md','scripts/r8_bl5_body_port_twofold.py','scripts/r8_bl5_body_port_probe.py','scripts/r8_bl5_matched_native_reference.py','scripts/r8_bl5_weak_continuum_reference.py']
snap=ROOT/'executed-v1';snap.mkdir(exist_ok=False)
for name in names:
    target=snap/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
for name in ('run.py','entry.py'):shutil.copyfile(ROOT/name,snap/name)
(ROOT/'binding-v1.json').write_text(json.dumps(dict(source={n:sha(REPO/n) for n in names},tools={n:sha(ROOT/n) for n in ('run.py','entry.py')},wheel_path=str(wheel),wheel_sha256=sha(wheel),installed_site=str(SITE),installed_modules=actual,supervisor_sha256=sha(base),function_sha256=sha(fn),wmi_sha256=sha(WMI),authority='One conditional job; shell max3 correction RHS then only if original gates pass one beam RHS; no specimen rerun'),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'entry.py')],'specimen-v1',2*1024**3)
