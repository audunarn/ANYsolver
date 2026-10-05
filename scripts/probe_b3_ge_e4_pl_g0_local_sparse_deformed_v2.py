"""G0 F08-D-v2: correct the local physical/retained block inventory."""

from __future__ import annotations

import json

import numpy as np

import probe_b3_ge_e4_pl_g0_local_sparse_deformed as v1


original_gather = v1.seam.gather


def gather(count, slots, local_residuals, local_tangents):
    assert len(slots) == len(local_residuals) == len(local_tangents) == 2
    shared = set(slots[0]) & set(slots[1])
    assert len(shared) == 6
    internal = [set(ids[18:]) for ids in slots]
    assert len(internal[0]) == len(internal[1]) == 24
    assert not (internal[0] & internal[1]) and not (shared & (internal[0] | internal[1]))
    for ids, residual, tangent in zip(slots, local_residuals, local_tangents, strict=True):
        assert len(ids) == len(residual) == 42 and tangent.shape == (42, 42)
        assert np.linalg.norm(tangent[:18, 18:]) > 1e-12
        assert np.linalg.norm(tangent[18:, :18]) > 1e-12
        assert np.linalg.norm(tangent[18:, 18:]) > 1e-12
        physical_shared = [i for i, global_id in enumerate(ids[:18]) if global_id in shared]
        assert len(physical_shared) == 6
        assert np.linalg.norm(residual[physical_shared]) > 1e-12
        assert np.linalg.norm(tangent[np.ix_(physical_shared, physical_shared)]) > 1e-12
    assembled_r, assembled_k = original_gather(count, slots, local_residuals, local_tangents)
    a, b = (np.array(sorted(values), dtype=int) for values in internal)
    assert assembled_k[a, :][:, b].nnz == 0 and assembled_k[b, :][:, a].nnz == 0
    return assembled_r, assembled_k


v1.seam.gather = gather

if __name__ == "__main__":
    results = [v1.case("generalized"), v1.case("physical-fibre")]
    for row in results:
        row["block_inventory_corrected"] = True
    print(json.dumps(dict(profile="G0-F08-D-v2", status="diagnostic_pass",
                          results=results), sort_keys=True))
