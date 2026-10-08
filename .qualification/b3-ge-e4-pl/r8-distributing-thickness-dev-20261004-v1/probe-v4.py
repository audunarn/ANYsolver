from pathlib import Path
import hashlib,json,os,sys,time
import numpy as np,pytest
from threadpoolctl import threadpool_info
from scripts.r8_e02_distributing_thickness import build_case,parse_result
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
OLD=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.open('x',encoding='utf-8').write(json.dumps(v,indent=2)+'\n')
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
sources={p:sha(REPO/p) for p in ('scripts/r8_e02_distributing_thickness.py','scripts/r8_e02_distributing_feasibility.py','scripts/r8_e02_distributing_solid_area.py','scripts/r8_e02_rigid_tip_reference.py')}
kind=sys.argv[1];start=time.monotonic()
if kind=='checks':
 tests=('tests/test_r8_e02_distributing_thickness.py','tests/test_r8_e02_distributing_feasibility.py','tests/test_r8_e02_distributing_solid_area.py')
 record=dict(scope='Diagnostic helper and unchanged legacy exact-output controls, not acceptance',pools=pools,sources=sources,tests={p:sha(REPO/p) for p in tests})
 save(ROOT/'checks-runtime-v1.json',record)
 status=pytest.main(['-q',*[str(REPO/p) for p in tests],'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v1')])
 record.update(exit_code=int(status),elapsed_seconds=time.monotonic()-start)
 (ROOT/'checks-runtime-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');raise SystemExit(status)
elif kind=='prepare':
 executable=Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
 digest='27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
 assert sha(executable)==digest
 binding=dict(scope='ONE fixed40x16/nz4 Mx/Fy reference sensitivity; no acceptance/F03',sources=sources,pools=pools,executable=str(executable),executable_sha256=digest,cases={})
 for name in ('Mx','Fy'):
  text,metadata,area=build_case(name);case=ROOT/('ccx-'+name+'-v1');case.mkdir()
  (case/'reference.inp').open('x',encoding='ascii',newline='').write(text);save(case/'metadata.json',metadata)
  binding['cases'][name]=dict(rows=3*len(metadata['physical_nodes']),elements=len(metadata['elements']),deck_sha256=sha(case/'reference.inp'),map_identity=area.identity)
 save(ROOT/'binding-v4.json',binding);print(json.dumps(binding['cases']))
elif kind=='parse':
 binding=json.loads((ROOT/'binding-v4.json').read_text(encoding='utf-8'));assert binding['sources']==sources

 for rel,expected in binding['drivers'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected
 assert hashlib.sha256(Path(binding['prior_comparison']).read_bytes()).hexdigest()==binding['prior_comparison_sha256']
 prior=json.loads(Path(binding['prior_comparison']).read_text(encoding='utf-8'))
 results={}
 for name in ('Mx','Fy'):
  case=ROOT/('ccx-'+name+'-v1');assert sha(case/'reference.inp')==binding['cases'][name]['deck_sha256']
  event=json.loads((case/'execution-v4/execution.json').read_text(encoding='utf-8'));assert event['status']=='completed' and event['exit_code']==0
  stderr=(case/'execution-v4/stderr.log').read_text();assert not stderr.strip()
  sta=(case/'reference.sta').read_text();assert len(sta.splitlines())==3 and sta.splitlines()[-1].split()==['1','1','1','1','0.100000E+01','0.100000E+01','0.100000E+01']
  parsed=parse_result((case/'reference.dat').read_text(),(case/'execution-v4/stdout.log').read_text(),json.loads((case/'metadata.json').read_text(encoding='utf-8')))
  save(case/'parsed-v4.json',parsed)
  base=prior['levels']['40x16'][name];work=parsed['external_final_pairing_J']
  results[name]=dict(old_solid_pairing_J=base['solid_pairing_J'],new_solid_pairing_J=work,
    native_pairing_J=base['native_pairing_J'],reference_change_relative=(work-base['solid_pairing_J'])/base['solid_pairing_J'],
    native_difference_relative=(base['native_pairing_J']-work)/work,
    observable=parsed['observable'],print_bound_J=parsed['pairing_print_bound_J'],
    root_wrench_error=parsed['root_wrench_error'],root_wrench_print_bounds=parsed['root_wrench_print_bounds'],root_displacement_max=parsed['root_displacement_max'])
  assert all(abs(e)<=b for e,b in zip(parsed['root_wrench_error'],parsed['root_wrench_print_bounds']))
  assert parsed['root_displacement_max']==0.
 record=dict(scope='Thickness sensitivity only; no convergence/accuracy/F04/F03 acceptance',sources=sources,pools=pools,prior_comparison_sha256=sha(OLD/'paired-comparison-v1.json'),results=results)
 save(ROOT/'comparison-v4.json',record);print(json.dumps({k:{n:v[n] for n in ('reference_change_relative','native_difference_relative')} for k,v in results.items()}))
else:raise ValueError('declared diagnostic action required')
