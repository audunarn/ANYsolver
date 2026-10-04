# Fixed-sphere cap supporting source review

2026-10-04. Repository `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`, parent stated as `b956dda3`. Inspected only `beam_hemisphere_sphere_work.py`, `beam_hemisphere_sphere.py`, the extracted full-envelope method/legacy forwarding in `beam_radial_ends.py`, and conditional support dispatch in `core.py`. No numerical runs, production edits, nested delegation or engineering acceptance claim.

## Defect found and corrected during review

The first inspected geometry source called `Jet2.variable(0., size, 3*i+j)` at line 73, reversing the existing `(value, index, size)` signature. Every nonparallel call would fail at the first seed with an index outside a zero-length gradient. Reported immediately to the lead. A subsequent source read shows the corrected `Jet2.variable(0., 3*i+j, size)`. This finding is resolved in source; the reviewer did not execute the corrected map.

## Remaining admission/integration checks

1. `beam_hemisphere_sphere.py:14-29` requires one fixed sphere pair and an exterior gap budget but has no explicit `beam_end_caps=='hemisphere'` or endpoint stiffness requirement. It delegates to the general validator with `owned_point`. Verify that caps='none', missing endpoint stiffness, non-beam sources and incompatible selectors are rejected before construction; otherwise general line-only admission can be broader than this manager's endpoint protocol. This is a source-visible missing explicit guard, not a proven admitted counterexample within the allowed inspection.
2. `core.py:597-604` and `1250-1256` route multiple support interactions to the aggregate manager before the sphere route. The prior aggregate review found a legacy nonplane endpoint contributor. Verify that current aggregation either rejects the newly admitted sphere child or constructs this new manager. Current aggregate source was outside this assignment, so no current aggregate defect is claimed. Preserve the planes-only aggregate identity unless deliberately expanded.
3. The manager invokes the existing radial-end constructor (`sphere.py:48`). Verify initialization establishes all endpoint/kernel members before any dynamically dispatched evaluation and imposes no legacy ownership seam rejection on this continuous support profile. The constructor internals were outside the permitted extracted-method scope.

## Geometry reasoning supported by source

For endpoint displacement q=c-O and outward unit tangent d, the unconstrained closest sphere point is c-R*q/|q|. It belongs to the outward hemisphere exactly when q.d<=0. For q.d>0 the closest point on the hemisphere lies on its equator: with rho=|q-(q.d)d|, its centre distance is `sqrt((q.d)^2+(rho-R)^2)`. The source branch, tangent coefficients, cross-product rim direction and skin/rigid-point construction implement these identities (`work.py:54-63`, `77-101`, `108-114`). At q.d=0 the two gap/gradient limits coincide and the sphere Hessian is selected; Hessians have distinct one-sided limits.

The exact exterior restriction Q>max(R,Ro)^2 (`60-61`) matters to the rim conjugate: A=Q+R^2-Ro^2 is strictly positive. Then `A^2-4R^2*P` has the same sign as `A-2R*sqrt(P)`, and the denominator used at `95-98` is positive. Sphere activation uses Q-(R+Ro)^2 (`80`); rim activation uses the exact two-conjugate numerator. The nonzero exact numerator converting to floating zero is rejected (`102-105`). Floating root bounds affect magnitude, not the literal activation numerator.

Corrected centered/scaled Jet2 seeds include every beam translation and the obstacle centre (`71-76`); q includes endpoint-minus-centre work while v includes the actual B2/B3 derivative and B3 midnode arm. Cross-norm and tangent-normalization derivatives are retained (`83-92`). These maps still require independent numerical differentiation and covariance checks; source identities alone do not establish their numerical adequacy.

At a parallel rim, all minimizers have distance sqrt(Q+R^2), and the exterior restriction makes it strictly open. Source returns no unique points/normal and zero gradient/Hessian (`65-70`). Those zeros are zero-penalty-work placeholders, not smooth derivatives of the positive gap. Preserve that limitation for any future consumer.

## Assembly, wrench and sweep

`sphere.py:74-76` calls only distributed radial line work. Cap work uses the beam portion of the full gradient/Hessian, adds the point penalty consistently, scatters all beam nodal translations through `np.add.at`, and retains full cross-node sparse blocks (`79-94`). Beam wrench sums every cap nodal force at its actual position, including the B3 midnode (`85-86`), then adds line wrench. Setting the rigid wrench to its opposite (`95-96`) depends on the differentiated envelope's translation/rotation identities. Check independently that obstacle-centre gradient equals the rigid resultant and that rigid moment equals O cross rigid_force (no intrinsic spherical couple); opposite reported totals alone are not evidence of that identity.

