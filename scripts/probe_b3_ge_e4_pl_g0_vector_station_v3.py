"""G0 F03-V-v3: signed unit normal-axis torque at the real shell rail frame."""

from __future__ import annotations

import json

import numpy as np

import probe_b3_ge_e4_pl_g0_vector_station_v2 as v2


if __name__ == "__main__":
    results = []
    for topology in ("Q4", "S3-V2D"):
        for curved in (False, True):
            row = v2.prior.row(topology, curved)
            data = v2.physical_normal_fixture(topology, curved)
            selected_normal = data[4][:, 2]  # moment axis; not the pose reference frame
            reference = np.zeros(v2.prior.COUNT)
            reference[v2.prior.MULTIPLIERS+3:] = data[1].frame(v2.prior.STATION).T@selected_normal
            work, _ = v2.prior.evaluate(reference, data)
            shell_force = work.gradient[:v2.prior.SHELL].reshape(6, 6)[:, :3]
            shell_moment = np.cross(data[0], shell_force).sum(axis=0)
            beam_moment = work.gradient[v2.prior.CELLS:v2.prior.CELLS+3]
            errors = dict(shell_force=float(np.linalg.norm(shell_force.sum(axis=0))),
                          shell_signed_unit_moment=float(np.linalg.norm(shell_moment+selected_normal)),
                          beam_signed_unit_moment=float(np.linalg.norm(beam_moment-selected_normal)))
            assert max(errors.values()) <= 1e-10, (topology, curved, errors)
            row.update(errors)
            results.append(row)
    passed = all(row["status"] == "diagnostic_pass" for row in results)
    print(json.dumps(dict(profile="G0-F03-V-v3",
                          status="diagnostic_pass" if passed else "failed",
                          results=results), sort_keys=True))
    raise SystemExit(0 if passed else 1)
