# Multiple fixed-plane hemisphere support — development profile

`MULTIPLE_EXPLICIT_B2_B3_HEMISPHERE_SUPPORT_PLANES_STATIC_DEV_V1` composes the
[single-plane hemisphere support](GENERAL_CONTACT_HEMISPHERE_PLANE_DEV.md) on
shared authoritative coordinates. Implemented and installed-tested; no independent
engineering acceptance, normal application admission or release.

Run `examples/general_contact_multiple_hemisphere_planes.py`. Select
`beam_end_cap_work="hemisphere_support_dev"` with explicit hemisphere radii,
separate line/endpoint stiffnesses and dimensional gap budgets. All targets in
this selected profile must be fixed planes. The legacy owned-point mixed
plane/sphere/cylinder/capped-cylinder route remains unchanged.

Every child evaluates the same candidate pose. The global residual and sparse
tangent are sums of the actual line/cap potentials; B3 midnode terms and local
cross-node blocks remain. The minimum child step is rechecked against every
child at the actual common endpoint. Whole-curve regularity is checked on unique
physical cells; contact pairs are not deduplicated by cell identity. Duplicate
element/body pairs and exceeded aggregate candidate caps fail explicitly.

Results include integrated line/endpoint storage, each pair's cap fields and
per-body forces/moments about the global origin. Endpoint counts mean
**endpoint/target pairs**, not unique physical beam ends. Contributions to one
rigid body from multiple beam selections are grouped by its declared identity.
Restart binds the new composition and complete child geometry/law/settings/
physical-end contracts. No contact multiplier or physical material state is
committed during evaluation; the ordinary static driver owns the transaction.

## Checks actually run

The private installed suite passed **50 checks in 11.681 s**, with **355,713,024 B**
peak process-tree memory. JIT was disabled and effective thread pools used one
thread. 239 loaded modules and 502 package files matched candidate bytes.

Checks cover independently integrated orthogonal-plane energy, full virtual work
and 10⁻⁵ directional tangents, B3 cap/midnode work, both-body wrenches, shared-body
grouping, closed seam sweeps, genuine junction ends, common-step gap rejection,
duplicate/resource and incompatible-setting/geometry rejection. An independently
derived two-ended B3 bar differs by **1.733×10⁻¹⁴** against its 10⁻⁶ target with
gap budget 10⁻⁵ m (10⁻³ of radius). Force/displacement control, active JSON split
restart, law/settings incompatibility, injected second-child exception and
cancellation replay pass. Installed examples, single-plane and historical
mixed-obstacle routes and lazy no-contact behavior pass.

[Evidence](d1_review_support/contact_multiple_hemisphere_planes_20261004/summary.json)
contains four measured runs and 33 raw records. Supporting same-family source
scrutiny checked composition and identified child-protocol/selector/accounting
conditions exercised by the tests. It is not independent engineering acceptance.

This closes multiple-obstacle composition for the new fixed-plane development
law. Beam–shell physical ends/boundaries, curved-obstacle/beam-pair partner
transitions, surface friction/spin, native work, dynamics, mesh/enforcement
qualification and the full C0–C9 programme remain required.
