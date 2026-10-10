"""v8 physical half/prefix proof for the joint overlap certificate.

The v8 effective-settings repair: the small-patch driver fixture's
``_enabled`` selector previously left ``q4_source_overlap_dual_dev`` at
its False core default, so every expensive driver attempt exercised the
old overlap-local certificate instead of the already selected
joint-certificate candidate. ``_enabled`` now enables the joint dual and
explicitly asserts the returned effective flag plus the unchanged
intended D1/Jet2/fine-Q1/monolithic/primal-mortar route.

This module is the single guarded prefix proof required before any
reference-full or all-six driver work: it runs ONLY the existing
small-patch fixture's physical HALF check (one macro,
max_load_factor=0.5) with the explicit effective-settings assertion.
No fixture tuning: material, load, gap, tolerances and program are the
existing fixture's own. Only after the complete public
result/report/physics gates pass does it export the actual restart
checkpoint JSON and source/program/settings identifiers under the
attempt TEMP directory, enabling later connected
chronology/rollback/restart checks to reuse a genuinely accepted bound
checkpoint instead of repeatedly solving the first activation. An
internal Newton or partial-substep state is never exported.
"""
import json
import os
from dataclasses import asdict

from test_general_contact_admission_globalization_driver_small_patch import (
    _CHECKPOINT_HASH_KEY,
    _SOURCE_COLUMNS,
    _assert_active_contact,
    _case,
    _enabled,
    _solve,
)


def _source_manifest():
    """Bind the guard's immutable source snapshot identifiers when present."""
    runtime = os.environ.get("AUTOMATIC_RUNTIME_RESULT")
    if not runtime:
        return None
    install = os.path.join(os.path.dirname(runtime), "install.json")
    if not os.path.isfile(install):
        return None
    with open(install, encoding="utf-8") as handle:
        record = json.load(handle)
    return {"payload_sha256": record.get("payload_sha256"),
            "mode": record.get("mode")}


def test_prefix_half_joint_overlap_certificate_physical_gates():
    model, definition, settings, program = _case()
    enabled = _enabled(settings)
    # Explicit effective-settings contract (also asserted inside _enabled):
    # the joint overlap dual is the returned effective certificate flag
    # and the enable changes no intended route setting.
    assert enabled.q4_source_overlap_dual_dev is True
    assert enabled.q4_source_gap_certificate == "overlap_local_dev"
    assert enabled.path_continuation_maximum_halvings == 6
    # The single physical HALF/PREFIX macro of the existing fixture.
    result = _solve(model, definition, enabled, program,
                    max_load_factor=0.5, emit_restart_checkpoint=True)
    # Complete public result gate.
    assert result.status == "completed" and len(result.steps) == 1
    checkpoint = result.to_restart_checkpoint()
    history = checkpoint["path_state"]["history"]
    assert len(history) == 1
    record = history[0]
    # Physics gates: real active contact inside the family gap tolerance.
    _assert_active_contact(record)
    interior_load_node = 1 + (_SOURCE_COLUMNS + 1) + 1
    assert program.nodal_forces[0].node_id == interior_load_node
    center_uz = model.mesh.dof_manager.get_node_dofs(interior_load_node)[2]
    assert result.displacements[center_uz] < 0.0
    # Report gate: the committed record carries the program's own
    # half-load ramp endpoint and target.
    assert record["nodal_forces_n"] == program.force_values_at(1).tolist()
    # Every public result/report/physics gate passed: export the actual
    # complete restart checkpoint and the source/program/settings
    # identifiers under the attempt TEMP for later connected checks.
    temp = os.environ["TEMP"]
    with open(os.path.join(temp, "prefix-half-restart-checkpoint-v1.json"),
              "wb") as handle:
        handle.write(result.restart_checkpoint_bytes())
    identifiers = {
        "schema": "PREFIX_HALF_ACCEPTED_IDENTIFIERS_V1",
        "fixture_module":
            "test_general_contact_admission_globalization_driver_small_patch",
        "prefix_module":
            "test_general_contact_admission_globalization_prefix_half_v8",
        "checkpoint_sha256": checkpoint[_CHECKPOINT_HASH_KEY],
        "model_fingerprint": checkpoint["model_fingerprint"],
        "analysis_fingerprint": checkpoint["analysis_fingerprint"],
        "program": program.contract(),
        "settings": asdict(enabled),
        "continuation_block_present": "continuation" in record,
        "source_manifest": _source_manifest(),
    }
    with open(os.path.join(temp, "prefix-half-identifiers-v1.json"), "w",
              encoding="utf-8") as handle:
        json.dump(identifiers, handle, indent=2, sort_keys=True)
        handle.write("\n")
