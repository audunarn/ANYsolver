"""Read-only adjudication of one unregistered Q4/Q5/Q6 nested-x pilot.

The criteria are the unchanged draft signed-scalar and full-functional
settling rules. A passed pilot alone is not a scientific or G0 gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_primal_ritz import E0, F0, U0, YAW_LENGTH
from scripts._b3_e4_f03_qp_piecewise_functional import (
    PiecewiseFunctional, comparison,
)


WRENCH_SCALE = np.array((F0, F0, F0 * YAW_LENGTH))
POSE_SCALE = np.array((U0, U0, U0 / YAW_LENGTH))
VECTOR_FIELDS = ("tip_pose", "eta", "root_section", "tip_section",
                 "root_atom", "tip_atom", "line_wrench")
ENERGY_FIELDS = ("shell_energy_j", "beam_energy_j", "total_energy_j",
                 "external_work_j")
BAND_NAMES = ("quarter_1", "quarter_2", "quarter_3", "quarter_4",
              "0_to_1_over_32", "1_over_32_to_1_over_16",
              "15_over_16_to_31_over_32", "31_over_32_to_1")


def _read(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "UNREGISTERED_NESTED_X_PILOT":
        raise ValueError("unexpected pilot status")
    return record


def _signed(record: dict) -> dict[str, tuple[float, float]]:
    row = record["signed"]
    result = {}
    for key in ENERGY_FIELDS:
        result[key] = (float(row[key]), E0)
    for key in VECTOR_FIELDS:
        scale = POSE_SCALE if key == "tip_pose" else WRENCH_SCALE
        for i, (value, unit) in enumerate(zip(row[key], scale, strict=True)):
            result[f"{key}[{i}]"] = (float(value), float(unit))
    for name, values in zip(BAND_NAMES, row["bands"], strict=True):
        for i, (value, unit) in enumerate(zip(values, WRENCH_SCALE,
                                              strict=True)):
            result[f"{name}[{i}]"] = (float(value), float(unit))
    if len(result) != 49 or not all(np.isfinite(value) and np.isfinite(scale)
                                  and scale > 0 for value, scale in
                                  result.values()):
        raise ValueError("incomplete or nonfinite signed holdout")
    return result


def _functional(record: dict) -> PiecewiseFunctional:
    row = record["functional"]
    return PiecewiseFunctional(np.array(row["breaks"]),
        np.array(row["coefficients"]), np.array(row["cosine"]),
        np.array(row["atoms"]))


def adjudicate(paths: tuple[Path, Path, Path]) -> dict:
    rows = tuple(map(_read, paths))
    if tuple(row["degree"] for row in rows) != (4, 5, 6):
        raise ValueError("pilot requires Q4, Q5, Q6 in order")
    if not all(row["x_hex"] == rows[0]["x_hex"] and
               row["y_hex"] == rows[0]["y_hex"] and
               row["station_intervals"] == rows[0]["station_intervals"]
               for row in rows[1:]):
        raise ValueError("pilot levels do not share the exact fixed grid")
    inventory = tuple(_signed(row) for row in rows)
    signed = {}
    failures = []
    for key in inventory[0]:
        values = [inventory[i][key][0] for i in range(3)]
        scale = inventory[0][key][1]
        if any(inventory[i][key][1] != scale for i in range(1, 3)):
            raise ValueError("inconsistent signed scale")
        first, last = abs(values[1] - values[0]), abs(values[2] - values[1])
        pair_relative = (first / max(abs(values[0]), abs(values[1]),
                                     1e-3 * scale),
                         last / max(abs(values[1]), abs(values[2]),
                                    1e-3 * scale))
        pair_pass = all(value <= .01 for value in pair_relative)
        settling_pass = last <= first + 1e-5 * scale
        signed[key] = {"values": values, "scale": scale,
                       "absolute_changes": [first, last],
                       "pair_relative": pair_relative,
                       "one_percent_pass": pair_pass,
                       "absolute_change_pass": settling_pass}
        if not pair_pass or not settling_pass:
            failures.append(key)
    functionals = tuple(map(_functional, rows))
    first = comparison(functionals[0], functionals[1])
    second = comparison(functionals[1], functionals[2])
    differences = [float(np.sqrt(first[2].squared_total)),
                   float(np.sqrt(second[2].squared_total))]
    norms = [float(np.sqrt(first[0].squared_total)),
             float(np.sqrt(first[1].squared_total)),
             float(np.sqrt(second[1].squared_total))]
    relative = [differences[0] / max(norms[0], norms[1], 1000.),
                differences[1] / max(norms[1], norms[2], 1000.)]
    functional_pass = (all(value <= .01 for value in relative) and
                       differences[1] <= differences[0] + 10.)
    return {"status": "UNREGISTERED_PILOT_ADJUDICATION",
            "signed_count": len(signed), "signed": signed,
            "signed_failures": failures,
            "functional": {"norms_n": norms,
                           "differences_n": differences,
                           "relative_changes": relative,
                           "pass": functional_pass},
            "draft_settling_screen_pass": not failures and functional_pass,
            "qualification_status": "F03_G0B_OPEN"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("q4", type=Path)
    parser.add_argument("q5", type=Path)
    parser.add_argument("q6", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = adjudicate((args.q4, args.q5, args.q6))
    args.output.write_text(json.dumps(result, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"signed_failures": result["signed_failures"],
                      "functional": result["functional"],
                      "draft_settling_screen_pass":
                          result["draft_settling_screen_pass"]}))


if __name__ == "__main__":
    main()