The full-envelope implication is sound: the physical hemisphere is contained in its endpoint radius-R ball, so its obstacle gap cannot be smaller than the sphere/ball envelope gap. Thus actual whole-curve radius-envelope and tangent-regularity certification contains both branches, even during a seam crossing. `beam_radial_ends.py:174-195` retains curve regularity, exact affine Bernstein path controls, relative-speed bounds and a bounded temporal certificate; `sphere.py:103-107` uses it directly. Its radius must retain the existing combined obstacle-plus-beam radius convention, and owner bounds/regularity need their own evidence. The original radial-end route still applies the extracted full-envelope gate followed by legacy ownership-path admission (`197-205`), preserving that route's additional restriction in source.

Result/restart fields identify actual tangent hemisphere geometry, separate point springs, selector and full-envelope revision (`sphere.py:33-40`, `109-115`). Default `owned_point` dispatch is unaffected by the new conditional path. No moving obstacle, cylinder/capped-cylinder support, friction/material spin history or acceptance expansion follows from this slice.

## Necessary focused checks for lead execution

- Corrected nonparallel B2/B3 geometry calls; actual curved-B3 midnode force and all beam/centre Hessian blocks.
- Sphere/rim values against the constrained scalar geometry; exact binary activation and cancellation-sensitive gaps; seam one-sided Hessians and strictly open parallel disposition.
- Common translation/rotation covariance, obstacle-centre reaction, both-body wrench and spherical zero intrinsic couple.
- Independent cap sparse penalty reconstruction plus line work; caps='none'/missing stiffness/incompatible selector/multiple sphere dispositions.
- Full-radius sweep rejection of hidden penetration and tangent collapse; legacy owned-point and ownership-path behavior unchanged; restart identity and supported fixed-sphere force/displacement routes.

No checks in this list were executed by this reviewer.

## Delta disposition: resolved spatial envelope bounds

Follow-up source-only inspection, 2026-10-04. No numerical execution or production edits.

- The sphere validator now explicitly requires beam radius, declared hemispheres and endpoint stiffness (`beam_hemisphere_sphere.py:20-21`). This resolves the missing explicit admission guards noted above.
- The aggregate `_parts` path now rejects every nonplane body when the support selector is active (`multiple_beam_rigid.py:42-43`). Its fixed-plane support composition therefore cannot fall through to legacy radial endpoint work for the expanded single-sphere validator. Current `core.py:597-604` / `1250-1256` still sends multiple interactions through aggregate validation/construction and single spheres through their matching sphere path. The earlier composition concern is resolved in source.
- The sphere sweep requests `resolve_gap_bounds=True` (`sphere.py:110-116`). The extracted full-envelope helper uses `admit_above=None` only for that request (`beam_radial_ends.py:175-187`), resolving the existing 0.1*gap spatial accuracy before subtracting temporal speed. This can recover temporal margin that a safe but loose early-stop lower bound obscured. It does not enlarge the gap budget, omit regularity, replace a lower bound with samples or change the bounded spatial/temporal work budgets. Failure to obtain the bound remains non-success.
- The legacy method retains the default `resolve_gap_bounds=False` and invokes the helper without overriding it (`ends.py:199-206`). It therefore retains its early stop at -gap_tolerance and its subsequent ownership-path gate. The opt-in spatial resolution change does not widen legacy admission in the inspected source.
- The sphere constructor now stores the exact Fraction sum of the two literal binary radii before calling its base constructor (`sphere.py:51-55`), and the envelope helper passes that value to `curve_gap_lower` without converting it to float (`ends.py:185`). This is a bounds-only route: the line potential's radius arithmetic is unchanged. Restart metadata identifies resolved bounds and exact binary-radii addition (`sphere.py:118-124`). **Owner precision dependency:** `curve_gap_lower` and its radius conversion must preserve a supplied Fraction; routing it through `float` would discard the intended literal-sum protection. That referenced owner's implementation was outside this bounded scope and was called out to the lead for direct confirmation.

The lead reports source01/source02 seam-sweep rejection diagnosed as insufficient margin from the early-stop lower bound, followed by 14 passing source03 checks including covariance/wrench/Hessian work, independent bar work, admission/aggregate rejection and an actual active seam sweep. These are lead-reported outcomes, not checks run or raw evidence independently assessed by this reviewer. Preserve the failed source01/source02 evidence. This source delta introduces no additional blocker beyond confirmation of the Fraction-preserving bound-owner dependency and the previously stated evidence boundaries; it is not formal acceptance.


## Lead disposition — owner radius precision

The referenced _fraction cast did round Fraction back to float. Source06_radius retained a verified counterexample: constant curve at literal .11, exact sum of literal .01 and .1; the old bound returned zero rather than the negative exact gap. Source05_radius was an initial degree-zero fixture mistake, retained separately. curve_gap_lower now preserves Fraction radius inputs while keeping old float-input arithmetic. Installed final covers this exact guarantee, full active seam, new/legacy mechanical/state/selector routes and lazy no-contact. Reviewer did not run these checks; supporting review is not acceptance. Initial reversed Jet2 seed corrected before the first numerical run. Explicit cap/spring admission and multiple-sphere composition guards verified. Source01/02 conservative seam failures and source06 precision failure remain evidence, not retrospective passes.
