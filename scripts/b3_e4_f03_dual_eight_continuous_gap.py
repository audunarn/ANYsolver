"""Is the saved dual-eight null traction a continuous-law identity?"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
from time import monotonic

import numpy as np
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace


NULL_MODES = Path(
    "docs/agent_plans/B3_GE_E4_PL_F03_COMMON_TRACE_NULL_MODES_20260927.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(rows: list, kind: str) -> dict:
    coefficient = np.asarray(rows, dtype=float)
    intervals = len(coefficient)-1
    space = LineMultiplierSpace(kind, tuple(np.linspace(0., 1., intervals+1)))
    roots, weights = np.polynomial.legendre.leggauss(16)
    l2_gap = 0.
    l2_envelope = 0.
    max_relative_pointwise = 0.
    numerator = np.zeros(9)
    denominator = np.zeros(9)
    for index in range(intervals):
        low = .9+.1*index/intervals
        high = .9+.1*(index+1)/intervals
        for root, weight in zip(roots, weights):
            x = (low+high)/2+(high-low)*root/2
            phi = space.values((x-.9)/.1)
            force_term = float(phi@coefficient[:, 2])
            moment_term = float(-(x-.95)*(phi@coefficient[:, 4]))
            combined = force_term+moment_term
            envelope = abs(force_term)+abs(moment_term)
            dx = float(weight*(high-low)/2)
            l2_gap += dx*combined**2
            l2_envelope += dx*envelope**2
            max_relative_pointwise = max(
                max_relative_pointwise,
                abs(combined)/max(envelope, 1e-30))
            xi = (x-.95)/.05
            fields = np.r_[np.array([xi**p for p in range(7)]),
                           np.sin(np.pi*xi), np.cos(np.pi*xi)]
            numerator += dx*combined*fields
            denominator += dx*envelope*np.abs(fields)
    if l2_envelope <= 0.:
        raise ArithmeticError("saved null traction has no normal-position action")
    labels = [f"polynomial_degree_{p}" for p in range(7)]+[
        "sine", "cosine"]
    return {
        "relative_continuous_l2_action": float(np.sqrt(l2_gap/l2_envelope)),
        "max_relative_pointwise_action": max_relative_pointwise,
        "smooth_field_pairings": {
            label: {"signed_action": float(numerator[i]),
                    "relative_to_absolute_terms": float(
                        abs(numerator[i])/max(denominator[i], 1e-30))}
            for i, label in enumerate(labels)},
        "quadrature_order_per_interval": 16,
    }


def evaluate() -> dict:
    started = monotonic()
    saved = json.loads(NULL_MODES.read_text())
    cases = {}
    for beam in (12, 24):
        for kind in ("continuous_linear", "dual_linear"):
            key = f"b3_half_{beam}_{kind}_8"
            cases[key] = _case(
                saved["cases"][key]["raw_dual_by_basis"], kind)
    p1 = [value["relative_continuous_l2_action"]
          for key, value in cases.items() if "continuous_linear" in key]
    dual = [value["relative_continuous_l2_action"]
            for key, value in cases.items() if "dual_linear" in key]
    if max(p1) > 1e-10:
        raise ArithmeticError("analytic P1 continuous identity failed")
    if min(dual) < 1e-4:
        raise ArithmeticError("dual-eight continuous versus discrete question unresolved")
    return {
        "classification": "bounded continuous-gap action of saved null tractions; no F03 selection",
        "question": "Does the dual-eight discrete null act on a smooth gap that the current primal trace cannot represent?",
        "source_null_modes_sha256": _sha(NULL_MODES),
        "model": "same normalized saved P1/dual-eight left modes; scalar normal gap over x=.9..1",
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["scalar smooth-gap check isolates mean-z/first-y channels only",
                        "not a proof of uniform stability or physical locking"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded continuous-gap check exceeded 120 s")
    result["source_sha256"] = _sha(Path(__file__))
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"cases": {key: {
        "relative_continuous_l2_action": value["relative_continuous_l2_action"],
        "max_relative_pointwise_action": value["max_relative_pointwise_action"],
        "max_smooth_pairing": max(v["relative_to_absolute_terms"]
                                  for v in value["smooth_field_pairings"].values())}
        for key, value in result["cases"].items()},
        "elapsed_s": result["elapsed_s_not_benchmark"]}, sort_keys=True))


if __name__ == "__main__":
    main()
