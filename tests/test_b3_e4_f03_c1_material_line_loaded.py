"""Source-identity guard for the bounded same-law loaded comparison."""

import json
from pathlib import Path

import pytest

from scripts.b3_e4_f03_c1_material_line_loaded import (
    _validated_solid_reconstruction,
)


RECONSTRUCTION = (
    Path(__file__).resolve().parents[1] / "docs" / "agent_plans" /
    "B3_E4_F03_C1_MATERIAL_LINE_P0_SOLID_RECON_DEV_V1.json"
)


def test_reviewed_solid_reconstruction_is_admitted():
    solid = _validated_solid_reconstruction(RECONSTRUCTION)
    assert set(solid["cases"]) == {"tip_mx", "tip_fz"}
    assert len(solid["unit_records"]) == 24


def test_different_completed_solid_reconstruction_is_rejected(tmp_path):
    solid = json.loads(RECONSTRUCTION.read_text())
    solid["cases"]["tip_mx"]["source_model_sha256"] = "0" * 64
    path = tmp_path / "other-solid.json"
    path.write_text(json.dumps(solid), encoding="utf-8")
    with pytest.raises(ValueError, match="identity changed"):
        _validated_solid_reconstruction(path)
