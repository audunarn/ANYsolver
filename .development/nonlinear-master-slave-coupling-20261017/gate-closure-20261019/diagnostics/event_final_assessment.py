"""Reconcile final event candidate evidence; never invokes the solver."""
import hashlib
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path

PHASE = Path(__file__).resolve().parents[1]
TASK = PHASE.parent
REPO = TASK.parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


candidate = read(PHASE / "candidate-identities/event-final-frozen-candidate/candidate.json")
regression = read(PHASE / "event-final-regression-summary.json")
prior = read(PHASE / "final-preservation-v2.json")
parent = read(PHASE / "candidate-identities/final-frozen-candidate/candidate.json")
budget = read(TASK / "budget.json")
hashes = candidate["working_source_and_selected_inputs_sha256"]
current_mismatches = [p for p, h in hashes.items()
                      if not (REPO / p).is_file() or sha(REPO / p) != h]
protected = []
for row in prior["protected_backups"] + prior["unrelated_tracked_dirty_except_readme"]:
    protected.append(dict(path=row["path"], expected=row["actual"],
                          actual=sha(REPO / row["path"])))
product_delta = []
for p, h in candidate["owned_snapshot_sha256"].items():
    old = parent["owned_snapshot_sha256"].get(p)
    if h != old:
        product_delta.append(dict(path=p, before=old, after=h))
ids = list(regression["id_to_invocation"])
selection = read(PHASE / "event-final-all-collection-selection.json")
historical_modules = selection["all_required_targets"][:25]
historical_ids = [n for n in ids if any(n.startswith(p + "::") for p in historical_modules)]
continuation_rows = [r for r in regression["rows"] if "continuation" in r["name"]]
continuation_passed = bool(continuation_rows and all(
    r["status"] == "EXIT" and r["collected_count_matches"]
    and not any(r["actual_outcomes"].get(k, 0) for k in ("failed", "error", "skipped", "xfailed", "xpassed"))
    for r in continuation_rows))
failures = []
failure_assertions = []
for row in regression["rows"]:
    for line in (PHASE / "evidence" / row["name"] / "stdout.txt").read_text().splitlines():
        if line.startswith("FAILED tests/"):
            failures.append(line)
        if line.startswith("E ") and "AssertionError:" in line:
            failure_assertions.append(dict(invocation=row["name"], assertion=line.strip()))
full_rows = []
raw_folder = PHASE / "evidence/event-final-continuation-smoke-full/raw-artifacts"
for folder in sorted(raw_folder.iterdir()):
    if not folder.is_dir():
        continue
    terminal = pickle.loads((folder / "terminal.pkl").read_bytes())
    accepted_paths = sorted(folder.glob("accepted-*.pkl"))
    last = pickle.loads(accepted_paths[-1].read_bytes())
    full_rows.append(dict(case=folder.name, status=terminal["status"],
                          stop_reason=terminal["stop_reason"],
                          load_factor=terminal["load_factor"],
                          achieved_control=last["control"],
                          accepted_snapshot_count=len(accepted_paths),
                          adaptation=terminal["info"].get("displacement_control_adaptation"),
                          terminal_sha256=sha(folder / "terminal.pkl")))
record = dict(
    checked_utc=datetime.now(timezone.utc).isoformat(),
    state="verified partial implementation; scientific gates remain open",
    slice3_development_acceptance=False,
    candidate_identity=candidate["candidate_identity_sha256"],
    candidate_manifest="candidate-identities/event-final-frozen-candidate/candidate.json",
    head=candidate["head"], branch=candidate["branch"],
    source_input_count=len(hashes), source_mismatches=current_mismatches,
    protected_inputs=protected,
    preserved_protected_inputs=all(r["expected"] == r["actual"] for r in protected),
    delta_from_previous_verified_candidate=product_delta,
    regression=dict(summary="event-final-regression-summary.json",
                    required_modules=len(selection["all_required_targets"]),
                    actual_counts=regression["actual_terminal_counts"],
                    checks=regression["checks"], failed_test_lines=failures,
                    failure_assertions=failure_assertions,
                    historical_module_count=len(historical_modules),
                    historical_collected_ids=len(historical_ids),
                    historical_invocations=sorted(set(regression["id_to_invocation"][n]
                                                       for n in historical_ids))),
    continuation=dict(gate_passed=continuation_passed, target=-0.2,
                      original_controls_and_tolerances_preserved=True,
                      final_full_target_outcomes=full_rows,
                      accepted_state_byte_identity="event-final-accepted-state-identity.json",
                      accepted_snapshots_checked_before_completion_assertions=sum(
                          row["accepted_snapshot_count"] for row in full_rows),
                      raw_artifact_inventory="evidence/event-final-continuation-smoke-full/raw-artifacts-copy.json",
                      owner_handoff="continuation-repair-owner-handoff.json",
                      corrected_secant_diagnostic="continuation-accepted-secant-basin-guarded/result.json",
                      accepted_regularity_handoff="continuation-accepted-regularity/handoff.json",
                      accepted_regularity_conclusion="Loading direction changes material branch; inconclusive, stop. Literal committed tangent regularity is not loading-path proof.",
                      physical_collapse_or_root_nonexistence_established=False),
    mesh=dict(prior_source_bound_gate_passed=True,
              summary="../integrated-final-mesh-summary.json",
              rerun_on_event_candidate=False),
    analytical=dict(gate_passed=False,
                    original_summary="../integrated-final-arc-summary.json",
                    experimental_trace_completed_but_accuracy_failed="director-displacement-observed-n16"),
    review=dict(record="../supervisor_continuation2_delta_review.md",
                requested_Astra_high_full_progress_review_count=1,
                event_arithmetic_reconciliation="root-event-arithmetic-reconciliation-v3.json"),
    ledger=dict(path="../budget.json", allowance_seconds=budget["allowance_seconds"],
                used_before_this_metadata_invocation_seconds=budget["used_seconds"],
                remaining_before_this_metadata_invocation_seconds=budget["allowance_seconds"]-budget["used_seconds"],
                reserve_seconds=budget["final_verification_reserve_seconds"],
                attempt_count_before_this_metadata_invocation=len(budget["attempts"]),
                final_accounting="This invocation is charged by its receipt after this record is written."),
    scientific_tolerances_unchanged=True, public_converged_semantics_preserved=True,
    release_retired_programme_status_unchanged=True,
    commit_push_release_external_qualification_performed=False)
out = PHASE / "event-final-acceptance-record.json"
with out.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
print(json.dumps(dict(candidate=record["candidate_identity"],
                      counts=record["regression"]["actual_counts"],
                      source_mismatches=current_mismatches,
                      protected_inputs_preserved=record["preserved_protected_inputs"],
                      scientific_acceptance=False)))
