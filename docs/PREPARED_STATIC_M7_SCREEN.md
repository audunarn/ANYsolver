# M7 representative development and performance screen

Outcome: the representative barge now completes prepared evaluation with physical
shell/beam von Mises envelopes, all-node reaction envelopes and selected full
histories. Keep the preparation repairs and exact-accounting optimization in the
isolated candidate. The incremental 2x complete-workload / 50% peak-memory screen
is **NO_GO**; the smaller recurring gain is measured and retained without a release
or 10,000-case qualification claim. No commit, merge or push was performed.

## Implementation and comparison identities

The initial comparator is the M6 source preserved in `../m7-baseline/solver/src`.
M7a/M7b repair preparation: evaluate the prepared side of pressure verification in
one existing owned scope, with the independent native full-load oracle outside;
admit/capture envelope recipes outside the numerical span, then sample their
schemas in one guarded span. Canonical arithmetic and numerical criteria remain.

The final runtime comparison uses reviewed M7b (`../m7b-final/solver/src`) against
M7c (`../m7c-final/solver/src`). Both contain the same preparation repairs. M7c:

- Caches the existing exact retained-storage calculation while private state is
  unchanged; allocation and writable-mode access invalidate it before mutation.
- Starts new transactions uncached and gives them independent schema-index
  headers, preserving exact accounting and copy-on-write isolation.
- Constructs empty entity reducers directly instead of copying and discarding
  the complete entries table for every physical element.

Only three product modules differ from M6: `prepared_static_loads.py`,
`prepared_static_recovery.py`, `prepared_static_envelopes.py`. Final hashes are in
`../evidence/M7_RESULTS.json`. All active product Python files match M7c-final.
Default/pinned formulations, numerical recovery operations, governing/tie rules,
full-load provenance, private factors and ANYfem product source are unchanged.

Independent Read review found and closed ingress-helper/StaticCase authority,
transitive principal-helper authority, and transaction schema-index alias gaps.
Tests cover the corresponding refusals and cache isolation. No concrete review
finding remains in this bounded delta; this is not universal resistance to writes
through private internals or exhaustive mechanical qualification.

## Why the work changed direction

The initial complete barge attempt timed out at120.10seconds before load preparation
finished. A60.09second trace confirmed repeated native authority audits inside the
prepared pressure verification loop. After fixing that scope, load preparation
completed near42seconds, but the next120.10second attempt stalled in recovery
preparation. A small actual-element profile measured49 broad authority audits at
1.636 of2.824 profiled seconds. Schema sampling had the same missing shared scope.

That diagnostic also exposed an invalid pilot output request: massless coupling
elements do not advertise von Mises stress. The corrected pilot explicitly selects
all3185 physical Q4 shells and1060 beams for stress, while retaining every coupling
in stiffness, constraints, loads and reactions. The complete solver model has
4349nodes and5349elements. No geometry or mechanical element was removed.
This is whole-physical-model von Mises plus reactions, not every stress/resultant
component. Coupling stress requests retain their typed refusal.

After these repairs, one complete cold two-case result was delivered at106.78s;
its requested warm repeat subsequently timed out during envelope detachment.
A completed one-case profile then found retained-memory bookkeeping dominant:
5 nbytes calls consumed6.776 of13.900 profiled next() seconds, involving7.19million
recursive storage calls. Empty subsets also incurred discarded whole-table copies.
Inclusive profile figures overlap and must not be added. Profiling changes timing;
these numbers selected the target, not the final speedup claim.

## Matched representative results

Meshing is excluded. All runs use the saved complete barge fixture
`evidence/representative_barge2.fixture.json`; its mesh counts are unchanged from
the earlier0.7m fixture despite its historical filename. Same interpreter, JIT
enabled, single-thread effective BLAS/OpenMP settings and output scope. The barge
uses one evaluator-owned PARDISO factorization, with no stale rebuilds, across cold
and warm histories. New-process runs use the existing shared JIT cache; they are
not claims about an emptied compilation cache.

Primary cases: Seaway_000 through Seaway_003. Distinct holdout:
Seaway_137, Seaway_174, Seaway_211, Seaway_248. Primary ordering was baseline then
candidate; holdout was candidate then baseline. Complete output includes selected
histories, verbose diagnostics, envelope detachment/serialization and comparison
digest construction. Phase times remain nested within complete times; unattributed
overhead is retained. A 1GiB solver allocation estimate is configured and yields
one-case blocks. It is not an operating-system RSS cap.

| Four-case barge workload | M7b baseline | M7c candidate | Time reduction |
| --- | ---: | ---: | ---: |
| Primary, preparation through consumed output |112.179s|106.245s|5.3%|
| Holdout, preparation through consumed output |111.889s|109.383s|2.2%|
| Primary, first history after preparation |28.729s|22.833s|20.5%|
| Holdout, first history after preparation |28.474s|25.569s|10.2%|
| Holdout, reused evaluator through consumed output |29.717s|23.257s|21.7%|

