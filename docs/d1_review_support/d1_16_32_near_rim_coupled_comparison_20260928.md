# Bounded 16×8 → 32×8 near-rim coupled development comparison

**Question.** With unchanged y knots, target, load, fine-Q1 pressure and
normal/contact tolerances, does an x refinement materially change the coupled
partial-contact front and common physical bin forces? This is development
evidence, not a D1 acceptance execution or a pressure-only refinement.

The starting [16×8 coupled field](d1_saved_16x8_near_rim_field_20260928.json)
and its [same-mesh oracle comparison](d1_16x8_near_rim_oracle_comparison_20260928.json)
are bound to SHA-256
`8293e528837cc2a8a25444aa079944c9f8371f5a5b50280bb6dc91816d19b852`
and its earlier [independent comparison](../reference_cases/general_contact_d1_coupled_front_pose_development.md).
The new 32×8 run used source commit `ea69944b`, Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1, the same `near_rim8` y knots, 0.3 N distributed load, planar
two-S3 fixed target, 10,000 Pa/m normal regularization, 50 µm gap tolerance,
fine nodal Q1 pressure and 32 monolithic pivots. Both attempts omitted
checkpoint emission and retained the 180 s/1-GB process cap.

The first 32×8 attempt used `block_response_dev`. It stopped before an
accepted step with `contact_semismooth_block_response_failed` and detail
`MemoryError: monolithic block response exceeds declared dense budget`. The
[failure result](d1_32x8_near_rim_block_failure_20260928.json) and
[resource record](d1_32x8_near_rim_block_failure_resource_20260928.json)
are retained. The one corrective experiment used the existing sparse `direct`
solver without changing mesh, mechanics, acceptance criteria or resource cap.
It completed two steps in 153.07 s solver / 159.11 s process time with 509.09
MB peak process-tree memory. The [raw coupled result](d1_32x8_near_rim_direct_result_20260928.json)
and [resources](d1_32x8_near_rim_direct_resource_20260928.json) are retained.
The 32×8 field has 297/297 scaled pressure Gram rank (condition estimate
12.08), 96 active pressure modes, terminal complementarity relative force
4.35×10⁻¹⁵, and reported minimum gap lower bound −0.848 µm within the
declared 50 µm tolerance. These do not by themselves establish stability.

The independently implemented Q1/FV oracle has SHA-256
`9cfa980753f094a8373661e70ccdb55f2634894b3b02566efee76d00817991b3`.
The [same-mesh comparison](d1_32x8_near_rim_oracle_comparison_20260928.json)
validates model and pressure-node/support identity. Coupled versus independent
Q1 pressure L2 difference is 6.05×10⁻¹¹, common-bin L2 difference
2.16×10⁻¹¹, and reaction difference 9.44×10⁻¹⁴ relative. The 32×8 coupled
8×9 support-aligned bin-force L2 error versus FV is 0.4811%, with 0.2105%
rim-band integrated-force error. The earlier 16×8 errors are 0.3344% and
0.0205%, respectively. Their FV errors are nonmonotone and are not rounded
into a convergence claim.

The parameterized [common-field comparator](../../scripts/general_contact_d1_compare_coupled_fields.py)
checks both coupled-file hashes and the actual oracle file hash, records the
input-record hashes, and verifies saved model/normal settings, y knots,
pressure-node order and independently recomputed support/bin forces. The FV
bins are inherited from the two source-bound same-mesh comparison records;
their saved L2 metrics are recomputed from those bins. Its piecewise-bilinear pressure L2 integral
uses exact 2×2 Gauss on the union x grid, clipped at the physical obstacle
edge y=0.9 m; analytical full-cell and clipped-cell controls passed. The
[raw cross-mesh result](d1_16_32_near_rim_coupled_field_comparison_20260928.json)
reports:

| 16×8 → 32×8 common comparison | Difference |
|---|---:|
| 8×9 bin-force L1 / L2 | 0.1831% / 0.2521% |
| Rim-band integrated force | 0.1896% |
| Total integrated reaction | 0.00246% |
| Continuous Q1 pressure L2 over physical y≤0.9 m support | **7.8166%** |

Independent review caught an earlier comparison that included the unsupported
y∈(0.9,1] strip. Its 6.751% pressure metric is invalid for physical contact
support; the [failed output](d1_16_32_near_rim_unclipped_pressure_metric_20260928.json)
is retained. The bin and reaction comparisons were already restricted to the
correct physical region and did not change.

The [same-mesh comparator source](d1_near_rim_oracle_comparator_20260928.py)
and its output retain exact file/oracle hashes and dimensional bin forces.
Common bins can therefore look settled while the local pressure field still
changes materially. This x co-refinement does not separate structural and
pressure resolution, establish y/rim convergence, qualify a deformable
target, or close D1 pressure-space stability. A larger solve is not justified
by these observations alone; the next investigation must discriminate local
front resolution from pressure/structural coupling using the existing bounded
reference framework.
