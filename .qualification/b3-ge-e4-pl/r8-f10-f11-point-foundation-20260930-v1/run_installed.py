from pathlib import Path
import hashlib,json,os,sys,xml.etree.ElementTree as ET,zipfile
from importlib import metadata
import numpy as np,scipy,numba,pytest,threadpoolctl,anysolver
root=Path(__file__).resolve().parent;site=(root/'site').resolve()
w=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=json.loads((root/'contract.json').read_text())
assert all(sha(root/p)==h for p,h in contract['inputs_sha256'].items())
assert all(sha(w/p)==h for p,h in contract['source_sha256'].items())
wheel=root/'wheels/anysolver-0.4.7-py3-none-any.whl'
with zipfile.ZipFile(wheel) as z:
    emitted={p for p in z.namelist() if p.startswith('anysolver/') and p.endswith('.py')}
    expected={'anysolver/'+Path(p).relative_to('src/anysolver').as_posix() for p in contract['source_sha256']}
    assert emitted==expected
    assert all((site/p).read_bytes()==z.read(p)==(w/'src'/p).read_bytes() for p in emitted)
pools=threadpoolctl.threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
assert sys.version_info[:3]==(3,14,2)
dependencies={n:metadata.version(n) for n in contract['dependencies']}
assert dependencies==contract['dependencies']
identity={'source_commit':contract['source_commit'],'wheel_sha256':sha(wheel),
    'matching_modules':len(emitted),'dependencies':dependencies,'python':sys.version,
    'executable':sys.executable,'threads':pools,'jit_disabled':True,'numba_threads':1}
(root/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
print(json.dumps(identity),flush=True)
reports=root/'reports';assert not reports.exists();reports.mkdir()
os.environ['B2_POINT_FOUNDATION_REPORTS']=str(reports)
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp='+str(root/'pytest-tmp'),
    '--junitxml='+str(root/'inventory.xml'),'tests/test_b2_point_foundation.py'])
loaded={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items())
        if n.split('.')[0]=='anysolver' and getattr(m,'__file__',None)}
(root/'imports.json').write_text(json.dumps(loaded,indent=2)+'\n')
assert all(Path(p).is_relative_to(site) for p in loaded.values())
assert code==0,code
cases=ET.parse(root/'inventory.xml').findall('.//testcase')
assert len(cases)==65 and all(len(c)==0 for c in cases)
positive={f'{kind}-{sign}-{int(coupled)}-{form}.json' for kind in ('q4','s3') for sign in (-1,1)
    for coupled in (False,True) for form in ('base','shift','rotate','units','winding')}
defects=('nonfinite_vertices','collinear','malformed','zero_edge','negative_station','large_station',
    'nonfinite_station','nonfinite_offset','bad_offset','unrepresentable_offset')
negative={f'negative-{kind}-{defect}.json' for kind in ('q4','s3') for defect in defects}
negative|={'negative-q4-nonplanar.json'}|{f'negative-affine-{d}.json' for d in ('dimension','nonfinite_t','nonfinite_u0','dependent_rows')}
assert {p.name for p in reports.glob('*.json')}==positive|negative
maxima={};bending=[]
for name in positive:
    r=json.loads((reports/name).read_text());m=r['metrics']
    assert r['law_id']==contract['law_ids'][r['shell']]
    assert r['scales']=={'length_m':2.,'force_n':1.,'moment_nm':2.,'normalized_floor':1e-12}
    assert r['steps']==[1e-4,3e-5,1e-5]
    assert set(m)==set(contract['limits'])
    for key,limit in contract['limits'].items():
        if isinstance(m[key],list):
            assert len(m[key])==3 and all(np.isfinite(v) for v in m[key]),(name,key,m[key])
        value=max(m[key]) if isinstance(m[key],list) else m[key]
        assert np.isfinite(value) and value<=limit,(name,key,value,limit)
        maxima[key]=max(maxima.get(key,0.),value)
    assert r['rank']==6 and r['bending_rotation_norm']>1e-8
    bending.append(r['bending_rotation_norm'])
rejections={}
for name in negative:
    r=json.loads((reports/name).read_text())
    assert r['rejected'] and r['exception'] in ('ValueError','RepresentabilityError') and r['message']
    rejections[name]=r['exception']
summary={'status':'PASSED_POINT_STATIC_PORTION_ONLY','positive_cases':40,'negative_cases':25,
    'inventory':65,'maxima':maxima,'minimum_bending_rotation_norm':min(bending),
    'negative_rejections':rejections,'onsite_imports':len(loaded),
    'scope':contract['scope'],'general_F10_F11_G0B_F13':'OPEN'}
(root/'assessment.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
