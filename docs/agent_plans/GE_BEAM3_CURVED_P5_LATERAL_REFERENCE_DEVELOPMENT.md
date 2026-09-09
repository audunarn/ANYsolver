# P5 continuum lateral-neutral result — 2026-09-06

Research successor to `09d7fb1cfeb73620efc2afe8882684bc7c2e7ca2`, tree
`ab3265ab0f63ab7bfcd468b4e6e681dd1cdb1c85`. The separately reconstructed
continuum reference does not import discrete beam mechanics, cached tangents,
recovery, or continuation. It remains same-author development: neither
independent review nor a rigorous spectral/interval certificate is claimed.

## Equations, guards and the preflight finding

The companion equation map derives the out-of-plane second variation from
material strain/curvature, spatial multiplicative rotations, and quadratic rod
energy. It retains initial-curvature effects through the independently solved
base and retains spatial force and moment prestress terms in the variation.
Physical end constraints are clamped; the dead crown force has no second-
variation load tangent. Two half-intervals meet through continuous variational
displacement/momentum rather than smearing the crown force jump.

The tests compare the scalar coefficient quadratic form against separately
constructed rational cross-product/rotation variations, including unequal
torsion/lateral-bending stiffness and nonzero moments and forces. A separate
check reconstructs incremental spatial force/moment balance from the symmetric
Jacobi equations. Straight tests compare against both a matrix exponential and
the derived analytical clamped-column neutral condition. Tension, unloaded
states, reflection, piecewise transfer and bounded failure paths are covered.

An initial test failed because per-column normalization amplified a vanishing
boundary column. The equations themselves did not change. A common matrix
normalization corrected that reporting defect; zero/near-zero column tests
now protect it. The failure occurred before the arch reference evaluations;
it did not alter any accepted discrete qualification or proof packet. No
threshold was relaxed to accept the failed diagnostic.

After correction and adding bounded root tests, the suite passed **26 tests
in 0.41 seconds**. The artifact-generating root computations were separate
small reference diagnostics, not discrete beam or resource-wave reruns.
The unchanged planar-reference regression inventory separately passed
**17 tests in 1.25 seconds**.

## The sampled discrete sign change is earlier

The continuum base was freshly solved at the two preserved final discrete
crown drops. BVP9 supplied the base fields; IVP9/IVP11 independently checked
transfer integration, and stride-one/stride-two compared Hermite interpolation.

| Crown drop | Continuum load | IVP11 stride-1 determinant | IVP11 stride-2 determinant |
|---:|---:|---:|---:|
| 0.03717258569148828 | 0.028696361113710423 | 0.002812339324603073 | 0.002812339311289264 |
| 0.044820372353098756 | 0.027873673548955667 | 0.00020536863335727983 | 0.0002053686143213955 |

Both are nonsingular positive-determinant boundary maps. At the latter drop,
the discrete model already has a negative lateral direction. This difference
is not hidden. A determinant's sign is not an inertia count, so the table
alone cannot prove that the continuum is positive definite throughout the
interval or exclude earlier pairs of neutral points.

The explicitly added endpoint d=0.05 has continuum load 0.02698655468862975
and IVP11 determinant -0.0009059505515565326. The original equation-map file
records this deliberate interval extension before the bounded root diagnostic;
the root routine itself never searches for or expands a bracket.

## Bounded lateral-neutral bracket

Exactly twenty bisections were performed inside
[0.044820372353098756,0.05], first with stride-one and separately with stride-
two base interpolation. Both returned the identical displacement endpoints:

    left  = 0.04564716575317947
    right = 0.04564717069285733

Width is approximately 4.94e-9. Endpoint loads are
0.027747213792589615 and 0.027747213018465982. For stride-one the determinant
is +8.956890709503242e-11 on the left and -1.1021514888910858e-9 on the right;
stride-two gives +8.682312756309959e-11 and -1.1079319017487253e-9. These are
binary64 observed brackets, not certified outward-rounded intervals.

Each diagnostic retained all 22 base/transfer evaluation summaries and both
endpoint continuum fields/transfer matrices. Maximum transfer callbacks were
485 and 689, respectively, below the 10,000 cap. Each operation also had a
30-second cooperative whole-operation deadline; the combined command finished
in about four seconds. No timeout, failed evaluation retry or hidden search
extension occurred. Read-only checks verified the stored code/equation hashes,
trace counts, opposite endpoint signs, width, and equal endpoint coordinates.

Disposition: `OBSERVED_CONTINUUM_LATERAL_NEUTRAL_BRACKET`. This supports a
physical lateral-buckling mechanism in the vicinity of the discrete change,
but does not identify the discrete eigenvector or establish mesh convergence.
The discrete path only provides sampled signs, not a root-located critical
state. No 2% critical-load/displacement gate is declared passed. Mode-shape
comparison and a separately bounded refinement/root study are still needed
to distinguish approximation error from a spurious discrete instability.

## Preserved external records and source identities

Root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-continuum-lateral-20260906-b7443649efdf418b808dd746d00cb166`.

| File | Bytes | SHA-256 |
|---|---:|---|
| root-stride-1.json | 34293 | 3CAB47BFB275DE3D9AF26609F9F1291717420285BE1EBB458815B5C7B4D08E20 |
| root-stride-2.json | 34291 | FE310EC8836FDD0ADB58B8C910A47F111D32AD4097FE6BD9534279323FB6A1DA |

Both records bind the executed reference source SHA-256
`746F31E3327B8BBC69665EB01FDE74BA60ECC45E8ED9AB636E84A73BE35A0CEC`
and equation-map SHA-256
`AA43A98C4BA2459FA3E3B525293744820B1B875C81425C1FD0119B8A43EDAE03`.
The two outputs are different interpolation studies, not claimed byte-identical
cycles. Their endpoint displacement agreement is the reported comparison.

## Resumption boundary

Next recover the continuum lateral neutral shape from the preserved transfer/
base fields and compare its nodal direction with the preserved discrete odd
mode. Keep physical mass/modal claims separate from coordinate-metric shape
overlap. Do not modify the discrete element to force agreement; use independent
equations and bounded refinement to investigate any difference.

The overall programme remains active. General nonlinear material/state parity,
broader curved/slender and fully spatial references, robust local solves,
physical mass/dynamics, prestressed modal, production interfaces/restart,
independent review, packaging and objective beam-shell joints remain open.
No src, B2/B3/Q4/S3 mechanics, defaults, aliases or earlier proof/evidence files
changed. No resource request was consumed or reused by this small continuum
study. No push, merge, release or activation. Every result retains
production_qualified=false and NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
