# Native contact-free dynamics — development use

The separate `anysolver.ge_beam3_native_dynamics` interface composes the retained
native beam mechanics, finite inertia and SO(3) midpoint owner. It is **tested
and independently reviewed for bounded development use**, not accepted C7 or a
released dynamics capability. The historical native static selector is unchanged.

## Run the example

From this source worktree, with its `src` directory on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = 'src'
C:/Python/Python314/python.exe examples/native_contact_free_finite_velocity_dev.py
```

The example uses `define_beam` from the existing public native definition module,
then `create_analysis(SELECTOR, (definition,), ())` from the new module. It advances
two 0.001 s steps and prints JSON provenance, time, epoch and total energy.
The actual main-worktree example passed in 6.282 s with 197.927 MB peak process
memory. Its imported sources and effective default `1e-11` stage tolerance were
checked in `d1_review_support/native_dynamic_main_example_v1_20261001.summary.json`.
This is a routing result, not an energy-conservation or temporal-accuracy claim.

## Admitted development geometry and state

Use one centered elastic generalized ellipsoidal B3-GE element with three ordered
nodes. Supports are free or a homogeneous full clamp at the first node. The
existing signed constant reference-load contract is available. Other sections,
materials, boundaries, multiple elements and contact remain unsupported.

`initialize(positions, cell_rotations, physical_velocity15, position_low=...)`
uses node positions `(3,3)`, native cell SO(3) rotations `(2,3,3)`, and 15 physical
velocities: nine nodal translations, then the two spatial cell angular velocities.
The optional low position part preserves compensated coordinates. Omitted pose
values use the reference pose. Nodal frames are solved algebraic variables;
zero inertial placeholders do not constrain their physical motion. Physical
internal inertia is retained.

Call `trial(state, dt=...)`, optionally inspect `candidate_stage_audit(candidate)`,
then `commit(candidate)` or `discard(candidate)`. States and candidates are immutable,
issued by one analysis lifetime and cannot be transplanted between owners. Audit
snapshots are evidence, not commit credentials. The owner validates current
model/settings identity, cancellation, stale/forged objects and atomic rollback.
Its existing 120 s lifetime resource bound applies; it is not a general long-run
transient driver. `endpoint_accounting` reports compensated momenta and energy.

## Complete committed-state restart — development profile V2

`create_checkpoint()` exports only a committed current state and rejects pending
candidates. The payload includes compensated pose, physical cell rotations,
material histories, physical velocity/acceleration, time, epoch and lineage.
It binds model, numerical settings and the bounded complete package Python-source
manifest. A different source artifact is incompatible, even if its version agrees.

```python
from hashlib import sha256

