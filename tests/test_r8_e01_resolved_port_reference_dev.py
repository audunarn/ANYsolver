"""Source-only geometry and work controls for the inert E01 solid-port deck."""
from math import isclose

import numpy as np
import pytest

from scripts.r8_e01_resolved_port_reference_dev import EDGES, build, generate


def _nodes_and_elements(deck):
    lines = deck.splitlines()
    nodes, elements = {}, {}
    section = None
    current = None
    for line in lines:
        if line.startswith("*NODE") and not line.startswith("*NODE PRINT") and not line.startswith("*NODE FILE"):
            section = "nodes"
            continue
        if line.startswith("*ELEMENT"):
            section = "elements"
            continue
        if line.startswith("*"):
            section = None
            continue
        if section == "nodes":
            row = line.split(",")
            nodes[int(row[0])] = np.array([float(v) for v in row[1:]])
        elif section == "elements":
            row = [int(v) for v in line.split(",")]
            if current is None:
                assert len(row) == 16
                current = row
            else:
                assert len(row) == 5
                current += row
                elements[current[0]] = current[1:]
                current = None
    assert current is None
    return nodes, elements


def _equations(deck):
    lines = deck.splitlines()
    rows = []
    for index, line in enumerate(lines):
        if line != "*EQUATION":
            continue
        count = int(lines[index+1])
        parts = lines[index+2].split(",")
        assert len(parts) == 3*count
        rows.append([(int(parts[3*i]), int(parts[3*i+1]),
                      float(parts[3*i+2])) for i in range(count)])
    return rows


def _named_rows(deck, keyword):
    blocks = {}
    name = None
    for line in deck.splitlines():
        if line.startswith(keyword):
            name = line[len(keyword):].split(",", 1)[0]
            blocks[name] = []
        elif line.startswith("*"):
            name = None
        elif name is not None:
            blocks[name].append(line)
    return blocks


