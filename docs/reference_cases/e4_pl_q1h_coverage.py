"""Deterministic adaptive cover for the Q1H registered gauge domain."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import time

from e4_pl_q1h_interval import certify_variation_box_control


ORDER = ("p", "q", "a", "b")
NORMALIZERS = {
    # Target full widths are based on the control-coordinate sensitivity
    # certificate, not on the raw root extents.  This prevents premature
    # over-refinement of the much narrower relative-variation coordinates.
    "p": Fraction(2, 5),
    "q": Fraction(1, 5),
    "a": Fraction(1, 5),
    "b": Fraction(1, 10),
}


@dataclass(frozen=True)
class Box:
    bounds: tuple[tuple[Fraction, Fraction], ...]
    depth: int = 0
    path: str = ""

    def mapping(self) -> dict[str, tuple[Fraction, Fraction]]:
        return dict(zip(ORDER, self.bounds, strict=True))

    def split(self) -> tuple["Box", "Box"]:
        normalized = tuple(
            (upper - lower) / NORMALIZERS[name]
            for name, (lower, upper) in zip(ORDER, self.bounds, strict=True)
        )
        coordinate = max(range(4), key=lambda index: (normalized[index], -index))
        lower, upper = self.bounds[coordinate]
        midpoint = (lower + upper) / 2
        left = list(self.bounds)
        right = list(self.bounds)
        left[coordinate] = (lower, midpoint)
        right[coordinate] = (midpoint, upper)
        return (
            Box(tuple(left), self.depth + 1, self.path + "0"),
            Box(tuple(right), self.depth + 1, self.path + "1"),
        )


ROOT = Box(
    (
        (Fraction(-4), Fraction(4)),
        (Fraction(1, 4), Fraction(4)),
        (Fraction(-3, 8), Fraction(3, 8)),
        (Fraction(-3, 8), Fraction(3, 8)),
    )
)


def _square_minimum(lower: Fraction, upper: Fraction) -> Fraction:
    if lower <= 0 <= upper:
        return Fraction(0)
    return min(lower * lower, upper * upper)


def _centre_polynomial_maximum(box: Box) -> Fraction:
    """Exact max of the necessary centre condition over a parameter box."""

    p_bounds, q_bounds, _a_bounds, _b_bounds = box.bounds
    p2 = _square_minimum(*p_bounds)
    q2_lower = q_bounds[0] ** 2
    q2_upper = q_bounds[1] ** 2
    vertex = Fraction(257, 32) - p2
    candidates = (q2_lower, q2_upper, min(max(vertex, q2_lower), q2_upper))
    return max(
        289 * value - 16 * (1 + p2 + value) ** 2
        for value in candidates
    )


def exclusion_reason(box: Box) -> str | None:
    """Return a rigorous necessary-condition exclusion, if available."""

    _p_bounds, _q_bounds, a_bounds, b_bounds = box.bounds
    if _centre_polynomial_maximum(box) < 0:
        return "CENTRE_SINGULAR_RATIO_IMPOSSIBLE"
    disk_minimum = _square_minimum(*a_bounds) + _square_minimum(*b_bounds)
    if disk_minimum > Fraction(1, 8):
        return "RELATIVE_VARIATION_DISK_IMPOSSIBLE"
    return None


def _leaf_record(
    box: Box, classification: str, reason: str, certificate: dict[str, object] | None
) -> dict[str, object]:
    selected = {}
    if certificate is not None:
        for key in (
            "control_congruence_margin",
            "control_inverse_exact_dag",
            "core_coefficient_lower_bound",
            "h_kernel_certified_by_symbolic_factor_minors",
            "schur_metric_projection_upper_bound",
        ):
            value = certificate[key]
            if hasattr(value, "item"):
                value = value.item()
            selected[key] = value
    return {
        "bounds": {
            name: [
                [lower.numerator, lower.denominator],
                [upper.numerator, upper.denominator],
            ]
            for name, (lower, upper) in zip(ORDER, box.bounds, strict=True)
        },
        "certificate": selected,
        "classification": classification,
        "path": box.path,
        "reason": reason,
    }


def _evaluate_box(box: Box) -> tuple[str, str, dict[str, object] | None]:
    exclusion = exclusion_reason(box)
    if exclusion is not None:
        return "EXCLUDED", exclusion, None
    try:
        certificate = certify_variation_box_control(box.mapping())
    except ZeroDivisionError:
        return "SUBDIVIDE", "JACOBIAN_INTERVAL_CONTAINS_ZERO", None
    if certificate["classification"] == "POSITIVE":
        return "POSITIVE", str(certificate["reason"]), certificate
    return "SUBDIVIDE", str(certificate["reason"]), certificate


def verify_leaf_partition(leaves: list[dict[str, object]]) -> None:
    paths = [str(row["path"]) for row in leaves]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate leaf path")
    ordered = sorted(paths)
    for left, right in zip(ordered, ordered[1:]):
        if right.startswith(left):
            raise ValueError("leaf paths are not prefix-free")
    if sum((Fraction(1, 2 ** len(path)) for path in paths), Fraction(0)) != 1:
        raise ValueError("leaf paths do not cover the complete binary partition")
    by_path = {str(row["path"]): row for row in leaves}
    for path, row in by_path.items():
        box = ROOT
        for digit in path:
            left, right = box.split()
            box = left if digit == "0" else right
        expected = _leaf_record(box, "ROOT", "BOUND_CHECK", None)["bounds"]
        if row["bounds"] != expected:
            raise ValueError(f"leaf bounds do not match split path {path}")


def run_cover(*, max_processed: int, max_depth: int, progress_every: int) -> dict[str, object]:
    pending = [ROOT]
    processed = positive = excluded = unresolved = 0
    maximum_depth = 0
    reasons: dict[str, int] = {}
    leaves: list[dict[str, object]] = []
    started = time.monotonic()
    while pending and processed < max_processed:
        box = pending.pop()
        processed += 1
        maximum_depth = max(maximum_depth, box.depth)
        exclusion = exclusion_reason(box)
        if exclusion is not None:
            excluded += 1
            reasons[exclusion] = reasons.get(exclusion, 0) + 1
        else:
            try:
                certificate = certify_variation_box_control(box.mapping())
            except ZeroDivisionError:
                certificate = {
                    "classification": "UNRESOLVED",
                    "reason": "JACOBIAN_INTERVAL_CONTAINS_ZERO",
                }
            if certificate["classification"] == "POSITIVE":
                positive += 1
            elif box.depth < max_depth:
                left, right = box.split()
                # Right-first push makes the lower child deterministic next.
                pending.append(right)
                pending.append(left)
            else:
                unresolved += 1
                reasons[str(certificate["reason"])] = reasons.get(
                    str(certificate["reason"]), 0
                ) + 1
        if progress_every and processed % progress_every == 0:
            print(
                json.dumps(
                    {
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "excluded": excluded,
                        "max_depth": maximum_depth,
                        "pending": len(pending),
                        "positive": positive,
                        "processed": processed,
                        "unresolved": unresolved,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                flush=True,
            )
    return {
        "classification": (
            "POSITIVE_COMPLETE" if not pending and unresolved == 0 else "UNRESOLVED"
        ),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "excluded_leaf_count": excluded,
        "maximum_depth": maximum_depth,
        "pending_count": len(pending),
        "positive_leaf_count": positive,
        "processed_count": processed,
        "reason_counts": dict(sorted(reasons.items())),
        "schema": "anysolver.s4.e4-pl-q1h-coverage-diagnostic-v1",
        "unresolved_leaf_count": unresolved,
    }


def run_cover_parallel(
    *,
    contract_sha256: str,
    max_processed: int,
    max_depth: int,
    workers: int,
    wall_seconds: float,
) -> dict[str, object]:
    frontier = [ROOT]
    processed = positive = excluded = unresolved = 0
    maximum_depth = 0
    reasons: dict[str, int] = {}
    leaves: list[dict[str, object]] = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        while frontier and processed < max_processed:
            if time.monotonic() - started >= wall_seconds:
                break
            capacity = max_processed - processed
            active = frontier[:capacity]
            deferred = frontier[capacity:]
            outcomes = tuple(executor.map(_evaluate_box, active, chunksize=1))
            next_frontier: list[Box] = []
            for box, (classification, reason, certificate) in zip(
                active, outcomes, strict=True
            ):
                processed += 1
                maximum_depth = max(maximum_depth, box.depth)
                if classification == "EXCLUDED":
                    excluded += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
                    leaves.append(_leaf_record(box, classification, reason, certificate))
                elif classification == "POSITIVE":
                    positive += 1
                    leaves.append(_leaf_record(box, classification, reason, certificate))
                elif box.depth < max_depth:
                    next_frontier.extend(box.split())
                else:
                    unresolved += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
            frontier = next_frontier + deferred
            print(
                json.dumps(
                    {
                        "depth": maximum_depth,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "excluded": excluded,
                        "frontier": len(frontier),
                        "positive": positive,
                        "processed": processed,
                        "unresolved": unresolved,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                flush=True,
            )
    leaves.sort(key=lambda row: str(row["path"]))
    if not frontier and unresolved == 0:
        verify_leaf_partition(leaves)
    leaf_bytes = _canonical_bytes(leaves)
    complete = not frontier and unresolved == 0
    return {
        "alpha_star": [1, 1_000_000],
        "candidate_id": "candidate_e4_pl_q1h.wg2020_continuous_domain_coercivity_v1",
        "classification": (
            "PROVISIONAL_GO_E4_PL_Q1H_DOMAIN_COERCIVITY"
            if complete
            else "UNCLASSIFIED_E4_PL_Q1H_INTERVAL_COVERAGE"
        ),
        "contract_sha256": contract_sha256,
        "coverage_complete": complete,
        "excluded_leaf_count": excluded,
        "leaf_records": leaves,
        "maximum_depth": maximum_depth,
        "pending_count": len(frontier),
        "partition_sha256": hashlib.sha256(leaf_bytes).hexdigest().upper(),
        "positive_leaf_count": positive,
        "processed_count": processed,
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "reason_counts": dict(sorted(reasons.items())),
        "root_bounds": _leaf_record(ROOT, "ROOT", "REGISTERED_SUPERSET", None)["bounds"],
        "schema": "anysolver.s4.e4-pl-q1h-domain-coverage-v1",
        "study_id": "study_e4_pl_q1h.q1g_executable_domain_closure_v1",
        "unresolved_leaf_count": unresolved,
        "worker_count": workers,
    }


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def validate_contract(path: Path, claimed_sha256: str) -> dict[str, object]:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != claimed_sha256.upper():
        raise ValueError("contract hash mismatch")
    value = json.loads(
        raw,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON token {token}")
        ),
    )
    if raw != _canonical_bytes(value):
        raise ValueError("contract is not strict canonical JSON")
    if value.get("schema") != "anysolver.s4.e4-pl-q1h-domain-contract-v1":
        raise ValueError("unexpected contract schema")
    for row in value.get("inputs", []):
        source = Path(str(row["path"]))
        data = source.read_bytes()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest().upper() != row["sha256"]:
            raise ValueError(f"contract input mismatch: {source}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-processed", type=int, default=10_000)
    parser.add_argument("--max-depth", type=int, default=32)
    parser.add_argument("--progress-every", type=int, default=1_000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--wall-seconds", type=float, default=600.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    args = parser.parse_args()
    if args.max_processed <= 0 or args.max_depth < 0 or args.progress_every < 0:
        parser.error("bounds must be positive/nonnegative")
    if args.workers <= 0 or args.wall_seconds <= 0:
        parser.error("workers and wall seconds must be positive")
    validate_contract(args.contract, args.contract_sha256)
    result = run_cover_parallel(
        contract_sha256=args.contract_sha256.upper(),
        max_processed=args.max_processed,
        max_depth=args.max_depth,
        workers=args.workers,
        wall_seconds=args.wall_seconds,
    )
    payload = _canonical_bytes(result)
    if args.output is None:
        print(payload.decode(), end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if args.output.read_bytes() != payload:
            raise RuntimeError("canonical coverage output did not reopen byte-identically")
    return 0 if result["coverage_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
