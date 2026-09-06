# GE-B3 native bounded adaptive arc development

Private successor of `ec5c62e9c6479011af1d75088efdddfe0fe35831`, tree
`6ad0073bf9f62619b1e19cbe0422344b2ac55160`.

The new standalone `_ge_beam3_adaptive_arc_program` module adds native
Newton/line-search cutback without modifying the frozen fixed-step arc,
displacement or force modules, element operators, constitutive laws, tolerances,
aliases, defaults or historical evidence. It is not publicly exported.

## Explicit policy and native solve

`AdaptiveArcProgram` wraps an exact fixed `ArcProgram`. Each original segment
can be replaced only by its two ordered equal halves. There is no step growth,
coefficient tuning, branch switching, spatial-mode removal or regularization.
Depth (0--12), positive minimum step, total attempts (1--256) and total accepted
substeps (1--64) are explicit immutable policy inputs. The initial schedule must
fit the budgets. Splits also reserve enough accepted-step capacity to cover
the complete pending partition. A cancelled in-flight attempt consumes budget.

The driver performs actual native assembly, the full bordered predictor and
corrector, native load-parameter derivatives, and the objective frame-chord
constraint. It reuses frozen lower-level kernels, not a force-control solve or
an inverse-stiffness approximation. Only explicit iteration or line-search
exhaustion returns a recoverable result. Exceptions from mechanics, predictor
factorization, state guards or observers are not classified by matching message
text and cannot trigger subdivision.

Rejected trials are discarded before recording cutback. Accepted substeps
advance material histories and multiplicative nodal rotations normally; a
subsequent child segment starts at that new accepted origin. Numerical cutback
is inside one solver invocation, not permission to restart a failed process or
reuse a consumed formal resource request.

## Restart and atomic acceptance

The canonical wrapper binds the adaptive program, model, complete attempt
history and a native fixed-schedule capsule. Every attempt records its root,
dyadic depth/index, step size, preceding accepted count, outcome, reason and
iteration count. Restart reconstructs the pending partition from these records;
it never trusts a saved queue or resets consumed attempt budgets. Terminal
exhaustion returns failure without evaluating another numerical attempt.

The native capsule binds exactly the accepted substep sequence. Its existing
strict restore checks still validate material epochs/origins, rotations,
physical equilibrium and reactions, the preceding origin, predictor and final
arc equation. The wrapper also checks accepted iteration counts against the
native records. Failed attempts are operational records, not independently
replayed mechanical proofs.

Both layers are fully staged before commit. Staging failure retains the prior
valid accepted capsule. Cancellation before commit records an interrupted
attempt with unchanged accepted state; after commit it retains the newly
accepted state. Explicit caller continuation after cancellation can start a
new attempt with the remaining budget, never erase the interrupted attempt.
An observer that mutates program authority cannot replace the prior capsule.

The driver has a cooperative 600-second per-invocation deadline, explicit
iteration/backtracking limits and finite global attempt/step bounds. It is not
a process supervisor: a native sparse factorization is not interrupted by the
cooperative timer. Formal runs still require the separately authorized
process-tree/time/memory watchdog. No formal request is created here.

## Development checks

Initial 35 tests passed. An expanded diagnostic correctly failed its assertion
that cutback occurred: the chosen plastic example converged in two Newton
updates. That completed non-cutback trace is retained, not reclassified as a
solver defect. Tightening this diagnostic's explicit iteration budget to one
update exercised seven genuine iteration-limit cutbacks followed by eight
accepted `0.025` substeps covering the original `0.2` segment. The mechanics,
residual tolerance, material properties and reference geometry were unchanged.

The native checkpoint for the discovered schedule is byte-identical to an
explicit fixed-step solve using the same eight substeps and one-update bound.
This is not a claim that a single large material increment equals subdivided
increments. Restart after the first three genuinely rejected attempts is also
checked against uninterrupted continuation. Injection tests separately verify
that a consumed failure is not repeated after restart, without treating the
injected failure as a physical counterexample.

The first broad regression passed 253 tests before final guard hardening.
Focused failure-injection tests then reproduced two ways for a corrupted
observer-supplied program to disrupt failure-capsule construction, plus an
impossible line-search iteration record accepted by the parser. Failure-row
construction now occurs only inside guarded authority validation; on failure
the prior valid capsule is retained. A line-search exhaustion record must be
from an iteration that actually permits a corrector. These are successor
driver/record fixes, not changes to the physical formulation or frozen drivers.

Final tests, per-file inventories, source hashes and external artifact hashes
are recorded in `docs/reference_cases/ge_beam3_adaptive_arc_development_evidence.json`.

The hardened source passed 69 checks in 84.88 seconds: 43 adaptive-driver
tests, seven installed-control static checks, five arc-program static checks,
four arc-geometry static checks, five displacement static checks and five
installed-force static checks. A separate fresh-process repetition of the real
cutback/restart diagnostic passed in 57.13 seconds. Five new static checkpoint
binding tests then passed in 0.13 seconds. These are separate inventories,
not additional scientific cases or a performance acceptance claim.

The two hardened diagnostic capsules (65,477 bytes each), progress traces
and status records are byte-identical. Capsule SHA-256:
`dd2c8b9710009554c46f195df3f888a1e946d8b2dee6ecd559968befc2746b20`.
The six final files, 178,822 bytes, are preserved under:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-adaptive-arc-development-20260906-a44e104bbd6f`

A separate immutable prior archive retains nine files, 237,333 bytes,
including the non-cutback diagnostic and pre-hardening traces. The successful
diagnostic bytes are unchanged by the final guard fixes. Both archives were
checked file-by-file for byte counts and SHA-256 from the normal workspace
context. Only verified relay duplicates and empty relay directories were
removed; original temporary outputs remain. No formal resource request was
created, retried or consumed.

## Boundary and remaining work

Independent review and installed-wheel testing of this new adaptive successor
remain pending. Earlier installed fixed-control evidence does not qualify it.
This small diagnostic is not engineering post-buckling, critical-point,
stability/PSD, locking, slenderness or general plasticity qualification.

General section/load/constraint parity, loaded modal and buckling, straight and
curved engineering qualification, production integration and the objective
beam-shell connection remain required. Existing B2/B3/Q4/S3 mechanics and
qualification records are unchanged. No publication or default activation is
authorized by this development checkpoint.
