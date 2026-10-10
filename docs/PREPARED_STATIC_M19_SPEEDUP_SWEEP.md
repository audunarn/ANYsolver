# M19 — speed-up sweep of the vectorized route (investigation only)

2026-10-09. No product code was changed. Evidence: two cProfile runs on the
representative barge (`../evidence/m19-profile-cases/cases.pstats`, 40 vectorized
cases; `../evidence/m19-profile-preparation/preparation.pstats`, vectorized
preparation), recorded M18 phase timings, and source reading. Profiling inflates
time about 2.5x and inflates Python-call-heavy code (deep copies, guards) more
than numpy work, so the per-case gains below are shares of profiled time and
rough real-time estimates, not measurements.

## Where the time goes now

Vectorized route, M18 primary history, 300 cases (unprofiled):

| Part | Seconds | Per case |
|---|---:|---:|
| Load evaluation (original-time canonical loads) | 87.1 | 0.29 |
| Recovery phase | 57.2 | 0.19 |
| Application case resolution (outside solver phases) | 18.5 | 0.06 |
| Solve, certification, reduction | 3.7 | 0.01 |
| Preparation (once) | 111.4 | |

Profiled case time (40 cases, 55.8 s): reaction diagnostics 21.0 s, of which
17.2 s is deep copying of constant constraint metadata; pressure load kernel
15.4 s, of which `np.cross` 6.3 s and qualified-element guards most of the rest;
wet-pressure resolution 4.7 s; per-case native authority checks 1.4 s; the
vectorized stress evaluation and envelope folds about 0.5 s in total.

## Per-case findings, ranked (dominant for 10,000-case workloads)

1. **Reaction diagnostics deep-copy constant metadata every case.**
   `constraint_force_diagnostics` deep-copies `constraint_info` and
   `nullspace_info` twice per case (about 330,000 objects per case on the
   barge). 31% of profiled case time. The vectorized envelope only needs the
   three force maps. Fix without numeric change: compute the force maps with the
   same residual and accumulation, without metadata copies or per-MPC record
   dictionaries, for the envelope; keep full diagnostics only for selected
   reactions. If selected reactions are requested, sharing one frozen metadata
   copy across cases instead of copying is an output-semantics decision.
   Estimated 0.08-0.17 s per case.
2. **`np.cross` on 3-vectors in the pressure kernel.** 217,000 calls per 40
   cases inside `boundary.LoadCase._consistent_pressure_load` (four Gauss points
   per wet element), plus 62,000 in ANYfem centroid normals. numpy 2.4.3 forms
   the same two rounded products and one rounded subtraction as a written-out
   formula, so a hand-written cross product is bitwise identical. The per-node
   update loop can likewise be written with the same multiplication order. This
   is canonical load code shared by every route, so it needs an owner decision
   even though results are unchanged. Estimated 0.04-0.07 s per case; it also
   speeds preparation and the canonical routes.
3. **ANYfem recomputes wet-element centroids and normals every case.** The
   adapter's `_cached` centroid cache is cleared per case by
   `clear_case_caches`, so all 61,893 lookups in 40 cases miss. Geometry is fixed
   after preparation, so these can be captured once. About 7% of profiled case
   time plus 2.5% in `_input_storage_bytes` accounting of the cache entries.
   Estimated 0.03-0.05 s per case. No numeric change.
4. **One native authority check per case in the response load path.**
   `require_native_source_authority` (about 35 ms profiled) runs per case in
   `PreparedStaticResponseEvaluator._load_vector`, although the block's loads are
   evaluated in one loop with no caller code between cases. Checking once per
   block, as M17 did for routing checks, is equivalent and fails closed.
   Estimated 0.01-0.02 s per case at block 4.
5. **Per-block fixed costs at block size 4.** Authority and class-state checks,
   transactions and accounting run per block. The screens used block 4; a
   larger block under the same memory policy amortizes them. Unmeasured.
6. **Envelope label accounting grows with history length.** `VectorEnvelope`
   copies its label dictionary on every transaction and re-sums label sizes on
   every accounting call, which is quadratic in the number of cases. Negligible
   at 300 cases, roughly seconds at 10,000. Keep a running total instead.

**Contract-level lever (owner decision, not a missed optimization):** the
original-time canonical load per periodic sample, now about half of per-case
time, exists to check source agreement and to give the certificate and the
reactions the native load. Options are a vectorized load from the verified
compiled pressure bases (qualified by assessment like the stresses, with
reactions then compared under a scaled criterion instead of bitwise), or
verifying the original-time load only on a declared subset. Either removes
most of the 0.29 s per case. Qualified-element guards inside the native
pressure kernel (pinned `e4_pl_element.py`) are only removable through a
successor record.

Rough combined effect, unmeasured: items 1-4 together could take per-case time
from about 0.55 s to roughly 0.3-0.4 s. With the contract-level load change,
roughly 0.15-0.2 s.

## Preparation findings (matter for histories of a few hundred cases)

1. **Envelope recipe capture: 37% of profiled preparation.** For each of 4,245
   elements the capture warms native stress caches (`compute_stresses`) and
   compiles Q4 stages; qualified-element guard calls dominate both. Whether the
   warm-up is still needed when the vectorized route probes through the staged
   kernel needs a focused check before any change.
2. **Acceleration mass capture although the barge source has no acceleration.**
   About 19 s profiled (7%). The default prepares all load families. Scoping
   families to the declared sources, with explicit opt-in for others, is a
   capability decision.
3. **Vectorized probe build: 35 s profiled (about 14 s real).** 24 unit probes
   plus verification per Q4 element through the staged kernel. A batched
   matrix-input staged evaluation, or composing H from the captured stage
   matrices, keeps verification and removes most of this.
4. **Snapshot content digest: 9.7 s profiled.** Recursive per-value hashing of
   1.8 million values; hashing array bytes directly would be much faster but
   changes the digest format.
5. Duplicate captures (load maps capture all 5,349 elements again) cost 18.6 s
   profiled; smaller than they look because the load-map captures skip the
   warm-up and stage compile.
6. Stiffness assembly (about 19 s profiled) and the four independent full-load
   oracle assemblies (27 s profiled) are qualified or verification paths; no
   change recommended.

## Resources

Epoch m19: 470.107 of 600 s (cases profile 187.244, preparation profile
282.863); stopped. No correctness checks, no product edits, no Git operation.
