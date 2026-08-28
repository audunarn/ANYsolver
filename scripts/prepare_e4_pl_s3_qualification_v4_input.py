"""Create a deterministic, non-authorizing S3-v4 candidate binding.

The final candidate graph is intentionally supplied at execution time so
refreshed sibling commits and locally qualified wheels cannot be silently
inherited from protocol v2.  This standard-library program verifies clean Git
identities and live wheel bytes, binds the successor programs, and writes one
exclusive canonical JSON input.  A later reviewed authorization commit must
bind that output before any formal qualification execution.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
from typing import Any, Mapping, Sequence
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BINDING_GENERATOR = Path(__file__).resolve()
CONTRACT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v4_contract.json"
)
COORDINATOR = ROOT / "scripts" / "benchmark_e4_pl_s3_activation_cold_path.py"
FORMAL_RUNNER = ROOT / "scripts" / "run_e4_pl_s3_qualification_v4.py"
PREFLIGHT_RUNNER = ROOT / "scripts" / "run_e4_pl_s3_candidate_preflight_v4.py"
PREFLIGHT_CONFIG = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_pytest_isolation_v4.ini"
)
FINAL_GRAPH = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_qualification_v4_candidate_graph.json"
)
FINAL_BINDING = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_qualification_v4_candidate_binding.json"
)
SUCCESSOR = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v4.py"
)
TEST = ROOT / "tests" / "test_e4_pl_s3_activation_cold_path.py"
FORMAL_TEST = ROOT / "tests" / "test_e4_pl_s3_qualification_optimization_v4.py"
BASE_PROGRAM = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2.py"
)
BASE_INPUT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_default_activation_v2_input.json"
)
BASE_CONTRACT = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_default_activation_v2_contract.json"
)
BASE_TEST = ROOT / "tests" / "test_e4_pl_s3_default_activation_v2.py"
BATCH_BENCHMARK = ROOT / "scripts" / "benchmark_e4_pl_s3_reference_batch.py"
MIXED_STRUCTURAL_COMMON = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_structural_common.py"
)
MIXED_STRUCTURAL_PRODUCER = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_structural_producer.py"
)
MIXED_EIGEN_PERFORMANCE = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_eigen_performance.py"
)
MIXED_MESH_RUNNER = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_mesh_qualification_runner.py"
)
MIXED_MESH_SMOKE_INPUT = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_smoke_input.json"
)
MIXED_MESH_MANIFEST_PROGRAM = (
    ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_manifest.py"
)
OPTIMIZATION_EVIDENCE = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_qualification_optimization_v3_evidence.json"
)
MANIFEST = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
)
SCHEMA = "anysolver.e4-pl-s3-qualification-candidate-binding-v4"
GRAPH_SCHEMA = "anysolver.e4-pl-s3-final-candidate-graph-v4"
PREFLIGHT_SCHEMA = "anysolver.e4-pl-s3-candidate-preflight-v4"
CANDIDATES = (
    "ANY3dView",
    "ANYbuckling",
    "ANYfem",
    "ANYfileIO",
    "ANYgeometry",
    "ANYintelligent",
    "ANYmaterial",
    "ANYmesh",
    "ANYsolver",
    "ANYstructure",
    "ANYtk3D",
)
PACKAGED = frozenset(
    {
        "ANY3dView",
        "ANYbuckling",
        "ANYsolver",
        "ANYmesh",
        "ANYfem",
        "ANYstructure",
        "ANYtk3D",
        "ANYfileIO",
        "ANYmaterial",
        "ANYgeometry",
    }
)
PACKAGED_IDENTITIES = {
    "ANY3dView": ("ANY3dView", "0.5.4", "any3dview"),
    "ANYbuckling": ("ANYbuckling", "0.1.1", "anybuckling"),
    "ANYfem": ("ANYfem", "0.4.0", "anyfem"),
    "ANYfileIO": ("ANYfileio", "0.2.1", "anyfileio"),
    "ANYgeometry": ("ANYgeometry", "0.4.1", "anygeometry"),
    "ANYmaterial": ("ANYmaterial", "0.1.1", "anymaterial"),
    "ANYmesh": ("ANYmesher", "0.3.2", "anymesher"),
    "ANYsolver": ("ANYsolver", "0.4.0", "anysolver"),
    "ANYstructure": ("ANYstructure", "6.3.1", "anystruct"),
    "ANYtk3D": ("ANYtk3D", "0.5.3", "anytk3d"),
}
SOURCE_CANDIDATE_IMPORTS = {
    "ANY3dView": ("any3dview",),
    "ANYintelligent": ("fe_solver",),
    "ANYsolver": ("anysolver",),
}
SOURCE_CANDIDATE_IMPORT_ROOTS = {
    "ANY3dView": "src",
    "ANYbuckling": "tests",
    "ANYintelligent": ".",
    "ANYsolver": "src",
}
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
ANYTK3D_GATE_ROOT_ENVIRONMENT = {
    "ANYTK3D_ANY3DVIEW_ROOT": "ANY3dView",
}
CANDIDATE_GATE_ROOT_ENVIRONMENTS = {
    "ANYstructure": ANYSTRUCTURE_GATE_ROOT_ENVIRONMENT,
    "ANYtk3D": ANYTK3D_GATE_ROOT_ENVIRONMENT,
}
RUNTIME_DISTRIBUTION_IDENTITIES = frozenset(
    {
        "build",
        "charset-normalizer",
        "colorama",
        "contourpy",
        "cycler",
        "fonttools",
        "glcontext",
        "h5py",
        "iniconfig",
        "joblib",
        "kiwisolver",
        "llvmlite",
        "markdown-it-py",
        "matplotlib",
        "mdurl",
        "meshio",
        "moderngl",
        "narwhals",
        "numba",
        "numpy",
        "numpy-stl",
        "packaging",
        "pillow",
        "platformdirs",
        "pluggy",
        "psutil",
        "pygments",
        "pyparsing",
        "pyproject-hooks",
        "pytest",
        "python-dateutil",
        "python-utils",
        "pywin32",
        "reportlab",
        "rich",
        "scikit-learn",
        "scipy",
        "setuptools",
        "shapely",
        "six",
        "threadpoolctl",
        "tkinter-gl",
        "typing-extensions",
        "wheel",
        "xlwings",
    }
)
PROCESS_ENVIRONMENT_NAMES = (
    "COMSPEC",
    "HOME",
    "HOMEDRIVE",
    "HOMEPATH",
    "PATHEXT",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "WINDIR",
)
GIT_BOUND_CONFIG_OVERRIDES = (
    ("core.attributesFile", "NUL" if os.name == "nt" else "/dev/null"),
    ("core.commitGraph", "false"),
    ("core.fsmonitor", "false"),
    ("core.untrackedCache", "false"),
    ("log.showSignature", "false"),
)
_FROZEN_GIT_EXECUTABLE: Path | None = None
_FROZEN_GIT_ENGINE: Path | None = None
INSTALLED_TARGET_SCHEMA = "anysolver.exact-wheel-installed-target-v3"
INSTALLER_GENERATED_NAMES = frozenset(
    {"INSTALLER", "REQUESTED", "direct_url.json"}
)
PREFLIGHT_GATE_IDS = {
    "ANY3dView": ("full-repository-tests",),
    "ANYbuckling": ("full-repository-tests",),
    "ANYfem": (
        "full-supported-test-suite",
        "qualified-s3-policy-and-migration",
    ),
    "ANYfileIO": (
        "full-repository-tests",
        "neutral-shell-formulation-and-owner-normal",
    ),
    "ANYgeometry": ("full-repository-tests",),
    "ANYintelligent": (
        "full-supported-test-suite",
        "production-anysolver-adapter-routing",
    ),
    "ANYmaterial": ("full-repository-tests",),
    "ANYmesh": (
        "full-repository-tests",
        "qualified-s3-admission-repair-and-normals",
    ),
    "ANYsolver": (
        "merge-portable-tests",
        "package-isolation-and-default-routing",
        "q4-mechanics-identity",
    ),
    "ANYstructure": (
        "full-supported-test-suite",
        "runtime-state-v2-formulation-and-normal",
    ),
    "ANYtk3D": ("full-repository-tests",),
}
PREFLIGHT_GATE_NODES = {
    "ANY3dView": {"full-repository-tests": ("tests",)},
    "ANYbuckling": {"full-repository-tests": ("tests",)},
    "ANYfem": {
        "full-supported-test-suite": ("tests",),
        "qualified-s3-policy-and-migration": (
            "tests/test_s3_formulation_policy.py",
            "tests/test_e4_pl_default_routing.py",
            "tests/test_migration.py",
            "tests/test_legacy_geometry_owner_migration.py",
        ),
    },
    "ANYfileIO": {
        "full-repository-tests": ("tests",),
        "neutral-shell-formulation-and-owner-normal": ("tests/test_sesam.py",),
    },
    "ANYgeometry": {"full-repository-tests": ("tests",)},
    "ANYintelligent": {
        "full-supported-test-suite": (".",),
        "production-anysolver-adapter-routing": (
            "tests/test_external_anysolver_adapter.py",
        ),
    },
    "ANYmaterial": {"full-repository-tests": ("tests",)},
    "ANYmesh": {
        "full-repository-tests": ("tests",),
        "qualified-s3-admission-repair-and-normals": (
            "tests/test_s3_production.py",
            "tests/test_s3_quality.py",
            "tests/test_s3_repair.py",
            "tests/test_geometry_owner_integration.py",
        ),
    },
    "ANYsolver": {
        "merge-portable-tests": (),
        "package-isolation-and-default-routing": (
            "tests/test_s3_default_activation.py",
            "tests/test_e4_pl_s3_cross_wheel_v4.py",
            "tests/test_e4_pl_s3_exact_wheel_target_v3.py",
            "tests/test_extracted_package_wiring.py",
        ),
        "q4-mechanics-identity": (
            "tests/test_e4_pl_default_activation.py",
            "tests/test_e4_pl_q4_current_tangent.py",
            "tests/test_qualified_q4_assembly_authority.py",
            "tests/test_qualified_q4_cold_fallback.py",
        ),
    },
    "ANYstructure": {
        "full-supported-test-suite": (".",),
        "runtime-state-v2-formulation-and-normal": (
            "tests/test_s3_runtime_state_v2.py",
            "tests/test_fem_import_routing.py",
            "tests/test_sesam_fem_document_backend.py",
        ),
    },
    "ANYtk3D": {"full-repository-tests": ("tests",)},
}
PREFLIGHT_ENVIRONMENT = {
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
}
PREFLIGHT_TREE_RELEASE_ENVIRONMENT = "ANYSOLVER_S3_PREFLIGHT_TREE_RELEASE"
PREFLIGHT_TREE_RELEASE_BYTES = b"ANYSOLVER_S3_PREFLIGHT_TREE_ACCOUNTED_V1\n"
PREFLIGHT_TREE_RELEASE_WAIT_SECONDS = 5.0
PREFLIGHT_CANDIDATE_GIT_MODULES = frozenset(
    {
        "tests/test_e4_pl_s3_qualification_optimization_v3.py",
        "tests/test_e4_pl_s3_qualification_optimization_v4.py",
    }
)
PREFLIGHT_TREE_RELEASE_BOOTSTRAP = (
    "import os,pathlib,time\n"
    f"release=pathlib.Path(os.environ[{PREFLIGHT_TREE_RELEASE_ENVIRONMENT!r}])\n"
    f"deadline=time.monotonic()+{PREFLIGHT_TREE_RELEASE_WAIT_SECONDS!r}\n"
    "while not release.is_file():\n"
    "    if time.monotonic()>=deadline: raise RuntimeError('process-tree accounting was not released')\n"
    "    time.sleep(.01)\n"
    f"if release.read_bytes()!={PREFLIGHT_TREE_RELEASE_BYTES!r}: raise RuntimeError('process-tree accounting release differs')\n"
)
PREFLIGHT_BOOTSTRAP = PREFLIGHT_TREE_RELEASE_BOOTSTRAP + (
    "import importlib,json,pathlib,sys;"
    "target=pathlib.Path(sys.argv[1]).resolve(strict=True);"
    "root=pathlib.Path(sys.argv[2]).resolve(strict=True);"
    "config=pathlib.Path(sys.argv[3]).resolve(strict=True);"
    "basetemp=pathlib.Path(sys.argv[4]).resolve();"
    "imports=json.loads(sys.argv[5]);"
    "assert set(imports)=={'candidate_imports','candidate_sys_path','target_imports'};"
    "candidate_imports=imports['candidate_imports'];target_imports=imports['target_imports'];"
    "candidate_sys_path=(root/imports['candidate_sys_path']).resolve(strict=True);"
    "test_support=(root/'tests').resolve(strict=True);"
    "assert candidate_sys_path.is_relative_to(root);"
    "assert test_support.is_relative_to(root) and test_support.is_dir();"
    "assert isinstance(candidate_imports,list) and isinstance(target_imports,list);"
    "assert all(isinstance(name,str) and name for name in candidate_imports+target_imports);"
    "assert 'sitecustomize' not in sys.modules and 'usercustomize' not in sys.modules;"
    "sys.path[:0]=list(dict.fromkeys([str(candidate_sys_path),str(test_support),str(target),str(root)]));"
    "import pytest;"
    "assert pathlib.Path(pytest.__file__).resolve(strict=True).is_relative_to(target);"
    "target_mods=[importlib.import_module(name) for name in target_imports];"
    "candidate_mods=[importlib.import_module(name) for name in candidate_imports];"
    "assert all(pathlib.Path(mod.__file__).resolve(strict=True).is_relative_to(target) for mod in target_mods);"
    "assert all(pathlib.Path(mod.__file__).resolve(strict=True).is_relative_to(candidate_sys_path) for mod in candidate_mods);"
    "raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','-c',str(config),"
    "'--rootdir',str(root),'--confcutdir',str(root),'--import-mode=importlib',"
    "'--basetemp',str(basetemp),*sys.argv[6:]]))"
)
PREFLIGHT_PORTABLE_BOOTSTRAP = PREFLIGHT_TREE_RELEASE_BOOTSTRAP + (
    "import importlib.util,json,pathlib,sys;"
    "target=pathlib.Path(sys.argv[1]).resolve(strict=True);"
    "root=pathlib.Path(sys.argv[2]).resolve(strict=True);"
    "config=pathlib.Path(sys.argv[3]).resolve(strict=True);"
    "runroot=pathlib.Path(sys.argv[4]).resolve();"
    "imports=sys.argv[5];"
    "source=(root/'scripts'/'run_portable_ci.py').resolve(strict=True);"
    "spec=importlib.util.spec_from_file_location('_s3_v4_portable',source);"
    "assert spec is not None and spec.loader is not None;"
    "mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);"
    "bootstrap=sys.argv[6];"
    f"excluded={sorted(PREFLIGHT_CANDIDATE_GIT_MODULES)!r};"
    "mod._worker_command=lambda modules,worker:[sys.executable,'-I','-S','-B','-c',bootstrap,str(target),str(root),str(config),str((worker/'basetemp').resolve()),imports,*[f'--deselect={node}' for node in mod.DEDICATED_LANE_NODES if node.partition('::')[0] in set(modules)],*[module for module in modules if module not in excluded]];"
    "raise SystemExit(mod.run(workers=3,timeout_seconds=None))"
)
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9A-F]{64}")
Q4_BASE_IDENTITY = {
    "commit": "62464bea649229aa2c9f89ba7cbe431bf6a9282a",
    "parent": "19d7726ad09a4969c187af1816bab08596db7590",
    "subject": "docs: record bounded S3 activation forecast",
    "tree": "c5cc24fa60a3ce1cdc3a1910bd45fe0efe7ec620",
}
Q4_GUARD_SOURCE_IDENTITY = {
    "commit": "04ec1d5cbb5725913aec35ec62ba1de754881360",
    "parent": Q4_BASE_IDENTITY["commit"],
    "subject": "fix: bind Q4 vector state sealing to producer origin",
    "tree": "310f9cc18b3dd0fe439a96f8adcc0e36bafe94fb",
}
Q4_GUARD_IMPORT_IDENTITY = {
    "commit": "eeec9ebd430c65d0af5ac29f0f4ba0c1fe5ddbbc",
    "parent": "084f6da03d573ea0dedd46c0ecb45ebd487fad08",
    "subject": Q4_GUARD_SOURCE_IDENTITY["subject"],
    "tree": "60a01afc1cfe7521bb62c4a928632e4d7f4f2555",
}
Q4_GUARD_V2_PATH_BLOBS = (
    (
        "docs/reference_cases/e4_pl_q4_state_seal_guard_v2_incident.md",
        "dbb69ff168d2ed938eec87f3d86143aa3c0ec92d",
    ),
    (
        "src/anysolver/e4_pl_element.py",
        "031da1cde23e7983c0f94d837f5610a24737920b",
    ),
    (
        "src/anysolver/nonlinear_performance.py",
        "80e7bc75c897aa83617ae1d35b47631b894d5481",
    ),
    (
        "src/anysolver/nonlinear_state.py",
        "9b578d2d8ed55c3ab8e14f11c24737361d2a785e",
    ),
    (
        "src/anysolver/nonlinear_static.py",
        "645fcee0d5dd6ccf7ca89ea80870b2b0e22ba974",
    ),
    (
        "tests/test_e4_pl_q4_current_tangent.py",
        "ac4a695088aeb79dc6392163446f6acb2f662247",
    ),
)
Q4_GUARD_SOURCE_PATHS = (
    "src/anysolver/e4_pl_element.py",
    "src/anysolver/nonlinear_performance.py",
    "src/anysolver/nonlinear_state.py",
    "src/anysolver/nonlinear_static.py",
)
Q4_NONMECHANICS_INTEGRATION_PATH_BLOBS = (
    (
        "src/anysolver/anystructure_fem_mode.py",
        "9bcbacb9ac6a71fdb2f9c8c8349d50aadb16946d",
    ),
    (
        "src/anysolver/production_readiness.py",
        "b0562fdfa3d26a7c7bfd2a48c5fb70d0e95a8b4a",
    ),
    (
        "src/anysolver/runtime.py",
        "4f141a70a5c19aa5ee35869a02e88d21e9e370c3",
    ),
)
Q4_GUARD_SUCCESSOR_IDENTITY = {
    "commit": "bf9fa2c676507c2c86343c391c73f69319cb4525",
    "parent": "005d8a6ba32a0ed8888416d9c489b16d2540399b",
    "subject": "fix: replay accepted Q4 vector layer kinematics",
    "tree": "ce7f37f13337bb716d0957fdffe15cd26a4005e2",
}
Q4_GUARD_SUCCESSOR_PATH_BLOBS = (
    (
        "docs/reference_cases/e4_pl_q4_vector_layer_replay_guard_incident.md",
        "3579cc4b25736bf8643bebc33f1341d676c75c98",
    ),
    (
        "src/anysolver/e4_pl_element.py",
        "d8c42c4a3f6ebe10c2c7d4a96404b7bc9baa8129",
    ),
    (
        "tests/test_e4_pl_q4_current_tangent.py",
        "b91e47e11d3daa6357c5df6c4ef478a2f5c33431",
    ),
)
Q4_GUARD_PATH_BLOBS = (
    Q4_GUARD_V2_PATH_BLOBS[0],
    Q4_GUARD_SUCCESSOR_PATH_BLOBS[0],
    Q4_GUARD_SUCCESSOR_PATH_BLOBS[1],
    *Q4_GUARD_V2_PATH_BLOBS[2:5],
    Q4_GUARD_SUCCESSOR_PATH_BLOBS[2],
)
Q4_NONMECHANICS_INTEGRATION_PATHS = tuple(
    path for path, _blob_id in Q4_NONMECHANICS_INTEGRATION_PATH_BLOBS
)
Q4_FROZEN_SOURCE_EXCLUSIONS = tuple(
    sorted((*Q4_GUARD_SOURCE_PATHS, *Q4_NONMECHANICS_INTEGRATION_PATHS))
)
Q4_FROZEN_SOURCE_FILE_COUNT = 103
Q4_FROZEN_SOURCE_ROWS_SHA256 = (
    "6C3489D4814C28CDFCA47EE881CFA3CB38349C6774464EF366A8D8836B334560"
)


class BindingError(ValueError):
    """The supplied candidate graph cannot be bound safely."""


def _canonical_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _safe_archive_path(value: str, *, label: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(":" in part for part in path.parts)
        or any(ord(character) < 32 for character in value)
    ):
        raise BindingError(f"unsafe {label} path: {value!r}")
    return path.as_posix()


def _is_reparse(path: Path) -> bool:
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _regular_file_bytes(path: Path, *, label: str) -> bytes:
    if path.is_symlink() or _is_reparse(path) or not path.is_file():
        raise BindingError(f"{label} is not a non-reparse regular file")
    return path.read_bytes()


def _canonical_regular_file_route(value: object, *, label: str) -> Path:
    if type(value) is not str or not value:
        raise BindingError(f"{label} path is malformed")
    declared = Path(value)
    if not declared.is_absolute():
        raise BindingError(f"{label} path is not absolute")
    try:
        for route in (declared, *declared.parents):
            if route.is_symlink() or _is_reparse(route):
                raise BindingError(f"{label} route contains a reparse point")
        resolved = declared.resolve(strict=True)
    except OSError as exc:
        raise BindingError(f"{label} route cannot be resolved") from exc
    _regular_file_bytes(resolved, label=label)
    return resolved


def _tool_record(path: Path, *, label: str) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_absolute():
        raise BindingError(f"{label} path is not absolute")
    raw = _regular_file_bytes(resolved, label=label)
    return {
        "bytes": len(raw),
        "path": str(resolved),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }


def _apply_bound_git_controls(environment: dict[str, str]) -> None:
    """Install the complete fail-closed Git process control surface."""

    for name in tuple(environment):
        if (
            name in {"GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"}
            or name.startswith("GIT_CONFIG_KEY_")
            or name.startswith("GIT_CONFIG_VALUE_")
        ):
            del environment[name]
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_REPLACE_REF_BASE": "refs/disabled-replacements/",
            "GIT_CONFIG_COUNT": str(len(GIT_BOUND_CONFIG_OVERRIDES)),
        }
    )
    for index, (key, value) in enumerate(GIT_BOUND_CONFIG_OVERRIDES):
        environment[f"GIT_CONFIG_KEY_{index}"] = key
        environment[f"GIT_CONFIG_VALUE_{index}"] = value


def _closed_process_environment(launcher: Path, engine: Path) -> dict[str, str]:
    """Return the only inherited OS values exposed to scientific children."""

    result = {
        name: os.environ[name]
        for name in PROCESS_ENVIRONMENT_NAMES
        if name in os.environ and os.environ[name]
    }
    path_entries = [engine.parent, Path(sys.executable).resolve(strict=True).parent]
    system_root = result.get("SYSTEMROOT") or result.get("WINDIR")
    if system_root:
        system32 = Path(system_root) / "System32"
        if system32 not in path_entries:
            path_entries.append(system32)
    result["PATH"] = os.pathsep.join(str(path) for path in path_entries)
    _apply_bound_git_controls(result)
    return dict(sorted(result.items()))


def _git_environment(
    process_environment: Mapping[str, str], executable: Path
) -> dict[str, str]:
    result = dict(process_environment)
    path_entries = [executable.parent]
    system_root = result.get("SYSTEMROOT") or result.get("WINDIR")
    if system_root:
        path_entries.append(Path(system_root) / "System32")
    result["PATH"] = os.pathsep.join(str(path) for path in path_entries)
    _apply_bound_git_controls(result)
    return result


def _git_probe(
    launcher: Path,
    arguments: Sequence[str],
    process_environment: Mapping[str, str],
) -> bytes:
    completed = subprocess.run(
        [str(launcher), *arguments],
        check=False,
        capture_output=True,
        cwd=launcher.parent,
        env=_git_environment(process_environment, launcher),
    )
    if completed.returncode != 0 or completed.stderr:
        raise BindingError("Git runtime identity probe failed")
    return completed.stdout


def _git_engine_from_exec_path(launcher: Path, exec_path_raw: bytes) -> Path:
    try:
        exec_path = Path(exec_path_raw.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise BindingError("Git exec-path identity is malformed") from exc
    if os.name != "nt":
        return launcher
    candidates = []
    if len(exec_path.parents) >= 2:
        candidates.append(exec_path.parents[1] / "bin" / "git.exe")
    candidates.append(launcher)
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file() and not resolved.is_symlink() and not _is_reparse(resolved):
            return resolved
    raise BindingError("Git native engine is unavailable")


def _git_loadable_surface(launcher: Path, engine: Path) -> dict[str, Any]:
    """Hash every non-OS file reachable from the Git application dirs."""

    loadable_roots = sorted(
        {launcher.parent.resolve(strict=True), engine.parent.resolve(strict=True)},
        key=lambda path: str(path).casefold(),
    )
    loadable_rows: list[dict[str, Any]] = []
    loadable_directories: list[str] = []
    for index, root in enumerate(loadable_roots):
        if root.is_symlink() or _is_reparse(root) or not root.is_dir():
            raise BindingError("Git loadable runtime root is linked")
        prefix = f"root-{index}"
        for directory, directory_names, filenames in os.walk(root, followlinks=False):
            base_directory = Path(directory)
            directory_names.sort(key=str.casefold)
            filenames.sort(key=str.casefold)
            for name in directory_names:
                child = base_directory / name
                if child.is_symlink() or _is_reparse(child) or not child.is_dir():
                    raise BindingError("Git loadable runtime contains a linked directory")
                loadable_directories.append(
                    f"{prefix}/{child.relative_to(root).as_posix()}"
                )
            for name in filenames:
                child = base_directory / name
                loadable_rows.append(
                    _sha256_row(
                        f"{prefix}/{child.relative_to(root).as_posix()}",
                        _regular_file_bytes(child, label="Git loadable runtime file"),
                    )
                )
    loadable_rows.sort(key=lambda row: str(row["path"]).casefold())
    loadable_directories.sort(key=str.casefold)
    loadable_names = [str(row["path"]) for row in loadable_rows]
    if len({name.casefold() for name in loadable_names + loadable_directories}) != (
        len(loadable_names) + len(loadable_directories)
    ):
        raise BindingError("Git loadable runtime contains a case-fold collision")
    return {
        "directories_sha256": hashlib.sha256(
            canonical_bytes(loadable_directories)
        ).hexdigest().upper(),
        "directory_count": len(loadable_directories),
        "file_count": len(loadable_rows),
        "roots": [str(path) for path in loadable_roots],
        "rows_sha256": hashlib.sha256(
            canonical_bytes(loadable_rows)
        ).hexdigest().upper(),
    }


def _git_runtime_binding() -> tuple[dict[str, Any], dict[str, str]]:
    discovered = (
        str(_FROZEN_GIT_EXECUTABLE)
        if _FROZEN_GIT_EXECUTABLE is not None
        else shutil.which("git")
    )
    if discovered is None:
        raise BindingError("Git launcher is unavailable")
    launcher = Path(discovered).resolve(strict=True)
    if _FROZEN_GIT_ENGINE is None:
        provisional_environment = _closed_process_environment(launcher, launcher)
        provisional_exec_path = _git_probe(
            launcher, ("--exec-path",), provisional_environment
        )
        engine = _git_engine_from_exec_path(launcher, provisional_exec_path)
    else:
        engine = _FROZEN_GIT_ENGINE.resolve(strict=True)
    process_environment = _closed_process_environment(launcher, engine)
    loadable_surface = _git_loadable_surface(launcher, engine)
    exec_path_raw = _git_probe(engine, ("--exec-path",), process_environment)
    build_raw = _git_probe(
        engine,
        ("--version", "--build-options"),
        process_environment,
    )
    builtins_raw = _git_probe(
        engine,
        ("--list-cmds=builtins",),
        process_environment,
    )
    if not {
        "config",
        "diff",
        "fsck",
        "hash-object",
        "ls-files",
        "ls-tree",
        "merge-base",
        "rev-parse",
        "show",
        "status",
    } <= set(builtins_raw.decode("utf-8").splitlines()):
        raise BindingError("Git runtime lacks a required built-in command")
    return (
        {
            "build_options": _sha256_row("stdout", build_raw),
            "builtin_commands": _sha256_row("stdout", builtins_raw),
            "engine": _tool_record(engine, label="Git native engine"),
            "exec_path": exec_path_raw.decode("utf-8").strip().replace("\\", "/"),
            "exec_path_output": _sha256_row("stdout", exec_path_raw),
            "launcher": _tool_record(launcher, label="Git launcher"),
            "loadable_surface": loadable_surface,
        },
        process_environment,
    )


def _activate_bound_runtime_environment(runtime: object) -> Path:
    """Verify the bound Git/runtime launch surface before any Git authority use."""

    global _FROZEN_GIT_ENGINE, _FROZEN_GIT_EXECUTABLE
    if not isinstance(runtime, dict) or set(runtime) != {
        "closed_target",
        "distributions",
        "git",
        "process_environment",
        "python",
        "schema",
        "target",
    }:
        raise BindingError("isolated runtime environment fields differ")
    if runtime["schema"] != "anysolver.e4-pl-s3-isolated-runtime-environment-v2":
        raise BindingError("isolated runtime environment schema differs")
    git = runtime["git"]
    if not isinstance(git, dict) or set(git) != {
        "build_options",
        "builtin_commands",
        "engine",
        "exec_path",
        "exec_path_output",
        "launcher",
        "loadable_surface",
    }:
        raise BindingError("Git runtime binding fields differ")
    launcher_row = git["launcher"]
    engine_row = git["engine"]
    for row, label in ((launcher_row, "Git launcher"), (engine_row, "Git engine")):
        if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
            raise BindingError(f"{label} binding fields differ")
        if _tool_record(Path(str(row["path"])), label=label) != row:
            raise BindingError(f"{label} identity differs")
    launcher = Path(str(launcher_row["path"]))
    engine = Path(str(engine_row["path"]))
    process_environment = runtime["process_environment"]
    if (
        not isinstance(process_environment, dict)
        or process_environment != _closed_process_environment(launcher, engine)
        or not all(type(key) is str and type(value) is str for key, value in process_environment.items())
    ):
        raise BindingError("closed process environment differs")
    selected_git = shutil.which("git", path=process_environment["PATH"])
    if selected_git is None or Path(selected_git).resolve(strict=True) != engine:
        raise BindingError("closed process PATH does not select the bound Git engine")
    if _git_loadable_surface(launcher, engine) != git["loadable_surface"]:
        raise BindingError("Git loadable runtime surface differs")
    exec_raw = _git_probe(engine, ("--exec-path",), process_environment)
    build_raw = _git_probe(
        engine,
        ("--version", "--build-options"),
        process_environment,
    )
    builtins_raw = _git_probe(
        engine,
        ("--list-cmds=builtins",),
        process_environment,
    )
    if (
        git["exec_path_output"] != _sha256_row("stdout", exec_raw)
        or git["build_options"] != _sha256_row("stdout", build_raw)
        or git["builtin_commands"] != _sha256_row("stdout", builtins_raw)
        or git["exec_path"] != exec_raw.decode("utf-8").strip().replace("\\", "/")
        or _git_engine_from_exec_path(launcher, exec_raw) != engine
    ):
        raise BindingError("Git runtime identity differs")
    _FROZEN_GIT_EXECUTABLE = launcher
    _FROZEN_GIT_ENGINE = engine
    return launcher


def _python_runtime_binding(
    process_environment: Mapping[str, str],
) -> dict[str, Any]:
    """Bind every base-prefix code surface visible to isolated Python."""

    executable = Path(sys.executable).resolve(strict=True)
    executable_raw = _regular_file_bytes(executable, label="runtime Python executable")
    base = Path(sys.base_prefix).resolve(strict=True)
    stdlib = Path(sysconfig.get_path("stdlib")).resolve(strict=True)
    if not stdlib.is_relative_to(base):
        raise BindingError("Python stdlib is outside the base runtime")
    if base.is_symlink() or _is_reparse(base) or not base.is_dir():
        raise BindingError("Python base runtime is linked or not a directory")
    code_suffixes = {".py", ".pyc", ".pyd", ".pyw"}
    complete_extra_roots: set[str] = set()
    for child in sorted(base.iterdir(), key=lambda path: path.name.casefold()):
        if not child.is_dir() or child.name in {"DLLs", "Lib"}:
            continue
        for _directory, _directory_names, filenames in os.walk(
            child, followlinks=False
        ):
            if any(Path(name).suffix.casefold() in code_suffixes for name in filenames):
                complete_extra_roots.add(child.name)
                break
    rows: list[dict[str, Any]] = []
    directories: list[str] = []
    for directory, directory_names, filenames in os.walk(base, followlinks=False):
        base_directory = Path(directory)
        relative_directory = base_directory.relative_to(base)
        parts = relative_directory.parts
        if parts == ("Lib",):
            directory_names[:] = [
                name
                for name in directory_names
                if name not in {"site-packages", "dist-packages"}
            ]
        directory_names.sort(key=str.casefold)
        filenames.sort(key=str.casefold)
        for name in directory_names:
            child = base_directory / name
            if child.is_symlink() or _is_reparse(child) or not child.is_dir():
                raise BindingError("Python runtime contains a linked directory")
            directories.append(child.relative_to(base).as_posix())
        for name in filenames:
            child = base_directory / name
            first = parts[0] if parts else ""
            include = (
                not parts
                or first in {"DLLs", "Lib"}
                or first in complete_extra_roots
                or child.suffix.casefold() in code_suffixes
            )
            if not include:
                continue
            rows.append(
                _sha256_row(
                    child.relative_to(base).as_posix(),
                    _regular_file_bytes(child, label="Python runtime file"),
                )
            )
    rows.sort(key=lambda row: str(row["path"]))
    directories.sort()
    if len({str(row["path"]).casefold() for row in rows}) != len(rows):
        raise BindingError("Python runtime contains a case-fold collision")
    probe_code = (
        "import json,sys,sysconfig;"
        "print(json.dumps({'base_prefix':sys.base_prefix,'cache_tag':sys.implementation.cache_tag,"
        "'executable':sys.executable,'path':sys.path,'prefix':sys.prefix,"
        "'stdlib':sysconfig.get_path('stdlib'),'version':sys.version},"
        "allow_nan=False,ensure_ascii=True,separators=(',',':'),sort_keys=True))"
    )
    completed = subprocess.run(
        [str(executable), "-I", "-S", "-B", "-c", probe_code],
        check=False,
        capture_output=True,
        env=dict(process_environment),
    )
    if completed.returncode != 0 or completed.stderr or not completed.stdout:
        raise BindingError("isolated Python runtime probe failed")
    return {
        "base_prefix": str(base),
        "bytes": len(executable_raw),
        "cache_tag": str(sys.implementation.cache_tag),
        "directory_count": len(directories),
        "directories_sha256": hashlib.sha256(
            canonical_bytes(directories)
        ).hexdigest().upper(),
        "file_count": len(rows),
        "isolated_probe": _sha256_row("stdout", completed.stdout),
        "path": str(executable),
        "runtime_surface": (
            "EXECUTABLE_DLL_STDLIB_AND_BASE_ROOT_IMPORT_SURFACE"
        ),
        "rows_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest().upper(),
        "sha256": hashlib.sha256(executable_raw).hexdigest().upper(),
        "stdlib": str(stdlib),
        "version": sys.version,
    }


def _sha256_row(path: str, raw: bytes) -> dict[str, Any]:
    return {
        "bytes": len(raw),
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }


def _target_inventory(target: Path) -> list[dict[str, Any]]:
    target = target.resolve(strict=True)
    if target.is_symlink() or _is_reparse(target) or not target.is_dir():
        raise BindingError("isolated execution target is not a regular directory")
    rows: list[dict[str, Any]] = []
    seen_casefold: set[str] = set()
    for directory, directory_names, filenames in os.walk(target, followlinks=False):
        directory_names.sort()
        filenames.sort()
        base = Path(directory)
        for name in directory_names:
            child = base / name
            if child.is_symlink() or _is_reparse(child) or not child.is_dir():
                raise BindingError("installed target contains a linked directory")
        for name in filenames:
            child = base / name
            raw = _regular_file_bytes(child, label="installed target entry")
            relative = child.relative_to(target).as_posix()
            _safe_archive_path(relative, label="installed target")
            folded = relative.casefold()
            if folded in seen_casefold:
                raise BindingError("installed target contains a case-fold collision")
            seen_casefold.add(folded)
            basename = PurePosixPath(relative).name.casefold()
            if basename in {"sitecustomize.py", "usercustomize.py"} or (
                basename.endswith(".pyc")
                and (
                    basename.startswith("sitecustomize.")
                    or basename.startswith("usercustomize.")
                )
            ):
                raise BindingError("installed target contains a forbidden customization module")
            rows.append(_sha256_row(relative, raw))
    return rows


def _reject_source_candidate_target_shadowing(
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Forbid the isolated target from resolving a source-only candidate import."""

    for row in rows:
        path = str(row.get("path", ""))
        folded_path = path.casefold()
        for candidate_name, names in SOURCE_CANDIDATE_IMPORTS.items():
            if candidate_name in PACKAGED:
                continue
            for import_name in names:
                import_path = import_name.replace(".", "/").casefold()
                if folded_path.startswith(import_path + "/") or (
                    "/" not in folded_path
                    and folded_path.startswith(import_path + ".")
                ):
                    raise BindingError(
                        f"isolated runtime target shadows source candidate import {import_name}"
                    )


