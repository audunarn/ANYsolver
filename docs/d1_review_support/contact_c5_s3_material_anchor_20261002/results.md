# Planar S3 material-anchor friction — development result, 2 October 2026

Parent c1f05cf8; worktree `ANYsolver-contact-main-reconcile-20261001`, branch
`codex/contact-main-reconcile-20261001`. Candidate source/fixture hashes, numerical
environment and imported paths are in raw installed manifests. This is Level A
development evidence; it establishes neither C5 acceptance nor application/release
admission. Existing accepted normal subsets and all historical failures are intact.

## Integrated result

`S3_PLANAR_MATERIAL_ANCHOR_STATIC_DEV_V1` composes the existing projected mortar
normal owner with a persistent target facet/barycentric anchor. Actual target FE
interpolation convects the anchor; Coulomb return moves it across facets. The same
ordinary static path owns equilibrium, constraints, accepted history and restart.
The target's in-plane deformation is solved rather than fully prescribed.

The coupled case presses, sticks, crosses the artificial target diagonal in slip,
reverses, opens and recontacts. A 3/6 split exactly reproduces its ordered history
and final displacement within the declared tolerance. Changed friction definitions,
invalid coverage and corrupted anchor/storage reject before mutation. Local checks
cover independent uniform pressure/cap response, physical pressure cross derivative,
affine material convection, nonproportional common-spin work, no commit force jump,
smooth directional derivatives, one-sided seam residuals and zero-pressure history.

## Observed checks and resources

| Run | Observed result | Scope |
|---|---|---|
| source local v1 | 3 passed in pytest5.94s | Convection/work/crossing and state validation; earlier normal definition |
| source coupled v1 | 2 passed in pytest9.48s | Real deformable-target workflow/split restart and pressure/tangent; earlier normal definition |
| corrected source v2 | 6 passed; owner11.8645785s/183615488B peak | Includes seam/apex work discriminator and reviewed normal correction |
| source limit v3 | 2 passed; owner5.7402101s/180092928B peak | Zero-pressure projection loss and co-stretch regularization sensitivity |
| isolated build | Passed;13.5378746s/125169664B peak | Wheel build and local installation, no network/dependency replacement |
| final installed selection | **13 passed**;37.2726979s/178061312B process-tree peak | All8 material-anchor checks,2 legacy static/restart/context checks, retained-spin check and2 example modes |

Final wheel SHA256:
`30499198c1f20f514984600fa9c681682b59286b892ddd5ffb92f852089012f1`.
All456 source/wheel/site Python modules match byte for byte;237 imported modules
resolve inside the isolated site. Effective JIT off and BLAS/Numba1 are asserted
before and after the installed run. Routine caps180s/999292928B are retained.
Raw artifact root: `C:/ANYworkspaceWork/contact-anchor-package-20261002`.

## Review, corrections and retained uncertainty

Early Mistral Read found a normal/normal-derivative mismatch across anchor facets.
The candidate now differentiates one global patch area-vector normal; internal
triangle edges cancel. Its apex-motion virtual-work discriminator passes at either
seam facet. Return lookup uses machine-roundoff tie normalization rather than the
geometry-admission tolerance; excessive cone error rejects. Separate storage change,
return storage drop and projection loss prevent those numerical channels from being
labelled frictional dissipation. Negative physical gap at zero pressure retains a
returned zero-gap anchor; physical opening releases it. Checkpoint storage is
validated from the anchor and pose before publication.

Second Mistral Read found no equation error in the declared planar profile, while
retaining derivative, scale and energy limitations. Its statement that the seam
residual appears C1 is stronger than the tests establish: one-sided derivatives
converge separately; full generalized tangent admission remains open. See the
[review disposition](independent_review.md). Source-only reviews ran no tests and
are not scientific acceptance. Subsequent column-union/roundoff-scale safeguards
and explicit reporting labels do not alter the reviewed contact equations; the
final installed selection verifies their integrated behavior.

Common co-stretch of a nonzero spatial elastic gap can trigger return under this
regularized interacting-gap model. An independent scalar calculation reproduces
that contribution and its fourfold reduction at4x tangential stiffness with equal
initial traction. This is not physical-slip truth or a continuous-path work claim.
Endpoint/chord dissipation, regularization and time-step effects require refinement
before C5 admission. Exact sliding-seam/rim tangents reject; coverage is full,
quadrature fixed, finite rotations/creases and partial-overlap history remain open.

No frozen evidence was replayed/regraded, no resource/tolerance increased, no
whole-route speedup or no-contact5% performance claim is made. Unchanged no-contact,
historical sphere and accepted normal paths are reused by source impact analysis.
The full C0–C9 programme remains active.
