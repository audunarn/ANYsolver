# Quadratic physical-end source review — 2026-10-04

Scope: read-only scrutiny of the dirty candidate in `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`, HEAD `8081d582e60fe519e0de23fdf6b352c2a3b6ee5d`. No repository edits, solver executions, commits or additional workers. This is supporting source scrutiny by an OpenAI worker, not a different-model independent engineering acceptance or product qualification.

## Finding requiring a discriminating check

**P2 — preserve exact activation truth when numerical distance subtraction rounds to zero.** In `beam_curve_ends.py:90`, a non-open exact certificate is followed by `station.gap >= 0`, which can silently skip a strictly penetrating cap pair. `b3_distance_jet` obtains that gap by `distance - radius`. The B2 endpoint path instead retains exact squared-distance sign and uses rationalized subtraction.

Concrete stationary geometry in Q2 nodal order:

```
A = [(-1,-1,0), (-0.5,-0.5,0), (0,0,0)]
B = [(0.15,0.15,0), (0.65,0.65,0), (1.15,1.15,0)]
R = 0.21213203435596426
```

A endpoint 2 and B endpoint 0 are reciprocal strict clamps with negative source ownership; their affine paths are regular and squared-distance curvature is positive. For the exact rationals represented by these IEEE floats, `2*(0.15)^2 - R^2 < 0`; ordinary floating `sqrt(0.15^2+0.15^2)-R` equals zero. Exact scalar arithmetic in the review established those two signs (no solver execution). The lead should confirm actual NumPy/manager behavior in the authorized bounded check. Expected consequence if confirmed: zero endpoint energy/force and omitted active `ke * outer(gradient, gradient)` tangent despite an exact strict penetration. The missing force is roundoff scale, but the missing tangent contribution is finite. The fix should retain an exact activation sign or explicitly fail unresolved numerical activation; an arbitrary tolerance would change the law.

## Source conclusions

- **Point work and reduced Hessian:** the point potential has full weight `0.5*ke*g^2`; its residual and Hessian correctly use `ke*g*grad(g)` and `ke*(grad(g) grad(g)^T + g Hess(g))`. The reused interior jet includes both the derivative of Q2 shape weights and target curvature through the Schur correction. A fixed endpoint clamp correctly omits that correction.
- **B2/B3 maps and wrenches:** the parent's block assembly map preserves all B3 translational curvature modes, and embeds B2 midpoint motion with half weights without adding DOFs. Mapping residual/Hessian with its transpose is consistent. Reporting forces and moments in virtual Q2 coordinates preserves the resultant and moment after B2 redistribution because the virtual midpoint position is the same affine average.
- **Reference versus actual geometry:** admitted classical B3 references remain straight with a true midpoint through the existing element/parent validation. Deformed contact geometry is the full actual Q2 curve from all three nodal translations. Line work retains straight reference measure; point work has no length measure. This source does not admit curved-reference structural B3 elements.
- **Exact endpoint certificates:** Q2-to-Bernstein conversion, distance-squared differentiation, strict convexity, endpoint stationarity signs, and dyadic interior root brackets appear mathematically sound. Root brackets use entire temporal sign hulls. Spatial restriction retains rational geometry; its scalar float conversion is exact for the dyadic bounds used here. Polarization of equal-degree tensors proves the ownership sign over time and root bracket. Equality cannot establish a closed branch or ownership sign.
- **Opening:** component hull and distance-squared Bernstein lower bounds prove opening over the entire target curve and interval, including grazing equality. They may reject genuinely open nonconvex or poorly enclosed geometry; this is conservatism, not a demonstrated mechanics error.
- **Reciprocity/topology:** genuine ends are obtained from all material beam incidence, including unselected cells and midpoint incidences. Active endpoint clamps require a genuine target endpoint and a reverse strict cap-owned clamp to the original source. The symmetric endpoint key counts reciprocal work once. Swept endpoint proofs for both directions use the same temporal interval before checking reciprocity; subdivision is common. Separate regularity and parent gap certificates can safely be conjoined.
- **Dispatch:** the B3-containing single-cell hemisphere route reaches the new validator and manager. Multi-cell routes retain their existing owner. Existing elastic, isotropic, concentric von Karman admission is reused after stripping only endpoint law declarations for line validation.

## Checks still needed before accepting the candidate

The lead's authorized bounded checks should cover the exact activation example above; curved active end/interior force and reduced-Hessian directional differences; rigid translation/rotation work and total force/moment balance; mixed B2/B3 mapping and surface-order reversal; reciprocal end/end full weight versus two half-direction line weights; genuine end suppression at an unselected element junction (including a B3 midpoint); strict closed projection and ownership ties; and a path whose end states are regular but intermediate Q2 speed vanishes. Do not treat nonconvex projection or finite subdivision rejection as an established formulation failure.

The inherited distributed B3 law and gap/swept oracle were reused as context, not independently qualified here. Exact endpoint certificates do not upgrade the parent's floating distributed gap oracle into an exact whole-pair certificate. No new acceptance tolerances or domain expansion are implied by this report.

## Reviewed source identities (SHA256)

