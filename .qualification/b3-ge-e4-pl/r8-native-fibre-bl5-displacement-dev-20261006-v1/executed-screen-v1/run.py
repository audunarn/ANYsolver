from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys
ROOT=Path(__file__).resolve().parent; EVIDENCE=ROOT; REPO=ROOT.parents[2]
phase=sys.argv[1]
assert phase in ('screen-v1','tests-v1','tests-v2')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
previous=EVIDENCE.parent/'r8-bl5-released-reference-dev-20261005-v1/original-supervisor.py'
function=EVIDENCE.parent/'r8-bl5-weak-continuum-dev-20261006-v1/supervisor-function-v3.py'
spec=importlib.util.spec_from_file_location('bounded',previous);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT=ROOT;s.ENV=os.environ.copy()
for key in ('PYTHONOPTIMIZE','OPENBLAS_CORETYPE'):s.ENV.pop(key,None)
s.ENV.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',
             NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',BOUNDARY_PHASE=phase)
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
names=('src/anysolver/_stiffened_shell_affine_endpoint.py','src/anysolver/_stiffened_shell_displacement_control.py','src/anysolver/_stiffened_shell_displacement_corrector.py','src/anysolver/_stiffened_shell_displacement_checkpoint.py','src/anysolver/_stiffened_shell_ge_checkpoint_binary.py','src/anysolver/_stiffened_shell_ge_experimental.py','examples/stiffened_shell_native_fibre_bl5_displacement.py')
snapshot=ROOT/('executed-'+phase);snapshot.mkdir(exist_ok=False)
for name in names:
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,target)
for name in ('run.py','entry.py'):
    shutil.copyfile(ROOT/name,snapshot/name)
(ROOT/('binding-'+phase+'.json')).write_text(json.dumps(dict(source={n:sha(REPO/n) for n in names},tools={n:sha(ROOT/n) for n in ('run.py','entry.py')},supervisor_sha256=sha(previous),supervisor_function_sha256=sha(function),wmi_sha256=sha(WMI)),indent=2)+'\n')
s.supervise(['C:/Python/Python314/python.exe',str(ROOT/'entry.py')],phase,2*1024**3)
