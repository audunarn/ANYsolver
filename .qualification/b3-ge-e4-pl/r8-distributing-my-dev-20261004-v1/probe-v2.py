from pathlib import Path
from dataclasses import asdict
import hashlib,json,os,sys,time,zipfile
import numpy as np
from threadpoolctl import threadpool_info
from scripts.r8_e02_distributing_my import build_case,parse_result,native_case
from scripts.r8_e02_distributing_feasibility import _HEADER,_printed_number
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
OLD=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1'
THICK=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-thickness-dev-20261004-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.open('x',encoding='utf-8').write(json.dumps(v,indent=2,allow_nan=False)+'\n')
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
names=('scripts/r8_e02_distributing_my.py','scripts/r8_e02_distributing_thickness.py',
 'scripts/r8_e02_distributing_feasibility.py','scripts/r8_e02_distributing_solid_area.py',
 'scripts/r8_e02_native_rigid_tip.py','scripts/r8_e02_rigid_tip_reference.py')
sources={n:sha(REPO/n) for n in names};kind=sys.argv[1];start=time.monotonic()
if kind=='checks':
 import pytest
 tests=('tests/test_r8_e02_distributing_my.py','tests/test_r8_e02_distributing_thickness.py','tests/test_r8_e02_distributing_feasibility.py')
 record=dict(scope='New My/helper/legacy exact-output controls, not acceptance',sources=sources,pools=pools,tests={n:sha(REPO/n) for n in tests})
 save(ROOT/'checks-runtime.json',record)
 code=pytest.main(['-q',*[str(REPO/n) for n in tests],'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-scratch')])
 record.update(exit_code=int(code),seconds=time.monotonic()-start)
 (ROOT/'checks-runtime.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');raise SystemExit(code)
elif kind=='prepare':
 prior=OLD/'paired-comparison-v1.json';assert sha(prior)=='cf6f6c62339ca37008c7ce82fd59fd2d2c1c9ab6b3cff7dd10b165cbd56917b7'
 analysis=THICK/'analysis-v1.json'
 old=json.loads(prior.read_text(encoding='utf-8'));wheel,=(OLD/'dist').glob('*.whl')
 assert sha(wheel)==old['wheel_sha256']
 installed={}
 with zipfile.ZipFile(wheel) as archive:
  for name in archive.namelist():
   if name.startswith('anysolver/') and name.endswith('.py'):
    data=(OLD/'site'/name).read_bytes();assert data==archive.read(name),name
    installed[name]=hashlib.sha256(data).hexdigest()
 ccx=Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
 assert sha(ccx)=='27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
 text,metadata,area=build_case();case=ROOT/'ccx';case.mkdir()
 (case/'reference.inp').open('x',encoding='ascii',newline='').write(text);save(case/'metadata.json',metadata)
 assert 3*len(metadata['physical_nodes'])<=100000 and len(metadata['elements'])==2560
 record=dict(scope='ONE fixed unitMy; no convergence/physical/F03 acceptance',sources=sources,
  drivers={n:sha(ROOT/n) for n in ('run.py','probe.py')},
  prior_inputs={str(p.relative_to(REPO)).replace('\\','/'):sha(p) for p in (prior,analysis,wheel,OLD/'native-40x16-result-v1.json',THICK/'ccx-Mx-v5/parsed-v5.json')},installed_files=installed,
  wheel=str(wheel),wheel_sha256=sha(wheel),executable=str(ccx),executable_sha256=sha(ccx),
  rows=3*len(metadata['physical_nodes']),elements=len(metadata['elements']),deck_sha256=sha(case/'reference.inp'),map_identity=area.identity,pools=pools)
 save(ROOT/'binding-v2.json',record);print(json.dumps({'rows':record['rows'],'cells':record['elements'],'wheel':record['wheel_sha256']}))
