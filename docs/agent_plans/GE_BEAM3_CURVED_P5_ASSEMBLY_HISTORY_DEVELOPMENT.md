# P5 connected nonlinear histories — 2026-09-06

Author research successor to `4c3ecff2acf77fb6269cc6e1a39089b01e8754f4`,
tree `6c0278a7956d500ffb2cecc63d0683e94843854b`.
The previous turn completed a validated one-element research restart codec.
This turn adds connected finite-state assembly and whole-model transactions.
It does not qualify a production element or connection.

## Assembly and shared rotation authority

The new probe admits one through eight connected three-node beam elements,
with explicit integer connectivity, one section per element and initially
fixed six-DOF node clamps. Node IDs must be contiguous; duplicate element node
sets, repeated element nodes, disconnected graphs, invalid clamps and
inconsistent shared reference coordinates are rejected. References and section
objects are copied. Shared reference coordinates agree exactly.

Each global node stores its position and a spatial deformation rotation U,
initially identity. An element's current material triad is Q_ei = U_i R0_ei.
Thus shared rotational increments are unique but adjoining elements retain
their own reference tangent and anisotropic material roll. A shared node need
not have identical element reference triads. Positions update additively and
U updates by left multiplication with Exp(delta-theta); no accumulated
rotation vector is introduced.

Each element uses the existing mixed nonlinear density, local stationary
solve and condensed 18-coordinate tangent unchanged. A deterministic scatter
adds its energy, residual and tangent into the common global DOFs. Each
element receives its own complete committed station-origin tuple, unchanged
throughout all local solves and global line-search candidates. Applied loads
are spatial dead nodal forces only. This is not a follower-couple, distributed
load, MPC or beam-shell connection implementation.

## Bounds and convergence correction

Global trials allow at most 16 Newton updates and ten line-search candidates
per update. The total mixed-evaluation budget is 256 times the element count,
counting all element evaluations, including unsuccessful local attempts.
Each local solve retains the preceding 25-update, 12-backtrack and 64-evaluation
bounds. Callers may lower, not raise, the global budgets. There is no automatic
retry or load cutback. `response_at` uses at most 64 evaluations per element.

The first 18-test development run had one failure: the copied maximum-component
global convergence measure admitted a combined free-force Euclidean residual
of 1.0922299387118396e-11. The new assembly driver now requires a Euclidean
norm of all free forces and length-scaled free moments, divided by
max(1, Euclidean applied-force norm), to be at most 1e-11. This norm is invariant
under spatial rotation. No prior single-element code or accepted evidence was
changed and no tolerance was relaxed. The reaction test was also corrected
to sum current-position force lever arms, not bare couples alone.

Formal qualification still requires separate process-tree, memory, activity
and wave watchdogs and the resource authorization protocol. These ordinary
small tests are not a formal execution or a performance study.

## Whole-model state safety

A global trial binds its epoch, positions, common rotations, loads, nested
element/station origins, every element response, assembled response and
convergence/evaluation metadata. Only the instance-owned current unaltered
trial may commit. Commit reconstructs every element from the accepted local
rotations, moments and original histories, with no Newton solve. It verifies
exact response reproduction, local stability, station inventory, assembled
equilibrium and fixed nodes, then validates all new station histories.

New geometry, every element's histories and accepted replay data are fully
allocated before one checkpoint-tuple publication. A late element or final
station failure leaves all prior geometry/history/replay unchanged. No
element publishes independently. Exposed committed states are defensive
copies; accepted trial data is copied before publication. Stale, foreign,
altered and discarded trials cannot commit. Budget failures do not advance
the checkpoint.

These are single-process research transactions, not thread-safe concurrent
model editing or persistent crash recovery. The previous restart codec still
accepts only its original one-element model; it was not broadened implicitly.
An explicit assembled restart schema and tests remain to be implemented.

## Observed two-element material cycle

