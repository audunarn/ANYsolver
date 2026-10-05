from pathlib import Path
from hashlib import sha256
import sys,json,os
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_fine_lifecycle import _owner
from test_general_contact_native_curved_s3_static import _analysis
from test_general_contact_native_fibre_enforcement import _quantities,_response_errors,_gap
from test_general_contact_native_fibre_s3 import _independent_material_history
from anysolver._ge_beam3_p5_seeded.core import canonical


def test_new_anchored_first_target_from_coordinates_only():
    raw=(ROOT/'tests/data/general_contact_native_fibre_s3_plastic_k8e7_component_v1.checkpoint').read_bytes()
    digest=sha256(raw).hexdigest()
    assert digest=='5c72a14e4288010a7f9407ada3cd1c5334e37ae071a7baf2281de75615a7d50a'
    source=_owner()
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=8e7,
        integration_budget_policy='certified_active',root_tangent_enclosure_policy='anchored')
    origin=owner.initial.native_histories
    assert all(not np.any(station.rows) for cell in origin for station in cell.stations)
    before=canonical(origin)
    guess=owner.make_initial_guess(source,raw,digest)
    assert guess.source_owner_identity==source.identity and guess.owner_identity==owner.identity
    output=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-anchored-first-target.json')
    record=dict(scope='fresh anchored first target; coordinates-only seed, virgin histories',
        source_sha256=digest,source_identity=source.identity,owner_identity=owner.identity,
        guess_fingerprint=guess.fingerprint)
    output.write_text(json.dumps(record,indent=2))
    run=owner.solve(stop_after=1,initial_guess=guess)
    Path(str(output)+'.checkpoint').write_bytes(run.checkpoint)
    record.update(status=run.status,failure=run.failure,completed=run.accepted.completed_targets,
        checkpoint_sha256=run.checkpoint_sha256,candidates=owner.candidate_evaluations,
        pair_evaluations=owner.pair_evaluations,reuse_hits=owner.contact_reuse_hits,
        trial_failures=owner.curved_trial_failures)
    output.write_text(json.dumps(record,indent=2))
    assert run.status=='paused' and run.accepted.completed_targets==1,run.failure
    previous,_=source._restore(raw,digest)
    errors=_response_errors(_quantities(source,previous),_quantities(owner,run.accepted))
    gap=_gap(owner,run.accepted,129);contact=run.accepted.contact.contact
    report,proposed=_independent_material_history(owner,run.accepted.mechanical,origin)
    record.update(response_relative_errors=errors,independent_gap_m=gap,
        gap_lower_m=contact.minimum_gap_m,material=report)
    output.write_text(json.dumps(record,indent=2))
    # Same-mechanics policy comparison; the previously registered 2% response
    # target is retained, not a new convergence or native acceptance claim.
    assert max(errors.values())<=.02
    assert contact.minimum_gap_m>=-3e-5 and gap>=-3e-5
    assert contact.minimum_gap_m<=gap+1e-10
    assert np.linalg.norm(contact.beam_force_n+contact.shell_force_n)/.005<=1e-6
    assert np.linalg.norm(contact.beam_moment_nm+contact.shell_moment_nm)/.010<=1e-6
    assert tuple(proposed)==run.accepted.native_histories[0].stations
    assert canonical(origin)==before and owner.context._token is None
    assert not owner.context._lock.locked() and owner._contact_reuse_entry is None
    assert not owner._contact_reuse_enabled