elif kind=='native':
 binding=json.loads((ROOT/'binding-v2.json').read_text(encoding='utf-8'))
 # Verify every installed Python file against the ORIGINAL wheel before import.
 imported={}
 with zipfile.ZipFile(binding['wheel']) as archive:
  for name in archive.namelist():
   if name.startswith('anysolver/') and name.endswith('.py'):
    data=(OLD/'site'/name).read_bytes();assert data==archive.read(name),name
    imported[name]=hashlib.sha256(data).hexdigest()
 import anysolver
 assert imported==binding['installed_files']
 assert Path(anysolver.__file__).resolve().is_relative_to(OLD/'site')
 result=native_case()
 assert result['factors']==1 and set(result['results'])=={'My'}
 modules={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items() if name.startswith('anysolver') and getattr(module,'__file__',None)}
 assert all(Path(p).is_relative_to(OLD/'site') for p in modules.values())
 result.update(seconds=time.monotonic()-start,pools=threadpool_info(),sources=sources,wheel_sha256=binding['wheel_sha256'],installed_files=imported,actual_imports=modules)
 assert all(p['num_threads']==1 for p in result['pools'])
 save(ROOT/'native.json',result);print(json.dumps({'factors':result['factors'],'work':result['results']['My']['external_final_pairing_J']}))
elif kind=='compare':
 case=ROOT/'ccx';event=json.loads((case/'execution/execution.json').read_text(encoding='utf-8'))
 assert event['status']=='completed' and event['exit_code']==0
 assert not (case/'execution/stderr.log').read_text().strip()
 assert (case/'reference.sta').read_text().splitlines()[-1].split()==['1','1','1','1','0.100000E+01','0.100000E+01','0.100000E+01']
 metadata=json.loads((case/'metadata.json').read_text(encoding='utf-8'))
 dat=(case/'reference.dat').read_text();parsed=parse_result(dat,(case/'execution/stdout.log').read_text(),metadata)
 assert all(abs(e)<=b for e,b in zip(parsed['root_wrench_error'],parsed['root_wrench_print_bounds']))
 assert parsed['root_displacement_max']==0.
 save(case/'parsed.json',parsed)
 binding=json.loads((ROOT/'binding-v2.json').read_text(encoding='utf-8'))
 nevent=json.loads((ROOT/'native/execution.json').read_text(encoding='utf-8'))
 assert nevent['status']=='completed' and nevent['exit_code']==0
 assert not (ROOT/'native/stderr.log').read_text().strip()
 native=json.loads((ROOT/'native.json').read_text(encoding='utf-8'))
 assert native['sources']==binding['sources'] and native['wheel_sha256']==binding['wheel_sha256']
 assert native['installed_files']==binding['installed_files']
 assert native['actual_imports'] and all(Path(p).is_relative_to(OLD/'site') for p in native['actual_imports'].values())
 n=native['results']['My']
 analysis=json.loads((THICK/'analysis-v1.json').read_text(encoding='utf-8'))['results']['40x16']
 _,_,area=build_case();headers=list(_HEADER.finditer(dat));ub={}
 for i,h in enumerate(headers):
  if (h[1].lower(),h[2].upper())!=('displacements','ALL'):continue
  end=headers[i+1].start() if i+1<len(headers) else len(dat)
  for line in dat[h.end():end].splitlines():
   if line.strip():
    node,*fields=line.split();ub[int(node)]=[_printed_number(s)[1] for s in fields]
 bounds=np.sum([np.abs(w)@ub[node] for node,w in zip(area.node_ids,area.weights)],axis=0)
 observed=parsed['observable'];ref=parsed['external_final_pairing_J'];cand=n['external_final_pairing_J']
 old=analysis['solid_nz4'];cross=observed['rotation_components_rad'][0]-old['Mx_pose'][4]
 record=dict(scope='One independent moment; no convergence/F04/F03 acceptance',sources=sources,pools=pools,
  native=n,solid=parsed,solid_pose_decimal_bounds=bounds.tolist(),
  direct_My_difference_relative=(cand-ref)/ref,
  native_reciprocity_difference=n['port_rotation_rad'][0]-analysis['native']['Mx_pose'][4],
  solid_reciprocity_difference=cross,solid_reciprocity_decimal_bound=float(bounds[3]+old['Mx_pose_decimal_bounds'][4]),
  output_hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'native.json',case/'reference.dat',case/'parsed.json')})
 save(ROOT/'comparison.json',record)
 print(json.dumps({k:record[k] for k in ('direct_My_difference_relative','native_reciprocity_difference','solid_reciprocity_difference','solid_reciprocity_decimal_bound')}))
else:raise ValueError('declared bounded action required')
