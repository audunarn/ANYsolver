"""Synthetic parser cases; no external solver execution in these tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _b3_e4_ccx_3d_canary_parser import parse_completed_response  # noqa: E402


STATUS = """SUMMARY OF JOB INFORMATION
  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME
     1          1     1     1  0.100000E+01  0.100000E+01  0.100000E+01
"""


def dat_rows() -> str:
    rows = [" displacements (vx,vy,vz) for set ALLNODES and time  0.1000000E+01", ""]
    for i in range(1, 49):
        rows.append(f"{i:10d}  0.000000E+00  {i*1e-7:.6E}  0.000000E+00")
    rows += ["", " forces (fx,fy,fz) for set ALLNODES and time  0.1000000E+01"]
    return "\n".join(rows)


def test_parses_one_complete_printed_response():
    result = parse_completed_response("Job finished\n", STATUS, dat_rows())
    assert result["accepted_steps"] == 1
    assert result["printed_nodes"] == 48
    assert result["tip_translation_m"] == pytest.approx((0., 4.8e-6, 0.))
    assert result["tip_rotation_rad"] is None


def test_six_coordinate_beam_row_is_preserved():
    output = dat_rows().replace("4.800000E-06  0.000000E+00",
                                "4.800000E-06  0.000000E+00  1.000000E-04  0.000000E+00  2.000000E-04")
    parsed = parse_completed_response("Job finished", STATUS, output)
    assert parsed["tip_rotation_rad"] == pytest.approx((1e-4, 0., 2e-4))
    assert parsed["printed_six_coordinate_nodes"] == [48]


def test_zero_tip_allowed_only_for_unloaded_influence_response():
    zero = dat_rows().replace("4.800000E-06", "0.000000E+00")
    zero = zero.replace("4.700000E-06", "0.000000E+00")
    # Other nodes can still move under a prescribed boundary motion.
    assert parse_completed_response("Job finished", STATUS, zero,
                                    require_nonzero_tip=False)["tip_translation_m"] == (0., 0., 0.)
    with pytest.raises(ValueError, match="zero tip"):
        parse_completed_response("Job finished", STATUS, zero)


@pytest.mark.parametrize("stdout,status,dat,reason", [
    ("Job finished\nERROR", STATUS, dat_rows(), "cleanly"),
    ("Job finished", STATUS.replace("0.100000E+01", "0.900000E+00"), dat_rows(),
     "accepted"),
    ("Job finished", STATUS +
     "     1          2     1     1  0.100000E+01  0.100000E+01  0.100000E+01\n",
     dat_rows(), "accepted"),
    ("Job finished", STATUS, dat_rows().replace("ALLNODES", "OTHER"), "block"),
    ("Job finished", STATUS, dat_rows().replace("        48", "        47"),
     "displacement"),
    ("Job finished", STATUS, dat_rows().replace("4.800000E-06", "NaN"),
     "displacement"),
    ("Job finished", STATUS, dat_rows().replace(
        "4.800000E-06  0.000000E+00",
        "4.800000E-06  0.000000E+00  0.000000E+00"), "displacement"),
    ("Job finished", STATUS, dat_rows().replace(
        "\n forces (", "\n        48  0.000000E+00  4.800000E-06  0.000000E+00\n\n forces ("),
     "displacement"),
])
def test_rejects_incomplete_or_corrupt_output(stdout, status, dat, reason):
    with pytest.raises(ValueError, match=reason):
        parse_completed_response(stdout, status, dat)
