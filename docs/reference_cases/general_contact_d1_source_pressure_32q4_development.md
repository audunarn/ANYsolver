# Distributed shell pressure under 32-Q4 source refinement

**Status:** bounded development, 28 September 2026. The new 32-Q4 run is
neither an independent continuum reference nor a formal acceptance run. It
does not change the earlier frozen 8/16/24-Q4 evidence.

## Question and unchanged case

The flat, fixed two-S3 target and the distributed 0.3 N three-step press are
unchanged. The source uses 32 Q4 faces with fine nodal Q1 pressure, explicit
10,000 Pa/m normal regularization, 50 µm physical-gap tolerance, 1e-5 Pa
pressure-change tolerance, seven augmentations and 250/200 Pa supported-Schur
caps. The only intended mechanical change from the earlier 24-Q4 source
candidate is source refinement. The 32-Q4 press took 496.8 s, including its
nonlinear and pressure updates.

The raw result is
`reports/general_contact_d1_distributed_32q4_fine_press_dev_20260928.json`.
It completed 3/3 steps. At full press: source force 0.103857266657 N,
minimum independently checked gap -0.01791 µm, final pressure change
3.60e-14 Pa, reduced residual 1.27e-9 N, 66/66 supported pressure rank,
24 active modes and four augmentations. The reported pressure Gram scaled
condition is 10.937; its two full-press Schur conditions are 24,402 and
20,078. No numerical limit was raised.

## Field and response comparison

The read-only
`scripts/general_contact_d1_pressure_field_compare.py` reconstructs the
piecewise bilinear pressure on each source reference face and integrates the
squared field difference exactly over common-refined intervals. Saved
comparison reports cover the full strip, the contact-front neighborhood
`x∈[0.625,0.75]`, and the established-contact interior `x∈[0.8,1]`.
Here x is the normalized source-strip coordinate, shared by all meshes.

| Source Q4 count | Full-press force (N) | Peak nodal pressure (Pa) | First active x | Active modes |
|---:|---:|---:|---:|---:|
| 8 | 0.1034798152 | 0.63217 | 0.75000 | 6 |
| 16 | 0.1038715597 | 0.50478 | 0.68750 | 12 |
| 24 | 0.1038788373 | 0.59754 | 0.66667 | 18 |
| 32 | 0.1038572667 | 0.69139 | 0.65625 | 24 |

| Reference-strip region | 16→24 absolute L2 change | 24→32 absolute L2 change | Later-field-relative change |
|---|---:|---:|---|
| Full x∈[0,1] | 0.0145123 Pa m | 0.0287703 Pa m | 7.04% → 13.82% |
| Front x∈[0.625,0.75] | 0.0120918 Pa m | 0.0279147 Pa m | 11.22% → 25.40% |
| Interior x∈[0.8,1] | 0.0027788 Pa m | 0.0011561 Pa m | 1.759% → 0.732% |

The units for these L2 values use a unit-width reference strip in y and a
one-meter source span in x. The force changes by about 0.0208% from 24 to
32 Q4, while the *whole-field* pressure change grows. Nearly all of the new
L2 difference lies in the moving contact-front neighborhood; the established
interior improves. The first active source mode moves left with refinement.
Independent read-only scrutiny found no concrete defect in the result or the
exact common-refinement comparator. It confirmed that about 94% of the
squared 24→32 full-field difference lies in the stated front interval. This
is a development review, not an acceptance assessment.
These observations do not distinguish physical free-boundary behavior from
pressure-space or structural discretization error. [Auliac et al.](https://www.numdam.org/item/10.1051/m2an/2012064.pdf)
analyze free-boundary singularity effects in a different Signorini mortar
problem; their rates and local solution do not transfer to this shell case.

## Decision

Do not use the 32-Q4 pressure field as an exact reference or promote complete
pressure-space acceptance. The unchanged rank, weak multiplier, physical-gap
and integration gates pass, and integrated force is relatively insensitive,
but the full pressure field is not Cauchy-monotone over 16/24/32 Q4. The next
claim-bearing pressure test needs an independent contact-front benchmark or
a separately justified edge-aware stability measure, plus source mesh and
enforcement separation. Further uniform refinement alone is not a useful
automatic next step at this measured cost.
