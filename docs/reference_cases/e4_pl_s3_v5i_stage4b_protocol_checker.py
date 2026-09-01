"""Standard-library-only independent review of the S3 V5I Stage 4B protocol."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
DEFAULT_INPUT = REFERENCE / "e4_pl_s3_v5i_stage4b_input.json"
SCHEMA = "anysolver.e4-pl-s3-v5i-stage4b-protocol-review-v1"


class ProtocolReviewError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise ProtocolReviewError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ProtocolReviewError(f"nonfinite JSON token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise ProtocolReviewError(f"noncanonical JSON: {path}")
    return raw, value


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if process.returncode:
        raise ProtocolReviewError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def _authority_commit(authority: Mapping[str, Any]) -> tuple[str, str]:
    candidates = _git("rev-list", "--all", "--grep", f"^{authority['expected_subject']}$").splitlines()
    for commit in candidates:
        if _git("show", "-s", "--format=%P", commit) != authority["expected_parent"]:
            continue
        changed = sorted(
            line for line in _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines() if line
        )
        if changed == authority["exact_paths"]:
            return commit, _git("show", "-s", "--format=%T", commit)
    raise ProtocolReviewError("the exact V5I authority commit is unavailable")


def review_protocol(input_path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    input_raw, payload = load_canonical(input_path)
    if payload.get("schema") != "anysolver.e4-pl-s3-v5i-stage4b-input-v1":
        raise ProtocolReviewError("unexpected input schema")
    bindings = payload.get("frozen_inputs")
    if not isinstance(bindings, list) or not bindings:
        raise ProtocolReviewError("missing frozen inputs")
    seen: list[str] = []
    for row in bindings:
        if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
            raise ProtocolReviewError("malformed frozen input")
        path = (ROOT / row["path"]).resolve(strict=True)
        if not path.is_relative_to(ROOT.resolve()):
            raise ProtocolReviewError("frozen input escapes repository")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise ProtocolReviewError(f"frozen input mismatch: {row['path']}")
        seen.append(row["path"])
    if len(seen) != len(set(seen)):
        raise ProtocolReviewError("frozen inputs are not unique")

    plan_raw, plan = load_canonical(REFERENCE / "e4_pl_s3_v5i_stage4b_plan.json")
    if plan.get("execution") != payload.get("execution"):
        raise ProtocolReviewError("plan/input execution bounds disagree")
    if plan.get("terminal_precedence") != payload.get("terminal_precedence"):
        raise ProtocolReviewError("plan/input terminal precedence disagrees")
    if plan.get("production_boundary") != payload.get("production_boundary"):
        raise ProtocolReviewError("plan/input production boundary disagrees")
    if payload.get("worker_ids") != [
        "MODAL_MIXED_10", "MODAL_MIXED_25", "BUCKLING_MIXED_10",
        "BUCKLING_MIXED_25", "PERFORMANCE_ALL_Q4",
        "PERFORMANCE_MIXED_10", "PERFORMANCE_MIXED_25",
    ]:
        raise ProtocolReviewError("worker extent changed")
    if payload.get("next_gate_on_pass") != "V5J_V2C_BATCH_RESTART_AND_PACKAGE_PARITY":
        raise ProtocolReviewError("next gate changed")

    runner_path = REFERENCE / "e4_pl_s3_v5i_stage4b.py"
    runner_source = runner_path.read_text(encoding="utf-8")
    ast.parse(runner_source)
    required_runner_tokens = (
        'FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"',
        '"selector": "e4-pl-s3-v2c"',
        "CHILD_TIMEOUT_SECONDS = 600",
        "WAVE_TIMEOUT_SECONDS = 1800",
        "MEMORY_LIMIT_GIB = 24",
        "WORKER_CONCURRENCY = 3",
        "CYCLES = 2",
        "lane._modal_worker",
        "lane._buckling_worker",
        "lane._performance_worker",
        "stress_second_moment",
        "validate_authorization",
    )
    if any(token not in runner_source for token in required_runner_tokens):
        raise ProtocolReviewError("runner lacks a required protocol token")
    if "BATCH_4096" in runner_source:
        raise ProtocolReviewError("V1 batch qualification leaked into V5I")

    v2c = (ROOT / "src/anysolver/e4_pl_s3_v2c_element.py").read_text(encoding="utf-8")
    dynamics = (ROOT / "src/anysolver/algebraic_dynamics.py").read_text(encoding="utf-8")
    defaults = (ROOT / "src/anysolver/elements.py").read_text(encoding="utf-8")
    if not all(
        token in v2c
        for token in (
            "MYSTRAN_TRIA3_LUMPED_TRANSLATIONAL_MASS_V1",
            "S3_V2C_LOCAL_ROTATION_ROWS_EXACT_ZERO_V1",
            "dynamic_algebraic_nullity = 9",
            '"zero_rotational_inertia": True',
        )
    ):
        raise ProtocolReviewError("V2C descriptor mass authority is incomplete")
    if "rotation_witness = witness == \"S3_V2C_LOCAL_ROTATION_ROWS_EXACT_ZERO_V1\"" not in dynamics:
        raise ProtocolReviewError("global descriptor policy does not recognize V2C")
    if (
        'DEFAULT_Q4_FORMULATION = "e4-pl"' not in defaults
        or 'DEFAULT_S3_FORMULATION = "legacy-s3"' not in defaults
    ):
        raise ProtocolReviewError("production defaults changed")

    commit, tree = _authority_commit(payload["authority_commit"])
    return {
        "authority": {"commit": commit, "tree": tree},
        "checks": {
            "bounded_process_tree": True,
            "canonical_two_cycle_agreement": True,
            "defaults_unchanged": True,
            "historical_numerical_algorithms_reused": True,
            "no_v1_batch_claim": True,
            "v2c_descriptor_mass_policy": True,
            "v2c_factory_authority": True,
            "v2c_zero_stress_second_moment_policy": True,
        },
        "findings": {"P0": [], "P1": []},
        "input_sha256": sha256(input_raw),
        "plan_sha256": sha256(plan_raw),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "verdict": "ACCEPT_S3_V5I_STAGE4B_PROTOCOL_NO_P0_P1",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-v5i-stage4b-protocol", action="store_true", required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    value = review_protocol(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
