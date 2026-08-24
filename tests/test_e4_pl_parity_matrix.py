from __future__ import annotations

import ast
import json
from pathlib import Path

from anysolver import QualifiedE4PLShellElement
from anysolver.elements import ShellElement, create_element


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "reference_cases" / "e4_pl_q1j_parity_matrix.json"


def _public_shell_api() -> set[str]:
    tree = ast.parse((ROOT / "src" / "anysolver" / "elements.py").read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in {"Element", "ShellElement"}:
            for child in node.body:
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not child.name.startswith("_")
                ):
                    result.add(child.name)
    return result


def test_parity_matrix_classifies_every_public_shell_capability() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert matrix["schema"] == "anysolver.s4.e4-pl-q1j-parity-matrix-v1"
    assert set(matrix["public_api"]) == _public_shell_api()
    capabilities = matrix["capabilities"]
    assert len({row["id"] for row in capabilities}) == len(capabilities)
    required = {row["id"]: row for row in capabilities if row["required"]}
    for capability in (
        "warped_curved_geometry",
        "generalized_shell_sections",
        "geometric_stiffness_and_buckling",
        "nonlinear_geometry",
        "mass_and_dynamics",
        "contact_and_coupling",
        "physical_recovery",
        "deletion_damage_and_restart_state",
        "batched_assembly_and_performance",
        "factory_and_default_activation",
    ):
        assert capability in required


def test_open_parity_items_fail_closed_before_default_activation() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    open_markers = ("PENDING", "BLOCKED", "LEGACY_FALLBACK")
    open_required = [
        row for row in matrix["capabilities"]
        if row["required"] and any(marker in row["status"] for marker in open_markers)
    ]
    assert open_required
    assert matrix["activation"] == {
        "default_factory": "BLOCKED_UNTIL_ALL_REQUIRED_CAPABILITIES_CLOSE",
        "legacy_shell_default": True,
        "public_package_export": True,
        "qualified_element_factory_alias": True,
    }
    default = create_element("shell", 1, [1, 2, 3, 4], "steel")
    assert type(default) is ShellElement
    assert QualifiedE4PLShellElement.__module__ == "anysolver.e4_pl_element"


def test_runtime_shell_dispatch_accepts_subclasses_without_exact_name_checks() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in matrix["capabilities"]}
    assert by_id["runtime_exact_class_name_dispatch"]["status"] == "CLOSED_ISINSTANCE_DISPATCH"
    runtime_source = (ROOT / "src" / "anysolver" / "runtime.py").read_text(encoding="utf-8")
    test_case_source = (ROOT / "src" / "anysolver" / "test_cases.py").read_text(encoding="utf-8")
    assert '.__class__.__name__ != "ShellElement"' not in runtime_source
    assert '.__class__.__name__ == "ShellElement"' not in runtime_source
    assert ".__class__.__name__ == 'ShellElement'" not in test_case_source
    assert "isinstance(element, _full_backend.ShellElement)" in runtime_source
    assert "isinstance(element, ShellElement)" in test_case_source
