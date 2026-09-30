from pathlib import Path
import hashlib,json,sys,zipfile
from importlib import metadata

import numpy as np
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
        ('numpy','scipy','numba','pytest','threadpoolctl','mpmath','ANYmaterial','ANYmesher','ANYfileio')}}
(root/'identity.json').write_text(json.dumps({'artifacts':artifacts,'environment':environment},indent=2)+'\n')
print(json.dumps(environment),flush=True)
selected=[root/'tests'/name for name in (
    'test_stiffened_shell_b2_q4_point_experimental.py',
    'test_stiffened_shell_b2_q4_panel_experimental.py',
    'test_b2_f10_f11_point_attachment.py',
    'test_b2_f10_f11_s3_point_attachment.py')]
selected.append(root/'consumer-tests/test_experimental_b2_stiffened_shell_consumer.py')
code=pytest.main(['-q','-c',str(root/'pytest.ini'),'--junitxml',str(root/'inventory.xml'),
                 '--basetemp',str(root/'pytest-tmp')]+[str(p) for p in selected])
if code:raise SystemExit(code)
from scripts.experimental_stiffened_ge_bl5_reference_panel import make_definition,run
import anysolver
from anysolver import stiffened_shell as ss
report=run()
assert Path(report['source']).resolve().is_relative_to(site)
assert report['qualification']=='experimental' and report['factorizations']==1
(root/'example.json').write_text(json.dumps(report,indent=2)+'\n')

# Independently retained private counterfactual, never re-executed here.
parent=w/'.qualification/b3-ge-e4-pl/r8-bl5-port-boundary-decision-dev-20260930-v1/r8-bl5-port-boundary-control-v2/case'
with np.load(parent/'states.npz',allow_pickle=False) as saved:
    expected=saved['corrected'].copy();lam=saved['corrected_lambda'].copy()
owner=ss.create_analysis(definition=make_definition())
try:
    actual=owner.solve_linear((ss.NodalAction('beam',117,(0.,0.,0.,10.,0.,0.)),))
    q=np.r_[actual.shell_displacement,actual.beam_coordinates];n=6*(34+17)
    pairs={'physical_nodal':(q[:n],expected[:n]),
        'retained_rotations':(q[n:].reshape(-1,24)[:,:6],expected[n:].reshape(-1,24)[:,:6]),
        'retained_resultants':(q[n:].reshape(-1,24)[:,6:],expected[n:].reshape(-1,24)[:,6:]),
        'weak_multipliers':(actual.multipliers,lam[:80])}
    parity={k:float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-20)) for k,(a,b) in pairs.items()}
    control={'role_relative_parity':parity,'criterion':1e-10,
        'parent_states_sha256':sha(parent/'states.npz'),
        'parent_report_sha256':sha(parent/'report.json'),
        'source':anysolver.__file__,
        'semantics':'Reference-linear ground supports equivalent in displacement to comparator nodal root ties; reactions retain different provenance.'}
    (root/'support-control.json').write_text(json.dumps(control,indent=2)+'\n')
    np.savez_compressed(root/'support-states.npz',actual=q,expected=expected,
                        actual_lambda=actual.multipliers,expected_lambda=lam,reactions=actual.reactions)
    assert max(parity.values())<=1e-10,parity
finally:owner.close()
loaded={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items())
        if n.split('.')[0] in ('anysolver','anyfem') and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(site) for p in loaded.values())
(root/'imports.json').write_text(json.dumps(loaded,indent=2)+'\n')
print(json.dumps({'onsite_imports':len(loaded),'public_support_control':parity,'examples':2}),flush=True)
