from pathlib import Path
import os,json,sys,runpy
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
from test_general_contact_native_curved_s3_work import _moved
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work
BASE=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005')

def test_saved_rejected_pose_independent_work_and_tangent():
    pose=json.loads((BASE/'candidate09/saved_rejected_pose_capture/actual_result.json-rejected-pose.json').read_text())
    comparison=json.loads((BASE/'candidate09/rejected_pose_budget_comparison/actual_result.json-allocation-comparison.json').read_text())
    assert comparison['full_reference']['diagnostics']==pose['diagnostics']
    assert comparison['certified_active']['status']=='completed'
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=4e7)
    original=owner.pairs[0].work;assert original.identity==pose['work_identity']
    work=NativeCurvedMaterialS3Work(original.contact,original.shell,integration_budget_policy='certified_active')
    args=[np.array(pose[k]) for k in ('positions','position_low','cell_rotations','shell_displacement')]
    value=work.evaluate(*args)
    oracle=runpy.run_path(str(BASE/'candidate08/test_fine_pose_independent_residual.py'))['oracle']
    independent,control=oracle(work,*args,24,1e-12)
    record=dict(scope='saved rejected pose local work and tangent; no coupled convergence',
        independent_control=control,residual_relative_error=float(np.linalg.norm(value.residual-independent)/np.linalg.norm(independent)),
        tangent_errors=[],virtual_work_errors=[])
    dest=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-independent-checks.json')
    dest.write_text(json.dumps(record,indent=2))
    assert record['residual_relative_error']<=1e-5,record
    d=np.random.default_rng(813).normal(size=len(value.residual))*.001;d[24:42]=0.
    def moved(h):
        p,low,U,u=_moved(*args,d,h)
        low=low.copy()
        for node in range(3):
            for axis in range(3):
                p[node,axis],low[node,axis]=split_sum((float(args[0][node,axis]),float(args[1][node,axis]),float(h*d[6*node+axis])))
        return p,low,U,u
    for h in (1e-5,2e-6):
        plus=work.evaluate(*moved(h));minus=work.evaluate(*moved(-h))
        derivative=(plus.residual-minus.residual)/(2*h)
        error=float(np.linalg.norm(value.tangent@d-derivative)/np.linalg.norm(derivative))
        energy_derivative=(plus.contact.potential_j-minus.contact.potential_j)/(2*h)
        ve=float(abs(energy_derivative-value.residual@d)/max(abs(value.residual@d),1e-15))
        record['tangent_errors'].append(error);record['virtual_work_errors'].append(ve)
        dest.write_text(json.dumps(record,indent=2))
        assert error<=1e-5 and ve<=1e-5,record