from pathlib import Path
from hashlib import sha256
import sys,os,json,time,runpy
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001');sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_fine_lifecycle import _owner
from test_general_contact_native_curved_s3_work import _moved
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work
BASE=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005')

def test_saved_full_opening_trial_anchored_enclosure():
    raw=(ROOT/'tests/data/general_contact_native_fibre_s3_plastic_k8e7_component_v1.checkpoint').read_bytes()
    trace=json.loads((BASE/'candidate11/installed_opening_actual_first_step_observation/actual_result.json-opening-first-step.json').read_text())
    owner=_owner();state,_=owner._restore(raw,sha256(raw).hexdigest())
    step=np.array(trace['step']);assert next(e['fraction'] for e in trace['events'] if e['phase']=='activation_fraction')==1.
    m=owner.context.advance(state.mechanical,step[:owner.context.count]);u=state.shell_displacement+step[owner.context.count:]
    nodes=owner.context.nodes[0];args=(m.positions[nodes],m.position_low[nodes],m.cell_rotations[0],u)
    original=owner.pairs[0].work
    record=dict(scope='saved actual full opening Newton trial; no coupled solve/commit',policies={},
        positions=args[0].tolist(),position_low=args[1].tolist(),cell_rotations=args[2].tolist(),shell_displacement=u.tolist())
    dest=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-anchored-opening-pose.json')
    for policy in ('componentwise','anchored'):
        work=NativeCurvedMaterialS3Work(original.contact,original.shell,integration_budget_policy='certified_active',root_tangent_enclosure_policy=policy)
        t=time.monotonic()
        try:
            value=work.evaluate(*args);c=value.contact
            record['policies'][policy]=dict(status='completed',elapsed_s=time.monotonic()-t,
                intervals=c.integration_intervals,evaluations=c.integration_evaluations,
                errors=[c.energy_error_j,c.force_error_n,c.tangent_error_n_per_m])
        except (ValueError,MemoryError) as exc:
            record['policies'][policy]=dict(status='rejected',elapsed_s=time.monotonic()-t,failure=str(exc),diagnostics=getattr(exc,'integration_diagnostics',None))
        dest.write_text(json.dumps(record,indent=2))
    assert record['policies']['componentwise']['status']=='rejected'
    assert record['policies']['anchored']['status']=='completed',record
    oracle=runpy.run_path(str(BASE/'candidate08/test_fine_pose_independent_residual.py'))['oracle']
    independent,control=oracle(work,*args,24,1e-12)
    record['independent_control']=control
    record['relative_residual_error']=float(np.linalg.norm(value.residual-independent)/np.linalg.norm(independent))
    dest.write_text(json.dumps(record,indent=2))
    assert record['relative_residual_error']<=1e-5,record
    d=np.random.default_rng(419).normal(size=len(value.residual))*.001;d[24:42]=0.
    record['tangent_errors']=[];record['virtual_work_errors']=[]
    def moved(h):
        p,low,U,u=_moved(*args,d,h);low=low.copy()
        for node in range(3):
            for axis in range(3):
                p[node,axis],low[node,axis]=split_sum((float(args[0][node,axis]),float(args[1][node,axis]),float(h*d[6*node+axis])))
        return p,low,U,u
    for h in (2e-6,1e-6):
        plus=work.evaluate(*moved(h));minus=work.evaluate(*moved(-h))
        derivative=(plus.residual-minus.residual)/(2*h)
        error=float(np.linalg.norm(value.tangent@d-derivative)/np.linalg.norm(derivative))
        energy=(plus.contact.potential_j-minus.contact.potential_j)/(2*h)
        ve=float(abs(energy-value.residual@d)/max(abs(value.residual@d),1e-15))
        record['tangent_errors'].append(error);record['virtual_work_errors'].append(ve)
        dest.write_text(json.dumps(record,indent=2))
        assert error<=1e-5 and ve<=1e-5,record
