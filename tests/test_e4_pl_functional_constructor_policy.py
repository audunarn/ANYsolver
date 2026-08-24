"""Closed-world constructor policy for the Q1M functional burn-in lane."""

from __future__ import annotations

import ast
import importlib.util
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _gate_module():
    path = ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    spec = importlib.util.spec_from_file_location("e4_pl_burnin_gate_policy", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _enclosing_function(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> str:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return "<module>"


def _constructor_calls(
    paths: list[Path],
) -> dict[str, Counter[tuple[str, str]]]:
    calls = {
        "ShellElement": Counter(),
        "LegacyShellElement": Counter(),
        "QualifiedE4PLShellElement": Counter(),
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        aliases = {name: {name} for name in calls}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            for imported in node.names:
                if imported.name in aliases:
                    aliases[imported.name].add(imported.asname or imported.name)
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called_name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            for constructor, local_names in aliases.items():
                if called_name in local_names:
                    calls[constructor][
                        (relative, _enclosing_function(node, parents))
                    ] += 1
                    break
    return calls


def test_functional_lane_direct_shell_calls_are_provably_non_q4() -> None:
    inventory = _gate_module().inventory()
    paths = [ROOT / relative for relative in inventory["functional"]]
    calls = _constructor_calls(paths)

    expected_non_q4 = Counter(
        {
            ("tests/test_fe_solver_contact.py", "_q8_panel"): 1,
            ("tests/test_fe_solver_contact.py", "_tri_panel"): 1,
            (
                "tests/test_fe_solver_element_qualification.py",
                "test_q8r_hourglass_cache_is_invalidated_after_geometry_change",
            ): 1,
            (
                "tests/test_fe_solver_theory.py",
                "test_shell_shape_functions_partition_unity",
            ): 1,
            ("tests/test_fe_solver_triangular_shell.py", "_tri_model"): 1,
            (
                "tests/test_fe_solver_triangular_shell.py",
                "test_triangular_shell_shape_functions_interpolate_and_reproduce_fields",
            ): 1,
            (
                "tests/test_fe_solver_triangular_shell.py",
                "test_triangular_aliases_and_mixed_q4_t3_assembly",
            ): 3,
            ("tests/test_fe_solver_triangular_shell_backend.py", "_tri_model"): 1,
            (
                "tests/test_fe_solver_triangular_shell_backend.py",
                "test_triangular_shell_shape_functions_interpolate_and_reproduce_fields",
            ): 1,
            (
                "tests/test_fe_solver_triangular_shell_backend.py",
                "test_triangular_aliases_and_mixed_q4_t3_assembly",
            ): 3,
            ("tests/test_follower_pressure.py", "_single_shell"): 1,
            ("tests/test_generalized_shell_sections.py", "_model_with_shell"): 1,
            ("tests/test_orthotropic_elements.py", "_shell_topology"): 1,
            (
                "tests/test_production_readiness.py",
                "test_production_validation_marks_q8r_as_experimental",
            ): 1,
            (
                "tests/test_production_validation.py",
                "test_validate_production_model_reports_q8_midside_and_warp_warnings",
            ): 1,
            (
                "tests/test_recovery_qualification.py",
                "test_patch_rejects_reduced_q8_and_warped_q4_outside_qualified_scope",
            ): 1,
        }
    )
    assert calls["ShellElement"] == expected_non_q4
    assert sum(calls["ShellElement"].values()) == 20
    assert calls["QualifiedE4PLShellElement"] == Counter()


def test_functional_lane_legacy_q4_calls_are_explicit_and_closed_world() -> None:
    inventory = _gate_module().inventory()
    paths = [ROOT / relative for relative in inventory["functional"]]
    calls = _constructor_calls(paths)

    expected_legacy = Counter(
        {
            ("tests/test_corotational.py", "_single_legacy_shell_model"): 1,
            ("tests/test_follower_pressure.py", "_clamped_pressure_plate"): 1,
            ("tests/test_generalized_shell_sections.py", "_legacy_shell"): 2,
            (
                "tests/test_recovery_qualification.py",
                "test_patch_rejects_reduced_q8_and_warped_q4_outside_qualified_scope",
            ): 1,
        }
    )
    assert calls["LegacyShellElement"] == expected_legacy
    assert sum(calls["LegacyShellElement"].values()) == 5


def test_production_constructor_calls_are_confined_to_central_factory() -> None:
    paths = sorted((ROOT / "src" / "anysolver").rglob("*.py"))
    calls = _constructor_calls(paths)
    assert calls["ShellElement"] == Counter()
    assert calls["LegacyShellElement"] == Counter(
        {("src/anysolver/elements.py", "create_shell_element"): 1}
    )
    assert calls["QualifiedE4PLShellElement"] == Counter(
        {("src/anysolver/elements.py", "create_shell_element"): 1}
    )
