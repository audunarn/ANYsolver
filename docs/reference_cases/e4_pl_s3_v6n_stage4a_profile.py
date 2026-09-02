"""Bounded, nonclassifying profiler for the frozen V2D Stage-4A leaf.

This program exists only to localize the V6M N80 timeout.  It reconstructs the
unchanged Stage-4A operations in their original order, emits a checkpoint after
each expensive stage, and never emits scientific evidence or a terminal that
can adjudicate S3.  The controller places the complete child tree in the same
24-GiB Windows Job Object used by the formal bounded runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
from typing import Any, Mapping, Sequence


REFERENCE = Path(__file__).resolve().parent
ADAPTER_PATH = REFERENCE / "e4_pl_s3_v6h_stage4a_adapter.py"
BOUNDED_PATH = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
MANIFEST_PATH = REFERENCE / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
CANDIDATE_ARCHIVE_PATH = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6k-2d91bba2\candidate-source.tar"
)
DEPENDENCY_ARCHIVE_PATH = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6l-dependency-closure\anyfileio-source.tar"
)
OPTIMIZED_CANDIDATE_ARCHIVE_PATH = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6n-lease-optimization-c1e2ad9\candidate-source.tar"
)

ADAPTER_SHA256 = "2C70B6B952CB7100ED1ED7C3E9BAB867C634BD11497422DF2916D045948E54C5"
BOUNDED_SHA256 = "C5B192C9C3F6EE2C68A42AB4A0CFBCDBE81581381B800C13AACCE0BB219A3383"
MANIFEST_SHA256 = "3EA7ABD0B332831D62B30B3CD52E0DB85EC951B125340FFAF40A891DC37BD589"
CANDIDATE_ARCHIVE_SHA256 = "AC1EA6D71A273355439B25F915EE7BB383DC60769F22EEA8CC84095CDDAF426F"
DEPENDENCY_ARCHIVE_SHA256 = "ABDFD6F6B6E04185FD277E4EE80400FA05B702BD43BA50851C4F9E85A5970C90"
OPTIMIZED_CANDIDATE_ARCHIVE_SHA256 = "DBEFBF12554832962C375F0CD827BE5310E0507145A5B6C84CFD68EB9BC2ABA1"
SCHEMA = "anysolver.e4-pl-s3-v6n-stage4a-nonclassifying-profile-v1"
RESULT_SCHEMA = "anysolver.e4-pl-s3-v6n-stage4a-bounded-profile-result-v1"
MAX_WALL_SECONDS = 600
MEMORY_LIMIT_BYTES = 24 * 1024**3
ALLOWED_RECORD_IDS = tuple(
    f"N80:10PCT:dispersed:{diagonal}"
    for diagonal in ("slash", "backslash", "alternating")
)
COMPARISON_RECORDS = {
    "N20:1PCT:dispersed:slash": (
        Path(
            r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6m-validator-safe\wave-02\worker-1\scientific.json"
        ),
        "78C097500A5901E0B969DAA8FDAB38ACF88EFCA4B07251F0FC94B71D953E78C2",
    ),
    "N40:10PCT:dispersed:slash": (
        Path(
            r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6m-validator-safe\wave-15\worker-1\scientific.json"
        ),
        "A207D2B4809E5EF631D878B6C9F0E9D81D0C489751D771B5B145217B44E67D75",
    ),
}


class ProfileError(RuntimeError):
    """Raised when a diagnostic binding or output is invalid."""


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _publish_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def _require_bindings() -> None:
    expected = {
        ADAPTER_PATH: ADAPTER_SHA256,
        BOUNDED_PATH: BOUNDED_SHA256,
        MANIFEST_PATH: MANIFEST_SHA256,
        CANDIDATE_ARCHIVE_PATH: CANDIDATE_ARCHIVE_SHA256,
        DEPENDENCY_ARCHIVE_PATH: DEPENDENCY_ARCHIVE_SHA256,
        OPTIMIZED_CANDIDATE_ARCHIVE_PATH: OPTIMIZED_CANDIDATE_ARCHIVE_SHA256,
    }
    for path, digest in expected.items():
        if not path.is_file() or path.is_symlink() or _sha256_path(path) != digest:
            raise ProfileError(f"frozen diagnostic input differs: {path.name}")


def _member(record_id: str) -> dict[str, Any]:
    if record_id not in ALLOWED_RECORD_IDS and record_id not in COMPARISON_RECORDS:
        raise ProfileError("record is outside the registered diagnostic sets")
    level_text, fraction, mask, diagonal = record_id.split(":")
    wanted_level = int(level_text.removeprefix("N"))
    wanted_fraction = int(fraction.removesuffix("PCT"))
    manifest = json.loads(MANIFEST_PATH.read_bytes())
    matches = [
        (index, record)
        for index, record in enumerate(manifest["records"])
        if int(record["level"]) == wanted_level
        and int(record["s3_area_fraction_percent"]) == wanted_fraction
        and str(record["mask"]) == mask
        and str(record["diagonal"]) == diagonal
    ]
    if len(matches) != 1:
        raise ProfileError("registered timeout record is not unique")
    index, record = matches[0]
    return {"manifest_index": index, "record": record, "record_id": record_id}


class _Progress:
    def __init__(self, path: Path, record_id: str) -> None:
        self._stream = path.open("xb", buffering=0)
        self._record_id = record_id
        self._sequence = 0
        self._wall_origin = time.monotonic()
        self._cpu_origin = time.process_time()

    def emit(self, phase: str, **counts: int) -> None:
        self._sequence += 1
        record = {
            "counts": {key: int(value) for key, value in sorted(counts.items())},
            "cpu_seconds": round(time.process_time() - self._cpu_origin, 6),
            "phase": phase,
            "record_id": self._record_id,
            "sequence": self._sequence,
            "wall_seconds": round(time.monotonic() - self._wall_origin, 6),
        }
        self._stream.write(_canonical(record))
        os.fsync(self._stream.fileno())

    def close(self) -> None:
        self._stream.close()


def _array_hash(array: Any) -> str:
    import numpy as np

    made = np.ascontiguousarray(array)
    header = f"{made.dtype.str}|{','.join(map(str, made.shape))}|".encode("ascii")
    return _sha256_bytes(header + made.tobytes(order="C"))


def _require_extracted_root(root: Path, marker: Path) -> None:
    resolved = root.resolve()
    required = (resolved / marker).resolve()
    try:
        required.relative_to(resolved)
    except ValueError as exc:
        raise ProfileError("extracted marker escapes its root") from exc
    if not required.is_file() or required.is_symlink():
        raise ProfileError(f"extracted environment marker is absent: {marker}")


def run_worker(
    record_id: str,
    progress_path: Path,
    output_path: Path,
    candidate_root: Path,
    dependency_root: Path,
) -> dict[str, Any]:
    """Run the original leaf operations with diagnostic checkpoints only."""

    _require_bindings()
    _require_extracted_root(candidate_root, Path("src/anysolver/__init__.py"))
    _require_extracted_root(dependency_root, Path("src/anyfileio/__init__.py"))
    member = _member(record_id)
    progress = _Progress(progress_path, record_id)
    try:
        progress.emit("IDENTITY_COMPLETE")
        sys.path.insert(0, str(REFERENCE))
        import e4_pl_s3_v6h_stage4a_adapter as adapter

        base = adapter.configure()
        base._ACTIVE_CANDIDATE_ROOT = candidate_root.resolve()
        model, kinds, element_counts, combined_counts = adapter.build_model_for_validation(
            member["record"]
        )
        progress.emit(
            "MODEL_BUILT",
            elements=len(model.mesh.elements),
            nodes=len(model.mesh.nodes),
        )
        reference, reference_digest, reference_center = base.mindlin_nodal_reference(80)
        progress.emit("REFERENCE_BUILT", dofs=int(reference.size))

        import numpy as np
        from scipy.sparse.linalg import spsolve
        from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix

        stiffness, _assembly = assemble_stiffness_matrix(model)
        progress.emit(
            "STIFFNESS_ASSEMBLED",
            matrix_dimension=int(stiffness.shape[0]),
            nonzeros=int(stiffness.nnz),
        )
        load, _load_info = assemble_load_vector(model, model.load_cases[0])
        progress.emit("LOAD_ASSEMBLED", load_entries=int(load.size))
        model.apply_boundary_conditions()
        fixed = np.asarray(sorted(model.mesh.dof_manager._constrained_dofs), dtype=np.intp)
        free_mask = np.ones(stiffness.shape[0], dtype=bool)
        free_mask[fixed] = False
        free = np.flatnonzero(free_mask)
        progress.emit("BOUNDARY_EXTRACTED", fixed_dofs=int(fixed.size), free_dofs=int(free.size))
        free_stiffness = stiffness[free][:, free]
        free_load = load[free]
        progress.emit("FREE_MATRIX_SLICED", nonzeros=int(free_stiffness.nnz))
        solution = np.zeros(stiffness.shape[0], dtype=float)
        solution[free] = spsolve(free_stiffness, free_load)
        if not np.all(np.isfinite(solution)):
            raise ProfileError("direct sparse solution contains nonfinite values")
        progress.emit("SOLVE_COMPLETE", solution_entries=int(solution.size))

        residual = stiffness[free] @ solution - free_load
        stiffness_solution = stiffness @ solution
        stiffness_reference = stiffness @ reference
        solution_total = float(solution @ stiffness_solution)
        reference_total = float(reference @ stiffness_reference)
        cross = float(solution @ stiffness_reference)
        error_total = max(solution_total + reference_total - 2.0 * cross, 0.0)
        residual_relative = float(
            np.linalg.norm(residual)
            / max(np.linalg.norm(free_load), np.finfo(float).tiny)
        )
        progress.emit("ENERGY_COMPLETE")

        component_quadratics = {
            "physical": 0.0,
            "q4_pl": 0.0,
            "s3_pl": 0.0,
            "q4_hourglass": 0.0,
        }
        material = model.get_material("phase4a_steel")
        total_elements = len(model.mesh.elements)
        for completed, (element_id, element) in enumerate(model.mesh.elements.items(), 1):
            mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
            local = solution[mapping]
            components = element.compute_stiffness_components(model.mesh, material)
            component_quadratics["physical"] += float(local @ components["physical"] @ local)
            if kinds[int(element_id)] == "Q4":
                component_quadratics["q4_pl"] += float(local @ components["pl"] @ local)
                component_quadratics["q4_hourglass"] += float(
                    local @ components["hourglass"] @ local
                )
            else:
                component_quadratics["s3_pl"] += float(local @ components["pl"] @ local)
            if completed % 500 == 0 or completed == total_elements:
                progress.emit(
                    "COMPONENT_PROGRESS",
                    completed_elements=completed,
                    total_elements=total_elements,
                )
        reconstruction = sum(component_quadratics.values())
        if abs(reconstruction - solution_total) > 2.0e-10 * max(abs(solution_total), 1.0):
            raise ProfileError("component energies do not reconstruct total energy")
        progress.emit("COMPONENT_COMPLETE", elements=total_elements)
        made = {
            "classification": "NONCLASSIFYING_RUNTIME_DIAGNOSTIC_ONLY",
            "hashes": {
                "free_load": _array_hash(free_load),
                "reference": _array_hash(reference),
                "solution": _array_hash(solution),
            },
            "identities": {
                "adapter_sha256": ADAPTER_SHA256,
                "bounded_process_sha256": BOUNDED_SHA256,
                "manifest_sha256": MANIFEST_SHA256,
                "reference_sha256": reference_digest,
            },
            "measurements": {
                "component_reconstruction": reconstruction,
                "energy_error_total": error_total,
                "reference_center": reference_center,
                "residual_relative": residual_relative,
                "solution_total": solution_total,
            },
            "record_id": record_id,
            "schema": SCHEMA,
        }
        _publish_exclusive(output_path, made)
        progress.emit("DIAGNOSTIC_COMPLETE")
        return made
    finally:
        progress.close()


def run_equivalence_worker(
    record_id: str,
    output_path: Path,
    candidate_root: Path,
    dependency_root: Path,
) -> dict[str, Any]:
    """Compare one optimized record with preserved V6M scientific output."""

    _require_bindings()
    if record_id not in COMPARISON_RECORDS:
        raise ProfileError("record is outside the frozen equivalence pair")
    _require_extracted_root(candidate_root, Path("src/anysolver/__init__.py"))
    _require_extracted_root(dependency_root, Path("src/anyfileio/__init__.py"))
    reference_path, reference_sha256 = COMPARISON_RECORDS[record_id]
    if _sha256_path(reference_path) != reference_sha256:
        raise ProfileError("preserved V6M comparison wrapper differs")
    preserved = json.loads(reference_path.read_bytes())
    if preserved.get("record_ids") != [record_id]:
        raise ProfileError("preserved V6M comparison record ID differs")
    old_record = preserved["scientific_payload"]["record"]

    sys.path.insert(0, str(REFERENCE))
    import e4_pl_s3_v6h_stage4a_adapter as adapter

    base = adapter.configure()
    base._ACTIVE_CANDIDATE_ROOT = candidate_root.resolve()
    new_record = adapter.produce_case(_member(record_id))
    old_raw = _canonical(old_record)
    new_raw = _canonical(new_record)
    made = {
        "classification": "NONCLASSIFYING_BYTE_EQUIVALENCE_DIAGNOSTIC_ONLY",
        "equal": old_raw == new_raw,
        "optimized_candidate_archive_sha256": OPTIMIZED_CANDIDATE_ARCHIVE_SHA256,
        "optimized_record_sha256": _sha256_bytes(new_raw),
        "preserved_record_sha256": _sha256_bytes(old_raw),
        "preserved_wrapper_sha256": reference_sha256,
        "record_id": record_id,
        "schema": "anysolver.e4-pl-s3-v6n-guard-equivalence-v1",
    }
    _publish_exclusive(output_path, made)
    return made


def _environment() -> dict[str, str]:
    made = dict(os.environ)
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        made[key] = "1"
    made["PYTHONHASHSEED"] = "0"
    return made


def _extract_archive(archive: Path, destination: Path) -> None:
    """Extract a frozen Git archive after rejecting links and path traversal."""

    destination.mkdir(parents=True, exist_ok=False)
    resolved = destination.resolve()
    with tarfile.open(archive, "r") as package:
        for member in package.getmembers():
            target = (resolved / member.name).resolve()
            try:
                target.relative_to(resolved)
            except ValueError as exc:
                raise ProfileError("archive member escapes extraction root") from exc
            if member.issym() or member.islnk() or member.isdev():
                raise ProfileError("archive contains a link or device member")
        package.extractall(resolved, filter="data")


def run_bounded(
    record_id: str,
    output_dir: Path,
    wall_seconds: int,
    *,
    mode: str = "profile",
) -> dict[str, Any]:
    """Launch one profiler child with a hard process-tree wall and memory cap."""

    _require_bindings()
    _member(record_id)
    if mode == "profile" and record_id not in ALLOWED_RECORD_IDS:
        raise ProfileError("profile mode requires one V6M timeout record")
    if mode == "equivalence" and record_id not in COMPARISON_RECORDS:
        raise ProfileError("equivalence mode requires one preserved comparison record")
    if mode not in {"profile", "equivalence"}:
        raise ProfileError("unknown bounded diagnostic mode")
    if not 1 <= wall_seconds <= MAX_WALL_SECONDS:
        raise ProfileError("diagnostic wall must be between 1 and 600 seconds")
    output_dir.mkdir(parents=True, exist_ok=False)
    candidate_root = output_dir / "candidate"
    dependency_root = output_dir / "dependency"
    candidate_archive = (
        CANDIDATE_ARCHIVE_PATH
        if mode == "profile"
        else OPTIMIZED_CANDIDATE_ARCHIVE_PATH
    )
    _extract_archive(candidate_archive, candidate_root)
    _extract_archive(DEPENDENCY_ARCHIVE_PATH, dependency_root)
    progress_path = output_dir / "progress.jsonl"
    diagnostic_path = output_dir / "diagnostic.json"
    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"
    result_path = output_dir / "bounded-result.json"

    sys.path.insert(0, str(REFERENCE))
    import e4_pl_s3_v2_bounded_process as bounded

    job = bounded._ProcessJob(MEMORY_LIMIT_BYTES)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker" if mode == "profile" else "--equivalence-worker",
        "--record-id",
        record_id,
        "--progress",
        str(progress_path),
        "--output",
        str(diagnostic_path),
        "--candidate-root",
        str(candidate_root),
        "--dependency-root",
        str(dependency_root),
    ]
    started = time.monotonic()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = job.launch(
            command,
            cwd=Path(__file__).resolve().parents[2],
            env=_environment()
            | {
                "PYTHONPATH": os.pathsep.join(
                    (
                        str((candidate_root / "src").resolve()),
                        str((dependency_root / "src").resolve()),
                    )
                )
            },
            stdout=stdout,
            stderr=stderr,
        )
        status = "RUNNING"
        termination_proven = False
        try:
            while process.poll() is None and time.monotonic() - started < wall_seconds:
                time.sleep(0.5)
            if process.poll() is None:
                status = "TIMEOUT"
                termination_proven = job.terminate(124)
            else:
                _, active, _ = job.accounting()
                deadline = time.monotonic() + 15.0
                while active and time.monotonic() < deadline:
                    time.sleep(0.05)
                    _, active, _ = job.accounting()
                termination_proven = active == 0
                status = "COMPLETED" if process.returncode == 0 else "FAILED"
            cpu_100ns, active, peak_memory = job.accounting()
            termination_proven = termination_proven and active == 0
        finally:
            if process.poll() is None:
                termination_proven = job.terminate(124) and termination_proven
            job.close()

    progress_raw = progress_path.read_bytes() if progress_path.exists() else b""
    diagnostic_raw = diagnostic_path.read_bytes() if diagnostic_path.exists() else b""
    last_phase = None
    progress_records = []
    for line in progress_raw.splitlines():
        progress_records.append(json.loads(line))
    if progress_records:
        last_phase = progress_records[-1]["phase"]
    made = {
        "classification": "NONCLASSIFYING_RUNTIME_DIAGNOSTIC_ONLY",
        "cpu_100ns": int(cpu_100ns),
        "diagnostic_bytes": len(diagnostic_raw),
        "diagnostic_sha256": _sha256_bytes(diagnostic_raw) if diagnostic_raw else None,
        "last_phase": last_phase,
        "peak_tree_memory_bytes": int(peak_memory),
        "progress_bytes": len(progress_raw),
        "progress_sha256": _sha256_bytes(progress_raw),
        "mode": mode,
        "record_id": record_id,
        "returncode": process.returncode,
        "schema": RESULT_SCHEMA,
        "status": status,
        "termination_proven": bool(termination_proven),
        "wall_limit_seconds": wall_seconds,
    }
    _publish_exclusive(result_path, made)
    return made


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--equivalence-worker", action="store_true")
    parser.add_argument("--run-bounded", action="store_true")
    parser.add_argument(
        "--record-id",
        choices=ALLOWED_RECORD_IDS + tuple(COMPARISON_RECORDS),
        required=True,
    )
    parser.add_argument("--progress", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--dependency-root", type=Path)
    parser.add_argument("--wall-seconds", type=int, default=MAX_WALL_SECONDS)
    parser.add_argument("--mode", choices=("profile", "equivalence"), default="profile")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if sum((args.worker, args.equivalence_worker, args.run_bounded)) != 1:
        raise SystemExit(
            "select exactly one of --worker, --equivalence-worker, or --run-bounded"
        )
    if args.worker:
        if (
            args.progress is None
            or args.output is None
            or args.candidate_root is None
            or args.dependency_root is None
        ):
            raise SystemExit(
                "--worker requires --progress, --output, --candidate-root, and "
                "--dependency-root"
            )
        run_worker(
            args.record_id,
            args.progress.resolve(),
            args.output.resolve(),
            args.candidate_root.resolve(),
            args.dependency_root.resolve(),
        )
        return 0
    if args.equivalence_worker:
        if (
            args.output is None
            or args.candidate_root is None
            or args.dependency_root is None
        ):
            raise SystemExit(
                "--equivalence-worker requires --output, --candidate-root, and "
                "--dependency-root"
            )
        made = run_equivalence_worker(
            args.record_id,
            args.output.resolve(),
            args.candidate_root.resolve(),
            args.dependency_root.resolve(),
        )
        return 0 if made["equal"] else 3
    if args.output_dir is None:
        raise SystemExit("--run-bounded requires --output-dir")
    made = run_bounded(
        args.record_id,
        args.output_dir.resolve(),
        args.wall_seconds,
        mode=args.mode,
    )
    return 0 if made["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
