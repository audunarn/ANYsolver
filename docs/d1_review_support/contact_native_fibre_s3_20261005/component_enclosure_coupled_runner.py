from pathlib import Path
from hashlib import sha256
import sys
sys.path.insert(0,'C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001/tests')
from test_general_contact_native_fibre_enforcement import _enforcement_case

def test_saved_k4e7_to_component_enclosure_k8e7():
    raw=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate10/installed_seeded_k4e7_certified_active/actual_result.json-enforcement.checkpoint').read_bytes()
    assert sha256(raw).hexdigest()=='a88d56a9ec6b1347794ff08a50fa72793865d1f28c9ff189249aa4f8719c0c83'
    _enforcement_case(8e7,seeded=True,source_checkpoint=raw,integration_budget_policy='certified_active',
        source_integration_budget_policy='certified_active',root_tangent_enclosure_policy='componentwise')