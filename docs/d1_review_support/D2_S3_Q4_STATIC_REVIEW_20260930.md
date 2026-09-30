# D2 S3-source / Q4-target static integration — independent review

2026-09-30. Bounded source and saved-evidence review; no reviewer numerical run or production edit. **Scoped local development PASS after the swept norm-bound correction.** This records code integration for two S3 source faces and one original Q4 target, isotropic elasticity, small-rotation physical skins, finite projected penalty and the conservative whole-face gap gate. It does not accept D2, qualify continuum/spatial accuracy, admit arbitrary warped/distorted maps or generic rotating CCD, or promote an installed artifact.

## Reviewed source

Worktree `C:/ANYworkspaceWork/ANYsolver-general-contact`. Final SHA256:

| File under `src/anysolver/general_contact/` | SHA256 |
|---|---|
| `s3_q4_swept.py` | `35aa736fddafeef067bc341c84cdd0a91b62d339e98726efc08e225e506a0c76` |
| `core.py` | `207a0fd46e27fc762cd6d992e55293a4ad17058d418d1bd011b9f101b2b0bfe2` |
| `s3_patch_static.py` | `0efd5954c9339c5bd4a0d8b2c960878f5cdab8c50e523fc3841cfa7827c2b77f` |
| `s3_patch_mortar_energy.py` | `ef8d44042beab99d1fe7b97adabbd1bbbefab8f5b96fef7395e6f5aff1cf6f09` |
| `s3_patch_augmented.py` | `1ce8ee2769fcb32dc7cd613fe45c04017e34b1a096c3f64c3237d42ae9a12fe9` |
| `static_path.py` | `70df4e7a4030a00f24afd992bd05c5b8eec4375da7014323be65e73f936cef1b` |

Test `tests/test_general_contact_s3_q4_static_dev.py`: `4ddf0b91bf31b047f582cc5809de1d7609ca74bec44f18e0494930a5a6a67aff`. The previously reviewed [S3/Q4 Jet2 primitive](D2_S3_Q4_JET2_REVIEW_20260930.md) and shared clip helper retain their reviewed hashes (`1a7456f0…` / `5327364a…`).

## Equations, admission and path bounds

The explicit `jet2_s3_q4_dev` route dispatches the original bilinear-target implicit inverse and reference-measure P1 source integration. Pair support and weighted-gap derivatives accumulate on shared source-node rows before normalized gap and pressure are formed. The existing law remains `g=W/S`, `p=kappa[-g]+`, residual `-sum p*(dW-g*dS)` with the complete derivative of that work. Moving support storage is not asserted to be its potential. Multipliers remain zero; no pressure row is dropped or zeroed to repair resolution.

Scalar/Jet2 support and weighted-gap agreement remain separate gates. Integration and four dimensioned derivative controls are required. Unresolved area, inverse, polarity and touching branches fail closed. The existing S3 operand-cancellation fallback is still restricted to a triangular target: S3/Q4 cancellation that reaches this fallback rejects, rather than borrowing its barycentric conditioning proof. This conservative limitation is retained.

Manager validation requires exactly two native S3 source faces/one qualified Q4 target, the explicit mode, whole-face gap, exact support, nested structural enforcement and no augmentation, tie, rigid-body or D1 admission. The new profile and differentiation setting bind restart identity; legacy branches/defaults remain unchanged. Core selection delegates to that manager validation. Actual residual/tangent maps include both bodies and physical skin offsets.

The new swept certificate encloses the original affine skin-node paths using quadratic source-normal Bernstein controls, all four Q4 corner Jacobian controls and outward separation boxes. Every normal-control cross product must retain positive projected polarity. Rounded subdivision endpoints carry their inherited errors into child orientation and gap bounds; unresolved intervals reject/subdivide within the existing cap. The bound covers whole faces and can be conservative outside represented overlap.

Independent review found that the initial negative-gap denominator assumed the computed normalized reference had exact unit norm. Final code divides its dot-product lower bound outward by the reference norm's outward upper bound, as required by Cauchy's inequality. Positive and negative numerator branches use the corresponding certified norm bounds. The correction changes no pressure/work/tangent equation and introduces no gap tolerance relaxation.

## Retained execution evidence and disposition

