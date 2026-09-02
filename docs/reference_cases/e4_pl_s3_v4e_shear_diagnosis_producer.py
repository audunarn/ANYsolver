"""Bounded producer for the research-only V4E thickness-scaled shear diagnosis."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v4a_screen_producer as q4_source
import e4_pl_s3_v4d_screen_producer as v4d


CONTRACT = REFERENCE / "e4_pl_s3_v4e_shear_diagnosis_contract.json"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4e-shear-diagnosis-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v4e-shear-diagnosis-check-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v4e-shear-diagnosis-aggregate-v1"
THICKNESSES = (1.0, 0.1, 0.01, 0.001)
DIAGONALS = ("slash", "backslash")
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)

canonical_bytes = q4_source.canonical_bytes
sha256_file = q4_source.sha256_file
load_canonical = q4_source.load_canonical
exclusive_write = q4_source.exclusive_write


class DiagnosisError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4e-shear-diagnosis-contract-v1":
        raise DiagnosisError("unexpected V4E diagnosis contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise DiagnosisError(f"frozen input mismatch: {path}")
    prereg = load_canonical(REFERENCE / "e4_pl_s3_v4e_preregistration_result.json")
    if prereg.get("terminal") != "PROVISIONAL_GO_E4_PL_S3_V4E_BOUNDED_SHEAR_DIAGNOSIS" or prereg.get("next_gate_authorized") is not True:
        raise DiagnosisError("V4E preregistration does not authorize this diagnosis")
    return contract


def _macro_matrices(thickness: float, diagonal: str) -> dict[str, np.ndarray]:
    q4_source.THICKNESS = float(thickness)
    v4d.physical_first.THICKNESS = float(thickness)
    coordinates = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)))
    q4_raw = q4_source._qualified_q4_components(coordinates, NORMAL)
    q4 = {name: np.asarray(q4_raw[name], dtype=np.float64) for name in ("physical", "pl", "total")}
    s3 = {name: np.zeros((24, 24), dtype=np.float64) for name in q4}
    triangles = ((0, 1, 3), (1, 2, 3)) if diagonal == "slash" else ((0, 1, 2), (0, 2, 3))
    for triangle in triangles:
        made = v4d.v4d_components(coordinates[np.asarray(triangle)])
        for name in s3:
            s3[name] += q4_source._embed(np.asarray(made[name]), triangle, 4)
    return {"coordinates": coordinates, **{f"q4_{name}": value for name, value in q4.items()}, **{f"s3_{name}": value for name, value in s3.items()}}


def _sample(thickness: float, diagonal: str) -> dict[str, Any]:
    made = _macro_matrices(thickness, diagonal)
    modes = v4d.physical_first._trace_modes(made["coordinates"])
    vector = modes["linear_rotation"]
    q4_action = made["q4_total"] @ vector
    s3_action = made["s3_total"] @ vector
    q4_energy = float(vector @ q4_action)
    s3_energy = float(vector @ s3_action)
    residual = float(np.linalg.norm(s3_action - q4_action, ord=np.inf) / max(np.linalg.norm(q4_action, ord=np.inf), 1.0))
    physical_residual = float(np.linalg.norm(made["s3_physical"] @ vector - made["q4_physical"] @ vector, ord=np.inf) / max(np.linalg.norm(made["q4_physical"] @ vector, ord=np.inf), 1.0))
    pl_work = max(abs(float(vector @ made["q4_pl"] @ vector)), abs(float(vector @ made["s3_pl"] @ vector)))
    identity_worst = 0.0
    for name in ("constant_kappa_x", "constant_kappa_y", "constant_kappa_xy", "quadratic_transverse"):
        mode = modes[name]
        expected = made["q4_total"] @ mode
        identity_worst = max(identity_worst, float(np.linalg.norm(made["s3_total"] @ mode - expected, ord=np.inf) / max(np.linalg.norm(expected, ord=np.inf), 1.0)))
    return {
        "diagonal": diagonal,
        "energy_ratio_hex": float(s3_energy / q4_energy).hex(),
        "identity_trace_worst_relative_inf_hex": identity_worst.hex(),
        "linear_rotation_action_relative_inf_hex": residual.hex(),
        "physical_action_relative_inf_hex": physical_residual.hex(),
        "pl_work_abs_hex": pl_work.hex(),
        "q4_energy_hex": q4_energy.hex(),
        "s3_energy_hex": s3_energy.hex(),
        "thickness_hex": float(thickness).hex(),
    }


def _classify(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_key = {(str(row["diagonal"]), float.fromhex(str(row["thickness_hex"]))): row for row in records}
    stable = True
    per_diagonal: dict[str, Any] = {}
    for diagonal in DIAGONALS:
        one = by_key[(diagonal, 0.01)]
        two = by_key[(diagonal, 0.001)]
        residuals = tuple(float.fromhex(str(row["linear_rotation_action_relative_inf_hex"])) for row in (one, two))
        ratios = tuple(float.fromhex(str(row["energy_ratio_hex"])) for row in (one, two))
        passed = min(residuals) > 0.1 and abs(residuals[0] - residuals[1]) <= 0.01 and 0.0 < min(ratios) <= max(ratios) < 1.0 and abs(ratios[0] - ratios[1]) <= 0.01
        stable = stable and passed
        per_diagonal[diagonal] = {"energy_ratio_difference_hex": abs(ratios[0] - ratios[1]).hex(), "passed": passed, "residual_difference_hex": abs(residuals[0] - residuals[1]).hex()}
    identity = max(float.fromhex(str(row["identity_trace_worst_relative_inf_hex"])) for row in records) <= 3.0e-9
    zero_pl = all(float.fromhex(str(row["pl_work_abs_hex"])) == 0.0 for row in records)
    return {"identity_passed": bool(identity and zero_pl), "per_diagonal": per_diagonal, "shear_replacement_required": bool(identity and zero_pl and stable), "thin_limit_stable": bool(stable), "zero_pl_work": bool(zero_pl)}


def produce_proof() -> dict[str, Any]:
    validate_authority()
    records = [_sample(thickness, diagonal) for thickness in THICKNESSES for diagonal in DIAGONALS]
    return {
        "activation_authorized": False,
        "classification": _classify(records),
        "contract_sha256": sha256_file(CONTRACT),
        "later_stages": "NOT_EXECUTED_DIAGNOSTIC_ONLY",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "records": records,
        "records_sha256": sha256_bytes(canonical_bytes(records)),
        "schema": PROOF_SCHEMA,
        "stage4a_rerun_authorized": False,
    }


def adjudicate(*, identical: bool, report: Mapping[str, Any]) -> str:
    if not identical or not report.get("authority_complete"):
        return "BLOCKED_E4_PL_S3_V4E_PROCESS_OR_EVIDENCE"
    if not report.get("diagnostic_identity_passed"):
        return "NO_GO_E4_PL_S3_V4E_DIAGNOSTIC_IDENTITY"
    if not report.get("shear_replacement_required"):
        return "UNCLASSIFIED_E4_PL_S3_V4E_SHEAR_SOURCE_UNRESOLVED"
    return "UNCLASSIFIED_E4_PL_S3_V4E_SHEAR_FORMULATION_REPLACEMENT_REQUIRED"


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise DiagnosisError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    checker = REFERENCE / "e4_pl_s3_v4e_shear_diagnosis_checker.py"
    deadline = time.monotonic() + wave_timeout_seconds
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V4E_PROCESS_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checks = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION", "sequence": 0}))
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            v4d.physical_first._run_child([sys.executable, str(Path(__file__).resolve()), "--emit-proof", "--output", str(proof)], remaining)
            commands = [[sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)] for path in checks]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(v4d.physical_first._run_child, command, int(max(1, min(timeout_seconds, deadline - time.monotonic())))) for command in commands]
                for future in futures:
                    future.result()
            identical = checks[0].read_bytes() == checks[1].read_bytes()
            report = load_canonical(checks[0])
            terminal = adjudicate(identical=identical, report=report)
            cycles.append({"checker_replicas_byte_identical": identical, "checker_sha256": sha256_file(checks[0]), "cycle": cycle, "proof_bytes": proof.stat().st_size, "proof_sha256": sha256_file(proof), "terminal": terminal})
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE", "sequence": 1}))
        if cycles[0]["proof_sha256"] != cycles[1]["proof_sha256"] or cycles[0]["checker_sha256"] != cycles[1]["checker_sha256"]:
            terminal = "BLOCKED_E4_PL_S3_V4E_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V4E_PROCESS_OR_EVIDENCE"
    aggregate = {"activation_authorized": False, "contract_sha256": sha256_file(CONTRACT), "cycles": cycles, "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "schema": AGGREGATE_SCHEMA, "stage4a_rerun_authorized": False, "terminal": terminal}
    exclusive_write(root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-proof", action="store_true")
    mode.add_argument("--run-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--wave-timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    if args.emit_proof:
        if args.output is None:
            raise DiagnosisError("--output is required")
        exclusive_write(args.output, produce_proof())
    else:
        if args.output_root is None:
            raise DiagnosisError("--output-root is required")
        run_bounded(args.output_root, timeout_seconds=args.timeout_seconds, wave_timeout_seconds=args.wave_timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
