"""Fixture construction only; no native assembly, nonlinear solve or spectra."""
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_fibre_arch_refinement as family
from test_ge_beam3_retained_fibre_control import arch


def test_two_macro_family_preserves_existing_geometry_and_section():
    old, new = arch(), family.model(2)
    assert tuple(old.mesh.nodes) == tuple(new.mesh.nodes)
    for node in old.mesh.nodes:
        np.testing.assert_array_equal(old.mesh.nodes[node].coords(), new.mesh.nodes[node].coords())
    for eid in old.mesh.elements:
        a, b = old.mesh.elements[eid], new.mesh.elements[eid]
        assert a.node_ids == b.node_ids
        assert a.operator.reference.fingerprint() == b.operator.reference.fingerprint()
        assert a.operator.cell.identity == b.operator.cell.identity


@pytest.mark.parametrize('count', [2, 4, 6])
def test_refinement_preserves_parabola_crown_and_physical_frame(count):
    made = family.model(count); program = family.program(count)
    assert len(made.mesh.nodes) == 2*count+1 and len(made.mesh.elements) == count
    assert 6*(2*count+1)+24*count <= 256
    assert program.control_node == count+1 and program.targets == family.TARGETS
    for element in made.mesh.elements.values():
        ref = element.operator.reference
        np.testing.assert_array_equal(ref.nodal_triads[:, :, 1], np.tile([0., 0., 1.], (3, 1)))
        for node in element.node_ids:
            x, y, z = made.mesh.nodes[node].coords()
            assert y == .1*(1-x*x) and z == 0.


@pytest.mark.parametrize('value', [True, 0, 1, 3, 8, 4.])
def test_unregistered_refinement_fails_before_import_or_solve(value):
    with pytest.raises(ValueError): family.model(value)
    with pytest.raises(ValueError): family.program(value)
