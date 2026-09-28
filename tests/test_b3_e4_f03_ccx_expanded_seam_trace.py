"""Bounded expanded-shell kinematics, without claiming sided interface work."""

import numpy as np
import pytest

from scripts.b3_e4_f03_ccx_expanded_seam_trace import reconstruct


def _fields():
    coordinates = {}
    for i in range(5):
        x = i/4
        for y, z in ((0., -.0175), (0., .0175),
                     (-.005, .0175), (.005, .0175)):
            coordinates[len(coordinates)+1] = (x, y, z)
    return coordinates


def _manifest():
    return {"profile": "native_line_geometry", "variant": "flat", "nx": 4}


def test_common_finite_rigid_motion_preserves_relative_face_triads():
    coordinates = _fields()
    angle = .31
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array(((c, 0., s), (0., 1., 0.), (-s, 0., c)))
    shift = np.array((.13, -.07, .04))
    displacement = {n: rotation@np.asarray(x)+shift-np.asarray(x)
                    for n, x in coordinates.items()}
    result = reconstruct(_manifest(), coordinates, displacement)
    assert result["sample_count"] == 5
    assert result["max_reference_seam_gap_m"] < 1e-14
    assert result["max_current_seam_gap_m"] < 1e-14
    assert result["max_relative_triads_frobenius"] < 1e-13


def test_director_mismatch_is_detected_without_a_position_gap():
    coordinates = _fields()
    displacement = {n: np.zeros(3) for n in coordinates}
    # Move the two web faces oppositely in x at the interior seam station.
    displacement[11] = np.array((1e-4, 0., 0.))
    displacement[12] = np.array((-1e-4, 0., 0.))
    result = reconstruct(_manifest(), coordinates, displacement)
    assert result["max_current_seam_gap_m"] < 1e-14
    assert result["max_relative_triads_frobenius"] > 1e-2


def test_missing_face_or_field_is_rejected():
    coordinates = _fields()
    displacement = {n: np.zeros(3) for n in coordinates}
    with pytest.raises(ValueError, match="complete expanded"):
        reconstruct(_manifest(), coordinates, {1: np.zeros(3)})
    coordinates.pop(11)
    displacement.pop(11)
    with pytest.raises(ValueError, match="unique expanded"):
        reconstruct(_manifest(), coordinates, displacement)
