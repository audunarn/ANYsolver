"""Read-only Q6 default-to-nested-x sensitivity, without a convergence claim."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_precise_functional import from_qp_recovery_precise
from scripts._b3_e4_f03_qp_piecewise_functional import PiecewiseFunctional, comparison
from scripts.b3_e4_f03_qp_nested_x_adjudicate import _signed


def run(default_state: Path, default_scalars: Path, refined: Path) -> dict:
    with np.load(default_state) as arrays:
        q = np.array(arrays["q"], copy=True)
        eta = np.array(arrays["eta"], copy=True)
    old = json.loads(default_scalars.read_text(encoding="utf-8"))["cases"]["6"]
    new = json.loads(refined.read_text(encoding="utf-8"))
    trace = FinitePadQpTrace(6)
    if q.shape != (2 * trace.n,) or eta.shape != (3,) or new["degree"] != 6:
        raise ValueError("incompatible Q6 h-sensitivity input")
    if not all(x in new["x"] for x in trace.x):
        raise ValueError("X1 must exactly retain every X0 coordinate")
    if not np.allclose(trace.matrices(1., side="left")[0] @ q,
                       old["tip_pose"], rtol=0, atol=1e-12):
        raise ValueError("saved default state does not match signed outputs")
    old_functional = from_qp_recovery_precise(trace, q, eta).functional
    row = new["functional"]
    new_functional = PiecewiseFunctional(np.array(row["breaks"]),
        np.array(row["coefficients"]), np.array(row["cosine"]),
        np.array(row["atoms"]))
    first, second, difference = comparison(old_functional, new_functional)
    norms = [float(np.sqrt(first.squared_total)),
             float(np.sqrt(second.squared_total))]
    distance = float(np.sqrt(difference.squared_total))
    old_signed, new_signed = _signed({"signed": old}), _signed(new)
    signed = {}
    for key in old_signed:
        a, scale = old_signed[key]
        b, new_scale = new_signed[key]
        if scale != new_scale:
            raise ValueError("inconsistent h-sensitivity scale")
        signed[key] = {"default": a, "refined": b,
                       "absolute_change": abs(b-a),
                       "relative": abs(b-a) /
                           max(abs(a), abs(b), 1e-3*scale)}
    return {"status": "UNREGISTERED_Q6_H_SENSITIVITY",
            "default_state_sha256": hashlib.sha256(q.tobytes()).hexdigest(),
            "signed": signed,
            "max_signed_relative": max(v["relative"] for v in signed.values()),
            "functional_norms_n": norms,
            "functional_distance_n": distance,
            "functional_relative": distance / max(*norms, 1000.),
            "qualification_status": "F03_G0B_OPEN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("default_state", type=Path)
    parser.add_argument("default_scalars", type=Path)
    parser.add_argument("refined", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.default_state, args.default_scalars, args.refined)
    args.output.write_text(json.dumps(result, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"max_signed_relative": result["max_signed_relative"],
                      "functional_distance_n": result["functional_distance_n"],
                      "functional_relative": result["functional_relative"]}))


if __name__ == "__main__":
    main()
