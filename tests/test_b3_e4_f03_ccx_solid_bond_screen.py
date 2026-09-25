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


@pytest.mark.parametrize("factor", (1, 2, 4))
@pytest.mark.parametrize("load,expected", (("tip_mx", [0.,0.,0.,100.,0.,0.]),
                                            ("tip_fz", [0.,0.,1000.,0.,-1000.,0.])))
def test_terminal_bond_has_only_declared_shared_patch(factor, load, expected):
    deck, meta = SCREEN.build(factor, load, boundary_policy="left_root",
                              bond_policy="terminal")
    assert meta["bond_policy"] == "terminal"
    assert meta["bond_interval_m"] == [.9, 1.]
    assert meta["shared_interface_nodes"] == (factor+1)*(2*factor+1)
    assert meta["detached_interface_nodes"] == 4*factor*(2*factor+1)
    assert len(meta["shared_interface_node_ids"]) == meta["shared_interface_nodes"]
    assert len(meta["detached_stiffener_node_ids"]) == meta["detached_interface_nodes"]
    assert not set(meta["detached_stiffener_node_ids"]) & set(
        meta["shared_interface_node_ids"])
    assert not set(meta["beam_root_node_ids"]) & set(
        meta["plate_boundary_node_ids"])
    assert set(meta["boundary_node_ids"]) == (
        set(meta["beam_root_node_ids"]) | set(meta["plate_boundary_node_ids"]))
    assert "*MPC" not in deck and "*TIE" not in deck
    applied = {int(node): np.array(force) for node, force in
               meta["applied_nodal_forces_N"].items()}
    assert SCREEN._wrench(applied, meta["probe_coordinates_m"]) == pytest.approx(
        expected, abs=1e-10)
    displacement = {int(node): np.zeros(3) for node in meta["probe_node_ids"]}
    recovered = SCREEN.recover(meta, displacement)
    assert recovered["station_motion"]["500"]["interface_shared"] is False
    assert "shared_face_mean_translation_m" not in recovered["station_motion"]["500"]
    assert recovered["station_motion"]["1000"]["interface_shared"] is True
    assert "shared_face_mean_translation_m" in recovered["station_motion"]["1000"]
    assert recovered["unbonded_midspan_normal_separation_m"][
        "bar_minus_plate_z_m"] == [0., 0., 0.]
    bottom = next(index for index in meta["bar_station_nodes"]["500"]
                  if meta["probe_coordinates_m"][str(index)] == [.5, 0., .035])
    displacement[bottom] = np.array([0., 0., -1e-6])
    assert SCREEN.recover(meta, displacement)[
        "unbonded_midspan_normal_separation_m"]["bar_minus_plate_z_m"][1] == pytest.approx(-1e-6)


@pytest.mark.parametrize("factor", (1, 2, 4))
def test_reverse_fz_audit_preserves_geometry_and_reverses_exact_tip_wrench(factor):
    forward, control = SCREEN.build(factor, "tip_fz", boundary_policy="left_root",
                                    bond_policy="terminal")
    deck, meta = SCREEN.build(factor, "tip_fz", boundary_policy="left_root",
                              bond_policy="terminal", reverse_tip_fz=True)
    assert meta["shared_interface_node_ids"] == control["shared_interface_node_ids"]
    assert meta["detached_stiffener_node_ids"] == control["detached_stiffener_node_ids"]
    assert len(meta["unbonded_interface_pairs"]) == meta["detached_interface_nodes"]
    assert "*NODE PRINT,NSET=UnbondedInterface\nU" in deck
    assert "*NODE PRINT,NSET=UnbondedInterface" not in forward
    applied = {int(node): np.array(force) for node, force in
               meta["applied_nodal_forces_N"].items()}
    assert SCREEN._wrench(applied, meta["probe_coordinates_m"]) == pytest.approx(
        [0., 0., -1000., 0., 1000., 0.], abs=1e-10)
    interface={node:np.zeros(3) for pair in meta["unbonded_interface_pairs"]
               for node in pair}
    for plate, bar in meta["unbonded_interface_pairs"]:
        interface[bar][2]=1e-6
    audit=SCREEN.audit_unbonded_open(meta,interface)
    assert audit["paired_nodes"] == meta["detached_interface_nodes"]
    assert audit["minimum_reference_normal_gap_m"] == pytest.approx(1e-6)
    assert audit["negative_nodal_gaps"] == 0
    interface[meta["unbonded_interface_pairs"][0][1]][2]=-1e-6
    assert SCREEN.audit_unbonded_open(meta,interface)["negative_nodal_gaps"] == 1


def test_reverse_fz_audit_rejects_wrong_scope_and_incomplete_inventory():
    with pytest.raises(ValueError, match="reverse Fz"):
        SCREEN.build(1,"tip_mx",boundary_policy="left_root",
                     bond_policy="terminal",reverse_tip_fz=True)
    _,meta=SCREEN.build(1,"tip_fz",boundary_policy="left_root",
                        bond_policy="terminal",reverse_tip_fz=True)
    with pytest.raises(ValueError,match="incomplete"):
        SCREEN.audit_unbonded_open(meta,{})


