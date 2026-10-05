from pathlib import Path
from dataclasses import replace,asdict
import json,hashlib,math,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss,b3_ge
from test_stiffened_shell_native_point_displacement import native_state
from test_stiffened_shell_q4_pullback_owner import _definition
raw=Path(__file__).resolve().parent;repo=raw.parents[2];root=raw/'probe-outputs-v2';root.mkdir(exist_ok=False)
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
from dataclasses import replace
from anysolver._stiffened_shell_rotation_charts import physical_frames
from anysolver._stiffened_shell_ge_finite_experimental import _shell_material_arrays,_accepted_shell_material_origins,_require_native_s3_replay
from anysolver._stiffened_shell_beam_history import arrays
from anysolver._ge_beam3_pose_joint import _exp_terms
from test_stiffened_shell_native_s3_fibre_reversal import definition as s3_definition
cases=[('q4-generalized-j2',_definition(plastic=True,mixed=False),'native_generalized_q4_j2_history/unloaded-v1.bin'),('s3-fibre-j2',s3_definition(),'native_s3_fibre_history/unloaded-v1.bin')]
record=dict(scope='Scratch same-predecessor coordinate-rebase derivation; no public admission change',cases=[],artifacts=identities['artifacts'])
for name,definition,fixture in cases:
    owner=ss.create_analysis(definition=definition)
    try:
        rawcheckpoint=(repo/'tests/data'/fixture).read_bytes();accepted=owner.restore(rawcheckpoint)
        driver=owner._finite_driver;state=driver._state
        q=state.q.copy();q[:owner._shell_count].reshape(-1,6)[:,3:]=0.
        frames=physical_frames(state.q[:owner._shell_count],state.shell_anchors)
        candidate=replace(state,q=q,shell_anchors=frames)
        parents=(driver._shell_predecessors,driver._beam_predecessors)
        old=driver._assemble(state,0.,*parents,applied_load=accepted.applied_dead_load)
        new=driver._assemble(candidate,0.,*parents,applied_load=accepted.applied_dead_load)
        material_exact=True
        for (key,a),(other,b) in zip(arrays(owner._beam_parts,old[5],'beam'),arrays(owner._beam_parts,new[5],'beam'),strict=True):
            assert key==other;material_exact=material_exact and np.array_equal(a,b)
        q4_count=len(definition.shell.q4_elements)
        shell_relative=[]
        for a,b in zip(old[4][:q4_count],new[4][:q4_count],strict=True):
            for key in ('plastic_strain','alpha','layer_strain','layer_stress'):
                if key in a:
                    av,bv=np.asarray(a[key]),np.asarray(b[key]);shell_relative.append(float(np.max(abs(av-bv),initial=0.))/max(float(np.max(abs(av),initial=0.)),np.finfo(float).tiny))
        s3_exact=None
        if definition.shell.s3_elements:
            sealed=_accepted_shell_material_origins(owner,candidate,new[4])
            material=owner._shell_model.get_material('shell');s3_exact=True
            for (_,element,_,_),a,b in zip(owner._shell_parts[q4_count:],driver._shell_origins[q4_count:],sealed[q4_count:]):
                s3_exact=s3_exact and element.serialize_nonlinear_state(owner._shell_model.mesh,material,a,3)==element.serialize_nonlinear_state(owner._shell_model.mesh,material,b,3)
        mapped=old[0].copy()
        for i,row in enumerate(state.q[:owner._shell_count].reshape(-1,6)):
            # Assembled residual rows are SPATIAL wrenches; only increment columns use J.
            mapped[6*i+3:6*i+6]=old[0][6*i+3:6*i+6]
        error=float(np.linalg.norm(new[0]-mapped))/max(float(np.linalg.norm(old[0])),np.finfo(float).tiny)
        row=dict(name=name,physical_frames_exact=np.array_equal(physical_frames(candidate.q[:owner._shell_count],candidate.shell_anchors),frames),native_material_exact=material_exact,q4_material_max_relative=max(shell_relative,default=0.),s3_serialized_exact=s3_exact,spatial_row_invariance_relative=error,old_equilibrium=old[2],new_equilibrium=new[2],old_gap=old[3],new_gap=new[3],owner_checkpoint_unchanged=owner.checkpoint()==rawcheckpoint)
        record['cases'].append(row)
    finally:owner.close()
(root/'result-v1.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record['cases']),flush=True)
