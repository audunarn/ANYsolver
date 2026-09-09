# P5 native controls and solve-owned cancellation cleanup

Parent `453b3ace1fb122ac0662c5e126912df5999dc4a6`, tree
`75e746563049ea27c90c4e14247e9cf6a2da5231`.

## Actual control paths

Exercise the private curved P5 candidate through the actual public
`solve_static_nonlinear` displacement-control and load-program paths, and
`solve_static_arc_length`. No replacement solver or mechanics modification.

The clamped, coupled-section curved macrocell passes two displacement-control
increments to tip ux=0.03 and a bounded two-step arc trace. The arc terminal
`maximum_steps_reached` is the intended process bound, not evidence of a
limit point or postbuckling qualification. A six-increment load/unload/reverse
program preserves exact accepted-origin linkage and nondecreasing accumulated
plastic history. Every result is still private development evidence.

Both control paths also pass actual solver checkpoint split continuation:
two displacement increments split 1+1, and four arc increments split 2+2.
Resumed displacements, typed station histories and full canonical checkpoint
bytes match the corresponding uninterrupted paths exactly. These are small
curved fixtures, not a general restart/engineering qualification campaign.

## Genuine cancellation incident

The initial three-test smoke produced two passes and one failure in 9.48
seconds. Cooperative cancellation was requested inside an unaccepted P5
response after the first accepted force-control increment. `SolveCancelled`
was raised and the accepted material/kinematic state stayed unchanged, but
both the material and native rotation trial remained active. That leaked
transaction is a correctness/state-safety defect, not a scientific NO-GO for
the interpolation or a loss of qualification evidence.

The local reproduced store belonged to the terminating unit-test process;
it was not a running formal process, external resource lock or historical
authority request. No failed scientific run was restarted or reclassified.

## Repair

`nonlinear_state.py` now provides an internal operation-owned cleanup scope
using a `ContextVar`. `_activate_nonlinear_state_storage` registers only stores
activated by that solve. The public nonlinear-static and arc-length operation
boundaries invoke their existing under-lease drivers inside this scope.

On normal return, exception or cancellation, cleanup discards remaining
unaccepted trials of those registered stores. It does not commit, roll back
an accepted generation, or touch unrelated stores. Registrations are deduplicated
by identity. Nested scopes restore their parent's ownership and clean their
own stores only. Cleanup attempts every owned store and reports any failure,
including inconsistent native/material active-state flags, rather than
silently reporting a clean operation.

Only solver orchestration changes: `nonlinear_state.py`, `nonlinear_static.py`
and `arc_length.py`. Element mechanics, native rotation increments, section
return maps, accepted state, tolerances, defaults and legacy aliases remain
unchanged. No public API or checkpoint schema changes are introduced.

## Verification

- After the cleanup repair, the original three checks passed in 10.11 seconds.
- Expanded force/displacement/arc cancellation, load-program and cleanup-scope
  checks: 11 passed in 21.35 seconds.
- Native displacement/arc split-continuation checks: 2 passed (6 deselected)
  in 22.35 seconds.
- Final regression: **84 passed in 56.74 seconds** across
  `test_ge_beam3_curved_p5_native_controls.py`,
  `test_nonlinear_state_cleanup.py`,
  `test_nonlinear_static_state_lifecycle.py`, `test_native_rotation_state.py`,
  `test_nonlinear_state_batches.py`, `test_nonlinear_restart_checkpoint.py`,
  and `test_ge_beam3_mixed_p3_optin.py`. Separate run counts are not added.
- Each cancellation test captures the actual driver-owned store and verifies
  the first accepted material/rotation generation and byte-identical state
  remain intact while both unaccepted trial tokens are closed.
- Cleanup tests cover normal return, unrelated-store isolation, nested-scope
  ownership, exception propagation, accepted-commit preservation, and continued
  cleanup after an injected discard failure. The intentionally faulted test
  store is explicitly closed after its failure assertion.

The load-program and split-continuation tests use the real solver, canonical
checkpoint implementation and P5 state validators. No candidate coefficients
are tuned and no convergence threshold is relaxed. The small arc runs are
capped at two or four steps, ten iterations, fixed arc radius and one permitted
retry; no retry is needed in the passing cases. Static controls use at most
six requested increments, ten iterations and bounded line-search cuts. These
limits bound correctness fixtures, not a performance qualification threshold.

All tests use Python 3.13 `-B -m pytest -p no:cacheprovider`, one thread in
OMP/OpenBLAS/MKL/NumExpr, and fresh external temporary basetemps. No formal,
large-mesh or performance resource request is generated or consumed.

## Remaining goal

This checkpoint is same-author development and needs independent review;
it does not qualify the full beam or its beam-shell connection. In particular,
the short arc trace is not evidence of resolved onset, a first limit point,
postbuckling accuracy or freedom from slenderness-related locking. The prior
onset uncertainty and coordinate-low interface gap are still open.

Next priority is native mass/modal and current-state tangent integration,
retaining the established full-inertia/algebraic-trace policy instead of
silently replacing it with a static Guyan reduction. General objective
nonlinear section adapters, engineering gates, full standalone qualification
and objective beam-shell coupling remain required. Existing B2/B3, Q4/S3 and
historical evidence remain unchanged. No push, merge, release or activation.
