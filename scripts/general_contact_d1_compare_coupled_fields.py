"""Compare two saved near-rim coupled Q1 fields on common physical support.

Each input is a source-bound near-rim comparison record. The script verifies
the referenced coupled JSON and common independent FV oracle identity before
integrating the piecewise-bilinear pressure difference exactly by 2x2 Gauss
on the union x grid and shared y grid. It does not solve contact or qualify
pressure-space stability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from docs.d1_review_support import d1_rim_oracle as oracle


def _load(path: Path):
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "development_comparison_only":
        raise ValueError("input is not a near-rim coupled comparison")
    nx, ny = record["mesh"]
    if ny != 8 or nx < 1:
        raise ValueError("unexpected pressure mesh or comparison schema")
    coupled_path = Path(record["coupled_file"])
    if not coupled_path.is_absolute():
        coupled_path = Path.cwd()/coupled_path
    raw = coupled_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != record["coupled_sha256"]:
        raise ValueError("coupled source hash changed")
    oracle_path = Path(record["oracle_file"]).resolve()
    if (oracle_path != Path(oracle.__file__).resolve()
            or hashlib.sha256(oracle_path.read_bytes()).hexdigest()
            != record["oracle_sha256"]):
        raise ValueError("independent oracle source identity changed")
    coupled = json.loads(raw)
    if (coupled.get("status") != "completed"
            or coupled.get("columns") != nx
            or coupled.get("source_rows") != ny
            or coupled.get("source_y_profile") != "near_rim8"
            or coupled.get("pressure_basis") != "fine_nodal_q1"
            or coupled.get("total_downward_force_n") != 0.3):
        raise ValueError("coupled source model differs")
    if any(coupled.get(key) != value for key, value in
           record["validated_model_identity"].items()):
        raise ValueError("saved model identity no longer matches coupled source")
    if (coupled.get("normal_regularization_pa_per_m") != 10000.0
            or coupled.get("gap_tolerance_m") != 5.0e-5):
        raise ValueError("coupled normal settings differ")
    ids = coupled["contact"]["source_pressure_node_ids"]
    if ids != list(range(1, (nx+1)*(ny+1)+1)):
        raise ValueError("pressure node order differs")
    pressure = np.asarray(coupled["contact"]["numerical_pressure_pa"], dtype=float)
    pressure = pressure.reshape(ny+1, nx+1)
    if not np.all(np.isfinite(pressure)) or np.min(pressure) < 0.0:
        raise ValueError("pressure field is invalid")
    y_knots = np.asarray(record["source_y_knots_m"], dtype=float)
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, oracle.YR, 10), 1.0]
    xn = np.linspace(0.0, 1.0, nx+1)
    ix = oracle.bin_integrals_1d(nx, 8, nodes=xn, edges=edges_x)
    iy = oracle.bin_integrals_1d(8, 10, oracle.YR, y_knots, edges_y)
    expected_support = np.kron(iy.sum(axis=0), ix.sum(axis=0))
    if not np.allclose(coupled["contact"]["reference_support_m2"],
                       expected_support, rtol=1.0e-10, atol=1.0e-13):
        raise ValueError("coupled physical pressure support differs")
    recomputed_bins = oracle.q1_bins(
        dict(nx=nx, ny=ny, xn=xn, yn=y_knots, p=pressure),
        edges_x, edges_y,
    )
    stored_bins = np.asarray(record["coupled_bins_n"], dtype=float)
    reference_bins = np.asarray(record["fv_bins_n"], dtype=float)
    reaction = float(coupled["contact"]["integration_force"][2])
    if (stored_bins.shape != (10, 8) or reference_bins.shape != (10, 8)
            or not np.all(np.isfinite(stored_bins))
            or not np.all(np.isfinite(reference_bins))
            or not np.allclose(stored_bins, recomputed_bins,
                               rtol=1.0e-10, atol=1.0e-12)
            or abs(float(stored_bins.sum())-reaction) > 1.0e-10
            or abs(float(reference_bins.sum())-record["fv_reaction_n"])
            > 1.0e-10):
        raise ValueError("stored physical bins or reaction differ")
    physical_l2 = float(np.linalg.norm(stored_bins[:9]-reference_bins[:9])
                        / np.linalg.norm(reference_bins[:9]))
    if abs(physical_l2-record["coupled_vs_fv"]["l2_relative"]) > 1.0e-12:
        raise ValueError("stored FV bin metric differs from physical bins")
    return record, coupled, pressure


def _pressure_at(pressure, y_knots, x, y):
    nx = pressure.shape[1]-1
    i = min(int(nx*x), nx-1)
    j = min(int(np.searchsorted(y_knots, y, side="right")-1), len(y_knots)-2)
    a = nx*x-i
    b = (y-y_knots[j])/(y_knots[j+1]-y_knots[j])
    return float((1-a)*(1-b)*pressure[j, i]
                 + a*(1-b)*pressure[j, i+1]
                 + a*b*pressure[j+1, i+1]
                 + (1-a)*b*pressure[j+1, i])


def _relative_q1_l2(p, q, y_knots, *, support_y_max):
    """Integrate squared Q1 fields over represented physical target support."""
    if not y_knots[0] < support_y_max <= y_knots[-1]:
        raise ValueError("physical support end is outside source grid")
    x_knots = np.unique(np.r_[np.linspace(0.0, 1.0, p.shape[1]),
                                np.linspace(0.0, 1.0, q.shape[1])])
    squared_difference = squared_second = 0.0
    rule = (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0))
    for x0, x1 in zip(x_knots[:-1], x_knots[1:], strict=True):
        for y0, raw_y1 in zip(y_knots[:-1], y_knots[1:], strict=True):
            if y0 >= support_y_max:
                continue
            y1 = min(raw_y1, support_y_max)
            weight = (x1-x0)*(y1-y0)/4.0
            for gx in rule:
                x = (x0+x1)/2.0 + (x1-x0)*gx/2.0
                for gy in rule:
                    y = (y0+y1)/2.0 + (y1-y0)*gy/2.0
                    first_value = _pressure_at(p, y_knots, x, y)
                    second_value = _pressure_at(q, y_knots, x, y)
                    squared_difference += weight*(first_value-second_value)**2
                    squared_second += weight*second_value**2
    return float(np.sqrt(squared_difference/squared_second))


def compare(first_path: Path, second_path: Path):
    first, first_coupled, p = _load(first_path)
    second, second_coupled, q = _load(second_path)
    if (first["oracle_sha256"] != second["oracle_sha256"]
            or first["source_y_knots_m"] != second["source_y_knots_m"]
            or not np.array_equal(first["fv_bins_n"], second["fv_bins_n"])):
        raise ValueError("independent reference or physical bin identity differs")
    y_knots = np.asarray(first["source_y_knots_m"], dtype=float)
    if not np.all(np.diff(y_knots) > 0.0):
        raise ValueError("invalid shared y knots")
    # The finite S3 obstacle ends at y=.9. Nodal pressure outside its
    # projected support is not a physical contact-pressure field.
    support_y_max = oracle.YR
    first_bins = np.asarray(first["coupled_bins_n"], dtype=float)
    second_bins = np.asarray(second["coupled_bins_n"], dtype=float)
    if first_bins.shape != second_bins.shape or first_bins.shape != (10, 8):
        raise ValueError("common physical bins differ")
    difference = first_bins[:9]-second_bins[:9]
    reaction_first = float(first_coupled["contact"]["integration_force"][2])
    reaction_second = float(second_coupled["contact"]["integration_force"][2])
    return {
        "status": "development_comparison_only",
        "first_record": str(first_path),
        "second_record": str(second_path),
        "first_record_sha256": hashlib.sha256(first_path.read_bytes()).hexdigest(),
        "second_record_sha256": hashlib.sha256(second_path.read_bytes()).hexdigest(),
        "first_coupled_sha256": first["coupled_sha256"],
        "second_coupled_sha256": second["coupled_sha256"],
        "oracle_sha256": first["oracle_sha256"],
        "first_mesh": first["mesh"],
        "second_mesh": second["mesh"],
        "common_bin_shape": [8, 9],
        "pressure_support_y_max_m": support_y_max,
        "bin_force_l1_relative_to_second": float(
            np.sum(np.abs(difference))/np.sum(np.abs(second_bins[:9]))),
        "bin_force_l2_relative_to_second": float(
            np.linalg.norm(difference)/np.linalg.norm(second_bins[:9])),
        "rim_band_force_relative_to_second": float(
            abs(first_bins[8].sum()-second_bins[8].sum())
            / abs(second_bins[8].sum())),
        "q1_pressure_l2_relative_to_second": _relative_q1_l2(
            p, q, y_knots, support_y_max=support_y_max,
        ),
        "reaction_first_n": reaction_first,
        "reaction_second_n": reaction_second,
        "reaction_relative_change": float(
            abs(reaction_first-reaction_second)/abs(reaction_second)),
        "first_vs_fv_l2_relative": first["coupled_vs_fv"]["l2_relative"],
        "second_vs_fv_l2_relative": second["coupled_vs_fv"]["l2_relative"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = compare(args.first, args.second)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
