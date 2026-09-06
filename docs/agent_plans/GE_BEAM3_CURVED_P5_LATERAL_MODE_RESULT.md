# P5 lateral shape result and resumption checkpoint — 2026-09-06

The original comparison failure remains preserved at
`d3f1d9fe133b776eb4f70fdf1cc750169ff22e19`. A separately documented numerical
correction resolves the known Hermite coefficient knots, without changing
the rod equations, discrete mechanics, tolerances or existing evidence.
This successor uses new knot-resolved reference records, not the failed
comparison's old adaptive transfers. It is research, not qualification.

## Revalidated continuum endpoint records

No continuum base solve or root bisection was repeated. Reconstruct transfers
from the preserved endpoint base fields on 129 and 257 nodes per half. Their
largest normalized matrix difference was 9.186282127927082e-14. Both reference
interpolation strides retain the original opposite-sign displacement bracket
[0.04564716575317947,0.04564717069285733]. Four endpoint revalidations completed
in about 4.38 seconds combined; each propagation used 3328 or 6656 calls.

Root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-lateral-knot-20260906-e10841364c644b29b60f7c057c20a41e`.

| File | Bytes | SHA-256 |
|---|---:|---|
| root-stride-1.json | 29126 | 64C47952DACD030D81EC3A631744179C300C33052551E1EBE5C16A9E191019FC |
| root-stride-2.json | 29139 | A7917C813953D181DF20748C5E54179E0F84597585650B641FBD46B90E8F073C |

Propagator source SHA-256:
`8A5F8FC2CD58FA31A4B33EBB5BC36934F2DCD634E8940D712E0B9C28090B5C36`.
Revalidator source SHA-256:
`46CB8C8C03913DBEDC47469AEC80C1D21C6CF8A403E1CE40ACC78C1F71FDDA76`.
Each new record also binds the original root file's byte count/hash. It does
not overwrite the original transfers or misrepresent their adaptive traces as
new iterations. These remain numerical brackets, not interval certificates.

## Successor mode recovery and checks

The left endpoint is used consistently for both reference strides. Recover
the near-null boundary direction through SVD, then integrate the linear
six-state Jacobi field plus scalar quadratic-Lagrangian integral, resolving
every known coefficient knot. No nonlinear element or reference base/root
solver runs. All 33 nodal samples and actual end residuals are retained.

| Check | Stride 1 | Stride 2 | Unchanged limit |
|---|---:|---:|---:|
| Saved-transfer agreement | 5.4859290729510204e-12 | 5.045533127550559e-12 | 1e-8 |
| Normalized end residual | 2.7261299912645537e-9 | 2.2576694869353605e-9 | 1e-7 |
| Integral/boundary work consistency | 4.552301076334298e-12 | 1.5566750271376429e-12 | 1e-9 |
| RHS calls | 4096 | 4096 | 10000 |

The normalized second-variation integrals are approximately -8.16623e-11 and
-6.76307e-11, consistent with boundary work. These are near-neutral quadratic
variations with small nonzero end residuals, not negative stored strain energy
or a proof of exact constrained neutrality. No endpoint was silently zeroed.

The two continuum resolutions have combined sign-aligned shape distance
3.1355997869306875e-9. The raw squared cosine is 1.0000000000000004 from
floating-point roundoff; it is preserved rather than presented as greater-
than-perfect physical correlation. The distance is the more informative
interpolation-consistency value here.

## Comparison with the saved discrete lateral modes

Use reference-arclength trapezoid weights and span-scaled rotational
coordinates, not physical mass. The reported squared cosines are **not modal
MAC/frequency qualification**. The continuum mode and discrete modes are at
different crown drops. Sorted lowest eigenvectors need not retain a fixed
mode identity through the whole path, so all eight comparisons remain visible.

| Step (zero-based) | Combined squared cosine | Translation | Rotation |
|---:|---:|---:|---:|
| 0 | 0.04666945138098586 | 0.9990590048705117 | 0.046762071967574446 |
| 1 | 0.07290539255545722 | 0.9991585991813197 | 0.07216287720644912 |
| 2 | 0.14660316785030603 | 0.9995137326601908 | 0.1430649141111134 |
| 3 | 0.42821572674363406 | 0.9998771167993344 | 0.416083687567708 |
| 4 | 0.8704271200088044 | 0.9999862237768226 | 0.8630739410430713 |
| 5 | 0.9787953841322047 | 0.9999980692833754 | 0.9773341309503679 |
| 6 | 0.9971852551161057 | 0.9999997735012114 | 0.9969820338654882 |
| 7 | 0.999998133177368 | 0.9999999998014382 | 0.9999979938779706 |

At the final discrete crown drop 0.044820372353098756, the near-unit combined
shape agreement strongly supports the same physical lateral-buckling shape
as the separately reconstructed continuum neutral mode near 0.04564717.
It does not determine the discrete critical location, prove convergence or
exclude spurious modes elsewhere. Translation alone would have misleadingly
suggested near-agreement even at early steps, where rotational agreement is
poor. This validates retaining separate component comparisons.

The earlier discrete onset remains unresolved quantitatively. Do not declare
a critical-load/displacement gate passed from this shape agreement, tune a
stabilization, remove a negative direction or relax a tolerance. Next locate
the discrete lateral onset on multiple bounded meshes and compare critical
values against the continuum reference. Any larger run requires a fresh
resource request and frozen scope; the previous arch request stays consumed.

## Repeatability, tests and preservation

Two fresh processes produced byte-identical comparison files, in about 2.75
seconds combined. Each is **24751 bytes**, SHA-256
`0DBF23EFF59BB7E2B4A417FB62D8C1A8CA522417635EBC40B4183E01E0E9C288`.

Root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-lateral-mode-knot-20260906-ed3764de9c314809b3f371b10903f9c2`.
Files: `first/comparison.json`, `second/comparison.json`.
Mode reference source SHA-256:
`F2EBC21D48DAF48F1FF4D429220280D5CA3EC6816758522C5EFEE355DD990BB9`.
Comparison source SHA-256:
`DBE1F2AC50D9DAA13D02DBECC781BB3EA820C0C428B9130ACD318081CBFEFFF0`.
Read-only checks verified exact output equality and both executed source hashes.

Corrected suite: **20 passed in 1.61 seconds**. During implementation it also
caught an empty-sample interval call to SciPy dense output; intervals with no
requested node now skip that call, while every interval is still integrated.
The tests verify exact knot boundaries, matrix/vector linearity, unchanged
tolerances, analytical straight shape, work, endpoint/state identities,
separate comparison components and bounded failures. No scientific threshold
was changed to fix that implementation error.
The unchanged continuum lateral-reference regression inventory separately
passed **26 tests in 0.42 seconds**.

The full programme remains active and incomplete: general material/state
parity, broader curved/slender and spatial cases, physical mass/dynamics,
prestressed modal, production interfaces/restart, independent review, opt-in
packaging and objective beam-shell joints are still open. B2/B3/Q4/S3
mechanics/defaults, accepted qualification evidence and main are unchanged.
No push, merge, release or activation. Every comparison retains
production_qualified=false, qualification_gate=false and
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
