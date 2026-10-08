from pathlib import Path
import hashlib, importlib.util, inspect, json, os, shutil
RAW=Path(__file__).resolve().parent; REPO=RAW.parents[2]
EXE=Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe').resolve()
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(EXE)=='27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
assert sha(BASE)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
assert sha(RAW/'prepared-v2/released.inp')=='54d72909717c07a82bdd4bb70e87b5084a402e529e60ba1a4576b86d99c0b154'
model=json.loads((RAW/'prepared-v2/model.json').read_text())
assert model['model_sha256']=='a22170179b6e257a47288ff825a3b69ad503e5e3c4a040fcd5f3b53933c86463'
ROOT=RAW/'ccx-v1'; ROOT.mkdir(exist_ok=False)
shutil.copyfile(RAW/'prepared-v2/released.inp',ROOT/'released.inp')
shutil.copyfile(RAW/'prepared-v2/model.json',ROOT/'model.json')
spec=importlib.util.spec_from_file_location('bounded',BASE); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT=ROOT; s.ENV.pop('OPENBLAS_CORETYPE',None)
s.ENV.update(NUMBER_OF_CPUS='1',CCX_NPROC_RESULTS='1',CCX_NPROC_EQUATION_SOLVER='1',CCX_NPROC_STIFFNESS='1')
# Reuse only the existing bounded supervisor function, tighten its explicit
# numerical/unresolved ceiling to one, and preserve the exact derived function.
source=inspect.getsource(s.supervise).replace('numeric > 8','numeric > 1').replace('numerical_threads_limit=8','numerical_threads_limit=1')
(ROOT/'supervisor-function-v1.py').write_bytes(source.encode('utf-8'))
exec(compile(source,str(ROOT/'supervisor-function-v1.py'),'exec'),s.__dict__)
files=['scripts/r8_bl5_released_director_reference.py','scripts/r8_e02_double_output.py','scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_rigid_tip_reference.py']
(ROOT/'source-binding.json').write_text(json.dumps(dict(source={f:sha(REPO/f) for f in files},runner_sha256=sha(__file__),base_supervisor_sha256=sha(BASE),derived_supervisor_sha256=sha(ROOT/'supervisor-function-v1.py'),environment={k:s.ENV[k] for k in ('NUMBER_OF_CPUS','CCX_NPROC_RESULTS','CCX_NPROC_EQUATION_SOLVER','CCX_NPROC_STIFFNESS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_DISABLE_JIT')},scope='ONE exact new released-director CCX smoke; no accuracy/qualification'),indent=2)+'\n')
s.supervise([str(EXE),'-i','released'],'process',2*1024**3)
record=json.loads((ROOT/'process/execution.json').read_text())
assert record['status']=='completed' and record['exit_code']==0
for name in ('stdout.log','stderr.log'): shutil.copyfile(ROOT/'process'/name,ROOT/name)
outputs=('released.inp','released.frd','stdout.log','stderr.log','released.sta')
manifest=dict(schema='R8_BL5_RELEASED_REFERENCE_EXECUTION_V1',status='completed',exit_code=record['exit_code'],command=record['command'],working_directory=str(ROOT.resolve()),executable_sha256=sha(EXE),model_sha256=model['model_sha256'],files={name:sha(ROOT/name) for name in outputs})
(ROOT/'execution-binding.json').write_text(json.dumps(manifest,indent=2)+'\n')
