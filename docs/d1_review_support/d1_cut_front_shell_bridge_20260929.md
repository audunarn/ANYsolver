# D1 cut-front shell work bridge — bounded development result

**29 September 2026. Fixed-pose discriminator, not D1 qualification.**

## Decision question

The [exact scalar counterexample](d1_cut_front_exact_counterexample_20260929.md)
shows `O(θ³)` source-Q1 work on a signed pressure mode whose continuous
work is `O(θ²)` when the target rim clips a vanishing fraction of a source
cell. Does free S3 target motion detect that mode in the actual physical
Q4/S3 work map? A source-only result would justify a pressure-pairing
redesign; target `O(θ²)` work would leave two-body stability open.

## One fixed-pose family

The [probe](d1_cut_front_shell_work.py) builds eight flat Q4 source faces
on `x=[0,2], y=[0,2]` and two S3 target faces on
`x=[−0.113,2.127], y=[−0.087,1+θ]`. The source bottom and target top
skins are parallel with 40 µm opening. Only the target's upper rim moves.
Source `x=0` nodes and the target's left nodes are clamped. The signed
analytic pressure coefficients lie at source nodes 3, 8 and 13, whose
entire x-hat support lies away from the prescribed source edge. Work is
`zᵀ Dgbar`, with `z=Sλ`; no nonlinear equilibrium is solved.

The first `θ=.1` run failed closed on an exact clipping-boundary vertex.
Its [log](d1_cut_front_shell_010_log_20260929.txt) and
[resource record](d1_cut_front_shell_010_resource_20260929.json) are
retained. Extending the target left and lower edges generically removed
the artificial tie while preserving the full source x and lower-y support
and the target upper rim. The successful family used the same mechanics
and tolerances. Every run remained below 3 s and 175 MB process-tree RSS,
within the 180 s / 1 GB development cap. Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1 and one BLAS thread were recorded in each raw result. Contact
source was `4a3ba157b5d8c174569045c97cca9a27c40f155a`.

| Cut fraction θ | Free source normal work | Free target normal work | Target work / θ² |
|---:|---:|---:|---:|
| 0.100 | 9.522741e−5 | 4.419493e−4 | 0.044195 |
| 0.050 | 1.299647e−5 | 1.017924e−4 | 0.040717 |
| 0.025 | 1.719748e−6 | 2.408844e−5 | 0.038542 |

The source norm equals the independent exact tensor-Q1 expression
`(θ³/3−b²/d)√(1/8)` to relative error at most `7e−15` across these
poses. The full production force agrees with negative pressure-gap work
within `2.51e−19` in the recorded Euclidean units. Source and target
director-rotation work is at roundoff scale in this flat normal variation.
The target work is present on its **free** nodes 17 and 18, not only on
the clamped edge. [Raw v3 records](d1_cut_front_shell_010_v3_20260929.json),
[second cut](d1_cut_front_shell_005_v3_20260929.json) and
[third cut](d1_cut_front_shell_0025_v3_20260929.json) retain nodal
components and adjacent logs/resources. Earlier successful v2 records
are retained as the pre-refinement observations.

## Independent target-side limit

For this pressure mode, the scaled y-pressure converges as a measure:

```
θ⁻² pθ(y) dy  →  (1−3y) 1_[0,1](y) dy + 1/2 δ_(y=1).
```

The bulk term is invisible to the two full-cell Q1 source tests only after
the rim atom cancels their remaining moments. It need not be invisible to
the target's piecewise affine tests across its physical S3 diagonal.
An [independent piecewise-polynomial calculation](d1_cut_front_target_limit.py)
uses only the explicit two-triangle barycentric basis, splits at the x-hat
knot and S3 diagonal, and includes the rim atom. Its 3×2 Gauss rule is
exact for the resulting pieces. The limiting free-node work coefficients
before contact sign convention are `(-0.02541607853, +0.02541607853)`;
their norm is **0.03594376296**. The measured free-target norm divided
by `θ²` moves toward this nonzero limit. The production gap-gradient
components have the opposite sign, approaching
`(+0.02541607853, −0.02541607853)` after division by `θ²`. The
[raw analytic result](d1_cut_front_target_limit_20260929.json) is retained.

An independent reviewer checked the fixture, force map, constraints,
source/target trends, target-limit derivation and sign convention. The
target-side formula is an independent work oracle; the three production
poses by themselves are only a trend.

## Disposition

The two-S3 target detects **this** source-Q1 signed mode at order `θ²`,
including on unconstrained target coordinates. The scalar source-only
counterexample therefore does not reject the required deformable-target
Q4/S3 profile. It remains a warning for a separately admitted fixed-target
cut-rim profile.

No uniform inf-sup lower bound, full active/critical-cone analysis,
two-body energy-dual reference, nonlinear equilibrium or spatial response
gate was established. The saved nonlinear front has a strictly open
intermediate row, whereas this analytic direction presumes another active
front. Keep fine Q1 and the present monolithic candidate for the bounded
D1 workflow. The next pressure check must use the full two-body active
work space and an independent structural energy reference. Do not alter
the production pressure law or repeat a larger coupled mesh from this
single-mode result.
