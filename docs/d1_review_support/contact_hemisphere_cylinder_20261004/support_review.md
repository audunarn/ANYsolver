# Hemisphere/infinite-cylinder supporting source review

2026-10-04. Inspected new `beam_hemisphere_cylinder_work.py`, decision.md and the existing full-radius radial enclosure path and exact-control utilities. Read only; no numerical checks, production edits or engineering acceptance. Independent oracle execution/acceptance belongs to the lead and separately assigned reviewer.

## Actionable geometry/enclosure mismatch

Current kernel builds `P=I-outer(a,a)` after float normalization. A normalized binary64 axis is generally not exactly unit, so P is not an exact orthogonal projector. This matters in three places:

- rim quartic and candidate objective use `w.T P w`, but Jet2 objective uses `|P w|^2 = w.T P^2 w`;
- sphere branch subtracts beam radius R from `|P q|` as if projection preserved all transverse radius directions exactly;
- existing full-radius sweep encloses the legacy literal map, which need not bound Euclidean cylinder distance from below.

Concrete enclosure counterexample in exact arithmetic before matrix-entry rounding: let `s=a.T a != 1`, `q=b+t*a`, `b.T a=0`. True Euclidean axis distance is `|b|`; literal-map squared distance is `|b|^2+(1-s)^2*t^2*s`. With sufficiently large axial t, the literal bound can certify opening while the true cylinder penetrates. Rounding the matrix entries introduces additional error and does not restore a conservative ordering. Renormalizing the floating axis again does not remove this issue.

Smallest safe **new-profile-only** enclosure correction: form bound controls using exact binary-input Fractions and Euclidean projection `q-a*(a·q)/(a·a)`, or exact rational `I-aa.T/(a·a)`. Feed these rational transverse Bernstein controls into the existing lower-gap/speed/certificate machinery. Preserve legacy `self.projector` and distributed line potential arithmetic. A bound-only controls/projector hook in `_swept_full_envelope_admissible` would isolate the change. Existing `_controls` calls `_fraction(d)`, and `_fraction` converts via float, so passing a Fraction matrix to it loses exactness; use an exact-control helper or narrowly preserve Fraction entries in the new hook. Kernel geometry/Jet/station objectives must use the same prescribed axis-line semantics and avoid axial contamination; mixing the corrected enclosure with the current literal kernel is insufficient.

## Rim/station differentiation

The half-angle coefficients are correct for an exact orthogonal P. Expanding `-A*sin(theta)+B*cos(theta)+R*((C-D)*sin(theta)*cos(theta)+E*(cos(theta)^2-sin(theta)^2))` gives the implemented quartic. Including theta=pi covers the missing chart point. Sphere eligibility `radial·d<=0` correctly includes the radial minimum on the actual hemisphere and chooses sphere Hessian at the seam, subject to resolved geometry/sign arithmetic. Actual B2/B3 tangent coefficients and node-major beam+axis-point Jet seeds are correct.

For a resolved unique rim minimum, `Hxx-Hxt*Htx/Htt` is the correct envelope Hessian; the positivity/stationarity check is essential. Active tie rejection is appropriate, and an open tie may expose zero penalty work without claiming a unique normal/skin point.

The current Sturm count checks distinct real roots of the **rounded coefficient polynomial**, before Newton polishing and angular deduplication. It does not establish that final stations are distinct representatives of every root or that all physical stationary roots remain covered. Newton updates may move representatives, angle deduplication uses a fixed 1e-10 threshold, and only the selected station receives a derivative/curvature check. Necessary completeness discriminator: isolate/check every real root (including pi eligibility), preserve correspondence through refinement, and verify final stationary representatives/root separation before accepting a global active minimum. Count agreement alone is not global-minimum certification. A finite unresolved case must reject rather than silently lose a competing minimum.

## Remaining precision/admission checks

`q@q` controls station/tie tolerance even though arbitrarily large axial offsets should not affect cylinder gap; after correcting projection, scale those tolerances with transverse geometry. Direct `np.sum(coeff*x)` can lose translated B3 tangent cancellation; compute the tangent from centered/exact endpoint differences or reject unresolved inputs consistently. Sphere activation uses direct `rho-R-Ro` and float branch dot without an exact/stable sign guard; near-zero literal activation and nonzero-but-unrepresentable differences need a declared rejection/stable evaluation policy consistent with the existing plane/sphere support contracts. These issues require source correction or bounded admission, followed by independent axial-translation/rotation, near-seam, close-root/nonunique and smooth full-map derivative checks. No such outcomes are claimed here.
