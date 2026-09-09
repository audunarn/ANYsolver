# GE-B3 retained-fibre translation continuation — development checkpoint

Parent commit `6ff9191c8a55cb8ceaf102772bb5a928e58c1e83`, tree
`c878442e795cadaca1dc0ba34f6b77805739a99d`.
Private development only; independent scientific review remains PENDING.
Existing B2/B3/Q4/S3 mechanics, selectors, defaults and qualification records
are unchanged. No public activation or release is authorized by this record.

## Equations and source boundary

An unknown common multiplier of a spatial dead-load pattern and a prescribed
nodal translation give equilibrium plus one control equation. This is the
standard [displacement-control construction described by OpenSees](https://opensees.github.io/OpenSeesDocumentation/user/manual/analysis/integrator/DisplacementControl.html).
The present native implementation solves the full bordered system rather than
forming a load sensitivity through the inverse of an unbordered stiffness.

Let `y` contain all free nodal increments, cell rotations and retained cell
resultants, and let `lambda` multiply the fixed nodal load vector `f`.
The retained physical-fibre residual `r(y,lambda;origin)` and its derivative `H`
come from the unchanged native stationary potential. Define

`g(y)=d dot (x_control-X_control)`, `a=dg/dy`,

where the control direction `d` is a supplied physical unit vector and the
node's translations are free. The Newton equation at a prescribed target `s`
is

`[H, -f; a^T, 0] [delta_y; delta_lambda] = -[r; g-s]`.

All retained stationary coordinates participate. A simple load limit point
may make `H` singular while this complete border is nonsingular. If the
selected control coordinate ceases to parameterize the path or the full border
is singular, the bounded solve fails closed. It does not silently switch
branches, change the load pattern, regularize the matrix, or retry a target.
This is not general arc-length control or proof of a particular bifurcation.

Every trial is projected onto the same affine translation plane. The control
value uses exact dyadic arithmetic for its three paired-coordinate products,
with one final rounding. A large common reference translation must not erase
the small controlled increment. The direction and loads transform as physical
vectors under a common proper rotation; rotational coordinates remain native
spatial multiplicative increments.

## Globalization correction, not a mechanics correction

The first implementation compared the maximum of raw force residuals and
compatibility errors during line search. On the stiff shallow arch, the first
Newton step greatly reduced compatibility while developing the previously zero
forces; the incomparable residual units forced tiny steps and exhausted the
bounded search before the first accepted state.

For a current full border `B`, the corrected merit is the norm of the frozen-
border correction `B^-1 F(candidate)`, compared with the current Newton-step
norm. At a smooth current state, `F(y+alpha delta)=F(y)-alpha F(y)+O(alpha^2)`,
so this merit has the expected descent direction. The matrix is the complete
border, not `H^-1`, and is held fixed during each bounded backtracking search.
No mechanics coefficients, load cases, final equilibrium/compatibility/control
tolerances, regularization or stiffness floors are changed.

The preserved diagnostic first step accepted a full Newton correction; four
updates reached force/rotation equilibrium error `8.425646975286215e-14` and
compatibility error `1.7721224648365463e-15`, below the unchanged `1e-11` gates.
The original failed source and test outputs remain distinct evidence.

## Material transactions and restart

The physical model is captured once using the existing retained-fibre context
and a load-pattern-only descriptor. No force-controlled path is executed or
translated. A new translation-control schema binds the actual targets,
physical direction, load pattern, model and native operator identities.

At each target, the origin is exactly the previous committed fibre history.
Every Newton and line-search trial starts from that fixed origin. Only an
equilibrated, compatible state on the control plane can be staged. Before
staging, the accepted in-memory mechanical state, material histories, load
parameter and cursor must agree with the preceding accepted record. Full
recovery, reactions and the proposed histories are hash-bound before the
single publication point. Failure or cancellation before publication retains
the preceding complete capsule; cancellation after publication retains the
new complete capsule.

Strict canonical replay regenerates every accepted physical response from the
preceding material history, checks the control equation and actual load
parameter, and regenerates identical bytes. It does not advance geometry or
rerun Newton steps. Duplicate/nonfinite/noncanonical JSON, foreign schemas,
changed targets/directions/loads, altered state/history/recovery, dirty model
capture and rewind requests fail closed. Optional external SHA-256 authority
also protects metadata such as iteration counts, which physics cannot prove.

The existing two-MiB capsule limit and 256-coordinate small-model bound remain.
The controller/context has a 120-second cooperative deadline, explicit bounded
Newton/backtracking counts, inner material cancellation points and progress
events through iteration, trial and commit. There are no automatic retries or
resource-request/ledger operations in these small correctness tests.

## Scientific interpretation and remaining work

The shallow arch is a two-macrocell correctness fixture, not an independently
referenced or mesh-converged engineering qualification. Its load rises to a
local maximum, falls, and rises again on the inverted branch. The original
assertion that the last load must remain below the global sampled maximum was
incorrect; it is preserved as a separate failed test attempt. Correct checks
identify the local maximum and minimum without deleting the late restiffening
samples or changing the physical section or target schedule.

Passing this development lane establishes bounded continuation and state/replay
behavior for the tested cases only. It does not establish buckling factors,
stable-branch selection, an independently qualified critical load, general
plastic bifurcation directions, arc length, automatic cutback, broad arch/ring
and slenderness coverage, finite-velocity dynamics or beam-shell connections.
Those remain part of the full GE-B3 goal, together with independent review and
installed-package/performance qualification.

## Current disposition: required high-contrast case remains failing

Separate inventories:

- Initial smoke: 3 passed, 1 failed; 25.475 seconds.
- Natural-merit correction: 3 passed, 1 failed; 25.962 seconds. The remaining
  failure was the incorrect global-versus-local maximum assertion.
- Expanded state/rotation suite: 29 passed; 44.443 seconds.
- Latest stage-binding/high-contrast suite: **32 passed, 1 failed**;
  44.401 seconds. This is not an accepted or complete qualification cycle.

The latest passing cases include ordinary plastic reversal and exact resumed
checkpoint bytes, rejection of detached accepted states, resealed state
mutations, cancellation before/after publication, replay without geometry
advance, large common rotation (relative load-parameter discrepancy
`1.4432899320127035e-15`) and a `1e-9` controlled translation on a common
`2^30` coordinate offset. The coarse arch completes all eight targets with
equilibrium error at most `1.64568793081242e-12`; it rises to a sampled local
maximum near 297.944, falls to 175.490, then restiffens to 463.825. These
development samples are not a critical-load accuracy claim.

The required contrast-`1e12` reversal case fails before accepting target 1.
At target translation `.01`, the virgin elastic bordered predictor requests a
load-parameter increment `13955094349.613695` and maximum nodal/cell rotation
increment `10361069.606977427` radians. At least 22 halvings would be needed
just to enter the `0.9*pi` chart, beyond the frozen backtracking budget of 8.
Increasing that budget, weakening the chart or removing the case is not an
accepted repair. The failed test remains active. The last complete state is
the virgin capsule; no committed history was lost.

No second deterministic cycle was run after this failure, and no byte-identical
cycle-pair or qualification pass is claimed. Independent review is PENDING.

Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-control-development-20260907-8ede1edf9a8`.
47 content files, 1,521,771 bytes; manifest 7,292 bytes, SHA-256
`5a4334a25c3b440580acd9ac22c7b7472306b7e2ac04ce372fa68b68a279efb4`.
All four inventories and their source variants are preserved. Original
external test outputs remain untouched.

### Next concrete correction

Investigate a compatible material initial state at the projected target
kinematics, before global Newton, using the same physical-fibre potential:

`min_x sum_j w_j W_j(S_j x; accepted_origin_j)` subject to `L^T x=k(q)`.

Its equations are `grad W-Lp=0` and `L^T x-k=0`, with bordered derivative
`[A,-L;L^T,0]`. Solve this bounded local constitutive problem using the known
piecewise-quadratic fibre laws, not a virgin elastic extrapolation beyond
yield. Independently check compatibility, station equilibrium, conjugate
potential/work and fixed-origin histories against the existing resultant-entry
cell. Use it only to initialize trial retained resultants; do not globally
condense the stationary variables or commit trial histories. Preserve all
existing mechanics, chart, step, and final residual limits.

The high-contrast failure must pass before repeating deterministic development
cycles or advancing a qualification claim.
