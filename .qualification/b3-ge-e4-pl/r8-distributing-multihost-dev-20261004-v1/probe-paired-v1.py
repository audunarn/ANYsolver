"""Record actual candidate identities, fixed common work and printed bounds."""
from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np,anysolver
from threadpoolctl import threadpool_info
from scripts.r8_e02_distributing_feasibility import build_case,native_cases,parse_result
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert Path(anysolver.__file__).resolve().is_relative_to(ROOT/'site')
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
inputs=['scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_distributing_feasibility.py','scripts/r8_e02_native_rigid_tip.py','scripts/r8_e02_rigid_tip_reference.py','src/anysolver/_stiffened_shell_distributing_footprint.py','src/anysolver/_stiffened_shell_ge_distributing_reference.py']
sources={p:sha(REPO/p) for p in inputs};wheel,=(ROOT/'dist').glob('*.whl')
def save(path,value):path.open('x').write(json.dumps(value,indent=2,default=lambda v:v.tolist(),allow_nan=False)+'\n')
kind=sys.argv[1]
if kind=='prepare':
 record=dict(scope='Fixed-pad paired in-plane development comparison, not full convergence/F03/acceptance',pools=pools,jit_disabled=True,sources=sources,wheel_sha256=sha(wheel),installed_anysolver=str(anysolver.__file__),cases={})
 for nx,ny in ((10,4),(20,8),(40,16)):
  for name in ('Mx','Fy'):
   case=ROOT/f'ccx-{nx}x{ny}-{name}-v1';case.mkdir(exist_ok=False)
   deck,metadata,area=build_case(name,nx,ny)
   rows=3*len(metadata['physical_nodes']);assert rows<=100000
   (case/'reference.inp').open('x',encoding='ascii').write(deck)
   save(case/'metadata.json',metadata)
   record['cases'][f'{nx}x{ny}-{name}']=dict(rows=rows,elements=len(metadata['elements']),deck_sha256=sha(case/'reference.inp'),map_identity=area.identity)
 save(ROOT/'paired-binding-v1.json',record);print(json.dumps(record['cases']))
else:
 binding=json.loads((ROOT/'paired-binding-v1.json').read_text())
 assert binding['sources']==sources and binding['wheel_sha256']==sha(wheel)
 if kind=='native':
  nx,ny=map(int,sys.argv[2:]);start=time.monotonic();result=native_cases(nx,ny)
  result.update(runtime_seconds=time.monotonic()-start,pools=threadpool_info(),sources=sources,wheel_sha256=sha(wheel),installed_anysolver=str(anysolver.__file__))
  assert all(p['num_threads']==1 for p in result['pools'])
  save(ROOT/f'native-{nx}x{ny}-result-v1.json',result)
  print(json.dumps(dict(nx=nx,ny=ny,hosts=len(result['hosts']),factors=result['factors'],pairing_J={n:r['external_final_pairing_J'] for n,r in result['results'].items()})))
 elif kind=='parse':
  result=dict(scope='Paired in-plane comparison; thickness fixed; no converged accuracy/acceptance',sources=sources,wheel_sha256=sha(wheel),levels={})
  for nx,ny in ((10,4),(20,8),(40,16)):
   native=json.loads((ROOT/f'native-{nx}x{ny}-result-v1.json').read_text());assert native['sources']==sources
   level={}
   for name in ('Mx','Fy'):
    case=ROOT/f'ccx-{nx}x{ny}-{name}-v1'
    assert sha(case/'reference.inp')==binding['cases'][f'{nx}x{ny}-{name}']['deck_sha256']
    execution=json.loads((case/'execution-v1/execution.json').read_text());assert execution['status']=='completed' and execution['exit_code']==0
    parsed=parse_result((case/'reference.dat').read_text(),(case/'execution-v1/stdout.log').read_text(),json.loads((case/'metadata.json').read_text()))
    save(case/'parsed-v1.json',parsed)
    base=parsed['external_final_pairing_J'];cand=native['results'][name]['external_final_pairing_J']
    level[name]=dict(native_pairing_J=cand,solid_pairing_J=base,relative_pairing_difference=(cand-base)/base,solid_print_bound_J=parsed['pairing_print_bound_J'],root_wrench_error=parsed['root_wrench_error'],root_wrench_print_bounds=parsed['root_wrench_print_bounds'],native_controls=native['results'][name]['controls'],native_port_translation_m=native['results'][name]['port_translation_m'],solid_port_translation_m=parsed['observable']['port_translation_m'],native_rotation_rad=native['results'][name]['port_rotation_rad'],solid_rotation_rad=parsed['observable']['rotation_components_rad'])
   result['levels'][f'{nx}x{ny}']=level
  save(ROOT/'paired-comparison-v1.json',result)
  print(json.dumps({k:{n:dict(native=r['native_pairing_J'],solid=r['solid_pairing_J'],difference=r['relative_pairing_difference']) for n,r in v.items()} for k,v in result['levels'].items()}))
 else:raise ValueError('declared action required')
