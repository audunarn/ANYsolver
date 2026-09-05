# P5 reference-conditioning development — 2026-09-05

Continuation from clean handoff `cded3c8ae151b2931c2407ee95afd2e6f8053284`.
This is author diagnostic work, not a formal qualification result. Accepted
P3/P4 evidence and the earlier P5 algebra/finite probes remain unchanged.

## Finding

The initial axis-specific bending check did not show a large error: energy
should equal 1, and the four computed values at rho = 1, 100, 10000, 1000000
were respectively 1, 1.0000000000002756, 0.9999999986468022 and
1.0000000000360039. That one mode was insufficient to assess conditioning.

A three-component constant-spatial-moment construction exposes cancellation
in the direct reference Schur complement at axial/shear stiffness 1e12
relative to bending/torsion stiffness of order one. It is a numerical issue
in the P5 research calculation, not evidence that the published formulation,
accepted straight P3 candidate, or existing shell mechanics has failed.

The diagnostic uses section diag(rho^2,rho^2,rho^2,1,2,3), spatial moment
(0.3,-0.4,1), and three helper geometries. For each half, endpoint moments
are R0^T M, endpoint relative rotations are H m, and nodal translations
are constructed from cell rotation cross reference chord. Thus z=0 and
internal moment equilibrium holds in real arithmetic. Expected energy is
sum(m^T H m)/2, independent of axial/shear stiffness. This uses the same
reference metrics; it is neither an independent continuum solution nor an
independent quadrature check.

At rho = 1000000, observed relative energy errors were:

| Helper geometry (height, shift, twist) | Direct Schur | Retained QR factor |
|---|---:|---:|
| (0, 0, 0) | 2.54051e-5 | 9.36695e-12 |
| (0.4, 0, 0) | 3.63269e-6 | 3.18657e-11 |
| (0.6, 0.2, 0.15) | 4.62203e-5 | 4.71446e-11 |

All three geometries were also inspected at rho = 1, 100, and 10000.
Those twelve tiny element calculations are development diagnostics, not a
resource-heavy benchmark or a formal scientific wave. No timing-performance
claim is made. The two curved high-contrast factor results still exceed the
unchanged 1e-11 invariant accuracy target. Thin-range qualification remains
open; no tolerance has been changed.

## Equivalent reference-factor prototype

`docs/reference_cases/ge_beam3_curved_p5_factor_probe.py` constructs B such
that the moment-reduced reference energy is ||B[q;a]||^2/2. Each half
contributes Cholesky(F)^T Dz and Cholesky(H)^-1 De. Complete QR of the six
internal columns eliminates a without forming normal equations or subtracting
large stiffness matrices. The remaining 12-by-18 factor D represents nodal
energy as ||Dq||^2/2. The local minimizer map is also retained.

This changes only an alternate research calculation, not the discrete
potential, integration rule, coefficients, production code or existing probe.
Dense D^T D can still lose small-mode energy when contracted. The benefit
reported above requires retaining and applying D, not reconstructing a dense
matrix and assuming the conditioning problem is solved.

The prototype applies only at the stress-free reference state. It does not
address finite-state geometric stiffness, indefinite equilibria, finite
local Newton conditioning, assembled solves, nonlinear section history,
state/restart, or independent engineering reference validation.

## Verification and provenance

- New focused suite: 11 passed in 1.65 seconds.
- Existing algebra and finite-probe regression suite: 41 passed in 3.18 seconds.
- The tests reconstruct the reference operator, check local elimination and
  rigid modes, construct zero-force moment states, check covariance/reversal,
  reject invalid input, and check deterministic repeated factors.
- High-contrast tests use an explicit scale-dependent floating-point error
  bound to check the numerical algorithm. This is NOT a relaxed scientific
  acceptance threshold. Passing these tests does not clear the 1e-11 gate.
- No independent derivation review, candidate freeze, resource request,
  scientific execution, selector change, merge, release or activation.

SHA-256 of the new implementation:
`8AD96D1DA598C4A0537B8886BB9DDF954DF4A0CB79AE39A5C78B79FE0A3589E9`.

SHA-256 of `tests/test_ge_beam3_curved_p5_factor_probe.py`:
`B4EC9822F1FE8EA0A6912153154B0CBA8E3E1EE02FC1DBCFF70EDCBAE205CC91`.

## Next development step

Investigate a better scaled or analytically constraint-separated reference
representation and verify its low-energy modes against an independently
computed small-matrix reference. Separately diagnose the finite local solve
at high stiffness contrast; reference-only QR cannot establish its accuracy.
Do not begin assembled slenderness or historical formal reruns to compensate
for an unresolved local conditioning issue. Independent source-equation
review remains required before P5 candidate freeze.

The complete goal remains active. Nonlinear sections for both straight and
curved beams, curved engineering cases, dynamics/buckling, installed-wheel
qualification and objective beam-shell connections remain outstanding.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
