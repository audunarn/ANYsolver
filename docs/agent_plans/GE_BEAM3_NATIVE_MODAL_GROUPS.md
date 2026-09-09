# Complete reference-modal-group development gate

Base ff678e395eb5eb3bebdfa5dc2bc5dbe840abff89, tree
1237a4bd10cb18696b3ec4d4fef85f798ae45038. Five research-only paths:
this plan, ge_beam3_reference_modal_groups.py,
ge_beam3_continuum_frequency_shooting.py,
ge_beam3_curved_p5_modal_reference.py, test_ge_beam3_native_modal_groups.py.
No production mechanics, state, mass, tolerances, defaults or public changes.

## Preserved diagnosis and changed comparison

The historical six-mode gate remains NO_GO_GE_BEAM3_MODAL_OR_BUCKLING.
The saved-pencil diagnosis at the base records an exact unchanged trace map
and same-count eigensolve. An expanded eigensolve exposes the seventh bending
mode with 1.1761% frequency error and 0.99274 physical MAC against the sixth
continuum mode. The native sixth is the neighboring second torsional mode.
Neither that diagnostic nor this successor reclassifies historical evidence.

The reference-only policy GE_BEAM3_REFERENCE_BAND_COMPLETE_MODAL_GROUPS_V1
forms connected groups from [0.98*omega,1.02*omega] frequency bands. This
uses the existing 2% engineering criterion, not candidate-calibrated spacing.
Target the first six reference modes, including the entire group containing
mode six. Compute ten reference frequencies and require a disjoint guard mode
beyond the closed group. A group reaching the end of the window fails closed.
Groups and the mode count are fixed before any native model is evaluated.
No mode relabeling or candidate-driven matching is allowed.

Within each group compare physical mass-weighted subspaces using the minimum
squared principal correlation; require at least 0.95 at N8. Gram Cholesky
whitening/SVD is checked against scipy.linalg.subspace_angles on separately
stacked physical fields, agreement <=1e-11. This is an algorithmic cross-check,
not independent authorship. Singleton groups reduce to the original MAC.
Fixed-index correlations remain diagnostics. Frequency errors retain sorted
index comparison, decreasing maximum error on N1/2/4/8, and <2% at N8.

## Reference and unchanged mechanics

Retain the continuum equations, inherited source ledger, geometry, sections,
physical inertia, supports, station integration and native operators from
GE_BEAM3_NATIVE_CONTINUUM_FREQUENCIES.md. Extend the existing Ritz input
domain to allow 20 and 24 terms, leaving all old values/defaults unchanged.
Use Ritz 20/24 terms with 96 points for ten roots; require frequency changes
<1e-7. Compare 24 terms at 64/96 points, requiring <1e-11. These are unchanged
reference error limits, applied to the larger window.

Extend the shooting interface with explicit mode_count in [6,10], default6.
Solve only the closed reference group with the unchanged ODE11/ODE13 profiles,
60-second/60000-callback bounds, disjoint +/-0.2% brackets, root tolerances,
boundary/work checks. Profile frequency agreement <1e-8, Ritz/ODE <1e-7.
A reference check failure blocks interpretation; no bracket widening or retry.

Cases remain straight-diagonal, straight-coupled, curved-coupled. Each uses
N1, N2, N4, N8. Native mass normalization <=1e-11, reference orthogonality
<=1e-8; positive eigenvalues and byte-unchanged accepted state are required.
No eigenvalue clipping, artificial inertia or altered condensation.

## Separate inventories and execution

- Group local: 13 tests, 13 scientific JSON files (including invalid counts).
- Inherited reference local: 12 tests, four scientific JSON files.
- Each geometry: one test, eight scientific JSON files on complete success.

Run the two local smoke inventories before the three geometry rehearsals.
Only after all pass, two fresh-directory repeats of each inventory; require
byte-identical canonical scientific files separately for every inventory.
Freeze clean implementation before execution. Supervisors bind its commit,
fresh exclusive directories, runtime identity checks and full process trees.
At most three workers, one numerical thread, 24 GiB each, 600 seconds per
child, 120 seconds CPU inactivity, 1800 seconds per complete wave. No retry.
Preserve failure logs and partial diagnostics; never publish a partial PASS.

Process/evidence failure blocks; reference failure blocks engineering
interpretation; native frequency/group contradiction is a development
NO_GO_GE_BEAM3_MODAL_OR_BUCKLING. Success establishes only these registered
comparisons. Independent review remains PENDING. Extreme slenderness,
general geometry/support/material/dynamic parity, production integration and
objective beam-shell connection remain outstanding. Full goal is unchanged.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
