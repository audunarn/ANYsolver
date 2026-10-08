from pathlib import Path
import hashlib,json,os,sys
import numpy as np
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer
root=Path(__file__).resolve().parent;repo=root.parents[2];site=root/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site) and Path(consumer.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
artifacts=json.loads((root/'artifact-v1.json').read_text())['artifacts']
old=json.loads((root.parent/'r8-native-displacement-adaptive-dev-20261005-v1/installed-result-v1.json').read_text())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
sources={}
for name in old['sources']:
    checkout=repo if name.startswith('anysolver/') else fem
    digest=hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()
    assert hashlib.sha256((site/name).read_bytes()).hexdigest()==digest,name
    sources[name]=digest
for item in artifacts.values():assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest()==item['sha256']
targets=['test_stiffened_shell_native_displacement_chart.py','test_stiffened_shell_native_point_displacement.py','test_stiffened_shell_native_displacement_adaptive.py','test_stiffened_shell_native_plastic_s3_displacement.py','test_stiffened_shell_native_fibre_s3_displacement_identity.py','test_stiffened_shell_native_generalized_adaptive_history.py','test_stiffened_shell_native_generalized_q4_j2_history.py','test_stiffened_shell_displacement_rebase.py','test_stiffened_shell_curved_material_displacement.py']
record=dict(status='IN_PROGRESS',artifacts=artifacts,sources=sources,targets=targets,pools=threadpool_info())
def write(): (root/'installed-result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
write()
status=pytest.main(['-q',*[str(repo/'tests'/name) for name in targets],'--junitxml='+str(root/'installed-junit-v1.xml')])
record['pytest_exit']=status;write()
if status:raise SystemExit(status)
from anyfem.io.project_file import save_project,load_project
from anyfem.model.project import Project
from anyfem.model.records import AnalysisDefinition
from anyfem.solve.stiffened_shell_project import point_panel_from_analysis
from anysolver._stiffened_shell_displacement_adaptive import decode
from test_stiffened_shell_native_generalized_adaptive_history import exact
from test_stiffened_shell_q4_pullback_owner import _definition
from examples.stiffened_shell_coupled_s3_adaptive_history import definition as s3_definition
cases=[('q4-generalized-j2',_definition(plastic=True,mixed=False),'native_generalized_q4_j2_history/unloaded-v1.bin'),('s3-fibre-j2',s3_definition(),'native_s3_fibre_history/unloaded-v1.bin')]
record['consumer']=[]
for name,model,fixture in cases:
    directory=root/('consumer-'+name+'-v1');directory.mkdir()
    panel=consumer.ExperimentalGEPointPanel(model.shell,model.beams,model.points,model.fixed,q4_pullback_policy=model.q4_pullback_policy)
    consumer.save_case(panel,directory/'case.anyfem-ge.json');assert consumer.load_case(directory/'case.anyfem-ge.json').to_dict()==panel.to_dict()
    project=Project(name,mesh_only=True);analysis=AnalysisDefinition.experimental_point_panel('native chart',panel);project.add_analysis(analysis)
    saved=save_project(project,directory/'panel.anyfem');reopened=point_panel_from_analysis(load_project(saved).analyses[analysis.id]);assert reopened.to_dict()==panel.to_dict()
    owner=reopened.create_analysis();resumed=reopened.create_analysis()
    try:
        prefix=(repo/'tests/data'/fixture).read_bytes();before=owner.restore(prefix)
        changed=owner.rebase_rotations(before.generation);checkpoint=owner.checkpoint()
        (directory/'chart-prefix-v1.checkpoint').write_bytes(checkpoint)
        restored=resumed.restore(checkpoint);assert resumed.checkpoint()==checkpoint;exact(restored,changed)
        context,_=decode(owner,checkpoint)
        actions=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),) if name.startswith('q4') else tuple(ss.NodalAction('beam',node,(0.,0.,150.,0.,0.,0.)) for node in (105,205))
        kw=dict(displacement_control=ss.DisplacementControl('beam',105,2),increment_control=ss.AdaptiveIncrementControl(6,24),max_iterations=20,max_backtracks=12)
        final=owner.solve(actions,context.state.targets,**kw);again=resumed.solve(actions,context.state.targets,**kw)
        exact(final,again);assert owner.checkpoint()==resumed.checkpoint()
        for a,b in zip(final.shell_q4_material+final.shell_s3_material,again.shell_q4_material+again.shell_s3_material,strict=True):
            for key in ('layer_strain','layer_stress','plastic_strain','alpha'):np.testing.assert_array_equal(getattr(a,key),getattr(b,key))
        endpoint=owner.checkpoint();(directory/'final-v1.checkpoint').write_bytes(endpoint)
        record['consumer'].append(dict(name=name,case_project_roundtrip=True,exact_chart_restart=True,endpoint_sha256=hashlib.sha256(endpoint).hexdigest(),equilibrium=final.free_equilibrium_ratio,gap=final.constraint_max,chart_generation=changed.generation))
        write()
    finally:owner.close();resumed.close()
for name,module in tuple(sys.modules.items()):
    if name.startswith(('anysolver','anyfem')) and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(site),name
record['status']='PASSED_NATIVE_CHART_INSTALLED_NOT_QUALIFIED';write();print(json.dumps(dict(status=record['status'],cases=record['consumer'],sources=len(sources))),flush=True)
