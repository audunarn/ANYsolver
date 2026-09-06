# P5 retained-inertia native reference-modal integration

Parent `5adfdc7debf0cb859b66254e86bc7de9425adc68`, tree
`70764c07d2ef08b88f36ef0e4a2ff1b42184388d`.

## Scope and interface

Add the private source module `anysolver._native_reference_modal` and a P5
research adapter. This is a native FEModel/DOF/constraint integration step,
not public `solve_free_vibration` registration or production qualification.
The module imports no research or element mechanics. Its caller supplies
immutable elastic/kinetic factors and a mandatory bound-input guard.

The P5 adapter accepts only exact private DriverP5Element objects and a complete
explicit map of SPD 6x6 section inertia matrices. It copies the inertia inputs,
binds the reference geometry, physical section, element identity, native DOF
ownership, boundaries and factor packets, and rechecks these identities around
factor construction, assembly, constraint reduction, eigensolve and output.
Caller-owned inertia arrays are not live after capture. No station state is
created, committed or advanced by this reference-elastic path.

The adapter uses the existing reference factors at each private element's
declared quadrature order. The old kinetic helper also constructs a diagnostic
Guyan map; that map and its reduced mass are **not consumed by this solve**.
The mechanics, factors and historical proof files are unchanged.

## Retained inertia and shared equations

Each P5 packet has 18 nodal coordinates plus six cell-spin coordinates. Only
the 12 endpoint moments have already been eliminated from its elastic factor.
Every internal cell-spin coordinate is retained dynamically. Nine nodal trace
rotations per isolated element have exactly zero kinetic-factor columns.

The native assembler first assembles shared nodal DOFs and allocates separate
internal DOFs in ordered element-ID order. It rejects conflicting declarations
at shared DOFs. It uses the actual common constraint transformation, then solves
the **assembled** free zero-inertia trace equations by a QR/least-squares map.
It never eliminates an inertial cell coordinate or balances each incident
element's trace independently. Condensed elastic and mass matrices are formed
from retained energy factors, not subtraction of large Schur blocks.

The reduced physical mass must pass Cholesky without a mass floor, penalty,
pseudoinverse or numerical mass-kernel inference. Eigenvalues are returned raw,
including negative/near-zero values. No rigid-mode filtering or eigenvalue
clipping is performed. Mode signs are deterministically selected; this is not
a promise of invariant individual vectors within repeated eigenspaces.
Nodal and element-owned internal modal fields are both returned, along with
the full pencil, reduction map and bound identities. Arrays are byte-backed
read-only snapshots. Free-row full-pencil residual and modal mass normalization
are checked at the existing normalized 1e-11 development tolerance.

## Fail-closed limits

- Reference-elastic analysis only, not committed/prestressed modal analysis.
- Homogeneous nodal supports or free models only. General MPCs, affine supports,
  point masses and activity/deletion fail rather than being ignored.
- No beam-shell joint, transient, public factory, public mass API or restart
  schema change. The private element's nodal-only mass API still fails closed.
- Dense private models are limited to 256 augmented coordinates. This is a
  development scope bound, not an engineering or runtime acceptance criterion.
- Cooperative cancellation is checked before and after input guards and at
  solve stages. It cannot interrupt a synchronous LAPACK call; this is not a
  replacement for formal process-tree/time/memory supervision.
- `production_qualified=false` is explicit in every returned result.

## Checks completed

Initial four straight/curved one-/two-element smoke checks passed in 1.58 s.
The first complete 24-test implementation set passed in 1.85 s. No failure
or scientific terminal was reclassified and no failed resource request retried.

The final expanded combined correctness suite passed **124 tests in 34.12 s**;
one unrelated CLI-report test was explicitly deselected. This is one combined
development regression inventory, not an addition of earlier test counts or
a formal qualification inventory:

- `test_ge_beam3_curved_p5_native_modal.py` (30 tests)
- `test_ge_beam3_curved_p5_native_driver_probe.py`
- `test_ge_beam3_curved_p5_native_restart_recovery.py`
- `test_ge_beam3_mixed_p3_optin.py`
- `test_native_rotation_state.py`
- `test_constraint_audit.py`
- `test_fe_solver_mass_modal.py` excluding `validity_report_cli`

The new tests cover preserved full-inertia pencil equality, six free rigid
modes, nonzero incident/shared trace moments summing to zero, internal modes
with every nodal DOF fixed, non-Guyan cell-spin response, deterministic output
with reversed element insertion, actual DOF mapping, cancellation, ownership,
input/hash/factor mutations, exact zero-inertia declarations, unsupported
routes and read-only output. Separate direct station-velocity integration
checks kinetic energy; the uneliminated 36-coordinate stationary Hessian's
moment Schur complement checks the supplied 24-coordinate stiffness. These
checks share existing source-equation helpers and are not an independently
authored scientific review or a new continuum qualification campaign.

Tests used Python 3.13, one numerical-library thread, `-B`, disabled pytest cache,
and fresh temporary basetemps. No benchmark, large mesh, formal wave, resource
request, ledger row, external authority or publication was created.

## Continuation

Retained-inertia reference-modal assembly is now available to the private
native candidate. Remaining work includes independently reviewed engineering
modal checks and public solver integration under explicit qualified capability
authority; committed-state/prestressed full-inertia operators and buckling;
broader material/load parity; and the separately qualified objective joint.
Do not substitute this reference-only result for any of those gates. The
fine-mesh compensated-position integration and unresolved lateral critical-point
sign from the preserved 32-macrocell diagnostics also remain open.

P3/P4/P5 accepted and failed evidence remains unchanged. Existing B2/B3/Q4/S3
mechanics, selectors, defaults, package versions and recovery are unchanged.
This checkpoint **adds a private source module**; do not describe the full
branch as research-only or as having no source-code delta. No push, merge,
tag, release or activation is authorized by this checkpoint.
