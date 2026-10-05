from pathlib import Path
import hashlib,importlib.metadata,importlib.util,json,os,sys,time
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer

raw=Path(__file__).resolve().parent;repo=raw.parents[2]
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
site=raw/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
import scipy.linalg
pools=threadpool_info()
assert pools and all(p['num_threads']==1 for p in pools)
sources={}
for package,checkout in (('anysolver',repo),('anyfem',fem)):
    for path in (site/package).rglob('*.py'):
        relative=path.relative_to(site)
        assert path.read_bytes()==(checkout/'src'/relative).read_bytes(),relative
        sources[relative.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
artifacts=json.loads((raw/'artifact-v1.json').read_text(encoding='utf-8'))['artifacts']
for artifact in artifacts.values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest()==artifact['sha256']
tests=[repo/'tests'/name for name in (
    'test_stiffened_shell_native_point_displacement.py',
    'test_stiffened_shell_native_coupled_displacement.py',
    'test_stiffened_shell_native_s3_displacement.py',
    'test_stiffened_shell_displacement_checkpoint.py',
    'test_stiffened_shell_displacement_corrector.py',
    'test_stiffened_shell_displacement_public.py',
    'test_stiffened_shell_displacement_rebase.py',
    'test_stiffened_shell_curved_material_displacement.py')]
record=dict(scope='Installed elastic mixed/all-S3 native POINT plus affected Q4/BL5/curved displacement controls; not qualification',
    sources=sources,artifacts=artifacts,pools=pools,
    tests={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in tests},
    dependencies={n:importlib.metadata.version(n) for n in ('ANYsolver','ANYfem','ANYmaterial','numpy','scipy','pytest')})
out=raw/'installed-runtime-v1.json'
out.open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
started=time.monotonic()
status=pytest.main(['-q',*[str(p) for p in tests],'-p','no:cacheprovider',
    '--basetemp',str(raw/'pytest-v1'),'-o','junit_family=legacy','--junitxml',str(raw/'installed-v1.xml')])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-started)
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if status:raise SystemExit(status)
example=repo/'examples/stiffened_shell_native_s3_displacement.py'
sys.path.insert(0,str(example.parent))
spec=importlib.util.spec_from_file_location('native_s3_displacement_example',example)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
record['public_examples']={};record['consumers']={}
for all_s3 in (False,True):
    name='all-s3' if all_s3 else 'mixed'
    publicdir=raw/('public-'+name+'-v1')
    public=module.workflow(publicdir,all_s3)
    model=module.definition(all_s3)
    panel=consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
        q4_pullback_policy=model.q4_pullback_policy)
    directory=raw/('consumer-'+name+'-v1');directory.mkdir()
    consumer.save_case(panel,directory/'case.anyfem-ge.json')
    assert consumer.load_case(directory/'case.anyfem-ge.json').to_dict()==panel.to_dict()
    project=Project('experimental native '+name+' displacement',mesh_only=True)
    analysis=AnalysisDefinition.experimental_point_panel('fixed targets',panel)
    project.add_analysis(analysis)
    saved=save_project(project,directory/'panel.anyfem')
    reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id])
    assert reopened.to_dict()==panel.to_dict()
    control=reopened.create_analysis()
    try:
        prefix=(publicdir/'prefix.checkpoint').read_bytes()
        restored=control.restore(prefix)
        assert control.checkpoint()==prefix
        direction=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),)
        final=control.solve(direction,(public['history'][-1][0],),
            displacement_control=ss.DisplacementControl('beam',105,2),max_iterations=20,max_backtracks=12)
        assert control.checkpoint()==(publicdir/'completed.checkpoint').read_bytes()
        assert final.history==tuple(map(tuple,public['history']))
        record['public_examples'][name]=public
        record['consumers'][name]=dict(case_project_roundtrip=True,exact_prefix_restore=True,
            exact_completed_checkpoint=True,production_qualified=False)
        out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    finally:control.close()
record.update(example_sha256=hashlib.sha256(example.read_bytes()).hexdigest(),
    definition_example_sha256=hashlib.sha256((example.parent/'stiffened_shell_ge_gravity.py').read_bytes()).hexdigest())
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('PASS: installed controls, both public S3 meshes, ANYfem experimental roundtrip and exact continuation.',flush=True)
