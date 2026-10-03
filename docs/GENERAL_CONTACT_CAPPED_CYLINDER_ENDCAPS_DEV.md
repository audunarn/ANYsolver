# Physical round-beam ends against a finite cylinder

3 October 2026. **Implemented and installed-tested development; no independent
engineering acceptance, normal application admission or release.** This advances
classical static geometry in D3 without completing D3 or the C0–C9 programme.

## Public use and limits

Select `ContactSurface(..., beam_radius=r, beam_end_caps="hemisphere")` and specify
both `line_stiffness` (N/m²) and `endpoint_stiffness` (N/m) in the interaction.
Use one explicit B2/B3 selection against one `RigidCappedCylinder`, with fixed
axis and optional prescribed translation. The existing exterior, concentric
elastic scalar/von-Karman beam restrictions and dimensional gap budget smaller
than the beam radius apply. B3 reference cells are straight with midpoint nodes;
their actual deformed quadratic curves and end derivatives are retained.

The [example](../examples/general_contact_beam_end_capped_cylinder.py) presses an
axially guided B2 through the ordinary nonlinear static route and emits a
checkpoint. Its stiffness and gap values are explicit demonstration inputs.
The no-cap selection remains available with its historical restart contract.

This is a **discrete additive distributed-line plus endpoint-point potential**,
not integration of a continuous hemispherical surface or a section-resolved
pressure field. It does not enable beam friction, native contact, finite-rotation
structural admission, dynamic impact or arbitrary contact interactions.

## Work, topology and ownership

For the declared cylinder distance `d`, beam radius `r` and compressive gap
`g=d-r`, an owned active end contributes

```text
E_end = 0.5 * k_end * g²
R_end = k_end * g * grad(d)
K_end = k_end * (grad(d) outer grad(d) + g * Hessian(d))
```

The obstacle lies on the outward hemisphere only when its closest-point direction
has positive product with the actual outward beam tangent. Equivalently the
cylinder distance gradient has strictly negative product with that tangent.
All endpoint translational work is mapped to authoritative DOFs; the obstacle
receives the opposite force and moment about the reported global-zero origin.
Line and endpoint storage are reported separately, with their sum explicitly
labelled as the algorithmic contact potential. Endpoint records carry stable
node/element/local-end identities and centre-offset gaps; a side-owned end's
record is not labelled as a recovered physical hemisphere gap.

Physical ends are determined from all material-node uses of every classical
B2/B3 element, including unselected neighbours and B3 middle nodes. A selection
boundary or a shared junction never creates an endpoint spring. This correction
also applies to the existing plane owner. Plane cap checkpoints bind a new
topology revision and reject older incompatible contracts; uncapped contracts
are unchanged. The plane owner's other ownership mechanics are not qualified by
the new cylinder checks.

Active ownership changes would remove finite endpoint energy. They are rejected
unless the entire transition can be certified open. Exact rational Bernstein
point/tangent intervals bound the cylinder distance directional derivative
through the whole affine static path; sampled endpoints do not suffice. The
existing complete-curve exterior/gap certificate remains required. Exhausted
subdivision fails or cuts back. This is not a dynamic-stage certificate.

An active atomic endpoint on a cylinder cap/rim or side/rim transition has two
different one-sided Hessians. The candidate rejects these seams, including
unresolved seams at represented arithmetic precision. Independent one-sided
checks establish the distinction. Smooth-side, cap and rim branches retain
their actual derivatives; no generalized tangent is silently substituted.

## Roots, restart and retained failure

Exactly certified full flat-cap curves use the existing verified rational
quadratic root solver for activation partitions. Representable cuts must have an
exact open-side certificate. Other geometry retains its existing bounded
partition/integration route. Mixed-panel adaptive Gauss estimates remain estimates,
not rigorous arbitrary-geometry integration certificates.

Endpoint stiffness, physical topology and the hemisphere ownership revision are
restart-bound. Active and open fresh-model continuation and incompatible-law
rejection are checked. A swept preflight that rejects before equilibrium assembly
now records `residual_norm=None`, `residual_evaluated=False` and its failure reason,
rather than storing the internal infinity sentinel in a JSON checkpoint. Genuine
computed nonfinite results are not masked and cannot become valid checkpoints.

The unaligned prescribed-tool case **remains NONPASS** at its registered
`1e-6` relative work target: reported work `9.9995584348e-6 J`, final storage
`9.9995000250e-6 J`. An independent accepted-force-history integral reproduced
the reported work, identifying trapezoidal activation error. A prospectively
prescribed activation stage, followed by fresh open restart, passes the unchanged
target: work `9.9995000250e-6 J` and storage `9.9995000250e-6 J`. This different
load-path case is not a retrospective repair or general event-handling claim.

## Evidence

[Summary](d1_review_support/contact_capped_endcaps_20261003/summary.json),
[raw evidence](d1_review_support/contact_capped_endcaps_20261003/raw.zip) and
[supporting scrutiny](d1_review_support/contact_capped_endcaps_20261003/review.md)
bind parent `47d4ab19` and the candidate file hashes. The final private installed
package passes 67 checks in 29.849 s with peak process-tree RSS 337104896 bytes,
under 180 s / 953 MiB limits. Tests include independent endpoint energy/work,
complete and isolated directional tangents, one-sided seams, B3/junction ownership,
rigid covariance/wrench, force and displacement reactions, active/open restart,
tool work, the public example, installed no-contact lazy behaviour and existing
plane/sphere/infinite-cylinder/capped-cylinder routes. Effective runtime and
source/installed byte parity are recorded in the summary.

Fixture errors, activation-root exhaustion, unaligned work error, preflight
checkpoint failure and the seam checks that initially reached the line integration
budget are retained. Same-family supporting source scrutiny identified the
atomic feature seam; it is not independent engineering acceptance. Broader
geometry, mesh/enforcement refinement, physical integration certification,
application admission and programme acceptance remain open.
