"""Fixed-pose block preflight for a separately identified E4-PL bubble.

This extends the actual flat E4-PL stationary stress/strain spaces and its
compatible displacement by one mode each. It does not add a moving contact
geometry coordinate or alter the production shell/contact formulation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.e4_pl_element import (
    _coefficients, _compatible, _solve_stationary_system,
    _source_fields, _stationary_blocks,
)

from d1_cut_front_shell_work import build_patch
from d1_jump_stabilization_screen import _nodal_pressure


SOURCE_CELL_NODES = (2, 3, 8, 7)


def enriched_e4pl_bubble_block(element, model) -> tuple[np.ndarray, float, float]:
    """Return mixed E4-PL nodal/bubble blocks and production nodal parity."""
    hx, hy = 0.5, 1.0
    components = element.compute_stiffness_components(
        model.mesh, model.materials[element.material_name],
    )
    frame = np.asarray(components["frame"])
    if np.linalg.norm(frame-np.eye(3)) > 1.0e-12:
        raise AssertionError("preflight requires the aligned flat E4-PL cell")
    constitutive, _ = element._constitutive_and_drill_stiffness(
        model.materials[element.material_name], frame,
    )
    local = np.array(((-hx/2.0, -hy/2.0), (hx/2.0, -hy/2.0),
                      (hx/2.0, hy/2.0), (-hx/2.0, hy/2.0)))
    coefficients = _coefficients(local)
    original_stationary, original_coupling, _ = _stationary_blocks(
        local, coefficients, constitutive,
    )
    stationary = np.zeros((37, 37))
    stationary[:35, :35] = original_stationary
    coupling = np.zeros((25, 37))
    coupling[:24, :35] = original_coupling
    points, weights = np.polynomial.legendre.leggauss(3)
    for r, wr in zip(points, weights):
        for s, ws in zip(points, weights):
            bubble_r = -2.0*r*(1.0-s*s)
            bubble_s = -2.0*s*(1.0-r*r)
            bubble_strain = np.array((0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                      2.0*bubble_r/hx,
                                      2.0*bubble_s/hy))
            n_sigma, n_epsilon = _source_fields(coefficients, float(r), float(s))
            compatible = _compatible(local, coefficients, float(r), float(s))
            weight = wr*ws*coefficients["jc"]
            stationary[:14, 36] -= weight*(n_sigma.T@bubble_strain)
            stationary[36, :14] -= weight*(bubble_strain@n_sigma)
            stationary[35, 14:35] -= weight*(bubble_strain@n_epsilon)
            stationary[14:35, 35] -= weight*(n_epsilon.T@bubble_strain)
            modal_mass = weight*float(bubble_strain@bubble_strain)
            stationary[35, 36] -= modal_mass
            stationary[36, 35] -= modal_mass
            stationary[14:35, 36] += weight*(n_epsilon.T@constitutive@bubble_strain)
            stationary[36, 14:35] += weight*(bubble_strain@constitutive@n_epsilon)
            stationary[36, 36] += weight*(bubble_strain@constitutive@bubble_strain)
            local_coupling = weight*(bubble_strain@compatible)
            for node in range(4):
                coupling[6*node:6*node+5, 35] += local_coupling[5*node:5*node+5]
            coupling[24, :14] += weight*(n_sigma.T@bubble_strain)
            coupling[24, 35] += modal_mass
    solution, _ = _solve_stationary_system(stationary, coupling)
    core = -coupling@solution
    core = 0.5*(core+core.T)
    nodal_parity = float(np.linalg.norm(core[:24, :24]-components["core"])
                         / max(np.linalg.norm(components["core"]), 1.0e-30))
    if nodal_parity > 1.0e-10:
        raise AssertionError("new stationary block changes production nodal core")
    return core[:24, 24], float(core[24, 24]), nodal_parity


def screen(theta: float) -> dict:
    if not 0.0 < theta <= 0.1:
        raise ValueError("theta must lie in (0,.1]")
    model, definition, settings = build_patch(theta, touching=True)
    manager = GeneralS3PatchManager(model, definition, settings)
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    count = len(manager.law.pressure_mode_ids)
    state = linearize(manager, displacement, np.zeros(count), tangent=False)
    pressure_by_node = _nodal_pressure(theta)
    pressure = np.array(tuple(pressure_by_node[int(node)-1]
                              for node in manager.law.pressure_mode_ids))
    support = np.asarray(state.state.reference_support)
    if np.any(support[np.flatnonzero(pressure)] <= 0.0):
        raise AssertionError("pressure direction has unsupported hats")
    nodal_work = (support*pressure) @ state.gap_gradient
    source_x_coefficient = float(pressure_by_node[7]) / (
        -(theta**2/2.0-theta**3/3.0)
        /(0.25+theta-theta**2+theta**3/3.0)
    )
    beta = -(theta**2/2.0-theta**3/3.0)/(
        0.25+theta-theta**2+theta**3/3.0
    )
    bubble_force = source_x_coefficient*beta/36.0
    cross_local, bubble_stiffness, nodal_parity = enriched_e4pl_bubble_block(
        model.mesh.elements[2], model,
    )
    full_stiffness = assemble_stiffness_matrix(model)[0]
    _, _, transform, offset, _, _ = build_constraint_transformation(
        full_stiffness, np.zeros(displacement.size), model,
    )
    if np.linalg.norm(offset) != 0.0:
        raise AssertionError("unexpected constraint offset")
    reduced = (transform.T @ full_stiffness @ transform).tocsc()
    factor = splu(reduced)
    cross_full = np.zeros(displacement.size)
    for local_node, node in enumerate(SOURCE_CELL_NODES):
        dofs = model.mesh.dof_manager.get_node_dofs(node)
        cross_full[np.asarray(dofs)] += cross_local[6*local_node:6*local_node+6]
    cross_reduced = np.asarray(transform.T@cross_full).reshape(-1)
    work_reduced = np.asarray(nodal_work@transform).reshape(-1)
    schur = bubble_stiffness-float(cross_reduced@factor.solve(cross_reduced))
    bubble_residual = bubble_force-float(cross_reduced@factor.solve(work_reduced))
    if bubble_stiffness <= 0.0 or schur <= 0.0:
        raise AssertionError("derived enriched bubble has no positive energy")
    return {
        "status": "fixed-pose new mixed E4-PL block; contact bubble geometry absent",
        "theta": theta,
        "enriched_to_production_e4pl_nodal_core_relative": nodal_parity,
        "bubble_stiffness_n_per_m": bubble_stiffness,
        "condensed_bubble_stiffness_n_per_m": schur,
        "exact_bubble_contact_force_n": bubble_force,
        "condensed_bubble_contact_force_n": bubble_residual,
        "condensed_contact_force_over_theta_squared": bubble_residual/theta**2,
        "bubble_energy_dual_increment_j": bubble_residual**2/schur,
        "nodal_energy_dual_j": float(work_reduced@factor.solve(work_reduced)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theta", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    result = screen(args.theta)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"theta": result["theta"],
                      "nodal_parity": result["enriched_to_production_e4pl_nodal_core_relative"],
                      "schur": result["condensed_bubble_stiffness_n_per_m"],
                      "bubble_response": result["condensed_contact_force_over_theta_squared"]}))
