from pathlib import Path
from hashlib import sha256
import os,json,sys,time,runpy
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work
BASE=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005')

def test_mapped_k8e7_root_enclosure_and_independent_residual():
    raw=(BASE/'candidate10/installed_seeded_k4e7_certified_active/actual_result.json-enforcement.checkpoint').read_bytes()
    digest=sha256(raw).hexdigest();assert digest=='a88d56a9ec6b1347794ff08a50fa72793865d1f28c9ff189249aa4f8719c0c83'
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=8e7,integration_budget_policy='certified_active')
    source=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=4e7,integration_budget_policy='certified_active')
    guess=owner.make_initial_guess(source,raw,digest)
    m=owner.context.advance(owner.initial.mechanical,guess.increment[:owner.context.count])
    u=owner.initial.shell_displacement+guess.increment[owner.context.count:]
    nodes=owner.context.nodes[0];args=(m.positions[nodes],m.position_low[nodes],m.cell_rotations[0],u)
    original=owner.pairs[0].work
    report=dict(scope='mapped initial guess local enclosure discriminator; no solve/commit',source_checkpoint_sha256=digest,
        positions=args[0].tolist(),position_low=args[1].tolist(),cell_rotations=args[2].tolist(),shell_displacement=u.tolist(),policies={})
    dest=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-root-comparison.json')
    for policy in ('spectral','componentwise'):
        work=NativeCurvedMaterialS3Work(original.contact,original.shell,integration_budget_policy='certified_active',root_tangent_enclosure_policy=policy)
        t=time.monotonic()
        try:
            value=work.evaluate(*args);c=value.contact
            report['policies'][policy]=dict(status='completed',elapsed_s=time.monotonic()-t,
                estimated_errors=[c.energy_error_j,c.force_error_n,c.tangent_error_n_per_m],intervals=c.integration_intervals,evaluations=c.integration_evaluations)
        except ValueError as exc:
            report['policies'][policy]=dict(status='rejected',elapsed_s=time.monotonic()-t,failure=str(exc),diagnostics=getattr(exc,'integration_diagnostics',None))
        dest.write_text(json.dumps(report,indent=2))
    assert report['policies']['spectral']['status']=='rejected'
    assert report['policies']['componentwise']['status']=='completed',report
    oracle=runpy.run_path(str(BASE/'candidate08/test_fine_pose_independent_residual.py'))['oracle']
    independent,control=oracle(work,*args,24,1e-12)
    report['independent_control']=control
    report['relative_residual_error']=float(np.linalg.norm(value.residual-independent)/np.linalg.norm(independent))
    dest.write_text(json.dumps(report,indent=2))
    assert report['relative_residual_error']<=1e-5,report