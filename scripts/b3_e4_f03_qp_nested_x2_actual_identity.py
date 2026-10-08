"""Reassemble saved Q6 h pilot states to audit actual-case nested work."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import threading
from time import perf_counter

import numpy as np
import psutil

from scripts._b3_e4_f03_conforming_qp_energy import assemble
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0, U0, YAW_LENGTH
from scripts._b3_e4_f03_qp_nested_identity import evaluate_nested_identity
from scripts.b3_e4_f03_qp_nested_x_pilot import refined_x, refined_x2


def _peak_sampler(stop, peak):
    process = psutil.Process()
    while not stop.is_set():
        peak[0] = max(peak[0], process.memory_info().rss)
        stop.wait(.25)
    peak[0] = max(peak[0], process.memory_info().rss)


def _state(operators, full, eta, signed):
    if not np.array_equal(eta, np.asarray(signed["eta"])):
        raise ValueError("saved root multiplier does not match signed output")
    q = full[operators.free_columns]
    stiffness = operators.shell_stiffness + operators.beam_stiffness
    shell_energy = float(q @ operators.shell_stiffness @ q / 2)
    beam_energy = float(q @ operators.beam_stiffness @ q / 2)
    work = float(operators.load @ q)
    tip = operators.tip_pose @ q
    residual = stiffness @ q + operators.root_constraint.T @ eta - operators.load
    d = np.sqrt(E0/stiffness.diagonal())
    pose_scale = np.array((1/U0, 1/U0, YAW_LENGTH/U0))
    return q, {
        "free_state_sha256": hashlib.sha256(q.tobytes()).hexdigest(),
        "shell_energy_j": shell_energy,
        "beam_energy_j": beam_energy,
        "external_work_j": work,
        "tip_pose": tip.tolist(),
        "root_reaction_physical": (-eta).tolist(),
        "signed_shell_energy_defect_scaled":
            abs(shell_energy-signed["shell_energy_j"])/E0,
        "signed_beam_energy_defect_scaled":
            abs(beam_energy-signed["beam_energy_j"])/E0,
        "signed_work_defect_scaled":
            abs(work-signed["external_work_j"])/E0,
        "signed_tip_defect_scaled": float(np.max(np.abs(
            pose_scale*(tip-np.asarray(signed["tip_pose"]))))),
        "free_equilibrium_scaled": float(np.max(np.abs(d*residual/E0))),
        "root_compatibility_scaled": float(np.max(np.abs(
            pose_scale*(operators.root_constraint@q)))),
        "shell_nnz": operators.shell_stiffness.nnz,
        "beam_nnz": operators.beam_stiffness.nnz,
    }


def run(default_state, default_scalars, x1_path, x2_path):
    x1 = json.loads(Path(x1_path).read_text(encoding="utf-8"))
    x2 = json.loads(Path(x2_path).read_text(encoding="utf-8"))
    old = json.loads(Path(default_scalars).read_text(encoding="utf-8"))["cases"]["6"]
    with np.load(default_state) as arrays:
        full0 = np.array(arrays["q"], copy=True)
        eta0 = np.array(arrays["eta"], copy=True)
    traces = (FinitePadQpTrace(6), FinitePadQpTrace(6, x=refined_x()),
              FinitePadQpTrace(6, x=refined_x2()))
    if (x1["status"] != "UNREGISTERED_NESTED_X_PILOT" or
            x2["status"] != "UNREGISTERED_NESTED_X2_PILOT" or
            x1["x_hex"] != [x.hex() for x in traces[1].x] or
            x2["x_hex"] != [x.hex() for x in traces[2].x] or
            full0.shape != (2*traces[0].n,) or
            not np.isfinite(full0).all() or not np.isfinite(eta0).all()):
        raise ValueError("incompatible saved Q6 h states")
    full = [full0]
    for trace, record in zip(traces[1:], (x1, x2), strict=True):
        q = np.array(record["free_state"])
        if (q.shape != (len(trace.free_columns),) or
                hashlib.sha256(q.tobytes()).hexdigest() !=
                record["free_state_sha256"]):
            raise ValueError("saved reduced state hash mismatch")
        state = np.zeros(2*trace.n)
        state[trace.free_columns] = q
        full.append(state)
    etas = (eta0, np.array(x1["root_multiplier"]),
            np.array(x2["root_multiplier"]))
    signed = (old, x1["signed"], x2["signed"])
    stop = threading.Event()
    peak = [psutil.Process().memory_info().rss]
    sampler = threading.Thread(target=_peak_sampler, args=(stop, peak),
                               daemon=True)
    sampler.start()
    try:
        operators, times, rows, reduced = [], [], [], []
        for trace, state, eta, row in zip(traces, full, etas, signed,
                                          strict=True):
            start = perf_counter()
            op = assemble(trace)
            times.append(perf_counter()-start)
            q, audit = _state(op, state, eta, row)
            operators.append(op)
            reduced.append(q)
            rows.append(audit)
        identities = [asdict(evaluate_nested_identity(
            operators[i], operators[i+1], reduced[i], reduced[i+1]))
            for i in (0, 1)]
        for row in rows:
            if max(row[key] for key in (
                    "signed_shell_energy_defect_scaled",
                    "signed_beam_energy_defect_scaled",
                    "signed_work_defect_scaled",
                    "signed_tip_defect_scaled",
                    "free_equilibrium_scaled",
                    "root_compatibility_scaled")) > 1e-10:
                raise ArithmeticError("saved state or operator check failed")
        for identity in identities:
            if (identity["fine_energy"] <
                    identity["coarse_energy"]-1e-10*E0 or
                    max(identity[key] for key in (
                        "defect_scaled", "load_embedding_scaled",
                        "root_embedding_scaled", "tip_embedding_scaled")) > 1e-10):
                raise ArithmeticError("actual Q6 h-nested identity failed")
    finally:
        stop.set()
        sampler.join(timeout=2.)
    return {"status": "UNREGISTERED_ACTUAL_Q6_H_IDENTITY",
            "source": "saved X0/X1/X2 states reassembled",
            "assembly_times_s": times,
            "sampled_peak_rss_bytes": peak[0],
            "cases": dict(zip(("X0", "X1", "X2"), rows, strict=True)),
            "identities": dict(zip(("X0_to_X1", "X1_to_X2"),
                                   identities, strict=True)),
            "qualification_status": "F03_G0B_OPEN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("default_state", type=Path)
    parser.add_argument("default_scalars", type=Path)
    parser.add_argument("x1_q6", type=Path)
    parser.add_argument("x2_q6", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.default_state, args.default_scalars,
                 args.x1_q6, args.x2_q6)
    args.output.write_text(json.dumps(result, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"assembly_times_s": result["assembly_times_s"],
                      "sampled_peak_rss_bytes": result["sampled_peak_rss_bytes"],
                      "identities": result["identities"]}))


if __name__ == "__main__":
    main()
