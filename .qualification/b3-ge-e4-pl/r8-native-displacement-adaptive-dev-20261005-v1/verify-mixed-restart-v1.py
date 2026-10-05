"""Continue the actually accepted adaptive midpoint through the consumer."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anyfem.solve.stiffened_shell import ExperimentalGEPointPanel,save_case,load_case
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
from test_stiffened_shell_native_plastic_s3_displacement import definition,compare
from test_stiffened_shell_native_point_displacement import DIRECTION,CONTROL,OPTIONS

root=Path(__file__).resolve().parent;repo=root.parents[2]
assert Path(ss.__file__).resolve().is_relative_to(root/'site-v3')
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
program=json.loads((root/'program-result-v1.json').read_text())
assert program['status']=='COMPLETED_DEVELOPMENT_NOT_QUALIFIED'
model=definition(True,True)
panel=ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,
    q4_pullback_policy=model.q4_pullback_policy)
directory=root/'consumer-mixed-v1';directory.mkdir()
save_case(panel,directory/'case.anyfem-ge.json')
assert load_case(directory/'case.anyfem-ge.json').to_dict()==panel.to_dict()
project=Project('mixed adaptive accepted midpoint',mesh_only=True)
analysis=AnalysisDefinition.experimental_point_panel('mixed adaptive',panel);project.add_analysis(analysis)
saved=save_project(project,directory/'panel.anyfem')
reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.to_dict()==panel.to_dict()
owner=reopened.create_analysis();oracle=ss.create_analysis(definition=model)
try:
    prefix=(root/'program-accepted-1-v1.checkpoint').read_bytes()
    owner.restore(prefix)
    assert owner.checkpoint()==prefix
    result=owner.solve(DIRECTION,(program['nominal_target'],),displacement_control=CONTROL,
        increment_control=ss.AdaptiveIncrementControl(6,24),**OPTIONS)
    final=(root/'program-prefix-v1.checkpoint').read_bytes()
    reference=oracle.restore(final);compare(result,reference)
    assert owner.checkpoint()==final
    assert result.increment_attempts==reference.increment_attempts
    assert len(result.increment_attempts)==3 and not result.increment_attempts[0].accepted
    assert result.status=='completed' and not result.production_qualified
    assert all(np.max(x.alpha)>0. for x in result.shell_q4_material+result.shell_s3_material)
    record=dict(status='MIXED_ADAPTIVE_RESTART_VERIFIED_NOT_QUALIFIED',
        case_project_roundtrip=True,exact_midpoint_continue=True,
        preserved_rejected_work=True,actual_q4_s3_flow=True,
        completed_sha256=hashlib.sha256(final).hexdigest(),
        equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max)
finally:owner.close();oracle.close()
sys.path.insert(0,str(repo/'examples'))
from stiffened_shell_native_plastic_s3_displacement import workflow
record['public_example']=workflow(root/'example-adaptive-v1',adaptive=True)
record['example_sha256']=hashlib.sha256((repo/'examples/stiffened_shell_native_plastic_s3_displacement.py').read_bytes()).hexdigest()
(root/'mixed-restart-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record),flush=True)
