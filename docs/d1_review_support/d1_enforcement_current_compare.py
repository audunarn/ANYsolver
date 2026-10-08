"""Summarize three paired complete D1 route runs without new solves."""

import json
from pathlib import Path
import statistics

import numpy as np


root = Path(__file__).resolve().parent
records = {}
resources = {}
for mode in ("nested", "monolithic"):
    records[mode] = [
        json.loads((root / f"d1_enforcement_{mode}_{i}_20260929.json").read_text())
        for i in (1, 2, 3)
    ]
    resources[mode] = [
        json.loads((root / f"d1_enforcement_{mode}_{i}_resource_20260929.json").read_text())
        for i in (1, 2, 3)
    ]
all_runs = records["nested"]+records["monolithic"]
source_commits = {run["source_commit"] for run in all_runs}
environment = {
    (run["python"], run["numpy"], run["scipy"],
     run["openblas_threads"], run["omp_threads"])
    for run in all_runs
}
if len(source_commits) != 1 or len(environment) != 1:
    raise AssertionError("source or numerical environment differs")
if any(run["status"] != "completed" or run["accepted_steps"] != 2
       for run in all_runs):
    raise AssertionError("one route did not complete its two steps")
if any(resource["status"] != "completed" or resource["exit_code"] != 0
       for group in resources.values() for resource in group):
    raise AssertionError("one bounded process failed")
if len({run["normal_stiffness_pa_per_m"] for run in all_runs}) != 1:
    raise AssertionError("normal regularization differs")
if len({run["gap_tolerance_m"] for run in all_runs}) != 1:
    raise AssertionError("physical gap setting differs")

parity = []
for nested, monolithic in zip(records["nested"], records["monolithic"]):
    if len(nested["step_summary"]) != len(monolithic["step_summary"]):
        raise AssertionError("step histories differ")
    parity.append({
        "maximum_absolute_displacement_difference": float(np.max(np.abs(
            np.asarray(nested["displacements_mixed_dof"])
            - np.asarray(monolithic["displacements_mixed_dof"])
        ))),
        "maximum_absolute_contact_force_difference_n": max(
            float(np.max(np.abs(
                np.asarray(a["contact_force_n"])
                - np.asarray(b["contact_force_n"])
            ))) for a, b in zip(
                nested["step_summary"], monolithic["step_summary"],
            )
        ),
        "maximum_absolute_pressure_difference_pa": max(
            float(np.max(np.abs(
                np.asarray(a["numerical_pressure_pa"])
                - np.asarray(b["numerical_pressure_pa"])
            ))) for a, b in zip(
                nested["step_summary"], monolithic["step_summary"],
            )
        ),
        "maximum_absolute_minimum_gap_difference_m": max(
            abs(a["minimum_gap_m"]-b["minimum_gap_m"])
            for a, b in zip(
                nested["step_summary"], monolithic["step_summary"],
            )
        ),
    })

def series(mode, field, *, resource=False):
    group = resources[mode] if resource else records[mode]
    return [float(run[field]) for run in group]


nested_process = series("nested", "elapsed_seconds", resource=True)
monolithic_process = series("monolithic", "elapsed_seconds", resource=True)
out = {
    "source_commit": next(iter(source_commits)),
    "environment": list(next(iter(environment))),
    "run_order": ["nested_1", "monolithic_1", "monolithic_2",
                  "nested_2", "nested_3", "monolithic_3"],
    "nested": {
        "process_seconds": nested_process,
        "solve_seconds": series("nested", "solve_seconds"),
        "peak_process_tree_memory_mb": series(
            "nested", "peak_process_tree_memory_mb", resource=True,
        ),
    },
    "monolithic": {
        "process_seconds": monolithic_process,
        "solve_seconds": series("monolithic", "solve_seconds"),
        "peak_process_tree_memory_mb": series(
            "monolithic", "peak_process_tree_memory_mb", resource=True,
        ),
        "candidate_evaluations_per_step": [
            [row["candidate_evaluations"] for row in run["step_summary"]]
            for run in records["monolithic"]
        ],
        "backtracks_per_step": [
            [row["backtracks"] for row in run["step_summary"]]
            for run in records["monolithic"]
        ],
    },
    "paired_parity": parity,
    "median_process_speed_ratio_nested_over_monolithic": (
        statistics.median(nested_process)
        / statistics.median(monolithic_process)
    ),
    "paired_process_speed_ratios": [
        a/b for a, b in zip(nested_process, monolithic_process)
    ],
    "median_peak_memory_mb": {
        mode: statistics.median(
            series(mode, "peak_process_tree_memory_mb", resource=True),
        ) for mode in ("nested", "monolithic")
    },
    "twofold_median_target_met": (
        statistics.median(nested_process)
        / statistics.median(monolithic_process) >= 2.0
    ),
}
output = root / "d1_enforcement_current_compare_20260929.json"
if output.exists():
    raise FileExistsError(output)
output.write_text(json.dumps(out, indent=2)+"\n", encoding="utf-8")
print(json.dumps({
    "source_commit": out["source_commit"],
    "median_process_speed_ratio": out[
        "median_process_speed_ratio_nested_over_monolithic"],
    "twofold_target_met": out["twofold_median_target_met"],
    "max_force_difference_n": max(
        row["maximum_absolute_contact_force_difference_n"] for row in parity),
}))