def _target_directory_inventory(target: Path) -> list[str]:
    """Return every installed-target directory below the bound root."""

    target = target.resolve(strict=True)
    if target.is_symlink() or _is_reparse(target) or not target.is_dir():
        raise BindingError("isolated execution target is not a regular directory")
    rows: list[str] = []
    seen_casefold: set[str] = set()
    for directory, directory_names, _filenames in os.walk(target, followlinks=False):
        directory_names.sort()
        base = Path(directory)
        for name in directory_names:
            child = base / name
            if child.is_symlink() or _is_reparse(child) or not child.is_dir():
                raise BindingError("installed target contains a linked directory")
            relative = child.relative_to(target).as_posix()
            _safe_archive_path(relative, label="installed target directory")
            folded = relative.casefold()
            if folded in seen_casefold:
                raise BindingError("installed target contains a directory case-fold collision")
            seen_casefold.add(folded)
            rows.append(relative)
    return sorted(rows)


def _implied_target_directories(paths: Sequence[str]) -> set[str]:
    implied: set[str] = set()
    for value in paths:
        for parent in PurePosixPath(value).parents:
            if parent != PurePosixPath("."):
                implied.add(parent.as_posix())
    return implied


def _record_digest(raw: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode(
        "ascii"
    )


def _read_record(raw: bytes, *, label: str) -> dict[str, tuple[str, str]]:
    try:
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise BindingError(f"{label} is not valid UTF-8 CSV") from exc
    result: dict[str, tuple[str, str]] = {}
    seen_casefold: set[str] = set()
    for row in rows:
        if len(row) != 3:
            raise BindingError(f"{label} row width differs")
        path = _safe_archive_path(row[0], label=label)
        folded = path.casefold()
        if path in result or folded in seen_casefold:
            raise BindingError(f"{label} contains duplicate paths")
        seen_casefold.add(folded)
        result[path] = (row[1], row[2])
    if not result:
        raise BindingError(f"{label} is empty")
    return result


def _installed_member_path(value: str) -> str:
    parts = PurePosixPath(value).parts
    if len(parts) >= 3 and parts[0].endswith(".data"):
        if parts[1] not in {"purelib", "platlib"}:
            raise BindingError("wheel uses an unsupported .data installation scheme")
        return _safe_archive_path(
            PurePosixPath(*parts[2:]).as_posix(), label="installed wheel"
        )
    return _safe_archive_path(value, label="installed wheel")


def _metadata_identity(raw: bytes, *, label: str) -> tuple[str, str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BindingError(f"{label} METADATA is not UTF-8") from exc
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if not line:
            break
        key, separator, value = line.partition(":")
        if separator and key in {"Name", "Version"}:
            if key in fields:
                raise BindingError(f"{label} METADATA duplicates {key}")
            fields[key] = value.strip()
    if set(fields) != {"Name", "Version"}:
        raise BindingError(f"{label} METADATA identity is incomplete")
    return fields["Name"], fields["Version"]


def _wheel_blueprint(name: str, wheel: Mapping[str, Any]) -> dict[str, Any]:
    expected_distribution, expected_version, import_name = PACKAGED_IDENTITIES[name]
    wheel_path = _canonical_regular_file_route(
        wheel["path"], label=f"{name} wheel"
    )
    raw = _regular_file_bytes(wheel_path, label=f"{name} wheel")
    if (
        wheel_path.name != wheel["filename"]
        or type(wheel["bytes"]) is not int
        or wheel["bytes"] != len(raw)
        or not raw
        or type(wheel["sha256"]) is not str
        or HEX64.fullmatch(wheel["sha256"]) is None
        or hashlib.sha256(raw).hexdigest().upper() != wheel["sha256"]
    ):
        raise BindingError(f"{name} wheel bytes differ")
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
        bad = archive.testzip()
    except (OSError, zipfile.BadZipFile) as exc:
        raise BindingError(f"{name} wheel archive is malformed") from exc
    if bad is not None:
        raise BindingError(f"{name} wheel CRC differs: {bad}")
    members: dict[str, bytes] = {}
    seen_casefold: set[str] = set()
    for info in archive.infolist():
        archive_path = _safe_archive_path(info.filename.rstrip("/"), label="wheel")
        if info.is_dir():
            continue
        mode = (info.external_attr >> 16) & 0xFFFF
        kind = stat.S_IFMT(mode)
        if kind not in {0, stat.S_IFREG} or stat.S_ISLNK(mode):
            raise BindingError(f"{name} wheel contains a non-regular member")
        folded = archive_path.casefold()
        if archive_path in members or folded in seen_casefold:
            raise BindingError(f"{name} wheel contains duplicate paths")
        seen_casefold.add(folded)
        members[archive_path] = archive.read(info)
    record_paths = [path for path in members if path.endswith(".dist-info/RECORD")]
    metadata_paths = [path for path in members if path.endswith(".dist-info/METADATA")]
    if len(record_paths) != 1 or len(metadata_paths) != 1:
        raise BindingError(f"{name} wheel metadata membership differs")
    record_path = record_paths[0]
    dist_info = record_path.rsplit("/", 1)[0]
    if not metadata_paths[0].startswith(dist_info + "/"):
        raise BindingError(f"{name} wheel dist-info roots differ")
    distribution, version = _metadata_identity(members[metadata_paths[0]], label=name)
    if (
        _canonical_distribution_name(distribution)
        != _canonical_distribution_name(expected_distribution)
        or version != expected_version
    ):
        raise BindingError(f"{name} wheel distribution identity differs")
    record = _read_record(members[record_path], label=f"{name} wheel RECORD")
    if set(record) != set(members):
        raise BindingError(f"{name} wheel RECORD membership differs")
    installed: dict[str, dict[str, Any]] = {}
    for archive_path, member_raw in members.items():
        digest, size = record[archive_path]
        if archive_path == record_path:
            if digest or size:
                raise BindingError(f"{name} wheel RECORD self-row differs")
        elif digest != f"sha256={_record_digest(member_raw)}" or size != str(
            len(member_raw)
        ):
            raise BindingError(f"{name} wheel RECORD hash or size differs")
        installed_path = _installed_member_path(archive_path)
        if installed_path in installed:
            raise BindingError(f"{name} wheel installation paths collide")
        installed[installed_path] = {
            **_sha256_row(installed_path, member_raw),
            "archive_path": archive_path,
        }
    if not any(
        path == f"{import_name}.py" or path.startswith(f"{import_name}/")
        for path in installed
    ):
        raise BindingError(f"{name} wheel does not contain its runtime import root")
    installed_record_path = _installed_member_path(record_path)
    return {
        "dist_info": _installed_member_path(dist_info),
        "distribution": expected_distribution,
        "files": installed,
        "import_name": import_name,
        "record": {
            "archive_path": record_path,
            "bytes": len(members[record_path]),
            "row_count": len(record),
            "sha256": hashlib.sha256(members[record_path]).hexdigest().upper(),
            "target_path": installed_record_path,
        },
        "version": expected_version,
    }


def _installed_wheel_manifest(
    name: str,
    wheel: Mapping[str, Any],
    target: Path,
    closed_target: Mapping[str, Any],
) -> dict[str, Any]:
    blueprint = _wheel_blueprint(name, wheel)
    target_record_path = target / Path(blueprint["record"]["target_path"])
    target_record_raw = _regular_file_bytes(
        target_record_path, label=f"{name} installed RECORD"
    )
    target_record = _read_record(target_record_raw, label=f"{name} installed RECORD")
    expected_paths = set(blueprint["files"])
    record_path = str(blueprint["record"]["target_path"])
    allowed_generated = {
        f"{blueprint['dist_info']}/{generated}"
        for generated in INSTALLER_GENERATED_NAMES
    }
    generated_paths = set(target_record) - expected_paths
    if not generated_paths <= allowed_generated:
        raise BindingError(f"{name} installed RECORD claims an unregistered file")
    if set(target_record) != expected_paths | generated_paths:
        raise BindingError(f"{name} installed RECORD membership differs")
    rows: list[dict[str, Any]] = []
    for path in sorted(target_record):
        digest, size = target_record[path]
        installed_path = target / Path(path)
        installed_raw = _regular_file_bytes(
            installed_path, label=f"{name} installed file"
        )
        if path == record_path:
            if digest or size:
                raise BindingError(f"{name} installed RECORD self-row differs")
            provenance = "TARGET_RECORD"
        else:
            if digest != f"sha256={_record_digest(installed_raw)}" or size != str(
                len(installed_raw)
            ):
                raise BindingError(f"{name} installed RECORD hash or size differs")
            if path in blueprint["files"]:
                expected = blueprint["files"][path]
                if (
                    len(installed_raw) != expected["bytes"]
                    or hashlib.sha256(installed_raw).hexdigest().upper()
                    != expected["sha256"]
                ):
                    raise BindingError(f"{name} installed file differs from exact wheel")
                provenance = "WHEEL_RECORD"
            else:
                provenance = "INSTALLER_GENERATED"
        rows.append({**_sha256_row(path, installed_raw), "provenance": provenance})
    return {
        "closed_target": dict(closed_target),
        "distribution": blueprint["distribution"],
        "files": rows,
        "files_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest().upper(),
        "import_name": blueprint["import_name"],
        "record": blueprint["record"],
        "schema": INSTALLED_TARGET_SCHEMA,
        "target": str(target),
        "version": blueprint["version"],
        "wheel_sha256": wheel["sha256"],
    }


def _build_installed_target_manifests(
    target: Path,
    candidates: Mapping[str, Mapping[str, Any]],
    *,
    allow_unregistered: bool = False,
) -> dict[str, dict[str, Any]]:
    target = target.resolve(strict=True)
    actual_rows = _target_inventory(target)
    actual_directories = _target_directory_inventory(target)
    closed_target = {
        "directories_sha256": hashlib.sha256(
            canonical_bytes(actual_directories)
        ).hexdigest().upper(),
        "directory_count": len(actual_directories),
        "file_count": len(actual_rows),
        "rows_sha256": hashlib.sha256(canonical_bytes(actual_rows)).hexdigest().upper(),
    }
    manifests = {
        name: _installed_wheel_manifest(
            name,
            candidates[name]["wheel"],
            target,
            closed_target,
        )
        for name in sorted(PACKAGED)
    }
    claimed: dict[str, str] = {}
    for name, manifest in manifests.items():
        for row in manifest["files"]:
            path = str(row["path"])
            if path in claimed:
                raise BindingError(
                    f"installed target path is claimed by {claimed[path]} and {name}"
                )
            claimed[path] = name
    actual_paths = {str(row["path"]) for row in actual_rows}
    if not allow_unregistered and actual_paths != set(claimed):
        raise BindingError("installed target contains unregistered files")
    implied_paths = actual_paths if allow_unregistered else set(claimed)
    if set(actual_directories) != _implied_target_directories(sorted(implied_paths)):
        raise BindingError("installed target contains unregistered directories")
    all_paths = actual_paths | set(actual_directories)
    if len({path.casefold() for path in all_paths}) != len(all_paths):
        raise BindingError("installed target contains a file/directory case-fold collision")
    return manifests


def _runtime_environment_binding(
    target: Path,
    candidate_manifests: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind every non-candidate distribution in the isolated target."""

    target = target.resolve(strict=True)
    actual_rows = _target_inventory(target)
    _reject_source_candidate_target_shadowing(actual_rows)
    actual_by_path = {str(row["path"]): row for row in actual_rows}
    candidate_paths = {
        str(row["path"])
        for manifest in candidate_manifests.values()
        for row in manifest["files"]
    }
    extra_paths = set(actual_by_path) - candidate_paths
    record_paths = sorted(
        path for path in extra_paths if path.endswith(".dist-info/RECORD")
    )
    claimed: dict[str, str] = {}
    distributions: list[dict[str, Any]] = []
    identities: set[str] = set()
    for record_path in record_paths:
        dist_info = PurePosixPath(record_path).parent.as_posix()
        metadata_path = f"{dist_info}/METADATA"
        if metadata_path not in extra_paths:
            raise BindingError("runtime distribution METADATA is absent")
        distribution, version = _metadata_identity(
            (target / Path(metadata_path)).read_bytes(),
            label=f"runtime {dist_info}",
        )
        canonical_name = _canonical_distribution_name(distribution)
        if canonical_name in identities:
            raise BindingError("runtime distribution identity is duplicated")
        identities.add(canonical_name)
        record_raw = _regular_file_bytes(
            target / Path(record_path),
            label=f"runtime {dist_info} RECORD",
        )
        record = _read_record(record_raw, label=f"runtime {dist_info} RECORD")
        rows: list[dict[str, Any]] = []
        for path in sorted(record):
            if path not in extra_paths or path in claimed:
                raise BindingError("runtime RECORD ownership differs")
            raw = _regular_file_bytes(
                target / Path(path),
                label=f"runtime {dist_info} file",
            )
            digest, size = record[path]
            if path == record_path:
                if digest or size:
                    raise BindingError("runtime RECORD self-row differs")
            elif digest != f"sha256={_record_digest(raw)}" or size != str(len(raw)):
                raise BindingError("runtime RECORD hash or size differs")
            claimed[path] = canonical_name
            rows.append(dict(actual_by_path[path]))
        distributions.append(
            {
                "dist_info": dist_info,
                "distribution": distribution,
                "file_count": len(rows),
                "files_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest().upper(),
                "normalized_name": canonical_name,
                "record_sha256": hashlib.sha256(record_raw).hexdigest().upper(),
                "version": version,
            }
        )
    if set(claimed) != extra_paths:
        raise BindingError("isolated runtime target contains non-RECORD files")
    if identities != RUNTIME_DISTRIBUTION_IDENTITIES:
        raise BindingError("isolated runtime target distribution identities differ")
    directories = _target_directory_inventory(target)
    git_runtime, process_environment = _git_runtime_binding()
    python_runtime = _python_runtime_binding(process_environment)
    return {
        "closed_target": {
            "directories_sha256": hashlib.sha256(
                canonical_bytes(directories)
            ).hexdigest().upper(),
            "directory_count": len(directories),
            "file_count": len(actual_rows),
            "rows_sha256": hashlib.sha256(
                canonical_bytes(actual_rows)
            ).hexdigest().upper(),
        },
        "distributions": sorted(
            distributions, key=lambda row: str(row["normalized_name"])
        ),
        "git": git_runtime,
        "process_environment": process_environment,
        "python": python_runtime,
        "schema": "anysolver.e4-pl-s3-isolated-runtime-environment-v2",
        "target": str(target),
    }


def _bind_execution_target(
    target: Path,
    candidates: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    manifests = _build_installed_target_manifests(
        target, candidates, allow_unregistered=True
    )
    runtime = _runtime_environment_binding(target, manifests)
    result = {name: dict(candidate) for name, candidate in candidates.items()}
    for name in PACKAGED:
        wheel = dict(result[name]["wheel"])
        wheel["installed_target"] = manifests[name]
        result[name]["wheel"] = wheel
    return result, runtime


def _verify_bound_execution_target(
    target: Path,
    candidates: Mapping[str, Mapping[str, Any]],
    runtime_environment: object,
) -> dict[str, dict[str, Any]]:
    stripped: dict[str, dict[str, Any]] = {}
    for name, candidate in candidates.items():
        copied = dict(candidate)
        wheel = copied.get("wheel")
        if name in PACKAGED:
            if not isinstance(wheel, dict) or "installed_target" not in wheel:
                raise BindingError(f"{name} installed-target binding is absent")
            wheel_copy = dict(wheel)
            wheel_copy.pop("installed_target")
            copied["wheel"] = wheel_copy
        stripped[name] = copied
    expected_candidates, expected_runtime = _bind_execution_target(target, stripped)
    if candidates != expected_candidates or runtime_environment != expected_runtime:
        raise BindingError("bound isolated execution environment differs")
    return expected_candidates


def _reverify_one_installed_target(
    name: str,
    wheel: Mapping[str, Any],
    value: object,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "closed_target",
        "distribution",
        "files",
        "files_sha256",
        "import_name",
        "record",
        "schema",
        "target",
        "version",
        "wheel_sha256",
    }:
        raise BindingError(f"{name} installed-target binding is malformed")
    target = Path(str(value["target"])).resolve(strict=True)
    actual_rows = _target_inventory(target)
    actual_directories = _target_directory_inventory(target)
    expected_closed = {
        "directories_sha256": hashlib.sha256(
            canonical_bytes(actual_directories)
        ).hexdigest().upper(),
        "directory_count": len(actual_directories),
        "file_count": len(actual_rows),
        "rows_sha256": hashlib.sha256(canonical_bytes(actual_rows)).hexdigest().upper(),
    }
    if value["closed_target"] != expected_closed:
        raise BindingError(f"{name} installed target inventory differs")
    expected = _installed_wheel_manifest(name, wheel, target, expected_closed)
    if value != expected:
        raise BindingError(f"{name} installed target provenance differs")
    return expected


def _bind_installed_target(
    target: Path,
    candidates: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    manifests = _build_installed_target_manifests(target, candidates)
    result = {name: dict(candidate) for name, candidate in candidates.items()}
    for name in PACKAGED:
        wheel = dict(result[name]["wheel"])
        wheel["installed_target"] = manifests[name]
        result[name]["wheel"] = wheel
    return result


def _verify_bound_installed_target(
    target: Path,
    candidates: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    stripped: dict[str, dict[str, Any]] = {}
    bound: dict[str, object] = {}
    for name, candidate in candidates.items():
        copied = dict(candidate)
        wheel = copied.get("wheel")
        if name in PACKAGED:
            if not isinstance(wheel, dict) or "installed_target" not in wheel:
                raise BindingError(f"{name} installed-target binding is absent")
            wheel_copy = dict(wheel)
            bound[name] = wheel_copy.pop("installed_target")
            copied["wheel"] = wheel_copy
        stripped[name] = copied
    expected = _build_installed_target_manifests(target, stripped)
    if bound != expected:
        raise BindingError("bound installed target differs from exact wheels")
    return _bind_installed_target(target, stripped)


def _pairs(values: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise BindingError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise BindingError(f"nonfinite JSON value is forbidden: {value}")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_bytes(),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise BindingError(f"{path} must contain one JSON object")
    return value


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _file_binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or resolved.is_symlink():
        raise BindingError(f"binding target is not a regular file: {path}")
    raw = resolved.read_bytes()
    if not raw:
        raise BindingError(f"binding target is empty: {path}")
    return {
        "bytes": len(raw),
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
    }


def _git(root: Path, *arguments: str) -> str:
    launcher = _FROZEN_GIT_EXECUTABLE
    if launcher is None:
        discovered = shutil.which("git")
        if discovered is None:
            raise BindingError("Git launcher is unavailable")
        launcher = Path(discovered).resolve(strict=True)
    engine = _FROZEN_GIT_ENGINE or launcher
    executable = engine if _FROZEN_GIT_ENGINE is not None else launcher
    process_environment = _closed_process_environment(launcher, engine)
    environment = _git_environment(process_environment, executable)
    result = subprocess.run(
        [
            str(executable),
            "--no-replace-objects",
            "-c",
            f"safe.directory={root}",
            "-c",
            "core.autocrlf=true" if os.name == "nt" else "core.autocrlf=input",
            "-c",
            "core.attributesFile=NUL" if os.name == "nt" else "core.attributesFile=/dev/null",
            "-c",
            "core.commitGraph=false",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.untrackedCache=false",
            "-C",
            str(root),
            *arguments,
        ],
        check=False,
        capture_output=True,
        cwd=executable.parent,
        env=environment,
        text=True,
    )
    if result.returncode != 0:
        raise BindingError(f"Git identity check failed for {root}")
    return result.stdout.rstrip("\r\n")


def _git_hash_worktree(root: Path, paths: Sequence[str]) -> list[str]:
    """Hash every tracked file through only the frozen built-in clean rules."""

    launcher = _FROZEN_GIT_EXECUTABLE
    if launcher is None:
        discovered = shutil.which("git")
        if discovered is None:
            raise BindingError("Git launcher is unavailable")
        launcher = Path(discovered).resolve(strict=True)
    engine = _FROZEN_GIT_ENGINE or launcher
    executable = engine if _FROZEN_GIT_ENGINE is not None else launcher
    process_environment = _closed_process_environment(launcher, engine)
    result = subprocess.run(
        [
            str(executable),
            "--no-replace-objects",
            "-c",
            f"safe.directory={root}",
            "-c",
            "core.autocrlf=true" if os.name == "nt" else "core.autocrlf=input",
            "-c",
            "core.attributesFile=NUL" if os.name == "nt" else "core.attributesFile=/dev/null",
            "-c",
            "core.commitGraph=false",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.untrackedCache=false",
            "-C",
            str(root),
            "hash-object",
            "--stdin-paths",
        ],
        check=False,
        capture_output=True,
        cwd=executable.parent,
        env=_git_environment(process_environment, executable),
        input="".join(f"{path}\n" for path in paths),
        text=True,
    )
    hashes = result.stdout.splitlines()
    if result.returncode != 0 or result.stderr or len(hashes) != len(paths):
        raise BindingError("tracked worktree hashing failed")
    return hashes


def _reject_worktree_git_overrides(root: Path) -> None:
    """Reject repository-local routes that can transform executable bytes."""

    config_raw = _git(root, "config", "--show-scope", "--null", "--list")
    fields = config_raw.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise BindingError("candidate Git configuration scope is malformed")
    for index in range(0, len(fields), 2):
        scope = fields[index].casefold()
        entry = fields[index + 1]
        if scope == "command":
            continue
        if scope not in {"local", "worktree"}:
            raise BindingError("candidate Git configuration escaped the closed scopes")
        key, separator, _value = entry.partition("\n")
        normalized = key.casefold()
        if separator != "\n" or (
            normalized.startswith(
                (
                    "commitgraph.",
                    "core.fsmonitor",
                    "filter.",
                    "fsmonitor.",
                    "include.",
                    "includeif.",
                )
            )
            or normalized == "diff.external"
            or (
                normalized.startswith("diff.")
                and normalized.endswith((".command", ".textconv"))
            )
            or (
                normalized.startswith("merge.")
                and normalized.endswith(".driver")
            )
            or normalized
            in {
                "core.attributesfile",
                "core.commitgraph",
                "core.hookspath",
                "core.worktree",
                "extensions.partialclone",
                "extensions.worktreeconfig",
                "gpg.program",
                "interactive.difffilter",
                "log.showsignature",
            }
            or (
                normalized.startswith("gpg.")
                and normalized.endswith(".program")
            )
            or (
                normalized.startswith("remote.")
                and normalized.endswith((".partialclonefilter", ".promisor"))
            )
        ):
            raise BindingError("candidate Git configuration contains an executable override")
    info_value = _git(root, "rev-parse", "--git-path", "info/attributes")
    info_path = Path(info_value)
    if not info_path.is_absolute():
        info_path = root / info_path
    if info_path.exists() or info_path.is_symlink():
        raise BindingError("candidate Git info attributes are forbidden")


def _closed_worktree_binding(root: Path) -> dict[str, Any]:
    """Hash the complete checkout surface and reject ignored/untracked entries."""

    root = root.resolve(strict=True)
    _reject_worktree_git_overrides(root)
    tracked_raw = _git(root, "ls-files", "-z", "--cached")
    tracked = [path for path in tracked_raw.split("\0") if path]
    flagged_raw = _git(root, "ls-files", "-v", "-z", "--cached")
    flagged = [entry for entry in flagged_raw.split("\0") if entry]
    staged_raw = _git(root, "ls-files", "--stage", "-z", "--cached")
    staged_entries = [entry for entry in staged_raw.split("\0") if entry]
    tree_raw = _git(root, "ls-tree", "-rz", "HEAD")
    tree_entries = [entry for entry in tree_raw.split("\0") if entry]
    if (
        len(tracked) != len(set(tracked))
        or len({path.casefold() for path in tracked}) != len(tracked)
        or any(_safe_archive_path(path, label="tracked checkout") != path for path in tracked)
        or len(flagged) != len(tracked)
        or any(
            len(entry) < 3
            or entry[0] != "H"
            or entry[1] != " "
            or entry[2:] != tracked[index]
            for index, entry in enumerate(flagged)
        )
    ):
        raise BindingError("tracked checkout paths or index flags are malformed")
    staged: list[tuple[str, str, str]] = []
    for entry in staged_entries:
        metadata, separator, path = entry.partition("\t")
        fields = metadata.split()
        if (
            separator != "\t"
            or len(fields) != 3
            or fields[2] != "0"
            or path != tracked[len(staged)]
        ):
            raise BindingError("candidate index stage differs")
        staged.append((fields[0], fields[1], path))
    tree: list[tuple[str, str, str]] = []
    for entry in tree_entries:
        metadata, separator, path = entry.partition("\t")
        fields = metadata.split()
        if separator != "\t" or len(fields) != 3 or fields[1] != "blob":
            raise BindingError("candidate HEAD tree contains a non-blob entry")
        tree.append((fields[0], fields[2], path))
    if staged != tree or [row[2] for row in staged] != tracked:
        raise BindingError("candidate index differs from HEAD tree")
    if _git_hash_worktree(root, tracked) != [row[1] for row in staged]:
        raise BindingError("candidate worktree bytes differ from HEAD")
    rows: list[dict[str, Any]] = []
    directories: list[str] = []
    for directory, directory_names, filenames in os.walk(root, followlinks=False):
        base = Path(directory)
        if base == root:
            directory_names[:] = [name for name in directory_names if name != ".git"]
            filenames = [name for name in filenames if name != ".git"]
        directory_names.sort()
        filenames.sort()
        for name in directory_names:
            child = base / name
            if child.is_symlink() or _is_reparse(child) or not child.is_dir():
                raise BindingError("candidate checkout contains a linked directory")
            relative = child.relative_to(root).as_posix()
            _safe_archive_path(relative, label="candidate directory")
            directories.append(relative)
        for name in filenames:
            child = base / name
            relative = child.relative_to(root).as_posix()
            _safe_archive_path(relative, label="candidate file")
            rows.append(
                _sha256_row(
                    relative,
                    _regular_file_bytes(child, label="candidate checkout file"),
                )
            )
    rows.sort(key=lambda row: str(row["path"]))
    directories.sort()
    actual_paths = [str(row["path"]) for row in rows]
    expected_directories = sorted(_implied_target_directories(tracked))
    combined = actual_paths + directories
    if (
        actual_paths != sorted(tracked)
        or directories != expected_directories
        or len({path.casefold() for path in combined}) != len(combined)
    ):
        raise BindingError(
            "candidate checkout contains ignored, untracked, or extra directory entries"
        )
    return {
        "directories_sha256": hashlib.sha256(
            canonical_bytes(directories)
        ).hexdigest().upper(),
        "directory_count": len(directories),
        "file_count": len(rows),
        "rows_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest().upper(),
    }


def _commit_identity(root: Path, commit: str) -> dict[str, str]:
    fields = _git(
        root,
        "show",
        "-s",
        "--format=%H%x00%T%x00%P%x00%s",
        commit,
    ).split("\x00")
    if len(fields) != 4 or " " in fields[2]:
        raise BindingError(f"Git commit identity differs for {commit}")
    return {
        "commit": fields[0],
        "tree": fields[1],
        "parent": fields[2],
        "subject": fields[3],
    }


def _changed_paths(root: Path, parent: str, commit: str) -> list[str]:
    value = _git(root, "diff", "--name-only", parent, commit)
    return value.splitlines() if value else []


def _blob(root: Path, commit: str, path: str) -> str:
    return _git(root, "rev-parse", f"{commit}:{path}")


def _frozen_source_rows(root: Path, commit: str) -> list[dict[str, str]]:
    output = _git(root, "ls-tree", "-r", commit, "--", "src/anysolver")
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        metadata, separator, path = line.partition("\t")
        fields = metadata.split()
        if (
            separator != "\t"
            or len(fields) != 3
            or fields[1] != "blob"
            or HEX40.fullmatch(fields[2]) is None
            or not path.startswith("src/anysolver/")
        ):
            raise BindingError("frozen Q4 source tree entry is malformed")
        if path not in Q4_FROZEN_SOURCE_EXCLUSIONS:
            rows.append({"git_blob": fields[2], "path": path})
    if [row["path"] for row in rows] != sorted(row["path"] for row in rows):
        raise BindingError("frozen Q4 source tree order differs")
    return rows


def _verify_anysolver_policy(
    value: object,
    solver: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind the reviewed guard correction and a base-identical source superset."""

    if not isinstance(value, dict) or set(value) != {
        "base_commit",
        "changed_paths",
        "q4_guard_import_commit",
    }:
        raise BindingError("ANYsolver policy fields differ")
    base_commit = value["base_commit"]
    changed_paths = value["changed_paths"]
    guard_import_commit = value["q4_guard_import_commit"]
    if (
        base_commit != Q4_BASE_IDENTITY["commit"]
        or guard_import_commit != Q4_GUARD_IMPORT_IDENTITY["commit"]
        or not isinstance(changed_paths, list)
        or any(type(path) is not str or not path for path in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        raise BindingError("ANYsolver policy is malformed")
    solver_root = Path(str(solver["root"])).resolve(strict=True)
    candidate_commit = str(solver["commit"])
    if _commit_identity(solver_root, base_commit) != Q4_BASE_IDENTITY:
        raise BindingError("frozen Q4 base identity differs")
    if (
        _commit_identity(solver_root, Q4_GUARD_SOURCE_IDENTITY["commit"])
        != Q4_GUARD_SOURCE_IDENTITY
    ):
        raise BindingError("reviewed Q4 guard source identity differs")
    if (
        _commit_identity(solver_root, guard_import_commit)
        != Q4_GUARD_IMPORT_IDENTITY
    ):
        raise BindingError("imported Q4 guard identity differs")
    if _changed_paths(
        solver_root,
        Q4_GUARD_SOURCE_IDENTITY["parent"],
        Q4_GUARD_SOURCE_IDENTITY["commit"],
    ) != [path for path, _blob_id in Q4_GUARD_V2_PATH_BLOBS]:
        raise BindingError("reviewed Q4 guard path set differs")
    if _changed_paths(
        solver_root,
        Q4_GUARD_IMPORT_IDENTITY["parent"],
        Q4_GUARD_IMPORT_IDENTITY["commit"],
    ) != [path for path, _blob_id in Q4_GUARD_V2_PATH_BLOBS]:
        raise BindingError("imported Q4 guard path set differs")
    for path, expected_blob in Q4_GUARD_V2_PATH_BLOBS:
        observed = {
            _blob(solver_root, Q4_GUARD_SOURCE_IDENTITY["commit"], path),
            _blob(solver_root, guard_import_commit, path),
        }
        if observed != {expected_blob}:
            raise BindingError(f"reviewed Q4 guard blob differs: {path}")
    if (
        _commit_identity(solver_root, Q4_GUARD_SUCCESSOR_IDENTITY["commit"])
        != Q4_GUARD_SUCCESSOR_IDENTITY
    ):
        raise BindingError("reviewed Q4 vector replay guard identity differs")
    if _changed_paths(
        solver_root,
        Q4_GUARD_SUCCESSOR_IDENTITY["parent"],
        Q4_GUARD_SUCCESSOR_IDENTITY["commit"],
    ) != [path for path, _blob_id in Q4_GUARD_SUCCESSOR_PATH_BLOBS]:
        raise BindingError("reviewed Q4 vector replay guard path set differs")
    for path, expected_blob in Q4_GUARD_PATH_BLOBS:
        if _blob(solver_root, candidate_commit, path) != expected_blob:
            raise BindingError(f"reviewed Q4 final guard blob differs: {path}")
    for path, expected_blob in Q4_NONMECHANICS_INTEGRATION_PATH_BLOBS:
        if _blob(solver_root, candidate_commit, path) != expected_blob:
            raise BindingError(f"bound nonmechanics integration blob differs: {path}")
    _git(solver_root, "merge-base", "--is-ancestor", guard_import_commit, candidate_commit)
    observed_paths = _changed_paths(solver_root, base_commit, candidate_commit)
    if observed_paths != changed_paths:
        raise BindingError("ANYsolver changed paths differ")
    base_rows = _frozen_source_rows(solver_root, base_commit)
    candidate_rows = _frozen_source_rows(solver_root, candidate_commit)
    rows_sha256 = hashlib.sha256(canonical_bytes(base_rows)).hexdigest().upper()
    if (
        base_rows != candidate_rows
        or len(base_rows) != Q4_FROZEN_SOURCE_FILE_COUNT
        or rows_sha256 != Q4_FROZEN_SOURCE_ROWS_SHA256
    ):
        raise BindingError("frozen Q4 mechanics/source identity differs")
    return {
        "base": dict(Q4_BASE_IDENTITY),
        "candidate": {
            "commit": candidate_commit,
            "tree": str(solver["tree"]),
        },
        "changed_paths": changed_paths,
        "frozen_q4_source_identity": {
            "excluded_authorized_guard_paths": list(Q4_GUARD_SOURCE_PATHS),
            "excluded_nonmechanics_integration_paths": list(
                Q4_NONMECHANICS_INTEGRATION_PATHS
            ),
            "bound_nonmechanics_integration_paths": [
                {"git_blob": blob_id, "path": path}
                for path, blob_id in Q4_NONMECHANICS_INTEGRATION_PATH_BLOBS
            ],
            "file_count": len(base_rows),
            "rows_sha256": rows_sha256,
            "scope": (
                "ALL_TRACKED_SRC_ANYSOLVER_FILES_EXCEPT_EXACT_GUARD_AND_"
                "NON_Q4_INTEGRATION_PATHS"
            ),
        },
        "guard_correction": {
            "authorized_paths": [
                {"git_blob": blob_id, "path": path}
                for path, blob_id in Q4_GUARD_PATH_BLOBS
            ],
            "imported": dict(Q4_GUARD_IMPORT_IDENTITY),
            "reviewed_source": dict(Q4_GUARD_SOURCE_IDENTITY),
            "vector_replay_successor": dict(Q4_GUARD_SUCCESSOR_IDENTITY),
            "scope": "GUARD_SERIALIZATION_AND_STATE_LIFECYCLE_ONLY",
        },
        "q4_mechanics_change": "NONE",
    }


def _reverify_bound_anysolver_policy(
    value: object,
    solver: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BindingError("bound ANYsolver policy is malformed")
    input_policy = {
        "base_commit": Q4_BASE_IDENTITY["commit"],
        "changed_paths": value.get("changed_paths"),
        "q4_guard_import_commit": Q4_GUARD_IMPORT_IDENTITY["commit"],
    }
    expected = _verify_anysolver_policy(input_policy, solver)
    if value != expected:
        raise BindingError("bound ANYsolver guard-only identity differs")
    return expected


def _verify_candidate(name: str, value: object) -> dict[str, Any]:
    input_fields = {
        "commit",
        "root",
        "subject",
        "tree",
        "wheel",
    }
    if not isinstance(value, dict) or set(value) not in (
        input_fields,
        input_fields | {"working_tree"},
    ):
        raise BindingError(f"{name} candidate fields differ")
    commit = value["commit"]
    tree = value["tree"]
    subject = value["subject"]
    if (
        type(commit) is not str
        or HEX40.fullmatch(commit) is None
        or type(tree) is not str
        or HEX40.fullmatch(tree) is None
        or type(subject) is not str
        or not subject
        or "\n" in subject
        or "\r" in subject
    ):
        raise BindingError(f"{name} Git identity is malformed")
    root = Path(str(value["root"])).resolve(strict=True)
    if not root.is_dir():
        raise BindingError(f"{name} root is not a directory")
    _reject_worktree_git_overrides(root)
    _git(root, "fsck", "--full", "--strict")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise BindingError(f"{name} candidate root is dirty")
    working_tree = _closed_worktree_binding(root)
    if "working_tree" in value and value["working_tree"] != working_tree:
        raise BindingError(f"{name} closed checkout identity differs")
    observed = {
        "commit": _git(root, "rev-parse", "HEAD"),
        "tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "subject": _git(root, "show", "-s", "--format=%s", "HEAD"),
    }
    if observed != {"commit": commit, "tree": tree, "subject": subject}:
        raise BindingError(f"{name} candidate Git identity differs")
    wheel = value["wheel"]
    if name in PACKAGED:
        if not isinstance(wheel, dict) or set(wheel) not in (
            {
                "bytes",
                "filename",
                "path",
                "sha256",
            },
            {
                "bytes",
                "filename",
                "installed_target",
                "path",
                "sha256",
            },
        ):
            raise BindingError(f"{name} wheel binding is malformed")
        installed_target = wheel.get("installed_target")
        wheel_base = {
            key: wheel[key]
            for key in (
                "bytes",
                "filename",
                "path",
                "sha256",
            )
        }
        wheel_base["path"] = str(
            _canonical_regular_file_route(
                wheel_base["path"], label=f"{name} wheel"
            )
        )
        _wheel_blueprint(name, wheel_base)
        if installed_target is not None:
            wheel_base["installed_target"] = _reverify_one_installed_target(
                name, wheel_base, installed_target
            )
        wheel = wheel_base
    elif wheel is not None:
        raise BindingError(f"{name} must not carry a wheel")
    return {
        "commit": commit,
        "root": str(root),
        "subject": subject,
        "tree": tree,
        "wheel": wheel,
        "working_tree": working_tree,
    }


def _preflight_environment(
    runtime_environment: Mapping[str, Any],
    target: Path,
    scratch_root: Path,
    candidate_name: str,
    dependency_roots: Mapping[str, object],
) -> dict[str, str]:
    process_environment = runtime_environment.get("process_environment")
    if not isinstance(process_environment, dict) or not all(
        type(key) is str and type(value) is str
        for key, value in process_environment.items()
    ):
        raise BindingError("preflight process environment differs")
    controlled_names = {
        environment_name
        for mapping in CANDIDATE_GATE_ROOT_ENVIRONMENTS.values()
        for environment_name in mapping
    }
    if controlled_names & set(process_environment):
        raise BindingError("preflight dependency roots must not be inherited")
    root_environment = CANDIDATE_GATE_ROOT_ENVIRONMENTS.get(candidate_name, {})
    expected_dependencies = set(root_environment.values())
    if (
        candidate_name not in CANDIDATES
        or not isinstance(dependency_roots, Mapping)
        or set(dependency_roots) != expected_dependencies
    ):
        raise BindingError(f"{candidate_name} preflight dependency roots differ")
    result = dict(process_environment)
    result.update(PREFLIGHT_ENVIRONMENT)
    for test_repository_override in (
        "GIT_GRAFT_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_REPLACE_REF_BASE",
    ):
        result.pop(test_repository_override, None)
    result["PYTHONPATH"] = str(target.resolve(strict=True))
    scratch_root = scratch_root.resolve(strict=True)
    if not scratch_root.is_dir() or scratch_root.is_symlink():
        raise BindingError("preflight scratch root is not a regular directory")
    result["TEMP"] = str(scratch_root)
    result["TMP"] = str(scratch_root)
    for environment_name, dependency_name in sorted(root_environment.items()):
        dependency_root = Path(
            str(dependency_roots[dependency_name])
        ).resolve(strict=True)
        if not dependency_root.is_dir():
            raise BindingError(
                f"{candidate_name} preflight dependency root is not a directory"
            )
        result[environment_name] = str(dependency_root)
    return dict(sorted(result.items()))


def _preflight_dependency_roots(
    candidate_name: str,
    candidates: Mapping[str, Mapping[str, Any]],
) -> dict[str, str]:
    root_environment = CANDIDATE_GATE_ROOT_ENVIRONMENTS.get(candidate_name, {})
    result: dict[str, str] = {}
    for dependency_name in sorted(root_environment.values()):
        candidate = candidates.get(dependency_name)
        if not isinstance(candidate, Mapping) or type(candidate.get("root")) is not str:
            raise BindingError(f"{candidate_name} preflight dependency candidate differs")
        result[dependency_name] = str(candidate["root"])
    return result


def _preflight_dependency_candidate_bindings(
    candidate_name: str,
    candidates: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    roots = _preflight_dependency_roots(candidate_name, candidates)
    result: dict[str, dict[str, Any]] = {}
    for dependency_name in sorted(roots):
        candidate = candidates[dependency_name]
        if not all(
            key in candidate
            for key in ("commit", "root", "subject", "tree", "working_tree")
        ):
            raise BindingError(f"{candidate_name} preflight dependency identity differs")
        result[dependency_name] = {
            key: candidate[key]
            for key in ("commit", "root", "subject", "tree", "working_tree")
        }
    return result


def _preflight_target_identity(target: Path) -> dict[str, Any]:
    target = target.resolve(strict=True)
    rows = _target_inventory(target)
    directories = _target_directory_inventory(target)
    return {
        "directories_sha256": hashlib.sha256(
            canonical_bytes(directories)
        ).hexdigest().upper(),
        "directory_count": len(directories),
        "file_count": len(rows),
        "path": str(target),
        "rows_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest().upper(),
    }


def _execution_copy_binding(candidate_root: Path, execution_root: Path) -> dict[str, Any]:
    """Bind tracked candidate bytes in a disposable preflight execution copy."""

    candidate_root = candidate_root.resolve(strict=True)
    execution_root = execution_root.resolve(strict=True)
    tracked = [
        path
        for path in _git(candidate_root, "ls-files", "-z", "--cached").split("\0")
        if path
    ]
    directories = sorted(_implied_target_directories(tracked))
    for relative in directories:
        directory = execution_root / Path(relative)
        if directory.is_symlink() or _is_reparse(directory) or not directory.is_dir():
            raise BindingError("preflight execution-copy directory differs")
    rows = [
        _sha256_row(
            relative,
            _regular_file_bytes(
                execution_root / Path(relative),
                label="preflight execution-copy file",
            ),
        )
        for relative in tracked
    ]
    return {
        "directories_sha256": hashlib.sha256(
            canonical_bytes(directories)
        ).hexdigest().upper(),
        "directory_count": len(directories),
        "file_count": len(rows),
        "rows_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest().upper(),
    }


def _preflight_python_identity(runtime_environment: Mapping[str, Any]) -> dict[str, Any]:
    python = runtime_environment.get("python")
    if not isinstance(python, dict):
        raise BindingError("preflight Python identity differs")
    try:
        result = {
            "bytes": python["bytes"],
            "path": python["path"],
            "sha256": python["sha256"],
            "version": python["version"],
        }
    except KeyError as exc:
        raise BindingError("preflight Python identity differs") from exc
    if (
        type(result["bytes"]) is not int
        or type(result["path"]) is not str
        or type(result["sha256"]) is not str
        or type(result["version"]) is not str
    ):
        raise BindingError("preflight Python identity differs")
    return result


def _preflight_command(
    name: str,
    identifier: str,
    candidate_root: Path,
    execution_target: Path,
    runtime_environment: Mapping[str, Any],
    output_directory: Path,
) -> list[str]:
    python = runtime_environment.get("python")
    if not isinstance(python, dict) or type(python.get("path")) is not str:
        raise BindingError("preflight Python identity differs")
    python_path = Path(str(python["path"])).resolve(strict=True)
    candidate_root = candidate_root.resolve(strict=True)
    execution_target = execution_target.resolve(strict=True)
    output_directory = output_directory.resolve(strict=True)
    import_binding = json.dumps(
        {
            "candidate_imports": list(SOURCE_CANDIDATE_IMPORTS.get(name, ())),
            "candidate_sys_path": SOURCE_CANDIDATE_IMPORT_ROOTS.get(name, "."),
            "target_imports": (
                [PACKAGED_IDENTITIES[name][2]]
                if name in PACKAGED_IDENTITIES
                and PACKAGED_IDENTITIES[name][2]
                not in SOURCE_CANDIDATE_IMPORTS.get(name, ())
                else []
            ),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    if identifier == "merge-portable-tests":
        if name != "ANYsolver":
            raise BindingError("portable preflight route differs")
        return [
            str(python_path),
            "-I",
            "-S",
            "-B",
            "-c",
            PREFLIGHT_PORTABLE_BOOTSTRAP,
            str(execution_target),
            str(candidate_root),
            str(PREFLIGHT_CONFIG.resolve(strict=True)),
            str((output_directory / f"{name}-{identifier}-portable").resolve()),
            import_binding,
            PREFLIGHT_BOOTSTRAP,
        ]
    nodes = PREFLIGHT_GATE_NODES.get(name, {}).get(identifier)
    if nodes is None:
        raise BindingError("preflight gate route differs")
    basetemp = output_directory / f"{name}-{identifier}-basetemp"
    return [
        str(python_path),
        "-I",
        "-S",
        "-B",
        "-c",
        PREFLIGHT_BOOTSTRAP,
        str(execution_target),
        str(candidate_root),
        str(PREFLIGHT_CONFIG.resolve(strict=True)),
        str(basetemp.resolve()),
        import_binding,
        *nodes,
    ]


def _verify_preflight(
    name: str,
    candidate: Mapping[str, Any],
    value: object,
    execution_target: Path,
    runtime_environment: Mapping[str, Any],
    candidates: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Verify one canonical clean-tree/test-gate result and all bound logs."""

    if not isinstance(value, dict) or set(value) != {
        "bytes",
        "path",
        "sha256",
    }:
        raise BindingError(f"{name} preflight binding is malformed")
    path = Path(str(value["path"])).resolve(strict=True)
    if not path.is_file() or path.is_symlink():
        raise BindingError(f"{name} preflight is not a regular file")
    raw = path.read_bytes()
    if (
        type(value["bytes"]) is not int
        or value["bytes"] != len(raw)
        or not raw
        or type(value["sha256"]) is not str
        or HEX64.fullmatch(value["sha256"]) is None
        or hashlib.sha256(raw).hexdigest().upper() != value["sha256"]
    ):
        raise BindingError(f"{name} preflight bytes differ")
    record = read_json(path)
    if raw != canonical_bytes(record) or set(record) != {
        "candidate",
        "checkout_after",
        "checkout_before",
        "clean_tree",
        "commit",
        "dependency_candidates_after",
        "dependency_candidates_before",
        "dependency_roots_clean",
        "execution_checkout_after",
        "execution_checkout_before",
        "execution_root",
        "execution_target",
        "gates",
        "generated_products",
        "preflight_config",
        "preflight_runner",
        "python_runtime",
        "schema",
        "scratch_root",
        "tree",
    }:
        raise BindingError(f"{name} preflight record differs")
    gates = record["gates"]
    expected_dependencies = _preflight_dependency_candidate_bindings(
        name,
        candidates,
    )
    output_directory = path.parent.resolve(strict=True)
    expected_execution_root = (output_directory / "candidate-source").resolve(
        strict=True
    )
    expected_scratch_root = (output_directory / "process-temp").resolve(strict=True)
    if (
        record["schema"] != PREFLIGHT_SCHEMA
        or record["candidate"] != name
        or record["commit"] != candidate["commit"]
        or record["tree"] != candidate["tree"]
        or record["clean_tree"] is not True
        or record["dependency_candidates_before"] != expected_dependencies
        or record["dependency_candidates_after"] != expected_dependencies
        or record["dependency_roots_clean"] is not True
        or record["execution_checkout_before"] != candidate.get("working_tree")
        or record["execution_checkout_after"] != candidate.get("working_tree")
        or record["execution_root"] != str(expected_execution_root)
        or record["scratch_root"] != str(expected_scratch_root)
        or record["checkout_before"] != candidate.get("working_tree")
        or record["checkout_after"] != candidate.get("working_tree")
        or record["execution_target"] != _preflight_target_identity(execution_target)
        or record["generated_products"] != []
        or record["preflight_config"] != _file_binding(PREFLIGHT_CONFIG)
        or record["preflight_runner"] != _file_binding(PREFLIGHT_RUNNER)
        or record["python_runtime"]
        != _preflight_python_identity(runtime_environment)
        or not isinstance(gates, list)
        or not gates
    ):
        raise BindingError(f"{name} preflight identity is not green")
    expected_environment = _preflight_environment(
        runtime_environment,
        execution_target,
        expected_scratch_root,
        name,
        _preflight_dependency_roots(name, candidates),
    )
    identifiers: list[str] = []
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {
            "command",
            "controller",
            "environment",
            "id",
            "log",
            "passed",
            "returncode",
            "stderr_log",
            "working_directory",
        }:
            raise BindingError(f"{name} preflight gate differs")
        command = gate["command"]
        identifier = gate["id"]
        log = gate["log"]
        stderr_log = gate["stderr_log"]
        controller = gate["controller"]
        expected_nodes = PREFLIGHT_GATE_NODES[name].get(identifier)
        expected_command = _preflight_command(
            name,
            identifier,
            expected_execution_root,
            execution_target,
            runtime_environment,
            output_directory,
        )
        if (
            type(identifier) is not str
            or not identifier
            or expected_nodes is None
            or not isinstance(command, list)
            or command != expected_command
            or gate["environment"] != expected_environment
            or gate["working_directory"] != str(expected_execution_root)
            or gate["passed"] is not True
            or type(gate["returncode"]) is not int
            or gate["returncode"] != 0
            or not isinstance(log, dict)
            or set(log) != {"bytes", "path", "sha256"}
            or not isinstance(stderr_log, dict)
            or set(stderr_log) != {"bytes", "path", "sha256"}
            or not isinstance(controller, dict)
            or set(controller) != {
                "active_descendants_observed",
                "inactivity_seconds",
                "memory_limit_bytes",
                "peak_tree_memory_bytes",
                "progress_signals_observed",
                "terminal",
                "tree_accounting_release",
            }
            or type(controller["active_descendants_observed"]) is not bool
            or controller["inactivity_seconds"] != 1800
            or controller["memory_limit_bytes"] != 24 * (1 << 30)
            or type(controller["peak_tree_memory_bytes"]) is not int
            or controller["peak_tree_memory_bytes"] <= 0
            or not isinstance(controller["progress_signals_observed"], list)
            or controller["progress_signals_observed"]
            != sorted(set(controller["progress_signals_observed"]))
            or any(
                signal not in {"active-processes", "cpu", "files", "stderr", "stdout"}
                for signal in controller["progress_signals_observed"]
            )
            or controller["terminal"] != "completed"
            or controller["tree_accounting_release"]
            != "ATTACH_BEFORE_GATE_RELEASE_V1"
        ):
            raise BindingError(f"{name} preflight gate is not green")
        for relative in expected_nodes:
            node_path = (expected_execution_root / relative).resolve(strict=True)
            expected_kind = (
                node_path.is_dir()
                if relative in {".", "tests"}
                else node_path.is_file()
            )
            if not expected_kind or not node_path.is_relative_to(
                expected_execution_root
            ):
                raise BindingError(f"{name} preflight node differs")
        log_path = Path(str(log["path"])).resolve(strict=True)
        expected_log_path = (
            output_directory / f"{name}-{identifier}.log"
        ).resolve()
        if not log_path.is_file() or log_path.is_symlink():
            raise BindingError(f"{name} preflight log is not regular")
        if log_path != expected_log_path:
            raise BindingError(f"{name} preflight log route differs")
        log_raw = log_path.read_bytes()
        if (
            type(log["bytes"]) is not int
            or log["bytes"] != len(log_raw)
            or not log_raw
            or type(log["sha256"]) is not str
            or HEX64.fullmatch(log["sha256"]) is None
            or hashlib.sha256(log_raw).hexdigest().upper() != log["sha256"]
        ):
            raise BindingError(f"{name} preflight log differs")
        stderr_path = Path(str(stderr_log["path"])).resolve(strict=True)
        expected_stderr_path = (
            output_directory / f"{name}-{identifier}.stderr.log"
        ).resolve()
        if (
            not stderr_path.is_file()
            or stderr_path.is_symlink()
            or stderr_path != expected_stderr_path
        ):
            raise BindingError(f"{name} preflight stderr log differs")
        stderr_raw = stderr_path.read_bytes()
        if (
            type(stderr_log["bytes"]) is not int
            or stderr_log["bytes"] != len(stderr_raw)
            or type(stderr_log["sha256"]) is not str
            or HEX64.fullmatch(stderr_log["sha256"]) is None
            or hashlib.sha256(stderr_raw).hexdigest().upper()
            != stderr_log["sha256"]
        ):
            raise BindingError(f"{name} preflight stderr log differs")
        identifiers.append(identifier)
    if identifiers != list(PREFLIGHT_GATE_IDS[name]):
        raise BindingError(f"{name} preflight gate order or identity differs")
    return {
        "record": record,
        "result": {
            "bytes": len(raw),
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
        },
    }


def build_binding(graph_path: Path) -> dict[str, Any]:
    if graph_path.resolve(strict=True) != FINAL_GRAPH.resolve():
        raise BindingError("candidate graph route differs")
    graph_raw = graph_path.read_bytes()
    graph = read_json(graph_path)
    if graph_raw != canonical_bytes(graph):
        raise BindingError("candidate graph is not canonical JSON")
    if set(graph) != {
        "anysolver_policy",
        "candidates",
        "execution_target",
        "preflight_results",
        "schema",
    }:
        raise BindingError("candidate graph fields differ")
    if graph["schema"] != GRAPH_SCHEMA:
        raise BindingError("candidate graph schema differs")
    candidates = graph["candidates"]
    if not isinstance(candidates, dict) or tuple(candidates) != CANDIDATES:
        raise BindingError("candidate order or membership differs")
    verified_candidates = {
        name: _verify_candidate(name, candidates[name]) for name in CANDIDATES
    }
    target = Path(str(graph["execution_target"])).resolve(strict=True)
    if not target.is_dir():
        raise BindingError("isolated execution target is not a directory")
    verified_candidates, runtime_environment = _bind_execution_target(
        target, verified_candidates
    )
    preflight = graph["preflight_results"]
    if not isinstance(preflight, dict) or tuple(preflight) != CANDIDATES:
        raise BindingError("candidate preflight membership or order differs")
    verified_preflight = {
        name: _verify_preflight(
            name,
            verified_candidates[name],
            preflight[name],
            target,
            runtime_environment,
            verified_candidates,
        )
        for name in CANDIDATES
    }
    files = {
        "base_contract": _file_binding(BASE_CONTRACT),
        "base_input": _file_binding(BASE_INPUT),
        "base_program": _file_binding(BASE_PROGRAM),
        "base_test": _file_binding(BASE_TEST),
        "batch_benchmark": _file_binding(BATCH_BENCHMARK),
        "binding_generator": _file_binding(BINDING_GENERATOR),
        "contract": _file_binding(CONTRACT),
        "coordinator": _file_binding(COORDINATOR),
        "formal_runner": _file_binding(FORMAL_RUNNER),
        "formal_test": _file_binding(FORMAL_TEST),
        "manifest": _file_binding(MANIFEST),
        "mixed_eigen_performance": _file_binding(MIXED_EIGEN_PERFORMANCE),
        "mixed_mesh_manifest_program": _file_binding(MIXED_MESH_MANIFEST_PROGRAM),
        "mixed_mesh_runner": _file_binding(MIXED_MESH_RUNNER),
        "mixed_mesh_smoke_input": _file_binding(MIXED_MESH_SMOKE_INPUT),
        "mixed_structural_common": _file_binding(MIXED_STRUCTURAL_COMMON),
        "mixed_structural_producer": _file_binding(MIXED_STRUCTURAL_PRODUCER),
        "optimization_evidence": _file_binding(OPTIMIZATION_EVIDENCE),
        "preflight_config": _file_binding(PREFLIGHT_CONFIG),
        "preflight_runner": _file_binding(PREFLIGHT_RUNNER),
        "successor": _file_binding(SUCCESSOR),
        "test": _file_binding(TEST),
    }
    solver = verified_candidates["ANYsolver"]
    policy = _verify_anysolver_policy(graph["anysolver_policy"], solver)
    return {
        "anysolver_policy": policy,
        "candidate_graph": _file_binding(graph_path),
        "candidate_preflight": verified_preflight,
        "candidates": verified_candidates,
        "execution_target": str(target),
        "files": files,
        "formal_execution_authorized": False,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "runtime_environment": runtime_environment,
        "schema": SCHEMA,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() != FINAL_BINDING.resolve():
            raise BindingError("candidate binding route differs")
        value = build_binding(args.candidate_graph)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(value))
        return 0
    except (BindingError, OSError, subprocess.SubprocessError) as exc:
        print(f"candidate binding blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
