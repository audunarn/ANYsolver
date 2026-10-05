from pathlib import Path
import os,json,time,sys
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work
POSE=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate09/saved_rejected_pose_capture/actual_result.json-rejected-pose.json')

def test_saved_rejected_pose_allocation_comparison():
    pose=json.loads(POSE.read_text())
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=4e7)
    work=owner.pairs[0].work
    assert owner.identity==pose['owner_identity'] and work.identity==pose['work_identity']
    args=[np.array(pose[k]) for k in ('positions','position_low','cell_rotations','shell_displacement')]
    records={}
    for policy in ('full_reference','certified_active'):
        candidate=NativeCurvedMaterialS3Work(work.contact,work.shell,integration_budget_policy=policy)
        t=time.monotonic()
        try:
            value=candidate.evaluate(*args);c=value.contact
            records[policy]=dict(status='completed',elapsed_s=time.monotonic()-t,
                intervals=c.integration_intervals,evaluations=c.integration_evaluations,
                errors=[c.energy_error_j,c.force_error_n,c.tangent_error_n_per_m],
                energy=c.potential_j,residual=value.residual.tolist(),tangent=value.tangent.toarray().tolist())
        except (MemoryError,ValueError) as exc:
            records[policy]=dict(status='rejected',elapsed_s=time.monotonic()-t,
                failure=str(exc),diagnostics=getattr(exc,'integration_diagnostics',None))
        Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-allocation-comparison.json').write_text(json.dumps(records,indent=2))
    assert records['full_reference']['status']=='rejected'
    assert json.loads(json.dumps(records['full_reference']['diagnostics']))==pose['diagnostics']
    assert records['certified_active']['status']=='completed',records['certified_active']