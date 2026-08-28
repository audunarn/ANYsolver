"""Exact-wheel S3 default and provenance gate for formal qualification v4."""

from __future__ import annotations

import hashlib
import importlib
from importlib import metadata
import os
from pathlib import Path
import sys
from typing import Any

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("ANYSOLVER_S3_V4_CROSS_WHEEL") != "1",
    reason="runs only in the hash-bound isolated-wheel qualification target",
)


EXPECTED_DISTRIBUTIONS = {
    "ANY3dView": "0.5.4",
    "ANYbuckling": "0.1.1",
    "ANYsolver": "0.4.0",
    "ANYfem": "0.4.0",
    "ANYmesher": "0.3.2",
    "ANYstructure": "6.3.1",
    "ANYtk3D": "0.5.3",
    "ANYfileio": "0.2.1",
    "ANYmaterial": "0.1.1",
    "ANYgeometry": "0.4.1",
}


def _load_generator() -> Any:
    generator = sys.modules.get("_s3_v4_nested_target")
    assert generator is not None, "verified v4 binding generator is not active"
    return generator


def _verify_bound_target_before_runtime_imports() -> tuple[Any, dict[str, Any]]:
    generator = _load_generator()
    binding_path = Path(os.environ["ANYSOLVER_S3_V4_BINDING"]).resolve(strict=True)
    raw = binding_path.read_bytes()
    binding = generator.read_json(binding_path)
    assert raw == generator.canonical_bytes(binding)
    target = Path(os.environ["ANYSOLVER_S3_V4_TARGET"]).resolve(strict=True)
    assert target == Path(binding["execution_target"]).resolve(strict=True)
    candidates = binding["candidates"]
    assert (
        generator._verify_bound_execution_target(
            target,
            candidates,
            binding["runtime_environment"],
        )
        == candidates
    )
    assert "sitecustomize" not in sys.modules
    assert "usercustomize" not in sys.modules
    return generator, binding


def _assert_runtime_modules_match_bound_wheel(
    target: Path,
    candidate: dict[str, Any],
) -> None:
    installed = candidate["wheel"]["installed_target"]
    import_name = installed["import_name"]
    importlib.import_module(import_name)
    exact_files = {
        row["path"]: row
        for row in installed["files"]
        if row["provenance"] == "WHEEL_RECORD"
    }
    observed = 0
    for module_name, module in tuple(sys.modules.items()):
        if module_name != import_name and not module_name.startswith(import_name + "."):
            continue
        origin = getattr(module, "__file__", None)
        if origin is None:
            continue
        path = Path(str(origin)).resolve(strict=True)
        assert path.is_relative_to(target)
        relative = path.relative_to(target).as_posix()
        row = exact_files[relative]
        raw = path.read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest().upper() == row["sha256"]
        observed += 1
    assert observed > 0


def test_exact_wheels_import_and_route_qualified_s3_with_provenance() -> None:
    _generator, binding = _verify_bound_target_before_runtime_imports()
    assert {
        distribution: version
        for distribution, version, _import_name in _generator.PACKAGED_IDENTITIES.values()
    } == EXPECTED_DISTRIBUTIONS
    intelligent_root = Path(binding["candidates"]["ANYintelligent"]["root"]).resolve(
        strict=True
    )
    for import_name in _generator.SOURCE_CANDIDATE_IMPORTS["ANYintelligent"]:
        source_module = importlib.import_module(import_name)
        assert source_module.__file__ is not None
        assert Path(source_module.__file__).resolve(strict=True).is_relative_to(
            intelligent_root
        )
    import anysolver
    from anysolver.e4_pl_s3_element import (
        FORMULATION_ID,
        QualifiedE4PLS3ShellElement,
    )
    from anysolver.elements import (
        DEFAULT_S3_FORMULATION,
        create_shell_element,
        shell_formulation_diagnostics,
    )

    target = Path(os.environ["ANYSOLVER_S3_V4_TARGET"]).resolve(strict=True)
    assert Path(str(anysolver.__file__)).resolve().is_relative_to(target)
    assert anysolver.__version__ == EXPECTED_DISTRIBUTIONS["ANYsolver"]
    candidates = binding["candidates"]
    for candidate_name, (distribution_name, version, _import_name) in (
        _generator.PACKAGED_IDENTITIES.items()
    ):
        distribution = metadata.distribution(distribution_name)
        assert distribution.version == version
        assert Path(distribution.locate_file("")).resolve().is_relative_to(target)
        _assert_runtime_modules_match_bound_wheel(target, candidates[candidate_name])
    assert DEFAULT_S3_FORMULATION == "e4-pl-s3"
    element = create_shell_element(1, [1, 2, 3], "qualified")
    assert type(element) is QualifiedE4PLS3ShellElement
    assert element.formulation_id == FORMULATION_ID
    diagnostic = shell_formulation_diagnostics(node_count=3)
    assert diagnostic["selected_formulation"] == "e4-pl-s3"
    assert diagnostic["topology_policy"] == "QUALIFIED_E4_PL_S3_DEFAULT"
    assert diagnostic["production_default"] is True