payload = analysis.create_checkpoint()
trusted_digest = sha256(payload).hexdigest()
fresh = create_analysis(SELECTOR, (definition,), ())
state = fresh.restore_checkpoint(payload, expected_sha256=trusted_digest)
```

Use matching definitions, supports and settings in a fresh, never-initialized
owner. Restore validates the stored state, original algebraic correction witness
and stored-acceleration physical balance without repairing the payload. Old
states/candidates remain unusable as new-owner credentials. Cancellation and
exceptional exits roll back reissuance. Each new owner retains its 120-second
lifetime; restart does not renew an execution authority. Keep physical work and
impulse journals externally: this snapshot does not reconstruct a prior trajectory.
The expected digest is a caller-trusted integrity anchor, not a producer signature.

The free, unloaded, default-tolerance split fixture passes two tests/four steps
in30.857s/205.619MB, with complete state/checkpoint/accounting parity and independent
saved assessment (`native_dynamic_restart_v5_20261001.summary.json`). Exact source is
integrated in main; a separate installed V2 check also passes (details below). This does not
qualify loaded/clamped restart, temporal convergence, impact or C7.

## Evidence and remaining limits

The independently assessed default API fixture passed two endpoints and ownership
controls, with energy/linear/angular momentum defects within its unchanged gates:
`d1_review_support/native_dynamic_interface_v4_20261001.summary.json` and
`D6_NATIVE_FREE_TEMPORAL_REVIEW_20260930.md`. The preceding strict `1e-15` API fixture
failed before its first accepted endpoint and remains NONPASS; its cause is not
assigned by the default success. Earlier full-amplitude and momentum-refinement
failures also remain. Smaller-vibration tighter-solve results are separately bound.

No general temporal convergence, contact impact, installed-package scientific
admission, broader native scope or full C7 acceptance follows from these results.
The separate restart fixture above is limited to its stated development scope.
See the capability ledger and full programme for the outstanding requirements.

### Installed development routing — 2026-10-01

A separate local wheel from source checkpoint4c3ac836 verifies all445 package
Python files and runs both public development examples successfully:17.027s,
194.327MB peak process memory. Evidence:
`d1_review_support/native_beam_installed_development_v1_20261001.summary.json`.
Target:`C:/ANYworkspaceWork/general-contact-native-beam-dev-20261001/target`;
wheel SHA256`8df161b0c70ee9bc2400e9e01f59352c559a366e036f01b704b6d055347f0ff9`.
This closes packaging/routing only; accepted oldartifact and scientific admission
remain unchanged. Source state is bound explicitly, including preserved development
files; a commit label alone is not the package identity.

Installed runtime diagnostics report effective BLAS pools of1 and an OpenMP
pool of32, despite the requested environment value1. No effective whole-process
single-thread or performance-improvement claim is made by this routing check.

### Installed V2 restart development check — 2026-10-01

Wheel18d8046d verifies all446 installed Python sources and runs the actual V2
public example plus the complete split-restart fixture:48.838s/205.586MB,
2example steps plus4fixture steps and2passing tests. Actual profile, restart flag
and default1e-11 tolerance are checked in the target process; every imported
solver module comes from the installed target. All four fixture states and
endpoint accounting match managed V5 exactly. The package manifests differ, so
checkpoints remain bound to their own artifact rather than interchangeable.

Target:`C:/ANYworkspaceWork/general-contact-native-restart-dev-20261001/target`.
Evidence:`d1_review_support/native_dynamic_restart_installed_v1_20261001.summary.json`.
Independent saved assessment in `D6_NATIVE_FREE_TEMPORAL_REVIEW_20260930.md`
closes this installed development routing/state check, not C7 scientific
admission or release. Earlier accepted contact artifacts and failures remain.

### Driven temporal development control — 2026-10-01

One curved free beam with the actual section centroid(.035,-.025,.012)m and
cross inertia passes20constant-line-force steps:4coarse,8fine and8half load over
.004s. The force(.2,-.15,.1)N/m acts on the lifted reference line, not the mass
centroid, and excites the elastic modes. Continuous and discrete midpoint
references retain all15 modes; the spatial matrices are authenticated shared
inputs. Resolved trajectory errors decrease by factors.2514–.2521 under timestep
halving. Maximum nonlinear-to-discrete discrepancy is1.596e-7; energy/momentum
gates pass. Load-halving differences and invariant errors are below their frozen
floors, so no order follows from those comparisons.

Evidence: `d1_review_support/native_forced_response_v2_20261001.summary.json`,
with full source snapshots and bound input. Runtime94.982s/222.003MB; explicit
solve tolerance1e-12, unchanged physical gates and default1e-11. Independent saved
assessment confirms the scoped result. The preceding180s import timeout and40s startup-only trace
are retained; a fresh task-owned Numba cache resolved the cache-creation stall,
verified in the actual target process. No production source changed. This is a
small-motion temporal development result, not native impact or fullC7 acceptance.

### Supported driven response — 2026-10-01

The same curved beam with a homogeneous full first-node clamp passes20steps,
97.500s/222.941MB. A fresh constrained12physical/24algebraic reference checks
trajectories and support impulses. All six clamp rows are retained, including
the algebraic-frame couple and the force moment about the stated origin; fixed
support work is exactly zero. Independent saved assessment reconciles initial
consistency, signed stages, energy/momentum journals, sources and physical gates.
Trajectory refinement ratios.2515–.2524 and support-force impulse ratio.2503 match
the continuous/discrete references. Below-floor results give no order claim.

Evidence: `d1_review_support/native_clamped_response_v1_20261001.summary.json` and
`native_clamped_response_review_20261001.md`. Actual explicit solve tolerance
remains1e-12, physical gates/defaults unchanged. This is temporal development
against shared spatial matrices; it does not establish continuum accuracy,
finite-angle torque-free motion, loaded restart or fullC7.

### Optional acceleration coordinates — local development

`create_analysis(..., stage_coordinates='acceleration')` selects midpoint
acceleration in the15physical Newton slots. Algebraic frame/resultant increments
are unchanged. The default is `increment`. Audits label the selected coordinates
and supply `increment42` for physical displacement/spin interpretation; translations
retain their compensated high/low poses. Restart identity binds the choice.

The named free high-spin step(35,-25,20)rad/s,h=.0005s passes12.030s/222.818MB,
two iterations/no backtracks, with independent saved assessment. Stage residual
2.301e-13 and two directional errors1.376e-12/5.033e-12 meet original gates.
Normalized E/P/H defects2.186e-7/6.169e-8/4.932e-9 pass1e-6. Evidence:
`d1_review_support/native_finite_spin_acceleration_chart_v2_20261001.summary.json`
and its `.review.md`. This tests the chart plus initialized-acceleration Newton
seed; it does not isolate the cause of the old increment stall or qualify a
finite-angle trajectory. The increment NONPASS and preinitializer input-alias
NONPASS remain. No installed chart or fullC7 claim follows.

The later16-step spin screen stopped at step3 on the unchanged energy gate:
three solver commits, two gate-passing endpoints. Stage equilibrium and momentum
passed. A new short four-step half-control at shared0.001s passed all gates;
energy defect ratio.250028 supports timestep dependence, without an order or
full-trajectory accuracy claim. See native_finite_spin_trajectory_v1_20261001 and
native_finite_spin_temporal_half_v1_20261001 summaries/reviews in d1_review_support.
That short control alone did not establish finite-angle coverage or C7 admission.

The native Newton loop now reuses the exact accepted line-search stage, retaining
the same equations and guards. The focused four-step check preserves all physical
state/work/accounting bit-for-bit and reduces stage evaluations20to12. Stale and
accepted-line cancellation controls pass. This is an evaluation-count result;
the instrumented route is not a paired runtime benchmark. See
native_stage_reuse_v2_20261001.summary.json/.review.md. V1 verification failure
from an incorrect context-identity assertion is retained.

The new full-duration N192/T=.008 finite-spin development trajectory now passes
192 original gates with independently verified complete journals. Final cell
geodesics.377595/.378736rad meet the declared.2rad coverage; cumulative normalized
E/P/H maxima3.1974e-7/8.1311e-9/1.0288e-9 meet1e-6. Elapsed684.256s,
peak393.941MB, one explicit840s owner without checkpoint segments. See
`d1_review_support/native_finite_spin_resolution_v1_20261001.summary.json` and
`.review.md`. This is finite-angle development evidence, not temporal/spatial
accuracy, installed admission, native impact or C7 acceptance.

## Batched finite inertia and exact principal spin — development

The centered finite owner now uses NumPy column batching of the same physical
inertia product rules. The original scalar remains the verification oracle;
there is no new differentiation engine, mandatory backend or changed mechanics.
Balanced complete four-step phases show27.46% median reduction, with exact
physical state/work/accounting and derivative discrepancy8.97e-17. This is a
short-route measurement, not general trajectory affordability.

A straight, zero-centroid beam spinning about its longitudinal principal axis
has the independent exact solution r(t)=r(0), R(t)=Rx(Omega*t)R(0). Eight steps
at Omega=50rad/s reproduce.4rad with frame error below3e-15 and the original
balance/state gates. This exact invariant case does not replace verification
of deforming nonprincipal spin. The new batch wheel/public example is verified
with447source matches; all public profile restrictions remain.
See [principal review](d1_review_support/native_principal_spin_v1_20261001.review.md)
and [installed check](d1_review_support/native_inertia_batch_installed_v1_20261001.review.md).

The runtime lifetime defaults to120s. Explicit `runtime_limit_seconds` must be
positive and at most900s; the captured lifetime and setting bind restart identity.
A restart does not renew a trajectory's execution authority. Extended owners
reject the optional local operator-validation scope. These resource controls do
not admit general contact, additional elements or C7 qualification.


### Finite-angle temporal self-convergence — 1 October

The frozenT=.0045s programme reuses N192prefix108 and completes freshN162/N216
with one840s owner each. Required endpoint gates pass; final two cell angles are
about.21325/.21336rad. Measured process costs469.504s/453.947MB and601.339s/543.941MB,
with459source bindings unchanged. No segmentation or owner-clock renewal occurred.

The saved comparison selects common2j/3j/4j states without interpolation. Resolved
velocity/cell-rotation ratios2.857135/2.857119 match expected20/7. Position differences
are below the registered resolution requirement, so no position order or extrapolation
is reported. This establishes empirical second-order-compatible temporal
self-convergence for this named finite-spin fixture, not continuum/spatial accuracy,
a certified error bound, general nonprincipal-motion admission or fullC7 acceptance.
See `d1_review_support/native_finite_spin_temporal_refinement_v1_20261001.comparison.json`
and adjacent `.review.md`. All older failures retain their original meaning.

## Native trajectory controller (development subset, 2026-10-06)

`ge_beam3_native_dynamics.solve_transient(analysis, TransientConfig(...))` adds
bounded multi-step control around the existing native SO(3) midpoint owner.
The new example is `examples/native_contact_free_transient_dev.py` (free or
homogeneous first-node clamp; optional existing constant line load).
Prior private installed manual/split, cancellation and interrupt checks: **3PASS**;
loaded/clamped CLI passes. Full module source runs timed out; C7 stays open.

Here `initial_displacement` is binary64 physical15: nine reference nodal
translation increments followed by two spatial cell rotation vectors, applied
by left SO(3) multiplication. Positions retain compensated high/low parts.
`initial_velocity` uses the same physical15 ordering. The native initializer
solves nodal-frame algebraics and owns all histories, states and candidates.
`dt`, `t_end` and `save_every` come from the existing TransientConfig; default
beta/gamma are unused compatibility placeholders, not a Newmark selection.
HHT, damping, output subsets, stress/recovery and resource overrides refuse.

Only native Newton iteration/backtracking nonconvergence permits bounded
halving; mutation, cancellation and other failures do not switch algorithms.
All candidate accounting and checkpoint/result bytes prepare before one commit.
Genesis and restore preparation run inside the native-owned atomic operation.
Controller-only follow-up checks actual owner.current identity after commit,
including a commit that succeeds then raises: it exposes prepared accepted bytes.
Private native trial receipts capture issuance before return; exact-candidate
cleanup/no-op after native rollback preserves original control signals.

The new V1 controller capsule embeds the exact native capsule and complete step
journal. A trusted external SHA and matching fresh owner are required. Initial15,
dt/cadence/cutback bounds bind identity; t_end can extend. Cadence counts all
accepted steps; final state is always available separately. A split at a truncated
endpoint changes the time grid and is not promised identical to an unsplit run.
Both capsule and result use the existing 2MiB native canonical codec bound.
Endpoint energy/momentum and midpoint load/support work/impulses are diagnostics,
not added energy gates or exact continuous integrals. The fixed-frame clamp
couple is a genuine stage reaction despite zero frame inertia; free algebraics
and resultants are not inertial loads. Source-prepared tests retain separate
force/moment scales; old finite-spin NONPASS is not regraded. Updated private
installed commit/receipt5cases and impacted cancellation1case pass; the original
12s source timeout stays retained. Twelve jobs used231.943637/270s; C7 stays open.

## Manufactured principal-axis loading: installed development verified

`examples/native_manufactured_dynamic_loading_dev.py` prepares the existing public
`solve_transient` route with simultaneous constant distributed force and longitudinal
distributed couple. Its independent helper imports no solver or production kernel.
The geometric ellipse is separately declared: A=pi*b*c, Iy=A*c^2/4, Iz=A*b^2/4,
rhoJx=rho*(Iy+Iz). EllipsoidalGeneralizedSection names a generalized yield law;
it does not establish this geometry or a contact envelope.

The reference requires a free, straight, centered, zero-lift element, world-x
principal axis, diagonal physical inertia, common translations and Rx frames.
a=f/rhoA and alpha=c_x/rhoJx give quadratic endpoint position/angle and linear
velocity/spin. Strains, resultants and elastic storage remain zero. Work is
F dot delta_shift + Cx*delta_angle on this commuting path; angular impulse also
includes the centroid orbital moment about fixed global zero. This is not a
general SO(3) couple potential. Actual half-cell interpolation gives force
weights L/4,L/2,L/4 and physical cell-couple weights L/2,L/2.

Frozen candidate: L=2m, rho=2700kg/m^3, b=.02m, c=.03m, E=1e7Pa, nu=.3,
f=(0,.4,0)N/m, c=(.04,0,0)Nm/m, v0=(0,.1,.02)m/s, phi0=.125rad,
omega0=25rad/s, dt=.0025s, four steps. Native midpoint poses are endpoint
averages, differing from continuum midtime by a*dt^2/8 and alpha*dt^2/8;
reference stages respect that distinction. Separate positive SI input scales
normalize analytic errors (<=.1%) and work/impulse/balance errors (<=1e-6).

The five prepared tests share one observed four-step public trajectory plus
fresh two-step prefix and two-step resume owners: eight native advances total.
Stage observation calls the authentic audit then copies data; it does not
modify mechanics. Exact checkpoint/results restart equality is separate from
tolerance-based analytic comparison. Five installed checks and the actual CLI
now pass at candidate fdbae395 on the held receipt artifact. Worst normalized
reference error is 2.602647347139155e-13; angle increment is .2512091543634712rad.
Full/fresh-split results and complete checkpoint bytes match exactly. Runs used
63.12627979996614/100 separately approved seconds; 36.87372020003386 remains
only for loading. The later connected/shared source is not tested by this artifact.
[Measured evidence](d1_review_support/contact_native_transient_20261006/manufactured_loading_development.md).
Deforming/nonprincipal/spatial/continuum validation and full C7 acceptance remain
open; this invariant candidate supplies no engineering qualification.

The loading candidate preserves the producer's energy labels: raw elastic_energy
is work.mixed_potential=response.potential (strain potential), and total_energy
is kinetic plus strain potential. It independently verifies line_force_work,
then separately derives conservative potential/total by subtracting that work.
The derived total increment is physical load work minus line-force-work change;
these extra checks do not relabel or alter native accounting. A contrary early
review finding was withdrawn after constructor/source inspection; both the
initial source snapshot and resolved review delta remain in raw evidence.
