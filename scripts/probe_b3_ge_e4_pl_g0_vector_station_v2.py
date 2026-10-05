"""G0 F03-V-v2: apply the reference moment about the actual curved shell normal."""

from __future__ import annotations

import json

import numpy as np

import probe_b3_ge_e4_pl_g0_vector_station as prior


original_fixture = prior.fixture


def physical_normal_fixture(topology, curved):
    data = list(original_fixture(topology, curved))
    samples = data[3]
    axial = (samples[1]+samples[2]-samples[0]-samples[3])/2.
    transverse = (samples[2]+samples[3]-samples[0]-samples[1])/2.
    axis = axial/np.linalg.norm(axial)
    transverse -= axis*float(axis@transverse)
    lateral = transverse/np.linalg.norm(transverse)
    normal = np.cross(axis, lateral)
    assert normal[2] > .99 and (np.linalg.norm(normal[:2]) > 1e-3 if curved
                                   else np.linalg.norm(normal[:2]) < 1e-12)
    data[4] = np.column_stack((axis, lateral, normal))
    return tuple(data)


prior.fixture = physical_normal_fixture

if __name__ == "__main__":
    results = []
    for topology in ("Q4", "S3-V2D"):
        for curved in (False, True):
            result = prior.row(topology, curved)
            result["reference_normal_tilt"] = float(np.linalg.norm(
                physical_normal_fixture(topology, curved)[4][:2, 2]))
            results.append(result)
    passed = all(result["status"] == "diagnostic_pass" for result in results)
    print(json.dumps(dict(profile="G0-F03-V-v2",
                          status="diagnostic_pass" if passed else "failed",
                          results=results), sort_keys=True))
    raise SystemExit(0 if passed else 1)
