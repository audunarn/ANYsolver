"""Read-only unchanged-rule adjudication of an unregistered Q6 x-grid pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_precise_functional import from_qp_recovery_precise
from scripts._b3_e4_f03_qp_piecewise_functional import (
    PiecewiseFunctional, comparison,
)
from scripts.b3_e4_f03_qp_nested_x_adjudicate import _signed
from scripts.b3_e4_f03_qp_nested_x_pilot import refined_x, refined_x2


def _functional(row):
    return PiecewiseFunctional(np.array(row["breaks"]),
        np.array(row["coefficients"]), np.array(row["cosine"]),
        np.array(row["atoms"]))


def adjudicate(default_state: Path, default_scalars: Path,
               x1_path: Path, x2_path: Path) -> dict:
    with np.load(default_state) as arrays:
        q0 = np.array(arrays["q"], copy=True)
        eta0 = np.array(arrays["eta"], copy=True)
    original = json.loads(default_scalars.read_text(encoding="utf-8"))
    x1 = json.loads(x1_path.read_text(encoding="utf-8"))
    x2 = json.loads(x2_path.read_text(encoding="utf-8"))
    if (original["status"] != "UNREGISTERED_DIAGNOSTIC" or
            x1["status"] != "UNREGISTERED_NESTED_X_PILOT" or
            x2["status"] != "UNREGISTERED_NESTED_X2_PILOT" or
            x1["degree"] != 6 or x2["degree"] != 6):
        raise ValueError("wrong fixed-Q6 pilot input")
    trace0 = FinitePadQpTrace(6)
    if (q0.shape != (2*trace0.n,) or eta0.shape != (3,) or
            x1["x_hex"] != [x.hex() for x in refined_x()] or
            x2["x_hex"] != [x.hex() for x in refined_x2()] or
            x1["y_hex"] != x2["y_hex"] or
            x1["y_hex"] != [y.hex() for y in trace0.y] or
            not all(x in x1["x"] for x in trace0.x) or
            not all(x in x2["x"] for x in x1["x"])):
        raise ValueError("fixed nested x-grid or physical state mismatch")
    row0 = original["cases"]["6"]
    if (not np.array_equal(eta0, np.asarray(row0["eta"])) or
            not np.allclose(trace0.matrices(1., side="left")[0]@q0,
                            row0["tip_pose"], rtol=0, atol=1e-12)):
        raise ValueError("default raw state does not match signed outputs")
    signed_rows = tuple(_signed({"signed": row}) for row in
                        (row0, x1["signed"], x2["signed"]))
    signed = {}
    failures = []
    for name in signed_rows[0]:
        values = [signed_rows[i][name][0] for i in range(3)]
        scale = signed_rows[0][name][1]
        if any(signed_rows[i][name][1] != scale for i in (1, 2)):
            raise ValueError("inconsistent signed normalization")
        first, last = abs(values[1]-values[0]), abs(values[2]-values[1])
        relative = (first/max(abs(values[0]), abs(values[1]), 1e-3*scale),
                    last/max(abs(values[1]), abs(values[2]), 1e-3*scale))
        relative_pass = all(value <= .01 for value in relative)
        settling_pass = last <= first + 1e-5*scale
        signed[name] = {"values": values, "scale": scale,
                        "absolute_changes": [first, last],
                        "pair_relative": relative,
                        "one_percent_pass": relative_pass,
                        "absolute_change_pass": settling_pass}
        if not relative_pass or not settling_pass:
            failures.append(name)
    f0 = from_qp_recovery_precise(trace0, q0, eta0).functional
    f1, f2 = _functional(x1["functional"]), _functional(x2["functional"])
    a, b, ab = comparison(f0, f1)
    b2, c, bc = comparison(f1, f2)
    norms = [float(np.sqrt(x.squared_total)) for x in (a, b, c)]
    if abs(b2.squared_total-b.squared_total) > 1e-10*max(1., b.squared_total):
        raise ArithmeticError("shared X1 functional norm changed")
    differences = [float(np.sqrt(ab.squared_total)),
                   float(np.sqrt(bc.squared_total))]
    relative = [differences[0]/max(norms[0], norms[1], 1000.),
                differences[1]/max(norms[1], norms[2], 1000.)]
    functional_pass = (all(value <= .01 for value in relative) and
                       differences[1] <= differences[0]+10.)
    return {"status": "UNREGISTERED_Q6_H_ADJUDICATION",
            "default_state_sha256": hashlib.sha256(q0.tobytes()).hexdigest(),
            "signed_count": len(signed), "signed": signed,
            "signed_failures": failures,
            "functional": {"norms_n": norms,
                           "differences_n": differences,
                           "relative_changes": relative,
                           "pass": functional_pass},
            "draft_settling_screen_pass": not failures and functional_pass,
            "qualification_status": "F03_G0B_OPEN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("default_state", type=Path)
    parser.add_argument("default_scalars", type=Path)
    parser.add_argument("x1_q6", type=Path)
    parser.add_argument("x2_q6", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = adjudicate(args.default_state, args.default_scalars,
                        args.x1_q6, args.x2_q6)
    args.output.write_text(json.dumps(result, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"signed_failures": result["signed_failures"],
                      "functional": result["functional"],
                      "draft_settling_screen_pass":
                          result["draft_settling_screen_pass"]}))


if __name__ == "__main__":
    main()
