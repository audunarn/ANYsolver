from pathlib import Path
import hashlib,json,sys,zipfile
from importlib import metadata

import numpy as np
import anysolver
import anysolver._b2_physical_linear_definition
import anysolver._b2_physical_flexibility_linear
import numba,pytest,threadpoolctl

root=Path(__file__).resolve().parent;site=(root/'site').resolve()
w=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'runners-manifest.json').read_text())
assert all(sha(root/p)==h for p,h in manifest['fixtures_sha256'].items())
assert all(sha(root/'wheels'/p)==h for p,h in manifest['wheels_sha256'].items())
source=json.loads((root/'source-manifest.json').read_text())
assert all(sha(w/p)==h for p,h in source['source_sha256'].items())
artifacts={}
for name,src in (('anysolver',w/'src/anysolver'),('anyfem',fem/'src/anyfem')):
    wheel=next((root/'wheels').glob(name+'-*.whl'))
    files={name+'/'+p.relative_to(src).as_posix():p for p in src.rglob('*.py')}
    with zipfile.ZipFile(wheel) as z:
        emitted={p for p in z.namelist() if p.startswith(name+'/') and p.endswith('.py')}
        assert emitted==set(files)
        assert all(p.read_bytes()==z.read(k)==(site/k).read_bytes() for k,p in files.items())
    artifacts[name]={'wheel_sha256':sha(wheel),'matching_modules':len(files),
                     'source_sha256':{k:sha(p) for k,p in files.items()}}
pools=threadpoolctl.threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
environment={'python':sys.version,'executable':sys.executable,'threads':pools,
    'jit_disabled':True,'numba_threads':numba.config.NUMBA_NUM_THREADS,
    'dependencies':{n:metadata.version(n) for n in
        ('numpy','scipy','numba','pytest','threadpoolctl','ANYmaterial','ANYmesher','ANYfileio')}}
(root/'identity.json').write_text(json.dumps({'artifacts':artifacts,'environment':environment},indent=2)+'\n')
print(json.dumps(environment),flush=True)
targets=['tests/test_stiffened_shell_b2_experimental.py', 'tests/test_b2_f13_affine_batch_dev.py', 'tests/test_b2_physical_linear_definition.py', 'tests/test_b2_physical_linear_oriented_graph.py', 'tests/test_b2_physical_linear_trace.py', 'tests/test_stiffened_shell_b2_q4_panel_experimental.py', 'tests/test_stiffened_shell_b2_q4_point_experimental.py', 'tests/test_b2_f10_f11_point_attachment.py', 'tests/test_b2_f10_f11_s3_point_attachment.py', 'consumer-tests/test_experimental_b2_stiffened_shell_consumer.py']
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--basetemp='+str(root/'pytest-tmp'),'--junitxml='+str(root/'inventory.xml'),*targets])
loaded={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('anysolver','anyfem') and getattr(m,'__file__',None)}
(root/'imports.json').write_text(json.dumps(loaded,indent=2)+'\n')
assert all(Path(p).is_relative_to(site) for p in loaded.values())
assert code==0,code
from collections import Counter
import xml.etree.ElementTree as ET
cases=ET.parse(root/'inventory.xml').findall('.//testcase')
assert len(cases)>=120 and all(len(c)==0 for c in cases)
counts=dict(Counter(c.attrib['classname'] for c in cases))
report={'status':'PASSED_DEVELOPMENT_ONLY','installed_cases':len(cases),'inventory':counts,'onsite_imports':len(loaded),'changed_method':'ExperimentalB2Q4PanelAnalysis.solve_linear_many','full_F13_M3':'OPEN'}
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
