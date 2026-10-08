"""Headless work and deck checks; these tests never invoke CalculiX."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_b3_e4_ccx_3d_footprint_feasibility as base  # noqa: E402
import generate_b3_e4_ccx_3d_reciprocity_influences as influence  # noqa: E402


@pytest.mark.parametrize("group", ["shell", "beam"])
@pytest.mark.parametrize("component", range(6))
def test_signed_influence_decks_preserve_only_admitted_model(group, component):
    original = base.build_deck(1, "force_y")
    decks = [influence.build_influence_deck(group, component, sign*influence.DELTA)
             for sign in (-1,1)]
    assert len(set(decks)) == 2
    for sign, deck in zip((-1,1),decks):
        assert deck.count("*STEP\n") == 1
        assert deck.count("*EQUATION\n") == 12
        assert "*CLOAD" not in deck
        assert "*ELEMENT,TYPE=S4,ELSET=Panel" in deck
        assert "*ELEMENT,TYPE=B31,ELSET=Beam" in deck
        before, after = deck.split("*BOUNDARY\n", 1)
        assert "*STEP\n" in before
        assert "*BOUNDARY" not in before
        boundary, trailing = after.split("*NODE PRINT,NSET=AllNodes",1)
        rows = [row.split(",") for row in boundary.splitlines()]
        assert len(rows) == 36
        assert len({(int(row[0]),int(row[1])) for row in rows}) == 36
        assert all(row[1] == row[2] and len(row) == 4 for row in rows)
        assert all(np.isfinite(float(row[3])) for row in rows)
        assert all(len(row[3]) <= 20 and float(row[3][:20]) == float(row[3])
                   for row in rows)
        intended = influence.support_motion(group, component,
                                             sign*influence.DELTA)
        assert all(float(row[3]) == pytest.approx(
            intended[(int(row[0]),int(row[1]))], rel=0, abs=1e-16)
            for row in rows)
        # Remove the step support rows and restore the original model-level
        # homogeneous cards and force: every other line must be identical.
        restored = deck.replace("*STATIC\n*BOUNDARY\n"+boundary,
                                "*STATIC\n*CLOAD\n48,2,1000\n")
        restored = restored.replace("*MATERIAL,NAME=Isotropic",
                                    "*BOUNDARY\nPanelEnds,1,3\nBeamRoot,1,6\n*MATERIAL,NAME=Isotropic")
        assert restored == original
    minus = influence.support_motion(group,component,-influence.DELTA)
    plus = influence.support_motion(group,component,influence.DELTA)
    assert all(minus[dof] == -value for dof,value in plus.items())


def test_shell_rigid_work_basis_is_force_and_moment_about_origin():
    nodes = influence.support_coordinates()
    forces = {node: np.array((node*.13, -node*.31, node*.47))
              for node in influence.SHELL_SUPPORTS}
    total_force = sum(forces.values(),np.zeros(3))
    total_moment = sum((np.cross(nodes[node],force)
                        for node,force in forces.items()),np.zeros(3))
    for component in range(6):
        displacement = influence.support_motion("shell",component,influence.DELTA)
        work = sum(sum(force[k]*displacement[(node,k+1)] for k in range(3))
                   for node,force in forces.items())/influence.DELTA
        expected = (total_force if component < 3 else total_moment)[component % 3]
        assert work == pytest.approx(expected,abs=1e-10)


def test_beam_root_work_basis_and_global_origin_shift():
    root = influence.support_coordinates()[influence.BEAM_ROOT]
    force = np.array((7.,-11.,13.))
    moment = np.array((-17.,19.,-23.))
    for component in range(6):
        motion = influence.support_motion("beam",component,influence.DELTA)
        value = (force if component<3 else moment)[component%3]
        work = (sum(force[i]*motion[(influence.BEAM_ROOT,i+1)] for i in range(3))+
                sum(moment[i]*motion[(influence.BEAM_ROOT,i+4)] for i in range(3)))
        assert work/influence.DELTA == pytest.approx(value)
    assert np.cross(root,force)+moment == pytest.approx((-15.9,19.7,-23.))


def test_rejects_unfrozen_amplitudes_and_invalid_modes():
    with pytest.raises(ValueError, match="frozen"):
        influence.build_influence_deck("shell",0,2e-5)
    with pytest.raises(ValueError, match="group"):
        influence.case_name("other",0,influence.DELTA)
    assert len(f"{influence.DELTA:.17g}") > 20
    with pytest.raises(ValueError, match="20 characters"):
        influence.checked_boundary_token(f"{influence.DELTA:.17g}")
    assert influence.checked_boundary_token("1e-05") == "1e-05"
