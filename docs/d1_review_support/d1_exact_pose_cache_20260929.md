# D1 exact-pose float-witness cache — 29 September 2026

This bounded experiment tested a different measured cost mechanism from the earlier arithmetic micro-optimizations. The monolithic driver often evaluates a trial without a tangent, accepts it, and then revisits that exact physical pose with a tangent. The Q4/S3 path normally evaluates independent float overlap geometry on both calls before differentiating with Jet2.

A temporary one-entry cache reused only the **complete float geometry state** when source and target physical coordinates had byte-exact pose identity. It retained independent float-versus-Jet2 comparisons, both-body force maps, adaptive derivative decisions and all contact gates; changed poses recomputed the float state. A focused test passed (1 test, 2 deselected): residual/tangent, support, gap, Gram, overlap branch and triangle count matched the uncached route exactly; a moved pose caused a new float evaluation and a changed nodal-force vector did not reuse pressure.

One matched, instrumented eight-Q4 monolithic complete route (two force steps, checkpoint enabled) ran in separate bounded processes with the cache disabled and enabled. Both completed under the existing 180 s / 1 GB limit. Final displacements, contact result, step counters and checkpoint SHA-256 are exactly equal.

| Measure | Cache disabled | Cache enabled |
|---|---:|---:|
| Instrumented solver time | 12.897 s | 12.325 s |
| Process elapsed time | 14.597 s | 14.014 s |
| Peak process-tree memory | 282.640 MB | 282.657 MB |
| Aggregate float geometry calls | 12 | 7 |
| Raw nodal-force work calls | 10 | 10 |

The single-pair solver-time ratio is **1.046×**. It demonstrates five avoided float preparations and exact mechanics on this route, but neither a stable whole-route speedup nor the material saving needed for the 16×16 target case. The temporary cache and its focused test were therefore removed from production. The [candidate patch text](d1_exact_pose_cache_candidate_20260929_patch.json), [baseline](d1_exact_pose_cache_baseline_20260929.json), [candidate](d1_exact_pose_cache_candidate_20260929.json), their resource/log records and [historical runner](d1_exact_pose_cache_route.py) are retained. The patch text is JSON-escaped to preserve Git diff context lines. The runner checks the temporary source SHA and rejects current HEAD; applying the patch is required to reproduce this experiment.

Independent mechanics review confirmed that the float integration is a fail-closed witness for the Jet2 values, so deleting it wholesale would change the current qualification boundary. Any later one-pass geometry design must retain independent float/Jet2 value comparisons, clip ownership, moving-projection derivatives and separate adaptive value/derivative limits. The D1 coupled spatial and pressure-space gates remain open.
