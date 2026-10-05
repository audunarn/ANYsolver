from pathlib import Path
from dataclasses import replace,asdict
import json,hashlib,math,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss,b3_ge
from test_stiffened_shell_native_point_displacement import native_state
from test_stiffened_shell_q4_pullback_owner import _definition
raw=Path(__file__).resolve().parent;repo=raw.parents[2];root=raw/'installed-v1';root.mkdir(exist_ok=False)
previous=raw.parent/'r8-native-displacement-adaptive-dev-20261005-v1'
site=previous/'site-v3'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
identities=json.loads((previous/'installed-result-v1.json').read_text())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
for name,digest in identities['sources'].items():
    checkout=repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()==digest,name
    assert hashlib.sha256((site/name).read_bytes()).hexdigest()==digest,name
definition=_definition(plastic=True,mixed=False)
import pytest
import anyfem.solve.stiffened_shell as consumer
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
from anysolver._stiffened_shell_displacement_adaptive import decode
from test_stiffened_shell_native_generalized_adaptive_history import exact
assert Path(consumer.__file__).resolve().is_relative_to(site)
status=pytest.main(['-q',str(repo/'tests/test_stiffened_shell_native_generalized_q4_j2_history.py'),'--junitxml='+str(root/'junit-v1.xml')])
assert status==0
panel=consumer.ExperimentalGEPointPanel(definition.shell,definition.beams,definition.points,definition.fixed,q4_pullback_policy=definition.q4_pullback_policy)
consumer.save_case(panel,root/'case.anyfem-ge.json')
assert consumer.load_case(root/'case.anyfem-ge.json').to_dict()==panel.to_dict()
project=Project('generalized Q4J2 controller transition',mesh_only=True)
analysis=AnalysisDefinition.experimental_point_panel('yielded reload',panel);project.add_analysis(analysis)
saved=save_project(project,root/'panel.anyfem')
reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id])
assert reopened.to_dict()==panel.to_dict()
owner=reopened.create_analysis();oracle=ss.create_analysis(definition=definition)
try:
    rawcheckpoint=(raw/'transition-outputs-v1/accepted-1-v1.checkpoint').read_bytes()
    previous_result=owner.restore(rawcheckpoint);assert owner.checkpoint()==rawcheckpoint
    context,_=decode(owner,rawcheckpoint)
    result=owner.solve((ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),),context.state.targets,displacement_control=ss.DisplacementControl('beam',105,2),increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12)
    endpoint=(raw/'transition-outputs-v1/prefix-v1.checkpoint').read_bytes();reference=oracle.restore(endpoint)
    exact(result,reference);assert owner.checkpoint()==endpoint
    for a,b in zip(result.shell_q4_material,reference.shell_q4_material,strict=True):
        for name in ('layer_strain','layer_stress','plastic_strain','alpha'):np.testing.assert_array_equal(getattr(a,name),getattr(b,name))
    assert result.increment_attempts==reference.increment_attempts
    force=float(result.applied_dead_load[owner._shell_count+6*owner._beam_index[105]+2])
    assert force==1000.+100.*result.amplitude
    record=dict(status='PASSED_GENERALIZED_Q4J2_RESTART_NOT_QUALIFIED',artifacts=identities['artifacts'],sources=identities['sources'],case_project_roundtrip=True,exact_pending_programme_restart=True,endpoint_sha256=hashlib.sha256(endpoint).hexdigest(),force_baseline_n=1000.,amplitude=result.amplitude,actual_tip_force_n=force,equilibrium=result.free_equilibrium_ratio,gap=result.constraint_max,pools=threadpool_info(),test_sha256=hashlib.sha256((repo/'tests/test_stiffened_shell_native_generalized_q4_j2_history.py').read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256((repo/'tests/data/native_generalized_q4_j2_history/unloaded-v1.bin').read_bytes()).hexdigest())
    (root/'result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('artifacts','sources','pools')}),flush=True)
finally:owner.close();oracle.close()