@pytest.mark.parametrize("factor", (1, 2, 4))
@pytest.mark.parametrize("load,expected", (("tip_mx", [0.,0.,0.,100.,0.,0.]),
                                            ("tip_fz", [0.,0.,1000.,0.,-1000.,0.])))
def test_detached_bar_control_preserves_mesh_loads_and_separate_roots(factor,load,expected):
    _, terminal=SCREEN.build(factor,load,boundary_policy="left_root",
                             bond_policy="terminal")
    deck,meta=SCREEN.build(factor,load,boundary_policy="left_root",
                            bond_policy="detached")
    assert meta["shared_interface_nodes"] == 0
    assert meta["bond_interval_m"] is None
    assert meta["detached_interface_nodes"] == (5*factor+1)*(2*factor+1)
    assert meta["plate_elements"] == terminal["plate_elements"]
    assert meta["bar_elements"] == terminal["bar_elements"]
    assert set(meta["beam_root_node_ids"]).isdisjoint(meta["plate_boundary_node_ids"])
    assert "*CONTACT PAIR" not in deck and "*TIE" not in deck
    applied={int(node):np.array(force) for node,force in
             meta["applied_nodal_forces_N"].items()}
    assert SCREEN._wrench(applied,meta["probe_coordinates_m"]) == pytest.approx(
        expected,abs=1e-10)
    displacement={int(node):np.zeros(3) for node in meta["probe_node_ids"]}
    assert not SCREEN.recover(meta,displacement)["station_motion"]["1000"]["interface_shared"]


@pytest.mark.parametrize("factor", (1, 2, 4))
def test_terminal_hard_mortar_faces_exclude_bonded_patch(factor):
    deck, meta = SCREEN.build(factor, "tip_fz", boundary_policy="left_root",
                              bond_policy="terminal", contact_policy="mortar_hard")
    assert meta["contact_policy"] == "mortar_hard"
    assert len(meta["plate_contact_face_element_ids"]) == 8*factor**2
    assert len(meta["bar_contact_face_element_ids"]) == 8*factor**2
    assert max(meta["plate_contact_face_element_ids"]) <= meta["plate_elements"]
    assert min(meta["bar_contact_face_element_ids"]) > meta["plate_elements"]
    assert "PlateUnbondedFaces,S2" in deck
    assert "BarUnbondedFaces,S1" in deck
    assert "*CONTACT PAIR,INTERACTION=HardUnbonded,TYPE=MORTAR" in deck
    assert "*SURFACE INTERACTION,NAME=HardUnbonded\n*CONTACT PAIR" in deck
    assert "*SURFACE BEHAVIOR" not in deck and "ADJUST" not in deck
    assert "*CONTACT PRINT,FREQUENCY=9999\nCDIS,CSTR,CNUM" in deck
    without, _ = SCREEN.build(factor, "tip_fz", boundary_policy="left_root",
                              bond_policy="terminal")
    assert "*CONTACT PAIR" not in without


def test_contact_requires_separate_terminal_bond():
    with pytest.raises(ValueError, match="requires terminal bond"):
        SCREEN.build(1, "tip_fz", boundary_policy="left_root",
                     contact_policy="mortar_hard")


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


def test_shared_face_trace_distinguishes_rigid_twist_from_section_warping():
    _, meta = SCREEN.build(4, "tip_mx", boundary_policy="left_root")
    twist = 1e-4
    rigid = {int(node): np.array([0., -(xyz[2]-.085)*twist,
                                  xyz[1]*twist])
             for node, xyz in meta["probe_coordinates_m"].items()}
    station = SCREEN.recover(meta, rigid)["station_motion"]["500"]
    assert np.linalg.norm(station["shared_face_minus_fitted_bottom_m"]) < 1e-15
    assert abs(station["shared_face_slope_minus_section_rx_rad"]) < 1e-14
    warped = {node: value + np.array([0., 0., .01 *
                                     meta["probe_coordinates_m"][str(node)][1] ** 3])
              for node, value in rigid.items()}
    station = SCREEN.recover(meta, warped)["station_motion"]["500"]
    assert abs(station["shared_face_slope_minus_section_rx_rad"]) > 1e-6
    assert station["max_warping_residual_m"] > 1e-8


def test_midspan_transverse_slope_preserves_independent_shear_field():
    _, meta = SCREEN.build(4, "tip_fz", boundary_policy="left_root")
    rotation = 1e-4
    rigid = {int(node): np.array([(xyz[2]-.085)*rotation, 0.,
                                  -xyz[0]*rotation])
             for node, xyz in meta["probe_coordinates_m"].items()}
    assert abs(SCREEN.recover(meta, rigid)[
        "midspan_transverse_kinematics"]["slope_plus_section_ry_rad"]) < 1e-14
    shear = 2e-5
    sheared = {node: value + np.array([0., 0., shear *
                                      meta["probe_coordinates_m"][str(node)][0]])
               for node, value in rigid.items()}
    measured = SCREEN.recover(meta, sheared)["midspan_transverse_kinematics"]
    assert measured["slope_plus_section_ry_rad"] == pytest.approx(shear, abs=1e-13)
