"""Kinematic witnesses for the local resolved-solid trace projections."""

import numpy as np

from scripts.b3_e4_f03_c1_solid_trace_residual import (
    SOURCE, _bar_section_fit, _plate_director_fit,
)
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


def test_local_plate_director_fit_preserves_representable_motion():
    deck, = (SOURCE / "tip_mx").glob("*.inp")
    coords = _read_deck_nodes(deck)
    plate, _ = _element_domain_nodes(deck)
    displacement = {}
    for node in plate:
        x, y, z = coords[node]
        translation = np.array((x * 1e-5, -y * 2e-5, x * y * 3e-5))
        rotation = np.array((2e-4, -3e-4, 0.))
        displacement[node] = translation + np.cross(rotation, (0., 0., z))
    action = {node for node in plate if .9-1e-10 <= coords[node][0] <= 1.+1e-10
              and abs(abs(coords[node][2])-.0175) < 1e-10
              and abs(coords[node][1]) <= .05+1e-10}
    fitted, count = _plate_director_fit(coords, displacement, plate, action)
    assert count == 121
    assert max(np.linalg.norm(fitted[node]-displacement[node])
               for node in action) < 1e-15


def test_local_bar_fit_preserves_rigid_sections():
    deck, = (SOURCE / "tip_mx").glob("*.inp")
    coords = _read_deck_nodes(deck)
    _, bar = _element_domain_nodes(deck)
    displacement = {}
    for node in bar:
        x, y, z = coords[node]
        translation = np.array((x * 1e-5, -x * 2e-5, x * 3e-5))
        rotation = np.array((2e-4, -3e-4, 4e-4))
        displacement[node] = translation + np.cross(
            rotation, (0., y, z-.0675))
    action = {node for node in bar if .9-1e-10 <= coords[node][0] <= 1.+1e-10
              and abs(coords[node][1]) <= .05+1e-10 and
              (abs(coords[node][2]-.0175) < 1e-10 or
               abs(coords[node][2]-.1175) < 1e-10)}
    fitted, rms = _bar_section_fit(coords, displacement, bar, action)
    assert len(rms) == 9
    assert max(rms.values()) < 1e-15
    assert max(np.linalg.norm(fitted[node]-displacement[node])
               for node in action) < 1e-15
