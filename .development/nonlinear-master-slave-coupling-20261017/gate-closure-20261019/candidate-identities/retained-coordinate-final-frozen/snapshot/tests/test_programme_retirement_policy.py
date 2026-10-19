"""Administrative regression tests for the retired-programme selection policy.

These tests are administrative only: they exercise the retirement manifest,
the stdlib selector and the portable-CI module selection.  They never import
programme or product source and never launch numerical work.  The policy is
the single shared overlay for default pytest and portable CI; these checks
guard against drift, blanket exclusions and silent manifest decay.
"""

from __future__ import annotations

import ast
import json

import pytest

from scripts import retirement_policy


def test_manifest_is_exact_and_well_formed():
    record = retirement_policy.load_manifest()
    assert record["schema"] == retirement_policy.SCHEMA
    assert record["policy"] == "ANY_ECOSYSTEM_PROGRAMME_RETIREMENT_20261016"
    paths = [path for group in record["groups"] for path in group["paths"]]
    assert len(paths) == len(set(paths))
    assert paths
    for path in paths:
        assert path.startswith("tests/test_")
        assert path.endswith(".py")
        assert "\\" not in path
    nodes = [node["id"] for node in record["nodes"]]
    assert len(nodes) == len(set(nodes))
    retired_modules = set(paths)
    for node in nodes:
        module = node.partition("::")[0]
        assert module not in retired_modules
        assert "::" in node
    for group in record["groups"]:
        assert group["reason"].strip()
        assert group["paths"]


def test_manifest_modules_exist_or_are_recorded_trackA_only():
    record = retirement_policy.load_manifest()
    checkout_specific = record["checkout_specific"]
    for group in record["groups"]:
        for path in group["paths"]:
            full = retirement_policy.ROOT / path
            if not full.is_file():
                assert checkout_specific.get(path) == ["rev8-trackA"], path


def test_split_selection_keeps_active_and_drops_retired():
    active_probe = "tests/test_e4_pl_s3_v2d_linear_native_parity.py"
    retired = sorted(retirement_policy.retired_module_paths())
    assert retired
    active, dropped = retirement_policy.split_selection(
        [active_probe, retired[0], active_probe]
    )
    assert active == (active_probe, active_probe)
    assert dropped == (retired[0],)


def test_retired_node_detection_and_mixed_module_separation():
    nodes = retirement_policy.retired_node_ids()
    assert nodes == frozenset({
        "tests/test_ge_beam3_branch_direction.py::"
        "test_exact_boundary_and_failed_event_work_are_reported"
    })
    node = next(iter(nodes))
    module = node.partition("::")[0]
    assert module not in retirement_policy.retired_module_paths()
    assert retirement_policy.is_retired_node(node)
    assert not retirement_policy.is_retired_node(
        module + "::test_implicit_station_direction_with_fixed_predecessor"
    )
    assert not retirement_policy.is_retired_node(
        module + "::test_zero_norm_and_invalid_direction"
    )


def test_opt_in_environment_gate(monkeypatch):
    monkeypatch.setenv(retirement_policy.OPT_IN_ENV, "1")
    assert retirement_policy.opt_in_enabled()
    monkeypatch.setenv(retirement_policy.OPT_IN_ENV, "0")
    assert not retirement_policy.opt_in_enabled()
    monkeypatch.delenv(retirement_policy.OPT_IN_ENV, raising=False)
    assert not retirement_policy.opt_in_enabled()


def test_portable_merge_selection_excludes_retired_modules():
    from scripts import run_portable_ci

    merged = run_portable_ci.merge_test_modules()
    retired = retirement_policy.retired_module_paths()
    assert not retired.intersection(merged)
    assert set(run_portable_ci.PORTABLE_CURRENT_S3_SUCCESSOR_MODULES).issubset(merged)


def test_retired_nodes_are_deselected_for_owned_modules():
    from scripts import run_portable_ci

    module = "tests/test_ge_beam3_branch_direction.py"
    command = run_portable_ci._worker_command([module], retirement_policy.ROOT)
    assert (
        "--deselect=tests/test_ge_beam3_branch_direction.py::"
        "test_exact_boundary_and_failed_event_work_are_reported"
    ) in command


def test_all_b2_physical_profile_modules_are_retired_and_shared_import_stays_active():
    retired = retirement_policy.retired_module_paths()
    on_disk = {
        "tests/" + path.name
        for path in (retirement_policy.ROOT / "tests").glob("test_b2_*.py")
    }
    assert on_disk
    assert on_disk <= retired
    # Shared public-namespace import compatibility is not a programme solve.
    assert "tests/test_common_main_import_admission.py" not in retired


def test_no_retained_test_module_imports_a_retired_helper():
    retired = retirement_policy.retired_module_paths()
    dotted = {path[6:-3].replace("/", ".") for path in retired}
    flat = {path[6:-3] for path in retired}
    for path in sorted((retirement_policy.ROOT / "tests").glob("test_*.py")):
        relative = "tests/" + path.name
        if relative in retired:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                base = name.split(".")[0]
                assert name not in dotted and base not in dotted, (relative, name)
                assert name not in flat and base not in flat, (relative, name)


