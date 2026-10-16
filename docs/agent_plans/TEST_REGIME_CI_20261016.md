# Portable testing and CI fixes — 2026-10-16

## Active scope and delivery gate

User authorizes remaining CI fixes, bounded Mistral implementation, CI optimization,
and push to main. Work is isolated on `codex/test-regime-ci-b020`, based on local
verified tooling commit `85bffc8d`, above main `b0202d33`.

Preserve all unrelated primary work, exact scientific comparisons/tolerances,
active coverage, retired selections, saved fixtures and historical evidence.
No numerical kernel or mechanics change was justified or made in this slice.
Local checks pass; full hosted CI for the candidate remains the promotion gate.
Do not report the old hosted replay failures repaired merely from local passes.

## Implemented changes

- Existing portable weighted sharding gains eight observed contact-test cost
  overrides. All 658 active modules, critical repetition, process isolation and
  all 32 OS/Python/shard/subshard allocations remain. Both assignments scored
  against one fixed heuristic model reduce maximum modeled load from 851658 to
  564133 (33.8%). This is not measured hosted wall-time savings.
- Seven invalid-shard-bound tests avoid rediscovering the entire inventory.
  Their error cases and separate full-coverage assertions remain. The same
  53-check set measured 115.9889903 -> 54.8651325 seconds locally, one before/after
  pair, with no whole-suite speedup claim.
- Focused development explicitly admits `--threads 1..8` (default 1), retaining
  `--jit on/off`. Runtime records distinguish capacity from active threads,
  initialize/require baseline active 1, keep BLAS 1, check bounded OpenMP,
  reject unavailable requested JIT and detect leaked scopes. Public
  `JIT_ENABLED` semantics and normal CI controls are unchanged.
- CI resolves/installs the four pinned sibling source packages and editable
  dev/Numba runtime in one pip invocation instead of two. Existing pip caching,
  pins, pip checks, matrix and 2400-second limits remain.
- CI workers emit small selection/progress/current-node/phase/lifecycle records;
  the parent records failure/timeout/interruption termination. The optional
  plugin does not change runtime settings, selection or pytest outcomes.
  The pinned upload action collects only named diagnostic JSON files, with
  unique matrix names and three-day retention, excluding all caches/basetemp.
- The checkpoint diagnostic assertion checks explicit disagreement markers,
  avoiding false matches on legitimate identity-component names.
- A compact Q4 current-source binding successor links immutable 0.4.2 evidence.
  The existing 47 roots now bind 133 transitive symbols, including the extracted
  nonlinear core. This is SOURCE_BINDING_ONLY_NO_NEW_QUALIFICATION. Historical
  records, source laws and defaults are unchanged. Optional sampling and the
  named experimental prepared consumers are explicitly not newly qualified.
  Mutation/default-workflow exclusion checks guard this boundary.

## Verification and unresolved evidence

Current local verification on the observed Python 3.14 CI dependency versions:

- 59 runner/retirement checks pass, including a live CI-plugin run of its own
  tests: 59 started/completed/passed, no remaining current node, exit 0.
- 36 final affected inventory/matrix/isolation, Q4 authority/default/tangent and
  diagnostic checks pass through the public focused CLI with JIT enabled.
- All five original replay failures pass unchanged, including rejected trials,
  cancellation, split restart and saved-record comparisons. This does not identify
  the hosted-only cause or constitute a numerical repair.
- License compliance passes. Preservation checks confirm all 731 pre-existing
  files, primary HEAD/index, frozen evidence and retired policies unchanged.

The exact observed stack is reproduced in the disposable local environment:
Python 3.14, NumPy 2.5.4, SciPy 1.18.1, Numba 0.68.0, llvmlite 0.50.0,
pytest 9.1.1, threadpoolctl 3.7.0. Earlier local checks used NumPy 2.4.3 or 2.4.6;
those passes alone were insufficient. The saved CI 3.11 failure used NumPy 2.4.6.
No shared installed runtime was modified.

Old hosted run: https://github.com/audunarn/ANYsolver/actions/runs/38899727006
It ended with 40 successful and 9 failed jobs: five exact replay failures, the
locally corrected diagnostic assertion, the locally corrected Q4 source binding,
and two shared-limit timeouts. Hosted replay/timeout disposition awaits the new
candidate's full CI. Saved fixtures and failure output are retained unchanged.

## Ownership, review and bounds

Mistral owned the connected investigation and CI implementation/repair. ROOT owned
the consequential Q4 binding disposition, independent review, reconciliation and
Git delivery. Independent Mistral review of the actual bundled Q4 diff/record has
no unresolved consequential finding. A tool-response mismatch in an earlier
multi-file read was detected; that incomplete review was not used for acceptance.

