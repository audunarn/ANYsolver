# Arithmetic-only fraction-free successor

Parent incident: `4126c8e`, failed loaded-spectrum source `19d390e`.
Keep the incident and every raw artifact immutable. Existing mechanics,
quadrature, mass, histories, recovery, spectral tolerances, root widths,
deadlines, aliases, defaults, and qualified Q4/S3 are unchanged.

## Exact arithmetic invariant

Convert the represented binary64 H, M, and shift into one positive-scaled
integer matrix representing the exact rational H-shift*M, without rounded
subtraction. At each step A/previous is the current Schur complement.
The symmetric Bareiss update is (d*A_ij-A_i0*A_0j)/previous; divisibility is
checked by divmod at every entry. Count the sign of d/previous, not d.
Both simultaneous pivot permutations and unimodular row/column additions
preserve inertia. If every diagonal vanishes but an off-diagonal is nonzero,
replace e_i by e_i+e_j, exposing diagonal 2*A_ij. An all-zero remainder
contributes its full nullity. Arithmetic failure remains a hard error.
The unchanged 30-second exact-inertia deadline is checked at each row.

Thirty-one initial arithmetic tests passed in 1.98 seconds, including a
separate retained rational-Schur oracle, random indefinite pencils, signed
previous pivots, hyperbolic and singular congruences, dyadic cancellation,
subnormals, cancellation/deadline checks, and unchanged input arrays.
These are same-author development tests, not independent scientific review.

## Bounded measurements and successor diagnostic

Before another spectral invocation, compare both arithmetic methods on the
same 45-coordinate pencil reconstructed from the saved native-1 packet.
Bind packet SHA-256 4519178585b0ba921559bf161a5bea4425a4f069f51f7f07a306edac303204c8.
Use the saved sixth-root lower bracket, one warm-up and eleven timed pairs
with alternating order. Require identical inertia for every call. Report
median/MAD/p95 and CPU externally; no general solver speed claim follows.
The benchmark has one thread, 24 GiB, a 180-second process-tree wall bound,
a 120-second activity bound and a 120-second cooperative comparison deadline.

Only after this measurement passes may a new, separately frozen loaded-arch
diagnostic run once in a fresh v2 directory. Its two continuum equilibria,
four reference spectra and two native spectra are unchanged, with no nonlinear
history solve. The original attempt remains failed; the successor is not an
automatic retry. Require its saved first native packet and all common reference
and checkpoint artifacts to match the failed attempt byte-for-byte. Complete
raw validation, process cleanup and final source guards precede publication.
No modal qualification or buckling-factor authority is granted by this step.
