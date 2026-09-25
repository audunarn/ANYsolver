"""Bounded controls for the exploratory conforming solid-bond deck."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "b3_e4_f03_ccx_solid_bond_screen.py"
SPEC = importlib.util.spec_from_file_location("solid_bond_screen", MODULE)
SCREEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREEN)


@pytest.mark.parametrize("factor", (1, 2))
@pytest.mark.parametrize("shear", ("uy_x", "ux_y"))
def test_shared_interface_and_prescribed_plate_only(factor, shear):
    deck, meta = SCREEN.build(factor, shear)
    assert meta["shared_interface_nodes"] == (2 * factor + 1) * (4 * factor + 1)
    assert meta["plate_elements"] == 96 * factor**3
    assert meta["bar_elements"] == 16 * factor**3
    assert deck.count("*SOLID SECTION") == 2
    assert "*MPC" not in deck and "*TIE" not in deck
    assert len(meta["probe_node_ids"]) == len(set(meta["probe_node_ids"]))
    for station in meta["bar_station_nodes"].values():
        assert len(station) == (2 * factor + 1)**2


def test_recovery_rigid_motion_and_orthogonal_shear_measures():
    _, meta = SCREEN.build(1, "uy_x")
    coordinates = meta["probe_coordinates_m"]
    for sign in (1., -1.):
        motion = {int(node): np.array([-.4e-4 * xyz[1],
                                       .4e-4 * xyz[0], 0.]) * sign
                  for node, xyz in coordinates.items()}
        result = SCREEN.recover(meta, motion)
        assert result["centerline_tangent_yaw_rad"] == pytest.approx(sign * .4e-4)
        assert result["surface_square_patch_yaw_rad"] == pytest.approx(sign * .4e-4)
        for station in result["station_motion"].values():
            assert station["section_rotation_rad"][2] == pytest.approx(sign * .4e-4)
            assert station["max_warping_residual_m"] < 1e-17


def test_probe_parser_requires_complete_unique_finite_inventory():
    dat = "displacements (vx,vy,vz) for set PROBE and time 0.1000000E+01\n\n"
    dat += "  1  0.0  1.0E-5  0.0\n  2  0.0  2.0E-5  0.0\n\n"
    values = SCREEN.parse_probe_displacements(dat, {1, 2})
    assert values[2][1] == pytest.approx(2e-5)
    with pytest.raises(ValueError, match="incomplete"):
        SCREEN.parse_probe_displacements(dat, {1, 2, 3})
