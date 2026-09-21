"""Bounded release gate for the accepted ANYsolver 0.4.7 artifact.

This gate verifies package identity and retained accepted performance evidence.
It does not rerun scientific qualification or promote experimental Armijo.
"""

from __future__ import annotations

import argparse
from email.parser import BytesParser
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.7"
TIMEOUT_SECONDS = 180
TERMINAL = "PROVISIONAL_GO_ANYSOLVER_0_4_7_BOUNDED_PERFORMANCE_RELEASE"
PERFORMANCE_FILES = {
    "static": (
        "docs/STATIC_RUNTIME_PERFORMANCE.md",
        "cbb92a59fddda847aa5953edaa7a2ed6be1ea64ed1995d415a59b72831bb31d1",
    ),
    "spectral": (
        "docs/SPECTRAL_MEDIUM_FINE_RESULTS.md",
        "89f1e32f580cbe4dddad9994fdea5f0c101fbfe4f9e352615b586c2af8a0bb02",
    ),
    "nonlinear": (
        "reports/performance/nonlinear_static_representative_adjudication.json",
        "4fab02974d4c815759a85920fc8a16a9c92149d2bc3643e08a6f76fd8d303593",
    ),
    "nonlinear_review": (
        "reports/performance/nonlinear_static_representative_independent_review.md",
        "02b1b7e509d880837af18585a1d1972278de5ddfa13318b70a6209aa71aef94e",
    ),
}
G7_FILES = {
    "contract": (
        "docs/reference_cases/b3_ge_g7_contract_v1.json",
        "ebc1731c1a75eb56c1f36d80b346863fd5e7607866fde2d6286cf501dc29d8fe",
    ),
    "confirmation": (
        "docs/reference_cases/b3_ge_g7_confirmation_v1.json",
        "ebdb4513bb637032335f4f8ab77f401ff3cdf5760052c16d7c1a6779a8ac8779",
    ),
    "review": (
        "docs/reference_cases/b3_ge_g7_review_v1.json",
        "9e9a7f6aa2b2387fcb514ece62e93f9530d615ffc9708819289039801a9fc97b",
    ),
    "status": (
        "docs/reference_cases/b3_ge_g7_status_v1.json",
        "c3faf028f9182db2dc65e9a941180f0bd083b3457b5abab51c3f2ea972244334",
    ),
}
RELEASE_DOCS = {
    "docs/ARCHITECTURE.md",
    "docs/ARC_LENGTH.md",
    "docs/B3_GE_PRODUCTION_OPT_IN.md",
    "docs/E4_PL_MIGRATION.md",
    "docs/GE_BEAM3_NATIVE_WORKFLOWS.md",
    "docs/NONLINEAR_PERFORMANCE.md",
    "docs/PERFORMANCE_ARCHITECTURE.md",
    "docs/QUALITY_CONTROL.md",
    "docs/THEORY.md",
    "docs/releases/ANYsolver_0.4.6.md",
    "docs/releases/ANYsolver_0.4.7.md",
}


