"""Public and migration boundaries for qualified S3 V2D activation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from anysolver import (
    AnyStructureFEMConfig,
    LegacyS3MigrationWarning,
    LegacyShellElement,
    NativeParityE4PLS3V2DShellElement,
    S3_V2D_FORMULATION_ID,
    build_fe_model_from_generated_geometry,
    create_element,
    create_shell_element,
    shell_element_from_dict,
    shell_formulation_diagnostics,
)


NORMAL = (0.0, 0.0, 1.0)
ROOT = Path(__file__).resolve().parents[1]
ACTIVATION = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_v2d_default_activation_candidate.json"
)
INTEGRATION_REPAIR = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_v2d_default_integration_repair.json"
)
Q4_REPLAY_HOTFIX = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_q4_0_4_1_replay_hotfix.json"
)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key: {key}")
        made[key] = value
    return made


def _q4_replay_hotfix() -> dict[str, object]:
    raw = Q4_REPLAY_HOTFIX.read_bytes()
    payload = json.loads(raw, object_pairs_hook=_strict_object)
    assert raw == (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    for record in payload["historical_authority"]:
        source = ROOT / record["path"]
        data = source.read_bytes()
        assert len(data) == record["bytes"]
        assert hashlib.sha256(data).hexdigest().upper() == record["sha256"]
    return payload


def test_activation_candidate_binds_accepted_v6w_and_unchanged_q4() -> None:
    raw = ACTIVATION.read_bytes()
    payload = json.loads(raw, object_pairs_hook=_strict_object)
    assert raw == (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")

    for record in payload["predecessor_qualification"]:
        source = ROOT / record["path"]
        data = source.read_bytes()
        assert len(data) == record["bytes"]
        assert hashlib.sha256(data).hexdigest().upper() == record["sha256"]

    q4_data = (
        ROOT / "src" / "anysolver" / "e4_pl_element.py"
    ).read_bytes().replace(b"\r\n", b"\n")
    q4_blob = hashlib.sha1(
        f"blob {len(q4_data)}\0".encode("ascii") + q4_data
    ).hexdigest()
    hotfix = _q4_replay_hotfix()
    assert payload["production_boundary"]["q4_mechanics_blob"] == hotfix[
        "source_correction"
    ]["prior_git_blob"]
    assert q4_blob == hotfix["source_correction"]["current_git_blob"]
    assert hotfix["qualification_boundary"]["q4_coefficients_or_operators_changed"] is False
    assert payload["production_boundary"]["q4_mechanics_unchanged"] is True
    assert payload["production_boundary"]["publication_authorized"] is False
    assert payload["default_policy"]["current_model_q4"] == "e4-pl"
    assert payload["default_policy"]["current_model_s3"] == "e4-pl-s3-v2d"
    assert payload["terminal"] == (
        "PROVISIONAL_GO_E4_PL_S3_V2D_DEFAULT_ACTIVATION_CANDIDATE"
    )


def test_integration_repair_preserves_qualification_and_q4_boundary() -> None:
    raw = INTEGRATION_REPAIR.read_bytes()
    payload = json.loads(raw, object_pairs_hook=_strict_object)
    assert raw == (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")

    for record in payload["preserved_qualification"]:
        source = ROOT / record["path"]
        data = source.read_bytes()
        assert len(data) == record["bytes"]
        assert hashlib.sha256(data).hexdigest().upper() == record["sha256"]
    activation = payload["activation_candidate"]
    activation_data = (ROOT / activation["path"]).read_bytes()
    assert len(activation_data) == activation["bytes"]
    assert hashlib.sha256(activation_data).hexdigest().upper() == activation["sha256"]

    q4_data = (ROOT / "src" / "anysolver" / "e4_pl_element.py").read_bytes()
    q4_data = q4_data.replace(b"\r\n", b"\n")
    q4_blob = hashlib.sha1(
        f"blob {len(q4_data)}\0".encode("ascii") + q4_data
    ).hexdigest()
    hotfix = _q4_replay_hotfix()
    assert payload["production_boundary"]["q4_mechanics_blob"] == hotfix[
        "source_correction"
    ]["prior_git_blob"]
    assert q4_blob == hotfix["source_correction"]["current_git_blob"]
    assert hotfix["qualification_boundary"]["s3_evidence_changed"] is False
    assert payload["production_boundary"]["v6w_evidence_changed"] is False
    assert payload["production_boundary"]["s3_linear_stiffness_operator_changed"] is False
    assert payload["default_policy"]["current_model_s3"] == "e4-pl-s3-v2d"
    assert payload["terminal"] == (
        "PROVISIONAL_GO_E4_PL_S3_V2D_DEFAULT_INTEGRATION_REPAIRED"
    )


@pytest.mark.parametrize(
    "alias", ("shell", "s3", "tri3", "tria3", "t3", "shell3", "qualified-s3")
)
def test_current_three_node_aliases_select_exact_v2d(alias: str) -> None:
    element = create_element(
        alias,
        1,
        [1, 2, 3],
        "steel",
        thickness=0.01,
        reference_normal=NORMAL,
    )

    assert type(element) is NativeParityE4PLS3V2DShellElement
    assert element.formulation_id == S3_V2D_FORMULATION_ID


def test_default_fails_closed_without_physical_normal() -> None:
    with pytest.raises(ValueError, match="authoritative reference_normal"):
        create_shell_element(1, [1, 2, 3], "steel")


def test_direct_and_explicit_legacy_routes_remain_available() -> None:
    direct = LegacyShellElement(1, [1, 2, 3], "steel")
    explicit = create_shell_element(
        2, [1, 2, 3], "steel", formulation="legacy-s3"
    )

    assert type(direct) is LegacyShellElement
    assert type(explicit) is LegacyShellElement


def test_missing_identity_historical_record_never_inherits_new_default() -> None:
    payload = {
        "element_id": 7,
        "node_ids": [1, 2, 3],
        "material_name": "steel",
        "thickness": 0.01,
    }
    with pytest.warns(LegacyS3MigrationWarning, match="legacy-s3"):
        restored = shell_element_from_dict(payload)

    assert type(restored) is LegacyShellElement


def test_v2d_non_axis_owner_normal_round_trip_is_binary64_exact() -> None:
    element = create_shell_element(
        8,
        [1, 2, 3],
        "steel",
        formulation="e4-pl-s3-v2d",
        reference_normal=(0.8819212643483547, -0.4713967368259981, -4.8139e-16),
    )
    payload = element.to_dict()

    first = shell_element_from_dict(payload)
    second = shell_element_from_dict(first.to_dict())

    assert first.to_dict() == payload
    assert second.to_dict() == payload

    malformed = dict(payload)
    malformed["reference_normal"] = [2.0, 0.0, 0.0]
    with pytest.raises(ValueError, match="must be unit length"):
        shell_element_from_dict(malformed)


def test_diagnostics_report_both_topology_defaults() -> None:
    s3 = shell_formulation_diagnostics(node_count=3)
    q4 = shell_formulation_diagnostics(node_count=4)

    assert s3["production_default"] is True
    assert s3["selected_formulation"] == "e4-pl-s3-v2d"
    assert s3["topology_policy"] == "NATIVE_PARITY_E4_PL_S3_V2D_DEFAULT"
    assert q4["production_default"] is True
    assert q4["selected_formulation"] == "e4-pl"


def _authorized_generated_s3() -> dict[str, object]:
    return {
        "nodes": [
            {"id": 1, "coords": [0.0, 0.0, 0.0]},
            {"id": 2, "coords": [1.0, 0.0, 0.0]},
            {"id": 3, "coords": [0.5, 0.8660254037844386, 0.0]},
        ],
        "shells": [
            {
                "id": 1,
                "node_ids": [1, 2, 3],
                "thickness": 0.01,
                "formulation": "e4-pl-s3-v2d",
                "formulation_id": S3_V2D_FORMULATION_ID,
                "reference_normal": list(NORMAL),
                "owner_normal_authority": (
                    "PHYSICAL_SURFACE_OWNER_NORMAL_V2D_V1"
                ),
            }
        ],
    }


def test_generated_geometry_requires_and_constructs_exact_v2d_authority() -> None:
    model = build_fe_model_from_generated_geometry(
        _authorized_generated_s3(),
        AnyStructureFEMConfig(),
    )

    assert type(model.mesh.get_element(1)) is NativeParityE4PLS3V2DShellElement


@pytest.mark.parametrize(
    ("field", "message"),
    (
        ("formulation_id", "requires-formulation-id"),
        ("reference_normal", "requires-owner-normal"),
        ("owner_normal_authority", "requires-physical-owner-normal-authority"),
    ),
)
def test_generated_geometry_rejects_incomplete_v2d_authority(
    field: str,
    message: str,
) -> None:
    payload = _authorized_generated_s3()
    payload["shells"][0].pop(field)  # type: ignore[index,union-attr]

    with pytest.raises(ValueError, match=message):
        build_fe_model_from_generated_geometry(payload, AnyStructureFEMConfig())
