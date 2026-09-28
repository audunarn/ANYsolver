"""Inert folded-shell deck and synthetic CalculiX output checks."""

from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.b3_e4_f03_ccx_matched_t_reference import build_bundle, parse_outputs


def _synthetic_output(manifest):
    positions = {}
    motions = {}
    expected_y = {"plate": .2, "web_low": .1,
                  "web_center": .3, "web_high": .05}
    next_node = 1000
    for name, original in manifest["loaded_nodes"].items():
        xyz = manifest["nodes_m"][str(original)]
        side = manifest["loaded_sides"][name]
        axis = 2 if side == "plate" else 1
        thickness = manifest["plate_thickness_m"] if side == "plate" else manifest["web_thickness_m"]
        for sign in (-1, 1):
            point = xyz.copy()
            point[axis] += sign*thickness/2
            positions[next_node] = point
            motions[next_node] = (0., expected_y[name]+sign*.01, 0.)
            next_node += 1

    def row(node, values):
        return f" -1{node:10d}"+"".join(f"{v:12.5E}" for v in values)

    frd = ("    2C synthetic\n"+
           "\n".join(row(n, xyz) for n, xyz in positions.items())+
           "\n -3\n -4  DISP\n -5  D1\n"+
           "\n".join(row(n, xyz) for n, xyz in motions.items())+"\n -3\n")
    support = {node: [0., 0., 0.] for node in manifest["supports"]}
    by_position = {tuple(xyz): int(node)
                   for node, xyz in manifest["nodes_m"].items()}
    low = by_position[(0., -.5, 0.)]
    middle = by_position[(0., 0., 0.)]
    high = by_position[(0., .5, 0.)]
    applied = manifest["action_wrenches"][manifest["case"]]
    support[middle] = [-v for v in applied["force_n"]]
    mx, _, mz = [-v for v in applied["moment_nm_about_origin"]]
    support[low][0] += mz
    support[high][0] -= mz
    support[low][2] -= mx
    support[high][2] += mx
    dat = (" forces (fx,fy,fz) for set SUPPORTS and time  0.1000000E+01\n\n"+
           "\n".join(f" {node} "+" ".join(f"{v:.9E}" for v in support[node])
                     for node in manifest["supports"])+"\n\n")
    return frd, dat


@pytest.mark.parametrize("variant,expected_nodes,expected_elements", [
    ("flat", 45, 32), ("t", 55, 40),
])
def test_folded_shell_inventory_and_web_only_section(variant, expected_nodes,
                                                     expected_elements):
    deck, manifest = build_bundle(variant, "web_fy", root="hinged")
    assert manifest["node_count"] == expected_nodes
    assert manifest["element_count"] == expected_elements
    assert manifest["shell_elements"] == {
        "plate": 16, "web": 16, "flange": 8 if variant == "t" else 0}
    assert manifest["web_only_section"]["area_m2"] == pytest.approx(.002)
    assert manifest["web_only_section"]["centroid_z_m"] == pytest.approx(.1)
    assert manifest["web_only_section"]["Iy_m4"] == pytest.approx(.01*.2**3/12)
    assert manifest["web_only_section"]["Iz_m4"] == pytest.approx(.2*.01**3/12)
    assert 0 < manifest["web_only_section"]["J_rect_m4"] < .2*.01**3/3
    assert manifest["web_only_section"]["nominal_shear_area_m2"] == pytest.approx(
        5*.002/6)
    assert manifest["web_centroid_offset_from_plate_midplane_m"] == [0., 0., .1]
    assert manifest["section_axes"]["Iy"] == "about_y"
    assert manifest["section"]["area_m2"] == pytest.approx(
        .003 if variant == "t" else .002)
    assert manifest["section"]["centroid_z_m"] == pytest.approx(
        2/15 if variant == "t" else .1)
    assert "*BOUNDARY\nRoot,1,3,0" in deck
    assert "Root,1,6" not in deck
    assert manifest["six_dof_b3_root_match"] is False
    assert manifest["classification"] == "unmatched_supplementary_hinged_root_comparator"
    assert len(manifest["supports"]) == (11 if variant == "t" else 9)
    assert "*NODE FILE,OUTPUT=3D\nU" in deck
    assert "*NODE PRINT,NSET=Supports\nRF" in deck
    assert "*BEAM SECTION" not in deck
    assert "*EQUATION" not in deck
    assert ("*SHELL SECTION,ELSET=Flange" in deck) == (variant == "t")
    wrenches = manifest["action_wrenches"]
    assert wrenches["plate_fy"] == {
        "force_n": [0., 100., 0.], "moment_nm_about_origin": [0., 0., 100.]}
    assert wrenches["web_fy"] == {
        "force_n": [0., 100., 0.], "moment_nm_about_origin": [-10., 0., 100.]}
    assert wrenches["web_mx"]["force_n"] == [0., 0., 0.]
    assert wrenches["web_mx"]["moment_nm_about_origin"] == pytest.approx([10., 0., 0.])


@pytest.mark.parametrize("root", ["hinged", "clamped"])
@pytest.mark.parametrize("case,work", [
    ("plate_fy", 20.), ("web_fy", 30.), ("web_mx", 5.),
])
def test_synthetic_expanded_shell_work_and_support_balance(case, work, root):
    deck, manifest = build_bundle("t", case, root=root)
    assert ("Root,1,6,0" in deck) == (root == "clamped")
    frd, dat = _synthetic_output(manifest)
    result = parse_outputs(manifest, frd, dat)
    assert result["action_work_j"] == pytest.approx({
        "plate_fy": 20., "web_fy": 30., "web_mx": 5.})
    assert result["loaded_case_work_j"] == pytest.approx(work)
    assert result["linear_half_work_j"] == pytest.approx(work/2)
    assert result["wrench_balance"]["force_n"] == pytest.approx([0., 0., 0.])
    if root == "hinged":
        assert result["wrench_balance"]["moment_nm_about_origin"] == pytest.approx([0., 0., 0.])
        assert result["support_wrench_complete"] is True
    else:
        assert result["wrench_balance"]["moment_nm_about_origin"] is None
        assert result["support_wrench_complete"] is False
    assert result["six_dof_b3_root_match"] is (root == "clamped")
    assert "not seam interface work" in result["interpretation"]


def test_parser_rejects_missing_face_reaction_or_changed_manifest():
    _, manifest = build_bundle("flat", "web_fy", root="hinged")
    frd, dat = _synthetic_output(manifest)
    with pytest.raises(ValueError, match="ambiguous expanded shell face pair"):
        parse_outputs(manifest, frd.replace(" -1      1000", " -2      1000", 1), dat)
    with pytest.raises(ValueError, match="incomplete support reaction"):
        parse_outputs(manifest, frd, dat.replace(" 1 ", " 999 ", 1))
    changed = deepcopy(manifest)
    changed["web_only_section"]["centroid_z_m"] = -.1
    with pytest.raises(ValueError, match="manifest identity"):
        parse_outputs(changed, frd, dat)


def test_default_deck_is_explicitly_clamped_but_rotational_rf_is_unavailable():
    deck, manifest = build_bundle()
    assert "*BOUNDARY\nRoot,1,6,0" in deck
    assert manifest["root"] == "clamped"
    assert manifest["six_dof_b3_root_match"] is True
    assert manifest["rotational_support_reaction_available"] is False
