from pathlib import Path
from hashlib import sha256
import os,sys
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_fine_lifecycle import _check_lifecycle
from test_general_contact_native_curved_s3_static import _analysis


def owner():
    return _analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=8e7,
        integration_budget_policy='certified_active',root_tangent_enclosure_policy='anchored')


def test_anchored_opening():
    raw=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate12/installed_anchored_first_target/actual_result.json-anchored-first-target.json.checkpoint').read_bytes()
    assert sha256(raw).hexdigest()=='98d22bd2aff840df5d7b1034298891b179ed438ec9246a9f76b89445a7a15347'
    _check_lifecycle(2,raw,owner)


def test_anchored_recontact():
    raw=Path(os.environ['CONTACT_FINE_OPEN_CHECKPOINT']).read_bytes()
    assert sha256(raw).hexdigest()==os.environ['CONTACT_FINE_OPEN_SHA256']
    _check_lifecycle(3,raw,owner)
