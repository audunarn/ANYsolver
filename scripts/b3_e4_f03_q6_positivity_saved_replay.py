"""Replay the experimental Q6 positivity proof from archived inputs only.

This is a diagnostic using the same proof kernel; it is not independent
arithmetic verification or registered G0 acceptance.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

from scripts._b3_e4_f03_local_scientific_supervisor import (
    SupervisorLimits, frozen_thread_environment, supervise,
)
from scripts._b3_e4_f03_qp_h_contract import CASES, CASE_COUNTS
from scripts._b3_e4_f03_q6_positivity_archive import read_inputs
from scripts._b3_e4_f03_q6_positivity_interval import (
    PositivityIntervalBudget, certify_positive,
)
from scripts._b3_e4_f03_sparse_certificate import SparseBudget


_SECONDS = {"X0": 900., "X1": 1200., "X2": 1800.}
_RSS = 2*1024**3


def _json(path: Path, cap: int) -> tuple[dict, str]:
    with path.open("rb") as stream:
        payload = stream.read(cap+1)
    if not 0 < len(payload) <= cap:
        raise ValueError("positivity replay JSON byte bound exceeded")
    value = json.loads(payload)
    if type(value) is not dict:
        raise ValueError("positivity replay JSON object required")
    return value, hashlib.sha256(payload).hexdigest()


def _inverse(path: Path, order: int, expected_hash: str) -> bytes:
    size = 8*order*order
    with path.open("rb") as stream:
        payload = stream.read(size+1)
    if len(payload) != size or hashlib.sha256(payload).hexdigest() != expected_hash:
        raise ValueError("positivity replay inverse size/hash mismatch")
    return payload


def child(source: Path, output: Path, case_id: str,
          expected_source_hash: str) -> None:
    measurement, measurement_hash = _json(source / "measurement.json", 1024*1024)
    receipt, receipt_hash = _json(source / "receipt.json", 8192)
    attempt, _ = _json(source / "attempt.json", 8192)
    start, _ = _json(source / "start.json", 8192)
    if (measurement.get("status") != "UNREGISTERED_Q6_POSITIVITY_FEASIBILITY" or
            measurement.get("case_id") != case_id or
            measurement_hash != expected_source_hash or
            attempt.get("case_id") != case_id or
            start.get("case_id") != case_id or
            attempt.get("source_sha256") != start.get("source_sha256") or
            receipt.get("reason") != "completed" or receipt.get("exit_code") != 0 or
            receipt.get("failure") is not None):
        raise ValueError("positivity replay requires completed matching source")
    for key, module in (("proof_source_sha256", certify_positive.__module__),
                        ("archive_source_sha256", read_inputs.__module__)):
        actual = hashlib.sha256(
            Path(sys.modules[module].__file__).read_bytes()).hexdigest()
        if measurement.get(key) != actual:
            raise ValueError("positivity replay proof/archive source identity mismatch")
    order = CASE_COUNTS[case_id][2]
    if measurement.get("shell_order") != order:
        raise ValueError("positivity replay shell order mismatch")
    inventory = measurement["positivity_inputs_archive"]
    begun = perf_counter()
    k, working, lower, diagonal, permutation, scale, archive_bytes = read_inputs(
        source / "positivity_inputs.npz", order=order,
        k_nnz=measurement["shell_nnz"],
        working_nnz=measurement["working_nnz"],
        lower_nnz=measurement["lower_nnz"],
        archive_sha256=inventory["sha256"],
        original_sha256=inventory["original_sha256"],
        working_sha256=inventory["working_sha256"],
        lower_sha256=inventory["lower_sha256"])
    if (archive_bytes != inventory["bytes"] or
            inventory["original_sha256"] != measurement["original_scaled_shell_sha256"] or
            inventory["working_sha256"] != measurement["rounded_symmetric_working_sha256"] or
            inventory["lower_sha256"] != measurement["lower_sha256"] or
            hashlib.sha256(np.asarray(diagonal, dtype="<f8").tobytes()).hexdigest()
            != measurement["diagonal_sha256"] or
            hashlib.sha256(np.asarray(permutation, dtype="<i8").tobytes()).hexdigest()
            != measurement["permutation_sha256"]):
        raise ValueError("positivity replay archive inventory mismatch")
    raw_inverse = _inverse(source / "lower_inverse_float64.bin", order,
                           measurement["inverse_archive_sha256"])
    if (measurement.get("inverse_archive_bytes") != len(raw_inverse) or
            measurement.get("inverse_blocks") != (order+3)//4 or
            measurement.get("proof", {}).get("inverse", {}).get("inverse_columns") != order):
        raise ValueError("positivity replay inverse inventory mismatch")
    load_seconds = perf_counter()-begun
    inverse = np.frombuffer(raw_inverse, dtype="<f8").reshape((order, order))

    def blocks():
        for first in range(0, order, 4):
            yield first, np.array(inverse[:, first:first+4],
                                  dtype=np.float64, order="C", copy=True)

    budget = PositivityIntervalBudget(
        SparseBudget(order, max(k.nnz, lower.nnz), 4, 512*1024**2),
        50_000_000, 50_000_000)
    proof_start = perf_counter()
    proof = certify_positive(k, lower, diagonal, permutation, blocks(),
                             budget=budget)
    proof_seconds = perf_counter()-proof_start
    if proof != measurement["proof"] or proof.get("status") != "POSITIVE_QUADRATIC_FORM":
        raise ArithmeticError("positivity saved-input proof differs from source")
    with (output / "measurement.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "status": "UNREGISTERED_Q6_POSITIVITY_SAVED_REPLAY",
            "case_id": case_id,
            "source_measurement_sha256": measurement_hash,
            "source_receipt_sha256": receipt_hash,
            "source_archive_sha256": inventory["sha256"],
            "source_inverse_sha256": measurement["inverse_archive_sha256"],
            "archive_bytes": archive_bytes,
            "inverse_bytes": len(raw_inverse),
            "load_seconds": load_seconds,
            "proof_seconds": proof_seconds,
            "proof": proof,
            "proof_matches_source": True,
            "independent_arithmetic_proof": False,
            "scientific_registration": False,
        }, indent=2) + "\n")


def parent(source: Path, output: Path, case_id: str) -> None:
    if output.exists():
        raise FileExistsError("diagnostic evidence must not be overwritten")
    output.mkdir(parents=True)
    source = source.resolve(strict=True)
    _, source_hash = _json(source / "measurement.json", 1024*1024)
    command = [sys.executable, "-m", "scripts.b3_e4_f03_q6_positivity_saved_replay",
               "--child", str(source), str(output.resolve()), "--grid", case_id,
               "--expected-source-sha", source_hash]
    with (output / "attempt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "status": "UNREGISTERED_Q6_POSITIVITY_SAVED_REPLAY_ATTEMPT",
            "case_id": case_id,
            "source_measurement_sha256": source_hash,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "argv": command,
            "seconds_limit": _SECONDS[case_id],
            "tree_rss_bytes_limit": _RSS,
        }, indent=2) + "\n")
    with (output / "stdout.log").open("wb") as stdout, (
            output / "stderr.log").open("wb") as stderr:
        receipt = supervise(
            command, cwd=Path(__file__).resolve().parents[1],
            environment=frozen_thread_environment(), stdout=stdout,
            stderr=stderr, limits=SupervisorLimits(_SECONDS[case_id], _RSS),
            log_byte_limit=8*1024**2)
    with (output / "receipt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(receipt), indent=2) + "\n")
    if receipt.reason == "completed" and receipt.exit_code == 0:
        result, _ = _json(output / "measurement.json", 1024*1024)
        if result.get("source_measurement_sha256") != source_hash:
            raise ArithmeticError("positivity replay parent/child identity mismatch")
    print(json.dumps({"receipt_reason": receipt.reason,
                      "exit_code": receipt.exit_code,
                      "peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
                      "measurement_exists": (output / "measurement.json").exists()}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", nargs=2, type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--grid", choices=CASES, required=True)
    parser.add_argument("--expected-source-sha")
    args = parser.parse_args()
    if (args.child is None) == (args.source is None or args.output is None):
        parser.error("select exactly one child or supervised source/output")
    if args.child is not None:
        if args.expected_source_sha is None:
            parser.error("child requires expected source measurement hash")
        child(*args.child, args.grid, args.expected_source_sha)
    else:
        parent(args.source, args.output, args.grid)


if __name__ == "__main__":
    main()
