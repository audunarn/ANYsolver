"""Fixed-load work remains valid when the coarse trace rows are dependent."""

import numpy as np

from scripts.b3_e4_f03_c1_material_line_plate_only import _plate_rows, _wrench
from scripts.b3_e4_f03_plate_patch_work import build_solid_plate
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


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
