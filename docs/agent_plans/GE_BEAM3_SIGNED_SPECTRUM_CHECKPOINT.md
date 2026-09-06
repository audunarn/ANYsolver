# GE-B3 signed-spectrum development — 2026-09-07

Baseline `a2dbb114e4ecb6c2f45141b0b37e14188abf3231`, tree
`c2f265be51dbbef08f5d00dc762d72a326700597`. This checkpoint adds research
reconstructions and tests only. No existing source, element mechanics,
quadrature, section law, state schema, public selector or default is changed.

## Numerical change and checks

The loaded stationary Hessian is reconstructed as `K = F.T F + G` after
endpoint-moment elimination. Positive material rows come directly from the
partial-Legendre section Hessian and moment compliance. The signed `G` is
assembled from first section derivatives times strain second derivatives,
accepted endpoint-moment work and lifted spatial-dead-load work. It is not
obtained by subtracting two large tangents. This uses producer AD and section
code and is explicitly a same-author reconstruction, not an independent oracle.

Massless nodal traces are first separated by QR of their material columns.
Their signed geometric block and coupling are included in the subsequent
Schur elimination. The six cell rotations retain their actual inertia. The
physical mass is Cholesky-whitened; Jacobi SVD is applied only to the remaining
positive material rows. The total operator is kept as a large nonnegative
diagonal plus a separate signed correction. Shifted, diagonally congruent
inertia counts bracket the lowest requested squared frequencies. Negative
roots are retained; no square root of the total tangent, PSD fallback,
stiffness/mass floor, clipping or fitted coefficient is used.

The search has fixed caller-supplied brackets, a 96-step limit per requested
root and a frozen absolute bracket width of 1e-10 in these tests. Unresolved
signs fail closed. These are binary64 numerical brackets, NOT certified
intervals. The returned transformation is a spectral coordinate basis, not
completed eigenvectors of the signed operator. This is not yet a replacement
production eigensolver or a qualified buckling-factor calculation.

One straight macro at L/h=100 and 1,000,000 was solved through the actual
native force program for axial loads -1, -0.5 and +0.5. States were replayed
without mutation and checked for free equilibrium. A separate standard-library
reference constructs a planar two-cell pencil from its axial/shear,
initial-stress, endpoint-bending and kinetic terms. It eliminates massless
traces and computes the degree-four characteristic polynomial with exact
rational coefficients, then bisects two fixed brackets with 80-digit Decimal
arithmetic. It imports no producer, AD, NumPy or SciPy. It is nevertheless
same-author work, not independent review or a continuum qualification oracle.

All six cases agree with that finite-shear reference: the largest absolute
squared-frequency difference is 5.72e-11. The separate inextensible discrete
limit also agrees at high slenderness. At L/h=1,000,000 and axial load -1,
the first two squared frequencies are approximately -0.43670658028; neither
negative mode is discarded. A loaded, curved, coupled-section sample agrees
with the preserved moderate-conditioning dense pencil and verifies signed
trace reconstruction and physical mass normalization.

## Failures retained, not hidden

The preceding turn's test transcript was unavailable after context transfer.
No matching Python process remained; three raw loaded split records existed,
but the virgin record did not. No pass count is claimed for that invocation.
A direct virgin-state inspection measured geometric norm 2.2321342673e-15
and maximum station resultant norm 8.2028112952e-16. The development test's
exact-zero assertion was replaced by the existing 1e-11 roundoff-scale check.
The computed term is retained, not zeroed; no mechanical tolerance changed.

An added adversarial matrix test exposed excessive scaling by the largest
off-diagonal entry in each row. It produced an unresolved-sign exception,
not a false mode. That invocation had one failure and eleven passes. The
failed source (SHA-256 `80c236229fb7a7f32791e58585a14c607c4fbce2086999d11e67dbed35277e30`)
is archived. Scaling now uses diagonal magnitudes, with row scaling only
where a diagonal is exactly absent. The adversarial test subsequently passes.

## Validation and preservation

Separate final inventories: five split identities/rejections, eleven signed
linear-algebra/reference tests, seven loaded-spectrum tests, 23 preserved
loaded-modal tests and 17 preserved Jacobi-driver tests. The combined run
passed 63 tests in 70.16 seconds. A fresh-directory run of the 23 new tests
passed in 22.64 seconds; all seventeen emitted records are byte-identical.
The separate static run passed 23 tests in 0.50 seconds: seven new checkpoint
checks, five installed-reference checks, six relative-reference checks and
five preserved loaded-modal checks.
No formal resource request was consumed, reused or retried.

Sixty-seven files totaling 835,576 bytes, including intermediate outputs,
the recovered records and failed scaling source, were copied exclusively and
verified by byte count and SHA-256 from the normal workspace context:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-signed-spectrum-development-20260907-7c8b1cd04ceb`

The strict canonical source/archive inventory is
`docs/reference_cases/ge_beam3_signed_spectrum_evidence.json`.
Original temporary outputs and previous archives remain preserved.

## Next implementation work

Turn this validated numerical approach into a guarded private loaded-state
adapter with owned inputs, bounded cancellation, actual eigenvectors,
mass normalization and strong residual/cluster checks. Validate multi-element
curved/coupled high-contrast states, coordinate covariance and near-critical
sign uncertainty before promoting it. No reference-only positive solver may
substitute for a signed loaded solve. Broader modal/buckling engineering,
general nonlinear sections, geometry/coercivity coverage, independent review
and objective beam-shell connections remain required. Goal completion,
production qualification, publication and default changes are not asserted.
