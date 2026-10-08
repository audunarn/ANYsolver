"""Focused geometry and work checks for the plate-only external comparison."""

import numpy as np
import pytest

from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_plate_patch_work import (
    build_solid_plate, expected_wrench, graded_patch_force,
    graded_torque_load_maps, local_grid,
    shell_patch_force, uniform_operator_parity,
)


def test_axial_only_sixteen_cell_grid_holds_transverse_cuts_and_dense_cap():
    xs, ys = local_grid(16, transverse_cells=4)
    assert 6*len(xs)*len(ys) == 1782
    assert np.count_nonzero((xs >= .9) & (xs <= 1.)) - 1 == 16
    assert np.count_nonzero((ys >= -.05) & (ys <= .05)) - 1 == 4
    with pytest.raises(ValueError, match="bounded local patch"):
        local_grid(16)


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


def test_half_thickness_plate_preserves_patch_wrench_and_operator_parity():
    deck,meta=build_solid_plate(1,"tip_mx",thickness=.035)
    assert meta["thickness_m"]==.035
    assert np.array(meta["applied_wrench_N_Nm"])==pytest.approx(
        expected_wrench("tip_mx"),abs=1e-8)
    assert all(abs(meta["coordinates_m"][str(i)][2]-.0175)<1e-12
               for i in meta["loaded_node_ids"])
    assert "ELSET=Stiffener" not in deck
    assert uniform_operator_parity(thickness=.035)["relative_tangent_error"]<1e-10


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
    coarse_x,coarse_y=local_grid(4)
    fine_x,fine_y=local_grid(4,outer_refined=True)
    assert len(fine_x)*len(fine_y)*6<=1800
    assert set(coarse_x).issubset(fine_x) and set(coarse_y).issubset(fine_y)
    assert sum(.9-1e-12<=x<1.-1e-12 for x in fine_x)==4
    assert sum(-.05-1e-12<=y<.05-1e-12 for y in fine_y)==4
    with pytest.raises(ValueError,match="outer refinement"):
        local_grid(8,outer_refined=True)


def test_same_wrench_torque_maps_have_distinct_physical_work_channels():
    xs,ys=local_grid(4)
    maps=graded_torque_load_maps(xs,ys)
    assert set(maps)=={"smooth_traction","native_distributing_director",
                       "native_rigid_corners"}
    smooth=maps["smooth_traction"].reshape(-1,6)
    distributing=maps["native_distributing_director"].reshape(-1,6)
    rigid=maps["native_rigid_corners"].reshape(-1,6)
    assert np.count_nonzero(distributing[:,3])>4
    assert np.count_nonzero(distributing[:,2])==0
    assert np.count_nonzero(rigid[:,2])==4
    assert np.count_nonzero(rigid[:,3:])==0
    assert np.count_nonzero(smooth[:,2])>4
    assert np.count_nonzero(smooth[:,3:])==0
    assert not np.shares_memory(maps["smooth_traction"],
                                maps["native_rigid_corners"])
    with pytest.raises(ValueError,match="patch boundaries"):
        graded_torque_load_maps(np.array((-.5,0.,1.5)),ys)
