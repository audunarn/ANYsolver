"""Reconcile installed checks and finalize metadata without altering payloads."""
from pathlib import Path
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
BUILD = Path("C:/ANYworkspaceWork/beam-shell-incremental-delivery-20261020/build-v1")
BUNDLE = BUILD / "bundle"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(path):
    return {(case.attrib["classname"], case.attrib["name"]):
            "error" if case.find("error") is not None else
            "failed" if case.find("failure") is not None else
            "skipped" if case.find("skipped") is not None else "passed"
            for case in ET.parse(path).getroot().iter("testcase")}


first = cases(HERE / "installed-junit.xml")
fixed = cases(HERE / "installed-temp-fixture-junit.xml")
assert len(first) == 65 and list(first.values()).count("passed") == 64
assert len(fixed) == 1 and set(fixed.values()) == {"passed"}
assert set(fixed) == {key for key, status in first.items() if status == "error"}
combined = dict(first)
combined.update(fixed)
assert len(combined) == 65 and set(combined.values()) == {"passed"}
full = json.loads((HERE / "INSTALLED_VERIFICATION.json").read_text())
repair = json.loads((HERE / "INSTALLED_TEMP_FIXTURE.json").read_text())
assert repair["status"] == "PASS"
assert full["source_commit"] == repair["source_commit"]
assert full["version"] == repair["version"]
assert full["payload_files_verified"] == repair["payload_files_verified"] == 727
assert len(full["cli_runs"]) == 2
manifest = json.loads((BUNDLE / "MANIFEST.json").read_text())
for relative, digest in manifest["files"].items():
    assert sha(BUNDLE / relative) == digest, relative
packaging = json.loads((HERE / "PACKAGING_INPUTS.json").read_text())
for wheel in packaging["private_dependency_wheels"]:
    assert sha(BUNDLE / "wheelhouse" / Path(wheel["path"]).name) == wheel["sha256"]
unchanged = {path: digest for path, digest in manifest["files"].items() if path != "README.md"}
summary = dict(status="PASS_FOCUSED_INSTALLED_WORKFLOWS_ONLY", unique_tests=65,
    passed=65, failed=0, skipped=0, errors=0, real_cli_runs=2,
    source_commit=manifest["source_commit"], version=manifest["version"],
    solver_payload_files_verified=727,
    reconciliation="64 initial passes plus only the1 WinError5 temp-fixture error rerun successfully; no passed tests repeated",
    unchanged_artifact_identity=True, runtime=full,
    omitted=["serialized plastic checkpoint workflow"],
    scientific_gates="Director continuation and analytical accuracy remain open; no full-suite or qualification claim")
verification = BUNDLE / "verification"
verification.mkdir(exist_ok=False)
for source in ("INSTALLED_VERIFICATION.json", "INSTALLED_TEMP_FIXTURE.json",
               "installed-junit.xml", "installed-temp-fixture-junit.xml"):
    shutil.copyfile(HERE / source, verification / source)
(verification / "SUMMARY.json").write_text(json.dumps(summary, indent=2))
with (BUNDLE / "README.md").open("a", encoding="utf-8") as stream:
    stream.write("\nInstalled verification:65focused unique tests and both real preyield CLI runs pass "
                 "in fresh isolated WindowsPython3.12. All727installed solver payload files match "
                 "the built artifact. One system-temp fixture error was corrected with task-owned "
                 "temporary storage; the64passing tests were reused under unchanged payload hashes. "
                 "See verification/SUMMARY.json. This does not close the omitted plastic checkpoint "
                 "delivery or any historical scientific gate.\n")
for relative, digest in unchanged.items():
    assert sha(BUNDLE / relative) == digest
manifest.update(status="DELIVERED_CANDIDATE_PREYIELD_ONLY",
                installed_verification="verification/SUMMARY.json",
                finalization="Only README/manifest/verification metadata added; source, examples, tests, requirements, wheels and sdist unchanged")
manifest["files"] = {str(path.relative_to(BUNDLE)): sha(path)
                     for path in sorted(BUNDLE.rglob("*"))
                     if path.is_file() and path != BUNDLE / "MANIFEST.json"}
(BUNDLE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
final = BUILD / ("ANYsolver-beam-shell-" + manifest["version"] + "-verified.zip")
assert not final.exists()
with zipfile.ZipFile(final, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
    for path in sorted(BUNDLE.rglob("*")):
        if path.is_file():
            zipped.write(path, path.relative_to(BUNDLE))
delivery = dict(status=manifest["status"], source_commit=manifest["source_commit"],
    version=manifest["version"], bundle=str(final), sha256=sha(final), bytes=final.stat().st_size,
    focused_unique_passed=65, real_cli_runs_passed=2, payload_files_verified=727,
    runtime="Fresh WindowsPython3.12, JIToff, Numba1/allpools1, retired0; origins verified inside venv-v2",
    omitted_features=manifest["omitted_features"], scientific_clearance=False,
    source_and_artifact_code_unchanged_after_checks=True,
    original_build=json.loads((BUILD / "BUILD.json").read_text()),
    initial_temp_failure_retained=True, source_leaked_installation_retained=True,
    historical_budget_unchanged=True, published=False)
(HERE / "DELIVERY.json").write_text(json.dumps(delivery, indent=2))
print(json.dumps(delivery, indent=2))
