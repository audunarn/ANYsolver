# P5 bounded finite elastic path and transactions — 2026-09-05

Author development successor to `84ee2fa60a03a2405d6d3dfa4f648b85fd8110f7`.
This is research implementation/evidence, not a frozen formulation, production
solver integration, nonlinear material-state protocol or independent review.
The complete beam and beam-shell programme remains active and incomplete.

## Motivation and preserved failure

The earlier high-contrast, fully coupled, amplitude-one prescribed configuration
still fails local equilibrium. Its sampled spin derivatives suggest motion
toward a logarithm/chart boundary but do not prove nonexistence of an admissible
stationary solution. That case, its rejection test, its coefficients and all
earlier records remain unchanged. It has not been excluded or reclassified.

This successor instead connects successful finite local mechanics to a small
force-controlled boundary-value solve and explicit global-state transactions.
It establishes that a finite elastic loading/unloading path can be followed for
one declared coupled curved specimen. It does NOT resolve the extreme prescribed
state, establish section-domain coverage, or authorize rejection of arbitrary
loads in a finished production formulation.

## Bounded research driver

`FiniteCantileverPathProbe` has one three-node macro element, six DOFs at each
node, and the first vertex fixed in all six DOFs. The section is an immutable
copy of a fixed symmetric-positive-definite 6x6 matrix. It accepts spatial dead
nodal forces only, as a 3x3 array. Nodal couples, follower loads, nonlinear
sections, restart and multi-element assembly are not exposed by this driver.

The existing retained scalar-potential probe supplies internal residual,
analytic tangent, local equilibrium and Schur condensation unchanged. Each
global Newton trial updates positions additively and nodal matrices through
`Exp(dtheta) Q`. Rotation vectors are increments, never accumulated state.
Every individual increment must be below 0.9*pi; endpoint matrix wrapping is
not allowed to conceal a multiple-turn increment. Existing local spin and
relative-log guards remain in force.

Global residual merit uses free-node forces and moments divided by the reference
maximum nodal separation, normalized by max(1, largest applied force component).
The threshold is 1e-11. These are declared research units/scales, not a proof
of a complete coordinate/unit-invariant production convergence policy. Internal
local residual checks remain unchanged at 1e-11.

There are at most 16 global Newton iterations, 10 line-search candidates per
iteration and 48 complete local/Schur evaluations. Local solves retain their
25-iteration and 12-backtrack limits. Failed local evaluations consume the
global evaluation budget. Limits can be reduced but not enlarged by arguments.
There is no automatic load-step cutback or external resource-request retry.
Singular/nonfinite solves, exhausted budgets and unsuccessful line searches
raise a typed failure and return no accepted partial state.

These algorithmic bounds do not replace process/resource watchdogs needed for
future formal qualification. Only small ordinary development/unit commands
were run here; no resource request, authority record or formal run was created.

## Transactions

- `trial` starts from the committed configuration, invalidates any earlier
  pending trial, and does not modify committed state.
- Only a successfully converged, current, instance-owned trial may be committed.
- A canonical digest binds all trial fields. Modified arrays, stale trials,
  foreign trials and repeat commits are rejected.
- `discard` clears pending data without modifying committed state.
- Committing copies positions, nodal matrices and applied forces and advances
  the epoch. Exposed snapshots are copies; input arrays are not retained by
  reference.
- A failure after a successful intermediate Newton update still leaves the
  previously committed configuration intact. Failed line-search evaluations
  are bounded and counted.

This is a one-element elastic transaction implementation. It does not supply
objective material trial/commit/discard, plastic/fibre history, persisted
restart fingerprints, or a production transaction API. The digest detects
accidental trial mutation; it is not a security boundary against arbitrary
in-process modification of private Python attributes.

## Observed load path

Reference: existing `reference(0.4)`; complete coupled `section()` fixture.
The only applied load is the tip force `amplitude*[0.1,-0.3,0.2]`.
The prescribed sequence is 0.1, 0.5, 1, 0.5, 0, -0.5, 0. No failed load step
was automatically retried and no criterion was changed to accept the path.

| Amplitude | Newton updates | Full evaluations | Normalized free residual | Internal energy |
|---:|---:|---:|---:|---:|
| 0.1 | 3 | 4 | 3.24317e-12 | 0.00102488917 |
| 0.5 | 4 | 5 | 3.05311e-15 | 0.0237169193 |
| 1 | 4 | 5 | 2.91156e-14 | 0.0860758035 |
| 0.5 | 4 | 5 | 1.66533e-14 | 0.0237169193 |
| 0 | 4 | 5 | 1.02496e-13 | 2.01630e-27 |
| -0.5 | 4 | 5 | 1.11050e-13 | 0.0284302393 |
| 0 | 4 | 5 | 4.99132e-13 | 1.68591e-26 |

At amplitude one the tip displacement is approximately
`[-0.0315682,-0.388530,0.338361]`, with norm above 0.5 for endpoint separation 2.
Unloading returns positions and triads to the reference within 1e-11; the repeated
half-load state agrees within 1e-11. These results are not a finite engineering
oracle comparison, postbuckling result, plastic-history check or locking test.

## Checks and provenance

New focused suite: **17 passed in 7.40 seconds**.
Existing ten P5 research suites: **157 passed in 11.63 seconds**.

Tests separately check current-geometry force/moment balance, proper nodal
rotations, unchanged clamp, rigid rotation of reference/load/solution, agreement
with the original local scalar potential, loaded tangent and virtual-work
directional differences, tangent symmetry, deterministic repeated output,
loading/unloading/reversal, budgets, later local failure, mutation detection,
copy isolation, discard, ownership and stale/repeat-commit rejection.

Derivative/work finite differences use the existing 1e-7 check; equilibrium,
covariance and symmetry checks use 1e-11. They share the author and underlying
AD/metric implementation and do not constitute independent qualification.

- Probe SHA-256:
  `CC06857CA8D46C80D8B16187A1F14F590393BB5A710BD743C1883070D6B40192`.
- Test SHA-256:
  `C5455A2D5B80F8F49C82195156F7DD754A14FC8BD1EF7D27814B6EEAFF53EC91`.

Only the new research driver, test and this record are added. Existing B2/B3,
Q4/S3, defaults, production recovery/state, dependencies, workflows, package
metadata and accepted P3/P4 evidence remain unchanged. No push, merge, release,
selector activation or qualification authorization is supplied.

## Remaining work

Continue finite coupled-domain/cutback analysis without deleting the preserved
failure. Extend independently checked reference mass/modal behaviour and finite
engineering references. Nonlinear station-owned material history, multi-element
Newton/arc-length/postbuckling, precision-safe state/restart, load classes,
prestress/buckling, straight/curved domain qualification, installed-wheel
integration and objective eccentric/curved beam-shell connections remain open.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
