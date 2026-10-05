# Retained native beams and multiple S3 interiors — development profile

**4 October 2026. Implemented and tested; no independent engineering acceptance or release.**

Profile: `NATIVE_B3_GE_MULTIPLE_ELASTIC_S3_INTERIORS_STATIC_DEV_V1`.
Source parent: `f59efb58ad2728a3396d424c0e63c511a85fd649`; the local commit
containing this guide binds the candidate. Raw source/import hashes are retained.

## Usage and exact scope

Run `python examples/general_contact_native_multiple_s3_static.py` with ANYsolver
installed. It solves two curved native beams against two deformable physical S3
skins, including a shared target. The one-beam variant uses `analysis(beams=1)`.
The public opt-in factory `anysolver.general_contact.create_native_contact_analysis`
takes native definitions, supports, an explicit retained dead-load `Program`, a
shell-only `FEModel`, immutable `NativeS3ContactPair` records and dimensioned controls.
Native elements remain under `NativeBeamAnalysis`; they are not inserted into the
shell FEModel. The old single-native/single-S3 factory/profile and restart remain.

This owner admits one or two exact retained generalized native elements and two
through eight distinct explicit pairs. Every native beam and shell element must
participate; at most256 combined coordinates. Shells are exact elastic S3 V2D with
reference structural stiffness, physical skins/offset work and zero supports.
Static mechanisms, stale maps, duplicate physical pairs and excess resources fail.
Individual S3 interior/rim-clearance limits remain; there is no patch-union, physical
rim, native cap, beam–beam, friction, dynamic or nonlinear-shell admission here.
Native section/history infrastructure is retained; the tested section is the
ellipsoidal elastic fixture. Other section/material combinations are not qualified.

## Equations, geometry and state

One shared native context retains physical nodal/cell rotations and the18 algebraic
resultants per element. Full local42-native plus global-shell residual/Hessian
blocks are scattered before constraint reduction. Only the native principal block
receives spatial rotation-chart conversion; native–shell cross blocks are retained.
The shell pullback includes physical offset couples. Each consumed combined CSR map
must equal `block_diag(I42, physical_skin_map)` and its exact arrays bind identity.

All pairs see the same candidate and committed history origin. Each pair independently
checks its gap, rim, integration and conservative retained-path budget. Angular
limits and swept work use that beam's own24-coordinate internal block. Only after
complete equilibrium/correction and every pair gate do histories, shell displacement
and the checkpoint chain commit. Cancellation, later-pair exceptions and failed
trials preserve the last complete accepted capsule. Restart replays records and
rejects changed definitions/settings or external hashes.

Quadratic gap stationary points determine the geometric minimum. Activation roots define mandatory active partitions. Resolved optional stationary
partitions remain for legacy diagnostics; only an artificial near-end partition
is omitted, with its extremum still included in the minimum. Unresolved activation
intervals remain failures. Affected legacy kernel/owner checks passed.

## Verification actually run

Private installed target: `C:/ANYworkspaceWork/contact_native_multi_s3_20261004/installed2`.
Wheel SHA256: `f89bba5f77c01e2b6f8c4d9c95876b52dfef5eaade697a74983979fb3af88148`.
Installed29 checks passed in60.473s, peak332218368 process-tree bytes. All206 imported
modules and510 package Python files match source bytes. Effective JIT disabled,
Numba/BLAS1, bounded180s/953MiB. No complete-route speedup claim.

- Independent direct retained curve/ordered physical-skin scalar energy and work,
  including internal motion with exterior node positions exactly fixed.
- Complete algebraic-zero geometry rows, native–shell cross blocks, physical contact
  force/moment balance, constrained reactions and actual two-deforming-skin solves.
- One/two-beam smooth spatial tangent errors1.360e-9/1.530e-9 versus1e-5; equilibrium
  metrics below5.34e-14 versus1e-8. Minimum gaps about-0.0005351m versus explicit1mm.
- Byte-identical split restart, iteration failure, cancellation, later-child exception,
  changed map/settings/hash rejection and resource limits.
- Second beam cell-1 rotation within the actual advance/support contract: both end
  poses open, intermediate penetration rejected. Differing pair gap budgets checked.
- Actual runnable two-beam example and ordinary no-contact lazy path, plus affected
  legacy single-owner, line/S3 geometry and authoritative-work tests.

The scalar oracle constructs the retained quadratic curve and independent roots/
SciPy integration, without calling the production contact/curve kernel. It uses the
ordered moving triangle normal. Coupled residual differences verify the spatial
Jacobian; they do not independently qualify structural spatial accuracy. This is
code-development evidence, not a continuum/native qualification campaign.

## Retained failures and enforcement/path sensitivity

Raw evidence: `C:/ANYworkspaceWork/contact_native_multi_s3_20261004`;
[summary](d1_review_support/contact_native_multi_s3_20261004/summary.json),
[source scrutiny](d1_review_support/contact_native_multi_s3_20261004/support_review.md),
[decision record](d1_review_support/contact_native_multi_s3_20261004/design.md).
Seventeen bounded runs retain87 raw records, including nonpasses:

- Initial positive-gap near-end stationary point partition failure; corrected by
  retaining geometric extrema while omitting artificial near-end stationary partitions.
- Explicit1000N/m2 coupled line penalty reached the unchanged1mm gap cap. It is not
  a passed case. The delivered example explicitly declares10000N/m2.
- Invalid2pi increment and fixed-root movement sweep fixtures failed their actual
  native contracts; corrected valid.8rad/cell1 hidden-path fixture passed.
- Stronger40000N/m2 penalty exhausted bounded merit backtracking for one/two load
  increments. At the same four equal increments,10000 and40000 complete with gaps
  -0.0005350910 and-0.0002688940m. No tolerance/budget increase or automatic algorithm
  switch occurred. This is two-setting sensitivity, not enforcement convergence.

Supporting same-family source review found the work-map binding defect and oracle
normal convention mismatch, both fixed. It is not independent engineering acceptance.
Broader load-path robustness, spatial/enforcement/section qualification, native
beam–beam and beam–shell boundaries, friction/dynamics and the full C0–C9 remain open.
