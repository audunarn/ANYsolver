"""Bounded controls for the exploratory conforming solid-bond deck."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "b3_e4_f03_ccx_solid_bond_screen.py"
SPEC = importlib.util.spec_from_file_location("solid_bond_screen", MODULE)
SCREEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREEN)


@pytest.mark.parametrize("factor", (1, 2, 4))
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


@pytest.mark.parametrize("factor", (1, 2, 4))
@pytest.mark.parametrize("load,expected", (("tip_mx", [0.,0.,0.,100.,0.,0.]),
                                            ("tip_fz", [0.,0.,1000.,0.,-1000.,0.])))
def test_end_face_load_has_exact_declared_wrench(factor, load, expected):
    deck,meta=SCREEN.build(factor,load)
    assert "*CLOAD" in deck
    applied={int(node):np.array(force) for node,force in
             meta["applied_nodal_forces_N"].items()}
    assert len(applied)==(2*factor+1)**2
    assert SCREEN._wrench(applied,meta["probe_coordinates_m"]) == pytest.approx(expected,abs=1e-10)


@pytest.mark.parametrize("factor", (1, 4))
@pytest.mark.parametrize("load", ("tip_mx", "tip_fz"))
def test_left_edge_reference_preserves_end_wrench_and_free_stiffener(factor, load):
    _, meta = SCREEN.build(factor, load, boundary_policy="left")
    boundary = meta["boundary_coordinates_m"]
    assert meta["boundary_policy"] == "left"
    assert len(boundary) == (6 * factor + 1) * (2 * factor + 1)
    assert all(xyz[0] == -.5 for xyz in boundary.values())
    assert set(meta["boundary_node_ids"]).isdisjoint(
        meta["bar_station_nodes"]["0"])
    applied = {int(node): np.array(force) for node, force in
               meta["applied_nodal_forces_N"].items()}
    expected = ([0., 0., 0., 100., 0., 0.] if load == "tip_mx" else
                [0., 0., 1000., 0., -1000., 0.])
    assert SCREEN._wrench(applied, meta["probe_coordinates_m"]) == pytest.approx(
        expected, abs=1e-10)


@pytest.mark.parametrize("factor", (1, 4))
def test_left_edge_and_root_face_support_are_explicit(factor):
    deck, meta = SCREEN.build(factor, "tip_fz", boundary_policy="left_root")
    plate = set(meta["plate_boundary_node_ids"])
    root = set(meta["beam_root_node_ids"])
    support = set(meta["boundary_node_ids"])
    assert len(root) == (2 * factor + 1) ** 2
    assert root == set(meta["bar_station_nodes"]["0"])
    assert support == plate | root
    assert root - plate
    assert meta["support_set"] == "Supports"
    assert "*NODE PRINT,NSET=Supports" in deck
    assert "*MPC" not in deck and "*TIE" not in deck


@pytest.mark.parametrize("load", ("tip_mx", "tip_fz"))
def test_end_face_recovery_is_conjugate_to_actual_discrete_load(load):
    _, meta = SCREEN.build(1, load, boundary_policy="left_root")
    amplitude = 2.5e-5
    displacement = {}
    for node, xyz in meta["probe_coordinates_m"].items():
        _, y, z = xyz
        displacement[int(node)] = (
            np.array([0., -(z-.085)*amplitude, y*amplitude])
            if load == "tip_mx" else np.array([0., 0., amplitude]))
    result = SCREEN.recover(meta, displacement)
    measure = result["tip_work_conjugate_displacement"]
    assert measure["value"] == pytest.approx(amplitude, abs=1e-15)
    assert measure["unit"] == ("rad" if load == "tip_mx" else "m")
