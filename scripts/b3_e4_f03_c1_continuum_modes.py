"""Bounded C1 transverse-section and longitudinal-projection diagnostic.

This is a development check of the existing six-channel hybrid connection,
not a multiplier selection, exact-line qualification, or solid-bond oracle.
Only shell translations are varied; the native retained B3 port stays at its
actual C1 reference state. A separate E4 physical tangent measures whether
the supported shell fields carry strain energy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_distributed_surface_finite import (
    FiniteSurfaceLineHybrid, c1_hybrid_line_space,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")


def _station_gaps(patch: FiniteSurfaceLineHybrid,
                  shell_step: np.ndarray) -> tuple[dict[float, np.ndarray], float]:
    """Independently integrate the reference shell translation over each width."""
    step = np.asarray(shell_step, dtype=float).reshape(patch.shell_count, 6)
    if np.max(np.abs(step[:, 3:])) != 0. or not np.isfinite(step).all():
        raise ValueError("bounded diagnostic requires finite shell translations")
    grouped: dict[float, list] = {}
    for point in patch.points:
        grouped.setdefault(point.x, []).append(point)
    state = patch.beam.context.initial.mechanical
    station = {}
    local_square = 0.
    for x, points in grouped.items():
        _, _, frame = points[0].port.pose_pair(state)
        weight = float(sum(point.weight for point in points))
        inertia = sum(point.weight*point.y**2 for point in points)/weight
        if weight <= 0. or inertia <= 0.:
            raise ArithmeticError("C1 station lacks physical transverse measure")
        mean = np.zeros(3)
        mx = 0.
        mz = 0.
        for point in points:
            displacement = point.shape@step[point.nodes, :3]
            local = frame.T@displacement
            fraction = point.weight/weight
            mean += fraction*local
            mx += fraction*point.y*local[2]/inertia
            mz -= fraction*point.y*local[0]/inertia
            local_square += point.weight*float(displacement@displacement)
        station[x] = np.array((mean[0], mean[1], mean[2], mx, 0., mz))
    return station, float(np.sqrt(local_square))


def _report(patch: FiniteSurfaceLineHybrid, rows_by_kind: dict,
            shell_step: np.ndarray) -> dict:
    beam_step = np.zeros(patch.beam.context.count)
    direction = np.r_[shell_step.ravel(), beam_step]
    stations, slip_rms = _station_gaps(patch, shell_step)
    grouped_weight = {}
    for point in patch.points:
        grouped_weight[point.x] = grouped_weight.get(point.x, 0.)+point.weight
    mean_profile = sum((grouped_weight[x]*value
                        for x, value in stations.items()), np.zeros(6))
    integrated = patch.reference_trace()@direction
    if np.max(np.abs(integrated-mean_profile)) > 1e-12:
        raise ArithmeticError("continuous station work does not reproduce trace")
    row_max = {kind: float(np.max(np.abs(rows@direction)))
               for kind, rows in rows_by_kind.items()}
    resolution = {}
    for intervals in (2, 4, 8):
        for kind in KINDS:
            space = LineMultiplierSpace(
                kind, tuple(np.linspace(0., 1., intervals+1)))
            projected = np.zeros((space.count, 6))
            mass = np.zeros(space.count)
            for x, gap in stations.items():
                basis = space.values(float((x-.9)/.1))
                projected += grouped_weight[x]*basis[:, None]*gap
                mass += grouped_weight[x]*basis
            if np.min(mass) <= 0.:
                raise ArithmeticError("nonpositive multiplier basis integral")
            resolution[f"{kind}_{intervals}"] = {
                "max_integrated_gap": float(np.max(np.abs(projected))),
                "max_basis_mean_gap_m": float(np.max(np.abs(projected/mass[:, None]))),
                "rows": space.count*6,
            }
    profile = np.array(list(stations.values()))
    return {
        "sampled_local_slip_rms_m": slip_rms,
        "continuous_g6_component_max_abs": np.max(np.abs(profile), axis=0).tolist(),
        "continuous_g6_component_weighted_rms": np.sqrt(sum(
            grouped_weight[x]*value**2 for x, value in stations.items())).tolist(),
        "integrated_mean_g6": integrated.tolist(),
        "weak_row_max_abs_by_space": row_max,
        "longitudinal_resolution_detection": resolution,
        "station_count": len(stations),
    }


def evaluate() -> dict:
    xs, ys = local_grid(8, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    patch = FiniteSurfaceLineHybrid(xs, ys, beam, thickness=.035)
    rows_by_kind = {kind: c1_hybrid_line_space(
        xs, ys, beam, kind=kind)[0] for kind in KINDS}
    shell_size = patch.shell_size
    nx = len(xs)

    # An even, mean-free transverse field is invisible to a section law
    # containing only mean and first transverse moments. It vanishes at the
    # supported shell root and is nonzero only on the terminal bond nodes.
    y2 = patch.reference_nodes[:, 1]**2
    sampled_y2 = np.array([point.shape@y2[point.nodes]
                           for point in patch.points])
    mean_y2 = float(sum(point.weight*value for point, value in
                        zip(patch.points, sampled_y2)))
    transverse = np.zeros((patch.shell_count, 6))
    terminal = ((patch.reference_nodes[:, 0] >= .9-1e-12) &
                (np.abs(patch.reference_nodes[:, 1]) <= .05+1e-12))
    transverse[terminal, 2] = .01*(y2[terminal]-mean_y2)

    # Eight bond hosts supply a representable shell x field outside the
    # fixed two-cell multiplier spans. Project the shell-only x columns into
    # the common null of the three existing candidate row spaces.
    bond_columns = np.flatnonzero((xs >= .9-1e-12) & (xs <= 1.+1e-12))
    columns = np.zeros((shell_size+beam.context.count, len(bond_columns)))
    for column, i in enumerate(bond_columns):
        for j in range(len(ys)):
            columns[6*(j*nx+int(i))+2, column] = 1.
    combined = np.vstack([rows_by_kind[kind]@columns for kind in KINDS])
    u, singular, vh = np.linalg.svd(combined, full_matrices=True)
    coefficients = vh[-1]
    normalized_null = float(np.linalg.norm(combined@coefficients) /
                            max(np.linalg.norm(combined)*np.linalg.norm(coefficients),
                                1e-30))
    if normalized_null > 1e-10:
        raise ArithmeticError("no common representable longitudinal null")
    longitudinal = (columns[:shell_size]@coefficients).reshape(
        patch.shell_count, 6)
    longitudinal *= 1e-5/np.max(np.abs(longitudinal[:, 2]))

    physical_tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    reports = {}
    for name, step in (("transverse_section", transverse),
                       ("longitudinal_projection", longitudinal)):
        report = _report(patch, rows_by_kind, step)
        vector = step.ravel()
        report["physical_shell_energy_j"] = float(.5*vector@physical@vector)
        report["complete_shell_energy_j"] = float(.5*vector@physical_tangent@vector)
        report["fixed_root_max_displacement_m"] = float(np.max(np.abs(
            step[patch.reference_nodes[:, 0] <= -.5+1e-12])))
        if (report["physical_shell_energy_j"] <= 0. or
                report["fixed_root_max_displacement_m"] > 0.):
            raise ArithmeticError("supported physical shell mode is invalid")
        reports[name] = report
    if (max(reports["transverse_section"]["continuous_g6_component_max_abs"])
            > 1e-12 or
            reports["transverse_section"]["sampled_local_slip_rms_m"] <= 1e-6):
        raise ArithmeticError("transverse section-null classification failed")
    if (max(reports["longitudinal_projection"]["weak_row_max_abs_by_space"].values())
            > 1e-12 or
            max(reports["longitudinal_projection"]["continuous_g6_component_max_abs"])
            <= 1e-7):
        raise ArithmeticError("longitudinal projection-null classification failed")
    return {
        "classification": "bounded G0B development diagnostic; growing-space detection is not stability or multiplier selection",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "geometry": "C1 35 mm Q4 x8/y4 terminal bond, native retained B3-12, reference shell translations only",
        "law": "six-channel transverse mean/first-moment and director-pitch pose trace",
        "combined_row_singular_values": singular.tolist(),
        "common_null_relative_residual": normalized_null,
        "physical_tangent": "E4 physical stiffness without drilling completion",
        "modes": reports,
        "limitations": [
            "translation-only linearized fields; no loaded coupled solution",
            "a transverse section null does not by itself classify the intended connection law",
            "a longitudinal projection null on fixed multiplier spans is not a uniform inf-sup result",
            "growing-space row detection does not establish locking, loaded work, or mixed-system stability",
            "saved F5 common action does not provide one-sided retained B3 port work",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(evaluate(), indent=2, sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == "__main__":
    main()
