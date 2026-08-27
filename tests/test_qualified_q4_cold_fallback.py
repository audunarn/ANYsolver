"""Regression coverage for ineligible qualified-Q4 cold-plan records."""

from __future__ import annotations

import numpy as np

from anysolver import FEModel, QualifiedE4PLShellElement
from anysolver.matrix_assembly import assemble_stiffness_matrix


def _angled_q4_model(count: int = 64) -> FEModel:
    model = FEModel("qualified-q4-cold-fallback")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    node_id = 1
    for element_id in range(1, count + 1):
        offset = float(2 * element_id)
        node_ids: list[int] = []
        for x, y in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
            model.add_node(node_id, offset + x, y, 0.0)
            node_ids.append(node_id)
            node_id += 1
        model.add_element(
            element_id,
            QualifiedE4PLShellElement(
                element_id,
                node_ids,
                "steel",
                thickness=0.05,
                material_angle_deg=17.0,
            ),
        )
    return model


def _prewarm_element_caches(model: FEModel) -> None:
    for element in model.mesh.elements.values():
        element.compute_stiffness_matrix(
            model.mesh,
            model.materials[element.material_name],
        )


def test_ineligible_cold_record_uses_guarded_q4_fallback_exactly() -> None:
    cold_model = _angled_q4_model()
    warm_model = _angled_q4_model()
    _prewarm_element_caches(warm_model)

    cold, cold_info = assemble_stiffness_matrix(cold_model)
    warm, _warm_info = assemble_stiffness_matrix(warm_model)

    diagnostic = cold_info["diagnostics"]["qualified_e4_pl_stiffness"]
    assert diagnostic["path"] == "shared_geometry_cache"
    assert "trusted_cold_element_count" not in diagnostic
    assert all(
        element._qualified_components is not None
        for element in cold_model.mesh.elements.values()
    )

    difference = (cold - warm).tocsr()
    difference.eliminate_zeros()
    assert difference.nnz == 0
    np.testing.assert_array_equal(cold.indptr, warm.indptr)
    np.testing.assert_array_equal(cold.indices, warm.indices)
    np.testing.assert_array_equal(cold.data, warm.data)
