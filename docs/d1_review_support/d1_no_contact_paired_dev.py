"""Final-source preparation for the named 5% no-contact whole-route gate.

Run only after the D1 source is frozen, from the repository root::

    python docs/d1_review_support/d1_no_contact_paired_dev.py \
        --expected-head <full-final-commit-sha> --run-id <unique-run-id>

This reuses the retained, unmodified reports/d1_no_contact_shell_route.py
fixture. Each measurement is a fresh process and times its model construction
and solve after imports, with no same-process warm solve (the historical
"lazy_cold" contract). One excluded fresh-process preflight per source and case
warms filesystem/import caches. Twelve paired measurements per case alternate
baseline/current and current/baseline. The independent pairs are the sampling
units. The one-sided confidence bound is the smallest ordered paired time ratio
whose exact binomial coverage for the population median is at least 95%; no
normality assumption is needed. The gate requires that bound to be <= 1.05,
plus complete physical and identity parity. This is a final-source *candidate*
measurement; independent adjudication and all other D1 gates remain separate.

The worker exports displacement, convergence, load factor and contact-import
observables, but no complete reaction vector or beam MPC residual. Those are
outside this timing fixture and must be checked by the applicable mechanics
evidence. Do not edit the retained worker or replay its dated output names.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

import psutil


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "reports" / "d1_no_contact_shell_route.py"
BASELINE = ROOT / "reports" / "general_contact_nocontact_baseline_be41a77a" / "src"
CANDIDATE = ROOT / "src"
BASELINE_COMMIT = "be41a77a62e1cd7e1767bda6e955253af0819f91"
CASES = ("clamped_q4", "prescribed_mpc_beam")
THREAD_VARIABLES = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS")
CHILD_WALL_LIMIT = 180.0
CHILD_TREE_MEMORY_LIMIT = 1_000_000_000
OUTER_WALL_LIMIT = 900.0
OUTER_TREE_MEMORY_LIMIT = 4_000_000_000


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_tree_identity(source: Path) -> dict[str, object]:
    """Hash every Python source file, including untracked Python files."""
    root = source / "anysolver"
    files = sorted(root.rglob("*.py"))
    if not files or not (root / "__init__.py").is_file():
        raise RuntimeError(f"missing anysolver source: {root}")
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(source).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(_sha256(path)))
    return {"source": str(source.resolve()), "python_file_count": len(files),
            "tree_sha256": digest.hexdigest()}


def _verify_baseline_archive() -> dict[str, object]:
    """Compare every archived source file with the original Git blob."""
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "-z", BASELINE_COMMIT, "--", "src/anysolver"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    expected: dict[str, str] = {}
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise RuntimeError("baseline source contains unsupported Git entry")
        relative = raw_path.decode("utf-8").removeprefix("src/")
        expected[relative] = blob
    archived = {path.relative_to(BASELINE).as_posix(): path
                for path in (BASELINE / "anysolver").rglob("*.py")}
    if set(expected) != set(archived):
        raise RuntimeError("baseline archive file set differs from original commit")
    for relative, path in archived.items():
        # The retained Windows checkout has CRLF working-tree files while Git
        # stores the corresponding text blobs with LF line endings.
        content = path.read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha1(
            f"blob {len(content)}\0".encode("ascii") + content
        ).hexdigest()
        if actual != expected[relative]:
            raise RuntimeError(f"baseline archive blob mismatch: {relative}")
    return {"commit": BASELINE_COMMIT, "verified_git_blobs": len(expected),
            **_source_tree_identity(BASELINE)}


def _git_text(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _running_tree_bytes(worker: psutil.Process) -> int:
    total = 0
    try:
        processes = [worker, *worker.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0
    for process in processes:
        try:
            total += process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return total


def _stop_tree(worker: psutil.Process) -> None:
    try:
        children = worker.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        children = []
    for process in reversed(children):
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    try:
        worker.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


def _run_child(
    case: str, label: str, name: str, output: Path,
    deadline: float, environment: dict[str, str],
) -> dict[str, object]:
    source = BASELINE if label == "baseline" else CANDIDATE
    record_path = output / f"{name}.json"
    stdout_path = output / f"{name}.stdout.log"
    stderr_path = output / f"{name}.stderr.log"
    command = [sys.executable, str(WORKER), "--source", str(source),
               "--label", label, "--case", case, "--output", str(record_path)]
    if time.monotonic() > deadline:
        raise RuntimeError(f"{name}: outer_wall_limit_before_launch")
    start = time.monotonic()
    peak_tree_bytes = 0
    failure = None
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        process = subprocess.Popen(
            command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
        )
        owned = psutil.Process(process.pid)
        while process.poll() is None:
            elapsed = time.monotonic() - start
            tree_bytes = _running_tree_bytes(owned)
            peak_tree_bytes = max(peak_tree_bytes, tree_bytes)
            if elapsed > CHILD_WALL_LIMIT:
                failure = "child_wall_limit"
            elif time.monotonic() > deadline:
                failure = "outer_wall_limit"
            elif tree_bytes > CHILD_TREE_MEMORY_LIMIT:
                failure = "child_tree_memory_limit"
            elif tree_bytes + psutil.Process().memory_info().rss > OUTER_TREE_MEMORY_LIMIT:
                failure = "outer_tree_memory_limit"
            if failure:
                _stop_tree(owned)
                break
            time.sleep(0.05)
        return_code = process.wait(timeout=5)
    resource = {
        "command": command, "return_code": return_code,
        "elapsed_process_seconds": time.monotonic() - start,
        "sampled_peak_tree_rss_bytes": peak_tree_bytes,
        "limits": {"child_wall_seconds": CHILD_WALL_LIMIT,
                   "child_tree_memory_bytes": CHILD_TREE_MEMORY_LIMIT,
                   "outer_wall_seconds": OUTER_WALL_LIMIT,
                   "outer_tree_memory_bytes": OUTER_TREE_MEMORY_LIMIT},
        "failure": failure,
    }
    (output / f"{name}.resource.json").write_text(
        json.dumps(resource, indent=2) + "\n", encoding="utf-8"
    )
    if failure or return_code != 0 or not record_path.is_file():
        raise RuntimeError(f"{name}: {failure or f'child_exit_{return_code}'}")
    try:
        result = json.loads(record_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"{name}: invalid child record") from exc
    result["resource_record"] = f"{name}.resource.json"
    return result


def _check_identity(record: dict[str, object], label: str,
                    environment: dict[str, str]) -> None:
    source = BASELINE if label == "baseline" else CANDIDATE
    expected_module = (source / "anysolver" / "__init__.py").resolve()
    if (Path(str(record.get("source", ""))).resolve() != source.resolve()
            or Path(str(record.get("module", ""))).resolve() != expected_module):
        raise RuntimeError(f"{label}: effective anysolver module is not selected source")
    if record.get("contact_core_module_loaded") is not False:
        raise RuntimeError(f"{label}: contact core loaded on no-contact route")
    child_env = record.get("thread_environment")
    if not isinstance(child_env, dict) or any(
        child_env.get(name) != environment[name] for name in THREAD_VARIABLES
    ):
        raise RuntimeError(f"{label}: effective numerical thread settings differ")
    for key in ("python", "platform", "numpy", "scipy"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise RuntimeError(f"{label}: missing effective {key}")


def _check_physics(case: str, baseline: dict[str, object],
                   candidate: dict[str, object]) -> None:
    expected_steps = 40 if case == "clamped_q4" else 12
    for label, record in (("baseline", baseline), ("current", candidate)):
        if (record.get("case") != case or record.get("label") != label
                or record.get("warm_before_measure") is not False
                or record.get("status") != "completed"
                or record.get("steps") != expected_steps
                or record.get("contact_key_present") is not False):
            raise RuntimeError(f"{case}/{label}: route status or scope mismatch")
        if not math.isclose(float(record.get("load_factor", math.nan)), 1.0,
                            rel_tol=0.0, abs_tol=1e-12):
            raise RuntimeError(f"{case}/{label}: incomplete load factor")
        if not isinstance(record.get("newton_iterations"), int):
            raise RuntimeError(f"{case}/{label}: missing iteration count")
        if (not isinstance(record.get("whole_route_seconds"), (int, float))
                or not math.isfinite(float(record["whole_route_seconds"]))
                or float(record["whole_route_seconds"]) <= 0):
            raise RuntimeError(f"{case}/{label}: invalid whole-route time")
        if (not isinstance(record.get("peak_process_working_set_bytes"), int)
                or record["peak_process_working_set_bytes"] <= 0):
            raise RuntimeError(f"{case}/{label}: invalid peak working set")
    for key in ("steps", "newton_iterations", "displacement_digest_13dp",
                "python", "platform", "numpy", "scipy", "thread_environment"):
        if baseline.get(key) != candidate.get(key):
            raise RuntimeError(f"{case}: baseline/current {key} mismatch")
    if not math.isclose(float(baseline.get("displacement_norm_m", math.nan)),
                        float(candidate.get("displacement_norm_m", math.nan)),
                        rel_tol=1e-12, abs_tol=1e-13):
        raise RuntimeError(f"{case}: displacement norm mismatch")


def _upper_median_bound(ratios: list[float]) -> dict[str, float | int]:
    """Exact distribution-free upper bound for an independent population median."""
    n = len(ratios)
    ordered = sorted(ratios)
    for rank in range(1, n + 1):
        coverage = sum(math.comb(n, j) for j in range(rank)) / 2**n
        if coverage >= 0.95:
            return {"rank": rank, "coverage": coverage,
                    "one_sided_upper": ordered[rank - 1]}
    raise RuntimeError("too few pairs for a finite one-sided 95% median bound")


def _summarize(case: str, pairs: list[dict[str, object]]) -> dict[str, object]:
    ratios = [float(pair["current"]["whole_route_seconds"])
              / float(pair["baseline"]["whole_route_seconds"])
              for pair in pairs]
    bound = _upper_median_bound(ratios)
    memory = {label: [int(pair[label]["peak_process_working_set_bytes"])
                      for pair in pairs] for label in ("baseline", "current")}
    return {
        "case": case, "paired_ratios_current_over_baseline": ratios,
        "median_ratio": statistics.median(ratios),
        "ratio_range": [min(ratios), max(ratios)],
        "one_sided_median_upper_bound": bound,
        "peak_working_set_bytes": memory,
        "median_peak_working_set_bytes": {label: statistics.median(values)
                                           for label, values in memory.items()},
        "passes_5_percent_time_gate": bound["one_sided_upper"] <= 1.05,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True,
                        help="full SHA of the frozen final source commit")
    parser.add_argument("--run-id", required=True,
                        help="unique letters, numbers, underscores or hyphens")
    parser.add_argument("--pairs", type=int, default=12)
    parser.add_argument("--output-root", type=Path,
                        default=ROOT / "docs" / "d1_review_support" / "d1_no_contact_runs")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.run_id):
        parser.error("--run-id must be 1–64 letters, numbers, underscores or hyphens")
    if args.pairs < 6 or args.pairs % 2:
        parser.error("--pairs must be even and at least 6 for balanced AB/BA order")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.expected_head):
        parser.error("--expected-head must be a full 40-character commit SHA")
    if _git_text("rev-parse", "HEAD").lower() != args.expected_head.lower():
        raise RuntimeError("HEAD differs from the declared frozen final source")
    if _git_text("status", "--porcelain", "--untracked-files=all", "--", "src/anysolver"):
        raise RuntimeError("anysolver source is dirty; freeze the final source first")
    baseline_identity = _verify_baseline_archive()
    candidate_identity = _source_tree_identity(CANDIDATE)
    fixture_identity = {str(path.relative_to(ROOT)): _sha256(path)
                        for path in (WORKER,
                                     ROOT / "scripts" / "qualify_nonlinear_representative.py",
                                     ROOT / "docs" / "reference_cases"
                                     / "nonlinear_static_representative_manifest.json")}
    output = args.output_root.resolve() / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update({name: "1" for name in THREAD_VARIABLES})
    deadline = time.monotonic() + OUTER_WALL_LIMIT
    record: dict[str, object] = {
        "status": "running", "run_id": args.run_id,
        "source_identity": {"baseline": baseline_identity,
                            "current": {"head": args.expected_head.lower(),
                                        **candidate_identity}},
        "fixture_sha256": fixture_identity,
        "timing_scope": "fresh-process cold route: model construction and solve after imports",
        "preflight": "one excluded fresh-process run per source and case",
        "pair_order": "AB/BA alternating, exactly balanced",
        "pairs_per_case": args.pairs,
        "resource_caps": {"child_wall_seconds": CHILD_WALL_LIMIT,
                          "child_tree_memory_bytes": CHILD_TREE_MEMORY_LIMIT,
                          "outer_wall_seconds": OUTER_WALL_LIMIT,
                          "outer_tree_memory_bytes": OUTER_TREE_MEMORY_LIMIT},
        "statistical_rule": (
            "exact binomial one-sided >=95% upper confidence bound for "
            "population median paired current/baseline whole-route ratio <=1.05"
        ),
        "cases": {},
    }
    summary_path = output / "summary.json"
    try:
        for case in CASES:
            preflight = {}
            for label in ("baseline", "current"):
                sample = _run_child(case, label, f"{case}_preflight_{label}",
                                    output, deadline, environment)
                _check_identity(sample, label, environment)
                preflight[label] = sample
            _check_physics(case, preflight["baseline"], preflight["current"])
            pairs = []
            for index in range(args.pairs):
                order = (("baseline", "current") if index % 2 == 0
                         else ("current", "baseline"))
                pair: dict[str, object] = {"order": order}
                for label in order:
                    sample = _run_child(case, label,
                                        f"{case}_pair{index+1:02d}_{label}",
                                        output, deadline, environment)
                    _check_identity(sample, label, environment)
                    if sample["python"] != preflight[label]["python"] or any(
                        sample[key] != preflight[label][key]
                        for key in ("platform", "numpy", "scipy", "thread_environment")
                    ):
                        raise RuntimeError(f"{case}/{label}: effective environment changed")
                    if any(sample.get(key) != preflight[label].get(key) for key in (
                        "status", "steps", "newton_iterations", "load_factor",
                        "displacement_digest_13dp", "displacement_norm_m",
                        "contact_key_present", "contact_core_module_loaded",
                    )):
                        raise RuntimeError(f"{case}/{label}: physical result changed from preflight")
                    pair[label] = sample
                _check_physics(case, pair["baseline"], pair["current"])
                pairs.append(pair)
            result = _summarize(case, pairs)
            record["cases"][case] = result
            summary_path.write_text(json.dumps(record, indent=2) + "\n",
                                    encoding="utf-8")
        if _source_tree_identity(CANDIDATE) != candidate_identity:
            raise RuntimeError("candidate source changed during comparison")
        if _verify_baseline_archive() != baseline_identity:
            raise RuntimeError("baseline archive changed during comparison")
        if any(_sha256(ROOT / relative) != digest
               for relative, digest in fixture_identity.items()):
            raise RuntimeError("timing fixture changed during comparison")
        record["status"] = ("passes_named_time_screen" if all(
            result["passes_5_percent_time_gate"]
            for result in record["cases"].values()
        ) else "fails_named_time_screen")
    except BaseException as exc:
        record["status"] = "failed_or_incomplete"
        record["failure"] = f"{type(exc).__name__}: {exc}"
        summary_path.write_text(json.dumps(record, indent=2) + "\n",
                                encoding="utf-8")
        raise
    summary_path.write_text(json.dumps(record, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps({"status": record["status"], "summary": str(summary_path),
                      "cases": record["cases"]}, indent=2))
    return 0 if record["status"] == "passes_named_time_screen" else 2


if __name__ == "__main__":
    raise SystemExit(main())
