# Test regime and b0202d33 CI repair

Status: implementation started, 16 October 2026. Base b0202d33; isolated branch
codex/test-regime-ci-b020. Preserve unrelated main work and all earlier evidence.

The user requests a sweep of the existing testing method, faster execution,
inspection of b0202d33 hosted CI and fixes. Extend the existing focused portable
runner, deterministic sharding, isolation and retirement overlay; do not create
a competing test framework. Coverage, scientific tolerances, refusal/lifecycle
checks and retired-test selection remain authoritative.

CI run38899727006 initially had35successful jobs,7failed and7running. Saved logs
identify six native-contact replay/checkpoint failures and one stale Q4 source-
binding assertion. These are findings on main, not established consequences of
the small immutable-vector patch. Preserve exact failures; no blanket skips or
relaxed replay comparison to make CI green.

1. Mistral owns a connected tooling/runtime/sharding slice: audit actual setup,
   collection, compilation and test costs; implement evidenced low-risk fixes in
   the existing method; prove active inventory/coverage and retirement unchanged.
2. A separate Mistral Read assessment traces contact failures and proposes the
   smallest compatible repair. OpenAI adopts consequential source/replay contracts
   before implementation expands into checkpoint mechanics or frozen metadata.
3. Verify affected tooling and public runner paths, actual JIT/thread settings,
   cancellation/timeout and deterministic partition completeness. Report measured
   changes separately from estimated shard balance and unmeasured hosted savings.
4. OpenAI independently reviews source, actual receipts and dirty-work preservation.
   Local candidate delivery only; the previous main-push authority was consumed.

This is a new ordinary CI/tooling task, not a renewal of PR35's closed300second
salvage allowance or retired programme execution. First milestone uses a600second
cumulative process-wall bound with180seconds reserved for final checks, one serial
numerical/check tree, bounded commands and preserved failures. No full historical
campaign, parameter sweep, fixture rewrite or automatic budget extension. Stop
after three failed attempts at the same issue and record the concrete boundary.

Evidence: C:/Github/ANYsolver/.development/test-regime-ci-b020-20261016/ and
the isolated checkout's .development/test-regime-ci/. Exact commands, source and
effective settings, wall time, outcomes and remaining budget accompany each run.

## Mistral checkpoint 1 (implementation start)

Concrete findings from the owned sources (run_portable_ci.py 719 lines,
development_test_runtime.py 46 lines, ci.yml 452 lines, harness read-only):

- The runtime recorder hardcodes the focused contract: any
  `numba.get_num_threads() != 1`, any pool `num_threads != 1`, or effective JIT
  differing from `NUMBA_DISABLE_JIT` is an error. `os.environ["NUMBA_DISABLE_JIT"]`
  is an unguarded KeyError when unset. It records only final active values; no
  max/initial/final pool history. A compiled `recovery_threads=3` test therefore
  cannot pass even when explicitly admitted, and an OpenMP pool left at the
  admitted maximum is rejected although active threads were restored.
- The development envelope pins `NUMBA_NUM_THREADS=1` (via `_worker_environment`)
  with no CLI thread control; `--jit on` only flips `NUMBA_DISABLE_JIT=0`, so a
  3-thread compiled test cannot execute at all under the current envelope.
- CI: 32 pytest jobs (8 matrix shards x 4 subshards, Windows+Ubuntu, Python
  3.11-3.14), `--workers 2 --timeout-seconds 2400`, ten checked-in weight
  overrides; pip cache already enabled (not a new improvement).

Intended edit (existing services only, no new framework):

1. Add an explicit bounded development thread profile: `--threads N`
   (default 1, admitted 1..8, development mode only) setting
   `NUMBA_NUM_THREADS`; record the requested profile in selection.json.
2. Make the recorder validate against the explicitly requested profile
   (env-passed) instead of hardcoded 1: strict single-thread default retained;
   admitted N allows pools up to N while final active Numba threads must be
   restored to 1; record max/initial/final/actual pools and requested/effective
   JIT; missing contract env becomes an explicit error, not KeyError.
3. Derive measured cost concentration from saved job logs (`--durations` /
   step timings) and update weight overrides only where measured data
   justifies; distinguish measured vs modeled balance.
4. Regression coverage in tests/test_development_test_runner.py; focused checks
   and one production runner smoke through the 600 s harness.

