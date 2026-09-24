"""Unregistered X2 combined Q6 diagnostic with one owned assembly.

This measures certificate, primal positivity, physical recovery and spatial
checks in one supervised source process. A 2400-second observation cap is not
a scientific gate or a revision of the draft 1800-second case envelope.
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

from scripts._b3_e4_f03_conforming_qp_energy import assemble
from scripts._b3_e4_f03_local_scientific_supervisor import (
    SupervisorLimits, frozen_thread_environment, supervise,
)
from scripts._b3_e4_f03_qp_operator_identity import fingerprint
from scripts._b3_e4_f03_qp_h_contract import (
    trace_for_case, validate_case_payload, validate_spatial_payload,
)
from scripts.b3_e4_f03_q6_full_certificate_feasibility import child as certificate_child
from scripts.b3_e4_f03_q6_positivity_feasibility import child as positivity_child
from scripts.b3_e4_f03_qp_nested_x_pilot import run as physical_run
from scripts.b3_e4_f03_qp_nested_x2_spatial import run as spatial_run


_SECONDS = 2400.
_RSS_BYTES = 2*1024**3


def _recovery_source_hashes() -> dict[str, str]:
    functions = {
        "spatial_source_sha256": (spatial_run,
                                  "b3_e4_f03_qp_nested_x2_spatial.py"),
        "nodal_source_sha256": (spatial_run.__globals__["recover_nodal"],
                                "_b3_e4_f03_qp_nodal_recovery.py"),
    }
    result = {}
    for name, (function, filename) in functions.items():
        path = Path(function.__code__.co_filename)
        if path.name != filename:
            raise ValueError("unexpected Q6 recovery source path")
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _write(path: Path, value: dict) -> bytes:
    payload = (json.dumps(value, indent=2)+"\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)
    return payload


def _read(path: Path, cap: int) -> tuple[dict, str]:
    with path.open("rb") as stream:
        payload = stream.read(cap+1)
    if not 0 < len(payload) <= cap:
        raise ValueError("combined Q6 JSON evidence byte bound exceeded")
    value = json.loads(payload)
    if type(value) is not dict:
        raise ValueError("combined Q6 JSON object required")
    return value, hashlib.sha256(payload).hexdigest()


def child(output: Path) -> None:
    recovery_sources = _recovery_source_hashes()
    _write(output / "start.json", {
        "status": "UNREGISTERED_Q6_X2_SHARED_ASSEMBLY_STARTED",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **recovery_sources,
        "python_executable": sys.executable,
        "thread_environment": {name: os.environ.get(name) for name in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
    })
    begun = perf_counter()
    operators = assemble(trace_for_case("X2"))
    expected_trace = trace_for_case("X2")
    assembly_s = perf_counter()-begun
    if operators.dof_count != 5890:
        raise ArithmeticError("shared X2 operator inventory changed")
    operator_hash = fingerprint(operators, expected_trace)

    def assert_unchanged():
        if fingerprint(operators, expected_trace) != operator_hash:
            raise ArithmeticError("shared X2 operator content changed between phases")

    certificate_dir = output / "certificate"
    certificate_dir.mkdir()
    started = perf_counter()
    certificate_child(certificate_dir, "X2", operators=operators)
    assert_unchanged()
    certificate_s = perf_counter()-started
    certificate, certificate_hash = _read(certificate_dir / "measurement.json", 1024*1024)
    if certificate.get("certificate", {}).get("status") != "CERTIFIED_WITHIN_LIMIT":
        raise ArithmeticError("shared X2 KKT certificate did not pass")
    candidate, candidate_hash = _read(certificate_dir / "candidate_state.json", 2*1024*1024)
    if (candidate_hash != certificate["candidate_state_sha256"] or
            candidate.get("case_id") != "X2"):
        raise ValueError("shared X2 certificate candidate identity mismatch")
    state = np.asarray(candidate.get("scaled_kkt_state"), dtype=np.float64)
    if state.shape != (certificate["kkt_order"],) or not np.isfinite(state).all():
        raise ValueError("shared X2 certificate candidate invalid")

    positivity_dir = output / "positivity"
    positivity_dir.mkdir()
    started = perf_counter()
    positivity_child(positivity_dir, "X2", operators=operators)
    assert_unchanged()
    positivity_s = perf_counter()-started
    positivity, positivity_hash = _read(positivity_dir / "measurement.json", 1024*1024)
    if (positivity.get("proof", {}).get("status") != "POSITIVE_QUADRATIC_FORM" or
            positivity.get("shell_order") != operators.dof_count):
        raise ArithmeticError("shared X2 shell positivity did not pass")

    started = perf_counter()
    physical = physical_run(
        6, "x2", candidate_state=state,
        expected_kkt_sha256=certificate["scaled_kkt_rhs_sha256"],
        operators=operators)
    assert_unchanged()
    physical_bytes = _write(output / "physical.json", physical)
    validate_case_payload("X2", json.loads(physical_bytes))
    physical_s = perf_counter()-started
    if physical["elapsed"]["assembly_s"] > 1.:
        raise ArithmeticError("shared X2 physical route repeated assembly")

    started = perf_counter()
    spatial = spatial_run(output / "physical.json", operators=operators)
    if _recovery_source_hashes() != recovery_sources:
        raise ArithmeticError("Q6 recovery source changed during diagnostic")
    assert_unchanged()
    validate_spatial_payload("X2", hashlib.sha256(physical_bytes).hexdigest(),
                             spatial)
    spatial_bytes = _write(output / "spatial.json", spatial)
    spatial_s = perf_counter()-started
    _write(output / "measurement.json", {
        "status": "UNREGISTERED_Q6_X2_SHARED_ASSEMBLY_REHEARSAL",
        "assembly_seconds": assembly_s,
        "certificate_seconds": certificate_s,
        "positivity_seconds": positivity_s,
        "physical_seconds": physical_s,
        "spatial_seconds": spatial_s,
        "total_child_seconds": perf_counter()-begun,
        "certificate_measurement_sha256": certificate_hash,
        "positivity_measurement_sha256": positivity_hash,
        "candidate_state_sha256": candidate_hash,
        "scaled_kkt_rhs_sha256": certificate["scaled_kkt_rhs_sha256"],
        "original_scaled_shell_sha256": positivity["original_scaled_shell_sha256"],
        "physical_sha256": hashlib.sha256(physical_bytes).hexdigest(),
        "spatial_sha256": hashlib.sha256(spatial_bytes).hexdigest(),
        "shared_assembly": True,
        "reused_free_shell_for_spatial_recovery": True,
        **recovery_sources,
        "operator_fingerprint_sha256": operator_hash,
        "operator_unchanged_after_each_phase": True,
        "physical_recovery_uses_certificate_candidate": True,
        "diagnostic_kkt_certificate": certificate["certificate"]["status"],
        "diagnostic_shell_positivity": positivity["proof"]["status"],
        "scientific_registration": False,
    })


def parent(output: Path) -> None:
    if output.exists():
        raise FileExistsError("diagnostic evidence must not be overwritten")
    output.mkdir(parents=True)
    command = [sys.executable, "-m", "scripts.b3_e4_f03_q6_x2_shared_assembly_rehearsal",
               "--child", str(output.resolve())]
    _write(output / "attempt.json", {
        "status": "UNREGISTERED_Q6_X2_SHARED_ASSEMBLY_ATTEMPT",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "argv": command,
        "seconds_limit": _SECONDS,
        "tree_rss_bytes_limit": _RSS_BYTES,
        "stream_bytes_limit": 8*1024**2,
    })
    with (output / "stdout.log").open("wb") as stdout, (
            output / "stderr.log").open("wb") as stderr:
        receipt = supervise(
            command, cwd=Path(__file__).resolve().parents[1],
            environment=frozen_thread_environment(), stdout=stdout,
            stderr=stderr, limits=SupervisorLimits(_SECONDS, _RSS_BYTES),
            log_byte_limit=8*1024**2)
    _write(output / "receipt.json", asdict(receipt))
    print(json.dumps({"reason": receipt.reason, "exit_code": receipt.exit_code,
                      "peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
                      "measurement_exists": (output / "measurement.json").exists()}))


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
