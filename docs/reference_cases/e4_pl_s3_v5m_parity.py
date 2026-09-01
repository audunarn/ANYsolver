"""Bounded V5M batch, stateless-restart, and installed-wheel parity gate."""

from __future__ import annotations

import argparse
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import zipfile


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v5m_parity_contract.json"
CHECKER = REFERENCE / "e4_pl_s3_v5m_checker.py"
PROCESS_GUARD = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
WORKER_IDS = ("BATCH_4096", "SERIALIZATION_RESTART", "PACKAGE_WHEEL")
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
BLOCKED = "BLOCKED_E4_PL_S3_V5M_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V5M_BATCH_RESTART_OR_PACKAGE_PARITY"
GO = "PROVISIONAL_GO_E4_PL_S3_V5M_PARITY_CLOSED_ONLY"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
WORKER_CONCURRENCY = 3
CHECKER_CONCURRENCY = 4
CYCLES = 2
BATCH_ELEMENT_COUNT = 4096
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5m-worker-proof-v1"


class V5MParityError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5MParityError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5MParityError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5MParityError(f"noncanonical JSON: {path}")
    return raw, value


def _git(*arguments: str, cwd: Path = ROOT) -> str:
    process = subprocess.run(["git", *arguments], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise V5MParityError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def validate_protocol() -> dict[str, Any]:
    _raw, contract = load(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5m-parity-contract-v1":
        raise V5MParityError("unexpected V5M contract schema")
    for row in contract.get("frozen_inputs", []):
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise V5MParityError(f"frozen input mismatch: {row['path']}")
    boundary = contract.get("production_boundary")
    if boundary != {"activation_authorized": False, "default_q4_formulation": "e4-pl", "default_s3_formulation": "legacy-s3", "q4_mechanics_unchanged": True}:
        raise V5MParityError("V5M production boundary changed")
    return contract


def _inject_source_paths() -> None:
    paths = [ROOT / "src"]
    for parent in (ROOT, *ROOT.parents):
        for repository in ("ANYfileIO", "ANYgeometry", "ANYmaterial", "ANYmesh"):
            candidate = parent / repository / "src"
            if candidate.is_dir():
                paths.append(candidate)
    for path in reversed(paths):
        made = str(path)
        if made not in sys.path:
            sys.path.insert(0, made)


def _csr_hash(matrix: Any) -> str:
    payload = b"".join((
        str(tuple(int(value) for value in matrix.shape)).encode("ascii"), b"\0",
        matrix.indptr.dtype.str.encode("ascii"), b"\0", matrix.indptr.tobytes(order="C"), b"\0",
        matrix.indices.dtype.str.encode("ascii"), b"\0", matrix.indices.tobytes(order="C"), b"\0",
        matrix.data.dtype.str.encode("ascii"), b"\0", matrix.data.tobytes(order="C"),
    ))
    return sha256(payload)


def _csr_identical(left: Any, right: Any) -> bool:
    import numpy as np
    return bool(left.shape == right.shape and np.array_equal(left.indptr, right.indptr) and np.array_equal(left.indices, right.indices) and np.array_equal(left.data, right.data))


def _build_batch_model(count: int) -> Any:
    _inject_source_paths()
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEModel

    model = FEModel("v5m-batch-4096")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    for index in range(count):
        base = 3 * index + 1
        shift = 8.0 * index
        for node_id, coordinate in zip(
            (base, base + 1, base + 2),
            ((shift, 0.0, 0.0), (shift + 2.0, 0.0, 0.0), (shift + 0.3, 1.1, 0.0)),
        ):
            model.add_node(node_id, *coordinate)
        model.add_element(
            index + 1,
            create_shell_element(
                index + 1,
                (base, base + 1, base + 2),
                "steel",
                formulation="e4-pl-s3-v2c",
                thickness=0.08,
                reference_normal=(0.0, 0.0, 1.0),
            ),
        )
    return model


def _scalar_assembly(model: Any) -> Any:
    import numpy as np
    from scipy import sparse

    rows: list[Any] = []
    cols: list[Any] = []
    data: list[Any] = []
    for element in model.mesh.elements.values():
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        material = model.get_material(element.material_name)
        matrix = np.asarray(element.compute_stiffness_matrix(model.mesh, material), dtype=np.float64)
        rows.append(np.repeat(dofs, dofs.size))
        cols.append(np.tile(dofs, dofs.size))
        data.append(matrix.ravel())
    return sparse.coo_matrix(
        (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
        shape=(model.mesh.dof_manager.total_dofs, model.mesh.dof_manager.total_dofs),
    ).tocsr()


def _batch_worker(count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    _inject_source_paths()
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    started = time.perf_counter()
    model = _build_batch_model(count)
    built = time.perf_counter()
    scalar = _scalar_assembly(model)
    scalar_done = time.perf_counter()
    cold, cold_info = assemble_stiffness_matrix(model)
    cold_done = time.perf_counter()
    warm, warm_info = assemble_stiffness_matrix(model)
    warm_done = time.perf_counter()
    scalar_hash = _csr_hash(scalar)
    cold_hash = _csr_hash(cold)
    warm_hash = _csr_hash(warm)
    cold_diagnostics = cold_info["diagnostics"]["s3_v2c_exact_stiffness"]
    warm_diagnostics = warm_info["diagnostics"]["s3_v2c_exact_stiffness"]
    payload = {
        "cold_scalar_csr_byte_identical": _csr_identical(cold, scalar),
        "cold_warm_csr_byte_identical": _csr_identical(cold, warm),
        "csr_sha256": scalar_hash,
        "element_count": count,
        "hashes_identical": scalar_hash == cold_hash == warm_hash,
        "scalar_shell_element_count_warm": int(warm_info["diagnostics"]["scalar_shell_element_count"]),
        "vectorized_shell_element_count_warm": int(warm_info["diagnostics"]["vectorized_shell_element_count"]),
        "warm_global_plan_reused": bool(warm_diagnostics["plan_reused"]),
        "cold_element_plan_reused": bool(cold_diagnostics["plan_reused"]),
    }
    passed = payload == {
        "cold_scalar_csr_byte_identical": True,
        "cold_warm_csr_byte_identical": True,
        "csr_sha256": scalar_hash,
        "element_count": count,
        "hashes_identical": True,
        "scalar_shell_element_count_warm": 0,
        "vectorized_shell_element_count_warm": count,
        "warm_global_plan_reused": True,
        "cold_element_plan_reused": False,
    }
    diagnostics = {
        "build_seconds": built - started,
        "cold_seconds": cold_done - scalar_done,
        "scalar_seconds": scalar_done - built,
        "warm_seconds": warm_done - cold_done,
    }
    return {"passed": passed, "payload": payload}, diagnostics


def _serialization_worker() -> tuple[dict[str, Any], dict[str, Any]]:
    _inject_source_paths()
    import anysolver
    from anysolver.e4_pl_s3_v2c_element import StrictFlatLinearCapabilityError, StrictFlatLinearE4PLS3V2CShellElement
    from anysolver.elements import DEFAULT_Q4_FORMULATION, DEFAULT_S3_FORMULATION, create_shell_element, shell_element_from_dict

    orders = ((1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1))
    serialized: list[dict[str, Any]] = []
    roundtrip = True
    for index, order in enumerate(orders, start=1):
        element = create_shell_element(index, order, "steel", formulation="e4-pl-s3-v2c", thickness=0.08, reference_normal=(0.0, 0.0, 1.0))
        payload = element.to_dict()
        restored = shell_element_from_dict(payload)
        roundtrip = roundtrip and type(restored) is StrictFlatLinearE4PLS3V2CShellElement and restored.to_dict() == payload
        serialized.append(payload)
    candidate = create_shell_element(99, (1, 2, 3), "steel", formulation="e4-pl-s3-v2c", thickness=0.08, reference_normal=(0.0, 0.0, 1.0))
    identity_fields = (
        "formulation_id", "formulation_schema", "geometric_stiffness_policy_id", "implementation_id",
        "mass_policy_id", "quadrature_authority_id", "recovery_policy_id", "relaxation_authority_sha256",
        "selector", "serialization_policy_id", "type",
    )
    mutations_rejected = 0
    for field in identity_fields:
        changed = dict(candidate.to_dict())
        changed[field] = "MUTATED"
        try:
            shell_element_from_dict(changed)
        except ValueError:
            mutations_rejected += 1
    restart_calls = (
        lambda: candidate.__getstate__(),
        lambda: candidate.__setstate__({}),
        lambda: candidate.__reduce_ex__(5),
        lambda: copy.copy(candidate),
        lambda: copy.deepcopy(candidate),
        lambda: pickle.dumps(candidate, protocol=5),
    )
    restart_rejected = 0
    for operation in restart_calls:
        try:
            operation()
        except StrictFlatLinearCapabilityError as error:
            if "restart" in str(error):
                restart_rejected += 1
    payload = {
        "canonical_payload_sha256": sha256(canonical_bytes(serialized)),
        "default_q4_formulation": DEFAULT_Q4_FORMULATION,
        "default_s3_formulation": DEFAULT_S3_FORMULATION,
        "formulation_id": candidate.formulation_id,
        "mutation_count": len(identity_fields),
        "mutations_rejected": mutations_rejected,
        "public_export_matches": anysolver.STRICT_FLAT_S3_V2C_FORMULATION_ID == FORMULATION_ID,
        "restart_operation_count": len(restart_calls),
        "restart_operations_rejected": restart_rejected,
        "roundtrip_case_count": len(orders),
        "roundtrips_identical": roundtrip,
    }
    passed = bool(
        roundtrip
        and mutations_rejected == len(identity_fields)
        and restart_rejected == len(restart_calls)
        and payload["public_export_matches"]
        and DEFAULT_Q4_FORMULATION == "e4-pl"
        and DEFAULT_S3_FORMULATION == "legacy-s3"
    )
    return {"passed": passed, "payload": payload}, {}


def _run_checked(command: Sequence[str], *, cwd: Path, timeout: int = CHILD_TIMEOUT_SECONDS) -> tuple[bytes, bytes]:
    environment = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    process = subprocess.run(list(command), cwd=cwd, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    if process.returncode:
        raise V5MParityError(process.stderr.decode("utf-8", errors="replace") or f"command failed: {command[0]}")
    return process.stdout, process.stderr


def package_probe(target: Path, output: Path) -> None:
    resolved_target = target.resolve()
    sys.path[:] = [str(resolved_target), *[entry for entry in sys.path if entry and not str(Path(entry).resolve()).lower().startswith(str(ROOT.resolve()).lower())]]
    import anysolver
    from anysolver.e4_pl_s3_v2c_element import StrictFlatLinearE4PLS3V2CShellElement
    from anysolver.elements import DEFAULT_Q4_FORMULATION, DEFAULT_S3_FORMULATION, create_shell_element, shell_element_from_dict

    origin = Path(anysolver.__file__).resolve()
    candidate = create_shell_element(1, (1, 2, 3), "steel", formulation="e4-pl-s3-v2c", thickness=0.08, reference_normal=(0.0, 0.0, 1.0))
    serialized = candidate.to_dict()
    restored = shell_element_from_dict(serialized)
    result = {
        "candidate_class": type(candidate).__name__,
        "candidate_formulation_id": candidate.formulation_id,
        "default_q4_formulation": DEFAULT_Q4_FORMULATION,
        "default_s3_formulation": DEFAULT_S3_FORMULATION,
        "installed_origin_under_target": origin.is_relative_to(resolved_target),
        "public_export_matches": anysolver.STRICT_FLAT_S3_V2C_FORMULATION_ID == FORMULATION_ID,
        "roundtrip_identical": type(restored) is StrictFlatLinearE4PLS3V2CShellElement and restored.to_dict() == serialized,
        "source_root_absent_from_sys_path": all(
            not str(Path(entry).resolve()).lower().startswith(str(ROOT.resolve()).lower())
            or str(Path(entry).resolve()).lower().startswith(str(resolved_target).lower())
            for entry in sys.path
            if entry
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(canonical_bytes(result))


def _package_worker(anysolver_wheel: Path, anyfileio_wheel: Path, package_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package_root.mkdir(parents=True, exist_ok=False)
    target = package_root / "target"
    stdout, stderr = _run_checked(
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-compile", "--no-deps", "--target", str(target), str(anyfileio_wheel), str(anysolver_wheel)],
        cwd=package_root,
    )
    probe = package_root / "probe.json"
    probe_stdout, probe_stderr = _run_checked(
        [sys.executable, "-I", str(Path(__file__).resolve()), "--package-probe", "--target", str(target), "--output", str(probe)],
        cwd=package_root,
    )
    _probe_raw, value = load(probe)
    expected = {
        "candidate_class": "StrictFlatLinearE4PLS3V2CShellElement",
        "candidate_formulation_id": FORMULATION_ID,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "installed_origin_under_target": True,
        "public_export_matches": True,
        "roundtrip_identical": True,
        "source_root_absent_from_sys_path": True,
    }
    payload = {
        "anyfileio_wheel_bytes": anyfileio_wheel.stat().st_size,
        "anyfileio_wheel_sha256": sha256(anyfileio_wheel.read_bytes()),
        "anysolver_wheel_bytes": anysolver_wheel.stat().st_size,
        "anysolver_wheel_sha256": sha256(anysolver_wheel.read_bytes()),
        "probe": value,
    }
    diagnostics = {
        "install_stderr_sha256": sha256(stderr),
        "install_stdout_sha256": sha256(stdout),
        "probe_stderr_sha256": sha256(probe_stderr),
        "probe_stdout_sha256": sha256(probe_stdout),
    }
    return {"passed": value == expected, "payload": payload}, diagnostics


def produce(worker_id: str, *, anysolver_wheel: Path | None = None, anyfileio_wheel: Path | None = None, package_root: Path | None = None, batch_count: int = BATCH_ELEMENT_COUNT) -> tuple[dict[str, Any], dict[str, Any]]:
    if worker_id not in WORKER_IDS:
        raise V5MParityError(f"unknown V5M worker: {worker_id}")
    validate_protocol()
    started = time.perf_counter()
    if worker_id == "BATCH_4096":
        result, diagnostics = _batch_worker(batch_count)
    elif worker_id == "SERIALIZATION_RESTART":
        result, diagnostics = _serialization_worker()
    else:
        if anysolver_wheel is None or anyfileio_wheel is None or package_root is None:
            raise V5MParityError("package worker requires both frozen wheels and a fresh root")
        result, diagnostics = _package_worker(anysolver_wheel, anyfileio_wheel, package_root)
    proof = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "gate_status": PASS if result["passed"] else FAIL,
        "payload": result["payload"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": PROOF_SCHEMA,
        "worker_id": worker_id,
    }
    proof["scientific_payload_sha256"] = sha256(canonical_bytes(proof))
    diagnostics = {**diagnostics, "elapsed_seconds": time.perf_counter() - started, "worker_id": worker_id}
    return proof, diagnostics


def _load_guard() -> Any:
    spec = importlib.util.spec_from_file_location("_v5m_process_guard", PROCESS_GUARD)
    if spec is None or spec.loader is None:
        raise V5MParityError("cannot load bounded process guard")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _launch(label: str, command: Sequence[str], directory: Path, timeout: int, cwd: Path = ROOT) -> tuple[str, int, Path]:
    guard = _load_guard()
    directory.mkdir(parents=True, exist_ok=False)
    job = guard._ProcessJob(MEMORY_LIMIT_GIB * 1024**3)
    with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
        try:
            process = job.launch(list(command), cwd=cwd, env=_environment(), stdout=stdout, stderr=stderr)
            try:
                code = process.wait(timeout=timeout)
                status = "COMPLETE" if code == 0 else "FAILED"
            except subprocess.TimeoutExpired:
                status, code = "TIMEOUT", -9
                if not job.terminate():
                    status = "TERMINATION_FAILED"
        finally:
            job.close()
    return status, int(code), directory


def validate_authorization(path: Path) -> dict[str, Any]:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v5m-execution-authorization-v1":
        raise V5MParityError("unexpected V5M execution authorization schema")
    if _git("rev-parse", "HEAD^") != value.get("implementation_commit") or _git("show", "-s", "--format=%s", "HEAD") != value.get("expected_authorization_subject"):
        raise V5MParityError("V5M authorization topology changed")
    if _git("status", "--porcelain", "--untracked-files=all"):
        raise V5MParityError("V5M worktree is dirty")
    for row in value.get("frozen_inputs", []):
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise V5MParityError(f"authorization input mismatch: {row['path']}")
    contract = validate_protocol()
    external = contract["external_package_authority"]
    external_root = Path(external["repository"])
    safe = f"safe.directory={external_root.as_posix()}"
    if _git("-c", safe, "rev-parse", "HEAD", cwd=external_root) != external["commit"] or _git("-c", safe, "rev-parse", "HEAD^{tree}", cwd=external_root) != external["tree"]:
        raise V5MParityError("ANYfileIO package authority changed")
    if _git("-c", safe, "status", "--porcelain", "--untracked-files=all", cwd=external_root):
        raise V5MParityError("ANYfileIO package authority is dirty")
    return value


def _extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as stream:
        stream.extractall(destination)


def _build_frozen_wheels(root: Path, deadline: float) -> tuple[Path, Path, dict[str, Any]]:
    contract = validate_protocol()
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=False)
    anysolver_archive = artifacts / "anysolver.zip"
    anyfileio_archive = artifacts / "anyfileio.zip"
    external = contract["external_package_authority"]
    external_root = Path(external["repository"])
    jobs = (
        ("archive-anysolver", ["git", "archive", "--format=zip", f"--output={anysolver_archive}", "HEAD"], ROOT),
        ("archive-anyfileio", ["git", "-c", f"safe.directory={external_root.as_posix()}", "archive", "--format=zip", f"--output={anyfileio_archive}", external["commit"]], external_root),
    )
    for label, command, cwd in jobs:
        result = _launch(label, command, artifacts / "logs" / label, min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic()))), cwd)
        if result[0] != "COMPLETE":
            raise V5MParityError(f"{label} failed")
    anysolver_source = artifacts / "source-anysolver"
    anyfileio_source = artifacts / "source-anyfileio"
    _extract_archive(anysolver_archive, anysolver_source)
    _extract_archive(anyfileio_archive, anyfileio_source)
    wheelhouse = artifacts / "wheelhouse"
    wheelhouse.mkdir()
    for label, source in (("build-anysolver", anysolver_source), ("build-anyfileio", anyfileio_source)):
        result = _launch(label, [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(wheelhouse), str(source)], artifacts / "logs" / label, min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic()))))
        if result[0] != "COMPLETE":
            raise V5MParityError(f"{label} failed")
    anysolver_wheels = tuple(wheelhouse.glob("anysolver-*.whl"))
    anyfileio_wheels = tuple(wheelhouse.glob("anyfileio-*.whl"))
    if len(anysolver_wheels) != 1 or len(anyfileio_wheels) != 1:
        raise V5MParityError("frozen build did not produce exactly one wheel per distribution")
    made = {
        "anyfileio_wheel_bytes": anyfileio_wheels[0].stat().st_size,
        "anyfileio_wheel_sha256": sha256(anyfileio_wheels[0].read_bytes()),
        "anysolver_wheel_bytes": anysolver_wheels[0].stat().st_size,
        "anysolver_wheel_sha256": sha256(anysolver_wheels[0].read_bytes()),
    }
    return anysolver_wheels[0], anyfileio_wheels[0], made


def _cycle(root: Path, deadline: float, anysolver_wheel: Path, anyfileio_wheel: Path, wheel_identity: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=False)
    producer_results: dict[str, tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=WORKER_CONCURRENCY) as pool:
        futures = {}
        for worker_id in WORKER_IDS:
            directory = root / "workers" / worker_id.lower()
            command = [sys.executable, str(Path(__file__).resolve()), "--worker", worker_id, "--output", str(directory / "proof.json"), "--diagnostic-output", str(directory / "diagnostic.json")]
            if worker_id == "PACKAGE_WHEEL":
                command.extend(["--anysolver-wheel", str(anysolver_wheel), "--anyfileio-wheel", str(anyfileio_wheel), "--package-root", str(directory / "installed")])
            timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
            futures[pool.submit(_launch, worker_id, command, directory, timeout)] = worker_id
        for future in as_completed(futures):
            producer_results[futures[future]] = future.result()
    if any(result[0] != "COMPLETE" for result in producer_results.values()):
        raise V5MParityError("V5M producer process failure")
    checker_results: dict[tuple[str, int], tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=CHECKER_CONCURRENCY) as pool:
        futures = {}
        for worker_id in WORKER_IDS:
            proof = producer_results[worker_id][2] / "proof.json"
            for replica in (1, 2):
                directory = root / "checkers" / worker_id.lower() / str(replica)
                command = [sys.executable, str(CHECKER), "--verify-proof", "--proof", str(proof), "--output", str(directory / "check.json")]
                timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
                futures[pool.submit(_launch, f"{worker_id}-{replica}", command, directory, timeout)] = (worker_id, replica)
        for future in as_completed(futures):
            checker_results[futures[future]] = future.result()
    if any(result[0] != "COMPLETE" for result in checker_results.values()):
        raise V5MParityError("V5M checker process failure")
    proofs = {worker_id: load(producer_results[worker_id][2] / "proof.json")[1] for worker_id in WORKER_IDS}
    for worker_id in WORKER_IDS:
        first = (checker_results[(worker_id, 1)][2] / "check.json").read_bytes()
        second = (checker_results[(worker_id, 2)][2] / "check.json").read_bytes()
        if first != second:
            raise V5MParityError(f"checker replicas disagree: {worker_id}")
    gates = {worker_id: proofs[worker_id]["gate_status"] for worker_id in WORKER_IDS}
    passed = all(value == PASS for value in gates.values())
    common = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "coverage": {"batch_element_count": BATCH_ELEMENT_COUNT, "checker_replicas_per_worker": 2, "worker_ids": list(WORKER_IDS)},
        "gate_status": gates,
        "next_gate": "V5N_FULL_ACTIVATION_QUALIFICATION_PROTOCOL" if passed else None,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v5m-cycle-common-v1",
        "terminal": GO if passed else NO_GO,
        "wheel_identity": dict(wheel_identity),
    }
    raw = canonical_bytes(common)
    with (root / "common.json").open("xb") as stream:
        stream.write(raw)
    return raw, common


