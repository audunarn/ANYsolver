"""Independent active-subset solve of a retained linearized pressure map."""

from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path

import numpy as np


def solve(snapshot: Path, output: Path, *, index: int = 7) -> None:
    if output.exists():
        raise FileExistsError(output)
    with np.load(snapshot) as data:
        pressure = data[f"pressure_{index}"].copy()
        gap = data[f"gap_{index}"].copy()
        response = data[f"response_{index}"].copy()
    candidates = []
    terminal = (7, 8, 16, 17)
    all_modes = np.arange(len(pressure))
    for count in range(1, len(terminal)+1):
        for subset in combinations(terminal, count):
            active = np.asarray(subset, dtype=int)
            block = response[np.ix_(active, active)]
            condition = float(np.linalg.cond(block))
            if not np.isfinite(condition) or condition > 1.0e12:
                continue
            candidate = np.zeros_like(pressure)
            candidate[active] = np.linalg.solve(
                block, -gap[active]+response[active] @ pressure,
            )
            new_gap = gap+response @ (candidate-pressure)
            projected_residual = np.maximum(
                0.0, candidate-10000.0*new_gap,
            )-candidate
            inactive = np.setdiff1d(all_modes, active)
            candidates.append({
                "active_indices": list(map(int, subset)),
                "active_pressure_pa": candidate[active].tolist(),
                "minimum_active_pressure_pa": float(np.min(candidate[active])),
                "minimum_inactive_gap_m": float(np.min(new_gap[inactive])),
                "projected_residual_inf_pa": float(np.max(np.abs(projected_residual))),
                "active_response_condition": condition,
                "largest_step_pa": float(np.max(np.abs(candidate-pressure))),
            })
    candidates.sort(key=lambda item: item["projected_residual_inf_pa"])
    record = {"snapshot": str(snapshot), "index": index,
              "candidate_count": len(candidates), "best": candidates[:4]}
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["best"][0], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--index", type=int, default=7)
    args = parser.parse_args()
    solve(args.snapshot, args.output, index=args.index)
