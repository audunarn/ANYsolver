"""Installed verification of saved active mixed prefix; no loading retry."""
from pathlib import Path
import hashlib,json,sys
import xml.etree.ElementTree as ET
import numpy as np
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer

root=Path(__file__).resolve().parent;repo=root.parents[2]
previous=root.parent/'r8-native-plastic-s3-displacement-dev-20261005-v1'
site=previous/'site-v1';fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
sources={}
for package,checkout in (('anysolver',repo),('anyfem',fem)):
    for p in (site/package).rglob('*.py'):
        rel=p.relative_to(site)
        assert p.read_bytes()==(checkout/'src'/rel).read_bytes(),rel
        sources[rel.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
artifacts=json.loads((previous/'artifact-v1.json').read_text(encoding='utf-8'))['artifacts']
for artifact in artifacts.values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest()==artifact['sha256']
test=repo/'tests/test_stiffened_shell_native_mixed_j2_displacement_snapshot.py'
record=dict(scope='Saved active Q4/S3 mixed prefix installed replay/recovery only; full history FAILED',
    artifacts=artifacts,sources=sources,test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),
    pools=threadpool_info(),source_parent='189ebb84')
status=pytest.main(['-q',str(test),'-p','no:cacheprovider','--basetemp',str(root/'pytest-prefix-v1'),
                  '--junitxml',str(root/'installed-prefix-v1.xml')])
record['pytest_exit_code']=int(status)
if status:raise SystemExit(status)
from test_stiffened_shell_native_plastic_s3_displacement import definition,compare
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
model=definition(True,True)
panel=consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
                                      q4_pullback_policy=model.q4_pullback_policy)
directory=root/'consumer-prefix-v1';directory.mkdir()
consumer.save_case(panel,directory/'case.anyfem-ge.json')
assert consumer.load_case(directory/'case.anyfem-ge.json').to_dict()==panel.to_dict()
project=Project('actual active mixed prefix',mesh_only=True)
analysis=AnalysisDefinition.experimental_point_panel('saved prefix',panel);project.add_analysis(analysis)
saved=save_project(project,directory/'panel.anyfem')
reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.to_dict()==panel.to_dict()
owner=reopened.create_analysis();oracle=ss.create_analysis(definition=model)
try:
    raw=(root/'program-accepted-1-v1.checkpoint').read_bytes()
    result=owner.restore(raw);reference=oracle.restore(raw);compare(result,reference)
    assert owner.checkpoint()==oracle.checkpoint()==raw
    assert all(np.max(r.alpha)>0 for r in result.shell_q4_material+result.shell_s3_material)
    record.update(status='PREFIX_VERIFIED_FULL_HISTORY_OPEN',case_project_roundtrip=True,
        exact_restore=True,actual_q4_s3_flow=True,production_qualified=False,
        equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max)
    (root/'installed-prefix-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('sources','artifacts','pools')}),flush=True)
finally:owner.close();oracle.close()
