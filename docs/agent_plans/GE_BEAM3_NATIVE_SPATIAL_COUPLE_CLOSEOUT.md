# Native spatial nodal-couple development closeout

Corrected freeze `3c3731bff590c378288bee0b8ee050241c2a0730`, tree
`d34b1f4b4261d5aaa4ee0dac620e421782d5fb08`, passes this private development
gate. The four-path extent is in the plan/status. The initial c0ace92 freeze
and all its output remain preserved but are superseded by the range guard.
No physical beam/shell kernel, material law, qualification record, public
selector, version, release or default is changed.

## Separate inventories

- Initial smoke: 3 passed, 7 deselected; 27.468 seconds.
- Initial rehearsal: 15 passed; 137.940 seconds.
- Initial line-global regression: 11 passed; 66.771 seconds.
- Initial Q4 ownership regression: 12 passed; 10.033 seconds.
- Initial frozen cycle A: 15 passed; 164.190 seconds.
- Initial frozen cycle B: 15 passed; 159.387 seconds.
- Numeric-range witness: 3 failed, 15 deselected; 5.019 seconds.
- Corrected range checks: 3 passed, 15 deselected; 3.815 seconds.
- Corrected complete rehearsal: 18 passed; 134.522 seconds.
- Corrected line-global regression: 11 passed; 67.168 seconds.
- Corrected Q4 ownership regression: 12 passed; 9.634 seconds.
- Corrected frozen cycle A: 18 passed; 172.053 seconds.
- Corrected frozen cycle B: 18 passed; 169.245 seconds.

Times are supervisor wall-time diagnostics, not speed claims. Every child used
one numerical thread, 24-GiB tree memory, a 600-second wall cap and 120-second
CPU-inactivity cap, and exited with zero active descendants. Frozen replica
pairs used concurrent fresh directories. No automatic retry or consumed resource
request reuse occurred. Clean-head/configured-runtime guards passed before/after
both initial and corrected pairs; this is not complete dependency-graph authority.

## Work, tangent and actual solver evidence

The real force-control solver now adds spatial nodal couples as external chart
work A^T m and its analytic derivative, leaving internal material forces and
Hessians intact. It uses GENERAL factorization for the unsymmetric equilibrium
tangent. Shared nodes receive a couple once; direct support couples remain
external reactions. Committed native views and issued trial poses define the
chart; foreign stores, changed patterns and unissued poses are rejected.
Mid-evaluation failures discard uncommitted trials and reset programme scope.

Tests cover 1.2-radian pure torsion, biaxial bending, large proper common-frame
rotation, coupled curved physical plasticity with distributed line forces,
connected junction loading, virtual work, directional derivatives and failed-
increment history preservation. Maximum combined directional error is
8.997113668918618e-11 against 1e-7. Maximum virtual-work discrepancy is
7.632783294297951e-17. Position/rotation covariance errors are
1.8410966031475738e-16 / 1.6346915268601605e-15 against 1e-11. The connected
free residual norm is 9.537546213014048e-15. Actual general solves include a
tangent asymmetry norm of 3.3941125496954268; no symmetrization is used.

Constant spatial couples are nonconservative on SO(3). Closed noncommuting
orientation-loop work is nonzero; no fictitious rotation-vector potential or
conservative spectral authority is claimed.

## Preserved range incident and correction

After the initial successful finite-load cycles, three new tests demonstrated
missing rejection of an overflowing effective moment sum, overflowing chart-
force norm and combined external-load norm. Finite input components alone do
not guarantee a finite convergence reference. The initial freeze was therefore
superseded before closeout, rather than treating those tests as successful.

The correction rejects nonfinite effective sums, chart forces/tangents and
native external-force norms. The combined guard is restricted to the private
native line model; old beam/shell paths are unchanged. No coefficient, physical
equation or tolerance was changed. The deliberate combined-load range test
still emits NumPy's intermediate overflow warning before rejection; its raw
warning is preserved and is not a physical qualification result.

All 24 scientific files match byte-for-byte between corrected cycles. All 18
original finite-load scientific files also match the corrected files exactly.
The corrected line-global regression's 15 files match the preserved f5cbe04
cycle-A archive with exact byte counts/SHA-256. No historical campaign rerun
was needed for those read-only comparisons.

## Preservation and next work

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-native-spatial-couple-3c3731b-20260907`.
It contains 227 data files plus the strict canonical archive manifest: all
initial/corrected runs and the failed witness, four corrected frozen sources,
15 exact test/audit commands and supervisor observations. Every byte count and
SHA-256 was verified. Manifest SHA-256:
`EF7A9BCE6C477CD52BC69590A755C1E602EDEC6820FAA00CB688157D60602006`.
The initial commit remains reachable in branch history. Original run directories
and archives remain intact; only the verified transfer duplicate may be removed.

Independent review remains PENDING; production qualification remains false.
Moment-bearing restart and distributed couples are not authorized by this gate.
The earlier line-only restart codec is not full provenance for a couple-loaded
analysis. Next bind line/couple paths in a typed accepted chain and implement
the separately reviewed distributed-couple/internal-reduction successor.

For that successor, physical station frames are U_cell R0(s). Distributed
couples load internal cell rotations, not just nodal coordinates. At internal
equilibrium, conservative internal moments balance the nonzero applied couple.
The spatial Newton connection correction must therefore use conservative
internal moments, not the net residual. The internal Jacobian and condensed
tangent are generally unsymmetric; the preserved conservative Hessian-only
Schur boundary cannot be reused unchanged for those loads. This is a next-step
derivation constraint, not authorization to alter frozen mechanics here.

General nonlinear section/path parity, complete mass/modal/buckling/slenderness/
engineering/package gates, independent review and an objective beam-shell
connection remain required. Existing B2/B3, Q4/S3 and main are unchanged.
