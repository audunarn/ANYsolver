# D2 S3 normal-control lifecycle independent review — 30 September 2026

## Disposition

Scoped local development PASS for the covered S3/S3 two-body normal-control press/open/recontact path and authentic active/open restart. Source/evidence scrutiny found no remaining consequential sign, reaction ownership, fixed-scale or state-continuation blocker in this named fixture. This is local code/lifecycle verification, not D2 scientific acceptance, continuum/spatial qualification, continuous collision qualification, installed qualification, application admission or release.

The reviewer inspected source and saved records and reconciled their scalar/tree contents and hashes. No solver, test, numerical case or evidence replay was executed. This note is the reviewer's only write for this slice. Prior S3 partial-cut point-load NONPASS and covered point-load preflight WITHHELD remain unchanged; accepted D1 evidence was not re-audited.

## Controls, work and reaction ownership

The independent P1 reference remains the previously reviewed `d2_s3_deformable_mms_reference_dev.py`, SHA256 `4d8323b475aa0f274ee19b5141a6dc38034b99d76fac49283b5b3c70d6d8e837`. Its exact common-refinement support/mass/cross-mass map is `G=[M,-H]`, `g=1e-8+Gq/S`, `p=1e7 max(-g,0)` and full internal normal contact residual `-G.T p`. Structural `K0ff` is an explicitly shared owner input, not an independently verified structural kernel.

Lifecycle v1 is retained as setup NONPASS: six distinct controls exceeded the existing public path limit of three and were rejected before any solve. No API limit or production admission was broadened. V2 instead uses two unit normal controls, source master node 2 and target master node 8. Explicit normal MPC equations tie source 3/5/6 to 2 and target 9 to 8. Source fixed normals 1/4 and target fixed normals 7/10 remain disjoint; all in-plane coordinates and rotations are guided. The path is zero → source -1 micrometre / target +0.3 micrometre → zero → the same press, with two steps per segment. Applied nodal loads are zero.

The generalized reaction sign follows the driver's `external + C.T lambda - internal` residual. For each pose the independent six-row action is `K0ff q - Gfree.T p`; reported source reaction is the sum over source 2/3/5/6 and reported target reaction the sum over target 8/9. Comparing master-only rows would omit slave virtual work; the implemented group sums preserve it.

Both controls exhaust the remaining reduced coordinates, so the joint free map is empty. Diagnostic control actions are inserted once at masters 2/8; they are not applied nodal loads. Full residual constraint action retains the MPC redistribution, including its moment. Named support reconciliation uses `structural + contact - C.T lambda` and only each boundary condition's actual constrained components. The normal MPC rows do not overlap those components. Full ten-row normal contact work, including prescribed rows, and physical force/moment conversion remain separately checked. Relevant current adapter ranges: 129–210 (mechanics and fixed scales), 213–242 (fixture/MPC/control construction), 245–287 (group reactions and named supports).

Opening comparisons use fixed full-press scales: source displacement norm 2e-6 m, target norm 4.242640687119285e-7 m, pressure norm 22.227708281508598 Pa, and force scale 11.548348882810517 N. Force/moment and normal virtual-work normalization are recorded explicitly. These scales do not collapse at the zero-pressure open pose.

## Full-path evidence

`d2_s3_normal_control_lifecycle_v2_20260930.json` completes six actual poses, with pressure activity `[6,6,6,0,6,6]`, actual profile `S3_PATCH_PROJECTED_FINITE_PENALTY_STATIC_PATH_DEV_V0` and six complete element states. All nine per-pose predicates and four aggregate predicates pass. Maximum source/target displacement comparison is 2.709e-13; pressure 1.458e-12; grouped control reaction 1.867e-12; full normal contact residual 9.568e-13; prescribed-row/both-body normal work 5.347e-13. Named support differences are exactly zero; maximum full both-body wrench diagnostic is 9.614e-17. All are below the unchanged 1e-6 comparison limit.

Minimum independent represented gap is -1.225714 micrometres; conservative production whole-face lower bound is approximately -2.890000 micrometres, within the unchanged 50 micrometre budget. All six supports remain positive, pressure is nonnegative, algorithmic multipliers remain zero and regularization storage retains its separate nonpotential work convention. No moving-support potential is inferred.

Supervisor completed/exit 0: 4.0584197 s / 211.41504 MB under 180 s / 1,000,000,000 bytes. The v2 adapter subsequently changed only for restart integration; its retained runner snapshot matches its recorded SHA256 `86c9402de60653999bbc3d2af410d402e502cd5869e9f8708f73d0fa211a2481`. Its reference and production identities match the restart record/current source.

## Authentic restart and identity

`d2_s3_normal_control_restart_v1_20260930.json` stops public execution at fractions 1/3 and 2/3, yielding actual accepted-step 2 active and accepted-step 4 open roots, then resumes to 1.0. Each segment rebuilds the fixture; the next public solve receives the previously emitted checkpoint after canonical-byte write/read. No constructed states, fingerprint override or integrity override is present. Current adapter lines 307–375 inspect the reference, perform the three public segments, persist/load roots and compare continuation.

Independent order-insensitive full-tree reconciliation found zero differences between each persisted root and its emitted checkpoint payload, and zero differences between the complete final checkpoint and the saved full path. Each root retains all six element states and matching model/analysis fingerprints. The six actual pose indices are exactly 1–6; continuation displacement, pressure and control-reaction differences are exactly zero at every pose. All eight aggregate restart predicates and per-pose mechanics checks pass. Changing regularization to 2e7 Pa/m with the untouched open root raises `NonlinearCheckpointError: checkpoint analysis contract is incompatible`.

Supervisor completed/exit 0: 4.5694162 s / 212.004864 MB under 180 s / 1,000,000,000 bytes. The recorded adapter/reference/reference-record/six production hashes and both persisted-root hashes match their files, with zero mismatches. Current adapter and retained restart snapshot match SHA256 `4b66ba3f99ebb8bbe9cd3d3d619df47d77d9dba4bca34a2f8435780c8bc0ed81`. Production kernel remains the previously reviewed `0b2f64f0192e72edf374e2d7d9bd5a112936f42e8861a4d884fdfaf3bae20375`.

Raw identities (sibling logs, resource records and runner snapshots retained):

- Full lifecycle v2: `940b699d8fe51936283f71e013e0d8b1b51ece99bb1a3d40ab5b4a66503be8f1`.
- Restart v1: `d297aa1970fa9763d6e00159d94060e8691b6a74c099fc5704fde40ed25d22b4`.
- Active root1: `dc6f1cd1d45acc541e0c17e5f65d4dda03ae3db714f839eff698a6ed057fe556`.
- Open root2: `46b80f80952ba2bf7b33d9054395ebb15d494ce3f753810544a708bb87096f66`.

The supported conclusion is this covered, small normal-motion, two-body controlled pressure lifecycle and active/open restart integration. The fixed-XY/vertical-normal oracle does not establish general tangential projection, rotational work, structural accuracy or continuum accuracy. MPC-guided normal motion is not moving-front or uncovered-tip collision evidence. Arbitrary geometry, S3 partial-cut point-load adequacy, spatial accuracy and D2 acceptance remain open.
