"""Standard-library-only V6F audit; never imports candidate mechanics."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any


FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _class_methods(source: str, class_name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise ValueError(f"missing class {class_name}")


def audit(root: Path) -> dict[str, Any]:
    element_path = root / "src/anysolver/e4_pl_s3_v2d_element.py"
    recovery_path = root / "src/anysolver/recovery.py"
    tangent_path = root / "src/anysolver/current_state_tangent.py"
    elements_path = root / "src/anysolver/elements.py"
    element_source = element_path.read_text(encoding="utf-8")
    recovery_source = recovery_path.read_text(encoding="utf-8")
    tangent_source = tangent_path.read_text(encoding="utf-8")
    elements_source = elements_path.read_text(encoding="utf-8")
    methods = _class_methods(element_source, "NativeParityE4PLS3V2DShellElement")

    closed_requirements = {
        "ACTIVITY_CONTACT_BATCH": {
            "seal_noncurrent_deleted_state",
            "compute_noncurrent_deleted_residual_operator",
        },
        "DESCRIPTOR_MODAL_AND_RAYLEIGH": {
            "compute_mass_components",
            "dynamic_algebraic_directions",
        },
        "GENERALIZED_SECTION_AND_NONLINEAR_STATE": {
            "compute_nonlinear_response",
            "init_model_bound_nonlinear_state",
        },
        "LINEAR_STIFFNESS_FORCE_AND_LOADS": {
            "compute_stiffness_matrix",
            "compute_internal_forces",
            "compute_dead_transverse_pressure_load",
        },
        "OFFSET_DIRECTOR_AND_INITIAL_FIELDS": {
            "material_mid_surface_offset_from_reference",
            "native_reference_directors",
        },
        "REFERENCE_ELASTIC_BUCKLING": {"compute_geometric_stiffness_matrix"},
        "SAME_FORMULATION_SERIALIZATION_RESTART": {
            "serialize_nonlinear_state",
            "deserialize_nonlinear_state",
            "to_dict",
            "from_dict",
        },
    }
    closed = {
        route: required <= methods for route, required in sorted(closed_requirements.items())
    }

    v2d_recovery_registered = (
        "NativeParityE4PLS3V2DShellElement" in recovery_source
        and FORMULATION_ID in recovery_source
    )
    v2d_current_state_registered = (
        "NativeParityE4PLS3V2DShellElement" in tangent_source
        and FORMULATION_ID in tangent_source
    )
    global_tensor_route = (
        "global tensor recovery is pending a successor gate" not in element_source
    )
    open_routes = []
    if not v2d_recovery_registered:
        open_routes.append("COMMITTED_LAYERED_PUBLIC_RECOVERY")
    if not v2d_current_state_registered:
        open_routes.append("CURRENT_STATE_MODAL_AND_BUCKLING")
    if not global_tensor_route:
        open_routes.append("GLOBAL_TENSOR_AND_PATCH_RECOVERY")
    if not all(closed.values()):
        raise ValueError("a previously closed V2D route is no longer present")
    if 'DEFAULT_Q4_FORMULATION = "e4-pl"' not in elements_source:
        raise ValueError("qualified Q4 default changed")
    if 'DEFAULT_S3_FORMULATION = "legacy-s3"' not in elements_source:
        raise ValueError("legacy S3 default changed")

    terminal = (
        "UNCLASSIFIED_E4_PL_S3_V6F_REMAINING_PRODUCTION_PARITY"
        if open_routes
        else "PROVISIONAL_GO_E4_PL_S3_V6F_STAGE4A_RERUN_REVIEW"
    )
    return {
        "activation_authorized": False,
        "audit": {
            "closed_routes": closed,
            "open_route_count": len(open_routes),
            "open_routes": open_routes,
        },
        "inputs": {
            "current_state_tangent_sha256": _sha256(tangent_path),
            "element_sha256": _sha256(element_path),
            "elements_sha256": _sha256(elements_path),
            "recovery_sha256": _sha256(recovery_path),
        },
        "next_gate": (
            "V6G_V2D_RECOVERY_AND_CURRENT_STATE_EIGEN_PARITY"
            if open_routes
            else "V6G_STAGE4A_RERUN_AUTHORITY"
        ),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6f-final-parity-audit-result-v1",
        "stage4a_scientific_rerun_authorized": False,
        "terminal": terminal,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(_canonical(audit(args.root.resolve())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
