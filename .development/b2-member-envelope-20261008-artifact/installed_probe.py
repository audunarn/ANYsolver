"""Installed-wheel public B2 member-envelope development check."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from threadpoolctl import threadpool_info


root = Path(__file__).resolve().parents[2]
site = Path(sys.argv[1]).resolve()
wheel = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(site))
sys.path.append(str(root))

import anysolver  # noqa: E402
from anysolver import stiffened_shell as api  # noqa: E402

assert Path(anysolver.__file__).resolve().is_relative_to(site)
assert api.ExperimentalB2Q4PanelMemberResultantEnvelope.__name__.endswith("Envelope")
example = root / "examples/stiffened_shell_b2_physical_rigid_footprint.py"
spec = importlib.util.spec_from_file_location("b2_footprint_example", example)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.batch_workflow(10)
assert result["status"] == "completed", result
assert result["case_count"] == result["solve_count"] == 10, result
assert result["factorization_count"] == 1, result
assert result["member_resultant_envelope_count"] == 18, result
assert all(item["num_threads"] == 1 for item in threadpool_info())
print(json.dumps({
    "status": "PASSED", "imported_from": str(Path(anysolver.__file__).resolve()),
    "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
    "threadpools": threadpool_info(), "result": result,
}, indent=2))
