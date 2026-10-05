# Enriched shell pressure work at saved near-rim pose — development record

This is a fixed-pose development discriminator, not a D1 qualification run. It uses the saved 16×8 Q4 source/two fixed S3 target pose, retains its 153-mode nodal Q1 pressure field, and refines only the source structural x direction to 32×8. The pressure basis is prolonged to the refined source without adding pressure modes. The case ran under the existing 180 s / 1 GB limit.

| Check | Result |
|---|---:|
| Source skin midpoint interpolation error | 2.22e−16 m |
| Pressure support relative L2 error | 1.12e−13 |
| Normalized gap maximum error | 1.40e−17 m |
| Admissible displacement prolongation reconstruction error | 0 |
| Prolongated pressure work relative Frobenius error | 5.05e−10 |
| Restricted fine versus coarse structural energy relative Frobenius error | 3.806% |
| Full supported pressure modes, coarse work rank (prior check) | 144 / 153 |
| Full supported pressure modes, refined normalized compliance minimum eigenvalue | 5.51e−6 |
| Settled active pressure modes, coarse work rank (prior check) | 48 / 48 |
| Settled active finite-reference squared ratio | 0.855 |
| Bounded run | 34.33 s; 234.51 MB peak process-tree RSS |

The pressure work for every prolongated coarse admissible displacement agrees closely between grids. The positive refined compliance detects combinations that are null in the saved coarse test space. The 3.806% structural energy mismatch means the reported generalized ratios are finite-reference comparisons, not nested-energy inf-sup constants. This x-only, fixed-target comparison gives no mesh-uniform pressure-space bound or coupled nonlinear acceptance. It neither removes positive-support pressure modes nor changes the production basis.

An independent read-only review of the new prolongation and result found no implementation defect in the coordinate mapping, pressure-work comparison or metric calculation. It concurred that the nine coarse null combinations are a discrete detection gap relative to this richer shell test space. It cautioned that the 3.8% Frobenius energy discrepancy does not bound error in the weakest energy direction, so the active squared ratio of 0.855 cannot serve as a stability criterion. The cause of structural energy nonnesting remains unresolved.

The first invocation had an unset `PYTHONPATH` and stopped at import in 1.54 s. Its log is retained. The bounded retry completed the mechanics computation and deliberately returned non-success status `development_enriched_shell_energy_non_nested` because the prospective 0.1% nested-energy screen was exceeded. [Raw result](d1_shell_enriched_x2_nested_20260929.json), [resource record](d1_shell_enriched_x2_nested_resource_20260929.json), earlier [pair-guard stop](d1_shell_enriched_x2_guard_20260928.json) and [unenriched-work-check retry](d1_shell_enriched_x2_retry_20260929.json) are retained separately. The 0.1% screen is a development interpretation guard, not an engineering acceptance tolerance.

Source at run: HEAD `102121f778a55bb313c7b8329df03c5df20d346d`, plus uncommitted changes. SHA-256: probe `4F365DE5AF29475064D7C00BD9FA1B937C1C6292714C23E9FF6A67BAD001C370`; changed `linearized_pivot.py` `ADD412638F185F1CAD3AADF5334D852B0263523DA94EC4E37442A42E20158ECE`; contact owner `s3_patch_augmented.py` `63E026F049C0B1778E668E74D4A412FDAFC494260A5B720226173EDC90AA30A8`; saved pose `8293E528837CC2A8A25444AA079944C9F8371F5A5B50280BB6DC91816D19B852`. Runtime identity is in the raw result.

Focused verification of the modified pair-value guard: `tests/test_general_contact_exact_seam_schur.py` passed 4/4 in 20.01 s, including the adversarial weighted-gap perturbation rejection. A related broader test, `test_partial_patch_schur_matches_independent_reequilibration`, failed both on this worktree and when run with the original HEAD `linearized_pivot.py` loaded in memory. Its unchanged-baseline failure is retained in `reports/d1_enriched_related_baseline_test_20260929.txt`; it is not attributed to this guard change or counted as a pass.

Next decision: keep D1 pressure-space stability open. The refined space resolves the saved coarse nulls, but a mesh-family stability claim needs an appropriate shell energy-dual norm, more than one reference resolution, partial-front and two-body checks, and registered pressure/convergence criteria. Do not launch a larger coupled solve from this result alone.
