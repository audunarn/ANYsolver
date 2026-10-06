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
# Prospective reverse-load opening control

The separate `test_general_contact_arc_length_release.py` freezes a connected
two-S3/fixed-tool case: physical preload0.01N downward at nodes2/3/4, reversed
proportional force0.05N upward at each node, affine root offset-2um, normal
stiffness1e6 and50um gap gate. Ordinary spherical increments are initial/max0.05,
min5e-7, load scaling0.01, growth1, six steps and two physical preload steps.
The support remains the adopted additive staged offset -2um*(1+lambda).

The prepared oracle independently assembles P1 M/S, uses separately assembled
no-contact structural K and enumerates pressure active sets for the actual load
-0.01+0.05*lambda. It checks response/path/support-load-contact wrench at the
existing1e-6 gates and separate0.15N/0.15Nm scales, actual active preload/final
opening, and complete prefix3/resume3 capsule equality. Activation/release is
decided from production histories and gaps, not assumed from lambda0.2.
Final opening requires both inactive pressure and a strictly positive production
minimum physical gap; inactive weighted pressure alone is insufficient.

The bounded installed attempt reached six accepted public arc steps, then failed
in the test evidence writer on a NumPy boolean. The active/open, numerical
response/wrench and complete-restart assertions were not reached. The local
writer is repaired to preserve NumPy scalar values and save accepted capsules
before postchecks, but this repaired candidate has NOT been run. This is an open
development verification obligation, not release evidence or a passed lifecycle.
No production solver/physics/parameters were changed, no failed input was tuned,
and no new resource authority is implied.
