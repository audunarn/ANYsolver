"""Compare an accepted two-body D1 press with independent linear Q1 mortar."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

from docs.d1_review_support.d1_two_body_reference_oracle import (
    solve_reference, solve_reference_singleton,
)
from scripts.general_contact_d1_interior_press_dev import build_interior_press


def main(saved_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    expected = {
        "status": "completed", "accepted_steps": 2,
        "source_columns": 4, "source_rows": 4, "target_s3_faces": 2,
        "source_support": "perimeter", "load_shape": "interior_distributed",
        "force_n": 0.04, "reference_slope": 1.0e-4,
        "slide_body": "target", "four_phase": False,
    }
    if any(saved.get(key) != value for key, value in expected.items()):
        raise ValueError("saved nonlinear press differs from bounded oracle case")
    model, definition, _settings, program = build_interior_press(
        source_support="perimeter", source_columns=4, source_rows=4,
        target_columns=1, target_rows=1, force_n=0.04,
        reference_slope=1.0e-4, load_shape="interior_distributed",
        slide_body="target",
    )
    reference = solve_reference(
        model, definition, program, 2, physical_parallel_skin=True,
    )
    production = saved["history"][-1]["contact"]
    displacement = np.asarray(saved["displacements"], dtype=float)
    source_ids = tuple(production["source_pressure_node_ids"])
    if source_ids != reference["source_pressure_nodes"]:
        raise ValueError("oracle and solver source pressure order differ")
    pressure = np.asarray(production["numerical_pressure_pa"])
    active_production = [node for node, value in zip(source_ids, pressure)
                         if value > 0.0]
    active_reference = [node for node, value in zip(source_ids,
                                                    reference["pressure"])
                        if value > 0.0]
    force_prod = float(production["integration_force"][2])
    force_ref = float(reference["integrated_force"])
    norm_u = max(float(np.linalg.norm(reference["displacement"])), 1.0e-15)
    norm_p = max(float(np.linalg.norm(reference["pressure"])), 1.0e-15)
    normal_gap_at_production = (
        reference["initial_gap"]
        + reference["weighted_gap_work"] @ displacement/reference["support"]
    )
    result = {
        "status": "development_two_body_linear_oracle_comparison",
        "production_input": str(saved_path),
        "reference_scope": "frozen_xy_footprint_linear_two_body_q1_s3",
        "independent_initial_parallel_skin_gap_m": reference["initial_gap"],
        "independent_reference_overlap_area_m2": reference["integrated_area"],
        "oracle_active_set_iterations": reference["active_set_iterations"],
        "production_active_node_ids": active_production,
        "oracle_active_node_ids": active_reference,
        "production_integrated_normal_force_n": force_prod,
        "oracle_integrated_normal_force_n": force_ref,
        "integrated_force_relative_difference": abs(force_prod-force_ref)
                                              /max(abs(force_ref), 1.0e-15),
        "displacement_relative_l2_difference": float(np.linalg.norm(
            displacement-reference["displacement"])/norm_u),
        "pressure_relative_l2_difference": float(np.linalg.norm(
            pressure-reference["pressure"])/norm_p),
        "support_relative_l2_difference": float(np.linalg.norm(
            np.asarray(production["reference_support_m2"])
            -reference["support"])/np.linalg.norm(reference["support"])),
        "oracle_gap_at_production_minimum_m": float(np.min(
            normal_gap_at_production)),
        "production_normalized_gap_minimum_m": float(np.min(
            production["normalized_weighted_gap_m"])),
        "oracle_pressure_pa": reference["pressure"].tolist(),
        "oracle_displacements_m": reference["displacement"].tolist(),
    }
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items()
                      if not key.startswith("oracle_pressure")
                      and not key.startswith("oracle_displacements")}))


def singleton_family(output: Path, inputs: list[Path]) -> None:
    if output.exists() or len(inputs) != 3:
        raise ValueError("singleton family needs new output and three saved poses")
    cases = []
    for path in inputs:
        saved = json.loads(path.read_text(encoding="utf-8"))
        expected = {
            "status": "completed", "accepted_steps": 2,
            "source_support": "perimeter", "load_shape": "interior_distributed",
            "force_n": 0.04, "reference_slope": 1.0e-4,
            "slide_body": "target", "four_phase": False,
        }
        if (any(saved.get(key) != value for key, value in expected.items())
                or saved.get("source_columns") not in (4, 8)
                or saved.get("source_rows") not in (4, 8)
                or saved.get("target_s3_faces") not in (2, 4)):
            raise ValueError(f"saved pose is outside singleton family: {path}")
        model, definition, _settings, program = build_interior_press(
            source_support="perimeter",
            source_columns=saved["source_columns"],
            source_rows=saved["source_rows"],
            target_columns=saved["target_s3_faces"]//2,
            target_rows=1, force_n=0.04, reference_slope=1.0e-4,
            load_shape="interior_distributed", slide_body="target",
        )
        reference = solve_reference_singleton(model, definition, program, 2)
        production = saved["history"][-1]["contact"]
        pressure = np.asarray(production["numerical_pressure_pa"])
        if tuple(production["source_pressure_node_ids"]) != (
                reference["source_pressure_nodes"]):
            raise ValueError("oracle pressure node order differs")
        force_production = float(production["integration_force"][2])
        force_reference = float(reference["integrated_force"])
        displacement_production = np.asarray(saved["displacements"])
        displacement_reference = reference["displacement"]
        cases.append({
            "input": str(path),
            "source_q4_faces": saved["source_columns"]*saved["source_rows"],
            "target_s3_faces": saved["target_s3_faces"],
            "oracle_active_node_id": reference["active_node_id"],
            "production_active_node_ids": [node for node, value in zip(
                production["source_pressure_node_ids"], pressure)
                if value > 0.0],
            "oracle_integrated_normal_force_n": force_reference,
            "production_integrated_normal_force_n": force_production,
            "integrated_force_relative_difference": abs(
                force_production-force_reference)/max(abs(force_reference), 1e-15),
            "displacement_relative_l2_difference": float(np.linalg.norm(
                displacement_production-displacement_reference)
                /max(np.linalg.norm(displacement_reference), 1e-15)),
            "pressure_relative_l2_difference": float(np.linalg.norm(
                pressure-reference["pressure"])
                /max(np.linalg.norm(reference["pressure"]), 1e-15)),
            "oracle_initial_gap_m": reference["initial_gap"],
            "oracle_structural_free_coordinates": reference[
                "structural_free_coordinates"],
        })
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(cases))


def _source_vertical_samples(model, displacement, rows, sample_points,
                             *, columns=8):
    values_at_points = []
    for x, y in sample_points:
        local_x = (x-0.1)*columns
        local_y = (y-0.1)*rows
        column = min(int(local_x), columns-1)
        row = min(int(local_y), rows-1)
        x_fraction = local_x-column
        y_fraction = local_y-row
        values = np.array([
            displacement[model.mesh.dof_manager.get_node_dofs(
                1+j*(columns+1)+i)[2]]
            for j, i in ((row, column), (row, column+1),
                         (row+1, column), (row+1, column+1))
        ])
        weights = np.array([(1-x_fraction)*(1-y_fraction),
                            x_fraction*(1-y_fraction),
                            (1-x_fraction)*y_fraction,
                            x_fraction*y_fraction])
        values_at_points.append(float(weights @ values))
    return values_at_points


def offline_y_reference(output: Path, *, load_shape: str = "interior_distributed") -> None:
    """Screen source-y resolution with one independently clipped linear oracle.

    This keeps x resolution, target mesh, loads, support and initial opening
    fixed. The 16-row case is guarded in the fixture builder and is never an
    ordinary coupled-solve admission.
    """
    if output.exists():
        raise FileExistsError(output)
    cases = []
    # Physical source coordinates start at (0.1, 0.1), unlike local fractions.
    sample_points = ((0.6, 0.6), (0.6, 0.7), (0.6, 0.9))
    for rows in (4, 8, 16):
        model, definition, _settings, program = build_interior_press(
            source_support="perimeter", source_columns=8, source_rows=rows,
            source_y_profile="uniform_ref16" if rows == 16 else None,
            offline_structural_reference_y16=(rows == 16),
            target_columns=2, target_rows=1, force_n=0.04,
            reference_slope=1.0e-4, load_shape=load_shape,
            slide_body="target",
        )
        nodal_forces = np.asarray(program.force_values_at(2), dtype=float)
        if abs(float(np.sum(nodal_forces))+0.04) > 1.0e-12:
            raise ValueError("reference load does not balance to 0.04 N")
        centroid = [float(sum(
            -force*getattr(model.mesh.nodes[item.node_id], axis)
            for item, force in zip(program.nodal_forces, nodal_forces,
                                   strict=True))/0.04)
            for axis in ("x", "y")]
        if load_shape == "physical_bump" and np.max(
                np.abs(np.asarray(centroid)-0.6)) > 1.0e-12:
            raise ValueError("physical bump load centroid changed")
        try:
            reference = solve_reference_singleton(
                model, definition, program, 2,
                allow_multimode=(rows == 16 or load_shape == "physical_bump"))
        except ValueError as error:
            output.write_text(json.dumps({"cases": cases, "failed_rows": rows,
                                          "failure": str(error)}, indent=2)+"\n",
                              encoding="utf-8")
            raise
        displacement = reference["displacement"]
        source_values = _source_vertical_samples(
            model, displacement, rows, sample_points)
        cases.append({
            "source_columns": 8, "source_rows": rows,
            "target_s3_faces": 4,
            "load_shape": load_shape,
            "load_centroid_xy_m": centroid,
            "oracle_active_node_id": reference["active_node_id"],
            "oracle_active_node_ids": reference["active_node_ids"],
            "oracle_method": reference["reference_method"],
            "integrated_normal_force_n": reference["integrated_force"],
            "sample_xy_m": sample_points,
            "source_vertical_displacement_m": source_values,
            "structural_free_coordinates": reference[
                "structural_free_coordinates"],
        })
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(cases))


def offline_x_reference(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    cases = []
    points = ((0.6, 0.6), (0.6, 0.7), (0.6, 0.9))
    for columns in (8, 16):
        model, definition, _settings, program = build_interior_press(
            source_support="perimeter", source_columns=columns,
            source_rows=16, source_y_profile="uniform_ref16",
            offline_structural_reference_y16=True,
            target_columns=2, target_rows=1, force_n=0.04,
            reference_slope=1.0e-4, load_shape="physical_bump",
            slide_body="target",
        )
        reference = solve_reference_singleton(
            model, definition, program, 2, allow_multimode=True)
        forces = np.asarray(program.force_values_at(2))
        if abs(float(np.sum(forces))+0.04) > 1.0e-12:
            raise ValueError("x-reference load does not balance")
        cases.append({
            "source_columns": columns, "source_rows": 16,
            "target_s3_faces": 4, "load_shape": "physical_bump",
            "integrated_normal_force_n": reference["integrated_force"],
            "active_node_ids": reference["active_node_ids"],
            "sample_xy_m": points,
            "source_vertical_displacement_m": _source_vertical_samples(
                model, reference["displacement"], 16, points,
                columns=columns),
            "structural_free_coordinates": reference[
                "structural_free_coordinates"],
        })
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(cases))


def offline_target_reference(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    from examples.general_contact_d1_interior_controls_dev import (
        _independent_projected_gap_bound,
    )

    cases = []
    points = ((0.6, 0.6), (0.6, 0.7), (0.6, 0.9))
    for target_rows in (1, 2, 3):
        model, definition, _settings, program = build_interior_press(
            source_support="perimeter", source_columns=16,
            source_rows=16, source_y_profile="uniform_ref16",
            offline_structural_reference_y16=True,
            target_columns=2, target_rows=target_rows, force_n=0.04,
            reference_slope=1.0e-4, load_shape="physical_bump",
            slide_body="target",
            target_reference_full_left_clamp=(target_rows > 1),
        )
        target_first = 17*17+1
        middle_left = tuple(target_first+3*row
                            for row in range(1, target_rows))
        reference = solve_reference_singleton(
            model, definition, program, 2, allow_multimode=True)
        try:
            lower_gap = _independent_projected_gap_bound(
                model, definition, reference["displacement"],
                definition.interactions[0].gap_tolerance)
        except RuntimeError as error:
            output.write_text(json.dumps({
                "cases": cases, "failed_target_rows": target_rows,
                "failure": str(error)}, indent=2)+"\n", encoding="utf-8")
            raise
        cases.append({
            "source_columns": 16, "source_rows": 16,
            "target_columns": 2, "target_rows": target_rows,
            "target_s3_faces": 4*target_rows,
            "fixed_middle_left_nodes": middle_left,
            "load_shape": "physical_bump",
            "integrated_normal_force_n": reference["integrated_force"],
            "active_node_ids": reference["active_node_ids"],
            "independent_projected_lower_gap_m": lower_gap,
            "sample_xy_m": points,
            "source_vertical_displacement_m": _source_vertical_samples(
                model, reference["displacement"], 16, points,
                columns=16),
            "structural_free_coordinates": reference[
                "structural_free_coordinates"],
        })
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(cases))


def target8s3_coupled_oracle(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    from examples.general_contact_d1_interior_controls_dev import (
        _independent_projected_gap_bound,
    )

    model, definition, _settings, program = build_interior_press(
        source_support="perimeter", source_columns=8, source_rows=8,
        target_columns=2, target_rows=2,
        target_reference_full_left_clamp=True,
        force_n=0.04, reference_slope=1.0e-4,
        load_shape="physical_bump", slide_body="target",
    )
    reference = solve_reference_singleton(
        model, definition, program, 2, allow_multimode=True)
    gap = _independent_projected_gap_bound(
        model, definition, reference["displacement"],
        definition.interactions[0].gap_tolerance)
    record = {
        "source_q4_faces": 64, "target_s3_faces": 8,
        "load_shape": "physical_bump",
        "fixed_middle_left_node_id": 1+9*9+3,
        "integrated_normal_force_n": reference["integrated_force"],
        "active_node_ids": reference["active_node_ids"],
        "independent_projected_lower_gap_m": gap,
        "sample_xy_m": ((0.6, 0.6), (0.6, 0.7), (0.6, 0.9)),
        "source_vertical_displacement_m": _source_vertical_samples(
            model, reference["displacement"], 8,
            ((0.6, 0.6), (0.6, 0.7), (0.6, 0.9))),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


def target8s3_coupled_comparison(output: Path, reference_path: Path,
                                saved_path: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    from examples.general_contact_d1_interior_controls_dev import (
        _independent_projected_gap_bound,
    )

    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if (saved["status"] != "completed" or saved["accepted_steps"] != 2
            or saved["source_columns"] != 8 or saved["source_rows"] != 8
            or saved["target_s3_faces"] != 8
            or saved["target_reference_full_left_clamp"] is not True
            or saved["load_shape"] != "physical_bump"
            or saved["q4_gap_certificate"] != "overlap_local_dev"):
        raise ValueError("saved pose is outside selected target8s3 comparison")
    model, definition, _settings, _program = build_interior_press(
        source_support="perimeter", source_columns=8, source_rows=8,
        target_columns=2, target_rows=2,
        target_reference_full_left_clamp=True,
        force_n=0.04, reference_slope=1.0e-4,
        load_shape="physical_bump", slide_body="target",
    )
    displacement = np.asarray(saved["displacements"])
    contact = saved["history"][-1]["contact"]
    pressure = np.asarray(contact["numerical_pressure_pa"])
    force = float(contact["integration_force"][2])
    reference_force = reference["integrated_normal_force_n"]
    samples = _source_vertical_samples(
        model, displacement, 8, reference["sample_xy_m"])
    independent_lower = _independent_projected_gap_bound(
        model, definition, displacement,
        definition.interactions[0].gap_tolerance)
    record = {
        "saved_pose": str(saved_path), "oracle": str(reference_path),
        "solver_status": saved["status"],
        "accepted_steps": saved["accepted_steps"],
        "certificate": saved["q4_gap_certificate"],
        "production_integrated_normal_force_n": force,
        "oracle_integrated_normal_force_n": reference_force,
        "relative_integrated_force_difference": abs(
            force-reference_force)/abs(reference_force),
        "production_active_node_ids": [node for node, value in zip(
            contact["source_pressure_node_ids"], pressure) if value > 0.0],
        "oracle_active_node_ids": reference["active_node_ids"],
        "relative_source_displacement_difference": [
            abs(a-b)/max(abs(b), 1.0e-15) for a, b in zip(
                samples, reference["source_vertical_displacement_m"])],
        "independent_projected_lower_gap_m": independent_lower,
        "registered_gap_tolerance_m": (
            definition.interactions[0].gap_tolerance),
        "production_contact_force_balance_n": [
            a+b for a, b in zip(contact["integration_force"],
                                contact["target_force"])],
        "production_contact_moment_balance_nm": [
            a+b for a, b in zip(contact["integration_moment"],
                                contact["target_moment"])],
        "active_rim_pressure_pa": saved["history"][-1]["rim_pressure_pa"],
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


def coupled_y_comparison(output: Path, reference_path: Path,
                         saved_paths: list[Path]) -> None:
    if output.exists() or len(saved_paths) not in (1, 2):
        raise ValueError("coupled y comparison needs new output and one or two saved poses")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    cases = []
    for path in saved_paths:
        saved = json.loads(path.read_text(encoding="utf-8"))
        rows = saved["source_rows"]
        if (rows not in (8, 16) or saved["source_columns"] != 8
                or saved["target_s3_faces"] != 4
                or saved["status"] != "completed"
                or saved["accepted_steps"] != 2):
            raise ValueError(f"saved pose is outside bounded y comparison: {path}")
        corresponding = next(item for item in reference["cases"]
                             if item["source_rows"] == rows)
        if saved["load_shape"] != corresponding.get(
                "load_shape", "interior_distributed"):
            raise ValueError("coupled and oracle load fields differ")
        model, _definition, _settings, _program = build_interior_press(
            source_support="perimeter", source_columns=8,
            source_rows=rows,
            source_y_profile="uniform_ref16" if rows == 16 else None,
            offline_structural_reference_y16=(rows == 16),
            target_columns=2, target_rows=1, force_n=0.04,
            reference_slope=1.0e-4, load_shape=saved["load_shape"],
            slide_body="target",
        )
        production = saved["history"][-1]["contact"]
        pressure = np.asarray(production["numerical_pressure_pa"])
        production_force = float(production["integration_force"][2])
        reference_force = corresponding["integrated_normal_force_n"]
        samples = _source_vertical_samples(
            model, np.asarray(saved["displacements"]), rows,
            corresponding["sample_xy_m"])
        reference_samples = corresponding["source_vertical_displacement_m"]
        cases.append({
            "saved_pose": str(path), "source_rows": rows,
            "source_sample_xy_m": corresponding["sample_xy_m"],
            "production_source_vertical_displacement_m": samples,
            "oracle_source_vertical_displacement_m": reference_samples,
            "relative_source_displacement_difference": [
                abs(a-b)/max(abs(b), 1e-15)
                for a, b in zip(samples, reference_samples)],
            "production_active_node_ids": [node for node, value in zip(
                production["source_pressure_node_ids"], pressure)
                if value > 0.0],
            "oracle_active_node_ids": corresponding["oracle_active_node_ids"],
            "production_integrated_normal_force_n": production_force,
            "oracle_integrated_normal_force_n": reference_force,
            "relative_integrated_force_difference": abs(
                production_force-reference_force)/max(abs(reference_force), 1e-15),
        })
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(cases))


def bump_gap_preflight(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    from examples.general_contact_d1_interior_controls_dev import (
        _independent_projected_gap_bound,
    )

    model, definition, _settings, program = build_interior_press(
        source_support="perimeter", source_columns=8, source_rows=16,
        source_y_profile="uniform_ref16",
        offline_structural_reference_y16=True,
        target_columns=2, target_rows=1, force_n=0.04,
        reference_slope=1.0e-4, load_shape="physical_bump",
        slide_body="target",
    )
    reference = solve_reference_singleton(
        model, definition, program, 2, allow_multimode=True)
    tolerance = definition.interactions[0].gap_tolerance
    try:
        gap = _independent_projected_gap_bound(
            model, definition, reference["displacement"], tolerance)
    except RuntimeError as error:
        output.write_text(json.dumps({
            "status": "development_preflight_failed",
            "failure": str(error),
            "active_node_ids": reference["active_node_ids"],
            "integrated_normal_force_n": reference["integrated_force"],
            "gap_tolerance_m": tolerance,
        }, indent=2)+"\n", encoding="utf-8")
        raise
    record = {
        "status": "development_preflight_passed",
        "active_node_ids": reference["active_node_ids"],
        "integrated_normal_force_n": reference["integrated_force"],
        "independent_projected_lower_gap_m": gap,
        "gap_tolerance_m": tolerance,
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--singleton-family":
        singleton_family(Path(sys.argv[2]), [Path(path) for path in sys.argv[3:]])
    elif len(sys.argv) > 1 and sys.argv[1] == "--offline-y-reference":
        offline_y_reference(Path(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--offline-y-reference-bump":
        offline_y_reference(Path(sys.argv[2]), load_shape="physical_bump")
    elif len(sys.argv) > 1 and sys.argv[1] == "--offline-x-reference":
        offline_x_reference(Path(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--offline-target-reference":
        offline_target_reference(Path(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--target8s3-coupled-oracle":
        target8s3_coupled_oracle(Path(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--target8s3-coupled-comparison":
        target8s3_coupled_comparison(Path(sys.argv[2]), Path(sys.argv[3]),
                                    Path(sys.argv[4]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--coupled-y-comparison":
        coupled_y_comparison(Path(sys.argv[2]), Path(sys.argv[3]),
                             [Path(path) for path in sys.argv[4:]])
    elif len(sys.argv) > 1 and sys.argv[1] == "--bump-gap-preflight":
        bump_gap_preflight(Path(sys.argv[2]))
    else:
        main(Path(sys.argv[1]), Path(sys.argv[2]))
