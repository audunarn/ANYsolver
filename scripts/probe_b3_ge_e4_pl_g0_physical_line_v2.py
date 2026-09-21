"""G0 F03-P-v2: enforce relative work-energy equality at small compliance."""

from __future__ import annotations

import json

import probe_b3_ge_e4_pl_g0_physical_line as prior


if __name__ == "__main__":
    gradient = prior.line_samples()
    rows = []
    for topology in ("Q4", "S3-V2D"):
        for n in (4,8,16):
            row = prior.specimen(n,topology,gradient)
            work, twice = row["compliance"], row["twice_energy"]
            relative = abs(work-twice)/max(abs(work),abs(twice),1e-30)
            assert row["status"] == "diagnostic_pass" and relative <= 1e-8
            row["relative_work_error"] = relative
            rows.append(row)
    print(json.dumps(dict(profile="G0-F03-P-v2",status="diagnostic_pass",results=rows),
                     sort_keys=True))
