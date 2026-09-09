# GE-B3 V5: complete-map signed modal reassembly

Status: **development checks pass; qualification incomplete**.
Independent review: **PENDING**. This is a private numerical successor, not
public integration, a buckling certificate, or acceptance of the full beam.

Base: `316a285ae41439f49ff2319afa54016bac051d37`, tree
`24c4a4064fc941a573769089575f0fae1cacc672`. Work remains on
`codex/ge-beam3-curved-p5-objective-lift-v1`.

## Numerical change and its boundary

The preceding checkpoint preserved an actual curved E/R90 covariance failure
at L/h=1,000,000. Its separately coded Decimal audit localized most of that
probe's error to floating-point spectral reduction. That historical code,
failure, and evidence remain unchanged.

The new solver uses the preserved factor reduction only to obtain a complete
dynamic coordinate map V. It then reconstructs the original signed pencil
H = V^T (F^T F + G) V and M = V^T B^T B V, retaining geometric stiffness signs,
cell inertia, and massless nodal rotation traces. It never substitutes a
requested-modes-only subspace for this complete pencil.

Each supplied binary64 entry is converted to an integer over a power of two.
Products and sums in these bilinear forms use exact Python integers; only
each final output entry is rounded to binary64. This avoids cancellation
loss in separately rounded F V and G V intermediates. It does not claim that
the original geometry, beam equations, or their floating-point inputs are
mathematically exact. No new dependency or package requirement is introduced.

The subsequent inertia search and mode extraction remain numerical. Their
brackets are explicitly **not certified intervals**. Unresolved signs,
unrepresentable values, incomplete requested clusters and failed residuals
are rejected; no stiffness shift, negative-root clipping or mass floor is
used. The preserved signed trace elimination still requires a positive
algebraic block. Broad conditioning and units/scaling coverage remains open.

Returned physical modes undergo a second exact-supplied-data bilinear audit.
Its mode-energy scale catches false weak eigenvalues that a global normwise
backward error divided by unrelated large stiffness can hide. Separate
material/geometric action residuals and physical mass normalization are also
checked. These checks complement one another; none alone proves a complete
eigensystem or engineering qualification.

Compensated floating dot products use FMA when available and an exact Fraction
product-residual fallback otherwise. The forced fallback is tested on Python
3.13; an actual older-runtime installed-wheel test is still outstanding.
The mechanics splitter, local potential, section law, seed, force controller,
recovery and accepted-state transactions are imported unchanged.

## Observed validation

Two fresh-directory small correctness runs completed with **46 passed,
0 failed, 0 skipped each**, in 72.898 and 73.138 seconds. The **23 saved JSON
records match byte-for-byte**, including input summaries, modes and accepted
program snapshots. Raw NPZ factors and timing/JUnit diagnostics are preserved
but are not represented as a common scientific qualification aggregate.

| Separate inventory | Passed per run |
| --- | ---: |
| Exact dyadic arithmetic against Fraction reconstruction | 9 |
| Signed numerical kernel, mutation and cancellation guards | 19 |
| Research/native pencil versus 80-digit Decimal audit | 3 |
| Native state, mode covariance, prestress and replay | 15 |

The native checks include reference curved coupled sections at L/h=100,
10,000 and 1,000,000 under E, R90 and a general rotation; a finitely loaded
two-macro curved specimen under a general rotation; actual straight tensile
and compressive states; six analytical free-body modes; retained plastic
history in elastic unloading; active plastic/yield-boundary rejection; and
byte-identical loaded spectra under a 2^40 coordinate translation. These
are one/two-macro specimens, at most 42 coordinates, not a convergence or
domain qualification campaign. The curved covariance tolerance remains
rtol=atol=1e-11. The existing distinct reference-comparison tolerances are
visible in the bound tests and have not been promoted to a universal bound.

Two failed drafts are preserved: an inappropriate already-cancelled action
residual scale, and a rounded-intermediate reassembly that lost unit stiffness
when large coupled material/geometric terms cancelled. They motivated the
separate-action scale and exact supplied-data bilinear construction; neither
failure was waived or relabelled as passing. The original weak-root mutation
test explicitly rejects a forged small eigenvalue hidden by global stiffness.

## Preservation

External archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-reassembled-modes-development-20260907-ecb9c97eee78`.
It contains **134 files, 3,545,317 bytes**, verified individually by byte count
and SHA-256 from the ordinary workspace context after archival. The canonical
evidence file binds the eight new source/test files with UTF8-LF hashes,
all archive entries, both final JUnit reports, and all 23 matching JSON pairs.
Original temporary files and historical evidence remain. A kernel-only run
created no basetemp outputs; no absent raw transcript has been fabricated.

Only these private helpers, adapter, research probe, tests and checkpoint
documents are added. No existing tracked source, B2/B3, Q4/S3, accepted straight
beam, dependency, workflow, version, public alias, or default is changed.
Historical checkpoint tests remain attached to their original frozen extents;
their evidence is not rewritten as a result for this new checkpoint.

These ordinary small unit tests consumed no formal resource request. The
private kernels have cooperative cancellation and 600-second checks, not a
claim of hard process-tree termination. Subsequent isolated/formal runners
must provide their registered process/resource safeguards separately.

## Next work and open gates

1. Build from this clean checkpoint and validate the private wheel outside
   source trees, including native loaded/covariant/replay paths.
2. Broaden curved/slender loaded convergence, prestressed mode, buckling and
   postbuckling checks against separately reconstructed engineering references.
3. Complete V5 displacement/arc-length controls, general nonlinear/fibre
   sections, loads/couples/followers, solver parity and supported runtime coverage.
4. Develop the objective finite-rotation beam-shell connection, including
   eccentric and curved attachments, without delaying standalone qualification.
5. Obtain independent review and full formal qualification before public
   integration. No merge, release, default activation or completion is claimed.
