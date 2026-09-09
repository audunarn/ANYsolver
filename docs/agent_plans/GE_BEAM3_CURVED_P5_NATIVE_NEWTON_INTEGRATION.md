# P5 actual Newton-driver integration checkpoint

Parent `718d4797d01e8f6603e38a659a45ec49d9789197`, tree
`442278101e6fa82a8e615365bb3af37cffc6f2a2`.

## Change in integration authority

The previous private session proved scalar/assembly and station-state
compatibility, but could not protect commits made by the actual Newton driver:
that driver creates its own `NonlinearStateStore`. This checkpoint adds an
explicit internal opt-in material-validation protocol to the real store and
scalar dispatcher. No driver monkeypatch or substitute Newton solver is used.

Three source paths are involved:

- New `src/anysolver/_native_material_protocol.py`: exact validator type and
  a live store/token-bound material context; no mechanics or registration.
- `src/anysolver/nonlinear_state.py`: optional frozen validator binding,
  initial committed-state validation, candidate validation at staging and
  again before all commit pointer swaps, and live-context issuance.
- `src/anysolver/nonlinear_element_evaluation.py`: pass/revalidate that context
  only when an element explicitly declares the exact protocol version.

Existing elements do not opt in. Their positional calls and existing native
rotation-view calls are unchanged. The S3-specific consistency/materialization
protocol is not repurposed; dual registration is rejected. The new protocol
admits unbatched, explicit material histories only and fails closed for deletion.

Validators receive owned copies of current/previous material state and the
element's frozen DOF displacement slice. Initial-state validation completes
before exposing the new rotation store. All candidate validators complete
before any accepted material/rotation pointer swap. A generic dictionary
commit can no longer bypass validation for an opted-in model-bound element.
The context rechecks the actual active token, exact bound connectivity and
reference directors, and complete immutable view before/after mechanics.
An unbound low-level store cannot issue a valid material context.

## Private P5 successor

`DriverP5Element` is an unregistered `Element` subclass, using the preserved
P5 compensated mixed kernel and previous native chart conversion. It does
not inherit legacy B3 or change accepted P3 mechanics. Its identity is
`CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_NATIVE_DRIVER_V1`; its outer
state schema is `GE_BEAM3_P5_PRIVATE_DRIVER_STATION_STATE_V1`.

The outer state binds the private driver identity and redundant native
displacement/matrix data to the exact preserved station state. Validation
replays the local response from the prior accepted origins, checks the current
histories, and checks epoch/origin linkage for each candidate. A restored
material epoch is not confused with a newly created store's runtime generation.
No full-history authenticity or restart-file qualification is claimed.

Only standalone private P5 models are admitted here. Shells, legacy joints,
public aliases and default activation remain outside this candidate. The
element binds physical reference triads and exact nodal DOF ownership. Its
reference stiffness is the native virgin stationary Hessian required by the
driver's constraint reduction, not a legacy linear stiffness surrogate.
Mass, geometric-stiffness, out-of-transaction force, stress and serialization
routes remain explicitly unavailable in this private adapter.

## Development incident and verification

The first actual-driver smoke failed before Newton iteration because the
private adapter deliberately rejected the reference stiffness request.
Trace: `solve_static_nonlinear -> assemble_stiffness_matrix ->
compute_stiffness_matrix`. Added the native virgin Hessian route and verified
it against the independent assembly of the preserved reference-linear blocks
and their Schur complement. This checks compatibility with prior research,
not a newly independently authored mechanics oracle. Its numerical spectrum
has six rigid modes and twelve positive modes in this small fixture.
No coefficients, tolerances or scientific evidence were changed to obtain a pass.

- First smoke: one failed in 1.90 seconds (missing reference K0 route).
- Corrected curved plastic smoke: one passed in 4.27 seconds.
- Expanded native-driver tests: eleven passed in 10.11 seconds.
- Final integration regression: **99 passed in 32.31 seconds**, covering the
  13 new driver/protocol tests, previous private material/chart tests, native
  rotation store, nonlinear state batches and nonlinear-static state lifecycle.
- Separate accepted-P3 interface regression: **21 passed in 3.23 seconds**.
  Do not combine these inventories into one scientific count.

The actual public `solve_static_nonlinear` completed two-step straight and
curved coupled plastic cases. Exact snapshot linkage verifies that the second
accepted origins are the first accepted histories and final state is the last
accepted snapshot. An explicit always-on line-search run passed. A one-iteration
failure with cutback disabled retained the virgin committed state rather than
publishing the failed trial. Late validator failures, corrupted/resealed trial
and initial states, missing candidates, protocol mismatches, deletion and
unbound contexts are rejected before commit. Callback-copy isolation is tested.

All tests used Python 3.13, `-B -m pytest -p no:cacheprovider`, `-q --tb=short`,
one thread for OMP/OpenBLAS/MKL/NumExpr and fresh external temporary basetemps.
These are small correctness cases (at most two private macrocells), not a
performance or large-mesh wave. Newton cases use at most ten iterations per
step and no load-step cutback retries; the failure case allows one iteration.
No resource request was created, consumed or retried. No long formal run ran.

## Remaining qualification and next work

This is a local implementation checkpoint, not independent acceptance or a
formal candidate freeze. The new store protocol needs independent review and
broader lifecycle tests before integration. Source changes are explicit; this
checkpoint and the entire inherited branch are not research-only extents.
No B2/B3, Q4/S3 coefficients, state laws, recovery, aliases, defaults, version,
package metadata or historical evidence were modified. No push or release.

Next: native restart/recovery and nonzero-history continuation through the
actual driver; cancellation and cutback cases; load-program/displacement/
arc-length paths; native mass/current-state tangent integration; general
objective nonlinear section adapters; then the missing engineering, locking,
prestressed modal/buckling and independent-review qualification gates.
The preserved onset sign uncertainty and compensated-coordinate interface gap
remain open. Beam-shell connection qualification remains a separate required
part of the overall goal. Existing research evidence is not a substitute for
any of these requirements, and no public curved P5 activation is authorized.
