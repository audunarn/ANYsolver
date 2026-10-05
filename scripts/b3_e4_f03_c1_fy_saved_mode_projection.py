"""Project the saved 2:1 Fy/rotation mode; developmental interpretation only.

This reads the historical material-line linearized gap, not the prospective
L1 law. It does not rerun the eigensolve or assess F03 stability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _bases(x: np.ndarray, weights: np.ndarray) -> dict[str, tuple[np.ndarray, ...]]:
    cuts = np.linspace(0.9, 1.0, 9)
    p1 = np.zeros((len(x), 9))
    p0 = np.zeros((len(x), 8))
    paired = np.zeros((len(x), 4))
    for row, station in enumerate(x):
        edge = min(int(np.searchsorted(cuts, station, side="right")) - 1, 7)
        if edge < 0 or station < cuts[0] or station > cuts[-1]:
            raise ValueError("station left saved bonded interval")
        alpha = (station - cuts[edge]) / (cuts[edge + 1] - cuts[edge])
        p1[row, edge : edge + 2] = (1.0 - alpha, alpha)
        p0[row, edge] = 1.0
        paired[row, edge // 2] = 1.0
    mass = p1.T @ (weights[:, None] * p1)
    dual = p1 @ np.linalg.inv(mass)
    return {
        "A_P1_first_four_P0_last_two": (p1, p1, p1, p1, p0, p0),
        "B_P0_first_four_pair_P0_last_two":
            (p0, p0, p0, p0, paired, paired),
        "C_dual_P1_all_six": (dual,) * 6,
    }


def analyze(saved: dict) -> dict:
    x = np.asarray(saved["station_x_m"], dtype=float)
    w = np.asarray(saved["station_weights_m"], dtype=float)
    gap = np.asarray(saved["station_gap"], dtype=float)
    if (x.shape != (24,) or w.shape != (24,) or gap.shape != (24, 6)
            or not np.isfinite(x).all() or not np.isfinite(w).all()
            or not np.isfinite(gap).all() or np.any(w <= 0)
            or abs(float(w.sum()) - 0.1) > 1e-12):
        raise ValueError("saved eight-segment three-point mode changed")
    candidates = {}
    for name, spaces in _bases(x, w).items():
        channels = []
        for j, basis in enumerate(spaces):
            gram = basis.T @ (w[:, None] * basis)
            rows = basis.T @ (w * gap[:, j])
            coefficients = np.linalg.solve(gram, rows)
            projected = basis @ coefficients
            gap_norm = float(np.sqrt(np.dot(w, gap[:, j] ** 2)))
            residual = float(np.sqrt(np.dot(w, (gap[:, j] - projected) ** 2)))
            channels.append({
                "channel": ("fx", "fy", "fz", "mx", "my", "mz")[j],
                "weighted_gap_norm": gap_norm,
                "weighted_projected_norm": float(np.sqrt(np.dot(w, projected ** 2))),
                "weighted_unresolved_norm": residual,
                "unresolved_fraction": residual / gap_norm if gap_norm else 0.0,
                "max_abs_gap": float(np.max(np.abs(gap[:, j]))),
                "max_abs_weak_row": float(np.max(np.abs(rows))),
            })
        candidates[name] = channels
    return {
        "status": "SAVED_HISTORICAL_MODE_PROJECTION_ONLY",
        "source_git_of_saved_mode": saved["source_git"],
        "saved_beta": saved["beta"],
        "saved_shell_work": saved["shell_work_sq"],
        "saved_beam_work": saved["beam_work_sq"],
        "saved_work_parity_error":
            abs(saved["pairing_work_sq"] - saved["action_work_sq"]),
        "candidate_projections": candidates,
        "interpretation_limit": (
            "Historical zero-width material-line linearization and selective-Fz "
            "least-action field; neither the prospective L1 law nor a "
            "constrained-system or mesh-uniform stability assessment."),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("saved", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = analyze(json.loads(args.saved.read_text()))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({name: {row["channel"]: round(row["unresolved_fraction"], 6)
                             for row in channels}
                      for name, channels in result["candidate_projections"].items()}))
