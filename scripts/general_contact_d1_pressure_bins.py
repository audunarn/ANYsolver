"""Independent common-bin pressure-force comparison for the guided D1 strip.

This development postprocessor integrates source-only Q1 pressure exactly and
aggregates the independent finite-volume obstacle reaction. It never calls a
general-contact kernel. The same bin geometry can later consume a coupled Q1
pressure field after its physical identities have been checked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.general_contact_d1_continuum_obstacle_reference import solve
from scripts.general_contact_d1_source_y_resolution import run


def _linear_integrals(left: float, right: float, cell_left: float,
                      cell_right: float) -> np.ndarray:
    length = right-left
    local_mid = (0.5*(left+right)-cell_left)/(cell_right-cell_left)
    return length*np.array((1.0-local_mid, local_mid))


def integrate_q1_bins(pressure_grid: np.ndarray, bins_x: int, bins_y: int,
                      obstacle_y_right: float = 0.9,
                      source_y_knots: tuple[float, ...] | None = None) -> np.ndarray:
    """Return exact bilinear Q1 pressure integrals on physical [0,1]^2 bins."""
    pressure = np.asarray(pressure_grid, dtype=float)
    if (pressure.ndim != 2 or min(pressure.shape) < 2
            or not np.all(np.isfinite(pressure))
            or bins_x < 1 or bins_y < 1
            or not 0.0 < obstacle_y_right <= 1.0):
        raise ValueError("invalid Q1 field or physical comparison bins")
    ny, nx = pressure.shape[0]-1, pressure.shape[1]-1
    y_knots = (np.linspace(0.0, 1.0, ny+1) if source_y_knots is None
               else np.asarray(source_y_knots, dtype=float))
    if (y_knots.shape != (ny+1,) or not np.all(np.isfinite(y_knots))
            or y_knots[0] != 0.0 or y_knots[-1] != 1.0
            or np.min(np.diff(y_knots)) <= 0.0):
        raise ValueError("invalid source y knots")
    forces = np.zeros((bins_y, bins_x))
    for j in range(ny):
        cy0, cy1 = y_knots[j:j+2]
        for by in range(bins_y):
            y0 = max(cy0, by/bins_y)
            y1 = min(cy1, (by+1)/bins_y, obstacle_y_right)
            if y1 <= y0:
                continue
            wy = _linear_integrals(y0, y1, cy0, cy1)
            for i in range(nx):
                cx0, cx1 = i/nx, (i+1)/nx
                for bx in range(bins_x):
                    x0 = max(cx0, bx/bins_x)
                    x1 = min(cx1, (bx+1)/bins_x)
                    if x1 <= x0:
                        continue
                    wx = _linear_integrals(x0, x1, cx0, cx1)
                    forces[by, bx] += wy @ pressure[j:j+2, i:i+2] @ wx
    return forces


def finite_volume_bins(pressure_force: np.ndarray, bins_x: int,
                       bins_y: int) -> np.ndarray:
    force = np.asarray(pressure_force, dtype=float)
    if (force.ndim != 2 or not np.all(np.isfinite(force))
            or force.shape[0] % bins_y or force.shape[1] % bins_x):
        raise ValueError("finite-volume cells must partition common bins")
    ny, nx = force.shape
    return force.reshape(bins_y, ny//bins_y, bins_x, nx//bins_x).sum(axis=(1, 3))


def main(output: Path, *, source_nx: int = 4, source_ny: int = 8,
         fv_nx: int = 128, fv_ny: int = 160,
         bins_x: int = 16, bins_y: int = 16,
         source_y_profile: str | None = None,
         reference_file: Path | None = None,
         reference_sha256: str | None = None) -> None:
    if output.exists():
        raise FileExistsError(output)
    if (source_nx not in (4, 8, 16, 32) or source_ny not in (4, 8, 16, 32, 40, 80)
            or (fv_nx, fv_ny) not in ((128, 160), (128, 320), (256, 320))
            or bins_x not in (8, 16, 32) or bins_y not in (8, 16, 32)
            or fv_nx % bins_x or fv_ny % bins_y):
        raise ValueError("outside bounded development comparison grids")
    if (reference_file is None) != (reference_sha256 is None):
        raise ValueError("saved reference requires its expected SHA-256")
    if source_y_profile not in (None, "rim8"):
        raise ValueError("unknown bounded source y profile")
    if source_y_profile == "rim8" and source_ny != 8:
        raise ValueError("rim8 profile requires eight source rows")
    source_y_knots = (None if source_y_profile is None else
                      (0.0, 0.2, 0.4, 0.6, 0.75, 0.825, 0.875, 0.9, 1.0))
    source = run(source_nx, source_ny, obstacle_y_right=0.9,
                 source_y_knots=source_y_knots)
    source_bins = integrate_q1_bins(
        source["pressure_grid_pa"], bins_x, bins_y,
        source_y_knots=source_y_knots,
    )
    if reference_file is None:
        continuum = solve(fv_nx, fv_ny, 0.9)
        reference_bins = finite_volume_bins(
            continuum.pressure_force, bins_x, bins_y,
        )
        continuum_total = continuum.contact_reaction_n
        continuum_minimum_gap = continuum.minimum_gap_m
        continuum_active = int(np.sum(continuum.active))
        continuum_equilibrium = continuum.equilibrium_defect_n
    else:
        reference_bytes = reference_file.read_bytes()
        actual_hash = hashlib.sha256(reference_bytes).hexdigest()
        if (len(reference_sha256) != 64
                or any(character not in "0123456789abcdef"
                       for character in reference_sha256.lower())
                or actual_hash != reference_sha256.lower()):
            raise ValueError("saved finite-volume reference SHA-256 differs")
        saved = json.loads(reference_bytes)
        if (saved.get("method") !=
                "development independent Q1/FV conservative 2D common-bin pressure-force comparison; not acceptance"
                or saved.get("finite_volume_grid") != [fv_nx, fv_ny]
                or saved.get("common_bins") != [bins_x, bins_y]
                or saved.get("obstacle_y_right_m") != 0.9
                or saved.get("physical_domain_m")
                != [[0.0, 1.0], [0.0, 1.0]]):
            raise ValueError("saved finite-volume reference differs from bins")
        reference_bins = np.asarray(saved["finite_volume_bin_force_n"])
        if (reference_bins.shape != (bins_y, bins_x)
                or not np.all(np.isfinite(reference_bins))
                or np.min(reference_bins) < -1.0e-12):
            raise ValueError("saved finite-volume bins are invalid")
        continuum_total = saved["finite_volume_total_reaction_n"]
        continuum_minimum_gap = saved["finite_volume_minimum_cell_gap_m"]
        continuum_active = saved["finite_volume_active_cells"]
        continuum_equilibrium = saved["finite_volume_equilibrium_defect_n"]
        if (not all(np.isfinite(value) for value in (
                continuum_total, continuum_minimum_gap,
                continuum_equilibrium))
                or not isinstance(continuum_active, int)
                or isinstance(continuum_active, bool)
                or continuum_total <= 0.0 or continuum_active <= 0
                or continuum_minimum_gap < -1.0e-12
                or continuum_equilibrium > 1.0e-9):
            raise ValueError("saved finite-volume KKT/balance is invalid")
    source_total = float(np.sum(source_bins))
    reference_total = float(np.sum(reference_bins))
    if (abs(source_total-source["integrated_reaction_n"]) > 1.0e-12
            or abs(reference_total-continuum_total) > 1.0e-11):
        raise AssertionError("common-bin force lost the original reaction")
    difference = source_bins-reference_bins
    record = {
        "method": "development independent Q1/FV conservative 2D common-bin pressure-force comparison; not acceptance",
        "source_grid": [source_nx, source_ny],
        "source_y_profile": source_y_profile,
        "source_y_knots_m": source["source_y_knots_m"],
        "finite_volume_grid": [fv_nx, fv_ny],
        "finite_volume_reference_file": (str(reference_file)
                                         if reference_file is not None else None),
        "finite_volume_reference_sha256": (
            reference_sha256.lower() if reference_sha256 is not None else None),
        "common_bins": [bins_x, bins_y],
        "physical_domain_m": [[0.0, 1.0], [0.0, 1.0]],
        "obstacle_y_right_m": 0.9,
        "source_total_reaction_n": source_total,
        "finite_volume_total_reaction_n": reference_total,
        "source_bin_force_n": source_bins.tolist(),
        "finite_volume_bin_force_n": reference_bins.tolist(),
        "bin_force_l1_relative_to_reference": float(
            np.sum(np.abs(difference))/reference_total),
        "bin_force_l2_relative_to_reference": float(
            np.linalg.norm(difference)/np.linalg.norm(reference_bins)),
        "maximum_x_cumulative_force_difference_relative": float(
            np.max(np.abs(np.cumsum(np.sum(difference, axis=0))))
            / reference_total),
        "source_minimum_represented_gap_m": source["minimum_represented_gap_m"],
        "finite_volume_minimum_cell_gap_m": continuum_minimum_gap,
        "source_pressure_grid_pa": source["pressure_grid_pa"],
        "finite_volume_active_cells": continuum_active,
        "finite_volume_equilibrium_defect_n": continuum_equilibrium,
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "source_grid", "finite_volume_grid", "common_bins",
        "source_total_reaction_n", "finite_volume_total_reaction_n",
        "bin_force_l1_relative_to_reference",
        "bin_force_l2_relative_to_reference",
        "maximum_x_cumulative_force_difference_relative",
    )}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-nx", type=int, default=4)
    parser.add_argument("--source-ny", type=int, default=8)
    parser.add_argument("--fv-nx", type=int, default=128)
    parser.add_argument("--fv-ny", type=int, default=160)
    parser.add_argument("--bins-x", type=int, default=16)
    parser.add_argument("--bins-y", type=int, default=16)
    parser.add_argument("--source-y-profile", choices=("rim8",), default=None)
    parser.add_argument("--reference-file", type=Path, default=None)
    parser.add_argument("--reference-sha256", default=None)
    args = parser.parse_args()
    main(args.output, source_nx=args.source_nx, source_ny=args.source_ny,
         fv_nx=args.fv_nx, fv_ny=args.fv_ny,
         bins_x=args.bins_x, bins_y=args.bins_y,
         source_y_profile=args.source_y_profile,
         reference_file=args.reference_file,
         reference_sha256=args.reference_sha256)
