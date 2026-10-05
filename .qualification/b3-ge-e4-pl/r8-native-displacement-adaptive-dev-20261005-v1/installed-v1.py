"""Installed native adaptive lifecycle and unchanged consumer integration."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken,SolveCancelled
import anyfem.solve.stiffened_shell as consumer

root=Path(__file__).resolve().parent;repo=root.parents[2];site=root/'site-v3'
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
sources={}
for package,checkout in (('anysolver',repo),('anyfem',fem)):
    for p in (site/package).rglob('*.py'):
        rel=p.relative_to(site)
        assert p.read_bytes()==(checkout/'src'/rel).read_bytes(),rel
        sources[rel.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
artifacts=json.loads((root/'artifact-v3.json').read_text(encoding='utf-8'))['artifacts']
for item in artifacts.values():
    assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest()==item['sha256']
names=('native_displacement_adaptive','displacement_adaptive','native_point_displacement',
       'native_fibre_s3_displacement_identity','native_mixed_j2_displacement_snapshot',
       'displacement_s3_checkpoint_binary','native_plastic_s3_displacement')
tests=[repo/f'tests/test_stiffened_shell_{name}.py' for name in names]
record=dict(scope='Installed native adaptive displacement development; not qualification',
    source_parent='4fecd1ea',artifacts=artifacts,sources=sources,pools=threadpool_info(),
    tests={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tests})
status=pytest.main(['-q',*map(str,tests),'-p','no:cacheprovider',
    '--basetemp',str(root/'pytest-installed-v1'),'--junitxml',str(root/'installed-v1.xml')])
record['pytest_exit_code']=int(status)
if status:
    (root/'installed-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(status)
from test_stiffened_shell_native_plastic_s3_displacement import definition,compare
from test_stiffened_shell_native_point_displacement import ACTIONS,DIRECTION,CONTROL,OPTIONS
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
model=definition(False,False)
panel=consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
    q4_pullback_policy=model.q4_pullback_policy)
directory=root/'consumer-v1';directory.mkdir()
consumer.save_case(panel,directory/'case.anyfem-ge.json')
assert consumer.load_case(directory/'case.anyfem-ge.json').to_dict()==panel.to_dict()
project=Project('native adaptive S3 material',mesh_only=True)
analysis=AnalysisDefinition.experimental_point_panel('adaptive',panel);project.add_analysis(analysis)
saved=save_project(project,directory/'panel.anyfem')
reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.to_dict()==panel.to_dict()
owner=reopened.create_analysis();restored=reopened.create_analysis();oracle=ss.create_analysis(definition=model)
try:
    seed=owner.solve(ACTIONS,(.05,),**OPTIONS)
    initial=float(owner._finite_driver._state.q[CONTROL.dof(owner)])
    targets=(initial*1.01,initial*1.02)
    kw=dict(OPTIONS,displacement_control=CONTROL,increment_control=ss.AdaptiveIncrementControl(2,8))
    token=CancellationToken()
    try:
        owner.solve(DIRECTION,targets,**kw,cancellation_token=token,
                    on_accepted=lambda result:token.cancel('public adaptive prefix'))
    except SolveCancelled:pass
    else:raise AssertionError('consumer cancellation did not preserve prefix')
    prefix=owner.checkpoint();(root/'public-prefix-v1.checkpoint').write_bytes(prefix)
    restored.restore(prefix);oracle.restore(prefix)
    result=owner.solve(DIRECTION,targets,**kw)
    compare(result,restored.solve(DIRECTION,targets,**kw))
    compare(result,oracle.solve(DIRECTION,targets,**kw))
    assert owner.checkpoint()==restored.checkpoint()==oracle.checkpoint()
    assert result.status=='completed' and not result.production_qualified
    assert np.any(np.concatenate([x.alpha for x in result.shell_s3_material])>
                  np.concatenate([x.alpha for x in seed.shell_s3_material]))
    (root/'public-completed-v1.checkpoint').write_bytes(owner.checkpoint())
    record.update(status='PASSED_DEVELOPMENT_NOT_QUALIFIED',case_project_roundtrip=True,
        adaptive_prefix_restore=True,exact_continuation=True,actual_s3_flow=True,
        equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max)
    (root/'installed-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('sources','artifacts','pools','tests')}),flush=True)
finally:owner.close();restored.close();oracle.close()
