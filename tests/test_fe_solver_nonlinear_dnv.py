"""DNV-RP-C208-oriented nonlinear solver additions."""

from __future__ import annotations

import numpy as np
import pytest

from anysolver.boundary import BoundaryCondition, FixedSupport, LoadCase
from anysolver.buckling import BucklingMode, BucklingResult
from anysolver.elements import BeamElement
from anysolver.fe_core import FEModel
from anysolver.imperfections import (
    ImperfectionField,
    apply_imperfection,
    imperfection_from_buckling_mode,
    standard_member_bow,
    standard_plate_mode,
)
from anysolver.material_curves import (
    DNVC208MaterialCurve,
    FiberSectionPlasticityConfig,
    dnv_c208_steel_curve,
)
from anysolver.nonlinear_static import (
    DisplacementControl,
    NonlinearLoadProgram,
    NonlinearLoadStage,
    solve_static_nonlinear,
)


E = 210.0e9
NU = 0.3

EPP_CURVE = DNVC208MaterialCurve(
    sigma_prop=354.0e6,
    sigma_yield=355.0e6,
    sigma_yield_2=355.5e6,
    eps_p_y1=0.004,
    eps_p_y2=0.1,
    K=400.0e6,
    n=0.2,
)


def _guided_beam_model(curve=None, fiber=False) -> FEModel:
    model = FEModel(name="guided_beam")
    model.add_material("steel", E, NU, hardening_curve=curve)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    section = {"area": 0.01, "Iy": 1.0e-5, "Iz": 1.0e-5, "J": 1.0e-5}
    if fiber:
        section["fiber_plasticity"] = FiberSectionPlasticityConfig(5, 5)
    model.add_element(1, BeamElement(1, [1, 2], "steel", section))
    model.add_boundary_condition(FixedSupport("fixed", [1]))
    model.add_boundary_condition(
        BoundaryCondition("guide", [2], {"uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0})
    )
    return model


def test_dnv_c208_steel_curve_factory_matches_low_fractile_tables():
    s355 = dnv_c208_steel_curve("S355", 0.010)
    assert s355.sigma_prop == pytest.approx(320.0e6)
    assert s355.sigma_yield == pytest.approx(357.0e6)
    assert s355.sigma_yield_2 == pytest.approx(363.3e6)
    assert s355.eps_p_y1 == pytest.approx(0.004)
    assert s355.eps_p_y2 == pytest.approx(0.015)
    assert s355.K == pytest.approx(740.0e6)
    assert s355.n == pytest.approx(0.166)

    s420 = dnv_c208_steel_curve("S420", 0.020)
    assert s420.sigma_prop == pytest.approx(360.6e6)
    assert s420.sigma_yield == pytest.approx(402.4e6)
    assert s420.sigma_yield_2 == pytest.approx(407.3e6)
    assert s420.eps_p_y2 == pytest.approx(0.012)
    assert s420.K == pytest.approx(703.0e6)
    assert s420.n == pytest.approx(0.14)

    s460 = dnv_c208_steel_curve("S460", 0.050)
    assert s460.sigma_prop == pytest.approx(374.2e6)
    assert s460.sigma_yield == pytest.approx(417.5e6)
    assert s460.sigma_yield_2 == pytest.approx(421.2e6)

    with pytest.raises(NotImplementedError):
        dnv_c208_steel_curve("S355", 0.010, fractile="mean")


def test_eigenmode_imperfection_scales_to_requested_amplitude():
    model = FEModel(name="mode_scale")
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    shape = np.zeros(model.mesh.dof_manager.total_dofs)
    shape[model.mesh.get_node(2).dofs[2]] = 2.0
    result = BucklingResult(
        modes=[BucklingMode(1, 10.0, 10.0, shape, shape.copy(), 1.0, 0.1)],
        num_modes_requested=1,
        solver_status="ok",
        constraint_info={},
        assembly_info={},
    )

    field = imperfection_from_buckling_mode(model, result, 1, amplitude=0.03)
    assert field.max_offset == pytest.approx(0.03)
    assert field.as_arrays()[2][2] == pytest.approx(0.03)


def test_standard_imperfections_and_stress_free_reference_geometry():
    model = FEModel(name="imperfection")
    model.add_material("steel", E, NU)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.5, 0.0, 0.0)
    model.add_node(3, 3.0, 0.0, 0.0)
    model.add_element(1, BeamElement(1, [1, 3], "steel", {"area": 0.01, "Iy": 1.0e-5, "Iz": 1.0e-5, "J": 1.0e-5}))

    bow = standard_member_bow(model, [1, 2, 3])
    assert bow.max_offset == pytest.approx(3.0 / 300.0)
    assert np.linalg.norm(bow.as_arrays()[1]) == pytest.approx(0.0)
    assert np.linalg.norm(bow.as_arrays()[3]) == pytest.approx(0.0)

    imperfect = apply_imperfection(model, ImperfectionField({3: (0.0, 0.0, 0.02)}), copy_model=True)
    assert model.mesh.get_node(3).z == pytest.approx(0.0)
    assert imperfect.mesh.get_node(3).z == pytest.approx(0.02)
    element = imperfect.mesh.get_element(1)
    f_int, _, _ = element.compute_nonlinear_response(
        imperfect.mesh,
        imperfect.get_material("steel"),
        np.zeros(element.total_dofs),
        tangent=False,
    )
    assert np.linalg.norm(f_int) == pytest.approx(0.0, abs=1.0e-9)


def test_standard_plate_mode_default_s_over_200():
    model = FEModel(name="plate_mode")
    nid = {}
    k = 1
    for j in range(3):
        for i in range(3):
            model.add_node(k, 0.5 * i, 0.5 * j, 0.0)
            nid[(i, j)] = k
            k += 1
    field = standard_plate_mode(model, list(nid.values()))
    offsets = field.as_arrays()
    assert field.max_offset == pytest.approx(1.0 / 200.0)
    assert offsets[nid[(1, 1)]][2] == pytest.approx(1.0 / 200.0)
    assert np.linalg.norm(offsets[nid[(0, 0)]]) == pytest.approx(0.0)


def test_beam_fiber_plasticity_reaches_axial_yield():
    model = _guided_beam_model(curve=EPP_CURVE, fiber=True)
    element = model.mesh.get_element(1)
    u_elem = np.zeros(element.total_dofs)
    u_elem[6] = 0.008

    f_int, k_tan, state = element.compute_nonlinear_response(
        model.mesh, model.get_material("steel"), u_elem, tangent=True
    )
    assert k_tan.shape == (12, 12)
    assert state["alpha"].max() > 0.0
    assert state["axial_force"] == pytest.approx(np.mean(state["fiber_stress"]) * 0.01)
    assert state["axial_force"] == pytest.approx(355.0e6 * 0.01, rel=0.08)
    assert f_int[6] == pytest.approx(state["axial_force"], rel=1.0e-8)


def test_displacement_control_reports_peak_load_and_strain_history():
    model = _guided_beam_model(curve=EPP_CURVE, fiber=True)
    load = LoadCase(name="unit_pull")
    load.add_nodal_load(2, load_vector=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    result = solve_static_nonlinear(
        model,
        load_case=load,
        control="displacement",
        displacement_control=DisplacementControl(node_id=2, dof="ux", target_displacement=0.004),
        num_steps=4,
        max_iterations=30,
    )

    assert result.status == "completed"
    assert result.steps[-1].control_value == pytest.approx(0.004)
    assert result.peak_load_factor > 0.0
    assert result.last_converged_load_factor == pytest.approx(result.load_factor)
    assert result.info["force_displacement_history"][-1]["control_value"] == pytest.approx(0.004)
    assert result.info["strain_summary"]["max_equivalent_plastic_strain"] > 0.0


def test_nonlinear_load_program_applies_ordered_stages_to_completion():
    model = _guided_beam_model()
    permanent = LoadCase(name="permanent")
    permanent.add_nodal_load(2, load_vector=[1000.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    environmental = LoadCase(name="environmental")
    environmental.add_nodal_load(2, load_vector=[2000.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    program = NonlinearLoadProgram(
        [
            NonlinearLoadStage("permanent", permanent),
            NonlinearLoadStage("environmental", environmental),
        ]
    )

    result = solve_static_nonlinear(model, load_program=program, num_steps=4)

    assert result.status == "completed"
    assert result.load_factor == pytest.approx(2.0)
    assert result.info["load_program_stage_factors"] == {
        "permanent": pytest.approx(1.0),
        "environmental": pytest.approx(1.0),
    }
    assert {entry["active_stage"] for entry in result.info["force_displacement_history"]} == {
        "permanent",
        "environmental",
    }
