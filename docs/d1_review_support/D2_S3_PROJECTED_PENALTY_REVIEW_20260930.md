# D2 S3 projected finite-penalty independent review — 30 September 2026

## Disposition and ownership

Scoped local development review: the S3 admission/work plumbing and operand-roundoff correction have no remaining concrete blocker within the inspected smooth-branch scope. The manufactured covered-source ordinary-force and actual path-dispatch checks pass their retained code-verification criteria. The partial-cut point-load case remains NONPASS; the covered point-load case was withheld by reference-gap preflight. These outcomes are separate.

The independent reviewer read source and retained evidence and reconciled saved scalar/tree data. No test, solver, numerical case or evidence replay was executed by the reviewer. This file is the reviewer's only write. It confers no D2 scientific acceptance, installed qualification, application admission, release or wider programme completion. Accepted D1 evidence was not re-audited.

## Admission and equations

The additive profile `S3_PATCH_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0` requires exact native S3/S3 shell ownership with at least three faces, `jet2_s3_dev`, whole-face gap certification, exact nodal support and the nested structural route. Augmentation, shared-edge tie, macro pressure basis and D1 admission are excluded. The ordinary new-law kinematics/control restrictions and GENERAL tangent route remain applicable. The new profile is included in reachable tangent-column restriction; full residual rows and prescribed reactions remain present.

The literal work law is unchanged: with normalized gap `g = W/S`, permanent zero algorithmic multipliers give `p = kappa max(-g,0)` and `R = -p · (dW - g dS)`. Its tangent differentiates that residual. `0.5 kappa sum(S min(g,0)^2)` is separately labelled regularization storage; it is not asserted to be a moving-support potential. Whole-face S3 gap bounds remain conservative, including for partial cuts. Exact clipping incidences and unresolved branches still reject.

## Operand cancellation correction

The float S3 path evaluates `(polygon_point - interpolated_target) · n`; Jet2 evaluates `(source_origin - interpolated_target) · n`. Their exact values agree because polygon points lie in the source plane, but absolute Cartesian operands cancel through different arithmetic paths. A summation budget scaled only by the already cancelled weighted gap misses this source of roundoff.

Reviewed `s3_patch_augmented.py` SHA256:
`0b2f64f0192e72edf374e2d7d9bd5a112936f42e8861a4d884fdfaf3bae20375`.
The S3-only retry uses `gamma(64) max(L1 Cartesian operands) (1+kappa_source)(1+kappa_projected_target)`, multiplied by each row's positive maximum float/Jet support. Source and projected-target frame conditioning are explicit. Nonfinite/degenerate or insufficiently resolved frames/origins reject; distance allowance cannot exceed `1e-9` times the smallest source edge. The vector is reset per pair and propagated unchanged into the assembled-gap roundoff budget. The existing relative, support, derivative, integration and physical-gap gates remain separate; Q4 arithmetic allowance is unchanged.

This is a bounded development arithmetic allowance for admitted smooth branches, not a universal clipping/sliver error certificate. Nine new controls passed, with 21 earlier controls deselected: positive per-row scaling, actual translated 10 nm full work, shared-assembly propagation, material-error rejection, distant origin, source/target ill-conditioning and degeneracy. Recorded source identities matched. Resource: 4.951333 s, 212.1728 MB, exit 0, within 180 s / 1,073,741,824 bytes. See `d2_s3_projected_penalty_roundoff_summary_v1_20260930.json` (SHA256 `f375fe7fdb03921dacea5b968bfe57aae6efa30dec5b46e655454cd54c7f7570`). The prior 21-check kernel/admission summary remains local development evidence with its earlier failed checks and repairs retained.

## Independent oracle and retained failures

The helper independently clips triangles to the declared target rectangle and integrates affine P1 support and quadratic P1 mass exactly over fan triangles. It enumerates all 64 penalty active sets, checks signs/free equilibrium and retains every positive supported row. Structural `K0` is an explicitly shared owner input. The oracle is fixed XY/vertical normal; it does not independently verify structural kernels, moving projection/tangential work, continuum accuracy or continuous collision.

