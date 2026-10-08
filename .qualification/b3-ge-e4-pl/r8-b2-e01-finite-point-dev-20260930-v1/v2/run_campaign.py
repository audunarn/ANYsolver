from pathlib import Path
import os,sys,json,subprocess,hashlib,zipfile
root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_text());commands=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/'b2_e01_opensees_finite_point.py')==manifest['reference_sha256']
assert sha(root/'b2_e01_finite_point_native.py')==manifest['native_runner_sha256']
site=Path(manifest['native_site']);installed=site.parent
wheel=next((installed/'wheels').glob('anysolver-*.whl'))
assert sha(wheel)==manifest['native_wheel_sha256']
with zipfile.ZipFile(wheel) as z:
    names=[p for p in z.namelist() if p.startswith('anysolver/') and p.endswith('.py')]
    assert len(names)==386 and all(z.read(p)==(site/p).read_bytes() for p in names)
assert sha(Path(manifest['external_python']))==manifest['external_python_sha256']
assert sha(Path('C:/Python/Python314/Lib/site-packages/openseespywin/opensees.pyd'))==manifest['external_binary_sha256']
def run(argv,env,log):
    commands.append({'argv':argv,'env_PYTHONPATH':env['PYTHONPATH'],'log':log})
    (root/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    with (root/log).open('w') as out:code=subprocess.call(argv,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
    if code:raise RuntimeError(f'{log} exited{code}; preserve diagnostic output')
base=os.environ.copy();base.update(NUMBA_DISABLE_JIT='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')
native=base.copy();native['PYTHONPATH']=str(site)+os.pathsep+str(root)
record=json.loads((root/'native/native.json').read_text());assert record['status']=='PASSED_NATIVE_FIXED_SCREEN_ONLY'
assert len(record['panels'])==2 and all(len(p['cases'])==6 and p['constraint_row_max_error']<=1e-10 for p in record['panels'])
external=base.copy();external['PYTHONPATH']='C:/Python/Python314/Lib/site-packages'
run([manifest['external_python'],'-u','b2_e01_opensees_finite_point.py','--output-dir',str(root/'external')],external,'external.log')
summary=json.loads((root/'external/summary.json').read_text())
assert summary['status']=='PASSED_FIXED_REFERENCE_DIAGNOSTIC_ONLY'
assert len(summary['cases'])==18
print(json.dumps({'status':'PASSED_FIXED_NATIVE_AND_REFERENCE_SCREEN','native_cases':12,'external_beam_controls':6,'external_panel_cases':12,'not_qualification':True}))