The height-0.4 parabolic reference uses two macro elements (five global nodes),
the existing coupled directed-hardening section and eight stations per half:
32 station histories in total. Tip force is amplitude times [0.1,-0.3,0.2].

| Amplitude | Updates | Mixed evaluations | Global residual norm | Plastic stations per element |
|---:|---:|---:|---:|---|
| 0.1 | 5 | 34 | 3.37540e-15 | 16, 16 |
| 0.2 | 6 | 54 | 1.39052e-14 | 16, 16 |
| 0.1 | 4 | 62 | 8.26591e-12 | 0, 0 |
| 0 | 4 | 30 | 9.68751e-15 | 0, 0 |
| -0.1 | 4 | 30 | 4.69579e-15 | 0, 0 |
| 0 | 4 | 30 | 3.17501e-15 | 0, 0 |

The final permanent tip displacement is approximately
[0.1261288,-0.06212812,0.08157447]. The negative segment of this particular
cycle does not reactivate plastic flow. Histories remain monotone in their
accumulated variable and all stations have nonnegative dissipation increments.
This coarse result differs substantially from the prior single-element load
path. It is not evidence of nonlinear mesh convergence or a validated plastic
engineering solution. The cycles also have different initial loading samples;
do not attribute the entire difference to discretization without a controlled
comparison. Nonlinear quadrature and independent reference checks remain open.

## Verification and preservation

- New assembly suite: **20 passed in 12.73 seconds**.
- Existing seventeen P5 suites: **291 passed in 32.97 seconds**.
- Checks cover one-element agreement with the prior history driver, manual
  matrix scatter and virtual work, reference-linear tip compliance against
  the existing equilibrium/flexibility construction, a common-chart finite
  tangent directional check at 1e-7, symmetry and covariance at 1e-11,
  shared-node action/reaction, current-geometry force/moment balance,
  per-element material sections and distinct shared reference rolls.
- A reversed element with the prescribed section transform reproduces the
  assembled response. This is not a full reversed-history campaign.
- Injected final-element and last-station commit failures leave the complete
  prior checkpoint unchanged. Mutation, budgets, stale/foreign/discarded
  trials, Newton-free replay and defensive state copies are tested.
- A separate default-order load step commits/replays 48 stations per element,
  96 total. No equivalence with the 32-station cycle is asserted.
- A four-element closed piecewise-quadratic ring retains six binary64 rigid
  modes, a positive remaining spectrum and a zero-strain response under a
  large common rigid motion. It is a quadratic approximation, not an exact
  circular geometry or a qualified ring engineering/modal benchmark. Its
  adjacent reference tangents may differ at the shared vertices.

Driver SHA-256:
`75F1E381361A2028490CC3668D2EDF89F0491F615C392F1F0C3BC176FC9FA0E0`.
Test SHA-256:
`21D870DE503DF31A2157774D551BD17AF3818F8C822BF68E3DD7D99CD98845E7`.
These bind inspected working-file bytes.

Only the new research driver, test and this record are added. No source under
`src/`, existing B2/B3/Q4/S3 mechanics, recovery/state law, default, package,
dependency, workflow or historical qualification evidence is changed. No
source freeze, formal resource request, independent review, push, merge,
release or activation occurred.

## Next work and full-goal limits

Continue in the P5 worktree on `codex/ge-beam3-curved-p5-objective-lift-v1`.
Use controlled identical load schedules across discretizations and independent
nonlinear references before interpreting the coarse plastic response. Add
assembled restart identity/continuation rather than reusing the single-element
schema. General section adapters, nonlinear integration accuracy, the extreme
coupled local failure, arc length, compression/postbuckling, prestressed
modal/buckling, dynamics and curved/slender domain qualification remain open.
The reference-linear ring result does not close these finite-state gates.

Independent mechanics authorship/review, installed-wheel production integration
and objective eccentric/curved beam-shell connections remain required by the
full goal. This research shared-node beam assembly is not shell coupling.
No overall qualification claim is made. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
