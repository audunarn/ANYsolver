"""Deck-level guards for the bounded external rigid-section discriminator."""

import numpy as np
import pytest

from scripts import b3_e4_f03_ccx_rigid_section_control as control
from scripts import b3_e4_f03_ccx_solid_bond_screen as solid


@pytest.mark.parametrize("factor", (2, 4))
def test_rigid_sections_preserve_full_bond_load_and_support(factor):
    deck, model = control.rigid_section_deck(factor)
    original, base = solid.build(
        factor, "tip_mx", boundary_policy="left_root", bond_policy="full",
        element_family="C3D20R", plate_thickness_mm=35,
        tip_load_map="quadratic_face")
    sections = model["rigid_section_control"]["sections"]
    assert len(sections) == 4 * factor
    assert [item["station_x_m"] for item in sections] == pytest.approx(
        [(i + 1) / (4 * factor) for i in range(4 * factor)])
    members = [node for section in sections for node in section["node_ids"]]
    assert len(members) == len(set(members))
    assert not set(members).intersection(model["boundary_node_ids"])
    assert set(map(int, model["applied_nodal_forces_N"])).issubset(
        sections[-1]["node_ids"])
    assert deck.count("*RIGID BODY,NSET=") == len(sections)
    assert deck.count("*ELEMENT,TYPE=C3D20R") == original.count(
        "*ELEMENT,TYPE=C3D20R") == 2
    assert deck.count("*MATERIAL,NAME=Isotropic") == 1
    assert model["bond_interval_m"] == base["bond_interval_m"] == [0., 1.]
    assert model["boundary_node_ids"] == base["boundary_node_ids"]
    assert model["applied_nodal_forces_N"] == base["applied_nodal_forces_N"]
    applied = {int(node): np.asarray(force) for node, force in
               model["applied_nodal_forces_N"].items()}
    assert solid._wrench(applied, model["probe_coordinates_m"]) == pytest.approx(
        [0., 0., 0., 100., 0., 0.], abs=1e-9)


def test_rigid_section_control_rejects_unregistered_factor():
    with pytest.raises(ValueError, match="factor must be 2 or 4"):
        control.rigid_section_deck(1)
