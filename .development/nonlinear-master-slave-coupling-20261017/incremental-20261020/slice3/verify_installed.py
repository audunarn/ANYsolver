"""Verify the actual installed payload, runtime and focused delivered workflows."""
import hashlib
import importlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
BUNDLE = Path("C:/ANYworkspaceWork/beam-shell-incremental-delivery-20261020/build-v1/bundle")
MANIFEST = json.loads((BUNDLE / "MANIFEST.json").read_text())
finish_fixture = "--finish-temp-fixture" in sys.argv
assert sys.version_info[:2] == (3, 12)
assert os.environ["ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS"] == "0"
private = {name: importlib.import_module(name) for name in (
    "anysolver", "anysolver_results", "anymaterial", "anygeometry", "anymesher", "anyfileio")}
prefix = Path(sys.prefix).resolve()
assert all(Path(module.__file__).resolve().is_relative_to(prefix) for module in private.values())
assert version("ANYsolver") == MANIFEST["version"]
site = Path(private["anysolver"].__file__).resolve().parent.parent
for relative, expected in MANIFEST["source_files"].items():
    assert hashlib.sha256((site / relative).read_bytes()).hexdigest() == expected, relative
for relative, expected in MANIFEST["files"].items():
    assert hashlib.sha256((BUNDLE / relative).read_bytes()).hexdigest() == expected, relative
import numba
from threadpoolctl import threadpool_info
assert numba.config.DISABLE_JIT and numba.get_num_threads() == 1
assert all(pool["num_threads"] == 1 for pool in threadpool_info())
assert not any("C:/Github/ANYsolver/src" in path.replace("\\", "/") for path in sys.path)

cli_runs = []
for coupling in (() if finish_fixture else ("direct", "interpolated")):
    command = [sys.executable, "-I", str(BUNDLE / "examples/beam_shell_coupling.py"),
               "--coupling", coupling]
    start = time.perf_counter()
    with (HERE / (coupling + ".stdout.json")).open("wb") as out, (
            HERE / (coupling + ".stderr.txt")).open("wb") as err:
        process = subprocess.Popen(command, cwd=BUNDLE, stdout=out, stderr=err)
        try:
            code = process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, check=False)
            process.wait()
            raise
    assert code == 0, coupling
    payload = json.loads((HERE / (coupling + ".stdout.json")).read_text())
    assert payload["completed"] and payload["status"] == "completed"
    assert abs(payload["achieved_load_factor"]-1.) <= 1e-8
    assert payload["constraint_postcheck"]["status"] == "passed"
    cli_runs.append(dict(coupling=coupling, command=command, exit_code=code,
                         wall_seconds=time.perf_counter()-start, result=payload))

sys.path[:0] = [str(BUNDLE), str(BUNDLE / "tests")]
os.chdir(BUNDLE)
import pytest
class Counts:
    def pytest_sessionfinish(self, session, exitstatus):
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        self.values = dict(collected=session.testscollected, exit_code=int(exitstatus),
            outcomes={key: len(rows) for key, rows in reporter.stats.items()
                      if key in ("passed", "failed", "skipped", "error", "xfailed", "xpassed")})
counts = Counts()
label = "installed-temp-fixture" if finish_fixture else "installed"
temporary = HERE / (label + "-basetemp")
assert not temporary.exists(), "use a unique task-owned pytest temporary directory"
targets = ([str(BUNDLE / "tests/test_beam_shell_workflow.py") +
            "::test_cli_stdout_json_exit_status_and_output_file"] if finish_fixture else
           [str(BUNDLE / "tests" / name) for name in (
               "test_beam_shell_connection_options.py", "test_director_integrated_trace.py",
               "test_beam_shell_workflow.py")])
code = pytest.main(["-q", "--tb=short", "-o", "pythonpath=", "-p", "no:cacheprovider",
    "--basetemp=" + str(temporary), "--junitxml=" + str(HERE / (label + "-junit.xml")),
    *targets], plugins=[counts])
origins = {name: module.__file__ for name, module in sys.modules.copy().items()
           if (name == "anysolver" or name.startswith("anysolver."))
           and getattr(module, "__file__", None)}
assert all(Path(path).resolve().is_relative_to(prefix) for path in origins.values())
assert numba.config.DISABLE_JIT and numba.get_num_threads() == 1
assert all(pool["num_threads"] == 1 for pool in threadpool_info())
record = dict(status="PASS" if code == 0 else "FAIL", python=sys.version,
    executable=sys.executable, prefix=str(prefix), counts=counts.values,
    private_origins={name: module.__file__ for name, module in private.items()},
    solver_origins=origins, payload_files_verified=len(MANIFEST["source_files"]),
    jit_disabled=bool(numba.config.DISABLE_JIT), numba_threads=numba.get_num_threads(),
    numerical_pools=threadpool_info(), retired_selection=os.environ["ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS"],
    source_commit=MANIFEST["source_commit"], version=version("ANYsolver"),
    cli_runs=cli_runs,
    scientific_clearance=False, omitted=["serialized plastic checkpoint workflow"])
(HERE / ("INSTALLED_TEMP_FIXTURE.json" if finish_fixture else
         "INSTALLED_VERIFICATION.json")).write_text(json.dumps(record, indent=2))
raise SystemExit(code)
