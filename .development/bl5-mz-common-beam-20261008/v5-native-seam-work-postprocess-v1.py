"""Extract station-conjugate native virtual work from saved V5 arrays only."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
JUMP = HERE / "v5-retained-jump-postprocess-v1.json"
MATERIAL = HERE / "case-v5/material.json"
RESULT = HERE / "case-v5/result.json"
TARGET = HERE / "v5-native-seam-work-postprocess-v1.json"


def load(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def main() -> None:
    if TARGET.exists():
        raise SystemExit("Postprocessing record exists; preserve it")
    jump, jump_sha = load(JUMP)
    material, material_sha = load(MATERIAL)
    result, result_sha = load(RESULT)
    if (jump.get("identity") != "BL5_V5_SAVED_RETAINED_JUMP_POSTPROCESS_V1"
            or result.get("status") != "DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED"
            or len(material.get("elements", ())) != 2):
        raise ValueError("Unexpected saved V5 identities or element layout")

    # Retained physical-fibre order from _ge_beam3_retained_fibre.py:
    # six chord forces, then four three-component end moments. For each
    # neighboring half-cell, the right-end log has positive sign and the
    # next left-end log has negative sign. At the virgin reference the log
    # derivative is identity. Their p rows balance at the shared nodal
    # rotation, leaving the reference-linearized first variation
    #   -p_left . delta(phi_left) + p_right . delta(phi_right).
    elements = [row["resultants"] for row in material["elements"]]
    pairs = ((0, 9, 0, 12), (0, 15, 1, 6), (1, 9, 1, 12))
    rows = []
    for station, (le, li, re, ri) in zip(jump["stations"], pairs):
        left = elements[le][li:li + 3]
        right = elements[re][ri:ri + 3]
        if len(left) != 3 or len(right) != 3:
            raise ValueError("Incomplete saved retained moment")
        mismatch = [a - b for a, b in zip(left, right)]
        mismatch_norm = math.sqrt(sum(v * v for v in mismatch))
        average = [(a + b) / 2 for a, b in zip(left, right)]
        jump_spin = station["spin_jump_rad"]
        work = math.fsum(a * b for a, b in zip(average, jump_spin))
        rows.append(dict(x_m=station["x_m"],
                         left_moment_Nm=left, right_moment_Nm=right,
                         moment_balance_norm_Nm=mismatch_norm,
                         retained_spin_jump_rad=jump_spin,
                         balanced_first_variation_work_J=work))

    total = math.fsum(row["balanced_first_variation_work_J"] for row in rows)
    difference = result["work_difference_J"]
    record = dict(identity="BL5_V5_SAVED_NATIVE_SEAM_WORK_POSTPROCESS_V1",
                  source_sha256={"jump": jump_sha, "material": material_sha,
                                 "result": result_sha}, solver_executions=0,
                  stations=rows, sum_balanced_first_variation_work_J=total,
                  v5_body_work_difference_J=difference,
                  scale_ratio_to_v5_work_difference=abs(total / difference),
                  interpretation=("This is native retained-coordinate virtual work "
                                  "for the saved independent one-sided spin field. "
                                  "It is not a strain-energy partition, continuum "
                                  "traction work, or a causal allocation of the V5 "
                                  "body-work difference. A physical two-sided cut "
                                  "reference must still recover face actions and seam work."))
    TARGET.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(max_station_m=max(rows, key=lambda row: abs(row["balanced_first_variation_work_J"]))["x_m"],
                          sum_work_J=total,
                          ratio=record["scale_ratio_to_v5_work_difference"],
                          max_moment_imbalance_Nm=max(row["moment_balance_norm_Nm"] for row in rows))))


if __name__ == "__main__":
    main()
