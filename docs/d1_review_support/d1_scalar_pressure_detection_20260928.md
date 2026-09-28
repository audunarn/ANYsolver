# D1 scalar pressure detection — development discriminator

This record concerns the independent guided scalar area-obstacle fixture, not
the nonlinear Q4/S3 shell formulation or D1 acceptance. The prospective
question in `GENERAL_CONTACT_RESTART.md` was whether the settled pressure
space loses structural detectability under refinement, or whether the large
physical-pressure changes can coexist with smaller force changes.

The parameterized probe uses the same aligned physical rim at `y=0.9 m`,
identical load and support conditions, exact scalar KKT solves, and common
8×9 physical force bins. It compares pressure work in the *uncoupled,
constrained structural* energy norm. The finite-reference proxy is the
smallest generalized eigenvalue of `B_h K_h^-1 B_h^T` relative to the same
pressure work on a 2× enriched structural grid. Only exactly unsupported
pressure modes are removed. The separately reported active subspace uses
the settled KKT pressure greater than `1e-9 Pa`.

| Scalar grid | Supported / active / free | Full proxy β² | Active proxy β² |
|---|---:|---:|---:|
| 8×4 | 36 / 12 / 40 | about 0 | 0.7169 |
| 16×8 | 119 / 36 / 144 | about 0 | 0.7685 |
| 32×16 | 429 / 144 / 544 | about 0 | 0.7536 |

The full-space eigenvalues are at numerical zero (within `5.2e-15`),
despite positive-definite enriched reference blocks. The weakest 8×4 mode
is concentrated at the clamped `x=0` edge. The conforming Q1 pressure basis
has work-null combinations against structural displacements fixed there;
counting total free displacement coordinates alone misses this defect.
For 8×4, the constrained work matrix has rank 32 for 36 supported
pressure modes (x cross-mass rank 8/9, supported-y rank 4/4).
The active spaces tested here have positive finite-reference ratios, but
their behavior does not certify all supported modes or a uniform bound.
For the 8×4 active space, using a 4× reference changes β² from `0.7169`
to `0.6337`; the 2× proxy is visibly reference-dependent.

| Refinement | Common-bin force L2 | Physical pressure L2 | Regular rectangle pressure L2 | Physical pressure dual-norm difference |
|---|---:|---:|---:|---:|
| 8×4 → 16×8 | 15.199% | 39.314% | 17.833% | 3.172% |
| 16×8 → 32×16 | 3.664% | 34.972% | 4.232% | 1.344% |

The regular rectangle is `0.8≤x≤1`, `0≤y≤0.75 m`.
The dual norm applies each *physical* pressure field as a load to the same
2× enriched, contact-free structural grid. Force and dual-norm differences
decrease, while physical L2 remains strongly affected by the partial-contact
front/rim. This is evidence against treating one L2 pressure percentage as
a complete mechanics verdict. It does not establish pressure-space stability
or meet the registered spatial-accuracy gates.

The exact KKT, independent same-mesh scalar Q1 check, physical-bin reaction
check and five focused comparison tests passed. The bounded run completed in
`1.03 s` with `85.89 MB` peak process-tree RSS under the existing `180 s` /
`1 GB` development cap. The probe's own elapsed time was `0.185 s` and
peak working set `107.77 MB` (different memory metrics). Python `3.14.2`,
NumPy `2.4.6`, SciPy `1.17.1`, psutil `7.2.2`; starting source
`70d3e3cb718c7d9aecc12426667702512ecb0d7a` plus the probe changes
in this commit. The retained [full JSON](d1_pressure_detection_dual_20260928.json)
contains pressure fields, bins, weakest-mode locations, source/probe/oracle
hashes and all diagnostics. Its SHA-256 is
`9658dff5cff4d57f7a7ceae8378c9f034e628b3ba381d6f53ab7230a3b980467`.
The earlier [pre-dual-norm run](d1_pressure_detection_20260928.json) is
retained for chronology; it used the same detection calculations.

**Decision:** stop this scalar refinement branch. Derive the correct shell
pressure/trace norm and treatment of pressure modes at prescribed structural
boundaries before claim-bearing D1 pressure-space assessment. Apply a bounded
same-pose shell check to distinguish a physical active-front mode from a
boundary work-null mode. Reuse the present scalar field evidence only for
the limited fixed-target claim.
