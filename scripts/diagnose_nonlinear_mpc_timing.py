"""Measure short prescribed-MPC timing variance without adjudicating a gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMBA_NUM_THREADS": "1",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _distribution(values: Sequence[float]) -> dict[str, float | int]:
    samples = [float(value) for value in values]
    if not samples:
        raise ValueError("timing distribution is empty")
    ordered = sorted(samples)
    median = float(statistics.median(ordered))
    deviations = [abs(value - median) for value in ordered]
    if len(ordered) > 1:
        quartiles = statistics.quantiles(ordered, n=4, method="inclusive")
        q1 = float(quartiles[0])
        q3 = float(quartiles[2])
    else:
        q1 = ordered[0]
        q3 = ordered[0]
    mean = float(statistics.mean(ordered))
    return {
        "count": len(ordered),
        "minimum": ordered[0],
        "q1": q1,
        "median": median,
        "q3": q3,
        "maximum": ordered[-1],
        "mean": mean,
        "stdev": (
            float(statistics.stdev(ordered)) if len(ordered) > 1 else 0.0
        ),
        "median_absolute_deviation": float(statistics.median(deviations)),
    }


def summarize_pairs(pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not pairs:
        raise ValueError("diagnostic pair inventory is empty")

    def values(revision: str, field: str) -> list[float]:
        return [float(pair[revision][field]) for pair in pairs]

    baseline_route = values("baseline", "complete_route_wall_seconds")
    candidate_route = values("candidate", "complete_route_wall_seconds")
    baseline_solver = values("baseline", "solver_seconds")
    candidate_solver = values("candidate", "solver_seconds")
    baseline_build = [
        route - solver
        for route, solver in zip(baseline_route, baseline_solver)
    ]
    candidate_build = [
        route - solver
        for route, solver in zip(candidate_route, candidate_solver)
    ]
    paired_route_reductions = [
        (baseline - candidate) / baseline
        for baseline, candidate in zip(baseline_route, candidate_route)
    ]
    paired_solver_reductions = [
        (baseline - candidate) / baseline
        for baseline, candidate in zip(baseline_solver, candidate_solver)
    ]
    baseline_route_summary = _distribution(baseline_route)
    candidate_route_summary = _distribution(candidate_route)
    baseline_solver_summary = _distribution(baseline_solver)
    candidate_solver_summary = _distribution(candidate_solver)
    physical_hashes = {
        str(pair[revision]["physical_sha256"])
        for pair in pairs
        for revision in ("baseline", "candidate")
    }
    work_payloads = {
        json.dumps(pair[revision]["work"], sort_keys=True)
        for pair in pairs
        for revision in ("baseline", "candidate")
    }
    baseline_route_median = float(baseline_route_summary["median"])
    candidate_route_median = float(candidate_route_summary["median"])
    baseline_solver_median = float(baseline_solver_summary["median"])
    candidate_solver_median = float(candidate_solver_summary["median"])
    return {
        "route_seconds": {
            "baseline": baseline_route_summary,
            "candidate": candidate_route_summary,
            "separate_median_reduction_fraction": (
                baseline_route_median - candidate_route_median
            )
            / baseline_route_median,
            "paired_reduction_fraction": _distribution(
                paired_route_reductions
            ),
        },
        "solver_seconds": {
            "baseline": baseline_solver_summary,
            "candidate": candidate_solver_summary,
            "separate_median_reduction_fraction": (
                baseline_solver_median - candidate_solver_median
            )
            / baseline_solver_median,
            "paired_reduction_fraction": _distribution(
                paired_solver_reductions
            ),
        },
        "model_build_seconds": {
            "baseline": _distribution(baseline_build),
            "candidate": _distribution(candidate_build),
        },
        "physical_hash_count": len(physical_hashes),
        "work_signature_count": len(work_payloads),
        "physical_match": len(physical_hashes) == 1,
        "work_match": len(work_payloads) == 1,
    }


def _run_sample(
    *,
    runner: Path,
    site: Path,
    manifest: Path,
    case: str,
    timeout_seconds: float,
    log_path: Path,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(runner),
        "--worker",
        "--site",
        str(site),
        "--manifest",
        str(manifest),
        "--case",
        case,
        "--method",
        "never",
    ]
    env = os.environ.copy()
    env.update(THREAD_ENV)
    completed = subprocess.run(
        command,
        cwd=runner.parent.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(
            f"diagnostic worker failed with exit code {completed.returncode}; "
            f"see {log_path}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    try:
        sample = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"diagnostic worker produced malformed output; see {log_path}"
        ) from exc
    imported = Path(sample["identity"]["anysolver_module"]).resolve()
    try:
        imported.relative_to(site.resolve())
    except ValueError as exc:
        raise RuntimeError(
            f"worker imported {imported}, expected site {site.resolve()}"
        ) from exc
    return sample


def _write_report(result: Mapping[str, Any], path: Path) -> None:
    summary = result["summary"]
    route = summary["route_seconds"]
    solver = summary["solver_seconds"]
    build = summary["model_build_seconds"]
    lines = [
        "# Prescribed-motion/MPC timing variance diagnostic",
        "",
        "This diagnostic repeats the registered installed-worker route. It is "
        "not a qualification rerun and does not replace the formal NO-GO.",
        "",
        f"- Alternating pairs: {result['configuration']['pairs']}",
        f"- Physical hashes match: **{summary['physical_match']}**",
        f"- Work signatures match: **{summary['work_match']}**",
        "",
        "| Timing | Baseline median | Candidate median | Reduction |",
        "| --- | ---: | ---: | ---: |",
        (
            f"| Complete route | {route['baseline']['median']:.6f} s | "
            f"{route['candidate']['median']:.6f} s | "
            f"{route['separate_median_reduction_fraction']:.2%} |"
        ),
        (
            f"| Solver | {solver['baseline']['median']:.6f} s | "
            f"{solver['candidate']['median']:.6f} s | "
            f"{solver['separate_median_reduction_fraction']:.2%} |"
        ),
        (
            f"| Model build | {build['baseline']['median']:.6f} s | "
            f"{build['candidate']['median']:.6f} s | n/a |"
        ),
        "",
        "The paired complete-route reduction has median "
        f"{route['paired_reduction_fraction']['median']:.2%}, with a range "
        f"from {route['paired_reduction_fraction']['minimum']:.2%} to "
        f"{route['paired_reduction_fraction']['maximum']:.2%}.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--build-provenance", type=Path, required=True)
    parser.add_argument("--baseline-site", type=Path, required=True)
    parser.add_argument("--candidate-site", type=Path, required=True)
    parser.add_argument("--pairs", type=int, default=20)
    parser.add_argument(
        "--case",
        default="prescribed_mpc_beam_holdout",
    )
    parser.add_argument("--worker-timeout-seconds", type=float, default=300.0)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        raise SystemExit("--pairs must be positive")
    runner = Path(__file__).with_name("qualify_nonlinear_representative.py")
    manifest = args.manifest.resolve()
    provenance = args.build_provenance.resolve()
    baseline_site = args.baseline_site.resolve()
    candidate_site = args.candidate_site.resolve()
    started = datetime.now(timezone.utc).isoformat()
    pairs: list[dict[str, Any]] = []
    for pair_index in range(args.pairs):
        order = (
            ("baseline", "candidate")
            if pair_index % 2 == 0
            else ("candidate", "baseline")
        )
        pair: dict[str, Any] = {
            "pair": pair_index + 1,
            "order": list(order),
        }
        for revision in order:
            print(
                f"pair {pair_index + 1}/{args.pairs}: {revision}",
                flush=True,
            )
            site = baseline_site if revision == "baseline" else candidate_site
            pair[revision] = _run_sample(
                runner=runner,
                site=site,
                manifest=manifest,
                case=args.case,
                timeout_seconds=args.worker_timeout_seconds,
                log_path=(
                    args.log_dir.resolve()
                    / f"p{pair_index + 1}.{revision}.log"
                ),
            )
        pairs.append(pair)
    build_provenance = json.loads(provenance.read_text(encoding="utf-8"))
    result = {
        "schema": "anysolver.nonlinear_static.mpc_timing_diagnostic",
        "version": 1,
        "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "identity": {
            "manifest_sha256": _sha256(manifest),
            "build_provenance_sha256": _sha256(provenance),
            "runner_sha256": _sha256(runner),
            "diagnostic_sha256": _sha256(Path(__file__).resolve()),
            "baseline_revision": build_provenance["baseline_revision"],
            "candidate_revision": build_provenance["candidate_revision"],
            "baseline_wheel_sha256": build_provenance[
                "baseline_wheel_sha256"
            ],
            "candidate_wheel_sha256": build_provenance[
                "candidate_wheel_sha256"
            ],
            "baseline_site": str(baseline_site),
            "candidate_site": str(candidate_site),
        },
        "configuration": {
            "case": args.case,
            "pairs": args.pairs,
            "alternating_order": True,
            "worker_route": "one warm complete route, one measured complete route",
            "thread_environment": THREAD_ENV,
            "qualification_status": "diagnostic_only",
        },
        "pairs": pairs,
        "summary": summarize_pairs(pairs),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(result, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
