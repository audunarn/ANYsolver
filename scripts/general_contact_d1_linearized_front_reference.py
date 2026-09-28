"""Fixed-geometry linear Q4/S3 strip obstacle discriminator.

The elastic tangent comes from the admitted Q4 structure at its undeformed
pose. Contact integration, nodal pressure constraints and the bound-constrained
quadratic solve are independent of the general-contact kernel. This is a
development comparator, not an independent shell-mechanics oracle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.sparse.linalg import splu

from anysolver import BoundaryCondition, create_shell_element
from anysolver.assembly import build_constraint_transformation
from anysolver.fe_core import FEModel
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_pressure_field_compare import _squared_norm


def _planar_q1_matrix(columns: int) -> tuple[np.ndarray, np.ndarray]:
    """Integrate source Q1 products over x∈[0.1,1.1], y∈[0.1,1]."""
    stride = columns + 1
    mx = np.zeros((stride, stride))
    local = np.array(((2.0, 1.0), (1.0, 2.0))) / (6.0*columns)
    for cell in range(columns):
        mx[cell:cell+2, cell:cell+2] += local
    # eta=y-0.1 on [0,0.9]; shape functions are (1-eta,eta).
    my = np.array(((0.333, 0.162), (0.162, 0.243)))
    mass = np.kron(my, mx)
    support = mass @ np.ones(2*stride)
    if (np.min(support) <= 0.0 or
            abs(np.sum(support)-0.9) > 1.0e-13):
        raise AssertionError("independent Q1 overlap integration is invalid")
    return mass, support


def _nonnegative_quadratic(hessian: np.ndarray, linear: np.ndarray,
                           support: np.ndarray) -> np.ndarray:
    """Solve the pressure LCP with bounded optimization and certify KKT."""
    scale = float(np.max(np.diag(hessian)))
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("linearized pressure compliance is invalid")
    h = hessian/scale
    c = linear/scale
    result = minimize(
        lambda p: (0.5*float(p @ h @ p) + float(c @ p), h @ p+c),
        np.zeros(len(c)), jac=True, method="L-BFGS-B",
        bounds=[(0.0, None)]*len(c),
        options={"maxiter": 10000, "ftol": 1.0e-16,
                 "gtol": 1.0e-15, "maxls": 100},
    )
    pressure = result.x
    weighted_gap = linear+hessian @ pressure
    gap = weighted_gap/support
    complementarity = np.max(np.abs(pressure*gap))
    if (not result.success or np.min(pressure) < -1.0e-10
            or np.min(gap) < -1.0e-10
            or complementarity > 1.0e-10):
        raise RuntimeError(
            f"linearized pressure solve failed: {result.message}; "
            f"minimum gap={np.min(gap):.4g} m, "
            f"complementarity={complementarity:.4g} Pa m"
        )
    return pressure


def _source_model(columns: int) -> FEModel:
    """Reproduce only the deformable strip; the saved target is fully fixed."""
    if columns < 16 or columns > 128 or columns % 8:
        raise ValueError("bounded linearized source requires 16..128 Q4 columns in multiples of 8")
    model = FEModel(f"linearized_front_source_{columns}q4")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    stride = columns+1
    for row, y in enumerate((0.1, 1.1)):
        for column in range(stride):
            model.add_node(1+row*stride+column,
                           0.1+column/columns, y, 0.04004)
    for column in range(columns):
        element_id = column+1
        model.add_element(element_id, create_shell_element(
            element_id,
            (1+column, 2+column, stride+2+column, stride+1+column),
            "elastic", thickness=0.05,
            reference_normal=(0.0, 0.0, 1.0),
        ))
    source_nodes = tuple(range(1, 2*stride+1))
    model.add_boundary_condition(BoundaryCondition(
        "source_guide", source_nodes,
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_left_support", (1, stride+1), {"uz": 0.0},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_horizontal_path_anchor", (1, stride+1), {"ux": 0.0},
    ))
    return model


def _linearized_case(columns: int) -> dict:
    model = _source_model(columns)
    stride = columns+1
    model.apply_boundary_conditions()
    size = model.mesh.dof_manager.total_dofs
    zero = np.zeros(size)
    reference_force, stiffness, _trial = _assemble_nonlinear_system(
        model, zero, {}, 3, tangent=True, kinematics="von_karman",
    )
    if np.linalg.norm(reference_force) > 1.0e-8:
        raise ValueError("reference structural state is not stress free")
    load = np.zeros(size)
    source_z = []
    for row in range(2):
        for column in range(stride):
            node = 1+row*stride+column
            dof = model.mesh.dof_manager.get_node_dofs(node)[2]
            source_z.append(dof)
            weight = (0.5 if column in (0, columns) else 1.0)/(2*columns)
            load[dof] = -0.3*weight
    if abs(np.sum(load)+0.3) > 1.0e-14:
        raise AssertionError("independent distributed load is invalid")
    reduced_k, reduced_load, transform, offset, _, _ = (
        build_constraint_transformation(stiffness, load, model)
    )
    if np.linalg.norm(offset) > 0.0:
        raise ValueError("linearized reference requires zero prescribed pose")
    mass, support = _planar_q1_matrix(columns)
    work = sparse.lil_matrix((2*stride, size))
    for i, dof in enumerate(source_z):
        work[:, dof] = mass[:, i].reshape(-1, 1)
    reduced_work = (work.tocsr() @ transform).toarray()
    factor = splu(reduced_k.tocsc())
    free_q = factor.solve(reduced_load)
    response = factor.solve(reduced_work.T)
    compliance = reduced_work @ response
    asymmetry = float(np.max(np.abs(compliance-compliance.T)))
    compliance = 0.5*(compliance+compliance.T)
    initial_gap = 4.0e-5
    weighted_free_gap = support*initial_gap+reduced_work @ free_q
    pressure = _nonnegative_quadratic(
        compliance, weighted_free_gap, support,
    )
    q = free_q+response @ pressure
    gap = (support*initial_gap+reduced_work @ q)/support
    residual = reduced_k @ q-reduced_load-reduced_work.T @ pressure
    if np.linalg.norm(residual) > 1.0e-7:
        raise RuntimeError("linearized structural equilibrium is invalid")
    return {
        "columns": columns,
        "pressure": pressure.reshape(2, stride),
        "supported_modes": len(pressure),
        "active_modes": int(np.count_nonzero(pressure > 1.0e-8)),
        "first_active_reference_x": float(
            np.flatnonzero(pressure.reshape(2, stride)[0] > 1.0e-8)[0]
            / columns
        ),
        "maximum_pressure_pa": float(np.max(pressure)),
        "minimum_weighted_gap_m": float(np.min(gap)),
        "maximum_active_weighted_gap_m": float(
            np.max(np.abs(gap[pressure > 1.0e-8]))
        ),
        "integrated_force_n": float(support @ pressure),
        "reduced_equilibrium_residual_n": float(np.linalg.norm(residual)),
        "pressure_compliance_asymmetry": asymmetry,
    }


def _saved_pressure(path: Path, columns: int, step: int) -> np.ndarray:
    report = json.loads(path.read_text(encoding="utf-8"))
    if (report["columns"] != columns or report["status"] != "completed"
            or report["load_profile"] != "distributed"
            or report["total_downward_force_n"] != 0.3
            or report["target_right_x_m"] != 1.3
            or report.get("target_columns", 1) != 1
            or report.get("target_reference_slope", 0.0) != 0.0
            or report.get("pressure_basis", "fine_nodal_q1") != "fine_nodal_q1"
            or report["steps_per_segment"] != (2 if columns == 16 else 3)
            or report["history"][step]["step_index"]
            != report["steps_per_segment"]):
        raise ValueError(f"saved coupled report differs from reference: {path}")
    contact = report["history"][step]["contact"]
    if contact["source_pressure_node_ids"] != list(range(1, 2*columns+3)):
        raise ValueError(f"saved pressure identity differs from source: {path}")
    return np.asarray(contact["numerical_pressure_pa"], dtype=float).reshape(
        2, columns+1,
    )


def main(paths: list[Path], output: Path,
         exploratory_columns: tuple[int, ...] = ()) -> None:
    if output.exists() or len(paths) != 3:
        raise ValueError("provide three saved reports and a new output path")
    columns = (16, 24, 32)+exploratory_columns
    if columns != tuple(sorted(set(columns))):
        raise ValueError("exploratory columns must increase beyond 32 without duplicates")
    cases = [_linearized_case(n) for n in columns]
    for case, path, step in zip(cases[:3], paths, (-1, 2, -1)):
        saved = _saved_pressure(path, case["columns"], step)
        reference = (case["columns"], case["pressure"], {})
        observed = (case["columns"], saved, {})
        case["saved_report"] = str(path)
        case["saved_pressure_l2_relative_to_linearized"] = float(np.sqrt(
            _squared_norm(reference, observed)
            / _squared_norm(reference)
        ))
        case["saved_front_l2_absolute_pa_sqrt_m"] = float(np.sqrt(
            _squared_norm(reference, observed, x_min=0.625, x_max=0.75)
        ))
    adjacent = []
    for first, second in zip(cases, cases[1:]):
        earlier = (first["columns"], np.asarray(first["pressure"]), {})
        later = (second["columns"], np.asarray(second["pressure"]), {})
        adjacent.append({
            "columns": [first["columns"], second["columns"]],
            "full_relative_l2": float(np.sqrt(
                _squared_norm(earlier, later)/_squared_norm(later)
            )),
            "front_absolute_l2_pa_sqrt_m": float(np.sqrt(
                _squared_norm(earlier, later, x_min=0.625, x_max=0.75)
            )),
        })
    finest = (cases[-1]["columns"], cases[-1]["pressure"], {})
    finest_comparisons = []
    for case in cases[:-1]:
        earlier = (case["columns"], case["pressure"], {})
        finest_comparisons.append({
            "columns": case["columns"],
            "relative_full_l2": float(np.sqrt(
                _squared_norm(earlier, finest)/_squared_norm(finest)
            )),
            "absolute_front_l2_pa_sqrt_m": float(np.sqrt(
                _squared_norm(earlier, finest, x_min=0.625, x_max=0.75)
            )),
            "absolute_interior_l2_pa_sqrt_m": float(np.sqrt(
                _squared_norm(earlier, finest, x_min=0.8, x_max=1.0)
            )),
        })
    for case in cases:
        case["pressure"] = case["pressure"].tolist()
    report = {
        "candidate": "fixed_geometry_linearized_q4_s3_coupled_front_dev",
        "limitations": "shared stress-free Q4 structural tangent; independent planar contact mass matrix and QP; no moving projection or nonlinear path",
        "cases": cases,
        "adjacent": adjacent,
        "finest_columns": cases[-1]["columns"],
        "finest_comparisons": finest_comparisons,
    }
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "cases": [{key: value for key, value in case.items()
                   if key != "pressure"} for case in cases],
        "adjacent": adjacent,
        "finest_comparisons": finest_comparisons,
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exploratory-columns", type=int, nargs="*", default=[])
    args = parser.parse_args()
    main(args.reports, args.output, tuple(args.exploratory_columns))
