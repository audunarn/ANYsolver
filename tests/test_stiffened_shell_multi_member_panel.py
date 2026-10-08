"""End-to-end sparse development checks above the inherited consumer cap."""
import json
import numpy as np

from scripts.experimental_stiffened_ge_multi_member_panel import actions_for, make_definition, run


def test_connected_four_stiffener_reference_route(tmp_path):
    result = run(8, 4)
    (tmp_path/"panel-screen.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert result["status"] == "completed"
    assert result["beam_elements"] == 32
    assert result["shell_elements"] == 24
    assert result["preflight"]["constraints"] > 48
    assert result["preflight"]["reference_linear_factorizations"] == 1
    assert not result["production_qualified"]


def test_fixture_reference_axis_and_identity_are_explicit():
    definition = make_definition(2, 3)
    assert len({beam.sha256 for beam in definition.beams}) == 6
    shell_nodes = dict(zip(definition.shell.node_ids, definition.shell.coordinates_m))
    beam_nodes = {}
    for beam in definition.beams:
        element, _ = beam.instantiate()
        beam_nodes.update(zip(element.node_ids, element.operator.reference.coordinates))
    for point in definition.points:
        np.testing.assert_allclose(beam_nodes[point.beam_node]-shell_nodes[point.shell_node],
                                   (0., 0., .03), rtol=0., atol=1e-16)
    # Shell cells share complete edges; no coincident-coordinate auto-merging.
    assert len(definition.shell.node_ids) == 9
    assert len(beam_nodes) == 15


def test_independent_shell_resolution_and_sparse_point_layout():
    definition = make_definition(4, 3, shell_transverse_cells=5, tie_stride=2)
    assert len(definition.shell.q4_elements) == 20
    assert len(definition.beams) == 12
    assert len(definition.fixed) == 36  # Entire six-node clamped edge.
    assert len(definition.points) == 9
    assert len(actions_for(definition)) == 3
    shell_nodes = dict(zip(definition.shell.node_ids, definition.shell.coordinates_m))
    beam_nodes = {}
    for beam in definition.beams:
        element, _ = beam.instantiate()
        beam_nodes.update(zip(element.node_ids, element.operator.reference.coordinates))
    for point in definition.points:
        np.testing.assert_allclose(beam_nodes[point.beam_node]-shell_nodes[point.shell_node],
                                   (0.,0.,.03), rtol=0., atol=1e-16)
    assert len({beam_nodes[action.node][1] for action in actions_for(definition)}) == 3
    assert all(fixed.component in range(6) and shell_nodes[fixed.node][0] == 0.
               for fixed in definition.fixed)
