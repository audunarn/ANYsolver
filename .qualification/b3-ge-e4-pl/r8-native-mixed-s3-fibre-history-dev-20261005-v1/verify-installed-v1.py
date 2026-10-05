"""Installed simultaneous history test, public example and actual consumer restart."""
from pathlib import Path
import hashlib,json,sys,math
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer

root=Path(__file__).resolve().parent;repo=root.parents[2]
previous=root.parent/'r8-native-displacement-adaptive-dev-20261005-v1'
site=previous/'site-v3';fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
installed=json.loads((previous/'installed-result-v1.json').read_text())
for name,digest in installed['sources'].items():
    checkout=repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()==digest,name
    assert hashlib.sha256((site/name).read_bytes()).hexdigest()==digest,name
for item in installed['artifacts'].values():
    assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest()==item['sha256']
test=repo/'tests/test_stiffened_shell_native_s3_fibre_reversal.py'
fixture=repo/'tests/data/native_s3_fibre_history/unloaded-v1.bin'
assert fixture.read_bytes()==(root/'reversal-accepted-1-v1.checkpoint').read_bytes()
record=dict(scope='Installed all-S3/fibre signed history development, not qualification',
    source_parent='8e9121e1',artifacts=installed['artifacts'],sources=installed['sources'],pools=threadpool_info(),
    test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest())
status=pytest.main(['-q',str(test),'-p','no:cacheprovider','--basetemp',str(root/'pytest-installed-v1'),
                   '--junitxml',str(root/'installed-v1.xml')])
record['pytest_exit_code']=int(status)
if status:raise SystemExit(status)
from examples.stiffened_shell_coupled_s3_adaptive_history import definition,workflow,DIRECTION,CONTROL,OPTIONS,LIMITS
from test_stiffened_shell_native_plastic_s3_displacement import compare
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
public=workflow(root/'public-example-v1')
record['public_example']=public
model=definition();panel=consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
    q4_pullback_policy=model.q4_pullback_policy)
directory=root/'consumer-v1';directory.mkdir()
consumer.save_case(panel,directory/'case.anyfem-ge.json')
assert consumer.load_case(directory/'case.anyfem-ge.json').to_dict()==panel.to_dict()
project=Project('simultaneous S3 and fibre reversal',mesh_only=True)
analysis=AnalysisDefinition.experimental_point_panel('signed history',panel);project.add_analysis(analysis)
saved=save_project(project,directory/'panel.anyfem')
reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.to_dict()==panel.to_dict()
owner=reopened.create_analysis();oracle=ss.create_analysis(definition=model)
try:
    prefix=(root/'public-example-v1/unloaded.checkpoint').read_bytes()
    owner.restore(prefix)
    assert owner.checkpoint()==prefix
    nominal=public['reference_nominal_target'];targets=(nominal*.25,-nominal,nominal*1.1)
    result=owner.solve(DIRECTION,targets,displacement_control=CONTROL,increment_control=LIMITS,**OPTIONS)
    final=(root/'public-example-v1/completed.checkpoint').read_bytes()
    reference=oracle.restore(final);compare(result,reference)
    assert owner.checkpoint()==final and result.increment_attempts==reference.increment_attempts
    assert result.status=='completed' and not result.production_qualified
    record.update(status='PASSED_S3_FIBRE_REVERSE_RESTART_NOT_QUALIFIED',
        case_project_roundtrip=True,exact_unload_prefix_continue=True,
        positive_final_dissipation=math.fsum(math.fsum(x.incremental_dissipation_j) for x in result.beam_fibre_energy)>0.,
        equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max)
    record['example_sha256']=hashlib.sha256((repo/'examples/stiffened_shell_coupled_s3_adaptive_history.py').read_bytes()).hexdigest()
    (root/'installed-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('sources','artifacts','pools','public_example')}),flush=True)
finally:owner.close();oracle.close()
