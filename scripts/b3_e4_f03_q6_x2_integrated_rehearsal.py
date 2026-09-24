"""Unregistered X2 complete-route resource rehearsal under one supervisor.

The existing certificate and physical pilots each assemble independently;
this measures a conservative source-process route, not a qualified solver.
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
from scripts._b3_e4_f03_qp_h_contract import (
    validate_case_payload, validate_spatial_payload,
)
from scripts.b3_e4_f03_q6_full_certificate_feasibility import child as certificate_child
from scripts.b3_e4_f03_qp_nested_x_pilot import run as physical_run
from scripts.b3_e4_f03_qp_nested_x2_spatial import run as spatial_run


_SECONDS = 1800.
_TREE_RSS_BYTES = 2*1024**3
_STREAM_BYTES = 8*1024**2


def _write_new(path: Path, value: dict) -> bytes:
    payload = (json.dumps(value, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)
    return payload


def child(output: Path) -> None:
    _write_new(output / "start.json", {
        "status": "UNREGISTERED_X2_INTEGRATED_REHEARSAL_STARTED",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_executable": sys.executable,
        "thread_environment": {name: os.environ.get(name) for name in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
    })
    begun = perf_counter()
    certificate_dir = output / "certificate"
    certificate_dir.mkdir()
    certificate_child(certificate_dir, "X2")
    certificate_s = perf_counter() - begun
    with (certificate_dir / "measurement.json").open(encoding="utf-8") as stream:
        certificate = json.load(stream)
    if certificate["certificate"]["status"] != "CERTIFIED_WITHIN_LIMIT":
        raise ArithmeticError("X2 certificate diagnostic did not pass")
    candidate_bytes = (certificate_dir / "candidate_state.json").read_bytes()
    candidate_hash = hashlib.sha256(candidate_bytes).hexdigest()
    if candidate_hash != certificate["candidate_state_sha256"]:
        raise ArithmeticError("certificate candidate state hash mismatch")
    candidate = json.loads(candidate_bytes)
    if candidate.get("case_id") != "X2":
        raise ValueError("certificate candidate grid mismatch")
    candidate_state = np.asarray(candidate.get("scaled_kkt_state"), dtype=np.float64)
    if (candidate_state.shape != (certificate["kkt_order"],) or
            not np.isfinite(candidate_state).all()):
        raise ValueError("invalid certificate candidate state")
    started = perf_counter()
    physical = physical_run(
        6, "x2", candidate_state=candidate_state,
        expected_kkt_sha256=certificate["scaled_kkt_rhs_sha256"])
    physical_bytes = _write_new(output / "physical.json", physical)
    # Validate the actual JSON boundary: the producer uses tuples for grids,
    # while the durable case schema owns JSON list representations.
    validate_case_payload("X2", json.loads(physical_bytes))
    physical_s = perf_counter() - started
    started = perf_counter()
    spatial = spatial_run(output / "physical.json")
    validate_spatial_payload("X2", hashlib.sha256(physical_bytes).hexdigest(),
                             spatial)
    spatial_bytes = _write_new(output / "spatial.json", spatial)
    spatial_s = perf_counter() - started
    _write_new(output / "measurement.json", {
        "status": "UNREGISTERED_X2_INTEGRATED_RESOURCE_REHEARSAL",
        "certificate_measurement_sha256": hashlib.sha256(
            (certificate_dir / "measurement.json").read_bytes()).hexdigest(),
        "candidate_state_sha256": candidate_hash,
        "scaled_kkt_rhs_sha256": certificate["scaled_kkt_rhs_sha256"],
        "physical_sha256": hashlib.sha256(physical_bytes).hexdigest(),
        "spatial_sha256": hashlib.sha256(spatial_bytes).hexdigest(),
        "certificate_seconds": certificate_s,
        "physical_seconds": physical_s,
        "spatial_seconds": spatial_s,
        "total_child_seconds": perf_counter() - begun,
        "duplicate_assembly": True,
        "physical_recovery_uses_certificate_candidate": True,
        "scientific_registration": False,
    })


def parent(output: Path) -> None:
    if output.exists():
        raise FileExistsError("rehearsal evidence must not be overwritten")
    output.mkdir(parents=True)
    workdir = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "scripts.b3_e4_f03_q6_x2_integrated_rehearsal",
               "--child", str(output.resolve())]
    _write_new(output / "attempt.json", {
        "status": "UNREGISTERED_X2_INTEGRATED_REHEARSAL_ATTEMPT",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "argv": command,
        "seconds_limit": _SECONDS,
        "tree_rss_bytes_limit": _TREE_RSS_BYTES,
        "stream_bytes_limit": _STREAM_BYTES,
    })
    with (output / "stdout.log").open("wb") as stdout, (
            output / "stderr.log").open("wb") as stderr:
        receipt = supervise(
            command, cwd=workdir, environment=frozen_thread_environment(),
            stdout=stdout, stderr=stderr,
            limits=SupervisorLimits(_SECONDS, _TREE_RSS_BYTES),
            log_byte_limit=_STREAM_BYTES,
        )
    _write_new(output / "receipt.json", asdict(receipt))
    print(json.dumps({
        "receipt_reason": receipt.reason,
        "exit_code": receipt.exit_code,
        "peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
        "measurement_exists": (output / "measurement.json").exists(),
    }))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (args.child is None) == (args.output is None):
        parser.error("select exactly one child or supervised output")
    if args.child is not None:
        child(args.child)
    else:
        parent(args.output)


if __name__ == "__main__":
    main()
