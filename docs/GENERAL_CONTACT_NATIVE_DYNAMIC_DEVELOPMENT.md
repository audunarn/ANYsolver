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

`create_checkpoint` and `restore_checkpoint` currently raise `NotImplementedError`.
Durable restart needs complete dynamic state validation and fresh-owner reissuance;
the native static checkpoint is insufficient. This is the next integrated slice.

## Evidence and remaining limits

The independently assessed default API fixture passed two endpoints and ownership
controls, with energy/linear/angular momentum defects within its unchanged gates:
`d1_review_support/native_dynamic_interface_v4_20261001.summary.json` and
`D6_NATIVE_FREE_TEMPORAL_REVIEW_20260930.md`. The preceding strict `1e-15` API fixture
failed before its first accepted endpoint and remains NONPASS; its cause is not
assigned by the default success. Earlier full-amplitude and momentum-refinement
failures also remain. Smaller-vibration tighter-solve results are separately bound.

No general temporal convergence, contact impact, restart, installed-package
admission, broader native scope or full C7 acceptance follows from these results.
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
