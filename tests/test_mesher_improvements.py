import numpy as np
import pytest
import anysolver.mesh_gen as mesh_gen
from anysolver.fe_core import FEModel
from anysolver.mesh_gen import (
    PanelGeometry,
    MeshConfig,
    generate_stiffened_panel_mesh,
    verify_mesh_quality,
    _locate_shell_element_at_xy,
    _generate_shell_mesh,
)

def test_fast_locate_shell_element():
    """Verify that O(1) fast lookup yields identical results to sequential fallback search."""
    panel = PanelGeometry(length=2.0, width=1.0, plate_thickness=0.01)
    config = MeshConfig(shell_num_divisions_x=10, shell_num_divisions_y=5, align_mesh_to_stiffeners=False)

    shell_nodes, shell_elements = _generate_shell_mesh(panel, config)

    # Define test points inside the panel
    test_points = [
        (0.25, 0.25),
        (1.0, 0.5),
        (1.95, 0.05),
        (0.01, 0.99),
        (0.0, 0.0),
        (2.0, 1.0),
    ]

    for x, y in test_points:
        # 1. Fast O(1) lookup (which runs automatically inside the function first)
        res_fast = _locate_shell_element_at_xy(x, y, shell_nodes, shell_elements, config.tolerance)

        # 2. Sequential fallback check (by manually running the sequential search loop)
        res_seq = None
        tol = max(float(config.tolerance), 1.0e-10)
        for node_ids, _thickness in shell_elements.values():
            corner_ids = node_ids[:4]
            corner_coords = np.asarray([shell_nodes[nid] for nid in corner_ids], dtype=float)
            xmin, xmax = float(np.min(corner_coords[:, 0])), float(np.max(corner_coords[:, 0]))
            ymin, ymax = float(np.min(corner_coords[:, 1])), float(np.max(corner_coords[:, 1]))
            if xmin - tol <= x <= xmax + tol and ymin - tol <= y <= ymax + tol:
                dx = xmax - xmin
                dy = ymax - ymin
                if dx > tol and dy > tol:
                    xi = 2.0 * (x - xmin) / dx - 1.0
                    eta = 2.0 * (y - ymin) / dy - 1.0
                    xi = float(np.clip(xi, -1.0, 1.0))
                    eta = float(np.clip(eta, -1.0, 1.0))
                    from anysolver.mesh_gen import _shape_functions_4node
                    weights = _shape_functions_4node(xi, eta)
                    shell_coords = np.asarray([shell_nodes[nid] for nid in node_ids], dtype=float)
                    shell_point = weights @ shell_coords
                    res_seq = (list(node_ids), weights, shell_point)
                    break

        # Verify both results match exactly
        assert res_fast is not None
        assert res_seq is not None
        assert res_fast[0] == res_seq[0]  # Same element node IDs
        assert np.allclose(res_fast[1], res_seq[1], atol=1e-7)  # Same shape weights
        assert np.allclose(res_fast[2], res_seq[2], atol=1e-7)  # Same coordinates on shell


def test_coupling_generation_builds_structured_index_once(monkeypatch) -> None:
    panel = PanelGeometry(
        length=4.0,
        width=2.0,
        plate_thickness=0.01,
        num_stiffeners=8,
        stiffener_spacing=0.2,
    )
    config = MeshConfig(
        shell_num_divisions_x=40,
        shell_num_divisions_y=20,
        beam_num_divisions=40,
        align_mesh_to_stiffeners=False,
    )
    calls = 0
    original = mesh_gen._build_structured_shell_grid_index

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(mesh_gen, "_build_structured_shell_grid_index", counted)
    model = generate_stiffened_panel_mesh(panel, config)
    assert model.mesh.num_elements > 800
    assert calls == 1


def test_stiffener_alignment():
    """Verify that shell grid lines align exactly with stiffeners when align_mesh_to_stiffeners=True."""
    panel = PanelGeometry(
        length=2.0,
        width=1.0,
        plate_thickness=0.01,
        num_stiffeners=2,
        stiffener_spacing=0.3,  # Stiffeners at y = 0.3 and y = 0.6
    )

    # 1. With alignment enabled
    config_aligned = MeshConfig(
        shell_num_divisions_x=4,
        shell_num_divisions_y=6,
        align_mesh_to_stiffeners=True,
    )
    model_aligned = generate_stiffened_panel_mesh(panel, config_aligned)

    # Extract unique Y coordinates of the shell nodes
    y_coords_aligned = sorted(list(set(node.y for node in model_aligned.mesh.nodes.values() if node.id < 10000)))

    # Verify that stiffener positions (0.3, 0.6) are present in the grid line coordinates
    assert any(np.isclose(y, 0.3, atol=1e-7) for y in y_coords_aligned)
    assert any(np.isclose(y, 0.6, atol=1e-7) for y in y_coords_aligned)

    # 2. With alignment disabled (standard uniform grid)
    config_uniform = MeshConfig(
        shell_num_divisions_x=4,
        shell_num_divisions_y=6,
        align_mesh_to_stiffeners=False,
    )
    model_uniform = generate_stiffened_panel_mesh(panel, config_uniform)
    y_coords_uniform = sorted(list(set(node.y for node in model_uniform.mesh.nodes.values() if node.id < 10000)))

    # Uniform division of 1.0 by 6 should place nodes at [0.0, 0.1667, 0.3333, 0.5, 0.6667, 0.8333, 1.0]
    # Verify that 0.3 is NOT exactly on this grid (it would be closer to 0.3333)
    assert not any(np.isclose(y, 0.3, atol=1e-5) for y in y_coords_uniform)

def test_mesh_quality_diagnostics():
    """Verify that verify_mesh_quality correctly evaluates mesh metrics and warns about distortion."""
    panel = PanelGeometry(length=2.0, width=1.0, plate_thickness=0.01)
    # Generate simple clean panel mesh
    from anysolver.mesh_gen import generate_simple_panel_mesh
    model = generate_simple_panel_mesh(length=2.0, width=1.0, thickness=0.01, num_divisions_x=4, num_divisions_y=4)

    metrics = verify_mesh_quality(model)
    assert metrics["num_shell_elements"] == 16
    assert metrics["max_aspect_ratio"] == 2.0  # (2.0/4)/(1.0/4) = 0.5/0.25 = 2.0
    assert metrics["max_warp"] == 0.0
    assert len(metrics["warnings"]) == 0

    # 1. Distort an element to trigger aspect ratio warning
    # We change node coordinates to make a very thin/stretched element
    node = model.mesh.get_node(6)  # A node of element 1
    # Move it extremely close to node 1 in x, but keep y
    node.x = 0.001

    metrics_distorted = verify_mesh_quality(model)
    assert metrics_distorted["max_aspect_ratio"] > 5.0
    assert any("High aspect ratio" in w for w in metrics_distorted["warnings"])

    # Restore node position
    node.x = 0.5

    # 2. Warp an element to trigger warpage warning
    # We move one corner of a shell element out of the plane (z != 0)
    node_out_of_plane = model.mesh.get_node(7)
    node_out_of_plane.z = 0.15

    metrics_warped = verify_mesh_quality(model)
    assert metrics_warped["max_warp"] > 0.05
    assert any("Significant element warp" in w for w in metrics_warped["warnings"])