Remaining checks: tooling tests, runner smoke, weight-override justification
from logs. Reserved decisions for parent: public `JIT_ENABLED` meaning change
(proposed only); Q4 symbol-manifest binding contract (existing
`compute_nonlinear_response`/`compute_stresses` differ from the successor symbol
list; not refreshed to green).

## Completion checkpoint (2026-10-16)

The candidate keeps all658 active merge modules, existing repeated critical
coverage, Windows/Linux/Python matrix, process isolation, retirement overlay and
scientific tolerances. Eight contact-module scheduling overrides now use saved
hosted durations rather than tiny source sizes. Both assignments were scored
against the same candidate cost model: maximum modeled subshard cost851658 to
564133 (33.8% reduction). This is a scheduling estimate, not measured hosted
wall-time savings; failed-worker samples are lower bounds and two actual shards
hit2400seconds. Existing pip caching was already enabled.

Focused development gains explicit --threads1..8 (default1), paired with existing
--jit on/off. The recorder initializes active Numba1 before collection, retains
requested capacity, records initial/final state, enforces BLAS1, admits only
bounded OpenMP capacity, rejects unavailable requested JIT and failed observations,
and detects leaked active-thread scopes. Public JIT_ENABLED semantics are unchanged.
Example: python scripts/run_portable_ci.py --development
 tests/test_recovery_batches.py::test_compiled_isotropic_s4_matches_scalar_oracle_for_warped_global_output
 --jit on --threads 3 --timeout-seconds 90
This unchanged production oracle
passed with actual JIT enabled, capacity3, initial/final active1, BLAS1.

One CI refusal-diagnostic test now matches explicit disagreement markers instead
of looking for the word profile anywhere in identity-component details. Valid
restore and isolated semantic tamper checks remain unchanged. No checkpoint or
mechanics implementation, schema, fixture or tolerance was changed.

Hosted b0202d33 run38899727006 ended40passed jobs/9failed jobs: five exact native
contact replay failures, one refusal assertion, one Q4 source-authority mismatch,
and two2400second timeouts. Only the refusal assertion has a demonstrated local
fix. Replay determinism and current Q4 authority need separate bounded slices;
CI is still red. The decoded-state hypothesis was disproved by source inspection.
Do not refresh frozen evidence or loosen exact comparisons.

Mistral owned the initial connected implementation and seven passing check
attempts. Its review-fix continuation ended after inspection without edits or
handoff. Root completed the concrete small repair to avoid repeated ineffective
extensions. A separate Mistral final patch review completed; its two caller-context
concerns were resolved against baseline and actual runtime evidence. Full review
and adjudication are retained in the evidence root.

Evidence root: C:/Github/ANYsolver/.development/test-regime-ci-b020-20261016
Worker check ledger: this checkout's .development/test-regime-ci/BUDGET.json.
All process attempts, failures and settings are retained. One initial parent
check hit sandbox WinError5 path resolution; runner checks then passed with normal
Windows filesystem access. The old PR35 budget remains closed and unused.
Final totals and acceptance are recorded below after final verification.

## Final local acceptance

53 affected checks pass through the public focused CLI at JIT-off/threads1;
the unchanged compiled recovery oracle separately passes at JIT-on/capacity3.
All runtime records report no contract errors. The final timing report justified
one further mechanical test-only optimization: seven invalid-shard-bound cases
now use a tiny input instead of rediscovering the complete repository inventory.
All seven refusal cases and independent full-coverage checks remain. The same53
checks took115.9889903seconds before and54.8651325seconds after (process wall,
one local before/after pair; no hosted-speedup claim).

Final cumulative check process-wall:478.0781439/600seconds, including the failed
sandbox attempt. Remaining121.9218561seconds is unused; no extension or further
check campaign. Final preservation receipt confirms all731 pre-existing files,
primary HEAD/index and protected retirement/frozen CI paths unchanged. No source
mechanics or experimental-programme file was altered. The local candidate is
accepted for these tooling/diagnostic changes only, not as a green-CI release.
No integration to main or push has been performed for this milestone.

Exact commands, candidate hashes, effective settings, before/after schedule
scores, completed independent review/adjudication and all failure logs remain
under the evidence root. CI_REPAIR_STATUS.md identifies the next bounded replay,
Q4 authority and timeout-diagnosis slices without relaxing their gates.
