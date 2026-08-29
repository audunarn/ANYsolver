"""Hash-bound S3 activation optimization helpers.

This successor keeps the protocol-v2 scientific calculations intact while
moving connectivity-manifest ownership to the coordinator and amortizing the
plate record's assembly authority over one non-renewable lease.  It is a
research-only execution adapter; it does not independently authorize default
activation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Callable, Mapping


SCHEMA = "anysolver.e4-pl-s3-qualification-optimization-v4"
ANYSTRUCTURE_GATE_ROOT_ENVIRONMENT = {
    "ANYSTRUCTURE_ANY3DVIEW_ROOT": "ANY3dView",
    "ANYSTRUCTURE_ANYBUCKLING_ROOT": "ANYbuckling",
    "ANYSTRUCTURE_ANYFILEIO_ROOT": "ANYfileIO",
    "ANYSTRUCTURE_ANYGEOMETRY_ROOT": "ANYgeometry",
    "ANYSTRUCTURE_ANYMATERIAL_ROOT": "ANYmaterial",
    "ANYSTRUCTURE_ANYMESHER_ROOT": "ANYmesh",
    "ANYSTRUCTURE_ANYSOLVER_ROOT": "ANYsolver",
    "ANYSTRUCTURE_ANYTK3D_ROOT": "ANYtk3D",
}


def _checkpoint(callback: Callable[[str], None] | None, stage: str) -> None:
    if callback is not None:
        callback(stage)


def activate_assigned(
    base: Any,
    authority: Any,
    *,
    verified_loader: Callable[[str, Path], Any] | None = None,
    verified_data_bytes: Mapping[str, bytes] | None = None,
) -> Any:
    """Activate mechanics without regenerating the 252-record manifest.

    The standard-library coordinator has already selected and hash-bound the
    exact stored manifest row.  The child still loads the registered manifest
    generator because interface-cell construction uses its authored mask
    functions, but deliberately does not call ``build_manifest``.  Formal
    successor authority must bind this adapter, the stored manifest, and the
    coordinator-created assignment together.
    """

    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    generator = sys.modules.get("_s3_v4_binding_generator")
    if generator is None:
        raise base.QualificationError("verified binding generator is not active")
    candidates = authority.input.get("candidates")
    try:
        generator._activate_bound_runtime_environment(
            authority.input["runtime_environment"]
        )
        verified = generator._verify_bound_execution_target(
            authority.target,
            candidates,
            authority.input["runtime_environment"],
        )
    except (generator.BindingError, OSError) as exc:
        raise base.QualificationError(
            "exact-wheel installed target provenance differs"
        ) from exc
    if verified != candidates:
        raise base.QualificationError(
            "exact-wheel installed target binding is noncanonical"
        )
    imported = __import__("anysolver")
    if str(getattr(imported, "__version__", "")) != "0.4.0":
        raise base.QualificationError(
            "isolated target did not import ANYsolver 0.4.0"
        )
    if not Path(str(imported.__file__)).resolve().is_relative_to(
        authority.target
    ):
        raise base.QualificationError(
            "ANYsolver did not originate in the isolated target"
        )
    reference_cases = base.REFERENCE_CASES
    if str(reference_cases) not in sys.path:
        sys.path.insert(0, str(reference_cases))
    loader = base._load_module if verified_loader is None else verified_loader
    common = loader(
        "e4_pl_s3_mixed_structural_common",
        reference_cases / "e4_pl_s3_mixed_structural_common.py",
    )
    producer = loader(
        "_s3_activation_v3_structural_producer",
        reference_cases / "e4_pl_s3_mixed_structural_producer.py",
    )
    eigen = loader(
        "_s3_activation_v3_eigen",
        reference_cases / "e4_pl_s3_mixed_eigen_performance.py",
    )
    smoke_runner = loader(
        "_s3_activation_v3_smoke",
        reference_cases / "e4_pl_s3_mixed_mesh_qualification_runner.py",
    )
    if verified_data_bytes is not None:
        def read_verified_json(
            path: Path,
            *,
            style: str,
            label: str,
        ) -> tuple[dict[str, Any], bytes]:
            key = os.path.normcase(
                os.path.normpath(str(Path(path).absolute()))
            )
            raw = verified_data_bytes.get(key)
            if raw is None:
                raise smoke_runner.CampaignInputError(
                    f"unregistered frozen JSON route: {path}"
                )
            value = smoke_runner._strict_json(raw, label=label)
            if not isinstance(value, dict):
                raise smoke_runner.CampaignInputError(
                    f"{label} must be a JSON object"
                )
            expected = (
                smoke_runner._canonical_bytes(value)
                if style == "compact"
                else smoke_runner._pretty_canonical_bytes(value)
            )
            if raw != expected:
                raise smoke_runner.CampaignInputError(
                    f"{label} is not canonical {style} JSON"
                )
            return value, raw

        smoke_runner._read_canonical_json = read_verified_json
    smoke = smoke_runner.load_authorities(
        reference_cases / "e4_pl_s3_mixed_mesh_smoke_input.json"
    )
    payload = deepcopy(smoke.input_payload)
    payload["factories"]["default_s3_expected"] = "e4-pl-s3"
    smoke = replace(smoke, input_payload=payload)
    manifest_generator = loader(
        "_s3_activation_v3_manifest",
        reference_cases / "e4_pl_s3_mixed_mesh_manifest.py",
    )
    if verified_loader is not None:
        # Protocol-v2 helpers otherwise reload registered programs from their
        # paths after authority validation.  The formal runner supplies one
        # loader backed only by its already verified byte buffers.
        common._load_source = verified_loader
        eigen._load_module = verified_loader
        smoke_runner._load_manifest_generator = lambda: manifest_generator
    return base.MechanicsBundle(
        common,
        producer,
        eigen,
        smoke_runner,
        smoke,
        manifest_generator,
    )


def structural_authority(
    base: Any,
    authority: Any,
    bundle: Any,
    diagonal: str,
    *,
    base_factory: Callable[[Any, Any, str], Any] | None = None,
) -> Any:
    """Create a structural authority using the successor plate record path."""

    factory = base._structural_authority if base_factory is None else base_factory
    synthetic = factory(authority, bundle, diagonal)
    bundle.structural_producer._plate_case = (
        lambda made, record, *, recover_interface: plate_case(
            base,
            bundle,
            made,
            record,
            recover_interface=recover_interface,
        )
    )
    return synthetic


def run_pytest_lane_without_elapsed_ceiling(
    base: Any,
    authority: Any,
    name: str,
    cwd: Path,
    nodes: list[str] | tuple[str, ...],
    *,
    isolation_config_bytes: bytes,
) -> dict[str, Any]:
    """Run one registered special lane under its parent's Job Object.

    The formal v4 coordinator owns the complete process-tree memory cap and
    inactivity watchdog.  This nested lane therefore has no independent wall
    clock timeout; elapsed time is diagnostic and cannot classify the result.
    """

    import subprocess

    binding_path = Path(authority.input_path).resolve(strict=True)
    generator_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "prepare_e4_pl_s3_qualification_v4_input.py"
    ).resolve(strict=True)
    lane_temp = Path(tempfile.mkdtemp(prefix="anysolver-s3-v4-pytest-"))
    expected_binding_sha256 = hashlib.sha256(authority.input_raw).hexdigest().upper()
    outer_binding = base.strict_json(
        authority.input_raw,
        label="outer verified candidate binding",
    )
    expected_generator = outer_binding.get("files", {}).get("binding_generator")
    expected_config = outer_binding.get("files", {}).get("preflight_config")
    if (
        not isinstance(expected_generator, dict)
        or set(expected_generator) != {"bytes", "path", "sha256"}
        or expected_generator["path"]
        != "scripts/prepare_e4_pl_s3_qualification_v4_input.py"
    ):
        shutil.rmtree(lane_temp)
        raise base.QualificationError("verified binding generator authority differs")
    if (
        not isinstance(expected_config, dict)
        or set(expected_config) != {"bytes", "path", "sha256"}
        or expected_config["path"]
        != "docs/reference_cases/e4_pl_s3_pytest_isolation_v4.ini"
        or len(isolation_config_bytes) != expected_config["bytes"]
        or hashlib.sha256(isolation_config_bytes).hexdigest().upper()
        != expected_config["sha256"]
    ):
        shutil.rmtree(lane_temp)
        raise base.QualificationError("verified pytest isolation authority differs")
    staged_config = lane_temp / "pytest-isolation.ini"
    with staged_config.open("xb") as stream:
        stream.write(isolation_config_bytes)
    lane_code = base._pytest_lane_code(authority, nodes)
    needle = "+ ['-q']"
    if lane_code.count(needle) != 1:
        shutil.rmtree(lane_temp)
        raise base.QualificationError("pytest lane invocation authority differs")
    lane_code = lane_code.replace(
        needle,
        (
            "+ ['-q', '-p', 'no:cacheprovider', '-c', "
            f"{str(staged_config)!r}, '--rootdir', {str(cwd)!r}, "
            f"'--confcutdir', {str(cwd)!r}, '--import-mode=importlib', "
            f"'--basetemp', {str(lane_temp / 'basetemp')!r}]"
        ),
        1,
    )
    code = (
        "import hashlib,importlib,json,os,pathlib,sys,types;"
        "sys.dont_write_bytecode=True;"
        "binding_path=pathlib.Path(sys.argv[1]).resolve(strict=True);"
        "generator_path=pathlib.Path(sys.argv[2]).resolve(strict=True);"
        "expected_binding_sha256=sys.argv[3];"
        "expected_generator_bytes=int(sys.argv[4]);expected_generator_sha256=sys.argv[5];"
        "raw=binding_path.read_bytes();"
        "assert hashlib.sha256(raw).hexdigest().upper()==expected_binding_sha256;"
        "binding=json.loads(raw);row=binding['files']['binding_generator'];"
        "generator_status=generator_path.lstat();"
        "assert generator_path.is_file() and not generator_path.is_symlink() and not (getattr(generator_status,'st_file_attributes',0)&0x400);"
        "generator_raw=generator_path.read_bytes();"
        "assert row=={'bytes':expected_generator_bytes,'path':'scripts/prepare_e4_pl_s3_qualification_v4_input.py','sha256':expected_generator_sha256};"
        "assert len(generator_raw)==expected_generator_bytes and hashlib.sha256(generator_raw).hexdigest().upper()==expected_generator_sha256;"
        "generator=types.ModuleType('_s3_v4_nested_target');"
        "generator.__file__=str(generator_path);generator.__package__='';"
        "sys.modules[generator.__name__]=generator;"
        "exec(compile(generator_raw,str(generator_path),'exec',dont_inherit=True,optimize=0),generator.__dict__);"
        "binding=generator.read_json(binding_path);"
        "assert raw==generator.canonical_bytes(binding);"
        "generator._activate_bound_runtime_environment(binding['runtime_environment']);"
        "target=pathlib.Path(binding['execution_target']).resolve(strict=True);"
        "candidates=binding['candidates'];"
        "assert generator._verify_bound_execution_target(target,candidates,binding['runtime_environment'])==candidates;"
        "assert all(generator._verify_candidate(name,candidates[name])==candidates[name] for name in generator.CANDIDATES);"
        "assert 'sitecustomize' not in sys.modules and 'usercustomize' not in sys.modules;"
        "source_root=pathlib.Path(candidates['ANYintelligent']['root']).resolve(strict=True);"
        "roots=[str(target),str(source_root)];"
        "sys.path[:0]=list(dict.fromkeys(roots));"
        "source_mods=[importlib.import_module(name) for name in generator.SOURCE_CANDIDATE_IMPORTS['ANYintelligent']];"
        "assert all(getattr(mod,'__file__',None) is not None and pathlib.Path(mod.__file__).resolve(strict=True).is_relative_to(source_root) for mod in source_mods);"
        f"exec({lane_code!r})"
    )
    process_environment = authority.input["runtime_environment"].get(
        "process_environment"
    )
    if not isinstance(process_environment, dict) or not all(
        type(key) is str and type(value) is str
        for key, value in process_environment.items()
    ):
        raise base.QualificationError("bound process environment differs")
    environment = dict(process_environment)
    environment.update(
        {
            "ANYSOLVER_S3_V4_BINDING": str(binding_path),
            "ANYSOLVER_S3_V4_CROSS_WHEEL": "1",
            "ANYSOLVER_S3_V4_TARGET": str(authority.target),
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    if set(ANYSTRUCTURE_GATE_ROOT_ENVIRONMENT) & set(process_environment):
        shutil.rmtree(lane_temp)
        raise base.QualificationError(
            "ANYstructure dependency roots must not be inherited"
        )
    candidates = outer_binding.get("candidates")
    if not isinstance(candidates, dict):
        shutil.rmtree(lane_temp)
        raise base.QualificationError("bound candidate roots differ")
    structure = candidates.get("ANYstructure")
    if not isinstance(structure, dict) or type(structure.get("root")) is not str:
        shutil.rmtree(lane_temp)
        raise base.QualificationError("bound ANYstructure root differs")
    structure_root = Path(structure["root"]).resolve(strict=True)
    if Path(cwd).resolve(strict=True) == structure_root:
        for environment_name, candidate_name in sorted(
            ANYSTRUCTURE_GATE_ROOT_ENVIRONMENT.items()
        ):
            candidate = candidates.get(candidate_name)
            if not isinstance(candidate, dict) or type(candidate.get("root")) is not str:
                shutil.rmtree(lane_temp)
                raise base.QualificationError(
                    "bound ANYstructure dependency root differs"
                )
            environment[environment_name] = str(
                Path(candidate["root"]).resolve(strict=True)
            )
    for environment_name, length, alphabet in (
        ("E4_PL_S3_QUALIFICATION_REQUEST_ID", 32, "0123456789abcdef"),
        (
            "E4_PL_S3_QUALIFICATION_ATTEMPT_SHA256",
            64,
            "0123456789ABCDEF",
        ),
    ):
        value = os.environ.get(environment_name)
        if value is not None:
            if len(value) != length or any(character not in alphabet for character in value):
                raise base.QualificationError(f"{environment_name} is malformed")
            environment[environment_name] = value
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                "-B",
                "-c",
                code,
                str(binding_path),
                str(generator_path),
                expected_binding_sha256,
                str(expected_generator["bytes"]),
                str(expected_generator["sha256"]),
            ],
            cwd=cwd,
            check=False,
            capture_output=True,
            env=environment,
            text=True,
        )
    finally:
        shutil.rmtree(lane_temp)
    try:
        report: dict[str, Any] | None = base._parse_pytest_lane_report(
            completed.stdout
        )
    except base.QualificationError:
        report = None
    status = base._pytest_lane_status(completed.returncode, report)
    return {
        "lane": name,
        "passed": status == "PASS",
        "report": report,
        "requested_node_count": len(nodes),
        "returncode": completed.returncode,
        "status": status,
        "stderr": completed.stderr,
        "stdout": completed.stdout,
    }


def _solve_hard_navier_plate_under_lease(
    base: Any,
    model: Any,
    load: Any,
    qualified_runtime_guard: Any,
) -> tuple[Any, dict[str, Any], Any]:
    """Execute the unchanged flexural solve inside the caller-owned lease."""

    import numpy as np
    from scipy import sparse
    from anysolver.assembly import _solve_reduced_system
    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver.constraint_audit import constraint_residual_summary
    from anysolver.fe_core import FEModel
    from anysolver.matrix_assembly import _assemble_system_under_lease

    if type(model) is not FEModel or type(load) is not LoadCase:
        raise base.QualificationError(
            "bounded plate solve requires exact model/load types"
        )
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
        raise base.QualificationError("bounded plate support protocol changed")
    for support, (name, constraints) in zip(supports, expected_supports):
        if (
            type(support) is not BoundaryCondition
            or support.name != name
            or type(support.node_ids) is not list
            or type(support.dof_constraints) is not dict
            or support.dof_constraints != constraints
            or any(type(node_id) is not int for node_id in support.node_ids)
        ):
            raise base.QualificationError(
                "bounded plate support authority changed"
            )

    stiffness, force, assembly_info = _assemble_system_under_lease(
        model,
        load,
        qualified_runtime_guard=qualified_runtime_guard,
    )
    if (
        not sparse.isspmatrix_csr(stiffness)
        or stiffness.shape[0] != stiffness.shape[1]
        or force.shape != (stiffness.shape[0],)
        or not np.all(np.isfinite(force))
        or not np.all(np.isfinite(stiffness.data))
    ):
        raise base.QualificationError("bounded plate assembly is malformed")

    active_all = np.asarray(
        [
            dof
            for _node_id, node in sorted(model.mesh.nodes.items())
            for dof in (node.dofs[2], node.dofs[3], node.dofs[4])
        ],
        dtype=np.intp,
    )
    free_all = np.asarray(
        model.mesh.dof_manager.get_free_dofs(), dtype=np.intp
    )
    active_mask = np.zeros(stiffness.shape[0], dtype=bool)
    active_mask[active_all] = True
    active = free_all[active_mask[free_all]]
    inactive = free_all[~active_mask[free_all]]
    if active.size == 0 or active.size + inactive.size != free_all.size:
        raise base.QualificationError(
            "bounded plate coordinate partition is incomplete"
        )
    if inactive.size and np.any(force[inactive] != 0.0):
        raise base.QualificationError(
            "bounded plate inactive coordinates carry load"
        )

    inactive_active = stiffness[inactive, :][:, active].tocsr()
    active_inactive = stiffness[active, :][:, inactive].tocsr()
    inactive_active.eliminate_zeros()
    active_inactive.eliminate_zeros()
    if inactive_active.nnz or active_inactive.nnz:
        raise base.QualificationError(
            "bounded plate membrane/drill and flexural blocks are coupled"
        )

    reduced = stiffness[active, :][:, active].tocsr()
    solution, convergence = _solve_reduced_system(
        reduced,
        np.asarray(force[active], dtype=float),
        "direct",
    )
    active_force = np.asarray(force[active], dtype=float)
    refinement_steps = 0
    if convergence.get("status") == "converged":
        # Fine thin-plate systems can satisfy the solver's normwise backward
        # error while losing digits in the stricter load-scaled residual.
        # Retain the frozen residual limit and improve the same reduced
        # solution with at most two deterministic direct corrections.
        for _refinement in range(2):
            correction_rhs = active_force - np.asarray(
                reduced @ solution,
                dtype=float,
            ).reshape(-1)
            correction, correction_info = _solve_reduced_system(
                reduced,
                correction_rhs,
                "direct",
            )
            if correction_info.get("status") != "converged":
                break
            solution = np.asarray(solution + correction, dtype=float)
            refinement_steps += 1
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
        if (
            not math.isfinite(relative_residual)
            or relative_residual > 1.0e-8
        ):
            raise base.QualificationError(
                "bounded plate full-system residual exceeds its frozen limit: "
                f"{relative_residual:.17e} after {refinement_steps} refinements"
            )
    constraint_report = constraint_residual_summary(model, displacement)
    if constraint_report.get("status") != "passed":
        raise base.QualificationError(
            "bounded plate support postcheck failed"
        )
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
            "deterministic_iterative_refinement_steps": refinement_steps,
        },
        stiffness,
    )


def plate_case(
    base: Any,
    bundle: Any,
    authorities: Any,
    record: Mapping[str, Any],
    *,
    recover_interface: bool,
    activity: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], dict[tuple[int, int], float]]:
    """Run one unchanged plate record under one assembly authority lease."""

    import numpy as np
    from anysolver.boundary import LoadCase
    from anysolver.matrix_assembly import (
        _assemble_element_matrix_under_lease,
        _run_with_qualified_assembly_runtime_lease,
    )
    from anysolver.recovery import _recover_qualified_interface_fields

    producer = bundle.structural_producer
    smoke = authorities.smoke_runner
    smoke_authorities = producer._smoke_authorities(authorities)
    _checkpoint(activity, "model-construction")
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
    built.model.apply_boundary_conditions()
    _checkpoint(activity, "model-admitted")

    def operation(lease: Any) -> tuple[dict[str, Any], dict[tuple[int, int], float]]:
        _checkpoint(activity, "assembly-start")
        displacement, solver_info, stiffness = (
            _solve_hard_navier_plate_under_lease(
                base,
                built.model,
                load,
                lease,
            )
        )
        _checkpoint(activity, "solve-complete")
        solver_status = str(
            (solver_info.get("convergence_info") or {}).get(
                "status", "unknown"
            )
        )
        if solver_status != "converged":
            raise RuntimeError(
                f"pressure plate solve ended {solver_status!r}"
            )
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
            raise base.QualificationError(
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
        reference_vector = base._reference_nodal_field(
            built.model,
            reference["modes"],
            length=length,
            width=width,
        )
        if int((solver_info.get("assembly") or {}).get("num_elements", -1)) != len(
            built.model.mesh.elements
        ):
            raise base.QualificationError(
                "bounded stiffness assembly did not cover every plate element"
            )

        def assemble_stiffness(model: Any) -> tuple[Any, dict[str, Any]]:
            return _assemble_element_matrix_under_lease(
                model,
                "stiffness",
                lambda element, mesh, material: element.compute_stiffness_matrix(
                    mesh, material
                ),
                lease,
            )

        _checkpoint(activity, "observation-start")
        energies, error_energy, reference_energy, cell_errors = (
            base._observe_plate_case_v2(
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
                assemble_stiffness=assemble_stiffness,
                np_module=np,
            )
        )
        _checkpoint(activity, "observation-complete")
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
                "mindlin_center_displacement": reference[
                    "center_displacement"
                ],
                "mindlin_strain_energy": reference["strain_energy"],
                "pl_participation": {
                    key: energies[key] / denominator
                    for key in ("Q4_PL", "S3_PL")
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

    return _run_with_qualified_assembly_runtime_lease(
        built.model,
        context="activation-v3 plate record",
        allow_q4_cached_stiffness=True,
        operation=operation,
    )
