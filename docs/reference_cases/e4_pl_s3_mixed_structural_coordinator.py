"""Run the three mixed-Q4/S3 structural shards concurrently under hard bounds."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
import os
from pathlib import Path
import sys
import time
from typing import Any, Sequence

from e4_pl_q1w_bounded_runner import ProcessResult, run_bounded_process
from e4_pl_s3_mixed_structural_common import (
    AGGREGATE_SCHEMA,
    ALLOWED_EXECUTION_EXTENT,
    BLOCKED,
    GATE_IDS,
    PROGRAM_PATHS,
    PRODUCTION_RESTRICTION,
    ROOT,
    SHARD_IDS,
    StructuralEvidenceError,
    canonical_bytes,
    choose_terminal,
    load_authorities,
    sha256,
    strict_json,
    validate_shard,
    verify_execution_identity,
    write_exclusive,
)


THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}


def _progress(phase: str, **extra: Any) -> None:
    sys.stderr.buffer.write(canonical_bytes({"phase": phase, **extra}))
    sys.stderr.buffer.flush()


def _discard_incomplete(path: Path, result: ProcessResult) -> None:
    if result.status != "COMPLETE" or result.peak_rss_bytes is None:
        path.unlink(missing_ok=True)


def _require_observed_rss(result: ProcessResult) -> ProcessResult:
    if result.status == "COMPLETE" and result.peak_rss_bytes is None:
        return replace(result, status="RSS_UNAVAILABLE")
    return result


def _source_environment(root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    github = root.parents[2] if root.parent.name == ".perf2-worktrees" else root.parent
    sources = [
        root / "src",
        github / "ANYgeometry" / "src",
        github / "ANYmaterial" / "src",
        github / "ANYmesh" / "src",
        github / "ANYfileIO" / "src",
    ]
    pieces = [str(path) for path in sources if path.is_dir()]
    inherited = environment.get("PYTHONPATH", "")
    if inherited:
        pieces.append(inherited)
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    return environment


def _read_shard(path: Path, expected_shard: str, authorities: Any) -> dict[str, Any]:
    raw = path.read_bytes()
    value = strict_json(raw, label=f"{expected_shard} shard")
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise StructuralEvidenceError(f"{expected_shard} shard is not canonical JSON")
    return validate_shard(value, expected_shard, authorities=authorities)


def adjudicate(
    authorities: Any,
    process_rows: dict[str, tuple[ProcessResult, Path, int, int]],
    *,
    execution_tier: str,
    workers_overlap: bool,
) -> dict[str, Any]:
    blocked = not workers_overlap
    shard_rows: list[dict[str, Any]] = []
    combined_status: dict[str, str] = {}
    for shard_id in SHARD_IDS:
        result, output, _started_ns, _finished_ns = process_rows[shard_id]
        shard_hash = ""
        terminal = ""
        statuses: dict[str, str] = {}
        coverage = {
            "executed_gate_count": 0,
            "gate_count": 0,
            "representative_only_gate_count": 0,
        }
        if result.status != "COMPLETE" or not output.is_file():
            blocked = True
        else:
            try:
                value = _read_shard(output, shard_id, authorities)
                if value["authority_sha256"] != sha256(authorities.input_raw):
                    raise StructuralEvidenceError("shard input authority hash mismatch")
                if value["execution_tier"] != execution_tier:
                    raise StructuralEvidenceError("shard execution tier mismatch")
                statuses = dict(value["gate_status"])
                overlap = set(combined_status) & set(statuses)
                if overlap:
                    raise StructuralEvidenceError(f"duplicate gate ownership: {sorted(overlap)}")
                combined_status.update(statuses)
                coverage = dict(value["coverage"])
                terminal = str(value["terminal_status"])
                shard_hash = sha256(output.read_bytes())
            except (StructuralEvidenceError, KeyError, TypeError, ValueError, OSError):
                blocked = True
        shard_rows.append(
            {
                "coverage": coverage,
                "gate_status": statuses,
                "process_status": result.status,
                "rss_observed": result.peak_rss_bytes is not None,
                "shard_id": shard_id,
                "shard_sha256": shard_hash,
                "terminal_status": terminal,
            }
        )
    if set(combined_status) != set(GATE_IDS):
        blocked = True
        for gate in set(GATE_IDS) - set(combined_status):
            combined_status[gate] = BLOCKED
    ordered_statuses = [combined_status[gate] for gate in GATE_IDS]
    terminal = choose_terminal(ordered_statuses, blocked=blocked)
    return {
        "authority": {
            "allowed_changed_paths": list(ALLOWED_EXECUTION_EXTENT),
            "candidate_commit": authorities.input["candidate"]["commit"],
            "candidate_parent": authorities.input["candidate"]["parent"],
            "candidate_subject": authorities.input["candidate"]["subject"],
            "candidate_tree": authorities.input["candidate"]["tree"],
            "connectivity_manifest_sha256": sha256(authorities.manifest_raw),
            "execution_commit": authorities.execution_commit,
            "execution_subject": authorities.execution_subject,
            "execution_tree": authorities.execution_tree,
            "input_sha256": sha256(authorities.input_raw),
            "program_sha256": {
                name: sha256(authorities.program_raw[name])
                for name in PROGRAM_PATHS
            },
            "qualification_contract_sha256": sha256(authorities.contract_raw),
            "tracked_worktree_clean": True,
        },
        "gate_status": {gate: combined_status[gate] for gate in GATE_IDS},
        "execution_tier": execution_tier,
        "process_policy": {
            "automatic_retry": False,
            "memory_limit_gib_per_process": 24,
            "numerical_threads_per_process": 1,
            "timeout_seconds_per_process": 600,
            "workers": 3,
        },
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": AGGREGATE_SCHEMA,
        "shards": shard_rows,
        "terminal": terminal,
        "worker_overlap_verified": workers_overlap,
    }


def _execute_cycle(
    *,
    authorities: Any,
    repository_root: Path,
    input_path: Path,
    producer: Path,
    output_directory: Path,
    quick_smoke: bool,
) -> dict[str, Any]:
    output_directory.mkdir(parents=True, exist_ok=False)
    environment = _source_environment(repository_root)
    execution = authorities.input["execution"]
    timeout = int(execution["timeout_seconds_per_process"])
    memory = int(execution["memory_limit_gib_per_process"]) * 1024**3
    _progress("STRUCTURAL_SHARD_WAVE_INITIALIZED", shard_count=3, workers=3)

    def run_one(shard_id: str) -> tuple[str, ProcessResult, Path, int, int]:
        slug = shard_id.lower()
        shard_directory = output_directory / slug
        shard_directory.mkdir(parents=False, exist_ok=False)
        output = shard_directory / "shard.json"
        command = [
            sys.executable,
            str(producer),
            "--emit-structural-shard",
            "--input",
            str(input_path),
            "--shard-id",
            shard_id,
            "--output",
            str(output),
        ]
        if quick_smoke:
            command.append("--quick-smoke")
        started_ns = time.monotonic_ns()
        result = run_bounded_process(
            command,
            cwd=shard_directory,
            environment=environment,
            stdout_path=shard_directory / "stdout.log",
            stderr_path=shard_directory / "progress.jsonl",
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
        )
        finished_ns = time.monotonic_ns()
        result = _require_observed_rss(result)
        write_exclusive(
            shard_directory / "process.json",
            {
                "elapsed_ms": result.elapsed_ms,
                "finished_monotonic_ns": finished_ns,
                "peak_rss_bytes": (
                    result.peak_rss_bytes if result.peak_rss_bytes is not None else -1
                ),
                "returncode": result.returncode if result.returncode is not None else -1,
                "shard_id": shard_id,
                "started_monotonic_ns": started_ns,
                "status": result.status,
            },
        )
        _discard_incomplete(output, result)
        return shard_id, result, output, started_ns, finished_ns

    rows: dict[str, tuple[ProcessResult, Path, int, int]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run_one, shard_id) for shard_id in SHARD_IDS]
        for future in as_completed(futures):
            shard_id, result, output, started_ns, finished_ns = future.result()
            rows[shard_id] = (result, output, started_ns, finished_ns)
            _progress("STRUCTURAL_SHARD_TERMINAL", shard_id=shard_id, status=result.status)
    if set(rows) != set(SHARD_IDS):
        raise StructuralEvidenceError("not every launched shard reached a process terminal")
    workers_overlap = max(row[2] for row in rows.values()) < min(
        row[3] for row in rows.values()
    )
    return adjudicate(
        authorities,
        rows,
        execution_tier="QUICK_NONCLASSIFYING" if quick_smoke else "FORMAL_BOUNDED",
        workers_overlap=workers_overlap,
    )


def execute(
    *,
    repository_root: Path,
    input_path: Path,
    producer_path: Path,
    output_directory: Path,
    quick_smoke: bool,
) -> dict[str, Any]:
    # Full authority and clean-HEAD validation completes before mechanics are
    # launched. The coordinator imports neither mechanics nor NumPy/SciPy.
    repository_root = Path(repository_root).resolve(strict=True)
    if repository_root != ROOT.resolve(strict=True):
        raise StructuralEvidenceError("repository root differs from the frozen program authority")
    input_path = Path(input_path).resolve(strict=True)
    producer = Path(producer_path).resolve(strict=True)
    output_directory = Path(output_directory).resolve()
    authorities = load_authorities(input_path)
    if (
        producer.is_symlink()
        or not producer.is_file()
        or producer != authorities.program_paths["producer"]
        or sha256(producer.read_bytes()) != sha256(authorities.program_raw["producer"])
    ):
        raise StructuralEvidenceError("producer differs from its frozen program authority")
    output_directory.mkdir(parents=True, exist_ok=False)
    cycles: list[dict[str, Any]] = []
    cycle_raw: list[bytes] = []
    for cycle in (1, 2):
        _progress("STRUCTURAL_CYCLE_INITIALIZED", cycle=cycle)
        made = _execute_cycle(
            authorities=authorities,
            repository_root=repository_root,
            input_path=input_path,
            producer=producer,
            output_directory=output_directory / f"cycle-{cycle}",
            quick_smoke=quick_smoke,
        )
        cycles.append(made)
        cycle_raw.append(canonical_bytes(made))
        verify_execution_identity(authorities)
        _progress("STRUCTURAL_CYCLE_COMPLETED", cycle=cycle, terminal=made["terminal"])
    identical = cycle_raw[0] == cycle_raw[1]
    final = dict(cycles[0])
    final["cycle_agreement"] = {
        "byte_identical": identical,
        "canonical_cycle_count": 2,
        "cycle_payload_sha256": [sha256(raw) for raw in cycle_raw],
        "fresh_distinct_directories": True,
        "schema": "anysolver.e4-pl-s3-mixed-structural-cycle-agreement-v1",
    }
    if not identical:
        final["gate_status"] = {gate: BLOCKED for gate in GATE_IDS}
        final["terminal"] = choose_terminal(list(final["gate_status"].values()), blocked=True)
    return final


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-bounded-structural", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--aggregate", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--memory-limit-gib", type=int, default=24)
    parser.add_argument("--quick-smoke", action="store_true")
    args = parser.parse_args(argv)
    try:
        if (args.workers, args.timeout_seconds, args.memory_limit_gib) != (3, 600, 24):
            raise StructuralEvidenceError("formal controls are fixed at 3 workers/600 s/24 GiB")
        repository_root = args.repository_root.resolve(strict=True)
        input_path = args.input.resolve(strict=True)
        producer_path = args.producer.resolve(strict=True)
        output_directory = args.output_directory.resolve()
        aggregate_path = args.aggregate.resolve()
        if aggregate_path.is_relative_to(output_directory):
            raise StructuralEvidenceError("canonical aggregate must be outside diagnostics")
        value = execute(
            repository_root=repository_root,
            input_path=input_path,
            producer_path=producer_path,
            output_directory=output_directory,
            quick_smoke=bool(args.quick_smoke),
        )
        write_exclusive(aggregate_path, value)
        return 2 if value["terminal"].startswith("BLOCKED_") else 0
    except (StructuralEvidenceError, KeyError, TypeError, ValueError, OSError) as exc:
        print(f"mixed structural coordinator blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