Preparation in these matched runs was83.40–83.81seconds. The runtime optimization
does not target that cost. The representative retained-memory and scope repairs
are therefore useful, but short cold workflows improve much less than recurring
execution. Primary baseline's cold history completed and is usable; its warm run
failed only at the original64MiB diagnostic-output cap. That failed attempt is
preserved, no complete warm baseline time is claimed. Subsequent runs use128MiB;
primary cold output was below both caps. Both full holdout runs completed cleanly.

All compared physical-history and governing-envelope digests are identical,
including associated fields and input/case/time identities. Cold and warm results
also agree. Canonical load-vector and native staged-recovery checks remain separate
correctness evidence, rather than treating candidate parity as physical truth.

Observed peak working sets in the completed holdout were1159.08MiB baseline and
1158.72MiB candidate: no material peak-memory improvement. The harness retains a
cold detached summary while producing the warm run; this caller-owned output is
included in process peaks. These small histories do not measure 10,000-case memory
boundedness. There is no representative 10,000-case time projection from this screen.

## Disconnected free-free control

Eight balanced disconnected mixed bodies,48elements/64nodes, nonlinear time
histories with pressure, nodal and acceleration loading. Whole-model von Mises and
reactions plus selected full histories,1GiB estimated allocation limit, one-case
blocks. Each process uses one SciPy factorization, with no PARDISO activity or hidden
rebuild. A distinct64-case holdout reverses primary32-case execution order.

| Control | Baseline cold incl. preparation | Candidate cold | Baseline warm | Candidate warm |
| --- | ---: | ---: | ---: | ---: |
|32 cases|5.582s|5.250s|4.287s|3.949s|
|64-case holdout|9.984s|9.440s|8.776s|8.143s|

Warm time reductions are7.9% and7.2%; cold reductions are5.9% and5.4%.
106,272 binary64 comparisons are exact, with all nonnumeric labels/indices/schema
matching too. Peak memory remains approximately191MiB. These controls support
compatibility and a smaller gain; they are not a representative free-free vessel
qualification or a substitute for the barge workload.

## Verification and resource accounting

Final root verification: **104 passed**, JIT enabled, in38.7596062 process-wall
seconds. It covers new pressure/schema authority and memory accounting tests,
existing transactional envelopes, all three public ANYfem prepared suites, and
independent full-load, governing-case/block-size/restart and output-alias checks.
The initial combined invocation failed collection because both repositories have
`test_prepared_static_envelopes.py`. Importlib collection with explicit helper
paths resolved that harness collision without editing tests. Failed collection
cost8.5932301seconds and remains recorded. Root correctness use47.3528363/60s.

Worker runs01–07:23,6,8,34,9,34,16 passes respectively (130 passing executions,
with overlapping selections and intermediate source versions),50.8798155/120
correctness seconds. Final root checks assess the final source. Exact commands,
settings, source hashes, stdout/stderr and JUnit are in the run records.

User initially granted600 benchmark seconds and then authorized extensions needed
to conclude development. One recorded extension raised this milestone's TOTAL to
1200seconds. **1152.4490479seconds used;47.5509521seconds unspent and stopped.**
Warm-ups, profiles, failures, partial runs and all baseline/candidate processes are
charged. Correctness budgets above are tracked separately. No further campaign is
scheduled, and old milestone leftovers were not pooled.

Preserved failed/partial evidence includes the preparation timeouts, invalid coupling
component diagnostic, the interim warm-detachment timeout, the output-cap failure,
and one traced run's native access violation0xC0000005 during unchanged stiffness
before modified code. Its cause is unestablished. A timestamp audit confirms worker
verification began after that process exited, not concurrently. Untraced subsequent
runs completed. Neither the crash nor profiling runs supplies comparative timing.
No product sources changed during benchmark or final test processes.

## Evidence and reproduction

Under `C:/ANYworkspaceWork/prepared-static-20261008`:

- `evidence/M7_RESULTS.json`: exact ledger, source delta, measurements and comparisons.
- `evidence/checks/m7*/run.json`: executable commands, effective environment, source
  hashes, precise process-wall, exit/timeout state and cleanup records.
- `evidence/m7*-barge-*/stages.jsonl`: phase boundaries, output digests, backend counts,
  runtime settings and OS peak memory; adjacent JSONL files retain consumed output.
- `evidence/m7b-barge-case-profile/cases.pstats` and `profile-functions.json`: profile.
- `evidence/m7_pilot.py`: public ANYfem representative harness; use the recorded
  holdout command and128MiB output cap with new unique output paths for reproduction.
- `evidence/m7_free_control.py`: disconnected public-solver control harness.
- `evidence/m7_analyze.py`: analysis of saved evidence, without numerical reruns.
- `solver/.prepared-static-evidence/m7-solver-handoff.md`: implementation/check details.
- `fem/.prepared-static-evidence/prepared-m7-independent-review.md`: findings and repairs.

Reproduction remains subject to an available execution budget. The old failed
artifacts and M5 NO_GO archive are intact. Work remains isolated and uncommitted.
