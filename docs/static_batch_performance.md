# Static batch evidence, 2026-10-07

The bounded static workflow accepts independent load histories without assuming
proportional variation over time. It preserves existing linear-static mechanics;
it does not integrate dynamic response. See [the API and examples](static_batches.md).

## Baselines and implementation

The corrected solver baseline is `8cb0de07`, including activity invalidation.
Candidate product code is `d109511e`. Existing trusted load-vector guard gains in
`e593afe0` are already part of the baseline.

ANYfem measurements used the preserved application working snapshot plus its
envelope-factor correction (`5480690`), and streaming implementation `8403255`.
The snapshot contains unrelated user edits and is not published. The reviewed
headless prerequisites and equivalent correction are published separately as
`24ad3b3` and `448145f`; the application streaming commit is `3e4eb7f`. Its tree
matches the clean integration tree verified independently of unrelated UI edits.

## Measured results

Times below cover load evaluation through selected recovery, reactions,
envelopes and consumed output. They are not isolated backsolve times. Native
solver, assembly and recovery thread requests were one; JIT was enabled.

| Workload | Cases | Baseline seconds | Candidate seconds | Speedup |
| --- | ---: | ---: | ---: | ---: |
| Supported barge, pressure/connection pilot | 20 | 118.7706 | 84.9547 | 1.398x |
| Supported barge, distinct sampled holdout, warm | 8 | 44.8023 | 32.3879 | 1.383x |
| Mixed beam/shell free-free pilot, warm, first short pair | 20 | 0.9433 | 0.3669 | 2.571x |
| Same free-free history, reversed run order | 20 | 0.9029 | 0.3792 | 2.381x |
| Disconnected-body control, warm | 20 | 1.2922 | 0.5050 | 2.559x |

The short sequence consumed 141.3765876 seconds of its 300-second aggregate
limit, including startup and preflight. Its 68 paired case observations had
bit-identical selected-value digests and matching envelope values and governing
identities. The 20-case barge pilot was also bit-identical. Independent
baseline/candidate nodal, dead-pressure, follower-pressure and gravity vectors
passed `np.array_equal` on a small shell/beam/coupling model.

The short sequence ran on a shared workstation, with preflight CPU utilization
roughly 5-15%. A separate task's parallel integration startup briefly overlapped
and failed at startup. These are shared-machine observations, not isolated
benchmark statistics. An earlier separate warm free-free pilot measured
0.9052 -> 0.3690 seconds (2.453x), also with exact selected results.

Warm free-free measurements reduced actual numerical factorizations from 20 to
zero during the measured history: the candidate retained the one warm-up
factorization. The supported warm holdout retained its warm-up factorization on
both routes. Counts include backend attempts and stale-handle rebuilds.

The supported barge uses target size 0.7 m, 4,349 nodes and 26,094 DOFs, with
qualified Q4 shells, beams and coupled beam/shell elements. Approximate load
compression is disabled. A candidate acceleration variant completed 20 cases
in 118.8970 seconds; its matching baseline timed out, so no acceleration
end-to-end speedup is claimed. Small free-free fixtures have 48 DOFs (96 for
the disconnected control); these do not establish large-model scaling.

The original 100/200-case five-repeat campaign was canceled before execution
because it projected to several hours. The held-out positions were
2, 86, 170, 257, 341, 428, 512 and 599 from the frozen 200-case definition.
No full-history or five-repeat claim is made. The barge has not met the 2x target;
its smaller measured gain and bounded-output capability are retained explicitly.

## Retained memory and limits

Both public APIs completed lazy 100/200/500-case ownership probes with block
size 32, two selected DOFs, one element's stresses, reactions and 40 envelope
quantities. At most 32 records were acquired ahead of output. Previous returned
blocks and selected arrays were released before the next block was observed;
registered model load cases did not grow with history length.

Solver sampled RSS grew from 145.69 to 146.98 MB across these probes; the
application adapter grew from 147.06 to 149.72 MB. Python traced peaks grew
from 1.56 to 2.09 MB and 2.61 to 3.85 MB respectively. Final explicit-GC live
allocations for the 200/500-case probes were approximately 84-101 kB. This
supports bounded returned-object ownership, not constant RSS or a hard OS memory
cap. Native arenas, transient allocations, caller-retained outputs and input
histories must be accounted for separately. These are small-model observations.

## Verification and failures retained

Final focused solver stream checks: 36 passed with JIT enabled. Clean application
integration: 46 passed with JIT enabled. Application impacted suites: 129 passed;
reviewed prerequisite suites: 63 passed. Earlier solver checks include 73 legacy
guard tests, 16 coupled-acceleration tests, and 22 benchmark/envelope/backend-count
tests. These groups overlap other development runs and must not be summed as a
unique test count.

The refined existing solver impact selection produced 74 passes, 18 deselections
and one failure: a compiled-recovery test requested three Numba threads while the
harness allowed one. The same failure reproduced on the corrected baseline and
passed with the effective maximum set to three. No tolerance changed. An earlier
overbroad selection timed out; failed fixture attempts, acceleration baseline
timeouts and partial results remain in the local evidence record.

Exact commands, source hashes, runtime settings, JUnit, process-wall durations
and full logs are retained under
`C:/ANYworkspaceWork/static-batch-20261007/`. In particular, `short-measurements`,
`checks`, `activity-evidence`, `fem-factor-evidence` and `memory-evidence` contain
the underlying records. They are not an installed-artifact qualification claim.

## Bounded reproduction

