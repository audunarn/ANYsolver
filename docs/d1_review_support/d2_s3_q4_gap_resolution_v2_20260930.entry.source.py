"""Frozen entry for the authorized new scalar resolution checks only."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path("C:/ANYworkspaceWork/ANYsolver-general-contact")
STEM = ROOT / "docs/d1_review_support/d2_s3_q4_gap_resolution_v2_20260930"
inputs = json.loads(Path(str(STEM)+".inputs.json").read_text(encoding="utf-8-sig"))
for key, value in inputs["environment"].items():
    assert os.environ.get(key) == value, (key, os.environ.get(key), value)
for relative, digest in inputs["source_sha256"].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == digest, relative
cache = Path(os.environ["NUMBA_CACHE_DIR"])
cache.mkdir(exist_ok=True)
probe = cache / "writability.probe"
with probe.open("x") as stream:
    stream.write("writable")
probe.unlink()
module = importlib.import_module("anysolver.general_contact.s3_q4_gap_resolution")
assert Path(module.__file__).resolve() == (ROOT/inputs["module"]).resolve()
import numpy
import pytest
identity = dict(python=sys.executable, numpy=numpy.__version__, pytest=pytest.__version__,
                module=module.__file__, environment=inputs["environment"],
                source_sha256=inputs["source_sha256"], cwd=os.getcwd())
print(json.dumps({"identity": identity}), flush=True)
reports = []
class Collect:
    def pytest_runtest_logreport(self, report):
        reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                            duration_seconds=report.duration,
                            properties=dict(report.user_properties),
                            failure=str(report.longrepr) if report.failed else None))
started = time.perf_counter()
result = pytest.main([inputs["test"], "-k", inputs["pytest_selection"], "-q", "--junitxml="+str(STEM)+".xml"], plugins=[Collect()])
raw = dict(status="PASS" if result == 0 else "NONPASS", exit_code=int(result),
           elapsed_seconds=time.perf_counter()-started, identity=identity,
           frozen_inputs=inputs, reports=reports,
           scope="Level A operand resolution controls; no coupled solve or acceptance")
with Path(str(STEM)+".raw.json").open("x", encoding="utf-8") as stream:
    json.dump(raw, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": raw["status"], "new_check_count": sum(r["when"] == "call" for r in reports)}), flush=True)
raise SystemExit(result)

