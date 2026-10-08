"""Gate-shape checks for the unregistered nested-x screen."""

import json

import pytest

from scripts.b3_e4_f03_qp_nested_x_adjudicate import adjudicate


def _record(degree, quarter_fy=0.):
    bands = [[0., 0., 0.] for _ in range(8)]
    bands[2][1] = quarter_fy
    return {
        "status": "UNREGISTERED_NESTED_X_PILOT",
        "degree": degree, "x_hex": ["0x0p+0", "0x1p+0"],
        "y_hex": ["0x0p+0", "0x1p+0"],
        "station_intervals": [[0., 1.]],
        "signed": {
            "tip_pose": [0., 0., 0.],
            "shell_energy_j": 0., "beam_energy_j": 0.,
            "total_energy_j": 0., "external_work_j": 0.,
            "eta": [0., 0., 0.],
            "root_section": [0., 0., 0.],
            "tip_section": [0., 0., 0.],
            "root_atom": [0., 0., 0.],
            "tip_atom": [0., 0., 0.],
            "line_wrench": [0., 0., 0.], "bands": bands,
        },
        "functional": {"breaks": [0., 1.],
                       "coefficients": [[[0., 0., 0.]]],
                       "cosine": [0., 0., 0.],
                       "atoms": [[0., 0., 0.], [0., 0., 0.]]},
    }


def _paths(tmp_path, rows):
    paths = []
    for i, row in enumerate(rows):
        path = tmp_path / f"q{i}.json"
        path.write_text(json.dumps(row), encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def test_every_signed_band_is_in_the_holdout(tmp_path):
    rows = [_record(4, 0.), _record(5, 100.), _record(6, 300.)]
    result = adjudicate(_paths(tmp_path, rows))
    assert result["signed_count"] == 49
    assert result["signed_failures"] == ["quarter_3[1]"]
    assert not result["draft_settling_screen_pass"]
    assert result["qualification_status"] == "F03_G0B_OPEN"


def test_incomplete_band_or_mixed_grid_cannot_pass(tmp_path):
    rows = [_record(4), _record(5), _record(6)]
    rows[1]["signed"]["bands"].pop()
    with pytest.raises(ValueError, match=r"zip\(\) argument"):
        adjudicate(_paths(tmp_path, rows))
    rows = [_record(4), _record(5), _record(6)]
    rows[2]["x_hex"] = ["different"]
    with pytest.raises(ValueError, match="same|fixed grid"):
        adjudicate(_paths(tmp_path, rows))
