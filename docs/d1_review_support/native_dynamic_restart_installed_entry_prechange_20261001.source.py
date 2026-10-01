"""Build/install a source-bound development wheel and run two actual examples."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import zipfile

input_path = Path(sys.argv[1]).resolve()
record = json.loads(input_path.read_text(encoding="utf-8"))
root = Path(record["workspace"]).resolve()
artifact = Path(record["artifact_root"]).resolve()
assert Path.cwd().resolve() == root
for key, value in record["environment"].items():
    assert os.environ.get(key) == value, key


def verify():
    for item in record["sources"]:
        path = root / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], item["path"]


verify()
assert not artifact.exists()
artifact.mkdir()
pack = artifact / "source"
pack.mkdir()
shutil.copytree(root / "src", pack / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "*.pyc"))
for name in record["build_files"]:
    shutil.copy2(root / name, pack / name)
for name, args in (("build", [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(artifact / "wheel")]),):
    with (artifact / (name + ".log")).open("w", encoding="utf-8") as log:
        subprocess.run(args, cwd=pack, stdout=log, stderr=subprocess.STDOUT, check=True)
wheels = list((artifact / "wheel").glob("*.whl"))
assert len(wheels) == 1
wheel = wheels[0]
target = artifact / "target"
with (artifact / "install.log").open("w", encoding="utf-8") as log:
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-index", "--target", str(target), str(wheel)], stdout=log, stderr=subprocess.STDOUT, check=True)
installed = []
for item in record["sources"]:
    if item["path"].startswith("src/anysolver/") and item["path"].endswith(".py"):
        path = target / Path(item["path"]).relative_to("src")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], str(path)
        installed.append(item)
# No source-tree package was imported before target selection.
assert "anysolver" not in sys.modules
sys.path.insert(0, str(target))
import anysolver
import numpy
import scipy
from threadpoolctl import threadpool_info
assert Path(anysolver.__file__).resolve().is_relative_to(target)
examples = []
for relative in record["examples"]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        scope = runpy.run_path(str(root / relative))
        main = scope["main"]
        if "native_contact_free" in relative:
            original = main.__globals__["create_analysis"]
            owners = []
            def capture(*args, **kwargs):
                owner = original(*args, **kwargs)
                owners.append(owner)
                return owner
            main.__globals__["create_analysis"] = capture
            try:
                main()
            finally:
                main.__globals__["create_analysis"] = original
            assert len(owners) == 1 and owners[0]._context.stage_residual_tolerance == 1e-11
        else:
            result = main()
            assert result.status == "completed"
    payload = json.loads(output.getvalue())
    if "native_contact_free" in relative:
        assert payload["epoch"] == 2 and payload["time_seconds"] == .002
        assert payload["provenance"]["production_qualified"] is False
    examples.append({"path": relative, "output": payload})
for name, module in tuple(sys.modules.items()):
    if name == "anysolver" or name.startswith("anysolver."):
        assert Path(module.__file__).resolve().is_relative_to(target), name
verify()
summary = dict(status="PASS_INSTALLED_DEVELOPMENT_ROUTING_ONLY", scientific_acceptance=False,
    source_commit=record["source_commit"], installed_python_source_count=len(installed),
    input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
    wheel=str(wheel), wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    installed_target=str(target), python=sys.version, numpy=numpy.__version__, scipy=scipy.__version__,
    threadpools=threadpool_info(), examples=examples)
Path(record["summary_path"]).write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
print(json.dumps({key:summary[key] for key in ("status", "source_commit", "installed_python_source_count", "wheel_sha256")}))
