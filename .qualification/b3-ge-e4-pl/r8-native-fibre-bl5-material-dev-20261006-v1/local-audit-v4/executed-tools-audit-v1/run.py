from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys
ROOT=Path(__file__).resolve().parent;EVIDENCE=ROOT.parent;REPO=EVIDENCE.parents[2]
phase=sys.argv[1] if len(sys.argv)>1 else 'audit-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
preservation={}
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    manifest=json.loads((EVIDENCE/name).read_text())
    for p,row in manifest['artifacts'].items():assert sha(EVIDENCE/p)==row['sha256'],p
    preservation[name]=dict(sha256=sha(EVIDENCE/name),count=len(manifest['artifacts']))
read_handoff=json.loads((EVIDENCE/'owner-diagnosis-v3-handoff.json').read_text())
for name,row in read_handoff['new_files'].items():assert sha(EVIDENCE/name)==row['sha256'],name
artifact=json.loads((EVIDENCE/'artifact-binding-v1.json').read_text())
assert artifact['sha256']=='ca2503e2178aa536b79d556a2c105faef29977f6d7a1442e989bddde077cd849'
assert sha(artifact['artifact'])==artifact['sha256']
for name,digest in artifact['source'].items():assert sha(EVIDENCE/'installed-wheel-v1'/name.replace('\\','/').removeprefix('src/'))==digest
previous=EVIDENCE.parent/'r8-bl5-released-reference-dev-20261005-v1/original-supervisor.py'
function=EVIDENCE.parent/'r8-bl5-weak-continuum-dev-20261006-v1/supervisor-function-v3.py'
spec=importlib.util.spec_from_file_location('bounded',previous);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT=ROOT;s.ENV=os.environ.copy()
for key in ('PYTHONOPTIMIZE','OPENBLAS_CORETYPE'):s.ENV.pop(key,None)
s.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',
             NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',LOCAL_AUDIT_PHASE=phase)
exec(compile(function.read_text(),str(function),'exec'),s.__dict__)
WMI=Path('C:/Python/Python314/DLLs/_wmi.pyd').resolve();original=s.threads
def classified(proc):
    records=original(proc)
    for row in records:
        row['original_numeric_or_unresolved']=row['numeric_or_unresolved']
        row['exact_WMI_support']=row['query_status']==0 and row['start_module'] is not None and Path(row['start_module']).resolve()==WMI
        if row['exact_WMI_support']:row['numeric_or_unresolved']=False
    return records
s.threads=classified
CI=EVIDENCE.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
s.ENV['PYTHONPATH']=os.pathsep.join((str(EVIDENCE/'installed-wheel-v1'),str(CI),str(REPO)))
snapshot=ROOT/('executed-tools-'+phase);snapshot.mkdir(exist_ok=False)
for name in ('run.py','entry.py','audit.py'):shutil.copyfile(ROOT/name,snapshot/name)
for name in ('examples/stiffened_shell_native_fibre_bl5_material.py','examples/stiffened_shell_native_fibre_bl5.py'):
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
saved=('failed-prefix-bending-continuation-v1.bin','rejected-trial-state-v1/failed-Newton-trial.npz',
       'rejected-trial-state-v1/evaluation-130.npz','rejected-trial-state-v1/failed-Newton-fullstep.npy')
(ROOT/('binding-'+phase+'.json')).write_text(json.dumps(dict(consumed=preservation,
    read_handoff_sha256=sha(EVIDENCE/'owner-diagnosis-v3-handoff.json'),wheel_sha256=artifact['sha256'],
    installed_root=str(EVIDENCE/'installed-wheel-v1'),tools={n:sha(ROOT/n) for n in ('run.py','entry.py','audit.py')},
    fixture_sources={n:sha(REPO/n) for n in ('examples/stiffened_shell_native_fibre_bl5_material.py','examples/stiffened_shell_native_fibre_bl5.py')},
    saved_inputs={n:sha(EVIDENCE/n) for n in saved},supervisor_sha256=sha(previous),supervisor_function_sha256=sha(function),wmi_sha256=sha(WMI)),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'entry.py')],phase,2*1024**3)
