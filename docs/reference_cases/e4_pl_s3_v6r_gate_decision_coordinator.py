"""Run two bounded evidence-only V6R gate-decision cycles."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import ModuleType
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6r_gate_decision_contract.json"
CHECKER = REFERENCE / "e4_pl_s3_v6r_gate_decision_checker.py"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6r_gate_decision_execution_authorization.json"
BOUNDED = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
SCHEMA = "anysolver.e4-pl-s3-v6r-gate-decision-aggregate-v1"
DIAGONALS = ("slash", "backslash", "alternating")
BLOCKED = "BLOCKED_E4_PL_S3_V6R_EVIDENCE_OR_REVIEW"
NO_GO = "NO_GO_E4_PL_S3_V6R_SPATIAL_GATE_DISAGREEMENT"
PASS = "PROVISIONAL_GO_E4_PL_S3_V6R_STAGE4B_PREPARATION"
MEMORY_LIMIT_BYTES = 24 * (1 << 30)
THREAD_ENV = {name: "1" for name in ("BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS", "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "TBB_NUM_THREADS")}


class V6RCoordinatorError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    pairs = lambda rows: _pairs(rows)
    value = json.loads(raw, parse_constant=lambda item: (_ for _ in ()).throw(V6RCoordinatorError(f"nonfinite {item}")), object_pairs_hook=pairs)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6RCoordinatorError(f"noncanonical JSON: {path}")
    return value, raw


def _pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in rows:
        if key in made:
            raise V6RCoordinatorError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _load_bounded() -> ModuleType:
    name = "_s3_v6r_bounded_process"
    loaded = sys.modules.get(name)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name, BOUNDED)
    if spec is None or spec.loader is None:
        raise V6RCoordinatorError("cannot load process guard")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def validate_authority(*, execution: bool) -> tuple[dict[str, Any], bytes]:
    contract, raw = strict_json(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v6r-gate-decision-contract-v1" or contract.get("activation_authorized") is not False:
        raise V6RCoordinatorError("V6R contract differs")
    for item in contract["frozen_inputs"]:
        path = Path(item["path"])
        if not path.is_absolute():
            path = ROOT / path
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or sha256(payload) != item["sha256"]:
            raise V6RCoordinatorError(f"frozen input differs: {path}")
    for name, path in (("checker", CHECKER), ("coordinator", Path(__file__).resolve())):
        binding = contract["programs"][name]
        payload = path.read_bytes()
        if len(payload) != binding["bytes"] or sha256(payload) != binding["sha256"]:
            raise V6RCoordinatorError(f"V6R {name} differs")
    if execution:
        auth, auth_raw = strict_json(AUTHORIZATION)
        if (
            auth.get("schema") != "anysolver.e4-pl-s3-v6r-gate-decision-execution-authorization-v1"
            or auth.get("execution_authorized") is not True
            or auth.get("activation_authorized") is not False
            or auth.get("contract_sha256") != sha256(raw)
            or auth.get("review_sha256") != sha256((REFERENCE / "e4_pl_s3_v6r_gate_decision_review.json").read_bytes())
            or auth.get("user_approval") != "STANDING_S3_QUALIFICATION_APPROVAL"
        ):
            raise V6RCoordinatorError("V6R execution authorization differs")
        contract["authorization_sha256"] = sha256(auth_raw)
    return contract, raw


def _run(command: list[str], deadline: float, output: Path) -> None:
    bounded = _load_bounded()
    remaining = min(600, int(deadline - time.monotonic()))
    if remaining <= 0:
        raise V6RCoordinatorError("V6R cycle exceeded wall bound")
    job = bounded._ProcessJob(MEMORY_LIMIT_BYTES)
    env = os.environ.copy()
    env.update(THREAD_ENV)
    with output.with_suffix(".stdout.bin").open("xb") as stdout, output.with_suffix(".stderr.bin").open("xb") as stderr:
        try:
            process = job.launch(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
            try:
                code = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired as exc:
                job.terminate(124)
                raise V6RCoordinatorError("V6R checker timed out") from exc
            _cpu, active, peak = job.accounting()
            if code or active or peak > MEMORY_LIMIT_BYTES:
                job.terminate(125)
                raise V6RCoordinatorError("V6R checker failed its process bound")
        finally:
            job.close()


def _cycle(root: Path, cycle: int, contract: Mapping[str, Any]) -> dict[str, Any]:
    _load_bounded()
    made = root / f"cycle-{cycle}"
    made.mkdir()
    deadline = time.monotonic() + 1800
    rows = []
    failure_count = 0
    for diagonal in DIAGONALS:
        proof = Path(contract["proofs"][diagonal]["path"])
        outputs = [made / diagonal / "checker-a.json", made / diagonal / "checker-b.json"]
        outputs[0].parent.mkdir()
        commands = [[sys.executable, str(CHECKER), "--verify-gate-decision", "--proof", str(proof), "--output", str(output)] for output in outputs]
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_run, command, deadline, output) for command, output in zip(commands, outputs)]
            for future in futures:
                future.result()
        identical = outputs[0].read_bytes() == outputs[1].read_bytes()
        report, report_raw = strict_json(outputs[0])
        if not identical or report.get("decision_agreement") is not True or report.get("residual_bound_passed") is not True:
            raise V6RCoordinatorError(f"V6R checker evidence differs: {diagonal}")
        failure_count += int(report["producer_formal_failure_count"]) + int(report["independent_formal_failure_count"])
        rows.append({
            "checker_replicas_byte_identical": identical,
            "checker_sha256": sha256(report_raw),
            "diagonal": diagonal,
            "raw_metric_identity_passed": report["raw_metric_identity_passed"],
            "scientific_gate_passed": report["scientific_gate_passed"],
        })
    return {"cycle": cycle, "formal_failure_count": failure_count, "record_count": 18, "shards": rows}


def _identity(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "cycle"}


def adjudicate(cycles: Sequence[Mapping[str, Any]], complete: bool = True) -> str:
    if not complete or len(cycles) != 2 or _identity(cycles[0]) != _identity(cycles[1]):
        return BLOCKED
    return NO_GO if cycles[0]["formal_failure_count"] else PASS


def run(output_root: Path) -> dict[str, Any]:
    contract, contract_raw = validate_authority(execution=True)
    output_root.mkdir(parents=True, exist_ok=False)
    cycles = []
    complete = True
    try:
        for cycle in (1, 2):
            cycles.append(_cycle(output_root, cycle, contract))
    except BaseException as exc:
        complete = False
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
    terminal = adjudicate(cycles, complete)
    aggregate = {
        "activation_authorized": False,
        "contract_sha256": sha256(contract_raw),
        "cycles": cycles,
        "mechanics_executed": False,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "stage4b_execution_authorized": False,
        "stage4b_preparation_authorized": terminal == PASS,
        "terminal": terminal,
        "v6q_reclassified": False,
    }
    with (output_root / "aggregate.json").open("xb") as stream:
        stream.write(canonical_bytes(aggregate))
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-authority", action="store_true")
    mode.add_argument("--run-evidence-only", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    if args.validate_authority:
        validate_authority(execution=False)
        return 0
    if args.output_root is None:
        raise V6RCoordinatorError("--output-root is required")
    terminal = run(args.output_root)["terminal"]
    return 0 if terminal in {PASS, NO_GO} else 2


if __name__ == "__main__":
    raise SystemExit(main())
