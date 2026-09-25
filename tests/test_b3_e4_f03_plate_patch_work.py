"""Focused geometry and work checks for the plate-only external comparison."""

import numpy as np
import pytest

from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_plate_patch_work import (
    build_solid_plate, expected_wrench, graded_patch_force, local_grid,
    shell_patch_force, uniform_operator_parity,
)


@pytest.mark.parametrize("factor",(1,2))
@pytest.mark.parametrize("loading",("tip_mx","tip_fz"))
def test_quadratic_plate_deck_has_only_plate_and_exact_patch_wrench(factor,loading):
    deck,meta=build_solid_plate(factor,loading)
    assert "ELSET=Stiffener" not in deck
    assert "*CONTACT" not in deck
    assert deck.count("*ELEMENT,TYPE=C3D20R")==1
    assert meta["patch_faces"]==2*factor*factor
    assert meta["plate_elements"]>meta["patch_faces"]
    assert set(meta["loaded_node_ids"]).isdisjoint(meta["clamp_node_ids"])
    assert np.array(meta["applied_wrench_N_Nm"])==pytest.approx(
        expected_wrench(loading),abs=1e-8)
    assert all(meta["coordinates_m"][str(i)][0]==-.5
               for i in meta["clamp_node_ids"])
    assert all(.9-1e-12<=meta["coordinates_m"][str(i)][0]<=1.+1e-12
               and -.05-1e-12<=meta["coordinates_m"][str(i)][1]<=.05+1e-12
               and abs(meta["coordinates_m"][str(i)][2]-.035)<1e-12
               for i in meta["loaded_node_ids"])


@pytest.mark.parametrize("level",(2,4))
@pytest.mark.parametrize("loading",("tip_mx","tip_fz"))
def test_e4_patch_projection_has_same_global_wrench(level,loading):
    panel=make_shell(level,"Q4",n_y=level)
    force,wrench=shell_patch_force(panel,loading)
    assert len(force)==6*panel.node_count
    assert np.linalg.norm(force)>0
    assert wrench==pytest.approx(expected_wrench(loading),abs=1e-8)


def test_plate_patch_rejects_undeclared_inputs():
    with pytest.raises(ValueError,match="bounded quadratic"):
        build_solid_plate(3,"tip_mx")
    with pytest.raises(ValueError,match="bounded quadratic"):
        build_solid_plate(1,"pressure")


def test_local_patch_grid_resolves_both_directions_and_preserves_operator():
    assert uniform_operator_parity()["relative_tangent_error"]<1e-10
    for cells in (2,4,8):
        xs,ys=local_grid(cells)
        assert len(xs)*len(ys)*6<=1800
        assert sum(.9-1e-12<=x<1.-1e-12 for x in xs)==cells
        assert sum(-.05-1e-12<=y<.05-1e-12 for y in ys)==cells
        for loading in ("tip_mx","tip_fz"):
            force,wrench=graded_patch_force(xs,ys,loading)
            assert np.linalg.norm(force)>0
            assert wrench==pytest.approx(expected_wrench(loading),abs=1e-8)
