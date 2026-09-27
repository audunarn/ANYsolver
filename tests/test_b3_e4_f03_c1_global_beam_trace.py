"""Bounded physical-motion witnesses for retained B3 face fitting."""

import numpy as np
import pytest

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_global_beam_trace import (
    SOURCE, _action_density, _fit_case, _surface_samples,
)
from scripts.b3_e4_f03_c1_six_channel_same_beam import _solid_action_on_beam
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


@pytest.fixture(scope="module")
def sampled_face():
    deck, _, coords, _, _, _ = _source(SOURCE / "tip_mx")
    _, bar = _element_domain_nodes(deck)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    matrix, active, records = _surface_samples(coords, bar, beam)
    return coords, matrix, active, records, beam


def test_shared_native_trace_recovers_common_rigid_translation(sampled_face):
    coords, matrix, active, records, _ = sampled_face
    shift = np.array((2e-7, -3e-7, 4e-7))
    field = {node: shift for node in coords}
    result = _fit_case(matrix, records, field, np.ones(6))
    assert len(active) == result["trace_fit_rank"]
    assert result["face_rms_difference_m"] < 1e-16
    assert abs(result["outside_retained_b3_trace_work_J"]) < 1e-12


def test_shared_native_trace_recovers_common_rigid_rotation(sampled_face):
    coords, matrix, active, records, _ = sampled_face
    spin = np.array((2e-5, -3e-5, 4e-5))
    field = {node: np.cross(spin, xyz) for node, xyz in coords.items()}
    result = _fit_case(matrix, records, field, np.ones(6))
    assert len(active) == result["trace_fit_rank"]
    assert result["face_rms_difference_m"] < 1e-16
    assert abs(result["outside_retained_b3_trace_work_J"]) < 1e-12


def test_retained_trace_detects_nonrepresentable_face_warp(sampled_face):
    coords, matrix, _, records, _ = sampled_face
    field = {node: np.zeros(3) for node in coords}
    face_nodes = {node for ids, *_ in records for node in ids}
    node = next(node for node in face_nodes if
                abs(coords[node][0]-.95) < 1e-10 and
                abs(coords[node][1]) < 1e-10 and
                abs(coords[node][2]-.0175) < 1e-10)
    field[node] = np.array((0., 0., 1e-6))
    result = _fit_case(matrix, records, field, np.ones(6))
    assert result["face_rms_difference_m"] > 1e-9


def test_face_density_virtual_work_matches_independent_retained_action(
        sampled_face):
    _, matrix, active, records, beam = sampled_face
    dual = np.array((1000., -500., 200., 30., -40., 50.))
    from_face = matrix.T@_action_density(records, dual)
    from_port, _ = _solid_action_on_beam(beam, dual, 3)
    np.testing.assert_allclose(from_face, from_port[active],
                               rtol=2e-12, atol=1e-9)
