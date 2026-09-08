# Native bending/curved continuum-frequency development gate

Base 3645e86bf66d249907497eb8649e4a10f92eb3c5, tree
37f5d6c0455e0dffbc9e1862499839b53126c3ad. Research-only three-path extent:
this plan, ge_beam3_continuum_frequency_shooting.py and
test_ge_beam3_native_continuum_frequencies.py. No production-source edits.

## Frozen inherited inputs

- docs/reference_cases/ge_beam3_curved_p5_modal_reference.py:
  SHA-256 A98AF050A92380DE496F75B6D4D4EA1CA1C58B4BBF6FDA69F738D5E06DC2FCCE.
- docs/reference_cases/ge_beam3_curved_p4_source_ledger.json:
  SHA-256 7550E16D2538927FE0732EC733785D9A316E6E5D110FA99AC02DD07EEC5A9547.
- src/anysolver/_ge_beam3_native_generalized_modal.py:
  SHA-256 557425DC826A213F4B75524E0093FBB2604D3040C43BFE30BFE9CA647704B7FC.

The existing source ledger retains its exact artifact/equation routes.
Bibliographic cross-checks: Bali et al., DOI 10.1002/nme.6994, equations 6-11
(spatial balances/strains); DOI 10.1016/j.cma.2023.116495, equation 8 (inertia
in force/moment balance). Primary indexed equation text was accessible;
full-page retrieval was unavailable. No new PDF artifact or source authority
is claimed. The specialization below is author-derived and requires review.

## Separately implemented continuum reference

Reference curve r(t)=(t,h(1-t*t),0), -1<=t<=1; material frame columns are
(tangent, global z, tangent cross global z). Spatial perturbation q=(u,theta)
has strain (R.T(u_s+tangent cross theta), R.T theta_s). For generalized
elastic C and physical inertia J, define P=diag(R,R), S=P inv(C) P.T,
D=P J P.T, A=[[0,-skew(tangent)],[0,0]]. Integration by parts of the
quadratic elastic-minus-inertial potential gives

    q_s = A q + S f
    f_s = -omega^2 D q - A.T f,   f=(n,m).

Clamped q(-1)=0; free f(1)=0. The reference implements this 12-state system
directly, with six independent initial force columns. It imports no
ANYsolver or prior mechanics/frame/recovery/eigen helper.

Use the existing independent-code polynomial Ritz energy reference at
12/16 terms and 96 integration points; also compare 64/96-point quadrature.
Require first-six frequency changes below 1e-7 for polynomial refinement,
1e-11 for quadrature. Freeze disjoint shooting brackets at +/-0.2% of the
converged Ritz roots. No expansion/retry if a bracket fails. This anchoring
is disclosed, not a theorem excluding every unobserved continuum root.

Shooting profiles: DOP853 ODE11 (rtol=1e-11, atol=1e-13) and ODE13
(rtol=1e-13, atol=1e-15). Each is limited to 60 seconds and 60000 RHS calls.
Root solve: xtol=1e-12, rtol=1e-13, at most 60 iterations. Both profiles
must agree within 1e-8 in frequency; Ritz/ODE within 1e-7.
The high profile must satisfy normalized continuum energy identity 1e-11;
the coarse profile uses 1e-9 as its reference-discretization check.
Endpoint-force residuals use 1e-11 in both. There is no production tolerance
change. Analytic axial/torsional roots, Hamiltonian structure and rigid
fields independently check the ODE signs/kinematics.

## Frozen campaign

Cases: straight-diagonal, straight-coupled, curved-coupled (height .2).
C diagonal [1000,400,350,.8,1,1.2]; coupled adds symmetric C03=.04,
C15=.03. Uncoupled inertia diagonal [2,2,2,.07,.09,.11].
Coupled physical inertia uses mass 2, centroid [.03,-.02,.01], and
centroidal rotary tensor diag(.07,.09,.11), with the full parallel-axis
and translation/rotation blocks. These match the inherited native fixture.

For each case run N1/N2/N4/N8 with six actual native signed modes.
Require positive first-six eigenvalues, unchanged state, decreasing maximum
frequency error, finest maximum error <2%, and each finest mass-weighted MAC
>=.95. Compare physical lifted translation and cell rotation at 32 points per
half-cell against the continuum fields, not only algebraic nodal traces.
Native kinetic normalization must agree within 1e-11; separately integrated
reference mode orthogonality within 1e-8. No mode clipping or reassignment.

Separate inventories: local 12 tests (four scientific files); each geometry
one test with eight scientific files. Local smoke precedes the three geometry
rehearsals. Only if all pass, run two fresh-directory repeats and require
byte-identical scientific files within each inventory.

All workers: one numerical thread, 24 GiB process tree, 600 seconds,
120-second CPU inactivity, at most three concurrent. Whole wave <=1800
seconds; terminate its full tree on breach. No automatic retry. Preserve
all partial diagnostics; never create a passed partial aggregate.

## Decision boundary

Process/evidence failures block this gate. A reference failure blocks
engineering interpretation until corrected under a new freeze. A native
frequency/mode contradiction is a development NO-GO, not permission to tune
mechanics, inertia or tolerances.

A pass establishes these registered continuum-frequency comparisons only.
It does not qualify arbitrary curved geometry, extreme slenderness, broad
support/material/dynamic parity, public integration or beam-shell joints.
The strong and weak implementations are same-author work; independent
authorship/review remains PENDING. Full goal remains intact and incomplete.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