@pytest.mark.parametrize("sign", (1, -1))
@pytest.mark.parametrize("load", ("fy", "mx"))
def test_resolved_port_geometry_rows_and_rigid_work(sign, load):
    deck, info = build(sign, load)
    nodes, elements = _nodes_and_elements(deck)
    rows = _equations(deck)
    plate_xyz = np.array([nodes[n] for n in range(1, info["plate_nodes"]+1)])
    beam_xyz = np.array([nodes[n] for n in range(info["plate_nodes"]+1,
                                                 info["plate_nodes"]+info["beam_nodes"]+1)])
    np.testing.assert_allclose((plate_xyz.min(axis=0), plate_xyz.max(axis=0)),
                               ((0., -.5, -.035), (2., .5, .035)))
    np.testing.assert_allclose((beam_xyz.min(axis=0), beam_xyz.max(axis=0)),
                               ((0., -.55, .05 if sign == 1 else -.15),
                                (2., -.45, .15 if sign == 1 else -.05)))
    assert len(rows) == info["equation_count"] == 18
    assert len(elements) == info["plate_elements"]+info["beam_elements"] == 168
    assert info["port_patch_sizes"] == [(13, 21)]*3
    assert deck.count("*RIGID BODY") == 6
    assert deck.count("*SECTION PRINT") == 8
    nsets = {name: {int(n) for line in lines for n in line.split(",")}
             for name, lines in _named_rows(deck, "*NSET,NSET=").items()}
    root = {n for n, xyz in nodes.items() if xyz[0] == 0 and n <= info["plate_nodes"]}
    assert nsets["PlateRootFree"].isdisjoint(nsets["ShellPort0"])
    assert nsets["PlateRootFree"] | nsets["ShellPort0"] & root == root
    assert len(nsets["PlateRootFree"]) == info["root_free_nodes"]
    root_ref, root_rot = info["port_reference_nodes"]["shell_0"]
    for condition in ("PlateRootFree,1,3", f"{root_ref},1,3", f"{root_rot},1,3"):
        assert condition in deck.splitlines()
    for station, bounds in ((0, (0., .025)), (1000, (.975, 1.)),
                            (2000, (1.975, 2.))):
        patch = np.array([nodes[n] for n in nsets[f"ShellPort{station}"]])
        np.testing.assert_allclose((patch[:, 0].min(), patch[:, 0].max()), bounds)
        np.testing.assert_allclose(patch[:, 1], -.5)
        np.testing.assert_allclose((patch[:, 2].min(), patch[:, 2].max()),
                                   (-.035, .035))
    surfaces = _named_rows(deck, "*SURFACE,NAME=")
    assert set(surfaces) == set(info["cut_surfaces"])
    for name, lines in surfaces.items():
        side = "Plate" if name.startswith("Plate") else "Beam"
        expected_area = .07 if side == "Plate" else .01
        direction = "Left" if "Left" in name else "Right"
        station = int(name[len(side):].split(direction, 1)[0])
        face = "S4" if direction == "Left" else "S6"
        expected_count = 10 if side == "Plate" else 4
        assert len(lines) == info["cut_surfaces"][name]["count"] == expected_count
        assert info["cut_surfaces"][name]["face"] == face
        area = 0.
        rectangles = set()
        for line in lines:
            element_id, face_id = line.split(",")
            assert face_id == face
            cell = np.array([nodes[n] for n in elements[int(element_id)][:8]])
            face_points = cell[[1, 2, 6, 5] if face == "S4" else [0, 3, 7, 4]]
            np.testing.assert_allclose(face_points[:, 0], station/1000.)
            assert np.sign(face_points[:, 0].mean()-cell[:, 0].mean()) == (
                1 if face == "S4" else -1)
            rect = (face_points[:, 1].min(), face_points[:, 1].max(),
                    face_points[:, 2].min(), face_points[:, 2].max())
            assert rect not in rectangles
            rectangles.add(rect)
            area += (rect[1]-rect[0])*(rect[3]-rect[2])
        assert isclose(area, expected_area, rel_tol=0., abs_tol=1e-15)
    for cell in elements.values():
        xyz = np.array([nodes[n] for n in cell])
        assert xyz[1, 0] > xyz[0, 0]
        assert xyz[3, 1] > xyz[0, 1]
        assert xyz[4, 2] > xyz[0, 2]
        for mid, (a, b) in enumerate(EDGES, 8):
            np.testing.assert_allclose(xyz[mid], .5*(xyz[a]+xyz[b]),
                                       rtol=0., atol=1e-15)

    # Every independent reference port follows the same finite rigid motion.
    translation = np.array((.031, -.021, .013))
    rotation = np.array((.007, -.009, .005))
    values = {}
    for side in ("shell", "beam"):
        for station in (0, 1000, 2000):
            ref, rot = info["port_reference_nodes"][f"{side}_{station}"]
            values[ref] = translation+np.cross(rotation, nodes[ref])
            values[rot] = rotation
    residual = [sum(coef*values[node][dof-1] for node, dof, coef in row)
                for row in rows]
    assert max(map(abs, residual)) < 2e-15

    force = np.asarray(info["applied_force_n"])
    moment = np.asarray(info["applied_moment_nm"])
    arm = np.array((0., 0., sign*.1))
    expected_moment = moment+np.cross(arm, force)
    np.testing.assert_allclose(info["shell_tip_wrench_from_beam"][0],
                               force, rtol=0., atol=1e-13)
    np.testing.assert_allclose(info["shell_tip_wrench_from_beam"][1],
                               expected_moment, rtol=0., atol=1e-13)
    beam_virtual = force@(translation+np.cross(rotation, arm))+moment@rotation
    shell_virtual = force@translation+expected_moment@rotation
    assert isclose(beam_virtual, shell_virtual, rel_tol=0., abs_tol=2e-13)
    if load == "fy":
        assert expected_moment[0] == -sign*100.
    else:
        assert expected_moment[0] == 100.


def test_resolved_port_generation_preserves_all_cases_and_rejects_reuse(tmp_path):
    output = tmp_path/"reference"
    manifest = generate(output)
    assert manifest["status"] == "NOT_EXECUTED_NOT_QUALIFIED"
    assert {(case["model"]["sign"], case["model"]["load"])
            for case in manifest["cases"]} == {
                (1, "fy"), (1, "mx"), (-1, "fy"), (-1, "mx")}
    assert len(list(output.glob("*.inp"))) == 4
    with pytest.raises(FileExistsError, match="preserve"):
        generate(output)
    with pytest.raises(ValueError, match="offset sign"):
        build(0, "fy")
    with pytest.raises(ValueError, match="Fy or Mx"):
        build(1, "fx")
