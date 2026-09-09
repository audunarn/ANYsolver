# P5 control32 — bounded causal observation, no correction yet

Parent `b62298ebabca682c284754e46474c4d8ca3c3441`, tree
`35c11733939cbc9cc165a426c4022a90211ff8da`. Freeze exactly five paths:
the research displacement controller, new control32 diagnostic runner,
their two test files, and this plan. No production or other research
mechanics path changes.

## Question and nonqualification boundary

The consumed onset32 request failed at its first nonzero target with a
controlled-line-search error. The previous worker preserved the initial
state and traceback, but did not serialize the failed iteration values.
The evidence therefore did not establish roundoff, conditioning, local
stationarity, inappropriate Newton direction, or missing equilibrium as
the cause. This successor records the information needed to distinguish
those possibilities. It does not prescribe a correction or assume a cause.

Run only the initial target `0.1` and first nonzero target `0.095` of the
same 32-element parabolic arch (height 0.1, span 2, end clamps, section
diagonal `[1000,400,400,0.02,0.01,0.02]`, eight-point rule per half,
512 stations, explicit `ARCH_ONSET32` profile). No onset grid beyond these
two states, bisection, continuum solve, new geometry, altered section,
cutback or full refinement wave is allowed.

The target may fail again or may converge. Both are valid **observations**;
neither qualifies the element or replaces the previous failed result. An
unexpected convergence must remain visible, not trigger another attempt
to obtain a preferred failure. If the target fails, no target trial or
target matrix is fabricated. If it converges, the ordinary commit/replay
checks precede preservation of its raw trial. State remains research-only.

## Observation-only controller extension

Add an optional callable observer. With no observer, no diagnostic SVD or
metric computation occurs. The observer receives detached scalar data only,
never solver arrays, histories or a mutable checkpoint. Its return value
cannot change solver acceptance. Sink failure raises a distinct observation
error and cannot publish or commit a trial. At most 256 events are permitted
per trial; no extra element response is evaluated for observation.

Events record initialization, predictor, current iterations, linear
corrections, evaluated/rejected candidates, convergence or failure. They
contain mixed-evaluation counts, physical residual norm and translation/
scaled-rotation parts, largest residual component/DOF, largest local
stationarity residual, potential, current reaction, requested correction
sizes, actual candidate position/frame changes, linear-system residual and
the observed 2-norm condition number of the already assembled free system.
Condition numbers are numerical diagnostics, not rigorous error bounds.
Typed local candidate rejections are retained. No matrix or frame is
differentiated numerically and no operator is reauthored here.

The predictor/corrector solves, residual definition, `1e-11` acceptance,
sixteen-corrector limit, ten candidate backtracks, 8,192 mixed evaluations
per trial, multiplicative updates and transaction rules remain unchanged.
Observation computes diagnostics only after the same solver calculations;
it does not alter a tolerance, iterate, stiffness, load or reference value.
Observation failure is a blocked diagnostic, not a scientific solver result.

Flush each event to the external progress log so earlier observations survive
a later failure or process termination. A caught controller failure retains
its original iteration checkpoints and confirms no pending/newly committed
state. Failed-process checkpoints that never existed in the previous run
are not backfilled into that historical evidence.

## Frozen failed evidence and runtime

Preserve all eight files of the failed attempt under
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-onset32-20260906-93c594cb16aa430babae3a3fc62e2e2f`.
The runner binds their exact names, byte counts and SHA-256 values, including
the 309-byte blocked diagnostic
`82CF372AE545A55848B77CAB06060ADC313331B4DF5F4032C9FBD9F0C9247524`
and 1,155,343-byte initial trial
`C28606AC3E4A85AF82915CFEE610753A5B7364F850894CDDA628EFC8D4179770`.
It also verifies the continued absence of that attempt's aggregate/complete
packet. The failed request remains consumed. No old worker runs.

Retain the exact Python 3.13.9 executable and installed NumPy 2.4.3/SciPy
1.16.3 non-bytecode file inventory, canonical environment digest
`2CD226A5CF78C9CC833DCBAF7E4CD0C8EAB92DD8566AF69412E13D346DC298F4`.
Require clean ANYfileIO commit
`b48ba51c7b79e6d64b3f99c1fb131b9b602e7e1d`, tree
`29cb248a8d320607e21424c68625c4af6a949da1`.
Candidate, sibling, runtime and failed-input checks precede numerical imports
and repeat before finalization. No dependency installation is included.

## Execution authority and resource bounds

After the clean five-path freeze, generate one fresh request for the new
coordinator's exact emitted command and a fresh external directory. Obtain
its explicit administrator APPROVED ledger row, acquire its exact global
lease, execute the stored command once, then release in `finally` only after
the complete process tree is terminal. Neither prior request can be reused.
Create an exclusive permanent request claim; no automatic retry is allowed.

Use one contained child, one numerical-library thread, at most 24 GiB per
complete tree, a 600-second child envelope, 300-second CPU/checkpoint
inactivity limit and an 890-second coordinator watchdog. The existing
Windows Job containment and early timer/tree drainage remain unchanged.
No resource-heavy test runs concurrently with another global resource lane.

Preserve progress, PID/start data, stdout/stderr, raw available trials,
resource diagnostics and the captured controller outcome externally.
Process, observation, authority or malformed-evidence failure creates no
completed diagnostic; it preserves partial files and a blocked record.

If both-state observation completes, publish a canonical **diagnostic**
record, never an onset/qualification aggregate. Its disposition is
`RESEARCH_CONTROLLER_OBSERVATIONS_CAPTURED`, with explicit solver outcome
`FAILED` or `TARGET_CONVERGED`. A successfully captured failure can yield
resource execution success, but the solver outcome must still say FAILED.
Always retain `production_qualified=false` and the production restriction.

## Integrity validation and pre-freeze evidence

Strictly validate canonical JSON/JSONL, duplicate/nonfinite rejection,
the two exact target/origin identities, contiguous event sequences,
iteration/backtrack ordering, monotone evaluation counts and bounds,
component residual reconstruction, the unchanged candidate acceptance rule,
terminal consistency, raw trial hashes, initial checkpoint digest and
failure/checkpoint agreement. Reject a fabricated target trial after failure.
Bind complete packet and observation-log hashes into the final diagnostic.
This is integrity validation, not an independent mechanics oracle or review.

Small observer tests demonstrate byte-identical accepted trials, commits,
replay, frozen pre-extension two-element hashes and unchanged mixed counts;
mutation of observer data cannot modify solver state. They cover sink
failure, budget/update failure, typed candidate rejection and deterministic
logging. Diagnostic tests cover successful and deliberately update-limited
two-element paths, malformed/rehashed observations, request reuse,
authority guards and resource-failure preservation. These small fixtures
do not execute the 32-element failed target.

Final focused regression: **159 tests passed in 17.82 seconds** before this
freeze, including observation/diagnostic tests and unchanged controller,
extent, onset and prior-wave integrity tests. `git diff --check` passed.
Confirm the exact five paths and zero production delta at commit. Save the
actual resource request and diagnostic findings in a later documentary
closeout; do not mutate this authority while execution is active.

No numerical correction, onset qualification, push, merge, version/default
change or publication occurs here. Broad spatial/material/mass/dynamics,
production restart/interfaces, independent review, packaging and objective
beam-shell connection requirements remain open.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
