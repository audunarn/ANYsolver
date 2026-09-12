# Proposed private B2 physical-flexibility successor

DESIGN PROPOSAL ONLY. Specific operator-change approval is still pending.
Base: 62231d69b774f34c56eba50a4e23026d5c73ca5c. No implementation or execution
authority, amended scientific contract, accepted new formulation, or public
routing follows from this document. The full beam qualification goal remains.

## Exact proposed change

Replace only the private graph B2 scalar local potential with physical-section
force-based flexibility. Preserve public legacy BeamElement, its scalar shear
floor, generalized-section path, B3, native GE-B3, qualified Q4/S3, and defaults.
Do not call a public alternative under the old scalar identity or monkeypatch
an existing element. Use a new private local-operator identity and new graph
definition/runtime/restart authority; do not relabel prior packets.

Source background: elements.py `_beam2_basic_deformation_matrix` (814-848),
`_beam2_force_interpolation` (851-870), `_beam2_generalized_flexibility`
(873-889), and scalar nonlinear potential (4574-4615). Source normalized SHA:
f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37.
These existing equations motivate the proposal; their existence does not
authorize replacing the currently required exact scalar route.

## Frozen-equation proposal for independent review

Retain the current straight reference line, physical local-z orientation,
direct-anchor matrix chart and complete analytic first/second pullback.
No all-positive-domain exclusion is introduced to evade the shear floor.
Let S=diag(EA,GAky,GAkz,GJ,EIy,EIz), with all physical rigidities positive.
Use the existing six basic coordinates and exact equilibrium matrix H(xi):

    F = integral H^T S^-1 H ds; Kbasic = F^-1.

For homogeneous diagonal S, axial and torsional flexibility are L/EA and L/GJ.
Each bending pair has the exact two-by-two block

    F_b = L/EI * [[1/3,-1/6],[-1/6,1/3]]
          + 1/(GAk*L) * [[1,1],[1,1]].

Its symmetric and antisymmetric eigenvalues are L/(6EI)+2/(GAk*L) and
L/(2EI), respectively, strictly positive. The same force/moment sign maps as
the bound source apply. No max-denominator floor or added stiffness is allowed.
Three-point Gauss integration of this degree-two flexibility is exact;
closed-form blocks supply an independent reference, not a tuned replacement.

Use the source basic transform B with its axial row zeroed to construct K0.
For the unchanged local von-Karman axial strain

    e=(u2-u1)/L + ((v2-v1)^2+(w2-w1)^2)/(2L^2),
    U=0.5*d^T*K0*d + 0.5*EA*L*e^2,
    f=K0*d + EA*L*e*grad(e),
    K=K0 + EA*L*(grad(e)*grad(e)^T + e*Hess(e)).

Basic end forces use the physical-flexibility nonaxial operator, with axial
N=EA*e. Recover resultant=H*q and strain=S^-1*resultant at the existing three
stations, including derivatives. Verify integrated energy and virtual work
against this SAME potential. Axial geometric string forces enter the nonlinear
variation, not an invented extra physical shear. All chart Hessian and spatial
connection terms remain mandatory. No numerical frame differentiation.

This is scalar history-free elasticity only; generalized coupled sections and
history-bearing material are not accidentally accepted by reuse of flexibility
notation. Their original G4 obligations remain. Numerical implementation must
use scaled positive solves, check finite results and report representability
failure explicitly; it must not hide underflow with a new material floor or
claim every positive real is representable in binary64.

## Required bounded validation before graph propagation

Use the existing capsule and 600-second/24-GiB/one-thread child limits, at most
three children, 120-second inactivity guard, 1800-second wave, no retry.
Start with standard-library exact identities; do not rerun histories first.

1. EXACT_BLOCKS: rational integration of H against physical S; symmetry and
   positive block eigenvalues for arbitrary positive symbols via algebraic
   factorization, plus exact rational inverse identities.
2. CLAMP_WITNESS: L=E=1, nu=0, A=1e-14, Iy=Iz=J=1e-12, ky=kz=1;
   both transverse directions, displacement 1/100, axial -1/20000. New physical
   energy/work must agree, while the preserved legacy witness stays nonzero.
3. THRESHOLD_CONTROLS: same data with A=2e-12 and A=1e-10. Prove algebraic
   agreement with old scalar K where neither shear floor is active, not raw
   binary64 byte equality across different arithmetic implementations.
4. ANISOTROPIC_SHEAR: E=100, nu=1/4, A=1/10, Iy=1/100, Iz=1/50,
   J=1/200, ky=2/3, kz=5/6, L=2; separately exercise all six physical channels.
5. REFERENCE_ALGEBRA: rank six/nullity six, analytical rigid modes and work
   on a deterministic complement; no extra mode introduced by removing floor.
6. FINITE_VARIATIONS: the retained nonzero local recipe, every inherited
   directional step 1e-4/1e-5/1e-6, 1e-11 invariants and 1e-7 derivatives.
7. TRANSPORT: inherited connectivity reversal, passive coordinates, arbitrary
   common rigid motion, noncommuting increments and same-pose rebase.
8. UNITS_AND_RANGE: dimensionally consistent unit conversion; powers-of-two
   rescaling spanning below/at/above the historical floor, without threshold
   tuning. Freeze representability fixtures before implementation execution.
9. STATE_SAFETY: detached immutable output, no mutation/publication on failure,
   wrong identity/old packet rejection before construction, definition/cache
   identity, accepted-origin and prepare-all/atomic-commit enforcement.

Exact test-node inventory, runtime extent, capsule/source hash DAG and concrete
range/transport fixtures must be frozen in the successor contract after approval
and independent equation review, before any numerical implementation run.

## Evidence and remaining qualification

Existing rehearsal evidence remains valid only for its original operator and
authority. Do not reuse it as evidence for this new operator. Derive the exact
impact set from every graph/variant using B2, including multifamily loops;
freeze successor coverage without dropping any original MO01-MO18 obligation.
Other families' accepted results remain historical evidence, not fabricated
new-cycle outputs. Both full formal cycles remain mandatory after all gates.

Q4 physical recovery remains a separate unresolved derivation. This proposal
neither changes qualified Q4 mechanics nor treats its signed channels as one
physical resultant. Do not dispatch the full 375-history/3450-prefix matrix
while that requirement or another mandatory obligation remains open.

Approval requested is specifically to replace the private exact scalar B2
operator requirement with this independently reviewed physical-section successor,
while preserving public legacy behavior. Full-domain physical parity, not a
weaker admission subset, is the intended outcome. No default, release, main,
Q4/S3 qualification or ecosystem change is requested here.
