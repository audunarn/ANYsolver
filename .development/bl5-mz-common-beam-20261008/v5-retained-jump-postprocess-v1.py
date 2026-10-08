"""Postprocess the preserved V5 native solution; never launch a solver."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "case-v5/beam-solved.json"
TARGET = HERE / "v5-retained-jump-postprocess-v1.json"


def main() -> None:
    if TARGET.exists():
        raise SystemExit("Postprocessing record exists; preserve it")
    raw = SOURCE.read_bytes()
    report = json.loads(raw)
    if report.get("status") != "DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED":
        raise ValueError("V5 solved-body status changed")
    q = report["physical_coordinates"]
    if len(q) != 78 or not all(math.isfinite(value) for value in q):
        raise ValueError("Expected finite 30-nodal/48-retained V5 layout")

    # Five shared beam nodes occupy 30 coordinates. Each of two members has
    # two three-component retained cell spins, followed by 18 resultants.
    # The common node at x=.5 joins two different native members.
    stations = ((.25, 1, 30, 33), (.5, 2, 33, 54), (.75, 3, 54, 57))
    rows = []
    for x, node, left, right in stations:
        left_spin = q[left:left + 3]
        right_spin = q[right:right + 3]
        jump = [b - a for a, b in zip(left_spin, right_spin)]
        corners = []
        for y in (-.02, .02):
            for z in (-.03, .03):
                # Conditional rigid-section lift: delta u = delta phi cross r.
                slip = (jump[1] * z - jump[2] * y,
                        -jump[0] * z, jump[0] * y)
                corners.append(math.sqrt(sum(value * value for value in slip)))
        rows.append(dict(x_m=x, node_spin_rad=q[6 * node + 3:6 * node + 6],
                         left_cell_spin_rad=left_spin,
                         right_cell_spin_rad=right_spin,
                         spin_jump_rad=jump,
                         spin_jump_norm_rad=math.sqrt(sum(value * value for value in jump)),
                         max_rigid_section_corner_slip_m=max(corners)))

    result = dict(identity="BL5_V5_SAVED_RETAINED_JUMP_POSTPROCESS_V1",
                  source="case-v5/beam-solved.json",
                  source_sha256=hashlib.sha256(raw).hexdigest(),
                  solver_executions=0,
                  section_width_m=.04, section_height_m=.06,
                  largest_jump_station_m=max(rows, key=lambda row: row["spin_jump_norm_rad"])["x_m"],
                  stations=rows,
                  interpretation=("The saved native retained spins have one-sided values. "
                                  "Corner slip is a conditional rigid-section lift, not a "
                                  "measured physical seam gap or a matched solid solution. "
                                  "A two-sided reference must specify seam work before its "
                                  "compliance can allocate the V5 work difference."))
    TARGET.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(largest_jump_station_m=result["largest_jump_station_m"],
                          max_spin_jump_norm_rad=max(row["spin_jump_norm_rad"] for row in rows),
                          max_corner_slip_m=max(row["max_rigid_section_corner_slip_m"] for row in rows))))


if __name__ == "__main__":
    main()