def test_retired_node_descendants_do_not_bypass_retirement():
    node = next(iter(retirement_policy.retired_node_ids()))
    assert retirement_policy.is_retired_node(node)
    assert retirement_policy.is_retired_node(node + "[case-a]")
    assert retirement_policy.is_retired_node(node + "::nested")
    assert not retirement_policy.is_retired_node(node + "_longer")
    sibling = node.rpartition("::")[0] + "::test_sibling_stays_active"
    assert not retirement_policy.is_retired_node(sibling)
    retired_module = sorted(retirement_policy.retired_module_paths())[0]
    assert retirement_policy.is_retired_node(retired_module)
    assert retirement_policy.is_retired_node(retired_module + "::test_any")


def test_explicit_selector_refusal_normalizes_against_invocation_dir(tmp_path):
    retired_module = sorted(retirement_policy.retired_module_paths())[0]
    name = retired_module.partition("/")[2]
    assert retirement_policy.retired_explicit_selectors(
        [retired_module], retirement_policy.ROOT
    ) == (retired_module,)
    assert retirement_policy.retired_explicit_selectors(
        [name], retirement_policy.ROOT / "tests"
    ) == (name,)
    absolute = str(retirement_policy.ROOT / retired_module)
    assert retirement_policy.retired_explicit_selectors(
        [absolute], tmp_path
    ) == (absolute,)
    node_selector = retired_module + "::test_node"
    assert retirement_policy.retired_explicit_selectors(
        [node_selector], retirement_policy.ROOT
    ) == (node_selector,)
    assert retirement_policy.retired_explicit_selectors(
        ["tests", "tests/test_e4_pl_s3_v2d_linear_native_parity.py"],
        retirement_policy.ROOT,
    ) == ()


def test_mixed_node_explicit_selectors_refuse_before_collection():
    node = next(iter(retirement_policy.retired_node_ids()))
    module, _, suffix = node.partition("::")
    for selector in (node, node + "[case]", node + "::nested"):
        assert retirement_policy.retired_explicit_selectors(
            [selector], retirement_policy.ROOT
        ) == (selector,)
    selector = str(retirement_policy.ROOT / module) + "::" + suffix
    assert retirement_policy.retired_explicit_selectors(
        [selector], retirement_policy.ROOT / "tests"
    ) == (selector,)


def test_mixed_node_retirement_uses_file_identity_with_altered_pytest_root():
    node = next(iter(retirement_policy.retired_node_ids()))
    module, _, suffix = node.partition("::")
    physical = retirement_policy.ROOT / module
    shifted = physical.name + "::" + suffix
    assert retirement_policy.is_retired_collected_node(physical, shifted)
    assert retirement_policy.is_retired_collected_node(physical, shifted + "[case]")
    assert not retirement_policy.is_retired_collected_node(
        physical, physical.name + "::test_shared_sibling"
    )


def test_burnin_portable_inventory_assertions_hold_via_ast_body():
    # tests/test_e4_pl_burnin.py imports product modules at import time and
    # must not be imported here; execute only the audited administrative
    # assertion body of its portable-inventory test, unchanged.
    from scripts import run_portable_ci as portable_ci

    source_path = retirement_policy.ROOT / "tests" / "test_e4_pl_burnin.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "test_portable_ci_inventory_is_unique_and_excludes_long_lanes"
    )
    code = compile(
        ast.Module(body=function.body, type_ignores=[]), str(source_path), "exec"
    )
    exec(code, {"portable_ci": portable_ci})


def test_ge_inventory_rejects_arbitrary_non_ge_registrations(
    tmp_path, monkeypatch
):
    from scripts import run_portable_ci

    record = run_portable_ci._ge_beam3_inventory()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts").mkdir()
    for name in record["portable"] + record["extended"]:
        (tmp_path / name).touch()
    record["extended"].append("tests/test_not_a_ge_module.py")
    (tmp_path / "scripts" / "ge_beam3_release_test_inventory.json").write_text(
        json.dumps(record)
    )
    monkeypatch.setattr(run_portable_ci, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="incomplete or overlapping"):
        run_portable_ci._ge_beam3_inventory()


def test_development_targets_refuse_retired_selection_before_spawning(
    monkeypatch,
):
    from scripts import run_portable_ci

    retired_module = sorted(retirement_policy.retired_module_paths())[0]
    spawn_guard = []
    monkeypatch.setattr(
        run_portable_ci.subprocess, "Popen", lambda *a, **k: spawn_guard.append(a)
    )
    monkeypatch.setattr(
        run_portable_ci.tempfile,
        "mkdtemp",
        lambda **k: spawn_guard.append("mkdtemp"),
    )
    with pytest.raises(ValueError, match="retired programme"):
        run_portable_ci.run(
            workers=1, timeout_seconds=60, development_targets=[retired_module]
        )
    node = next(iter(retirement_policy.retired_node_ids()))
    with pytest.raises(ValueError, match="retired programme"):
        run_portable_ci.run(workers=1, timeout_seconds=60, development_targets=[node])
    assert spawn_guard == []
    sibling = (
        node.rpartition("::")[0]
        + "::test_implicit_station_direction_with_fixed_predecessor"
    )
    assert not retirement_policy.is_retired_node(sibling)
