# Multiple explicit physical beam-end interactions

4 October 2026. **Implemented and installed-tested development; no independent
engineering acceptance, normal application admission or release.** Profile:
`MULTIPLE_EXPLICIT_ROUND_BEAM_FIXED_RIGID_PHYSICAL_ENDS_STATIC_DEV_V1`.

## Public model and boundaries

Use at least two explicit `ContactInteraction` records for classical round B2/B3
selections against fixed planes, spheres, infinite cylinders or
`RigidCappedCylinder` bodies. Each pair must pass its existing single-pair
geometry, structural, material and numerical restrictions. Select hemisphere
ends explicitly and specify separate `endpoint_stiffness` (N/m) and
`line_stiffness` (N/m²). No dimensionless stiffness conversion or hidden default
is introduced. Mixed capped/uncapped children are permitted only under their
respective contracts.

The [example](../examples/general_contact_multiple_beam_ends.py) presses a guided
B3 outward against a left plane and a right sphere. `--right-obstacle cylinder`
and `--right-obstacle capped_cylinder` select the other fixed shapes. The midpoint
is fixed physically; the model introduces no hidden stabilization.

The historical uncapped plane/sphere/infinite-cylinder aggregate keeps its profile,
restart shape, summation order and limiter branch. The new profile is selected
only by explicit caps or finite-cylinder geometry. Moving multi-tools, automatic
pairing, friction, native beams, dynamics and general finite-rotation structural
admission remain outside this development row.

## Composition and ownership

The existing aggregate owner sums each child's residual, complete tangent and
potential on the same authoritative structural coordinates. It adds no extra
endpoint law. Each child retains its line/point work, actual B3 derivative and
all-material-node end topology. A selection boundary does not create an end.
Repeated element/body feature pairs reject, including aliases with different
interaction names. Genuine contact with separately declared bodies remains
separate mechanical work.

Line and endpoint energies and active/candidate endpoint counts are summed and
reported separately. Candidate counts count represented pair/end features, not
unique beam nodes. Pair records identify their rigid body; per-body forces and
moments accumulate in one pass about global zero. Repeated use of one body sums
into one body record. Equal/opposite aggregate wrenches do not substitute for
checking each physical contribution.

For the new profile, unique physical cells receive the shared exact Bernstein
regularity check at initial/candidate poses and throughout the affine static
path. A finite regular-prefix search precedes child trial limiters. Fractions
compose multiplicatively; the actual common endpoint is rechecked against
every child gap/ownership predicate and curve regularity. A failed child cannot
be dropped. Prefix reductions count in the aggregate swept-cutback diagnostic.
This is not a dynamic-path certificate or a new guarantee beyond the remaining
single-pair integration/geometry restrictions.

Restart binds the new composition revision, each complete child contract and
the aggregate candidate cap. Changing one endpoint law rejects continuation.
No physical history is committed by evaluating or limiting a trial; the existing
nonlinear-static transaction owns increment acceptance.

## Evidence and remaining work

[Evidence](d1_review_support/contact_multiple_endcaps_20261004/summary.json):
27 installed checks pass in 9.228 s, peak process-tree RSS 326,455,296 bytes;
212 loaded modules and 494 package files match source. JIT is disabled, pools
use one thread, and execution is bounded by 180 s/953 MiB. Seven runs/46 records
retain preliminary artifacts, raw results and supporting review.

The independent two-ended bar uses actual B3 end shape `N1=1-3s+2s²`, symmetric
motion `[-a,0,a]`, and a fixed midpoint. For `a=g0+delta`, `D=L+2a`, each end's
balance is derived independently:

```text
P = (2*EA/L)*a + k_end*delta
    + k_line*L*(delta²/(2*D) - delta³/(2*D²) + delta⁴/(6*D³))
```

All three right-obstacle cases match the independent root within 2.015e-14
relative displacement error, against the prospective 1e-6 code-comparison target.
This guided small-motion case is not continuum or general nonlinear qualification.
Other checks cover complete work/directional tangent, per-body/shared-body wrench,
duplicate/resource/moving-body rejection, force/displacement control, active fresh
restart, changed-law rejection, failed second-child cleanup, hidden material
collapse, the common trial limiter, public examples and previous no-cap routes.

[Supporting review](d1_review_support/contact_multiple_endcaps_20261004/review.md)
identified the plane endpoint-count spelling and missing regular-prefix counter;
both are corrected and tested. Same-family source scrutiny is not independent
engineering acceptance. Multiple moving tools and broader beam pairings,
mesh/enforcement refinement and full C2/D3 acceptance remain required.