Partial-cut coupled v1/v2 NONPASS records are retained. V1's missing diagnostic attribute masked the value disagreement; v2 revealed a 6.84e-20 m3 weighted-gap disagreement near cancellation. After the correction, unchanged v3 reached `contact_gap_exceeded`, not that arithmetic error: last accepted load factor 0.015869140625, failed factor 0.016693115234375, 139 Newton iterations and 122 swept trial cutbacks. Resource: 35.0239103 s / 210.464768 MB, exit 1. Its fixed-geometry full-load oracle predicts represented gap -1.386088238 mm, beyond the unchanged 50 micrometre budget. This is not proof of universal nonlinear formulation failure, and the partial-cut coupled row remains open.

Changing target extent only to 1.4 gave covered point-load reference gap -1.047563648 mm. The common-extent reference preflight correctly withheld a coupled solve: 1.7913764 s / 158.236672 MB, exit 1. No production gap rejection or coupled success is claimed for that record. Neither failure is repaired, pooled or regraded by the manufactured fixture; no additional stiffness/mesh/load sweep is inferred.

## Manufactured integration evidence

The distinct covered-source code fixture prescribes reference normal values `[0,-1,-1,0,-1,-1]` micrometres. Independent P1 `M/S` gives all six positive pressures; free-normal forcing is manufactured as `K0 q - G.T p`, without production contact calls. The enumerated oracle then recovers the solution independently of production contact assembly. The frozen comparison force scale is the sum of absolute manufactured free forces, 6.218453999122283 N.

Ordinary `d2_s3_manufactured_force_v1_20260930.json` and actual `d2_s3_manufactured_force_path_v2_20260930.json` both completed two steps at factors 0.5/1.0, with six complete element states. Recorded production identities match current source in both; the ordinary helper identity is historical because later helper-only edits corrected metadata and path keyword routing. Path v2's helper identity also matches. The actual path profile is `S3_PATCH_PROJECTED_FINITE_PENALTY_STATIC_PATH_DEV_V0`, with two zero in-plane controls replacing the equivalent boundary constraints and the same manufactured normal force history.

Both records give displacement/pressure/contact-force relative differences 4.896594557e-12 / 1.580536032e-12 / 1.003948266e-12 against the independent oracle. Independent represented gap is -0.990 micrometres; the conservative production whole-face lower bound is -2.590000040 micrometres, within 50 micrometres. All six supports and pressures are positive, algorithmic multipliers remain zero, and the maximum complete both-body wrench/reaction/map diagnostic is 1.642824436e-12, below 1e-6. All retained assessment predicates pass.

Resources: ordinary 3.3536413 s / 210.00192 MB; path v2 3.2272976 s / 209.657856 MB; both exit 0 within 180 s / 1,000,000,000 bytes. Ordinary raw `inputs.force_n=0.5` is a retained stale label: its complete nodal-force array and actually used comparison scales correctly record 6.218453999122283 N. It must not be described as the half-newton point-load case. Path v2 fixes that label. Path v1 remains a helper setup NONPASS: forbidden `num_steps` plus a path program was rejected before a solve; the later change corrected only keyword routing.

Raw result SHA256 identities:

- Ordinary MMS: `663f1a8602524cf1b79aefbf3a29ac8b341f3c45fe1aabb62277980a00bd29ca`.
- Path MMS v2: `a33542dd448d07b6973cc86b6cde408fb450d99a1154f1873b09e63a56582cb3`.
- Partial-cut v3: `f9d30e67bdb6186308e91ec1ff0a208fbc932edb7c792205e5e34d3e868f0162`.
- Covered point-load withheld: `70d401a7cba06ef24b37cf9987f6516309cb79cc988d538b59abdfb242c9ca95`.

The supported conclusion is locally tested S3 projected finite-penalty kernel/admission and manufactured ordinary/path integration. S3 partial-cut point-load adequacy, moving lifecycle/restart, arbitrary geometry, continuum/spatial accuracy, independently qualified continuous sweep and D2 acceptance remain outside this closure.
