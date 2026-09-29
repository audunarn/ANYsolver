# D1 deformable-target spatial reference — review candidate

**29 September 2026. Development comparison, not a frozen 2% pass.** This
uses the independently clipped small-motion Q1 mortar oracle under one fixed
0.04 N physical bump load, common `10⁻⁴` slope, perimeter-supported Q4
source, fully left-clamped S3 target with `E_target=5 E_source`, and the
same physical target extent. The target remains deformable. The production
comparison is the accepted two-step 12×12-Q4/4×4-cell-S3 pose at `y=−0.1 m`.
Reference construction and oracle limits are in
`d1_two_body_reference_oracle.py` and the retained saved-pose comparison.

## What the existing grid says

The candidate refined discrete reference is the independent 24×24-Q4 /
6×6-cell-S3 solution. One missing grid corner, 24×24/4×4, was computed
without a coupled nonlinear solve in **7.74 s/687 MB** under the routine
180 s/1 GB cap. With the existing 16×16/4×4 and 16×16/6×6 references,
it measures source refinement, target refinement and their cross interaction
at matching physical loads and supports. [Raw grid summary](d1_spatial_reference_grid_summary_20260929.json),
[new corner](d1_spatial_ref_source24_target4_20260929.json),
[resource](d1_spatial_ref_source24_target4_resource_20260929.json).

| Observable | 24/6 reference | 12/4 production difference | Source 16→24 at target 6 | Target 4→6 at source 24 | Cross interaction |
|---|---:|---:|---:|---:|---:|
| Integrated normal force | 0.018536660 N | 0.3158% | 0.8034% | 0.3635% | 0.0010% |
| Source `uz` at (0.6, 0.6) m | −0.192068 mm | 0.4580% | 0.2256% | 0.8276% | 0.0135% |
| Source `uz` at (0.6, 0.7) m | −0.180934 mm | 0.0468% | 0.5379% | 0.7221% | 0.0412% |
| Source `uz` at (0.6, 0.9) m | −0.105502 mm | 0.2146% | 0.3972% | 0.5782% | 0.0758% |

All percentages use the absolute 24/6 reference value of the same
observable. The cross term is `|R24,6−R24,4−R16,6+R16,4|/|R24,6|`.
It is small for integrated force and below 0.076% for these displacements.
The source sequence is **not monotone**: the 12/6 force is closer to 24/6
than the 16/6 force. Therefore the 0.316% production/refined difference
could include cancellation and cannot serve as the error estimate by itself.

The sum of the last measured source and target changes is 1.167% for force
and at most 1.260% for the three displacements. Their small measured cross
terms support using these as an *empirical uncertainty indicator*, not a
rigorous upper bound on the continuum tail. The remaining headroom under
the 2% response gate is 1.684% for force and at least 1.542% for the
displacements. An independent assessor must decide whether this grid and
the oracle's stated small-motion scope justify a registered uncertainty
within that headroom. No safety factor or acceptance threshold is being
selected from the observed production agreement.

## Decision before formal assessment

If the existing grid is adequate, freeze the exact reference data, units,
observables, uncertainty treatment and final-source nonlinear input before
one claim-bearing comparison. Verify same-mesh oracle/production model
difference and the ordinary equilibrium, gap, integration and pressure
gates separately. If uncertainty remains unresolved, choose **one** added
independent refinement that discriminates source-tail from target-tail error,
preflight its memory first, and retain the current nonmonotone sequence.
Do not infer the 2% result from close force agreement or silently convert
the linear oracle into a general nonlinear/deformable-work proof.

## 29 September bounded source-tail discriminator

One offline source32/target6 reference completed in 21.73 s with 1.72 GB
peak process-tree memory, after a 3.10 GB allocation inventory. The general
coupled fixture and its energy-evaluation cap were not expanded.
[Reference](d1_spatial_source32_target6_reference_20260929.json) and
[comparison](d1_spatial_source32_target6_comparison_20260929.json) retain
the full input identities and failed initial import preflight.

The contact force is 0.0185846458 N. Source16-to32 force changes by 0.5431%
and source24-to32 by 0.2582%; production12/target4 differs by 0.0568%.
The three production displacement differences are 0.3586%, 0.2494% and
0.1891%. These close differences remain development observations.
Nested force differences contract, but the central displacement reverses
direction and its last nested difference grows. There is no established
common asymptotic tail bound. **Stop this empirical refinement branch.**
The 2% spatial gate remains open pending an independently assessed error
method or an alternative representative reference; no threshold or
uncertainty factor is inferred from these outputs.
