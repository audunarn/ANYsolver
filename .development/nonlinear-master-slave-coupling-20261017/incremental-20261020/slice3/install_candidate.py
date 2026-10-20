"""One fresh Windows Python3.12 installation of the committed candidate."""
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE / "PACKAGING_INPUTS.json").read_text())
build = Path("C:/ANYworkspaceWork/beam-shell-incremental-delivery-20261020/build-v1")
bundle = build / "bundle"
environment = build.parent / "venv-v2"
assert not environment.exists(), "preserve prior environments; select a new attempt"
commands = [[inputs["python312"], "-I", "-m", "venv", str(environment)]]
python = environment / "Scripts/python.exe"
commands.append([str(python), "-I", "-m", "pip", "install", "--find-links", str(bundle / "wheelhouse"),
    "-r", str(bundle / "requirements-tested.txt"),
    "ANYsolver==0.4.7+beam.shell.candidate.20261020.s3", "ANYsolver-results==2.1.1",
    "ANYmaterial==0.2.0", "ANYgeometry==0.4.3", "ANYmesher==0.5.0", "ANYfileio==0.3.2"])
records = []
for command in commands:
    start = time.perf_counter()
    result = subprocess.run(command, check=False, timeout=100)
    records.append(dict(command=command, exit_code=result.returncode,
                        wall_seconds=time.perf_counter()-start))
    (HERE / "INSTALL_COMMANDS.json").write_text(json.dumps(records, indent=2))
    if result.returncode:
        raise SystemExit(result.returncode)
print(json.dumps(dict(python=str(python), bundle=str(bundle))))
