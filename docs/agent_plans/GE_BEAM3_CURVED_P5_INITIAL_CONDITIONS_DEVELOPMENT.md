# P5 explicit dynamic initial conditions

Parent `ca8243bcf38dc870e3804fa57d844a140422559e`, tree
`ef935004611f00e71b344c1d1eb0130521a55170`.
Add only this plan, a research initialization module and tests. Preserve all
existing mechanics, restart codecs, scientific evidence, aliases and defaults.

## Request and model identity

An explicit request binds the expected pristine physical model hash, desired
nodal positions, two cell rotations per macro, nodal translational velocities,
cell spatial angular velocities, nodal dead forces at time zero and shared
trace seed rotations. Missing optional fields mean reference/rest/zero values,
not inferred history. Copy and validate finite dimensions and proper SO(3)
matrices; clamped nodes retain reference positions, identity deformation
rotations and zero translational velocity.

The request is caller-supplied data, not a resource approval or scientific
qualification certificate. Initialization returns a new model and leaves the
expected model untouched. It is allowed only from a pristine expected model,
not as a hidden reset of an accepted/pending trajectory. Predeformation is
admitted only within the existing reference, rotation-chart and stable
algebraic-trace guards; this does not establish arbitrary-strain material
validity or plastic preload history.

Use a distinct initialized-model identity binding the physical model and
request digest, while reusing unchanged dynamic assembly equations. Keep the
accepted request/initialization receipt attached for the whole trajectory.
The old exact-type reference/rest restart codec must reject this model,
including its underlying engine, rather than losing initialization authority.
A matching initialized-model restart successor is required next.

## Consistency calculation

At fixed requested positions and cell rotations, solve the assembled free
nodal trace equilibrium using the preserved bounded root solver. Do not change
requested physical velocities or project away physical cell spins. Verify the
free trace tangent is symmetric/positive definite on this branch.

With p denoting physical translation/cell-spin coordinates and t the free
massless traces, recover the consistent trace rate from

    Ktt wt = -Ktp vp.

This is the derivative of the shared algebraic constraint, not trace inertia.
Assemble the full physical mass and convective inertia and solve

    Mpp ap = Fp - Felastic,p - Fconvective,p.

Clamped accelerations/rates remain zero. Retain endpoint force, full rate,
physical acceleration, energies, spatial momenta, constraint/balance residuals
and trace-solver counts in a deterministic initialization receipt. No trace
angular acceleration or plastic/internal history is fabricated.

All equations use the existing operators. Checks use the existing 1e-11
normalized balance rule; first directional constraint-rate checks use 1e-7.
Retain root bounds (eight updates/64 evaluations/ten backtracks), one numerical
thread in tests and a 600-second operation watchdog. No automatic retry.
Validate and construct everything before returning the initialized trajectory;
failures expose no partial model and do not mutate the expected caller.

## Verification and remaining scope

Check reference/rest equivalence, exact uniform free translation, curved
predeformation with noncommuting spins, differentiated trace constraints,
physical initial acceleration balance, observer covariance, clamp/model/input
rejection, bounded failure, preserved input ownership, deterministic receipts,
initialized trial/commit/discard/replay and legacy-codec rejection.

These are bounded small correctness tests, not a qualification wave. A strict
initialized restart codec, native solver/material-state integration, broader
engineering checks, independent review and beam-shell connections remain open.

## Observed development result

The initial 14 tests passed in 14.04 seconds. After adding the initial-force
full-mass comparison and large common rigid-rotation check, the initialization,
dynamic assembly and preserved reference/rest restart suites passed **87 tests
in 75.14 seconds**. Sixteen tests are new initialization checks. No mechanics
or tolerance correction was needed; no formal resource request was consumed.

Reference/rest initialization preserves physical results while carrying a
distinct model identity. A free curved chain with nonzero uniform translation
continues for three steps without artificial rotation or loss of velocity.
Curved predeformation retains the exact requested nodal and cell velocities;
its shared trace rates satisfy a separate directional constraint derivative
check and its acceleration satisfies reassembled physical force balance.
Single-macro acceleration, energy and spatial momenta agree with the existing
separate time-reference calculation (shared mechanics, not an independent
physical oracle). Initial nodal-force acceleration also agrees with the
separately assembled reference full-mass system.

Observer covariance passes for positions, rotations, rates, accelerations and
spatial momenta. A common rigid rotation with vector (2.6,-1.4,0.8), whose norm
exceeds 0.9 pi, is correctly admitted because the guarded relative rotations
remain small. Its elastic energy is zero to the existing check and consistent
shared trace rates recover the prescribed common angular velocity.

Deterministic initialization receipts, public-copy ownership, initialized
trial/commit/discard/replay, model/clamp/input rejection, failure atomicity and
watchdog checks pass. Initializing over a pending/accepted trajectory is
rejected. The old restart codec rejects both the initialized wrapper and its
underlying distinct engine class, preventing silent loss of initial-condition
context. An initialized restart successor remains unimplemented; these tests
do not qualify that missing capability or invent a plastic preload history.

Only this plan, the initialization module and its tests are added. All prior
tracked files, including accepted P3/P4 evidence and every P5 operator/restart
module, remain unchanged. No production routing, API, package, dependency,
default, release or qualification claim changes. `git diff --check` passed.

## Prioritize the remaining production goal

A read-only check of `src/anysolver/ge_beam3_element.py` and the accepted P3
integration plan confirms that the existing opt-in facade still exposes the
accepted straight P2 mechanics and limited P3 routes. P5 curved mechanics and
history-bearing section work remain research paths. The current branch has
eight earlier GE-B3 source additions relative to main; only this step has no
production delta. Do not describe the entire branch as research-only.

Next, audit and map the P5 static/material-state, mass/modal, current-state
buckling, recovery and restart requirements to the actual native solver
interfaces, then implement a separately identified private integration
successor without modifying the accepted P3 formulation or aliases. This is
more directly on the path to the requested standalone production beam than
indefinitely extending finite-transient research. Keep initialized-dynamics
restart and other dynamic limitations explicitly open; do not use them to
inflate qualification or silently broaden a public route. Beam-shell
connection qualification and independent scientific review remain required
for the full goal.
