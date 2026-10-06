# Affine support and equilibrium preload arc development profile

`examples/general_contact_arc_length_affine.py` uses the public arc route for a
connected elastic S3 patch, shared nodal penalty pressure and a fixed finite
triangulated tool. It declares a nonzero root support and an optional constant
load. Tools, normal law, physical skins and the spherical metric are unchanged.

Without preload, the support is `lambda*a`. With an explicit constant load case,
ordinary contact-aware static force control first equilibrates the model at
factor one, including support `a`, under the existing arc generation lease.
Continuation then gives additive support `(1+lambda)*a` and external force
`Fconstant + lambda*Freference`. An explicitly zero-force constant load case
still performs the prescribed-support preload. No artificial load is inserted.

V2 replay requires every assembled element, including elements outside the contact
selection, to use the admitted elastic isotropic material without hardening.
Unselected plastic/unknown material profiles refuse before preload. The selected
material scope is identity-bound. Preload history count, indices and factors are
cross-checked against the deterministic static summary.

The opt-in preload namespace V2 contains the committed base pose, material state,
accepted preload pose/contact path and deterministic static summary. Its analysis
identity binds the constant load, contributor and additive stage policy. Resume
replays the bounded contact path and recomputes base equilibrium/constraints;
it never repeats the committed preload solve. No-preload contact V1 and ordinary
contact-free checkpoint helpers retain their schemas. A failed preload returns
its ordinary static status/state without any continuation increments.

Independent development controls enumerate the P1 pressure active sets using
reference areas, a separate structural stiffness and the actual imposed support.
Response uses 10 micrometres as its displacement scale, force/moment use separate
0.15 N / 0.15 Nm scales, with 1e-6 gates. Spherical metrics use actual accepted
full displacement increments and load scaling. Physical gap remains 50 micrometres.
Raw structural support component sums are not moments about an origin; tests
include each node's accepted position cross support force. Existing contact
virtual-work/tangent controls retain the 1e-5 criterion.

This is development evidence, not engineering acceptance. Nonlinear/seeded
material, imperfection, friction, augmented enforcement, moving/free tools and
finite-rotation arc profiles remain unsupported.