class GateError(ValueError):
    """The bounded release gate was not satisfied."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise GateError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=lambda token: (_ for _ in ()).throw(
            GateError(f"nonfinite JSON value: {token}")
        ),
    )
    if not isinstance(value, dict):
        raise GateError(f"JSON root is not an object: {path}")
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")
    if raw != canonical:
        raise GateError(f"JSON is not canonical: {path}")
    return value, raw


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def _validate_g7() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    records: dict[str, dict[str, Any]] = {}
    for name, (relative, expected_hash) in G7_FILES.items():
        path = ROOT / relative
        value, raw = _strict_json(path)
        actual_hash = sha256(raw).hexdigest()
        if actual_hash != expected_hash:
            raise GateError(f"G7 {name} hash mismatch")
        loaded[name] = value
        records[name] = {
            "bytes": len(raw),
            "path": relative,
            "sha256": actual_hash,
        }
    if loaded["confirmation"].get("terminal") != "PROVISIONAL_GO_B3_GE_PRODUCTION_OPT_IN":
        raise GateError("G7 confirmation is not accepted")
    if loaded["review"].get("findings") != [] or loaded["review"].get("verdict") != (
        "ACCEPT_B3_GE_G7_PRODUCTION_OPT_IN_NO_P0_P1"
    ):
        raise GateError("G7 independent review is not accepted")
    status = loaded["status"]
    if (
        status.get("terminal") != "PROVISIONAL_GO_B3_GE_PRODUCTION_OPT_IN"
        or status.get("selector") != "b3-ge"
        or status.get("default_beam") != "LEGACY_B3"
        or status.get("public_default_routing_authorized") is not False
    ):
        raise GateError("G7 status boundary mismatch")
    contract = loaded["contract"]
    if (
        contract.get("selector") != "b3-ge"
        or contract.get("legacy_b3_default") is not True
        or contract.get("default_changed") is not False
    ):
        raise GateError("G7 contract boundary mismatch")
    return records


def _validate_performance_evidence() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for name, (relative, expected_hash) in PERFORMANCE_FILES.items():
        raw = (ROOT / relative).read_bytes()
        digest = sha256(raw).hexdigest()
        if digest != expected_hash:
            raise GateError(f"accepted {name} evidence hash mismatch")
        records[name] = {"path": relative, "bytes": len(raw), "sha256": digest}
    report = json.loads((ROOT / PERFORMANCE_FILES["nonlinear"][0]).read_bytes())
    decision = report["decision"]
    if (decision.get("completeness"), decision.get("performance"), decision.get("armijo")) != (
        "PASS", "GO", "NO-GO"
    ):
        raise GateError("nonlinear performance/Armijo decision mismatch")
    if not all(case.get("physical_match") for case in report["performance"].values()):
        raise GateError("nonlinear physical comparisons are incomplete")
    return records


def _git_identity(expected_commit: str) -> tuple[str, str]:
    if len(expected_commit) != 40:
        raise GateError("expected commit is not a full Git object ID")
    command = ["git", "-c", f"safe.directory={ROOT}", "-C", str(ROOT)]
    commit = subprocess.check_output(
        command + ["rev-parse", "HEAD"], text=True, timeout=TIMEOUT_SECONDS
    ).strip()
    tree = subprocess.check_output(
        command + ["rev-parse", "HEAD^{tree}"], text=True, timeout=TIMEOUT_SECONDS
    ).strip()
    dirty = subprocess.check_output(
        command + ["status", "--porcelain=v1", "--untracked-files=no"],
        text=True,
        timeout=TIMEOUT_SECONDS,
    ).strip()
    if commit != expected_commit:
        raise GateError("candidate commit mismatch")
    if dirty:
        raise GateError("candidate has tracked modifications")
    return commit, tree


def _source_runtime() -> dict[str, bytes]:
    root = ROOT / "src" / "anysolver"
    return {
        path.relative_to(ROOT / "src").as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    }


def _validate_wheel(path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    if path.name != f"anysolver-{VERSION}-py3-none-any.whl":
        raise GateError("wheel filename mismatch")
    if not path.is_file() or path.stat().st_size <= 0:
        raise GateError("wheel is missing or empty")
    source = _source_runtime()
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise GateError("wheel has duplicate entries")
        runtime_names = {
            name
            for name in names
            if name.startswith("anysolver/") and not name.endswith("/")
        }
        if runtime_names != set(source):
            raise GateError("wheel runtime path set differs from release source")
        for name, expected in source.items():
            if archive.read(name) != expected:
                raise GateError(f"wheel runtime differs from source: {name}")
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise GateError("wheel metadata count mismatch")
        headers = BytesParser().parsebytes(archive.read(metadata_names[0]))
        if headers["Name"].lower() != "anysolver" or headers["Version"] != VERSION:
            raise GateError("wheel metadata identity mismatch")
    return _file_record(path), source


def _validate_sdist(path: Path) -> dict[str, Any]:
    if path.name != f"anysolver-{VERSION}.tar.gz":
        raise GateError("source archive filename mismatch")
    if not path.is_file() or path.stat().st_size <= 0:
        raise GateError("source archive is missing or empty")
    with tarfile.open(path, "r:gz") as archive:
        files = [member.name for member in archive.getmembers() if member.isfile()]
    if len(files) != len(set(files)):
        raise GateError("source archive has duplicate entries")
    prefix = f"anysolver-{VERSION}/"
    if any(not name.startswith(prefix) for name in files):
        raise GateError("source archive has an unexpected root")
    relative = {name[len(prefix) :] for name in files}
    forbidden = (
        "docs/agent_plans/",
        "docs/reference_cases/",
        "reports/",
        "scripts/",
        "tests/",
    )
    if any(name.startswith(forbidden) for name in relative):
        raise GateError("source archive contains development-only material")
    docs = {name for name in relative if name.startswith("docs/")}
    if docs != RELEASE_DOCS:
        raise GateError("source archive documentation set mismatch")
    return {**_file_record(path), "file_count": len(files)}


def _installed_probe(wheel: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="anysolver-047-gate-") as raw:
        temporary = Path(raw)
        site = temporary / "site"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                str(site),
                str(wheel.resolve()),
            ],
            cwd=temporary,
            check=True,
            timeout=TIMEOUT_SECONDS,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        code = r'''import json, pathlib, sys
from importlib import metadata
site = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(site))
import anysolver
from anysolver import b3_ge
from anysolver.elements import ELEMENT_TYPES, QuadraticBeamElement, create_element
origin = pathlib.Path(anysolver.__file__).resolve()
if site not in origin.parents: raise RuntimeError("installed origin mismatch")
if anysolver.__version__ != "0.4.7": raise RuntimeError("installed version mismatch")
expected = {"ANYfileio":"0.3.2","ANYgeometry":"0.4.3","ANYmaterial":"0.2.0","ANYmesher":"0.5.0"}
actual = {name:metadata.version(name) for name in expected}
if actual != expected: raise RuntimeError(f"installed dependency identity mismatch: {actual!r}")
if b3_ge.SELECTOR != "b3-ge" or b3_ge.NAME != "B3-GE": raise RuntimeError("B3-GE identity mismatch")
if "b3-ge" in ELEMENT_TYPES: raise RuntimeError("B3-GE entered generic registry")
if type(create_element("quadratic_beam", 1, [1, 2, 3])) is not QuadraticBeamElement: raise RuntimeError("legacy B3 default changed")
from anysolver.nonlinear_static import NonlinearConvergenceSettings
if NonlinearConvergenceSettings().line_search == "armijo": raise RuntimeError("Armijo became a default")
if NonlinearConvergenceSettings(line_search="armijo").line_search != "armijo": raise RuntimeError("Armijo opt-in unavailable")
try: create_element("b3-ge", 2, [1, 2, 3])
except ValueError: pass
else: raise RuntimeError("B3-GE became a generic/default route")
print(json.dumps({"dependencies":actual,"installed_origin": True, "legacy_b3_default": True, "name": b3_ge.NAME, "selector": b3_ge.SELECTOR}, sort_keys=True, separators=(",", ":")))
'''
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code, str(site)],
            cwd=temporary,
            check=False,
            timeout=TIMEOUT_SECONDS,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise GateError(f"installed-wheel probe failed: {detail}")
        return json.loads(completed.stdout)


def run(wheel: Path, sdist: Path, expected_commit: str) -> dict[str, Any]:
    commit, tree = _git_identity(expected_commit)
    g7 = _validate_g7()
    performance = _validate_performance_evidence()
    wheel_record, runtime = _validate_wheel(wheel.resolve())
    sdist_record = _validate_sdist(sdist.resolve())
    installed = _installed_probe(wheel.resolve())
    return {
        "candidate": {"commit": commit, "tree": tree},
        "checks": {
            "g7_evidence_bound": True,
            "installed_origin": installed["installed_origin"],
            "legacy_b3_default": installed["legacy_b3_default"],
            "performance_evidence_retained": True,
            "release_documents_only": True,
            "runtime_matches_source": True,
        },
        "g7": g7,
        "performance_evidence": performance,
        "installed": installed,
        "runtime_file_count": len(runtime),
        "schema": "ANYSOLVER_0_4_7_BOUNDED_PERFORMANCE_RELEASE_GATE_V1",
        "sdist": sdist_record,
        "terminal": TERMINAL,
        "version": VERSION,
        "wheel": wheel_record,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--sdist", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run(args.wheel, args.sdist, args.expected_commit)
        raw = (
            json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("ascii")
        with args.output.open("xb") as stream:
            stream.write(raw)
    except (GateError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"bounded release gate failed: {error}", file=sys.stderr)
        return 1
    print(sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
