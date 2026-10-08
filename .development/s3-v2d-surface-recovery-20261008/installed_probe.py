"""Small public installed-wheel check for elastic mixed Q4/S3 recovery."""

import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np


site = Path(sys.argv[1]).resolve()
expected_wheel_sha256 = sys.argv[2]
wheel = Path(sys.argv[3]).resolve()
assert hashlib.sha256(wheel.read_bytes()).hexdigest() == expected_wheel_sha256
sys.path.insert(0, str(site))

import anysolver  # noqa: E402
from anysolver import FEModel, create_shell_element, recover_stress_result  # noqa: E402

assert Path(anysolver.__file__).resolve().is_relative_to(site)
model = FEModel("installed-mixed-q4-s3-recovery")
model.add_material("steel", 210.0e9, 0.3, density=7850.0)
coordinates = {
    1: (0.0, 0.0, 0.0),
    2: (1.0, 0.0, 0.0),
    3: (1.0, 1.0, 0.0),
    4: (0.0, 1.0, 0.0),
    5: (2.0, 0.0, 0.0),
    6: (2.0, 1.0, 0.0),
}
for node_id, coordinate in coordinates.items():
    model.add_node(node_id, *coordinate)
model.add_element(1, create_shell_element(1, [1, 2, 3, 4], "steel", thickness=0.07))
model.add_element(
    2,
    create_shell_element(
        2,
        [2, 5, 6],
        "steel",
        formulation="e4-pl-s3-v2d",
        thickness=0.07,
        reference_normal=(0.0, 0.0, 1.0),
    ),
)
displacement = np.zeros(model.mesh.dof_manager.total_dofs)
for node_id, (x, _y, _z) in coordinates.items():
    displacement[model.mesh.dof_manager.get_node_dofs(node_id)[0]] = 1.0e-4 * x
recovered = recover_stress_result(model, displacement).element_stresses
expected_xx = 210.0e9 * 1.0e-4 / (1.0 - 0.3**2)
for element_id, station_count in ((1, 4), (2, 3)):
    values = recovered[element_id]
    assert values["physical_stress_available"] is True
    assert values["membrane_xx"].shape == (station_count,)
    np.testing.assert_allclose(values["membrane_xx"], expected_xx, rtol=1.0e-11)
    assert values["von_mises"].shape == (station_count,)
print(
    json.dumps(
        {
            "status": "PASSED",
            "imported_from": str(Path(anysolver.__file__).resolve()),
            "wheel_sha256": expected_wheel_sha256,
            "site": str(site),
            "python": sys.executable,
            "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
            "element_ids": sorted(recovered),
            "station_counts": {str(k): int(len(v["von_mises"])) for k, v in recovered.items()},
        }
    )
)