```
beam_curve_end_geometry.py 3FF2D14C1CCDD2747822E572579E82F2B790916291F485D23C2CCFA56FE417D8
beam_curve_ends.py         A8B19B49EED44A264FFC7CDC83463FEC45E9AAB6B1AFEFA9E051123D313C1DB3
beam_pair_ends.py          EC9CECE34B9B2AFF0D588CC3D64BFD8E450B1F4E8ED59344ABF58474DF7452D3
core.py                   05276862AD74EC132253D593565E3EADD243CE8B818B9269BEBD5FCF06B7F076
```

## Delta review — activation correction

Read-only review of `beam_curve_ends.py` SHA256 `ECB6570037DAE783BCA96151855C293DCADB11B2002DB7FC4B6333EB186C3B17` confirms the clamp now obtains exact rational separation and squared distance, and computes the gap from `(squared-R^2)/(upper_sqrt(squared)+R)`. This removes subtraction cancellation in the original oblique example and preserves its active endpoint tangent at ordinary IEEE scales. Gradient/Hessian mapping, point weight and reciprocity are unchanged. Interior activation close to floating roundoff now raises explicit non-success unless opening was already exactly certified; that is a conservative scope restriction, not a redefined spring law.

One residual exact-sign corner remains in source: conversion of a nonzero rational gap to float can underflow to signed zero, after which `gap >= 0` still skips the active tangent. The B2 helper already handles this with `nextafter(0, sign)` when exact sign is nonzero. Reusing that guard, or failing explicitly on conversion underflow, would complete sign preservation unless the admitted coordinate/radius domain explicitly excludes this extreme scale. This is not the original ordinary-scale rounded-subtraction defect; no new numerical run was made to measure it.

The lead reports source02 confirms the exact oblique example and source03 passes four checks in 3.795 s with peak 184045568 B, covering curved/mixed full-work tangents and an independently formed P2 bar comparison at 8.409e-16 relative error plus restart. These are lead-supplied results, not tests executed or independently inspected by this reviewer. The prior 1e-7 m whole-curve gap-enclosure depth-25 failures and failed support-bound experiment remain failed evidence. `git diff` of `beam_curve_pair.py` is empty at this delta review despite its status marker, consistent with restored legacy content. The current 1e-5 m developmental gap-enclosure fixture is an explicit successor setting, not a retrospective regrade or an acceptance tolerance change.

Source conclusions remain supporting scrutiny only. This delta does not establish physical validation, different-model independent acceptance, qualification or release.

## Final delta review — exact whole-curve gap and swept bound

Reviewed identities: `beam_curve_end_geometry.py` SHA256 `059020E22A4E0877AFB277563696E10380642CE058E2D86AF8EC9D3B86D66017`; `beam_curve_ends.py` SHA256 `8166A77BC3774D32C91DC1518B2CE1268E045B1C84EFBA85B60EEB968D3FE356`. This assessment used source reads only, with no tests, imports or repository edits.

No additional correctness blocker was identified in the new whole-curve enclosure. Exact Q2 relative controls have degree (2,2), and their exact squared-distance controls degree (4,4). Each patch lower bound combines the coordinate hull, squared-distance Bernstein minimum and zero. Corners and centre supply valid upper bounds only. Pruning when a child lower bound cannot improve the current exact sampled upper bound is sound: subsequent reductions of that upper bound cannot invalidate earlier pruning. The best-first heap preserves the lowest surviving lower bound, and replacing an empty heap by the sampled upper bound is valid once all patches were rigorously pruned. Fixed cell/depth exhaustion remains explicit failure.

Exact square-root inequalities give conservative rational distance bounds. Conversion of the radius-subtracted bounds is outward, and success requires the actual outward reported gap width to satisfy the specified dimensional accuracy. Precision exhaustion is explicit failure. Thus the new caps-specific minimum-gap field is an enclosure over the complete two-Q2-curve domain; it is not inferred from the finite sampled minimum.

The caps manager alone now overrides the full-curve certificate and swept gap check. The exact affine Q2 velocity curves are bounded by their Bernstein controls. The maximum upper-bounded norm over every pair of control velocities is a valid upper bound for relative velocity at arbitrary material coordinates. Global minimum separation is Lipschitz under that speed bound, so each temporal interval's endpoint lower gaps minus `speed * interval_width / 2` conservatively bound every interior time. Exact rational midpoint geometry and outward scalar lower gaps preserve that argument. Regularity and common-interval endpoint reciprocity remain additional gates. `git diff --numstat` for legacy `beam_curve_pair.py` is empty in this review.

The clamp work now rejects nonzero exact squared-gap differences whose scalar conversion becomes zero, resolving the residual conversion-underflow concern from the preceding delta. Interior roundoff activation remains explicit non-success. Existing globally convex endpoint projection admission and rejection of unresolved closed ties/nonconvex projections remain scope restrictions.

The lead reports retained source05 rotated-covariance depth-25 failure at 1e-5 m gap accuracy and successor source06 five passes in 5.013 s at peak 181764096 B, including curved/mixed full tangent checks, P2 bar, covariance, and a 1e-7 m independent gap comparison under the same caps. These are lead-supplied bounded results, not tests executed or independently inspected by this reviewer. Preserve source05 and the earlier failures as failed evidence. The new exact oracle is a deliberate caps-specific implementation change, not a regrade of those failures. Full engineering acceptance programme remains incomplete; this source assessment does not qualify or release an installed candidate.