def run(authorization: Path, output: Path) -> dict[str, Any]:
    validate_authorization(authorization)
    if output.exists():
        raise V5MParityError("exclusive V5M output root exists")
    output.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    cycles: list[dict[str, Any]] = []
    raws: list[bytes] = []
    wheel_identity: dict[str, Any] = {}
    try:
        anysolver_wheel, anyfileio_wheel, wheel_identity = _build_frozen_wheels(output, deadline)
        for cycle in (1, 2):
            raw, value = _cycle(output / f"cycle-{cycle}", deadline, anysolver_wheel, anyfileio_wheel, wheel_identity)
            raws.append(raw)
            cycles.append(value)
        identical = raws[0] == raws[1]
        terminal = cycles[0]["terminal"] if identical and cycles[0]["terminal"] == cycles[1]["terminal"] else BLOCKED
    except Exception as error:
        identical = False
        terminal = BLOCKED
        (output / "failure.txt").write_text(f"{type(error).__name__}: {error}\n", encoding="utf-8")
    aggregate = {
        "activation_authorized": False,
        "authorization_sha256": sha256(authorization.read_bytes()),
        "cycles_byte_identical": identical,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v5m-aggregate-v1",
        "terminal": terminal,
        "wheel_identity": wheel_identity,
    }
    with (output / "aggregate.json").open("xb") as stream:
        stream.write(canonical_bytes(aggregate))
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", choices=WORKER_IDS)
    mode.add_argument("--run-v5m", action="store_true")
    mode.add_argument("--package-probe", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-output", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--anysolver-wheel", type=Path)
    parser.add_argument("--anyfileio-wheel", type=Path)
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--target", type=Path)
    args = parser.parse_args(argv)
    if args.package_probe:
        if args.target is None:
            raise V5MParityError("package probe target is required")
        package_probe(args.target, args.output)
    elif args.worker:
        if args.diagnostic_output is None:
            raise V5MParityError("worker diagnostic output is required")
        proof, diagnostic = produce(args.worker, anysolver_wheel=args.anysolver_wheel, anyfileio_wheel=args.anyfileio_wheel, package_root=args.package_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(proof))
        with args.diagnostic_output.open("xb") as stream:
            stream.write(canonical_bytes(diagnostic))
    else:
        if args.authorization is None:
            raise V5MParityError("V5M execution authorization is required")
        print(canonical_bytes(run(args.authorization, args.output)).decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
