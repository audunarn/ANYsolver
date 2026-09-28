# D1 fixed-structure y-pressure discriminator — development evidence

**Question.** With the independent scalar 32×8 structure, load and physical
support held fixed, does a change in y pressure with a checked active work rank
representation materially change the near-rim physical response? A small
change would shift attention to x/front and structural resolution; a large
change would keep y/rim pressure resolution on the D1 critical path. This is
the one y-axis follow-up selected after the saved active-response comparison.

The [parameterized independent probe](../../scripts/general_contact_d1_fixed_structure_pressure_probe.py)
reuses the prior Q1 mortar/FV oracle (SHA-256
`9cfa980753f094a8373661e70ccdb55f2634894b3b02566efee76d00817991b3`)
and source-bound comparison inputs (SHA-256
`d27cf3e4908bb67170914fd9c980b1316d9afb734ddd8307a8912b3fc21290c2`).
It compares matching y knots
`[0,.2,.4,.6,.75,.825,.875,.895,1]` with the nested coarser subset
`[0,.4,.75,.875,1]`, retaining 32 x-pressure intervals and the same 32×8
structural grid. The physical support ends at y=.9; all 8×9 bins and the
piecewise-Q1 pressure L2 integral clip there. Two-point Gaussian integration
is exact for the squared Q1 difference on the union mesh. A separate
analytical clipped-cell test passed. The matching pressure field reproduces
the independent 32×8 oracle before comparison.

| Same 32×8 structure | Matching y Q1 | Coarse y Q1 |
|---|---:|---:|
| Active/supported pressure modes | 96/297 | 60/165 |
| Active unit-diagonal compliance eigenvalue ratio | 2.34×10⁻⁵ | 2.38×10⁻⁵ |
| Equilibrium residual, N | 1.77×10⁻¹⁵ | 1.70×10⁻¹⁵ |
| Complementarity product, Pa·m | 6.37×10⁻¹⁸ | 6.96×10⁻¹⁹ |
| Minimum represented physical gap, m | −1.79×10⁻⁸ | −4.66×10⁻⁸ |

The [raw record](d1_fixed_structure_coarse_y_20260928.json) reports
coarse-versus-matching differences of **0.7359%** on common physical bin-force
L2, **0.5295%** in rim-band integrated force, **0.00671%** in total reaction,
and **71.53%** in physical-support pressure L2. The large pressure change is
consistent with a rim-sensitive local field; this calculation alone does not
prove a singularity, instability or a production defect. The probe took
0.061 s after import and peaked at 84.33 MB process working set, below the
retained development limits. Its first output lacked a peak-memory field;
the resource-record rerun reproduced every mechanics comparison exactly.

**Decision.** This nested coarsening is sensitive to y representation,
especially in pointwise pressure near the support edge. Keep the fine Q1
production basis and the existing pressure-space stability gate. Do not infer
convergence or choose the coarser basis from its small total-force difference.
The next claim-bearing spatial design must distinguish regular-area pressure
from the concentrated rim reaction, check the active work-map rank, and retain
common physical bin/integrated comparisons. The complete coarse pressure
work map is not full row rank: clamping one x edge leaves at most 32
independent x work directions for 33 x pressure nodes, so five y pressure
rows provide rank at most 160 for 165 supported modes. The 60-mode active
compliance is positive definite at the settled pose; it does not certify the
complete pressure space. A larger coupled y refinement
requires a specific resource preflight and independent assessment; this
development result alone does not authorize a larger run or a new tolerance.

An independent read-only review checked source hashes, exact cross-mass,
physical-support clipping, the analytical control and KKT interpretation. It
identified the full-map rank caveat above and found no further numerical
defect in this bounded comparison. This is not D1 acceptance review.
