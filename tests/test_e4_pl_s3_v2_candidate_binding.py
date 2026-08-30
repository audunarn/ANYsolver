from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from anysolver.e4_pl_s3_v2_element import (
    FORMULATION_ID,
    IMPLEMENTATION_ID,
    SELECTOR,
)
from anysolver.elements import DEFAULT_Q4_FORMULATION, DEFAULT_S3_FORMULATION


ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "docs" / "reference_cases" / "e4_pl_s3_v2_candidate_binding.json"


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _reject_nonfinite(value: str) -> object:
    raise ValueError(f"nonfinite JSON value: {value}")


def _decode(raw: bytes) -> dict[str, object]:
    made = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_nonfinite,
    )
    assert isinstance(made, dict)
    canonical = (json.dumps(made, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert raw == canonical
    return made


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_candidate_binding_is_canonical_and_binds_every_registered_file() -> None:
    binding = _decode(BINDING.read_bytes())
    assert set(binding) == {
        "authority_inputs",
        "candidate",
        "defaults",
        "formal_execution",
        "independent_evidence",
        "parent",
        "production_paths",
        "production_restriction",
        "schema",
        "scope",
        "test_lanes",
    }
    assert binding["schema"] == "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1"

    registered = binding["authority_inputs"] + binding["production_paths"]
    paths = [record["path"] for record in registered]
    assert len(paths) == len(set(paths))
    for record in registered:
        path = ROOT / record["path"]
        assert path.is_file()
        assert path.stat().st_size == record["bytes"]
        assert _sha256(path) == record["sha256"]


def test_candidate_identity_scope_defaults_and_formal_stop_are_exact() -> None:
    binding = _decode(BINDING.read_bytes())
    assert binding["candidate"] == {
        "formulation_id": FORMULATION_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "production_class": "StrictFlatLinearE4PLS3V2ShellElement",
        "selectors": [SELECTOR, "qualified-s3-v2"],
        "stage_gate": "PASS_E4_PL_S3_V2A_LOCAL_FORMULATION",
    }
    assert binding["defaults"] == {
        "default_q4_formulation": DEFAULT_Q4_FORMULATION,
        "default_s3_formulation": DEFAULT_S3_FORMULATION,
        "q4_mechanics_unchanged": True,
        "s3_v1_mechanics_unchanged": True,
    }
    assert DEFAULT_Q4_FORMULATION == "e4-pl"
    assert DEFAULT_S3_FORMULATION == "legacy-s3"
    assert binding["scope"] == {
        "blocked": [
            "curved_shell",
            "dynamic",
            "generalized_section",
            "material_nonlinearity",
            "mixed_element_mesh",
            "nonlinear_geometry",
            "qualified_recovery",
            "restart",
            "serialization",
        ],
        "model_boundary": "PURE_EXACT_V2_GLOBAL_FLAT_PLANE_COMMON_PHYSICAL_DIRECTOR",
        "supported": [
            "dead_uniform_or_affine_transverse_pressure",
            "linear_internal_force",
            "linear_stiffness",
            "raw_variational_resultants",
        ],
    }
    assert binding["formal_execution"] == {
        "candidate_wheel_frozen": False,
        "default_activation_authorized": False,
        "mixed_funnel_authorized": False,
        "next_required_authority": "STAGE_4_FLAT_MIXED_FUNNEL_SUCCESSOR_CONTRACT",
        "qualification_claimed": False,
    }
    assert binding["production_restriction"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"


def test_candidate_binding_parser_rejects_duplicate_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        _decode(b'{"a":1,"a":2}\n')
    with pytest.raises(ValueError, match="nonfinite JSON value"):
        _decode(b'{"a":NaN}\n')
