# D2 deformable S3 target manufactured integration review — 30 September 2026

## Disposition

Scoped local development review: PASS for the named covered S3/S3 manufactured ordinary-force and actual path-dispatch fixtures. No consequential reference, force-map, prescribed-row work or reaction blocker remains in the inspected scope. This is code integration evidence, not D2 scientific acceptance, spatial/continuum qualification, installed qualification, application admission or release.

The reviewer inspected source and retained records and reconciled saved data/hashes. No test, solver, numerical case or evidence replay was executed. This note is the reviewer's only write for this slice. The prior S3 partial-cut point-load NONPASS and covered point-load preflight WITHHELD remain unchanged; the manufactured cases neither repair nor regrade them. Accepted D1 evidence was not re-audited.

## Reference and two-body work

The independent helper `d2_s3_deformable_mms_reference_dev.py` (SHA256 `4d8323b475aa0f274ee19b5141a6dc38034b99d76fac49283b5b3c70d6d8e837`) integrates literal P1 source support `S`, source mass `M` and source/target cross mass `H` over seven common-refinement polygons. Its clipping and affine basis/integration code do not call production contact. The polynomial product rule is exact on each fan triangle. Partition, affine reproduction and constant/affine resultant/moment checks exercise both cross-mass orientation and action/reaction; maximum partition/affine error is 2.22e-16 and wrench error 4.44e-16.

The fixed-geometry normal map is `G = [M, -H]`, normalized gap `g = gap0 + G q / S`, pressure `p = kappa max(-g, 0)` and internal contact residual `-G.T p`. Thus physical source forces are `+M.T p` and target forces `-H.T p`. The manufacturer supplies `Ffree = K0ff qfree - Gfree.T p`. Structural `K0ff` is an explicitly shared owner input, not an independent structural oracle. Enumerating all 64 pressure masks gives one all-active solution, normal displacement recovery error 5.92e-19 m and free residual at roundoff. Recorded tangent condition is approximately 5.422e4; it is not a uniform conditioning claim.

Source reference normals are `[0,-1,-1,0,-1,-1]` micrometres; target normals `[0,0.3,0.3,0]` micrometres. Source nodes 2/3/5/6 and target nodes 8/9 are the six free normal coordinates. Source 1/4 and target 7/10 retain zero prescribed normals; every in-plane coordinate and rotation remains constrained. Target extent is 1.4 m, initial physical clearance 1e-8 m, regularization 1e7 Pa/m and physical-gap budget 50 micrometres. All six supported pressure rows are retained.

Relevant inspected implementation ranges are reference lines 70–126 (integrals) and 129–180 (manufacturer/mask solve), and coupled adapter lines 30–55 (constraints), 129–207 (full work/reaction comparison), 253–275 (joint forcing), 290–325 (scales, actual path and public solve).

## Ordinary and path evidence

Both records complete two accepted steps at load factors 0.5 and 1.0, preserve six complete element states and report all seven retained development predicates true. The path record actually uses `S3_PATCH_PROJECTED_FINITE_PENALTY_STATIC_PATH_DEV_V0`; its two zero node-2 in-plane controls replace equivalent constraints while the same six manufactured normal forces ramp from zero. Ordinary/path input records and independent oracle are identical. Their common comparison force scale is the sum of absolute manufactured free forces, 11.548348882810515 N.

The comparison retains all ten normal contact residual rows, including prescribed source/target rows. Separate source-only, target-only and prescribed-row virtual displacements compare normal work against `-G.T p` using actual pressure; the independent pressure comparison separately checks the constitutive result. Complete both-body wrench diagnostics include actual source/target structural residual, fixed reactions and physical contact force/moment conversion.

| Retained relative quantity | Ordinary | Actual path | Limit |
|---|---:|---:|---:|
| Source normal displacement | 1.914e-9 | 3.355e-9 | 1e-6 |
| Target normal displacement | 1.480e-8 | 2.591e-8 | 1e-6 |
| Pressure | 2.475e-11 | 4.379e-11 | 1e-6 |
| Contact force | 1.615e-12 | 1.392e-12 | 1e-6 |
| Full ten-row normal residual | 9.567e-13 | 9.567e-13 | 1e-6 |
| Prescribed-row/both-body normal work | 5.347e-13 | 5.347e-13 | 1e-6 |
| Maximum full both-body wrench diagnostic | 9.711e-13 | 1.037e-13 | 1e-6 |

Independent represented physical gap is approximately -1.225714 micrometres in both; conservative production whole-face lower bound is approximately -2.890000 micrometres. Both pass the unchanged 50 micrometre budget. Every support and pressure is positive and the algorithmic multipliers remain zero. The regularization storage and nonpotential projected weak-gap work labels remain separate.

Supervisor records show completed/exit 0: independent reference 1.5349458 s / 136.835072 MB under 180 s / 1,073,741,824 bytes; ordinary 3.613858 s / 210.722816 MB and path 2.9845223 s / 210.202624 MB, each under 180 s / 1,000,000,000 bytes. Sibling `.resource.json`, `.log` and ordinary/path `.runner.source.py` records are retained. Commands use the existing coupled helper with `--manufactured --deformable-target --target-extent 1.4`, adding `--force-path` only for the affected path check.

## Identities and limits

Ordinary/path adapter snapshots both match current SHA256 `e943c512db8cc1274a300ce4240e03b9bfc5679686229999da958749852b88a6`. The recorded independent helper and all seven recorded production hashes match current source, with zero mismatches. The previously reviewed S3 arithmetic/kernel source remains `0b2f64f0192e72edf374e2d7d9bd5a112936f42e8861a4d884fdfaf3bae20375`; no kernel modification is inferred from this fixture.

Raw result identities:

- Independent reference `d2_s3_deformable_mms_reference_v1_20260930.json`: `6891e57f91dde2effb123bb80b8a2254e34529cbf0ec4eda10134a9ad53a4409`.
- Ordinary `d2_s3_deformable_mms_force_v1_20260930.json`: `c6bd11fee8c7e8fba1a0f99f5f1695c76c89c85f962f9beb2daaa58b52d10ceb`.
- Actual path `d2_s3_deformable_mms_force_path_v1_20260930.json`: `03bfb53690263bb54d155fccdfc6bd7f58a655d0b64be3a78497f7e6a53624bc`.

The fixed-XY/vertical-normal oracle verifies this small smooth manufactured normal response; it does not independently verify moving tangential geometry, general rotational work, structural kernels or continuum accuracy. Physical Cartesian force/moment mapping is checked separately through the complete wrench diagnostics. These are two-step force-ramp integration cases, not moving-front or restarted-path tests. A checkpoint is emitted, but no restart claim follows. S3 partial-cut point-load adequacy, arbitrary geometry, spatial accuracy, continuous collision and D2 acceptance remain open.