All processes used180s/1GiB bounds; the reviewer inspected source, assertions, logs, XML and resource records rather than rerunning them.

- [V1](d2_s3_q4_static_v1_20260930.log): two mechanics/corner checks PASS; path converged but its nonexistent `contact_history` accessor caused NONPASS. Whole run remains NONPASS (11.387888s/335.798272MB).
- [V2](d2_s3_q4_static_v2_20260930.log): attempted public-route correction used an unsupported keyword and failed before solve (3.290261s/212.922368MB); retained NONPASS.
- [V3](d2_s3_q4_static_v3_20260930.log): corrected public path and corner checks PASS (9.717277s/336.371712MB).
- [V4](d2_s3_q4_static_v4_20260930.log): corrected swept bound's independent Decimal80 tilted negative-gap oracle and expanded path/restart check PASS, two other checks deselected (14.063921s/336.461824MB). A pytest temporary-directory cleanup PermissionError is preserved after test completion; supervisor exit0 and XML report two PASS.

Uniform30um compression gives independently known pressure300Pa over0.64m2: source/target forces `+192/-192N` and moments `(96,-96,0)` with opposite total wrench. Four shared source pressure rows/Gram rank4 and two both-body directional step sizes meet the unchanged1e-5 tangent criterion. Public press/slide/open/recontact with target normal motion gives192/192/0/128N and passes all whole-face gap gates. The final test emits an authentic open-prefix checkpoint, persists canonical bytes, rebuilds the model, resumes, and obtains exact displacement, complete material-state and history parity with the full path.

No remaining consequential integration blocker was found at these source identities. Claims remain limited to this guided planar-target fixture, local derivative controls, conservative affine-path rejection and its open-prefix lifecycle. Spatial accuracy, broader deformable-target geometry and engineering/application admission remain unmeasured; earlier D2 contrary evidence is unchanged.

## Addendum — structurally deforming target, local fixture

The preceding6079 bytes remain the original review, SHA256 `e081edbee1643f185f3a0ff52a3b950fb4fb2f7b9033a1d74008668f3cc2f75e`. The six reviewed production identities above are unchanged. New test SHA256: `95a508e410e77b4410c3adef3ba5e71c9def83671efd364d931c62e09e3e4c3f`.

The optional fixture removes target normal ties, fixes Q4 nodes5/6 normal displacement and retains free normal coordinates7/8 with guided rotations/in-plane coordinates. Source normal motion remains prescribed. Clearance1um/press1.3um is an explicitly different small-motion fixture. Its two upward0.01N target loads appear both in public force waypoints and independent reference RHS; they are physical loads, without hidden constraints or stiffness changes.

Independent triangle simplex moments integrate shared P1 source support S and P1×original-unit-square-Q1 coupling H. With h=H[:,free]/S, c=clearance+press and W=kappa*diag(S*active), the reference solves `(Kff+h.T*W*h)q=F+h.T*W*c`, tests `gap=c-h*q`, and recovers `p=kappa*max(-gap,0)`. The signs match downward target contact force and upward applied F. Kff is the existing linear structural operator with every other target coordinate constrained; it is an explicit shared input, not an independent structural formulation. All16 pressure sets are enumerated and exactly one is admissible. No production contact geometry, pressure or work routine constructs the reference integrals.

[V1](d2_s3_q4_deforming_target_v1_20260930.log) remains NONPASS: the pure-displacement rigid-source fixture has zero contact-free predictor reactions and is rejected before contact solve (3.931834s/246.939648MB). This public route admission limitation remains open. [V2](d2_s3_q4_deforming_target_v2_20260930.log) has one new PASS/four deselected, exit0,8.519357s/334.442496MB under180s/1GiB. Read assertions and XML establish actual nonzero downward target deformation, q/p relative agreement and source contact force agreement within the declared1e-6 controls.

**Scoped local development PASS for this mixed force/control fixture.** The reference freezes planar geometry and linear structural K; small-motion agreement does not certify the nonlinear geometry approximation at larger deformation, arbitrary warped targets, continuum accuracy or full deformable-target qualification. No new independent support/control-reaction reconciliation is claimed beyond the comparisons actually asserted. Original failures and the earlier guided path/restart evidence retain their own scope.