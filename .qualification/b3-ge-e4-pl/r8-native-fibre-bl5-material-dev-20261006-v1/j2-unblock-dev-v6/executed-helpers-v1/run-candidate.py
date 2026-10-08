from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys
ROOT=Path(__file__).resolve().parent; EVIDENCE=ROOT.parent; REPO=EVIDENCE.parents[2]
phase=sys.argv[1]
assert phase in ('helpers-v1','candidate-screen-v1')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
preservation={}
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    data=json.loads((EVIDENCE/name).read_text())
    for path,row in data['artifacts'].items():assert sha(EVIDENCE/path)==row['sha256'],path
    preservation[name]=dict(count=len(data['artifacts']),sha256=sha(EVIDENCE/name))
read=json.loads((EVIDENCE/'owner-diagnosis-v3-handoff.json').read_text())
for name,row in read['new_files'].items():assert sha(EVIDENCE/name)==row['sha256'],name
local=json.loads((EVIDENCE/'local-audit-v4/artifact-sha256.json').read_text())
for name,row in local['artifacts'].items():assert sha(EVIDENCE/'local-audit-v4'/name)==row['sha256'],name
v5=json.loads((EVIDENCE/'boundary-candidate-v5/artifact-sha256.json').read_text())
for name,row in v5['artifacts'].items():assert sha(EVIDENCE/'boundary-candidate-v5'/name)==row['sha256'],name
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
             NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',BOUNDARY_PHASE=phase)
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
s.ENV['PYTHONPATH']=os.pathsep.join((str(REPO/'src'),str(CI),str(REPO),str(REPO/'tests')))
names=('src/anysolver/_stiffened_shell_ge_finite_experimental.py','src/anysolver/_ge_beam3_fibre_cell.py',
       'src/anysolver/_ge_beam3_retained_fibre.py','src/anysolver/_stiffened_shell_ge_experimental.py',
       'src/anysolver/stiffened_shell.py','src/anysolver/_stiffened_shell_ge_point_buckling.py',
       'src/anysolver/_stiffened_shell_q4_algorithmic_pullback.py','src/anysolver/_stiffened_shell_q4_material_event.py','tests/test_q4_native_material_event.py','tests/test_native_fibre_boundary_proposal.py','tests/test_stiffened_shell_native_fibre_bl5_material.py',
       'examples/stiffened_shell_native_fibre_bl5_material.py','examples/stiffened_shell_native_fibre_bl5.py',
       'docs/reference_cases/stiffened_shell_native_fibre_bl5_material.md')
snapshot=ROOT/('executed-'+phase);snapshot.mkdir(exist_ok=False)
for name in names:
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
for name in ('run-candidate.py','entry-candidate.py','capture-candidate.py'):
    shutil.copyfile(ROOT/name,snapshot/name)
(ROOT/('binding-'+phase+'.json')).write_text(json.dumps(dict(source={n:sha(REPO/n) for n in names},
    tools={n:sha(ROOT/n) for n in ('run-candidate.py','entry-candidate.py','capture-candidate.py')},consumed=preservation,
    read_handoff_sha256=sha(EVIDENCE/'owner-diagnosis-v3-handoff.json'),local_manifest_sha256=sha(EVIDENCE/'local-audit-v4/artifact-sha256.json'),
    v5_manifest_sha256=sha(EVIDENCE/'boundary-candidate-v5/artifact-sha256.json'),frozen_wheel_sha256=artifact['sha256'],supervisor_sha256=sha(previous),supervisor_function_sha256=sha(function),
    wmi_sha256=sha(WMI)),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'entry-candidate.py')],phase,2*1024**3)