Use the benchmark driver from this checkout, with `PYTHONPATH` pointing to the
solver/application checkouts being compared. Set native and Numba thread limits
to one, enable JIT, use the same frozen neutral project/mesh fixture for barge
comparisons, and record effective imports and settings. The corrected baseline
must precede the new session/static-stream implementation.

```powershell
python scripts/benchmark_static_batches.py --route baseline --family free-free --history pilot --warmup --warmup-cases 1 --output baseline.json
python scripts/benchmark_static_batches.py --route candidate --family free-free --history pilot --warmup --warmup-cases 1 --output candidate.json
python scripts/benchmark_static_batches.py --route candidate --family supported --history holdout --sample-cases 8 --warmup --warmup-cases 1 --fixture barge07.fixture.json --output holdout.json
```

Select the baseline import roots before the first command and candidate roots
before subsequent commands. `--sample-cases` is an explicitly bounded subset,
not the full named history. Do not launch the canceled repeated campaign.

## Recovery and reaction follow-up (2026-10-08)

Compared with published solver `50d81d40`, static blocks now capture the
qualified recovery lease, built-in beam authority and Q4/S3 operation scopes
once per block. Individual stress/reaction operations retain full preflight
and output guards, and each case retains its model-change check. Borrowed
leases and shell operation tokens are explicitly revoked on exit, including
in copied contexts. Public per-case recovery remains available unchanged.

The frozen application tree is equivalent to published ANYfem `3e4eb7f`.
Serial warm comparisons used JIT enabled, one native/Numba worker, one warm-up
case, the same selected outputs and exact loading. These are one measured pair
per workload, not repeated-campaign estimates:

| Workload | Cases | Before | After | Observed ratio |
| --- | ---: | ---: | ---: | ---: |
| Supported barge, 0.7 m, 26,094 DOFs, eight held-out positions above | 8 | 32.330 s | 24.509 s | 1.319x |
| Disconnected free-free control, 96 DOFs | 20 | 0.480 s | 0.452 s | 1.063x |

These times cover load evaluation through selected recovery, reactions and
envelope output, excluding model preparation and warm-up. Barge recovery time
fell from 20.348 s to 13.169 s; the candidate phase includes block scope entry
and exit. Total barge time fell 24.2%. The small free-free difference is not a
repeatability or broad speedup claim. Peak working set was 597.5/604.2 MB for
barge and 176.5/177.4 MB for the control; no memory reduction is claimed.
Both sides reused the warm factor with zero measured factorization attempts.
All selected values and case digests were bit-identical, and envelope values
and governing identities matched exactly in both comparisons.

Final affected checks: 17 new lease/lifetime tests, 31 existing mutation tests,
36 existing static-batch tests, five compiled recovery tests, seven recovery
qualification tests, 11 recovery policy tests and seven application stream
tests passed (114 distinct tests). An independent copied-context counterexample
failed on the first candidate and passed on the published baseline; explicit
Q4/S3 token revocation repaired it. Fixture failures and that counterexample
are retained with the successful evidence under
`C:/ANYworkspaceWork/static-batch-20261007/recovery-slice/` and sibling `checks/`.

For this comparison use `--route candidate` on **both** import roots, since
the baseline already has the streaming API. The barge command above applies;
the control uses `--family multiple-body --history pilot --warmup
--warmup-cases 1`. The large canceled campaign remains canceled.

## Selected recovery and snapshot follow-up: NO_GO (2026-10-08)

A further prototype reused audited constraint fingerprints within one static
stream when current observations matched, including native eccentric beam-shell
coupling outputs. It retained session audits, public recovery calls and the
existing per-case checks. Selected stress recovery already restricted element
numerics to the requested selection; repeated model observations were the more
promising target.

The prototype was **not promoted**. Fresh serial warm comparisons against
`b246a985`, with the same frozen application, fixture, selections and thread
settings used above, gave:

| Workload | Before | Prototype | Observed change |
| --- | ---: | ---: | ---: |
| Eight held-out barge cases | 24.721 s | 27.204 s | 10.0% slower |
| Twenty disconnected free-free control cases | 0.436 s | 0.474 s | 8.7% slower |

Barge input/snapshot time increased from 6.320 to 7.831 s, and process peak
working set increased from 604.0 to 631.4 MB. All selected values and case
digests were bit-identical; envelope values and governing identities were exact
in both comparisons. These are bounded paired observations, not statistical
estimates from a repeated campaign.

A separate one-case warm diagnostic confirmed reuse was active: full constraint
audits dropped from 21 to six, while fingerprint calls dropped from 19 to four.
However, recursively encoding and checking the replacement observation consumed
3.200 s of profiled time. Model snapshots increased from 5.626 to 6.101 s in
the instrumented run. Thus rebuilding the observation cost more than the audit
work it avoided; no guard relaxation was accepted to manufacture a gain.
Profiled times include instrumentation overhead and are not workload timings.

The final affected groups covered 128 distinct passing checks, including
application integration and independent hidden-provider/code-mutation probes.
Failed development attempts remain recorded. The prototype, added tests,
commands, source identities, JUnit and both profiles are preserved under
`C:/ANYworkspaceWork/static-batch-20261007/selection-slice/`; the sibling
`checks/selection-*` directories hold full execution records. Only the evidence
report is delivered. Solver source remains exactly the faster `b246a985`
implementation; no new runtime cache or API is introduced by this follow-up.

Reconsider this approach only with a materially cheaper observation strategy
that preserves arbitrary-provider fallback and direct-mutation detection. The
earlier measured recovery improvement remains in production. No large campaign
was run.
