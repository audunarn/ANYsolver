"""Fixed-load work remains valid when the coarse trace rows are dependent."""

import numpy as np

from scripts.b3_e4_f03_c1_material_line_plate_only import _plate_rows, _wrench
from scripts.b3_e4_f03_c1_material_line_action_shape import _project_solid_trace_work
from scripts.b3_e4_f03_plate_patch_work import build_solid_plate
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def test_fixed_line_dual_preserves_wrench_and_work_on_both_solid_meshes(tmp_path):
    dual = np.array((4., -6., 8., 100., -70., 30.) * 4)
    wrenches = []
    ranks = []
    for factor in (2, 4):
        deck, _ = build_solid_plate(factor, "tip_mx", thickness=.035)
        source = tmp_path / f"plate-{factor}.inp"
        source.write_text(deck)
        coords = _read_deck_nodes(source)
        nodes, rows = _plate_rows(coords, factor)
        ranks.append(np.linalg.matrix_rank(rows, tol=1e-10))
        force = -(rows.T@dual).reshape(-1, 3)
        field = np.array([[.01*np.sin(node), .02*np.cos(node),
                           .005*np.sin(2*node)] for node in nodes])
        np.testing.assert_allclose(np.sum(force*field),
                                   -dual@(rows@field.ravel()), atol=2e-12)
        wrenches.append(_wrench(coords, nodes, force))
    assert ranks == [21, 24]
    np.testing.assert_allclose(wrenches[0], wrenches[1], atol=2e-10)


def test_global_trace_projection_preserves_representable_q4_work(tmp_path):
    deck, _ = build_solid_plate(4, "tip_mx", thickness=.035)
    source = tmp_path / "plate-4.inp"
    source.write_text(deck)
    coords = _read_deck_nodes(source)
    nodes, solid_rows = _plate_rows(coords, 4)
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    native_rows, measure = _rows(
        line, LineMultiplierSpace("piecewise_constant",
                                   tuple(np.linspace(0., 1., 5))))
    q = np.random.default_rng(917).normal(scale=1e-4,
                                           size=(line.shell_count, 6))
    solid_u = []
    for node in nodes:
        xyz = coords[node]
        support, shape = structured_q4_point_shape(xs, ys, xyz[0], xyz[1])
        solid_u.append(sum(
            (weight*(q[int(i), :3] +
                     np.cross(q[int(i), 3:], (0., 0., xyz[2]))))
            for i, weight in zip(support, shape)))
    part = np.tile((1., 2., 3., 4., 5., 6.), 4)
    unit = np.zeros((24, 3*len(nodes)))
    unit[0] = -np.asarray(solid_u).ravel()
    result = _project_solid_trace_work(
        part, coords=coords, solid_nodes=nodes,
        plate_selector=np.ones(3*len(nodes), dtype=bool),
        solid_rows=solid_rows, scale=np.ones(24), unit=unit,
        native_rows=native_rows, measure=measure,
        shell_size=6*line.shell_count, xs=xs, ys=ys, thickness=.035)
    np.testing.assert_allclose(result["unrepresented_trace_work_J"],
                               0., atol=2e-11)
