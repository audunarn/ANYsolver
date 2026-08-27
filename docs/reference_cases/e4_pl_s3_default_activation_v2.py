"""Bounded protocol-v2 qualification for qualified-S3 default activation.

Authority is validated with the standard library before numerical packages or
mechanics are imported.  Bounded worker waves never exceed three concurrent
processes.  The scientific record contains only deterministic facts; timings
and process measurements remain in separately hash-bound diagnostics.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
DEFAULT_INPUT = REFERENCE_CASES / "e4_pl_s3_default_activation_v2_input.json"
INPUT_SCHEMA = "anysolver.e4-pl-s3-default-activation-input-v2"
CONTRACT_SCHEMA = "anysolver.e4-pl-s3-default-activation-contract-v2"
WORKER_SCHEMA = "anysolver.e4-pl-s3-default-activation-worker-v2"
SCIENTIFIC_SCHEMA = "anysolver.e4-pl-s3-default-activation-scientific-v2"
TWO_CYCLE_SCHEMA = "anysolver.e4-pl-s3-default-activation-two-cycle-v2"
STRUCTURAL_WORKERS = (
    "STRUCTURAL_SLASH",
    "STRUCTURAL_BACKSLASH",
    "STRUCTURAL_ALTERNATING",
)
FOLLOWUP_WORKERS = ("EIGEN_PERFORMANCE", "SPECIAL_ECOSYSTEM")
BATCH_WORKERS = ("BATCH_0", "BATCH_1", "BATCH_2")
WORKERS = STRUCTURAL_WORKERS + FOLLOWUP_WORKERS + BATCH_WORKERS
EXECUTION_WAVES = (STRUCTURAL_WORKERS, FOLLOWUP_WORKERS, BATCH_WORKERS)
TERMINALS = (
    "BLOCKED_E4_PL_S3_DEFAULT_ACTIVATION_EVIDENCE_OR_REVIEW",
    "NO_GO_E4_PL_S3_DEFAULT_ACTIVATION_QUALIFICATION",
    "PROVISIONAL_GO_E4_PL_S3_DEFAULT_ACTIVATION",
)
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}


class QualificationError(ValueError):
    """An authority, process, or evidence record is invalid."""


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def strict_json(raw: bytes, *, label: str) -> object:
    def object_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        made: dict[str, object] = {}
        for key, value in pairs:
            if key in made:
                raise QualificationError(f"{label} contains duplicate key {key!r}")
            made[key] = value
        return made

    def constant(value: str) -> object:
        raise QualificationError(f"{label} contains nonfinite value {value!r}")

    try:
        return json.loads(raw, object_pairs_hook=object_hook, parse_constant=constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualificationError(f"{label} is not strict UTF-8 JSON") from exc


def _read_json(path: Path, *, pretty: bool, label: str) -> tuple[bytes, dict[str, Any]]:
    raw = Path(path).read_bytes()
    value = strict_json(raw, label=label)
    if not isinstance(value, dict):
        raise QualificationError(f"{label} must be an object")
    expected = pretty_bytes(value) if pretty else canonical_bytes(value)
    if raw != expected:
        raise QualificationError(f"{label} is not canonical JSON")
    return raw, value


def _exact_keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    actual = set(value)
    wanted = set(expected)
    if actual != wanted:
        raise QualificationError(
            f"{label} keys differ: missing={sorted(wanted-actual)}, extra={sorted(actual-wanted)}"
        )


def _digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise QualificationError(f"{label} must be an uppercase SHA-256")
    return value


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise QualificationError(f"{label} must be a positive integer")
    return int(value)


def _write_exclusive(path: Path, value: object, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = pretty_bytes(value) if pretty else canonical_bytes(value)
    with path.open("xb") as stream:
        stream.write(raw)


def _git(root: Path, *arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise QualificationError(completed.stderr.decode("utf-8", errors="replace").strip())
    return completed.stdout if binary else completed.stdout.decode("utf-8").strip()


def _regular_file(path: Path, *, label: str) -> bytes:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise QualificationError(f"{label} must be a regular file")
    status = resolved.stat()
    if status.st_size <= 0:
        raise QualificationError(f"{label} must be nonempty")
    attributes = int(getattr(status, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat_constants(), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    if attributes & reparse_flag:
        raise QualificationError(f"{label} must not be a reparse point")
    return resolved.read_bytes()


def stat_constants() -> Any:
    import stat

    return stat


@dataclass(frozen=True)
class Authority:
    input_path: Path
    input_raw: bytes
    input: dict[str, Any]
    contract_path: Path
    contract_raw: bytes
    contract: dict[str, Any]
    manifest_path: Path
    manifest_raw: bytes
    manifest: dict[str, Any]
    target: Path


def load_authority(input_path: Path = DEFAULT_INPUT) -> Authority:
    input_raw, payload = _read_json(Path(input_path), pretty=True, label="v2 input")
    _exact_keys(
        payload,
        ("candidates", "contract", "evidence", "execution", "programs", "schema"),
        "input",
    )
    if payload["schema"] != INPUT_SCHEMA:
        raise QualificationError("input schema mismatch")

    contract_row = payload["contract"]
    _exact_keys(contract_row, ("bytes", "path", "sha256"), "contract authority")
    contract_path = (ROOT / str(contract_row["path"])).resolve(strict=True)
    contract_raw, contract = _read_json(contract_path, pretty=True, label="v2 contract")
    if (
        len(contract_raw) != _positive_integer(contract_row["bytes"], "contract bytes")
        or sha256(contract_raw) != _digest(contract_row["sha256"], "contract hash")
        or contract.get("schema") != CONTRACT_SCHEMA
    ):
        raise QualificationError("contract authority mismatch")

    programs = payload["programs"]
    expected_programs = {"batch_benchmark", "runner", "test"}
    if not isinstance(programs, dict) or set(programs) != expected_programs:
        raise QualificationError("program authority set is incomplete")
    for name in sorted(programs):
        row = programs[name]
        _exact_keys(row, ("bytes", "path", "sha256"), f"programs.{name}")
        path = (ROOT / str(row["path"])).resolve(strict=True)
        raw = _regular_file(path, label=f"programs.{name}")
        if (
            len(raw) != _positive_integer(row["bytes"], f"programs.{name}.bytes")
            or sha256(raw) != _digest(row["sha256"], f"programs.{name}.sha256")
        ):
            raise QualificationError(f"programs.{name} authority mismatch")

    evidence = payload["evidence"]
    _exact_keys(
        evidence,
        ("connectivity_manifest", "opt_in_burnin", "prior_eigen", "prior_structural"),
        "evidence",
    )
    bound: dict[str, tuple[Path, bytes]] = {}
    for name, row in evidence.items():
        _exact_keys(row, ("bytes", "path", "sha256"), f"evidence.{name}")
        path = Path(str(row["path"]))
        path = path if path.is_absolute() else ROOT / path
        raw = _regular_file(path, label=f"evidence.{name}")
        if (
            len(raw) != _positive_integer(row["bytes"], f"evidence.{name}.bytes")
            or sha256(raw) != _digest(row["sha256"], f"evidence.{name}.sha256")
        ):
            raise QualificationError(f"evidence.{name} authority mismatch")
        bound[name] = (path.resolve(), raw)
    manifest_path, manifest_raw = bound["connectivity_manifest"]
    manifest_value = strict_json(manifest_raw, label="connectivity manifest")
    if not isinstance(manifest_value, dict) or len(manifest_value.get("records", ())) != 252:
        raise QualificationError("connectivity manifest must contain 252 gated records")

    candidates = payload["candidates"]
    expected_candidates = {
        "ANYfileIO",
        "ANYfem",
        "ANYintelligent",
        "ANYmesh",
        "ANYsolver",
        "ANYstructure",
    }
    if set(candidates) != expected_candidates:
        raise QualificationError("candidate repository graph is incomplete")
    for name in sorted(candidates):
        row = candidates[name]
        _exact_keys(row, ("commit", "root", "subject", "tree", "wheel"), f"candidate {name}")
        root = Path(str(row["root"])).resolve(strict=True)
        commit = str(row["commit"])
        observed = str(_git(root, "show", "-s", "--format=%H%n%T%n%s", commit)).splitlines()
        if observed != [commit, str(row["tree"]), str(row["subject"])]:
            raise QualificationError(f"candidate {name} git identity mismatch")
        wheel = row["wheel"]
        if wheel is None:
            continue
        _exact_keys(wheel, ("bytes", "filename", "path", "sha256"), f"candidate {name} wheel")
        wheel_path = Path(str(wheel["path"])).resolve(strict=True)
        raw = _regular_file(wheel_path, label=f"candidate {name} wheel")
        if (
            wheel_path.name != wheel["filename"]
            or len(raw) != _positive_integer(wheel["bytes"], f"candidate {name} wheel bytes")
            or sha256(raw) != _digest(wheel["sha256"], f"candidate {name} wheel hash")
        ):
            raise QualificationError(f"candidate {name} wheel mismatch")

    solver = candidates["ANYsolver"]
    changed = str(
        _git(
            Path(str(solver["root"])),
            "diff",
            "--name-only",
            str(contract["candidate_policy"]["anysolver_base_commit"]),
            str(solver["commit"]),
        )
    ).splitlines()
    if changed != contract["candidate_policy"]["anysolver_changed_paths"]:
        raise QualificationError("ANYsolver candidate path set differs from the contract")
    q4_raw = _git(
        Path(str(solver["root"])),
        "show",
        f"{solver['commit']}:src/anysolver/e4_pl_element.py",
        binary=True,
    )
    if sha256(q4_raw) != contract["candidate_policy"]["q4_mechanics_sha256"]:
        raise QualificationError("qualified Q4 mechanics changed")

    execution = payload["execution"]
    _exact_keys(
        execution,
        (
            "canonical_cycles",
            "memory_limit_gib_per_process",
            "numerical_threads_per_process",
            "target",
            "timeout_seconds_per_process",
            "total_command_limit_seconds",
            "workers",
        ),
        "execution",
    )
    if execution != {
        "canonical_cycles": 2,
        "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1,
        "target": execution["target"],
        "timeout_seconds_per_process": 540,
        "total_command_limit_seconds": 1200,
        "workers": 3,
    }:
        raise QualificationError("execution policy differs from protocol v2")
    target = Path(str(execution["target"])).resolve(strict=True)
    if not target.is_dir():
        raise QualificationError("isolated wheel target is absent")
    return Authority(
        input_path=Path(input_path).resolve(),
        input_raw=input_raw,
        input=payload,
        contract_path=contract_path,
        contract_raw=contract_raw,
        contract=contract,
        manifest_path=manifest_path,
        manifest_raw=manifest_raw,
        manifest=manifest_value,
        target=target,
    )


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise QualificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class MechanicsBundle:
    structural_common: Any
    structural_producer: Any
    eigen: Any
    smoke_runner: Any
    smoke: Any
    manifest_generator: Any


def _activate(authority: Authority) -> MechanicsBundle:
    imported = __import__("anysolver")
    if str(getattr(imported, "__version__", "")) != "0.4.0":
        raise QualificationError("isolated target did not import ANYsolver 0.4.0")
    if not Path(str(imported.__file__)).resolve().is_relative_to(authority.target):
        raise QualificationError("ANYsolver did not originate in the isolated target")
    if str(REFERENCE_CASES) not in sys.path:
        sys.path.insert(0, str(REFERENCE_CASES))
    common = _load_module(
        "e4_pl_s3_mixed_structural_common",
        REFERENCE_CASES / "e4_pl_s3_mixed_structural_common.py",
    )
    producer = _load_module(
        "_s3_activation_v2_structural_producer",
        REFERENCE_CASES / "e4_pl_s3_mixed_structural_producer.py",
    )
    eigen = _load_module(
        "_s3_activation_v2_eigen",
        REFERENCE_CASES / "e4_pl_s3_mixed_eigen_performance.py",
    )
    smoke_runner = _load_module(
        "_s3_activation_v2_smoke",
        REFERENCE_CASES / "e4_pl_s3_mixed_mesh_qualification_runner.py",
    )
    smoke = smoke_runner.load_authorities(
        REFERENCE_CASES / "e4_pl_s3_mixed_mesh_smoke_input.json"
    )
    payload = deepcopy(smoke.input_payload)
    payload["factories"]["default_s3_expected"] = "e4-pl-s3"
    smoke = replace(smoke, input_payload=payload)
    manifest_generator = _load_module(
        "_s3_activation_v2_manifest",
        REFERENCE_CASES / "e4_pl_s3_mixed_mesh_manifest.py",
    )
    if canonical_bytes(manifest_generator.build_manifest()) != authority.manifest_raw:
        raise QualificationError("connectivity manifest did not regenerate exactly")
    return MechanicsBundle(common, producer, eigen, smoke_runner, smoke, manifest_generator)


def _hard_navier(model: Any, level: int | None = None) -> list[int]:
    from anysolver.boundary import BoundaryCondition

    all_edge: list[int] = []
    x_edge: list[int] = []
    y_edge: list[int] = []
    for node_id, node in sorted(model.mesh.nodes.items()):
        x, y, _z = (float(value) for value in node.coords())
        on_x = min(abs(x), abs(x - 1.0)) <= 1.0e-12
        on_y = min(abs(y), abs(y - 1.0)) <= 1.0e-12
        if on_x or on_y:
            all_edge.append(int(node_id))
        if on_x:
            x_edge.append(int(node_id))
        if on_y:
            y_edge.append(int(node_id))
    model.boundary_conditions = [
        BoundaryCondition("hard-navier-translations", all_edge, {"ux": 0.0, "uy": 0.0, "uz": 0.0}),
        BoundaryCondition("hard-navier-x-edge-tangent-rotation", x_edge, {"rx": 0.0}),
        BoundaryCondition("hard-navier-y-edge-tangent-rotation", y_edge, {"ry": 0.0}),
    ]
    model.constraint_equations = []
    return all_edge


def _lower_one_sided_95(values: Sequence[float], levels: Sequence[int]) -> float | None:
    if len(values) != 4 or len(levels) != 4 or any(value <= 0.0 for value in values):
        return None
    x = [-math.log(float(value)) for value in levels]
    y = [math.log(float(value)) for value in values]
    mx = statistics.mean(x)
    my = statistics.mean(y)
    sxx = sum((value - mx) ** 2 for value in x)
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    residual = sum((b - (my + slope * (a - mx))) ** 2 for a, b in zip(x, y))
    standard_error = math.sqrt(max(residual, 0.0) / 2.0 / sxx)
    return float(slope - 2.919985580355516 * standard_error)


def _structural_sequences(diagonal: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"diagonal": diagonal, "fraction_percent": 0, "mask": "none"}
    ]
    for fraction in (1, 5, 10, 25):
        for mask in (
            "dispersed",
            "chain",
            "compact_cluster",
            "boundary_band",
            "hole_band",
        ):
            rows.append(
                {
                    "diagonal": diagonal,
                    "fraction_percent": fraction,
                    "mask": mask,
                }
            )
    if len(rows) != 21:
        raise QualificationError("structural diagonal shard is not exactly 21 sequences")
    return rows


def _structural_authority(
    authority: Authority,
    bundle: MechanicsBundle,
    diagonal: str,
) -> Any:
    coverage = deepcopy(authority.contract["coverage"]["structural"])
    coverage["convergence_sequences"] = _structural_sequences(diagonal)
    synthetic = SimpleNamespace(
        contract=authority.contract,
        input={"coverage": coverage},
        manifest=authority.manifest,
        manifest_raw=authority.manifest_raw,
        manifest_generator=bundle.manifest_generator,
        smoke_runner=bundle.smoke_runner,
        smoke_input_path=REFERENCE_CASES / "e4_pl_s3_mixed_mesh_smoke_input.json",
        program_raw={"v2": Path(__file__).read_bytes()},
        program_paths={"v2": Path(__file__)},
    )
    bundle.structural_producer._smoke_authorities = lambda _value: bundle.smoke
    bundle.structural_producer._plate_boundaries = _hard_navier
    bundle.structural_producer._plate_case = (
        lambda made, record, *, recover_interface: _plate_case_v2(
            bundle,
            made,
            record,
            recover_interface=recover_interface,
        )
    )
    bundle.structural_producer.activate_numerics(synthetic)
    return synthetic


def _reference_nodal_field(
    model: Any,
    modes: Sequence[tuple[int, int, float, float, float, float, float, float]],
    *,
    length: float,
    width: float,
) -> Any:
    """Project the independently authored Mindlin series at mesh nodes.

    The reference uses ``w``, ``theta_x`` and ``theta_y`` from the frozen
    modal field.  Membrane and drilling coordinates are exactly zero.  This
    creates a deterministic reference vector in the candidate discrete space
    without importing or inspecting either element implementation.
    """

    import numpy as np

    values = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    for node in model.mesh.nodes.values():
        x, y, _z = (float(value) for value in node.coords())
        transverse = 0.0
        rotation_x = 0.0
        rotation_y = 0.0
        for m, n, _a, _b, _qmn, w, theta_x, theta_y in modes:
            sin_x = math.sin(m * math.pi * x / length)
            cos_x = math.cos(m * math.pi * x / length)
            sin_y = math.sin(n * math.pi * y / width)
            cos_y = math.cos(n * math.pi * y / width)
            transverse += w * sin_x * sin_y
            rotation_x += theta_x * cos_x * sin_y
            rotation_y += theta_y * sin_x * cos_y
        values[int(node.dofs[2])] = transverse
        # Shell kinematics are ``gamma_x=w,x+ry`` and
        # ``gamma_y=w,y-rx``.  The independent series names its director
        # components theta_x/theta_y, hence this fixed physical-rotation map.
        values[int(node.dofs[3])] = -rotation_y
        values[int(node.dofs[4])] = rotation_x
    return values


def _solve_hard_navier_plate_v2(
    model: Any,
    load: Any,
) -> tuple[Any, dict[str, Any], Any]:
    """Solve the frozen flat-plate system through its exact flexural block.

    The protocol-v2 convergence fixture is a flat, symmetric-section plate
    with zero membrane/drill loading.  Its ``(w, rx, ry)`` block is exactly
    uncoupled from ``(u, v, rz)``.  Prove those conditions on the assembled
    production operator before reducing; an altered fixture or formulation
    therefore fails closed instead of silently taking this bounded route.
    """

    import numpy as np
    from scipy import sparse
    from anysolver.assembly import _solve_reduced_system
    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver.constraint_audit import constraint_residual_summary
    from anysolver.fe_core import FEModel
    from anysolver.matrix_assembly import assemble_system

    if type(model) is not FEModel or type(load) is not LoadCase:
        raise QualificationError("bounded plate solve requires exact model/load types")
    expected_supports = (
        (
            "hard-navier-translations",
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        ),
        ("hard-navier-x-edge-tangent-rotation", {"rx": 0.0}),
        ("hard-navier-y-edge-tangent-rotation", {"ry": 0.0}),
    )
    supports = tuple(model.boundary_conditions)
    if (
        len(supports) != len(expected_supports)
        or type(model.constraint_equations) is not list
        or model.constraint_equations
    ):
        raise QualificationError("bounded plate support protocol changed")
    for support, (name, constraints) in zip(supports, expected_supports):
        if (
            type(support) is not BoundaryCondition
            or support.name != name
            or type(support.node_ids) is not list
            or type(support.dof_constraints) is not dict
            or support.dof_constraints != constraints
            or any(type(node_id) is not int for node_id in support.node_ids)
        ):
            raise QualificationError("bounded plate support authority changed")

    model.apply_boundary_conditions()
    stiffness, force, assembly_info = assemble_system(model, load)
    if (
        not sparse.isspmatrix_csr(stiffness)
        or stiffness.shape[0] != stiffness.shape[1]
        or force.shape != (stiffness.shape[0],)
        or not np.all(np.isfinite(force))
        or not np.all(np.isfinite(stiffness.data))
    ):
        raise QualificationError("bounded plate assembly is malformed")

    active_all = np.asarray(
        [
            dof
            for _node_id, node in sorted(model.mesh.nodes.items())
            for dof in (node.dofs[2], node.dofs[3], node.dofs[4])
        ],
        dtype=np.intp,
    )
    free_all = np.asarray(model.mesh.dof_manager.get_free_dofs(), dtype=np.intp)
    active_mask = np.zeros(stiffness.shape[0], dtype=bool)
    active_mask[active_all] = True
    active = free_all[active_mask[free_all]]
    inactive = free_all[~active_mask[free_all]]
    if active.size == 0 or active.size + inactive.size != free_all.size:
        raise QualificationError("bounded plate coordinate partition is incomplete")
    if inactive.size and np.any(force[inactive] != 0.0):
        raise QualificationError("bounded plate inactive coordinates carry load")

    # Sparse products may retain explicitly stored zeros, so remove them
    # before requiring exact algebraic decoupling in both directions.
    inactive_active = stiffness[inactive, :][:, active].tocsr()
    active_inactive = stiffness[active, :][:, inactive].tocsr()
    inactive_active.eliminate_zeros()
    active_inactive.eliminate_zeros()
    if inactive_active.nnz or active_inactive.nnz:
        raise QualificationError(
            "bounded plate membrane/drill and flexural blocks are coupled"
        )

    reduced = stiffness[active, :][:, active].tocsr()
    solution, convergence = _solve_reduced_system(
        reduced,
        np.asarray(force[active], dtype=float),
        "direct",
    )
    displacement = np.zeros(stiffness.shape[0], dtype=float)
    displacement[active] = solution
    if convergence.get("status") == "converged":
        residual = np.asarray(
            stiffness[free_all, :] @ displacement - force[free_all],
            dtype=float,
        ).reshape(-1)
        denominator = max(
            float(np.max(np.abs(force[free_all]), initial=0.0)),
            np.finfo(float).tiny,
        )
        relative_residual = float(
            np.max(np.abs(residual), initial=0.0) / denominator
        )
        if not math.isfinite(relative_residual) or relative_residual > 1.0e-8:
            raise QualificationError(
                "bounded plate full-system residual exceeds its frozen limit"
            )
    constraint_report = constraint_residual_summary(model, displacement)
    if constraint_report.get("status") != "passed":
        raise QualificationError("bounded plate support postcheck failed")
    return (
        displacement,
        {
            "assembly": assembly_info,
            "bounded_exact_block_reduction": {
                "active_coordinates": int(active.size),
                "inactive_coordinates": int(inactive.size),
            },
            "constraint_postcheck": constraint_report,
            "convergence_info": convergence,
        },
        stiffness,
    )


def _run_finalized_plate_observation(
    model: Any,
    observation_lease: Any,
    operation: Any,
) -> Any:
    """Run one admitted observation and always close its exact lease."""

    try:
        result = operation()
    except BaseException as operation_error:
        try:
            observation_lease(
                model,
                context="activation-v2 plate observation exceptional output",
                final=True,
            )
        except BaseException as lease_error:
            raise lease_error from operation_error
        raise
    observation_lease(
        model,
        context="activation-v2 plate observation output",
        final=True,
    )
    return result


def _observe_plate_case_v2(
    *,
    built: Any,
    displacement: Any,
    reference_vector: Any,
    stiffness: Any,
    producer: Any,
    authorities: Any,
    level: int,
    record: Mapping[str, Any],
    recover_interface: bool,
    smoke: Any,
    thickness: float,
    pressure: float,
    length: float,
    width: float,
    material_spec: Mapping[str, Any],
    moment_modes: Any,
    recover_fields: Any,
    assemble_stiffness: Any,
    np_module: Any,
) -> tuple[dict[str, float], float, float, dict[tuple[int, int], list[float]]]:
    """Observe component/recovery facts inside one caller-owned lease."""

    np = np_module
    # Preserve the original material lookup as an admitted observation even
    # though the warm immutable component maps now carry the needed operators.
    built.model.get_material(str(material_spec["name"]))
    error_vector = displacement - reference_vector
    energies = {
        "Q4_PL": 0.0,
        "Q4_RESIDUAL_HOURGLASS": 0.0,
        "S3_PL": 0.0,
        "TOTAL": 0.5 * float(displacement @ stiffness @ displacement),
    }
    error_energy = max(float(error_vector @ stiffness @ error_vector), 0.0)
    reference_energy = max(
        float(reference_vector @ stiffness @ reference_vector), 0.0
    )
    cell_errors: dict[tuple[int, int], list[float]] = {}
    split, band = producer._interface_cells(
        authorities.manifest_generator,
        level=level,
        mask=str(record["mask"]),
        split_count=int(record["split_base_cell_count"]),
    )
    if recover_interface and not split:
        band = {(i, j) for j in range(level) for i in range(level)}
    element_id = 0
    recovery_cells: dict[int, tuple[int, int]] = {}
    recovery_centroids: dict[int, tuple[float, float]] = {}
    for j in range(level):
        for i in range(level):
            connectivities = smoke._cell_connectivity(
                i,
                j,
                level,
                split=(i, j) in split,
                diagonal=str(record["diagonal"]),
            )
            for kind, _nodes in connectivities:
                element_id += 1
                element = built.model.mesh.elements[element_id]
                namespace = object.__getattribute__(element, "__dict__")
                node_ids = dict.get(namespace, "node_ids")
                if (
                    type(namespace) is not dict
                    or type(node_ids) is not tuple
                    or len(node_ids) not in {3, 4}
                ):
                    raise QualificationError(
                        f"plate element {element_id} has incompatible owned routing"
                    )
                mapping = np.asarray(
                    [
                        dof
                        for node_id in node_ids
                        for dof in built.model.mesh.nodes[int(node_id)].dofs
                    ],
                    dtype=np.intp,
                )
                local = displacement[mapping]
                components = dict.get(namespace, "_qualified_components")
                if components is None:
                    raise QualificationError(
                        f"plate element {element_id} lacks its warm component cache"
                    )
                if kind == "S3":
                    energies["S3_PL"] += 0.5 * float(
                        local @ components["pl"] @ local
                    )
                else:
                    energies["Q4_PL"] += 0.5 * float(
                        local @ components["pl"] @ local
                    )
                    energies["Q4_RESIDUAL_HOURGLASS"] += 0.5 * float(
                        local @ components["hourglass"] @ local
                    )
                if recover_interface and (i, j) in band:
                    coordinates = np.asarray(
                        [
                            built.model.mesh.nodes[int(node_id)].coords()
                            for node_id in node_ids
                        ],
                        dtype=float,
                    )
                    centroid = np.mean(coordinates, axis=0)
                    recovery_cells[element_id] = (i, j)
                    recovery_centroids[element_id] = (
                        float(centroid[0]),
                        float(centroid[1]),
                    )

    if recovery_cells:
        recovered = recover_fields(
            built.model,
            displacement,
            tuple(recovery_cells),
            return_global=True,
        )
        if set(recovered) != set(recovery_cells):
            raise QualificationError(
                "qualified interface recovery did not cover every selected element"
            )
        for recovered_id, recovery in recovered.items():
            moments = []
            for component in ("xx", "yy", "xy"):
                top = np.asarray(
                    recovery[f"global_{component}_top"], dtype=float
                )
                bottom = np.asarray(
                    recovery[f"global_{component}_bot"], dtype=float
                )
                moments.append(
                    float(np.mean(top - bottom)) * thickness**2 / 12.0
                )
            centroid_x, centroid_y = recovery_centroids[int(recovered_id)]
            expected = producer._mindlin_moments(
                centroid_x,
                centroid_y,
                length=length,
                width=width,
                thickness=thickness,
                elastic_modulus=float(material_spec["elastic_modulus"]),
                poisson_ratio=float(material_spec["poisson_ratio"]),
                modes=moment_modes,
            )
            scale = max(float(np.linalg.norm(expected)), pressure * 1.0e-12)
            error = float(
                np.linalg.norm(np.asarray(moments) - expected) / scale
            )
            cell_errors.setdefault(recovery_cells[int(recovered_id)], []).append(
                error
            )
    # Close the bracket around the direct reads of immutable component cache
    # arrays.  The second warm assembly rejects any changed global operator;
    # the caller's final lease additionally rejects ABA changes.
    post_matrix, post_info = assemble_stiffness(built.model)
    if (
        int(post_info.get("num_elements", -1)) != len(built.model.mesh.elements)
        or post_matrix.shape != stiffness.shape
        or (post_matrix != stiffness).nnz != 0
    ):
        raise QualificationError(
            "plate component observation changed the qualified stiffness"
        )
    return energies, error_energy, reference_energy, cell_errors


def _plate_case_v2(
    bundle: MechanicsBundle,
    authorities: Any,
    record: Mapping[str, Any],
    *,
    recover_interface: bool,
) -> tuple[dict[str, Any], dict[tuple[int, int], float]]:
    """Execute one plate record with a real discrete energy-error norm.

    The historical producer reported only a total-energy-defect proxy.  V2
    retains that number as a diagnostic, but classifies the stiffness-energy
    norm of ``u_h - I_h u_ref`` against the independently authored Mindlin
    reference field.  No extra solve or recovery sweep is required.
    """

    import numpy as np
    from anysolver.boundary import LoadCase
    from anysolver.matrix_assembly import (
        _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE,
        assemble_stiffness_matrix,
    )
    from anysolver.recovery import _recover_qualified_interface_fields

    producer = bundle.structural_producer
    smoke = authorities.smoke_runner
    smoke_authorities = producer._smoke_authorities(authorities)
    built = smoke.build_case_model(
        smoke_authorities,
        producer.case_spec(record, prefix="STRUCTURAL_CONVERGENCE"),
        include_auxiliary_inputs=False,
    )
    level = int(record["level"])
    producer._plate_boundaries(built.model, level)
    reference_spec = authorities.input["coverage"]["convergence_reference"]
    load = LoadCase("uniform_pressure_mindlin_reference")
    pressure = float(reference_spec["pressure"])
    for element_id in built.model.mesh.elements:
        load.add_pressure_load(int(element_id), pressure)
    built.model.load_cases = [load]
    displacement, solver_info, stiffness = _solve_hard_navier_plate_v2(
        built.model, load
    )
    solver_status = str(
        (solver_info.get("convergence_info") or {}).get("status", "unknown")
    )
    if solver_status != "converged":
        raise RuntimeError(f"pressure plate solve ended {solver_status!r}")
    center_id = (level // 2) * (level + 1) + level // 2 + 1
    center_w = abs(
        float(displacement[built.model.mesh.nodes[center_id].dofs[2]])
    )
    model_spec = smoke_authorities.input_payload["model"]
    material_spec = model_spec["material"]
    thickness = float(model_spec["section"]["thickness"])
    length = float(reference_spec["length"])
    width = float(reference_spec["width"])
    if (
        thickness != float(reference_spec["thickness"])
        or float(model_spec["coordinates"]["length_x"]) != length
        or float(model_spec["coordinates"]["length_y"]) != width
    ):
        raise QualificationError(
            "pressure-plate model and independent reference differ"
        )
    reference = producer._mindlin_plate_reference(
        length=length,
        width=width,
        thickness=thickness,
        pressure=pressure,
        elastic_modulus=float(material_spec["elastic_modulus"]),
        poisson_ratio=float(material_spec["poisson_ratio"]),
        terms=int(reference_spec["series_max_odd_index"]),
    )
    moment_modes = producer._mindlin_modes(
        length=length,
        width=width,
        thickness=thickness,
        pressure=pressure,
        elastic_modulus=float(material_spec["elastic_modulus"]),
        poisson_ratio=float(material_spec["poisson_ratio"]),
        terms=int(reference_spec["interface_series_max_odd_index"]),
    )
    reference_vector = _reference_nodal_field(
        built.model,
        reference["modes"],
        length=length,
        width=width,
    )
    # The solve has populated the formulation-native immutable component
    # caches.  Re-enter the exact warm assembly lease once and use its global
    # operator for the three total-energy quadratic forms.  This is exactly
    # the elementwise sum below, without 25,600 repeated public guard entries
    # at N=160.
    if int((solver_info.get("assembly") or {}).get("num_elements", -1)) != len(
        built.model.mesh.elements
    ):
        raise QualificationError(
            "bounded stiffness assembly did not cover every plate element"
        )
    observation_lease = _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
        built.model,
        context="activation-v2 plate observation preflight",
        allow_q4_cached_stiffness=True,
    )
    energies, error_energy, reference_energy, cell_errors = (
        _run_finalized_plate_observation(
            built.model,
            observation_lease,
            lambda: _observe_plate_case_v2(
                built=built,
                displacement=displacement,
                reference_vector=reference_vector,
                stiffness=stiffness,
                producer=producer,
                authorities=authorities,
                level=level,
                record=record,
                recover_interface=recover_interface,
                smoke=smoke,
                thickness=thickness,
                pressure=pressure,
                length=length,
                width=width,
                material_spec=material_spec,
                moment_modes=moment_modes,
                recover_fields=_recover_qualified_interface_fields,
                assemble_stiffness=assemble_stiffness_matrix,
                np_module=np,
            ),
        )
    )
    energy = energies["TOTAL"]
    energy_defect = abs(energy - reference["strain_energy"]) / max(
        abs(reference["strain_energy"]), np.finfo(float).tiny
    )
    denominator = max(abs(energy), np.finfo(float).tiny)
    discrete_energy_error = math.sqrt(
        error_energy / max(reference_energy, np.finfo(float).tiny)
    )
    return (
        {
            "center_displacement": center_w,
            "center_displacement_relative_error": abs(
                center_w - reference["center_displacement"]
            )
            / max(reference["center_displacement"], np.finfo(float).tiny),
            "connectivity_sha256": record["connectivity_sha256"],
            "discrete_reference_energy": reference_energy,
            "energy_defect_proxy": math.sqrt(max(energy_defect, 0.0)),
            "energy_norm_error": discrete_energy_error,
            "finite_element_strain_energy": energy,
            "level": level,
            "mindlin_center_displacement": reference["center_displacement"],
            "mindlin_strain_energy": reference["strain_energy"],
            "pl_participation": {
                key: energies[key] / denominator for key in ("Q4_PL", "S3_PL")
            },
            "q4_residual_hourglass_participation": energies[
                "Q4_RESIDUAL_HOURGLASS"
            ]
            / denominator,
            "record_id": producer.record_id(record),
            "solver_status": solver_status,
        },
        {cell: max(values) for cell, values in cell_errors.items()},
    )


def _gate_convergence(authority: Authority, payload: Mapping[str, Any]) -> tuple[dict[str, bool], dict[str, Any]]:
    limits = authority.contract["acceptance_gates"]
    convergence = limits["convergence"]
    rows = list(payload["rows"])
    levels = list(authority.contract["coverage"]["structural"]["required_levels"])
    baseline = next(row for row in rows if int(row["sequence"]["fraction_percent"]) == 0)
    baseline_fine = float(baseline["records"][-1]["center_displacement_relative_error"])
    passed = True
    summaries: list[dict[str, Any]] = []
    for sequence in rows:
        records = list(sequence["records"])
        response = [float(row["center_displacement_relative_error"]) for row in records]
        energy = [float(row["energy_norm_error"]) for row in records]
        response_slope = bundle_slope(response, levels)
        energy_lower = _lower_one_sided_95(energy, levels)
        successive = all(
            second <= float(convergence["successive_error_factor_maximum"]) * first + 1.0e-13
            for first, second in zip(response, response[1:])
        )
        fraction = int(sequence["sequence"]["fraction_percent"])
        ratio_limit = float(
            convergence[
                "finest_error_ratio_at_25_percent"
                if fraction == 25
                else "finest_error_ratio_through_10_percent"
            ]
        )
        fine_ratio = response[-1] / max(baseline_fine, sys.float_info.min)
        row_pass = bool(
            response_slope is not None
            and response_slope >= float(convergence["response_slope_lower_bound"])
            and energy_lower is not None
            and energy_lower >= float(convergence["energy_norm_slope_lower_95_percent"])
            and successive
            and (fraction == 0 or fine_ratio <= ratio_limit)
        )
        passed = passed and row_pass
        summaries.append(
            {
                "energy_norm_lower_95": energy_lower,
                "energy_norm_values": energy,
                "finest_error_ratio_to_all_q4": fine_ratio,
                "fraction_percent": fraction,
                "passed": row_pass,
                "response_error_slope": response_slope,
                "response_error_values": response,
            }
        )
    interface_limits = limits["interface_resultants"]
    interface_pass = True
    for row in payload["interface_rows"]:
        fraction = int(str(row["record_id"]).split(":")[1].removesuffix("PCT"))
        l2_limit = float(interface_limits["l2_ratio_at_25_percent" if fraction == 25 else "l2_ratio_through_10_percent"])
        p99_limit = float(interface_limits["p99_ratio_at_25_percent" if fraction == 25 else "p99_ratio_through_10_percent"])
        interface_pass = interface_pass and row["l2_ratio_to_all_q4"] is not None and row["p99_ratio_to_all_q4"] is not None
        interface_pass = interface_pass and float(row["l2_ratio_to_all_q4"]) <= l2_limit and float(row["p99_ratio_to_all_q4"]) <= p99_limit
    pl_pass = not any(":Q4_PL" in item or ":S3_PL" in item for item in payload["contradictions"])
    return (
        {"convergence": passed, "interface_resultants": interface_pass, "pl_participation": pl_pass},
        {"sequences": summaries, "interface_rows": payload["interface_rows"]},
    )


def bundle_slope(values: Sequence[float], levels: Sequence[int]) -> float | None:
    if len(values) != len(levels) or any(value <= 0.0 for value in values):
        return None
    x = [-math.log(float(level)) for level in levels]
    y = [math.log(float(value)) for value in values]
    mx, my = statistics.mean(x), statistics.mean(y)
    denominator = sum((value - mx) ** 2 for value in x)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / denominator


def _gate_locking(authority: Authority, payload: Mapping[str, Any], bundle: MechanicsBundle) -> tuple[bool, dict[str, Any]]:
    material = bundle.smoke.input_payload["model"]["material"]
    elastic = float(material["elastic_modulus"])
    poisson = float(material["poisson_ratio"])
    fixture = authority.contract["coverage"]["structural"]["locking_fixture"]
    length = float(fixture["length"])
    width = float(fixture["width"])
    force = float(fixture["tip_force"])
    error_limit = float(authority.contract["acceptance_gates"]["locking"]["finest_response_error_maximum"])
    spread_limit = float(authority.contract["acceptance_gates"]["locking"]["thin_range_response_spread_maximum"])
    passed = True
    diagnostics: list[dict[str, Any]] = []
    for group in payload["rows"]:
        ratios: list[float] = []
        rows: list[dict[str, Any]] = []
        for row in group["rows"]:
            thickness = float(row["thickness_ratio"]) * length
            inertia = width * thickness**3 / 12.0
            area = width * thickness
            shear_modulus = elastic / (2.0 * (1.0 + poisson))
            reference = force * length**3 / (3.0 * elastic * inertia) + force * length / ((5.0 / 6.0) * shear_modulus * area)
            ratio = abs(float(row["tip_displacement"])) / reference
            error = abs(ratio - 1.0)
            passed = passed and error <= error_limit
            if float(row["thickness_ratio"]) <= 1.0e-4:
                ratios.append(ratio)
            rows.append({"relative_error": error, "response_ratio": ratio, "thickness_ratio": row["thickness_ratio"]})
        spread = (max(ratios) - min(ratios)) / statistics.mean(ratios)
        passed = passed and spread <= spread_limit
        diagnostics.append({"fraction_percent": group["fraction_percent"], "rows": rows, "thin_range_response_spread": spread})
    return passed, {"reference": "TIMOSHENKO_CANTILEVER_BENDING_PLUS_SHEAR_V1", "groups": diagnostics}


def _structural_worker(
    authority: Authority,
    bundle: MechanicsBundle,
    worker_id: str,
) -> tuple[dict[str, bool], dict[str, Any], dict[str, int]]:
    diagonal = worker_id.removeprefix("STRUCTURAL_").lower()
    synthetic = _structural_authority(authority, bundle, diagonal)
    convergence, _convergence_status = bundle.structural_producer.produce_convergence(synthetic, quick=False)
    convergence_gates, convergence_diag = _gate_convergence(authority, convergence)
    topology_gate = (
        len(authority.manifest["records"]) == 252
        and canonical_bytes(bundle.manifest_generator.build_manifest()) == authority.manifest_raw
    )
    gates = {
        "convergence": convergence_gates["convergence"],
        "interface_resultants": convergence_gates["interface_resultants"],
        "pl_participation": convergence_gates["pl_participation"],
        "topology_252": topology_gate,
    }
    diagnostic = {
        "convergence": convergence_diag,
        "diagonal": diagonal,
        "support": "HARD_NAVIER_TRANSLATIONS_PLUS_TANGENTIAL_ROTATIONS_V2",
    }
    coverage = {
        "gated_topology_records": 84,
        "global_convergence_records": 84,
    }
    if worker_id == STRUCTURAL_WORKERS[0]:
        patch, _patch_status = bundle.structural_producer.produce_patch(synthetic, quick=False)
        locking, _locking_status = bundle.structural_producer.produce_locking(synthetic, quick=False)
        locking_gate, locking_diag = _gate_locking(authority, locking, bundle)
        patch_gate = not patch["contradictions"] and bool(patch["basis_complete"])
        covariance_gate = patch_gate and all(
            float(row["symmetry_residual"])
            <= float(
                authority.contract["acceptance_gates"][
                    "symmetry_and_covariance_residual_maximum"
                ]
            )
            and float(row["covariance_residual"])
            <= float(
                authority.contract["acceptance_gates"][
                    "symmetry_and_covariance_residual_maximum"
                ]
            )
            for row in patch["basis"]
        )
        gates.update(
            {
                "locking": locking_gate,
                "patch_and_equilibrium": patch_gate,
                "symmetry_and_covariance": covariance_gate,
            }
        )
        diagnostic.update({"locking": locking_diag, "patch": patch})
        coverage["locking_records"] = 18
    return gates, diagnostic, coverage


def _topology_rows(authority: Authority) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for fraction in (0, 10, 25):
        mask = "none" if fraction == 0 else "dispersed"
        matches = [
            row
            for row in authority.manifest["records"]
            if int(row["level"]) == 20
            and int(row["s3_area_fraction_percent"]) == fraction
            and str(row["mask"]) == mask
            and str(row["diagonal"]) == "alternating"
        ]
        if len(matches) != 1:
            raise QualificationError(f"cannot select N20 {fraction}% topology")
        result[fraction] = dict(matches[0])
    return result


def _candidate_case(bundle: MechanicsBundle, rows: Mapping[int, Mapping[str, Any]], fraction: int, *, auxiliary: bool) -> Any:
    row = rows[int(fraction)]
    spec = {
        "case_id": f"S3_DEFAULT_ACTIVATION_V2_N20_{fraction}",
        "topology": {key: row[key] for key in ("connectivity_sha256", "diagonal", "level", "mask", "split_base_cell_count")},
    }
    built = bundle.smoke_runner.build_case_model(bundle.smoke, spec, include_auxiliary_inputs=auxiliary)
    from anysolver.elements import DEFAULT_S3_FORMULATION

    if DEFAULT_S3_FORMULATION != "e4-pl-s3":
        raise QualificationError("qualified S3 is not the current-policy default")
    return built


def _working_set_bytes() -> int:
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        return -1


def _summary(values: Sequence[float]) -> dict[str, float]:
    ordered = sorted(float(value) for value in values)
    median = float(statistics.median(ordered))
    position = 0.95 * (len(ordered) - 1)
    lower, upper = math.floor(position), math.ceil(position)
    p95 = ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])
    return {"mad": float(statistics.median(abs(value - median) for value in ordered)), "median": median, "p95": float(p95)}


def _paired_performance(bundle: MechanicsBundle, rows: Mapping[int, Mapping[str, Any]], fraction: int) -> tuple[bool, dict[str, Any]]:
    from anysolver.assembly import solve_linear
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    models = {
        "all_q4": _candidate_case(bundle, rows, 0, auxiliary=True),
        "mixed": _candidate_case(bundle, rows, fraction, auxiliary=True),
    }
    for built in models.values():
        assemble_stiffness_matrix(built.model)
        displacement, info = solve_linear(built.model, built.load_case, constraint_mode="transformation")
        if (info.get("convergence_info") or {}).get("status") != "converged" or not all(math.isfinite(float(value)) for value in displacement):
            raise QualificationError("paired performance warmup failed")
    samples = {name: {"assembly": [], "solve": [], "rss": []} for name in models}
    for repetition in range(12):
        order = ("all_q4", "mixed") if repetition % 2 == 0 else ("mixed", "all_q4")
        for name in order:
            built = models[name]
            started = time.perf_counter()
            assemble_stiffness_matrix(built.model)
            samples[name]["assembly"].append(time.perf_counter() - started)
            started = time.perf_counter()
            _displacement, info = solve_linear(built.model, built.load_case, constraint_mode="transformation")
            samples[name]["solve"].append(time.perf_counter() - started)
            if (info.get("convergence_info") or {}).get("status") != "converged":
                raise QualificationError("paired performance solve failed")
            samples[name]["rss"].append(float(_working_set_bytes()))
    summaries = {name: {metric: _summary(values) for metric, values in metrics.items()} for name, metrics in samples.items()}
    ratios = {
        metric: summaries["mixed"][metric]["median"] / max(summaries["all_q4"][metric]["median"], sys.float_info.min)
        for metric in ("assembly", "solve", "rss")
    }
    passed = all(value <= 1.10 for value in ratios.values())
    return passed, {"fraction_percent": fraction, "order": "ALTERNATING_BALANCED_12_PAIRS", "ratios": ratios, "summaries": summaries}


def _eigen_authority(authority: Authority, bundle: MechanicsBundle) -> Any:
    coverage = deepcopy(authority.contract["coverage"]["eigen_performance"])
    rows = _topology_rows(authority)

    def bound_topology(fraction: int) -> dict[str, Any]:
        row = rows[fraction]
        return {
            key: row[key]
            for key in (
                "connectivity_sha256",
                "diagonal",
                "level",
                "mask",
                "s3_area_fraction_percent",
                "split_base_cell_count",
            )
        }

    coverage["matched_topologies"] = {
        "all_q4": bound_topology(0),
        "mixed_10_percent": bound_topology(10),
        "mixed_25_percent": bound_topology(25),
    }
    synthetic = SimpleNamespace(
        input={"coverage": coverage},
        contract=authority.contract,
        manifest=authority.manifest,
        manifest_raw=authority.manifest_raw,
        batch_path=ROOT / "scripts" / "benchmark_e4_pl_s3_reference_batch.py",
    )
    bundle.eigen._build_case = lambda _auth, fraction, auxiliary: _candidate_case(bundle, rows, fraction, auxiliary=auxiliary)
    bundle.eigen._apply_supported_boundary = _hard_navier
    return synthetic


def _eigen_worker(authority: Authority, bundle: MechanicsBundle) -> tuple[dict[str, bool], dict[str, Any], dict[str, int]]:
    synthetic = _eigen_authority(authority, bundle)
    rows = _topology_rows(authority)
    statuses: dict[str, bool] = {}
    diagnostics: dict[str, Any] = {}
    for fraction in (10, 25):
        modal_status, modal_diag = bundle.eigen._modal_worker(synthetic, fraction)
        buckling_status, buckling_diag = bundle.eigen._buckling_worker(synthetic, fraction)
        pair_pass, pair_diag = _paired_performance(bundle, rows, fraction)
        statuses[f"modal_{fraction}"] = all(value == bundle.eigen.PASS for value in modal_status.values())
        statuses[f"buckling_{fraction}"] = all(value == bundle.eigen.PASS for value in buckling_status.values())
        statuses[f"performance_{fraction}"] = pair_pass
        diagnostics[f"modal_{fraction}"] = modal_diag
        diagnostics[f"buckling_{fraction}"] = buckling_diag
        diagnostics[f"performance_{fraction}"] = pair_diag
    return statuses, diagnostics, {
        "modal_cases": 2,
        "buckling_cases": 2,
        "paired_performance_comparisons": 24,
    }


def _eigen_fraction_worker(
    authority: Authority,
    bundle: MechanicsBundle,
    fraction: int,
) -> tuple[dict[str, bool], dict[str, Any], dict[str, int]]:
    synthetic = _eigen_authority(authority, bundle)
    rows = _topology_rows(authority)
    modal_status, modal_diag = bundle.eigen._modal_worker(synthetic, fraction)
    buckling_status, buckling_diag = bundle.eigen._buckling_worker(synthetic, fraction)
    pair_pass, pair_diag = _paired_performance(bundle, rows, fraction)
    return (
        {
            f"modal_{fraction}": all(
                value == bundle.eigen.PASS for value in modal_status.values()
            ),
            f"buckling_{fraction}": all(
                value == bundle.eigen.PASS for value in buckling_status.values()
            ),
            f"performance_{fraction}": pair_pass,
        },
        {
            f"modal_{fraction}": modal_diag,
            f"buckling_{fraction}": buckling_diag,
            f"performance_{fraction}": pair_diag,
        },
        {
            "modal_cases": 1,
            "buckling_cases": 1,
            "paired_performance_comparisons": 12,
        },
    )


def _batch_shard_worker(
    authority: Authority,
    bundle: MechanicsBundle,
    shard_index: int,
) -> tuple[dict[str, bool], dict[str, Any], dict[str, int]]:
    synthetic = _eigen_authority(authority, bundle)
    benchmark = _load_module(
        f"_s3_activation_v2_batch_{shard_index}", synthetic.batch_path
    )
    spec = authority.contract["coverage"]["eigen_performance"]["batch"]
    arguments = [
        str(synthetic.batch_path),
        "--elements",
        str(spec["eligible_element_count"]),
        "--repeats",
        str(spec["repetitions_per_shard"]),
        "--qualification-shard-index",
        str(shard_index),
        "--qualification-shard-count",
        str(spec["shard_count"]),
        "--qualification-total-repeats",
        str(spec["repetitions"]),
        "--include-q4-comparator",
    ]
    import contextlib
    import io

    stream = io.StringIO()
    previous = list(sys.argv)
    try:
        sys.argv = arguments
        with contextlib.redirect_stdout(stream):
            returncode = benchmark.main()
    finally:
        sys.argv = previous
    if returncode != 0:
        raise QualificationError(f"batch shard {shard_index} returned {returncode}")
    payload = strict_json(
        stream.getvalue().encode("utf-8"), label=f"batch shard {shard_index}"
    )
    if not isinstance(payload, dict):
        raise QualificationError("batch shard output must be an object")
    expected_indices = list(range(shard_index, int(spec["repetitions"]), 3))
    equality_limit = float(authority.contract["acceptance_gates"]["batch"]["scalar_equality_relative"])
    equality = bool(
        payload.get("repetition_indices") == expected_indices
        and payload["stiffness"]["equality"]["maximum_scaled_error"]
        <= equality_limit
        and payload["recovery"]["equality"]["maximum_scaled_error"]
        <= equality_limit
    )
    fallback = bool(
        payload["stiffness"]["scalar_fallback_element_count"]
        == spec["eligible_element_count"]
        and payload["recovery"]["scalar_fallback_element_count"]
        == spec["eligible_element_count"]
        and payload["recovery"]["scalar_batch_count"] == 0
    )
    return (
        {
            "equality": equality,
            "scalar_fallback": fallback,
            "shard_complete": payload.get("status") == "completed",
        },
        {"benchmark": payload},
        {
            "batch_elements": int(spec["eligible_element_count"]),
            "batch_repetitions": len(expected_indices),
        },
    )


def _run_pytest_lane(authority: Authority, name: str, cwd: Path, nodes: Sequence[str]) -> dict[str, Any]:
    code = (
        "import pathlib,sys,pytest,anysolver;"
        f"target=pathlib.Path({str(authority.target)!r}).resolve();"
        "assert pathlib.Path(anysolver.__file__).resolve().is_relative_to(target);"
        f"raise SystemExit(pytest.main({list(nodes)!r}+['-q']))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=480,
    )
    return {"lane": name, "passed": completed.returncode == 0, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def _special_worker(authority: Authority, _bundle: MechanicsBundle) -> tuple[dict[str, bool], dict[str, Any], dict[str, int]]:
    lanes = authority.contract["coverage"]["special_pytest_lanes"]
    results: list[dict[str, Any]] = []
    for lane in lanes:
        root = Path(str(authority.input["candidates"][lane["repository"]]["root"])).resolve()
        nodes = [str(root / node.split("::", 1)[0]) + ("::" + node.split("::", 1)[1] if "::" in node else "") for node in lane["nodes"]]
        results.append(_run_pytest_lane(authority, str(lane["name"]), root, nodes))
    gates = {f"lane_{row['lane']}": bool(row["passed"]) for row in results}
    diagnostics = {row["lane"]: {key: value for key, value in row.items() if key != "lane"} for row in results}
    return gates, diagnostics, {"special_lanes": len(results), "registered_special_fixtures": 8}


def run_worker(authority: Authority, worker_id: str, output: Path) -> None:
    if worker_id not in WORKERS:
        raise QualificationError(f"unknown worker {worker_id}")
    bundle = _activate(authority)
    if worker_id in STRUCTURAL_WORKERS:
        gates, diagnostics, coverage = _structural_worker(authority, bundle, worker_id)
    elif worker_id == "EIGEN_PERFORMANCE":
        gates, diagnostics, coverage = _eigen_worker(authority, bundle)
    elif worker_id == "SPECIAL_ECOSYSTEM":
        gates, diagnostics, coverage = _special_worker(authority, bundle)
    else:
        gates, diagnostics, coverage = _batch_shard_worker(
            authority, bundle, int(worker_id.removeprefix("BATCH_"))
        )
    diagnostic_path = output.with_name("diagnostic.json")
    _write_exclusive(diagnostic_path, diagnostics, pretty=True)
    _write_exclusive(
        output,
        {
            "coverage": coverage,
            "gates": gates,
            "production_restriction": PRODUCTION_RESTRICTION,
            "schema": WORKER_SCHEMA,
            "worker_id": worker_id,
        },
    )


def _environment(authority: Authority) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    candidates = authority.input["candidates"]
    pieces = [
        str(authority.target),
        str(Path(candidates["ANYstructure"]["root"])),
        str(Path(candidates["ANYintelligent"]["root"])),
    ]
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _read_worker(path: Path, worker_id: str) -> dict[str, Any]:
    raw, value = _read_json(path, pretty=False, label=f"{worker_id} worker")
    _exact_keys(value, ("coverage", "gates", "production_restriction", "schema", "worker_id"), f"{worker_id} worker")
    if value["schema"] != WORKER_SCHEMA or value["worker_id"] != worker_id or raw != canonical_bytes(value):
        raise QualificationError(f"{worker_id} worker identity mismatch")
    if not isinstance(value["gates"], dict) or not value["gates"] or any(type(item) is not bool for item in value["gates"].values()):
        raise QualificationError(f"{worker_id} gates are malformed")
    return value


def _aggregate_batch_shards(
    authority: Authority, output_root: Path
) -> tuple[dict[str, bool], dict[str, Any]]:
    """Recombine the twelve registered paired timing observations."""

    payloads: list[dict[str, Any]] = []
    for worker_id in BATCH_WORKERS:
        path = output_root / worker_id.lower() / "diagnostic.json"
        _raw, diagnostic = _read_json(
            path, pretty=True, label=f"{worker_id} diagnostic"
        )
        _exact_keys(diagnostic, ("benchmark",), f"{worker_id} diagnostic")
        payload = diagnostic["benchmark"]
        if not isinstance(payload, dict):
            raise QualificationError(f"{worker_id} benchmark is malformed")
        payloads.append(payload)
    indices = sorted(
        int(index)
        for payload in payloads
        for index in payload["repetition_indices"]
    )
    spec = authority.contract["coverage"]["eigen_performance"]["batch"]
    expected = list(range(int(spec["repetitions"])))
    if indices != expected:
        raise QualificationError("batch shard repetition coverage is incomplete")

    def samples(route: str, mode: str) -> list[float]:
        return [
            float(value)
            for payload in payloads
            for value in payload[route][mode]["samples_seconds"]
        ]

    stiffness_batch = _summary(samples("stiffness", "batch"))
    stiffness_scalar = _summary(samples("stiffness", "scalar"))
    recovery_batch = _summary(samples("recovery", "batch"))
    recovery_scalar = _summary(samples("recovery", "scalar"))
    q4_values = [
        float(value)
        for payload in payloads
        for value in payload["qualified_q4_comparator"]["batch"][
            "samples_seconds"
        ]
    ]
    q4 = _summary(q4_values)
    stiffness_speedup = stiffness_scalar["median"] / max(
        stiffness_batch["median"], sys.float_info.min
    )
    recovery_speedup = recovery_scalar["median"] / max(
        recovery_batch["median"], sys.float_info.min
    )
    s3_q4_ratio = stiffness_batch["median"] / max(
        q4["median"], sys.float_info.min
    )
    minimum_speedup = float(
        authority.contract["acceptance_gates"]["batch"][
            "minimum_throughput_ratio"
        ]
    )
    baseline = float(
        authority.contract["acceptance_gates"]["performance"][
            "frozen_hot_path_baseline_seconds"
        ]
    )
    gates = {
        "complete_registered_repetitions": indices == expected,
        "stiffness_throughput": stiffness_speedup >= minimum_speedup,
        "recovery_throughput": recovery_speedup >= minimum_speedup,
        "warm_s3_vs_q4": s3_q4_ratio
        <= float(
            authority.contract["acceptance_gates"]["performance"][
                "warm_s3_tangent_ratio_to_qualified_q4_maximum"
            ]
        ),
        "candidate_hot_path": stiffness_batch["median"] <= 1.05 * baseline,
    }
    diagnostic = {
        "qualified_q4": q4,
        "recovery": {
            "batch": recovery_batch,
            "median_speedup": recovery_speedup,
            "scalar": recovery_scalar,
        },
        "repetition_indices": indices,
        "stiffness": {
            "batch": stiffness_batch,
            "frozen_baseline_seconds": baseline,
            "median_speedup": stiffness_speedup,
            "s3_over_q4_ratio": s3_q4_ratio,
            "scalar": stiffness_scalar,
        },
    }
    return gates, diagnostic


def run_cycle(
    authority: Authority,
    output_root: Path,
    *,
    deadline: float | None = None,
) -> tuple[bytes, dict[str, Any]]:
    from e4_pl_q1w_bounded_runner import run_bounded_process

    output_root.mkdir(parents=True, exist_ok=False)
    if deadline is None:
        deadline = time.monotonic() + float(
            authority.input["execution"]["total_command_limit_seconds"]
        )
    environment = _environment(authority)
    timeout = int(authority.input["execution"]["timeout_seconds_per_process"])
    memory = int(authority.input["execution"]["memory_limit_gib_per_process"]) * (1 << 30)

    def launch(worker_id: str) -> tuple[str, Any, Path]:
        directory = output_root / worker_id.lower()
        directory.mkdir()
        output = directory / "record.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--input",
            str(authority.input_path),
            "--worker",
            worker_id,
            "--output",
            str(output),
        ]
        remaining = max(1, int(deadline - time.monotonic()))
        result = run_bounded_process(
            command,
            cwd=directory,
            environment=environment,
            stdout_path=directory / "stdout.log",
            stderr_path=directory / "stderr.log",
            timeout_seconds=min(timeout, remaining),
            memory_limit_bytes=memory,
        )
        if result.status != "COMPLETE":
            output.unlink(missing_ok=True)
        return worker_id, result, output

    process_rows: list[tuple[str, Any, Path]] = []
    for wave in EXECUTION_WAVES:
        if time.monotonic() >= deadline:
            break
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="s3-activation-v2") as pool:
            futures = {pool.submit(launch, worker): worker for worker in wave}
            for future in as_completed(futures):
                process_rows.append(future.result())
    process_rows.sort(key=lambda row: WORKERS.index(row[0]))
    blocked = len(process_rows) != len(WORKERS)
    gates: dict[str, bool] = {}
    coverage: dict[str, int] = {}
    diagnostics: dict[str, Any] = {}
    for worker_id, result, output in process_rows:
        if result.status != "COMPLETE" or not output.is_file():
            blocked = True
            continue
        try:
            value = _read_worker(output, worker_id)
            for name, passed in value["gates"].items():
                key = f"{worker_id.lower()}::{name}"
                if key in gates:
                    raise QualificationError("duplicate gate")
                gates[key] = bool(passed)
            for name, count in value["coverage"].items():
                coverage[f"{worker_id.lower()}::{name}"] = int(count)
            diagnostic_path = output.with_name("diagnostic.json")
            diagnostics[worker_id] = {
                "diagnostic_sha256": sha256(diagnostic_path.read_bytes()),
                "elapsed_ms": int(result.elapsed_ms),
                "peak_rss_bytes": int(result.peak_rss_bytes or -1),
                "process_status": result.status,
                "stderr_sha256": sha256((output.parent / "stderr.log").read_bytes()),
                "stdout_sha256": sha256((output.parent / "stdout.log").read_bytes()),
            }
        except (OSError, QualificationError, TypeError, ValueError):
            blocked = True
    if not blocked:
        try:
            batch_gates, batch_diagnostic = _aggregate_batch_shards(
                authority, output_root
            )
            gates.update(
                {f"batch_aggregate::{name}": value for name, value in batch_gates.items()}
            )
            aggregate_path = output_root / "batch-aggregate-diagnostic.json"
            _write_exclusive(aggregate_path, batch_diagnostic, pretty=True)
            diagnostics["BATCH_AGGREGATE"] = {
                "diagnostic_sha256": sha256(aggregate_path.read_bytes()),
                "process_status": "DERIVED_COMPLETE",
            }
        except (OSError, QualificationError, TypeError, ValueError, KeyError):
            blocked = True
    terminal = TERMINALS[0] if blocked else TERMINALS[1] if not gates or not all(gates.values()) else TERMINALS[2]
    scientific = {
        "candidate_commits": {name: authority.input["candidates"][name]["commit"] for name in sorted(authority.input["candidates"])},
        "coverage": coverage,
        "gates": gates,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": SCIENTIFIC_SCHEMA,
        "terminal": terminal,
    }
    raw = canonical_bytes(scientific)
    with (output_root / "scientific.json").open("xb") as stream:
        stream.write(raw)
    _write_exclusive(output_root / "process-binding.json", diagnostics, pretty=True)
    return raw, scientific


def run_two_cycles(authority: Authority, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + float(
        authority.input["execution"]["total_command_limit_seconds"]
    )
    first_raw, first = run_cycle(
        authority, output_root / "cycle-1", deadline=deadline
    )
    if first["terminal"] != TERMINALS[2] or time.monotonic() - started >= 540.0:
        final = {
            "cycle_scientific_sha256": [sha256(first_raw)],
            "cycles_completed": 1,
            "production_restriction": PRODUCTION_RESTRICTION,
            "schema": TWO_CYCLE_SCHEMA,
            "scientific_byte_identical": False,
            "terminal": first["terminal"],
        }
        _write_exclusive(output_root / "two-cycle.json", final)
        return final
    second_raw, second = run_cycle(
        authority, output_root / "cycle-2", deadline=deadline
    )
    identical = first_raw == second_raw
    terminal = TERMINALS[0] if not identical else second["terminal"]
    final = {
        "cycle_scientific_sha256": [sha256(first_raw), sha256(second_raw)],
        "cycles_completed": 2,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": TWO_CYCLE_SCHEMA,
        "scientific_byte_identical": identical,
        "terminal": terminal,
    }
    _write_exclusive(output_root / "two-cycle.json", final)
    return final


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--authority-only", action="store_true")
    parser.add_argument("--worker", choices=WORKERS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-cycle", action="store_true")
    parser.add_argument("--run-two-cycles", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    try:
        authority = load_authority(args.input)
        if args.authority_only:
            print(sha256(authority.input_raw))
            return 0
        if args.worker:
            if args.output is None:
                raise QualificationError("--worker requires --output")
            run_worker(authority, args.worker, args.output)
            return 0
        if args.run_cycle:
            if args.output_root is None:
                raise QualificationError("--run-cycle requires --output-root")
            _raw, value = run_cycle(authority, args.output_root)
            print(value["terminal"])
            return 0 if value["terminal"] == TERMINALS[2] else 2
        if args.run_two_cycles:
            if args.output_root is None:
                raise QualificationError("--run-two-cycles requires --output-root")
            value = run_two_cycles(authority, args.output_root)
            print(value["terminal"])
            return 0 if value["terminal"] == TERMINALS[2] else 2
        raise QualificationError("select one execution mode")
    except (OSError, QualificationError, subprocess.SubprocessError) as exc:
        print(f"qualification blocked: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
