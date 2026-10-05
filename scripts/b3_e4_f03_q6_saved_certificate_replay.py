"""Replay an unregistered Q6 numerical certificate from saved inputs only.

The replay does not assemble a model, factorize a matrix, or solve for state.
It does reuse the experimental interval kernel, so it is not an independent
arithmetic proof or a scientific qualification result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from scripts._b3_e4_f03_local_scientific_supervisor import (
    SupervisorLimits, frozen_thread_environment, supervise,
)
from scripts._b3_e4_f03_qp_h_contract import CASE_COUNTS, CASES, minimum_inverse_bytes
from scripts._b3_e4_f03_q6_system_archive import read_system
from scripts._b3_e4_f03_sparse_certificate import SparseBudget, certificate_a


_CASE_NNZ = {"X0": 1200496, "X1": 2034304, "X2": 3102845}
_CASE_WORK_BYTES = {"X0": 256*1024**2, "X1": 384*1024**2,
                    "X2": 512*1024**2}
_CASE_SECONDS = {"X0": 900., "X1": 1200., "X2": 1800.}


def _read_json(path: Path, max_bytes: int) -> tuple[dict, str]:
    with path.open("rb") as stream:
        payload = stream.read(max_bytes + 1)
    if not 0 < len(payload) <= max_bytes:
        raise ValueError("Q6 replay JSON exceeds declared byte bound")
    result = json.loads(payload)
    if type(result) is not dict:
        raise ValueError("Q6 replay JSON object required")
    return result, hashlib.sha256(payload).hexdigest()


def _inverse_snapshot(path: Path, expected_size: int) -> tuple[bytes, str]:
    with path.open("rb") as stream:
        payload = stream.read(expected_size + 1)
    if len(payload) != expected_size:
        raise ValueError("Q6 replay raw inverse size mismatch")
    return payload, hashlib.sha256(payload).hexdigest()


def _check_parent_source_identity(attempt_hash: str, result_path: Path) -> None:
    result, _ = _read_json(result_path, 1024*1024)
    if result.get("source_measurement_sha256") != attempt_hash:
        raise ArithmeticError("Q6 replay attempt/child source identity mismatch")


def child(source: Path, output: Path, case_id: str) -> None:
    measurement, measurement_hash = _read_json(
        source / "measurement.json", 1024*1024)
    if (measurement.get("case_id") != case_id or
            measurement.get("status") != "UNREGISTERED_Q6_FULL_CERTIFICATE_FEASIBILITY"):
        raise ValueError("Q6 replay source case/status mismatch")
    receipt, receipt_hash = _read_json(source / "receipt.json", 8192)
    if (receipt.get("reason") != "completed" or receipt.get("exit_code") != 0 or
            receipt.get("failure") is not None):
        raise ValueError("Q6 replay requires completed source receipt")
    order = CASE_COUNTS[case_id][2] + 3
    nnz = _CASE_NNZ[case_id]
    if measurement.get("kkt_order") != order or measurement.get("kkt_nnz") != nnz:
        raise ValueError("Q6 replay source KKT inventory mismatch")
    start = perf_counter()
    matrix, rhs, displacement_scale, multiplier_scale, archive_bytes = read_system(
        source / "scaled_system.npz", order=order, nnz=nnz,
        archive_sha256=measurement["scaled_system_archive_sha256"],
        kkt_rhs_sha256=measurement["scaled_kkt_rhs_sha256"])
    if measurement["scaled_system_archive_bytes"] != archive_bytes:
        raise ValueError("Q6 replay scaled-system archive size mismatch")
    candidate, candidate_hash = _read_json(
        source / "candidate_state.json", 1024*1024)
    if (candidate_hash != measurement["candidate_state_sha256"] or
            candidate.get("case_id") != case_id):
        raise ValueError("Q6 replay candidate-state identity mismatch")
    state = np.asarray(candidate.get("scaled_kkt_state"), dtype=np.float64)
    if state.shape != (order,) or not np.isfinite(state).all():
        raise ValueError("Q6 replay finite candidate state required")
    inverse_path = source / "inverse_float64.bin"
    inverse_bytes, inverse_hash = _inverse_snapshot(
        inverse_path, minimum_inverse_bytes(case_id))
    if (measurement["inverse_archive_bytes"] != minimum_inverse_bytes(case_id) or
            inverse_hash != measurement["inverse_archive_sha256"]):
        raise ValueError("Q6 replay raw inverse identity mismatch")
    load_seconds = perf_counter() - start
    inverse = np.frombuffer(inverse_bytes, dtype="<f8").reshape(order, order)

    def blocks():
        for first in range(0, order, 4):
            yield first, np.array(inverse[:, first:first+4], dtype=np.float64,
                                  order="C", copy=True)

    budget = SparseBudget(order, nnz, 4, _CASE_WORK_BYTES[case_id])
    replay_start = perf_counter()
    certificate = certificate_a(matrix, blocks(), budget, b=rhs, z=state,
                                interval_kernel="compiled_experimental")
    replay_seconds = perf_counter() - replay_start
    if certificate != measurement["certificate"]:
        raise ArithmeticError("Q6 saved-only certificate differs from source")
    if certificate.get("status") != "CERTIFIED_WITHIN_LIMIT":
        raise ArithmeticError("Q6 saved-only certificate does not meet diagnostic limits")
    result = {
        "status": "UNREGISTERED_Q6_SAVED_ONLY_CERTIFICATE_REPLAY",
        "case_id": case_id,
        "source_measurement_sha256": measurement_hash,
        "source_receipt_sha256": receipt_hash,
        "source_system_sha256": measurement["scaled_system_archive_sha256"],
        "source_inverse_sha256": inverse_hash,
        "source_candidate_sha256": candidate_hash,
        "kkt_rhs_sha256": measurement["scaled_kkt_rhs_sha256"],
        "physical_scale_inventory": [int(displacement_scale.size),
                                     int(multiplier_scale.size)],
        "load_seconds": load_seconds,
        "certificate_seconds": replay_seconds,
        "certificate": certificate,
        "certificate_matches_source": True,
        "diagnostic_certificate_within_limit": True,
        "independent_arithmetic_proof": False,
        "scientific_registration": False,
    }
    with (output / "measurement.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")


def parent(source: Path, output: Path, case_id: str) -> None:
    if case_id not in CASES:
        raise ValueError("fixed Q6 grid required")
    if output.exists():
        raise FileExistsError("diagnostic evidence must not be overwritten")
    output.mkdir(parents=True)
    source = source.resolve(strict=True)
    _, attempt_hash = _read_json(source / "measurement.json", 1024*1024)
    command = [sys.executable, "-m", "scripts.b3_e4_f03_q6_saved_certificate_replay",
               "--child", str(source), str(output.resolve()), "--grid", case_id]
    with (output / "attempt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "status": "UNREGISTERED_Q6_SAVED_ONLY_REPLAY_ATTEMPT",
            "case_id": case_id,
            "source_measurement_sha256": attempt_hash,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "argv": command,
            "seconds_limit": _CASE_SECONDS[case_id],
            "tree_rss_bytes_limit": 2*1024**3,
            "stream_bytes_limit": 8*1024**2,
        }, indent=2) + "\n")
    with (output / "stdout.log").open("wb") as stdout, (
            output / "stderr.log").open("wb") as stderr:
        receipt = supervise(
            command, cwd=Path(__file__).resolve().parents[1],
            environment=frozen_thread_environment(), stdout=stdout,
            stderr=stderr,
            limits=SupervisorLimits(_CASE_SECONDS[case_id], 2*1024**3),
            log_byte_limit=8*1024**2)
    with (output / "receipt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(receipt), indent=2) + "\n")
    if receipt.reason == "completed" and receipt.exit_code == 0:
        _check_parent_source_identity(attempt_hash, output / "measurement.json")
    print(json.dumps({"receipt_reason": receipt.reason,
                      "exit_code": receipt.exit_code,
                      "peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
                      "measurement_exists": (output / "measurement.json").exists()}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", nargs=2, type=Path, metavar=("SOURCE", "OUTPUT"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--grid", choices=CASES, required=True)
    args = parser.parse_args()
    if (args.child is None) == (args.source is None or args.output is None):
        parser.error("select exactly one child or supervised source/output")
    if args.child is not None:
        child(*args.child, args.grid)
    else:
        parent(args.source, args.output, args.grid)


if __name__ == "__main__":
    main()
