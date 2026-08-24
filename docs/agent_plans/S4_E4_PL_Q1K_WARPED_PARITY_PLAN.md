# E4-PL Q1K: Warped-Facet Parity Closure

## Purpose

Close the only remaining functional parity gap in the dormant Q1J element
without changing its qualified planar mechanics.  A warped bilinear facet
cannot be reduced to one projected plane without losing physical rigid-body
motion, so Q1K uses the established integration-point varying-frame Q4 kernel
for genuinely warped facets and the Q1J 35+3 E4-PL kernel for planar facets.

## Frozen split

- `warpage_ratio <= planar_tolerance`: qualified E4-PL stationary kernel.
- `warpage_ratio > planar_tolerance`: direct varying-frame Q4 surface kernel.
- `warped_formulation="reject"`: explicit fail-closed mode.
- The old `legacy_warped_fallback` keyword is input compatibility only and is
  normalized immediately to one of the two explicit strategies.
- Every emitted component record reports `legacy_fallback=false` and names the
  selected direct formulation.

## Qualification obligations

For three non-coplanar distorted facets and all eight D4 numberings:

1. stiffness symmetry;
2. six analytical rigid modes and an 18-dimensional positive quotient;
3. operator congruence under numbering changes;
4. covariance under proper global rotation and translation;
5. byte-identical linear and nonlinear response to the established
   varying-frame Q4 kernel;
6. orthotropic and generalized-section stiffness parity;
7. generalized-section mass parity.

Q1K does not activate the default.  After these obligations and the complete
Q1J regression matrix pass, default replacement proceeds as a separate,
reversible release stage.
