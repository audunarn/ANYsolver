"""Pinned source and installed-wheel compatibility checks for ANYfileio."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import textwrap
import tomllib
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Any

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version


EXPECTED_REQUIREMENT = "ANYfileio>=0.2.1,<0.3"
EXPECTED_SPECIFIER = SpecifierSet(">=0.2.1,<0.3")
RELEVANT_PACKAGES = {
    "anymaterial",
    "anygeometry",
    "anymesher",
    "anyfileio",
}


def _project(root: Path) -> dict[str, Any]:
    return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]


def _assert_expected_fileio_requirement(requirement: str) -> None:
    parsed = Requirement(requirement)
    assert canonicalize_name(parsed.name) == "anyfileio"
    assert not parsed.extras
    assert parsed.marker is None
    assert parsed.url is None
    assert parsed.specifier == EXPECTED_SPECIFIER


def _source_fileio_requirements() -> list[str]:
    dependencies = _project(Path(__file__).resolve().parents[1])["dependencies"]
    return [
        item
        for item in dependencies
        if canonicalize_name(Requirement(item).name) == "anyfileio"
    ]


def _installed_fileio_requirements() -> list[str]:
    requirements = metadata.requires("ANYsolver") or []
    return [
        item
        for item in requirements
        if re.match(r"(?i)^anyfileio(?:\s|[<>=!~])", item)
    ]


def _is_beneath(path: Path, root: Path) -> bool:
    path_text = os.path.normcase(str(path.resolve()))
    root_text = os.path.normcase(str(root.resolve()))
    try:
        return os.path.commonpath((path_text, root_text)) == root_text
    except ValueError:
        return False


def test_is_beneath_treats_commonpath_value_error_as_not_beneath(
    monkeypatch,
) -> None:
    def reject_cross_drive(_paths: tuple[str, str]) -> str:
        raise ValueError("Paths don't have the same drive")

    monkeypatch.setattr(os.path, "commonpath", reject_cross_drive)
    assert _is_beneath(Path("installed-origin"), Path("workspace")) is False


def test_is_beneath_propagates_non_value_error(monkeypatch) -> None:
    import pytest

    def fail_unexpectedly(_paths: tuple[str, str]) -> str:
        raise RuntimeError("unexpected commonpath failure")

    monkeypatch.setattr(os.path, "commonpath", fail_unexpectedly)
    with pytest.raises(RuntimeError, match="unexpected commonpath failure"):
        _is_beneath(Path("installed-origin"), Path("workspace"))


def _assert_module_identity(
    name: str,
    module: ModuleType,
    versions: dict[str, str],
    roots: dict[str, str],
) -> None:
    assert getattr(module, "__version__") == versions[name]
    origin = Path(module.__file__).resolve()
    root = Path(roots[name]).resolve()
    assert _is_beneath(origin, root), (name, origin, root)
    assert "site-packages" not in os.path.normcase(str(origin))
    normal_checkout = Path(f"C:/Github/{name}")
    assert not _is_beneath(origin, normal_checkout)


def _source_ledgers() -> tuple[dict[str, str], dict[str, str]] | None:
    raw_versions = os.environ.get("ANYSOLVER_EXPECTED_SOURCE_VERSIONS")
    raw_roots = os.environ.get("ANYSOLVER_EXPECTED_SOURCE_ROOTS")
    if raw_versions is None and raw_roots is None:
        return None
    assert raw_versions is not None and raw_roots is not None
    versions = json.loads(raw_versions)
    roots = json.loads(raw_roots)
    expected = {
        "anysolver",
        "anymaterial",
        "anygeometry",
        "anymesher",
        "anyfileio",
    }
    assert set(versions) == expected
    assert set(roots) == expected
    return versions, roots


def _requirements_for(root: Path, package_name: str) -> list[Requirement]:
    project = _project(root)
    raw = list(project.get("dependencies", ()))
    if package_name == "anyfileio":
        raw.extend(project.get("optional-dependencies", {}).get("semantics", ()))
    requirements: list[Requirement] = []
    seen: set[str] = set()
    for item in raw:
        requirement = Requirement(item)
        name = canonicalize_name(requirement.name)
        if name not in RELEVANT_PACKAGES:
            continue
        assert name not in seen, (package_name, name)
        assert requirement.marker is None
        assert requirement.url is None
        seen.add(name)
        requirements.append(requirement)
    return requirements


def _assert_graph(
    roots: dict[str, Path], versions: dict[str, str]
) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for source, root in roots.items():
        project = _project(root)
        assert canonicalize_name(project["name"]) == source
        assert project["version"] == versions[source]
        for requirement in _requirements_for(root, source):
            target = canonicalize_name(requirement.name)
            assert target in versions
            assert Version(versions[target]) in requirement.specifier, (
                source,
                str(requirement),
                versions[target],
            )
            edges.add((source, target))
    required_edges = {
        ("anysolver", "anymaterial"),
        ("anysolver", "anymesher"),
        ("anysolver", "anyfileio"),
        ("anyfileio", "anymesher"),
        ("anyfileio", "anymaterial"),
    }
    if versions["anymesher"] == "0.2.1":
        required_edges.add(("anymesher", "anygeometry"))
    else:
        assert versions["anymesher"] == "0.1.0"
    assert required_edges <= edges
    return edges


def _assert_complete_source_graphs(roots: dict[str, str]) -> None:
    archives = Path(roots["anymaterial"]).resolve().parents[1]
    solver_root = Path(roots["anysolver"]).resolve().parent
    cells = {
        "legacy": (
            {
                "anysolver": solver_root,
                "anymaterial": archives / "material-current",
                "anygeometry": archives / "geometry-legacy",
                "anymesher": archives / "mesh-legacy",
                "anyfileio": archives / "fileio-legacy",
            },
            {
                "anysolver": "0.3.1",
                "anymaterial": "0.1.0",
                "anygeometry": "0.2.0",
                "anymesher": "0.1.0",
                "anyfileio": "0.1.0",
            },
        ),
        "current": (
            {
                "anysolver": solver_root,
                "anymaterial": archives / "material-current",
                "anygeometry": archives / "geometry-current",
                "anymesher": archives / "mesh-current",
                "anyfileio": archives / "fileio-current",
            },
            {
                "anysolver": "0.3.1",
                "anymaterial": "0.1.0",
                "anygeometry": "0.2.1",
                "anymesher": "0.2.1",
                "anyfileio": "0.2.0",
            },
        ),
    }
    for roots_by_name, versions in cells.values():
        _assert_graph(roots_by_name, versions)


def _metadata_requirement(metadata_mode: str) -> str:
    if metadata_mode == "source":
        requirements = _source_fileio_requirements()
    else:
        requirements = _installed_fileio_requirements()
    assert len(requirements) == 1
    _assert_expected_fileio_requirement(requirements[0])
    return requirements[0]


def probe_anyfileio_public_contract(
    *, metadata_mode: str, temporary_root: Path | None = None
) -> dict[str, Any]:
    import anyfileio
    import anygeometry
    import anymaterial
    import anymesher
    import anysolver
    from anysolver import external_references

    modules = {
        "ANYsolver": anysolver,
        "ANYmaterial": anymaterial,
        "ANYgeometry": anygeometry,
        "ANYmesher": anymesher,
        "ANYfileio": anyfileio,
    }
    expected_variables = {
        "ANYsolver": "EXPECTED_ANYSOLVER_VERSION",
        "ANYmaterial": "EXPECTED_ANYMATERIAL_VERSION",
        "ANYgeometry": "EXPECTED_ANYGEOMETRY_VERSION",
        "ANYmesher": "EXPECTED_ANYMESHER_VERSION",
        "ANYfileio": "EXPECTED_ANYFILEIO_VERSION",
    }
    workspace_raw = os.environ.get("GITHUB_WORKSPACE")
    if metadata_mode == "installed":
        assert workspace_raw is not None
    for distribution_name, module in modules.items():
        expected = os.environ.get(expected_variables[distribution_name])
        if metadata_mode == "installed":
            assert expected is not None, expected_variables[distribution_name]
        if expected is not None:
            assert module.__version__ == expected
        if metadata_mode == "installed":
            distribution = metadata.distribution(distribution_name)
            assert distribution.version == expected
            distribution_root = Path(distribution.locate_file("")).resolve()
            origin = Path(module.__file__).resolve()
            assert _is_beneath(origin, distribution_root)
            assert not _is_beneath(origin, Path(workspace_raw))
            assert not _is_beneath(distribution_root, Path(workspace_raw))

    symbols = (
        "SesamFemDocument",
        "FemRawRecord",
        "CalculixParsedResults",
        "read_sesam_fem_document",
        "write_sesam_fem_document",
        "parse_frd",
        "parse_dat",
        "merge_results",
    )
    assert all(hasattr(anyfileio, name) for name in symbols)
    assert anysolver.SesamFemDocument is anyfileio.SesamFemDocument
    assert anysolver.FemRawRecord is anyfileio.FemRawRecord
    assert anysolver.CalculixParsedResults is anyfileio.CalculixParsedResults
    assert external_references.parse_calculix_frd is anyfileio.parse_frd
    assert external_references.parse_calculix_dat is anyfileio.parse_dat
    assert external_references.merge_calculix_results is anyfileio.merge_results

    def round_trip(root: Path) -> None:
        source = root / "minimal.fem"
        target = root / "roundtrip.fem"
        source.write_text("IDENT          1\nIEND\n", encoding="ascii")
        document = anyfileio.read_sesam_fem_document(source)
        assert isinstance(document, anyfileio.SesamFemDocument)
        anyfileio.write_sesam_fem_document(document, target)
        reread = anyfileio.read_sesam_fem_document(target)
        assert isinstance(reread, anyfileio.SesamFemDocument)

    if temporary_root is None:
        with tempfile.TemporaryDirectory() as directory:
            round_trip(Path(directory))
    else:
        round_trip(temporary_root)

    requirement = _metadata_requirement(metadata_mode)
    origin = Path(anyfileio.__file__).resolve()
    return {
        "anyfileio_version": anyfileio.__version__,
        "anyfileio_origin": str(origin),
        "anysolver_version": anysolver.__version__,
        "anysolver_origin": str(Path(anysolver.__file__).resolve()),
        "anymaterial_version": anymaterial.__version__,
        "anymaterial_origin": str(Path(anymaterial.__file__).resolve()),
        "anygeometry_version": anygeometry.__version__,
        "anygeometry_origin": str(Path(anygeometry.__file__).resolve()),
        "anymesher_version": anymesher.__version__,
        "anymesher_origin": str(Path(anymesher.__file__).resolve()),
        "requirement": requirement,
        "metadata_mode": metadata_mode,
    }


def test_source_declares_exact_anyfileio_compatibility_range() -> None:
    assert _source_fileio_requirements() == [EXPECTED_REQUIREMENT]


def test_source_declares_coordinated_s3_foundation_floors() -> None:
    dependencies = _project(Path(__file__).resolve().parents[1])["dependencies"]
    selected = {
        canonicalize_name(Requirement(item).name): item
        for item in dependencies
        if canonicalize_name(Requirement(item).name)
        in {"anymaterial", "anymesher", "anyfileio"}
    }
    assert selected == {
        "anymaterial": "ANYmaterial>=0.1.1,<0.2",
        "anymesher": "ANYmesher>=0.3.2,<0.4",
        "anyfileio": "ANYfileio>=0.2.1,<0.3",
    }


def test_fileio_requirement_accepts_canonicalized_specifier_order() -> None:
    _assert_expected_fileio_requirement("ANYfileio<0.3,>=0.2.1")


def test_current_source_origins_and_complete_graphs() -> None:
    import pytest

    ledgers = _source_ledgers()
    if ledgers is None:
        pytest.skip("frozen source ledgers are supplied by the focused gate")
    versions, roots = ledgers

    import anyfileio
    import anygeometry
    import anymaterial
    import anymesher
    import anysolver

    modules = {
        "anysolver": anysolver,
        "anymaterial": anymaterial,
        "anygeometry": anygeometry,
        "anymesher": anymesher,
        "anyfileio": anyfileio,
    }
    for name, module in modules.items():
        _assert_module_identity(name, module, versions, roots)
    _assert_complete_source_graphs(roots)


def test_anyfileio_public_contract_used_by_anysolver(tmp_path: Path) -> None:
    result = probe_anyfileio_public_contract(
        metadata_mode="source", temporary_root=tmp_path
    )
    assert result["metadata_mode"] == "source"


def test_workflows_pin_compatibility_graph_and_actions() -> None:
    root = Path(__file__).resolve().parents[1]
    ci = (root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    publish = (root / ".github" / "workflows" / "publish.yml").read_text(
        encoding="utf-8"
    )
    action_refs = {
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
        "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33",
    }
    combined = ci + publish
    assert set(re.findall(r"(?m)^\s*- uses: (\S+)\s*$", combined)) == action_refs

    ci_header, ci_jobs = ci.split("jobs:\n", maxsplit=1)
    assert ci_header == (
        "name: Tests\n\non:\n  push:\n  pull_request:\n\n"
        "# Existing lanes retain the reviewed stable sibling graph.\n"
        "# The final-candidate lane separately freezes the release graph used by authority.\n\n"
    )
    assert re.findall(r"(?m)^  ([a-z0-9-]+):\n", ci_jobs) == [
        "pytest",
        "anymesher-compatibility",
        "anyfileio-compatibility",
        "wheel",
        "numba",
        "pardiso",
        "final-candidate-graph",
    ]
    publish_header, publish_jobs = publish.split("jobs:\n", maxsplit=1)
    assert publish_header == (
        "name: Publish\n\non:\n  workflow_dispatch:\n  release:\n"
        "    types: [published]\n\n"
    )
    assert re.findall(r"(?m)^  ([a-z0-9-]+):\n", publish_jobs) == [
        "dependency-gate",
        "build",
        "release-assets",
        "testpypi",
        "pypi",
    ]

    sibling_refs = {
        "07124405ce0160437928e9b0c3c7a0d530c1f5de",
        "2b6431c291c8f571803484f69d08807875996b72",
        "97b06b0cfc72179c4f6522f9077d8a1d91911d61",
        "c06c8fa9ca58f282941a921548bf8303a8ddd084",
    }
    final_candidate_refs = {
        "0591d4833806ee95bdd710c352a1f836af7b910e",
        "254ce138dfc72d48a971035b028ba2dc5e9f082b",
        "449a445746152c49315615ff8a1fc232db75afb9",
        "4a98b84879d5ccdc95052f626c4f96ed3340fbb7",
    }
    ci_hashes = set(re.findall(r"\b[0-9a-f]{40}\b", ci))
    assert ci_hashes == {
        "11d5960a326750d5838078e36cf38b85af677262",
        "a26af69be951a213d495a4c3e4e4022e16d87065",
    } | sibling_refs | final_candidate_refs
    assert "RE" + "BIND_FINAL" not in ci
    assert set(re.findall(r"\b[0-9a-f]{40}\b", publish)) == {
        "11d5960a326750d5838078e36cf38b85af677262",
        "a26af69be951a213d495a4c3e4e4022e16d87065",
        "ea165f8d65b6e75b540449e92b4886f43607fa02",
        "d3f86a106a0bac45b974a628896c90dbdf5c8093",
        "dc37677b2e1c63e2034f94d8a5b11f265b73ba33",
    }

    def job_block(workflow: str, name: str) -> str:
        match = re.search(
            rf"(?ms)^  {re.escape(name)}:\n.*?(?=^  [a-z0-9-]+:\n|\Z)",
            workflow,
        )
        assert match is not None, name
        return match.group(0)

    checkout_ref = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
    setup_ref = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
    upload_ref = "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
    download_ref = "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093"
    publish_ref = (
        "pypa/gh-action-pypi-publish@"
        "dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
    )

    def action_sequence(block: str) -> list[str]:
        return re.findall(r"(?m)^      - uses: (\S+)\s*$", block)

    for name in (
        "pytest",
        "anymesher-compatibility",
        "anyfileio-compatibility",
        "wheel",
        "numba",
        "pardiso",
        "final-candidate-graph",
    ):
        assert action_sequence(job_block(ci, name)) == [checkout_ref] * 5 + [
            setup_ref
        ]
    assert action_sequence(job_block(publish, "dependency-gate")) == [setup_ref]
    assert action_sequence(job_block(publish, "build")) == [
        checkout_ref,
        setup_ref,
        upload_ref,
    ]
    assert action_sequence(job_block(publish, "release-assets")) == [
        checkout_ref,
        upload_ref,
    ]
    assert action_sequence(job_block(publish, "testpypi")) == [
        download_ref,
        publish_ref,
    ]
    assert action_sequence(job_block(publish, "pypi")) == [
        download_ref,
        publish_ref,
    ]

    checkout_pattern = re.compile(
        rf"(?m)^      - uses: {re.escape(checkout_ref)}\n"
        r"        with:\n"
        r"          repository: (\S+)\n"
        r"          ref: (.+)\n"
        r"          path: (\S+)\n"
        r"          persist-credentials: false$"
    )
    current_checkouts = [
        (
            "audunarn/ANYmaterial",
            "2b6431c291c8f571803484f69d08807875996b72",
            ".ecosystem/ANYmaterial",
        ),
        (
            "audunarn/ANYgeometry",
            "97b06b0cfc72179c4f6522f9077d8a1d91911d61",
            ".ecosystem/ANYgeometry",
        ),
        (
            "audunarn/ANYmesh",
            "c06c8fa9ca58f282941a921548bf8303a8ddd084",
            ".ecosystem/ANYmesh",
        ),
        (
            "audunarn/ANYfileIO",
            "07124405ce0160437928e9b0c3c7a0d530c1f5de",
            ".ecosystem/ANYfileIO",
        ),
    ]
    compatibility_checkouts = {
        "anymesher-compatibility": [
            current_checkouts[0],
            (
                "audunarn/ANYfileIO",
                "${{ matrix.anyfileio-ref }}",
                ".ecosystem/ANYfileIO",
            ),
            (
                "audunarn/ANYgeometry",
                "${{ matrix.anygeometry-ref }}",
                ".ecosystem/ANYgeometry",
            ),
            (
                "audunarn/ANYmesh",
                "${{ matrix.anymesher-ref }}",
                ".ecosystem/ANYmesh",
            ),
        ],
        "anyfileio-compatibility": [
            current_checkouts[0],
            (
                "audunarn/ANYgeometry",
                "${{ matrix.anygeometry-ref }}",
                ".ecosystem/ANYgeometry",
            ),
            (
                "audunarn/ANYmesh",
                "${{ matrix.anymesher-ref }}",
                ".ecosystem/ANYmesh",
            ),
            (
                "audunarn/ANYfileIO",
                "${{ matrix.anyfileio-ref }}",
                ".ecosystem/ANYfileIO",
            ),
        ],
    }
    assert checkout_pattern.findall(job_block(ci, "pytest")) == current_checkouts
    for name in ("wheel", "numba", "pardiso"):
        block = job_block(ci, name)
        assert checkout_pattern.findall(block) == current_checkouts
        assert block.count(checkout_ref) == 5
    pytest_block = job_block(ci, "pytest")
    numba_block = job_block(ci, "numba")
    numba_test_install = 'python -m pip install -e ".[dev,numba]"'
    assert pytest_block.count(numba_test_install) == 1
    assert numba_block.count(numba_test_install) == 1
    for name, expected in compatibility_checkouts.items():
        block = job_block(ci, name)
        actual = checkout_pattern.findall(block)
        assert len(actual) == len(expected)
        for actual_row, expected_row in zip(actual, expected, strict=True):
            assert actual_row[0] == expected_row[0]
            assert actual_row[2] == expected_row[2]
            assert actual_row[1] == expected_row[1]
        assert block.count(checkout_ref) == 5
        probe = block.split(
            "      - name: Probe the installed endpoint outside the checkout\n",
            maxsplit=1,
        )[1]
        assert "python -m pip install $wheel[0].FullName" in probe
        assert "pip install --no-deps" not in probe
        assert probe.index("python -m pip install $wheel[0].FullName") < probe.index(
            "python -m pip check"
        )
        assert "--metadata-mode installed" in probe

    mesh_job = job_block(ci, "anymesher-compatibility")
    fileio_job = job_block(ci, "anyfileio-compatibility")
    wheel_job = job_block(ci, "wheel")

    wheel_target_marker = (
        "      - name: Install wheel and pinned siblings into a clean target\n"
    )
    wheel_import_marker = (
        "      - name: Import the installed wheel without site packages\n"
    )
    assert wheel_job.count(wheel_target_marker) == 1
    assert wheel_job.count(wheel_import_marker) == 1
    wheel_target_tail = wheel_job.split(wheel_target_marker, maxsplit=1)[1]
    wheel_target_step, separator, wheel_import_step = wheel_target_tail.partition(
        wheel_import_marker
    )
    assert separator
    assert wheel_target_step == (
        "        run: >-\n"
        '          python -c "import glob, subprocess, sys;\n'
        "          subprocess.check_call([sys.executable, '-m', 'pip', 'install',\n"
        "          '--target', '.wheel-smoke', '.ecosystem/ANYmaterial',\n"
        "          '.ecosystem/ANYgeometry', '.ecosystem/ANYmesh', '.ecosystem/ANYfileIO',\n"
        "          *glob.glob('dist/*.whl')])\"\n"
    )
    assert "--no-deps" not in wheel_target_step
    assert wheel_import_step.count("python -S -c") == 1
    assert wheel_import_step.count("str(Path('.wheel-smoke').resolve())") == 1

    def matrix_rows(block: str) -> str:
        marker = "      matrix:\n        include:\n"
        assert block.count(marker) == 1
        tail = block.split(marker, maxsplit=1)[1]
        rows, separator, _ = tail.partition("\n\n    steps:\n")
        assert separator
        return rows

    assert matrix_rows(mesh_job) == "\n".join(
        (
            '          - anymesher-version: "0.3.2"',
            "            anymesher-ref: c06c8fa9ca58f282941a921548bf8303a8ddd084",
            '            anygeometry-version: "0.4.1"',
            "            anygeometry-ref: 97b06b0cfc72179c4f6522f9077d8a1d91911d61",
            '            anyfileio-version: "0.2.1"',
            "            anyfileio-ref: 07124405ce0160437928e9b0c3c7a0d530c1f5de",
            "            anyfileio-install: .ecosystem/ANYfileIO[semantics]",
        )
    )
    assert matrix_rows(fileio_job) == "\n".join(
        (
            '          - anyfileio-version: "0.2.1"',
            "            anyfileio-ref: 07124405ce0160437928e9b0c3c7a0d530c1f5de",
            "            anyfileio-install: .ecosystem/ANYfileIO[semantics]",
            '            anymesher-version: "0.3.2"',
            "            anymesher-ref: c06c8fa9ca58f282941a921548bf8303a8ddd084",
            '            anygeometry-version: "0.4.1"',
            "            anygeometry-ref: 97b06b0cfc72179c4f6522f9077d8a1d91911d61",
        )
    )

    def probe_environment(block: str) -> str:
        probe = block.split(
            "      - name: Probe the installed endpoint outside the checkout\n",
            maxsplit=1,
        )[1]
        marker = "        env:\n"
        assert probe.count(marker) == 1
        environment, separator, _ = probe.split(marker, maxsplit=1)[1].partition(
            "        run: |\n"
        )
        assert separator
        return environment

    assert probe_environment(mesh_job) == "\n".join(
        (
            '          EXPECTED_ANYSOLVER_VERSION: "0.4.0"',
            '          EXPECTED_ANYMATERIAL_VERSION: "0.1.1"',
            "          EXPECTED_ANYMESHER_VERSION: ${{ matrix.anymesher-version }}",
            "          EXPECTED_ANYGEOMETRY_VERSION: ${{ matrix.anygeometry-version }}",
            "          EXPECTED_ANYFILEIO_VERSION: ${{ matrix.anyfileio-version }}",
            "",
        )
    )
    assert probe_environment(fileio_job) == "\n".join(
        (
            '          EXPECTED_ANYSOLVER_VERSION: "0.4.0"',
            '          EXPECTED_ANYMATERIAL_VERSION: "0.1.1"',
            "          EXPECTED_ANYFILEIO_VERSION: ${{ matrix.anyfileio-version }}",
            "          EXPECTED_ANYMESHER_VERSION: ${{ matrix.anymesher-version }}",
            "          EXPECTED_ANYGEOMETRY_VERSION: ${{ matrix.anygeometry-version }}",
            "",
        )
    )
    for value in sibling_refs:
        assert mesh_job.count(value) == 1
        assert fileio_job.count(value) == 1
    assert mesh_job.count("          - anymesher-version:") == 1
    assert fileio_job.count("          - anyfileio-version:") == 1
    expected_install = (
        "python -m pip install .ecosystem/ANYmaterial .ecosystem/ANYgeometry "
        '.ecosystem/ANYmesh "${{ matrix.anyfileio-install }}"'
    )
    assert mesh_job.count(expected_install) == 1
    assert fileio_job.count(expected_install) == 1

    def job_preamble(block: str) -> str:
        preamble, separator, _ = block.partition("    steps:\n")
        assert separator
        return preamble

    assert job_preamble(job_block(publish, "dependency-gate")) == (
        "  dependency-gate:\n"
        "    name: Verify sibling releases on target index\n"
        "    runs-on: ubuntu-latest\n"
    )
    assert job_preamble(job_block(publish, "build")) == (
        "  build:\n"
        "    if: github.event_name == 'workflow_dispatch'\n"
        "    needs: dependency-gate\n"
        "    runs-on: ubuntu-latest\n"
    )
    assert job_preamble(job_block(publish, "release-assets")) == (
        "  release-assets:\n"
        "    if: github.event_name == 'release'\n"
        "    needs: dependency-gate\n"
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      contents: read\n"
    )
    assert job_preamble(job_block(publish, "testpypi")) == (
        "  testpypi:\n"
        "    if: github.event_name == 'workflow_dispatch'\n"
        "    needs: build\n"
        "    runs-on: ubuntu-latest\n"
        "    environment:\n"
        "      name: testpypi\n"
        "      url: https://test.pypi.org/p/ANYsolver\n"
        "    permissions:\n"
        "      id-token: write\n"
    )
    assert job_preamble(job_block(publish, "pypi")) == (
        "  pypi:\n"
        "    if: github.event_name == 'release'\n"
        "    needs: release-assets\n"
        "    runs-on: ubuntu-latest\n"
        "    environment:\n"
        "      name: pypi\n"
        "      url: https://pypi.org/p/ANYsolver\n"
        "    permissions:\n"
        "      id-token: write\n"
    )

    dependency_job = job_block(publish, "dependency-gate")
    assert dependency_job.count(
        "TARGET_INDEX_URL: ${{ github.event_name == 'release' && "
        "'https://pypi.org/simple' || 'https://test.pypi.org/simple' }}"
    ) == 1
    testpypi_job = job_block(publish, "testpypi")
    pypi_job = job_block(publish, "pypi")
    assert testpypi_job.count(
        "repository-url: https://test.pypi.org/legacy/"
    ) == 1
    assert "repository-url:" not in pypi_job
    assert publish.count("repository-url:") == 1
    release_assets_job = job_block(publish, "release-assets")
    embedded_marker = "          python - <<'PY'\n"
    embedded_verifier = release_assets_job.split(embedded_marker, maxsplit=1)[1].split(
        "          PY\n", maxsplit=1
    )[0]
    compile(
        textwrap.dedent(embedded_verifier),
        "publish.yml:release-verifier",
        "exec",
    )
    assert "gh release download" in release_assets_job
    assert "SHA256SUMS" in release_assets_job
    assert "hashlib.sha256" in release_assets_job
    assert "REBIND_FINAL_ACCEPTED" not in publish
    assert publish.count('"REBIND_FINAL"') == 1
    assert (
        'Path("docs/reference_cases/e4_pl_s3_release_ledger.json")'
        in release_assets_job
    )
    assert "the canonical S3 release ledger is absent" in release_assets_job
    assert '["git", "show", f"HEAD:{ledger_path.as_posix()}"]' in release_assets_job
    assert "ledger_raw != committed_raw" in release_assets_job
    assert "object_pairs_hook=strict_pairs" in release_assets_job
    assert "parse_constant=reject_constant" in release_assets_job
    assert "ledger_raw != canonical" in release_assets_job
    assert "def git_environment():" in release_assets_job
    assert 'environment["GIT_CONFIG_NOSYSTEM"] = "1"' in release_assets_job
    assert 'environment["GIT_CONFIG_GLOBAL"] = os.devnull' in release_assets_job
    assert '"GIT_CONFIG_PARAMETERS"' in release_assets_job
    assert 'environment["GIT_ATTR_NOSYSTEM"] = "1"' in release_assets_job
    assert 'environment["GIT_NO_REPLACE_OBJECTS"] = "1"' in release_assets_job
    assert '"core.attributesFile="' in release_assets_job
    assert '"refs/replace"' in release_assets_job
    assert '"info/grafts"' in release_assets_job
    assert '"info/attributes"' in release_assets_job
    assert "Git replacement objects are forbidden" in release_assets_job
    assert "Git grafts are forbidden" in release_assets_job
    assert "Git info attributes are forbidden" in release_assets_job
    assert '"--no-ext-diff"' in release_assets_job
    assert '"--no-renames"' in release_assets_job
    assert release_assets_job.count("subprocess.run(") == 1
    assert release_assets_job.count("git_run(") >= 15
    optimization_contract = json.loads(
        (
            root
            / "docs"
            / "reference_cases"
            / "e4_pl_s3_qualification_optimization_v4_contract.json"
        ).read_text(encoding="utf-8")
    )
    release_ledger_schema = optimization_contract["release_authority"][
        "release_ledger_schema"
    ]
    assert release_ledger_schema == "anysolver.e4-pl-s3-release-ledger-v4"
    assert f'"{release_ledger_schema}"' in release_assets_job
    assert (
        '"anysolver.e4-pl-s3-qualification-candidate-binding-v4"'
        in release_assets_job
    )
    assert (
        '"anysolver.e4-pl-s3-qualification-authorization-v4"'
        in release_assets_job
    )
    for candidate in (
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
    ):
        assert f'"{candidate}"' in release_assets_job
    assert '"s3-v4-authority-reviewer"' in release_assets_job
    assert '"s3-v4-science-reviewer"' in release_assets_job
    assert '"s3-v4-post-qualification-reviewer"' in release_assets_job
    assert 'for token in ("PLACEHOLDER", "REBIND_FINAL", "TO_BE_REBOUND")' in release_assets_job
    assert '["git", "rev-list", "--parents", "-n", "1", "HEAD"]' in release_assets_job
    assert '["git", "rev-parse", f"{source_commit}^{{tree}}"]' in release_assets_job
    assert '"--name-status"' in release_assets_job
    assert 'changed != [f"A\\t{ledger_path.as_posix()}"]' in release_assets_job
    assert 'exact_keys(artifacts, {"wheel"}' in release_assets_job
    assert 'exact_keys(row, {"filename", "sha256"}' in release_assets_job
    assert 're.fullmatch(r"[0-9A-F]{64}", digest)' in release_assets_job
    assert "recorded_hashes != accepted_hashes" in release_assets_job
    assert "actual != accepted_hashes[name]" in release_assets_job
    assert "two-cycle qualification was not accepted" in release_assets_job
    assert "release wheel differs from the qualified candidate" in release_assets_job
    assert "resource completion authority differs" in release_assets_job
    assert 'raise SystemExit(f"{name} paths or order differ")' in release_assets_job
    assert "e4_pl_s3_v3_cycle_1_scientific.json" in release_assets_job
    assert "e4_pl_s3_v3_cycle_2_scientific.json" in release_assets_job
    assert "e4_pl_s3_v3_cycle_1_process_binding.json" in release_assets_job
    assert "e4_pl_s3_v3_cycle_2_process_binding.json" in release_assets_job
    assert 'cycle_set["process_binding_sha256"] != process_hashes' in release_assets_job
    assert "expected_scientific_fields" in release_assets_job
    assert "anysolver.e4-pl-s3-default-activation-scientific-v3" in release_assets_job
    assert "expected_worker_gate_names" in release_assets_job
    assert "expected_coverage_values" in release_assets_job
    assert "set(assignments) != expected_worker_set" in release_assets_job
    assert 'worker["status"] != "COMPLETE"' in release_assets_job
    assert (
        'worker["assignment_sha256"] != assignments[expected_worker]'
        in release_assets_job
    )
    assert 'evidence["scientific_payload_sha256"]' in release_assets_job
    assert "anysolver.e4-pl-s3-resource-completion-v3" in release_assets_job
    assert "anysolver.e4-pl-s3-resource-terminal-snapshot-v2" in release_assets_job
    assert "e4_pl_s3_v3_resource_ledger_snapshot.md" in release_assets_job
    assert "resource ledger request lifecycle differs" in release_assets_job
    assert "resource terminal row is malformed" in release_assets_job
    assert "post-qualification review differs" in release_assets_job
    assert "post-qualification release authorization differs" in release_assets_job
    assert "anysolver.e4-pl-s3-release-authorization-v2" in release_assets_job
    assert "integration_parents[2] != qualified_solver_commit" in release_assets_job
    assert "integration_tree != qualified_solver_tree" in release_assets_job
    assert '"refs/remotes/origin/main"' in release_assets_job
    assert (
        'for protected_commit in (integration_commit, source_commit, "HEAD"):'
        in release_assets_job
    )
    assert (
        "GITHUB_PROTECTED_ORIGIN_MAIN_AND_POST_QUALIFICATION_REVIEW"
        in release_assets_job
    )
    assert "QUALIFIED_S3_DEFAULT_AND_ACCEPTED_WHEEL_PUBLICATION_ONLY" in release_assets_job
    assert '"PROVISIONAL_GO_E4_PL_S3_DEFAULT_ACTIVATION"' in release_assets_job
    assert "gh release download \"$EXPECTED_TAG\"" in release_assets_job
    assert "--pattern" not in release_assets_job
    assert "anysolver-0.4.0.tar.gz" not in release_assets_job
    assert "ref: ${{ github.event.release.tag_name }}" in release_assets_job
    assert "fetch-depth: 0" in release_assets_job
    assert "persist-credentials: false" in release_assets_job
    assert "python -m build" not in release_assets_job
    assert "python -m build" not in pypi_job
    assert "name: qualified-release-distributions" in release_assets_job
    assert "name: qualified-release-distributions" in pypi_job
    assert "EXPECTED_TAG: v0.4.0" in release_assets_job
    assert "if [ \"$RELEASE_TAG\" != \"$EXPECTED_TAG\" ]" in release_assets_job
    assert "anysolver-0.4.0-py3-none-any.whl" in release_assets_job
    assert "set(names) != expected_names" in release_assets_job
    assert "expected_dependencies = {" in release_assets_job
    assert 'message.get("Version") != "0.4.0"' in release_assets_job
    assert "dependency floors differ" in release_assets_job
    assert "zipfile.ZipFile" in release_assets_job
    assert "--pattern '*.whl'" not in release_assets_job
    assert "--pattern '*.tar.gz'" not in release_assets_job

    permission_bodies: list[str] = []
    for name in (
        "dependency-gate",
        "build",
        "release-assets",
        "testpypi",
        "pypi",
    ):
        block = job_block(publish, name)
        match = re.search(
            r"(?m)^    permissions:\n((?:^      [^\n]*\n)+)", block
        )
        if match is not None:
            permission_bodies.append(match.group(1))
    assert permission_bodies == [
        "      contents: read\n",
        "      id-token: write\n",
        "      id-token: write\n",
    ]
    assert "permissions:" not in job_block(publish, "dependency-gate")
    assert "permissions:" not in job_block(publish, "build")
    assert "SIBLINGS" not in ci
    assert "git+https://" not in ci
    final_candidate_job = job_block(ci, "final-candidate-graph")
    for ref in final_candidate_refs:
        assert final_candidate_job.count(f"ref: {ref}") == 1
    for ref in sibling_refs:
        assert ref not in final_candidate_job
    for token in (
        'EXPECTED_ANYSOLVER_VERSION: "0.4.0"',
        'EXPECTED_ANYMATERIAL_VERSION: "0.1.1"',
        'EXPECTED_ANYGEOMETRY_VERSION: "0.4.1"',
        'EXPECTED_ANYMESHER_VERSION: "0.3.2"',
        'EXPECTED_ANYFILEIO_VERSION: "0.2.1"',
        "test_s3_default_activation.py",
        "test_e4_pl_s3_default_activation_v2.py",
        "test_e4_pl_default_activation.py",
    ):
        assert token in final_candidate_job
    assert ci.count("python -m pip check") == 9
    for requirement in (
        '"ANYmaterial>=0.1.1,<0.2"',
        '"ANYmesher>=0.3.2,<0.4"',
        '"ANYfileio>=0.2.1,<0.3"',
    ):
        assert publish.count(requirement) == 1


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    parser.add_argument(
        "--metadata-mode", choices=("source", "installed"), required=True
    )
    arguments = parser.parse_args()
    if not arguments.probe:
        parser.error("the standalone entry point requires --probe")
    print(
        json.dumps(
            probe_anyfileio_public_contract(
                metadata_mode=arguments.metadata_mode
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
