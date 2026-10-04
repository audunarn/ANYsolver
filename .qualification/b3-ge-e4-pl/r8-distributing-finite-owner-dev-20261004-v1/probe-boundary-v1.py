from pathlib import Path
import hashlib,importlib,importlib.metadata,json,os,runpy,sys,time
import numpy as np,pytest,anysolver
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];kind=os.environ['R8_MULTIH_HOST_KIND']
FEM=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
FEMRAW=ROOT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
product=REPO/'src' if kind=='consumer-source' else ROOT/'site'
assert Path(anysolver.__file__).resolve().is_relative_to(product)
names=('stiffened_shell','_stiffened_shell_ge_experimental','_stiffened_shell_ge_finite_experimental','_stiffened_shell_ge_distributing_finite','_stiffened_shell_ge_checkpoint_binary','_stiffened_shell_ge_body_load','_stiffened_shell_ge_distributed_load','_stiffened_shell_ge_pressure_load','_stiffened_shell_ge_reference_modal','_stiffened_shell_distributing_pose','_stiffened_shell_ge_distributing_reference','_stiffened_shell_distributing_footprint')
imports={}
for name in names:
 p=Path(importlib.import_module('anysolver.'+name).__file__).resolve()
 assert p==product/'anysolver'/(name+'.py') and sha(p)==sha(REPO/'src/anysolver'/(name+'.py'))
 imports[str(p)]=sha(p)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
wheel=next((ROOT/'dist').glob('*.whl'),None)
tests=[str(REPO/'tests'/p) for p in ('test_stiffened_shell_distributing_footprint.py','test_stiffened_shell_ge_distributing_reference.py','test_stiffened_shell_ge_distributing_owner.py','test_stiffened_shell_ge_distributing_finite_public.py','test_stiffened_shell_ge_distributing_finite.py','test_stiffened_shell_distributing_pose.py')]
if kind in ('consumer','consumer-source'):
 for name in ('solve.stiffened_shell','solve.stiffened_shell_project','model.records','io.project_file'):
  p=Path(importlib.import_module('anyfem.'+name).__file__).resolve()
  assert p==(FEM/'src/anyfem' if kind=='consumer-source' else ROOT/'fem-site/anyfem')/(name.replace('.','/')+'.py') and sha(p)==sha(FEM/'src/anyfem'/(name.replace('.','/')+'.py'))
  imports[str(p)]=sha(p)
 tests=[str(FEM/'tests/test_stiffened_shell_ge_distributing_consumer.py'),*[str(FEM/'tests/test_stiffened_shell_nodal_footprint_consumer.py')+'::'+n for n in ('test_strict_input_and_project_roundtrip_preserve_groups_without_assembly','test_legacy_point_schema_is_unchanged_and_rejects_footprint_fields','test_project_dispatch_preserves_explicit_linear_and_finite_selection')],str(FEM/'tests/test_stiffened_shell_ge_reference_modal_consumer.py')+'::test_from_definition_rejects_unverified_attachment_and_material_scope']
record=dict(scope='Finite distributing owner/legacy reference/consumer compatibility installed integration, not scientific/release acceptance',kind=kind,imports=imports,pools=pools,wheel_sha256=None if wheel is None else sha(wheel),wheel_bytes=None if wheel is None else wheel.stat().st_size,fem_wheel_sha256=None if kind=='consumer-source' or kind not in ('consumer',) else sha(next((ROOT/'fem-dist').glob('*.whl'))),tests={p:sha(Path(p.split('::')[0])) for p in tests},versions={n:importlib.metadata.version(n) for n in ('numpy','scipy','pytest','ANYmaterial','ANYmesher','ANYfileio')})
out=ROOT/(kind+'-runtime-v1.json');out.open('x').write(json.dumps(record,indent=2)+'\n');start=time.monotonic()
if kind=='example':
 example=REPO/'examples/stiffened_shell_ge_distributing_finite.py';sys.path.insert(0,str(example.parent));record['example_sha256']=sha(example)
 runpy.run_path(str(example),run_name='__main__');status=0
else:status=pytest.main(['-q',*tests,'-p','no:cacheprovider','--basetemp',str(ROOT/(kind+'-pytest-v1'))])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-start)
out.write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(status)
