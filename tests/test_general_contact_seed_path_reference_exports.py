"""Focused impact checks for the changed seed-gap reference exports.

Scope: D1_SEED_PATH_ADMISSION_DELIVERY_DEV600_V1 (DELTA_V2 continuation).

The changed reference (scripts/general_contact_seed_gap_reference.py)
gained the ten-record literal capture loader, the per-record runner, exact
rational string exports, the end-pose gap-definition distinction and the
chart/budget inconclusive refusal classification. These checks reuse the
original six reference obligations by direct import of the unmodified
original reference test module (compatibility of the changed exports with
the obligations that predate the change), then exercise the new exports
with focused checks only:

- capture loader binding: ten records, kinds, sha256, tolerance, explicit
  zero endpoint error boxes (never null), degenerate endpoint poses;
- the empty-domain record (path 6): the projected foot is provably outside
  the target triangle over the whole domain, so the foot-inside domain is
  empty, the record is vacuously safe and no finite gap interval exists
  or is required (lower and upper both None);
- a synthetic deep violation: physical_violation_proven classification
  with exact rational strings retained for every reported bound;
- a forced chart/budget exhaustion: chart_or_budget_inconclusive_refusal
  classification (inconclusive: neither safe nor violation proven).

Per-record production-stage results in this slice are diagnostics of the
literal captured arrays only; nothing here is an accepted nonlinear solve.
The contract gap, target-plane height and local-normal gap are reported
as three distinct quantities; no warped-gap/local-normal equivalence is
asserted anywhere. Nearest-rounded floats are descriptive only; the exact
rational strings are the retained bounds.
"""
import importlib.util
from fractions import Fraction
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "scripts" / "general_contact_seed_gap_reference.py"
ORIGINAL_TEST_PATH = (REPO_ROOT / "tests" /
                      "test_general_contact_seed_gap_reference.py")
CAPTURE_SHA256 = (
    "f8e7dee46a3135c621492364f5f727d0eb34d57873afeb7146606c4bda31a114"
)
GAP_TOLERANCE = 5e-5


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ref = _load_module("general_contact_seed_gap_reference", REFERENCE_PATH)
original = _load_module(
    "general_contact_seed_gap_reference_original_tests", ORIGINAL_TEST_PATH)

ORIGINAL_SIX = (
    "test_artifact_binding_and_embedded_literal",
    "test_exact_start_corner_gap_positive_foot_inside",
    "test_directed_float_box_contains_exact_point_values",
    "test_literal_path_zero_discriminator_certificate",
    "test_reference_detects_synthetic_deep_violation",
    "test_reference_certifies_synthetic_separation",
)


def test_original_six_reference_obligations_still_hold():
    for name in ORIGINAL_SIX:
        getattr(original, name)()


def test_capture_loader_exports():
    records = ref.load_capture_records()
    assert len(records) == 10
    assert [record["kind"] for record in records] == (
        ["endpoint"] * 2 + ["path"] * 8)
    assert [record["record_index"] for record in records] == (
        list(range(2)) + list(range(8)))
    for record in records:
        assert record["input_sha256"] == CAPTURE_SHA256
        assert float(record["path"]["gap_tolerance_m"]) == GAP_TOLERANCE
        errors = record["path"]["endpoint_errors"]
        assert len(errors) == 4
        if record["kind"] == "endpoint":
            # degenerate poses carry explicit zero boxes, never null
            assert all(float(value) == 0.0
                       for box in errors for row in box for value in row)
            assert (record["path"]["source_start_m"]
                    == record["path"]["source_end_m"])
            assert (record["path"]["target_start_m"]
                    == record["path"]["target_end_m"])


def _path6_record():
    return ref.load_capture_records()[8]  # two endpoint records first


def test_empty_domain_record_is_vacuously_safe():
    record = _path6_record()
    entry = ref.run_capture_record(record)
    assert entry["kind"] == "path" and entry["record_index"] == 6
    floated = entry["float_directed"]
    assert floated["status"] == "safe_within_tolerance"
    assert floated["min_gap_lower_m"] is None
    assert entry.get("min_gap_upper_m") is None
    # the directed certificate concluded safety; no exact rerun happened
    assert entry["exact_rational"] is None
    assert entry["feasible_point"] is None
    # the parameterized discriminator reports the same vacuous shape
    result = ref.run_discriminator(record=record)
    assert result["exact_rational"]["status"] == "safe_within_tolerance"
    assert result["exact_rational"]["min_gap_lower_m"] is None
    assert "min_gap_interval_m" not in result
    decision = result["decision"]
    assert decision["path_safe_within_tolerance"] is True
    assert decision["violation_proven"] is False
    assert decision["refusal_classification"] == "none_safe_within_tolerance"
    # no finite gap exists or is required on the empty foot-inside domain
    assert decision["min_gap_lower_plus_tolerance_m"] is None
    # end-pose distinction: all three quantities reported as exact
    # strings, or explicitly chart-unresolved with a reason
    samples = result["end_pose_distinction"]["samples"]
    assert samples
    for item in samples:
        if item.get("chart_ok"):
            for key in ("contract_gap", "plane_height", "local_normal_gap"):
                assert len(item[key]) == 2
                for value in item[key]:
                    Fraction(value)
        else:
            assert item.get("reason")


def _synthetic_violation_record():
    record = ref.load_literal_record()
    for corner in record["path"]["source_end_m"]:
        corner[2] -= 4e-4
    return record


def test_violation_classification_retains_exact_strings():
    record = _synthetic_violation_record()
    result = ref.run_discriminator(record=record)
    decision = result["decision"]
    assert decision["path_safe_within_tolerance"] is False
    assert decision["violation_proven"] is True
    assert decision["refusal_classification"] == "physical_violation_proven"
    violation = result["exact_rational"]["violation"]
    assert violation is not None
    tolerance = Fraction(float(GAP_TOLERANCE))
    low, high = (Fraction(value)
                 for value in violation["gap_interval_exact"])
    assert low <= high
    assert high < -tolerance
    witness = violation["point_witness"]
    assert witness is not None
    for key in ("t_exact", "u_exact", "v_exact"):
        assert Fraction(0) <= Fraction(witness[key]) <= Fraction(1)
    enclosure_low, enclosure_high = (
        Fraction(value) for value in witness["gap_interval_exact"])
    assert enclosure_low <= enclosure_high
    assert enclosure_high < -tolerance
    assert result["float_directed"]["status"] == "violation_proven"


def test_inconclusive_chart_budget_refusal_classification():
    record = _synthetic_violation_record()
    # depth 0 exhausts every non-concluding box: the same record that is
    # provably violating at full budget must classify as inconclusive
    # refusal, never as safe and never as an accepted violation.
    result = ref.run_discriminator(record=record, max_depth=0)
    decision = result["decision"]
    assert decision["path_safe_within_tolerance"] is False
    assert decision["violation_proven"] is False
    assert decision["inconclusive"] is True
    assert decision["refusal_classification"] == (
        "chart_or_budget_inconclusive_refusal")
    assert result["exact_rational"]["status"] == "inconclusive"
    assert result["exact_rational"]["remaining_boxes"]