Turn-bound worker runs left implementation without final handoff/verification.
ROOT preserved the logs and completed small integration repairs: a malformed test
newline, independent unit-plugin state, and failed-setup phase transition. The
real pytest child tests cover pass/skip/setup-fail/teardown-fail and unchanged
exit status; the live-plugin check guards counter contamination. No further
worker extension or mechanics formulation was started.

The new local check cap is 1800 seconds, one serial local check tree, with 450
seconds reserved for final/integration checks. Accounted use at local acceptance
is 647.8724368 seconds, including a conservative 3.374-second charge recovered
from untimed metadata/edit tool intervals. Exact child process times, failures,
source/settings and remaining allowance are in the ledger. Prior 600-second and
PR35 budgets remain closed; no retired campaign authority is renewed.

One pre-promotion hosted workflow dispatch uses the unchanged full matrix and
limits. No manual whole-workflow retry or parameter campaign is authorized by
this plan. A successful main push normally triggers its own automatic CI; that
standard trigger is preserved. Required failing gates must not be waived.

## Restart and evidence

Raw evidence and full commands are local, outside the integration payload:
`C:/Github/ANYsolver/.development/test-regime-ci-b020-20261016/continuation/`.
Worker ledger and disposable runtime:
`C:/Github/ANYsolver/.worktrees/test-regime-ci-b020-20261016/.development/ci-fixes-continuation/`.
The complete pre-compaction note is retained locally; earlier committed history
also retains the prior milestone. The current compact source binding is
`docs/reference_cases/e4_pl_q4_current_source_binding_20261016.json`.

Before resuming, inspect candidate GitHub checks, `ACTIVE_CONTINUATION.md`,
`Q4_ACCEPTANCE.md`, `CANDIDATE_PRESERVATION.json` and `BUDGET.json`. Do not rerun
passed unchanged checks to reconstruct evidence or renew consumed limits. A
remaining failure needs its exact current node/state and a bounded discriminating
check; no tolerance relaxation, fixture overwrite or retirement-based exclusion.

## Hosted gate failed — do not promote

The full candidate run [38913033117](https://github.com/audunarn/ANYsolver/actions/runs/38913033117)
finished with 34 successful jobs, 11 failures and four cancellations after the
required gates were already red. Main remains `b0202d33`. The candidate is not
accepted for integration; cancelled coverage is not a pass.

Mistral's subsequent test-only helper first attempts strict native/S3 fixture
restore, then permits a fresh local capsule only when differences are confined
to three derived contact diagnostic estimates. All physical/history/mechanical
fields remain exact; binding, hash, chain, malformed and physical one-ULP
differences stay refused. Production replay and original fixture bytes are
unchanged. Positive fixture consumers use the helper; CLI capsules go only to
temporary test folders. Eight helper/refusal cases passed. Consumer verification
and its timeout evidence must be read from the final local handoff/receipts.

ROOT corrected the workflow assertion for the adopted single dependency-resolver
invocation; the exact sibling pins, editable extras and official artifact-action
SHA remain asserted. This small connected CI assertion repair does not change
the workflow or mechanics. Mistral's editing continuation recovered and delivered
the helper after tool stalls; no mechanics implementation was taken over.

Unresolved hosted gates: an anchored/fine-lifecycle shell-moment one-ULP replay
failure; the sliding-friction displacement-force predictor; surface-replay
first-touch history; and the independent D1 KKT control-reaction comparison
(`1.4948506139016305e-05` against the unchanged `1e-6` criterion).
A final logging-only Windows run
[38920452517](https://github.com/audunarn/ANYsolver/actions/runs/38920452517)
passed its selected tests with eight captured evaluations and no observer errors.
It did not reproduce the moment failure and establishes no repair. Prior failed
observer attempts remain preserved, without physics-evidence status.

No further full-workflow retry, tolerance change, fixture regrading or main push
is justified by these results. Continue only from the exact failures and local
remaining budget in `continuation/FINAL_DISPOSITION.md` and the worker ledger.
Required full CI still has to pass before promotion. No hosted speedup is claimed.

Final local reconciliation: eight helper/refusal cases, two multifacet cases,
six material-recovery cases, six two-fibre cases, three enforcement cases and
the isolated CLI restart case passed. Three earlier restart items completed
before the combined batch's 250-second timeout; partial output is preserved.
The CLI-only retry passed in 94.5784 process-wall seconds within the same cap.
ROOT's final workflow assertion, license and preservation checks passed: all
731 protected primary files and the 32-row matrix remain intact. No `src/`,
fixture-data or retirement-policy changes exist relative to `b0202d33`.
Accounted local use is 1253.6266239 seconds; 546.3733761 seconds remain unused.
Raw worker handoff at `WE/FIXTURE_HELPER_HANDOFF.md` overstates two test counts
and misidentifies the folded editable install as a wheel install; actual
commands/output in the receipts and ROOT's reconciliation are authoritative.
These local results do not resolve the hosted gates or authorize promotion.
