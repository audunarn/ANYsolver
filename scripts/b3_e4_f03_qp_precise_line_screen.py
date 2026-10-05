"""Compare fast coefficient-space line integrals with the original trace route."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0, YAW_LENGTH
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_precise_functional import from_qp_recovery_precise
from scripts._b3_e4_f03_qp_precise_line_adjoint import PreciseLineAreaAdjoint
from scripts.b3_e4_f03_qp_nested_x_pilot import refined_x2


WINDOWS = ((0., 1.), (0., .25), (.25, .5), (.5, .75), (.75, 1.),
           (0., 1/32), (1/32, 1/16), (15/16, 31/32), (31/32, 1.),
           (.15, .25), (.31, .42), (.71, .79), (.85, .95))
SCALE = np.array((F0, F0, F0*YAW_LENGTH, F0, F0*YAW_LENGTH))


def run(path):
    row = json.loads(Path(path).read_text(encoding="utf-8"))
    trace = FinitePadQpTrace(6, x=refined_x2())
    if row["x_hex"] != [x.hex() for x in trace.x]:
        raise ValueError("saved X2 grid mismatch")
    q = np.zeros(2*trace.n)
    q[trace.free_columns] = row["free_state"]
    eta = np.asarray(row["root_multiplier"])
    original = FinitePadAreaAdjoint(trace, q, eta)
    functional = from_qp_recovery_precise(trace, q, eta).functional
    fast = PreciseLineAreaAdjoint(trace, q, eta, functional)
    checks = []
    for left, right in WINDOWS:
        old, new = original.integrated_line(left, right), fast.integrated_line(
            left, right)
        gap = float(np.max(np.abs(old-new)/SCALE))
        checks.append({"left": left, "right": right,
                       "reference": old.tolist(), "precise": new.tolist(),
                       "gap_scaled": gap})
    maximum = max(row["gap_scaled"] for row in checks)
    if maximum > 2e-10:
        raise ArithmeticError(f"coefficient-space line integrals differ: {maximum}")
    return {"status": "UNREGISTERED_X2_Q6_PRECISE_LINE_SCREEN",
            "qualification_status": "F03_G0B_OPEN",
            "input_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "maximum_gap_scaled": maximum, "windows": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.state)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"maximum_gap_scaled": result["maximum_gap_scaled"],
                      "windows": len(result["windows"])}))


if __name__ == "__main__":
    main()
