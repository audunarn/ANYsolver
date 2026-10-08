"""Reusable source-bound pytest entry; the external supervisor owns resources.

Level A development only. A passing invocation creates no scientific acceptance.
Each input and raw output remains a separate immutable execution record.
"""
import hashlib
import json
import os
from pathlib import Path
import sys


record_path = Path(sys.argv[1]).resolve()
record = json.loads(record_path.read_text(encoding="utf-8"))
root = Path(record["workspace"]).resolve()
if Path.cwd().resolve() != root:
    raise RuntimeError("development check workspace differs from recorded input")
for key, value in record["environment"].items():
    if os.environ.get(key) != value:
        raise RuntimeError(f"development check environment mismatch: {key}")


def verify_sources():
    for item in record["sources"]:
        path = (root/item["path"]).resolve()
        if not path.is_relative_to(root):
            raise RuntimeError("source binding escapes the recorded workspace")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError(f"changed development source: {item['path']}")


verify_sources()
import anysolver
import numpy
import scipy
import pytest
from threadpoolctl import threadpool_info

if Path(anysolver.__file__).resolve() != root/"src/anysolver/__init__.py":
    raise RuntimeError("development check imported a different ANYsolver package")
print(json.dumps({"input_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
                  "anysolver_file": anysolver.__file__, "python": sys.version,
                  "numpy": numpy.__version__, "scipy": scipy.__version__,
                  "threadpools": threadpool_info()}, sort_keys=True), flush=True)
exit_code = pytest.main(record["pytest_args"])
verify_sources()
print(json.dumps({"pytest_exit_code": exit_code,
                  "verified_source_count": len(record["sources"])}), flush=True)
raise SystemExit(exit_code)
