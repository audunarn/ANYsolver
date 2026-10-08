# D1 regular-support pressure discriminator — development evidence

**29 September 2026. No production-law change or D1 acceptance claim.**
The question is whether the 16×8→32×8 decline in the minimum guided scalar
pressure detection ratio arises primarily in ordinary, fully supported
pressure hats or near the partial-contact rim. Both inputs are previously
accepted fixed-target, planar, guided Q4/S3 poses; no new coupled equilibrium
was solved. Source code at run: `28232667dd5b8464a5ca0ee5cef9eca10bdd1850`
plus the optional offline probe change, SHA-256
`a24759d1801dacc5af5c94e2413af45dbe415e9dbe794cce7e674a0d9a816ff6`.

## Fixed method

Keep the same physical work `W=diag(S)D(gbar)`, constrained shell linear
stiffness, settled active pressure space and independent 512×512 Fourier
reference with its Parseval remainder. Select a Q1 pressure hat only when
its **complete reference support** lies inside a fixed rectangle, in metres
relative to the source lower-left corner:

| Subspace | Support rectangle `(x_min,x_max,y_min,y_max)` |
|---|---|
| Full settled-active control | `(0,1,0,1)` |
| Rim excluded | `(0.125,1,0,0.75)` |
| Strict interior | `(0.125,0.875,0.2,0.75)` |

The first narrower subset removes hats that reach the `.9 m` target rim.
The strict subset also removes the lower and right physical-edge hats. The
prescribed left edge is excluded in all narrower subsets. Compare principal
submatrices of the unchanged shell compliance, finite Fourier compliance and
its certified upper matrix. The generalized eigenvalues bracket the smallest
discrete-to-continuum **squared dual-response ratio** for the guided scalar
fixture. These are not new pass/fail thresholds.

## Result

| Pressure subspace | 16×8 modes | 16×8 ratio interval | 32×8 modes | 32×8 ratio interval |
|---|---:|---:|---:|---:|
| Full settled-active | 48 | `[0.591616, 0.593137]` | 96 | `[0.432783, 0.443156]` |
| Rim excluded | 24 | `[0.772423, 0.772843]` | 48 | `[0.763796, 0.765539]` |
| Strict interior | 6 | `[0.822423, 0.822838]` | 14 | `[0.783211, 0.784806]` |

The lower-bracket minimizing vector for the full active set has 99.991% and
99.99999% of its **unweighted coefficient-square** on y row 8. Its largest
32×8 coefficients alternate in sign along x. This is coefficient
localization, not physical pressure-energy localization, and the minimizing
vector for the true continuum compliance may differ from the lower-bracket
one. Row 8's Q1 hat is clipped to `.895≤y≤.9` of its `.895≤y≤1` support:
4.76% of its height and 0.227% of its one-dimensional reference support
integral. The narrower results associate most of the full-set decline with
that rim row. The strict interior minimum also drops by about 4.8% in
squared ratio, so ordinary-region sensitivity remains.

Production-versus-independent source-transverse pressure work differs by
2.60e-13 and 6.13e-13 relative; independent Fourier-versus-clipped Gram
differs by 1.49e-15 and 3.75e-15. Structural response residuals are
7.06e-15 and 1.78e-14 relative. The full-active interval exactly reproduces
the earlier saved reference within roundoff. An independent read-only reviewer
checked complete-hat selection, matrix restriction, interval signs and mode
interpretation and found no concrete defect.

The [16×8 result](d1_regular_support_16x8_20260929.json) ran in 11.25 s at
415.15 MB peak process-tree memory; the [32×8 result](d1_regular_support_32x8_v2_20260929.json)
ran in 21.07 s at 626.95 MB, each below 180 s / 1 GB. Their
[resource](d1_regular_support_16x8_resource_20260929.json) and
[resource](d1_regular_support_32x8_v2_resource_20260929.json) records and
captured logs retain the environment and source identities. The first 32×8
invocation used a nonexistent saved filename and stopped before mechanics;
its [failed log](d1_regular_support_32x8_log_20260929.txt) and
[resource record](d1_regular_support_32x8_resource_20260929.json) remain.

## Decision

This negative control argues against changing the entire primal Q1 pressure
basis solely because of the two full-active minima. It does not establish a
uniform inf-sup bound, shell trace norm, pressure-field convergence or the
D1 partial-front gate. The two saved structures refine x while retaining the
same nonuniform y knots, so even the strict interior decline is not an
asymptotic shape-regular verdict. Define the physical quotient for the
prescribed-edge null combinations and analyze a shape-controlled cut-front
family before deciding whether the positive but very small rim supports need
an explicitly stabilized pressure treatment. Keep the existing mechanics and
resource limits unchanged.
