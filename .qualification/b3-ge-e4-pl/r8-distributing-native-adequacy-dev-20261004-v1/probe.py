from pathlib import Path
import hashlib,json,os,sys,time,zipfile
import numpy as np
from threadpoolctl import threadpool_info
from scripts.r8_e02_distributing_native_adequacy import geometry,native_case
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
BASE=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1'
MY=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-my-dev-20261004-v1'
THICK=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-thickness-dev-20261004-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def convert(v):
 if isinstance(v,np.ndarray):return v.tolist()
 raise TypeError('unsupported diagnostic type '+type(v).__name__)
def save(p,v):
 text=json.dumps(v,indent=2,allow_nan=False,default=convert)+'\n';p.open('x',encoding='utf-8').write(text)
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
names=('scripts/r8_e02_distributing_native_adequacy.py','scripts/r8_e02_distributing_feasibility.py','scripts/r8_e02_native_rigid_tip.py')
sources={n:sha(REPO/n) for n in names};kind=sys.argv[1];start=time.monotonic()
if kind=='checks':
 import pytest
 tests=('tests/test_r8_e02_distributing_native_adequacy.py','tests/test_r8_e02_distributing_my.py','tests/test_r8_e02_distributing_thickness.py','tests/test_r8_e02_distributing_feasibility.py')
 record=dict(sources=sources,pools=pools,tests={n:sha(REPO/n) for n in tests});save(ROOT/'checks-runtime.json',record)
 code=pytest.main(['-q',*[str(REPO/n) for n in tests],'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-scratch')])
 record.update(exit_code=int(code),seconds=time.monotonic()-start)
 (ROOT/'checks-runtime.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');raise SystemExit(code)
elif kind=='prepare':
 baseline=BASE/'paired-comparison-v1.json';assert sha(baseline)=='cf6f6c62339ca37008c7ce82fd59fd2d2c1c9ab6b3cff7dd10b165cbd56917b7'
 wheel,=(BASE/'dist').glob('*.whl');assert sha(wheel)==json.loads(baseline.read_text(encoding='utf-8'))['wheel_sha256']
 installed={}
 with zipfile.ZipFile(wheel) as z:
  for name in z.namelist():
   if name.startswith('anysolver/') and name.endswith('.py'):
    data=(BASE/'site'/name).read_bytes();assert data==z.read(name);installed[name]=hashlib.sha256(data).hexdigest()
 nodes,cells,_,_,_=geometry(80,32)
 save(ROOT/'binding.json',dict(scope='ONE native80x32 Mx/My adequacy discriminator; no asymptotic/acceptance claim',
  sources=sources,drivers={n:sha(ROOT/n) for n in ('run.py','probe.py')},
  prior_inputs={str(p.relative_to(REPO)).replace('\\','/'):sha(p) for p in (baseline,wheel,MY/'comparison-v3.json',THICK/'analysis-v1.json')},
  wheel=str(wheel),wheel_sha256=sha(wheel),installed_files=installed,physical_retained_count=6*len(nodes)+42,rows=6*len(nodes)+42+6,cells=len(cells),pools=pools))
 print(json.dumps({'rows':6*len(nodes)+48,'cells':len(cells)}))
elif kind=='native':
 binding=json.loads((ROOT/'binding.json').read_text(encoding='utf-8'));assert sources==binding['sources']
 for name,digest in binding['installed_files'].items():assert sha(BASE/'site'/name)==digest
 import anysolver
 assert Path(anysolver.__file__).resolve().is_relative_to(BASE/'site')
 result=native_case();assert result['factors']==1 and set(result['results'])=={'Mx','My'}
 modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if n.startswith('anysolver') and getattr(m,'__file__',None)}
 assert modules and all(Path(p).is_relative_to(BASE/'site') for p in modules.values())
 result.update(seconds=time.monotonic()-start,sources=sources,pools=threadpool_info(),wheel_sha256=binding['wheel_sha256'],actual_imports=modules)
 assert all(p['num_threads']==1 for p in result['pools'])
 save(ROOT/'native.json',result);print(json.dumps({'factors':result['factors'],'work':{n:r['external_final_pairing_J'] for n,r in result['results'].items()}}))
elif kind=='compare':
 event=json.loads((ROOT/'native/execution.json').read_text(encoding='utf-8'));assert event['status']=='completed' and event['exit_code']==0
 assert not (ROOT/'native/stderr.log').read_text().strip()
 binding=json.loads((ROOT/'binding.json').read_text(encoding='utf-8'));native=json.loads((ROOT/'native.json').read_text(encoding='utf-8'))
 assert native['sources']==binding['sources'] and native['wheel_sha256']==binding['wheel_sha256']
 assert native['actual_imports'] and all(Path(p).is_relative_to(BASE/'site') for p in native['actual_imports'].values())
 old=json.loads((BASE/'paired-comparison-v1.json').read_text(encoding='utf-8'))['levels']['40x16']['Mx']
 my=json.loads((MY/'comparison-v3.json').read_text(encoding='utf-8'))
 reference=json.loads((THICK/'analysis-v1.json').read_text(encoding='utf-8'))['results']['40x16']['solid_nz4']
 results={}
 for name,coarse,solid in (('Mx',old['native_pairing_J'],reference['Mx_pose'][3]),('My',my['native']['external_final_pairing_J'],my['solid']['external_final_pairing_J'])):
  r=native['results'][name];value=r['external_final_pairing_J']
  results[name]=dict(old_native_work_J=coarse,new_native_work_J=value,solid_work_J=solid,mesh_pair_change_relative=(value-coarse)/coarse,
   native_reference_difference_relative=(value-solid)/solid,port_translation_m=r['port_translation_m'],rotation_rad=r['port_rotation_rad'],controls=r['controls'])
 x=results['Mx']['rotation_rad'][1];y=results['My']['rotation_rad'][0]
 record=dict(scope='Measured native mesh-pair stability only; no extrapolation/convergence/F04/F03 pass',sources=sources,pools=pools,results=results,
  cross_coupling_Mx_to_pitch=x,cross_coupling_My_to_roll=y,reciprocity_difference=x-y,
  saved_native40_cross=old['native_rotation_rad'][1],solid_cross=reference['Mx_pose'][4],native_result_sha256=sha(ROOT/'native.json'))
 save(ROOT/'comparison.json',record);print(json.dumps({'works':results,'cross':x,'reciprocity':x-y}))
else:raise ValueError('declared job required')
