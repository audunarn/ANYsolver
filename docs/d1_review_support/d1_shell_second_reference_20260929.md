# Second structural reference for saved shell pressure work — development

**Question.** Does the settled active pressure detection ratio at the saved 16×8 near-rim Q4/S3 pose saturate when its structural test space is enriched further in x? The first [same-energy check](d1_shell_common_metric_detection_20260929.md) used a 32×8 source structural reference and found a minimum squared response ratio of 0.854752. This run kept the same 153 physical Q1 pressure functions, saved 16×8 pose, fixed two-S3 target and constraints, but used a 64×8 source structural reference. It did not solve a new contact equilibrium.

The development case builder admits 64 columns only with `offline_structural_reference_64=True`; ordinary coupled case admission is unchanged. The probe interpolated source positions and admissible motions with quarter-point weights, then prolonged the unchanged pressure basis onto the fine nodes.

| Check | 32×8 reference | 64×8 reference |
|---|---:|---:|
| Source skin interpolation error | 2.22e−16 m | 2.22e−16 m |
| Pressure support relative L2 error | 1.12e−13 | 1.79e−13 |
| Prolongated pressure work relative error | 5.05e−10 | 7.67e−10 |
| Active same-energy squared response minimum | **0.854752** | **0.794360** |
| Active same-energy squared response maximum | 0.999958 | 0.999940 |
| Active metric bridge range | unity within ~2e−13 | unity within ~2e−13 |
| Minimum scaled eigenvalue of fine minus restricted compliance | −3.94e−16 | 2.71e−10 |
| Process-tree peak / elapsed | 237.86 MB / 34.81 s | 344.58 MB / 56.83 s |

The active minimum fell by 0.06039 in squared response (about 7.1% relative to the x2 value). The x2 reference is therefore not saturated for this saved active subspace. The positive-semidefinite projector relation and pressure-work agreement support that interpretation. The full coarse pressure work retains its nine null combinations, while both enriched references detect them. The energy metric bridge remains near unity for the active pressure response, even though the whole restricted E4-PL stiffness differs more strongly on the 64×8 grid.

Independent read-only review found no interpolation, constraint or pressure-basis defect. It confirmed that the x4 change is a real reference-level change in this fixed-pose calculation. Because the E4-PL core is non-Galerkin and no direct 32×8-to-64×8 common-energy comparison was made, this is not a monotonic continuum-convergence result or a mesh-uniform inf-sup trend. The near-unity bridges concern only the saved coarse active pressure work.

The [raw result](d1_shell_common_metric_x4_20260929.json) retains `development_enriched_shell_energy_non_nested` and exit 2, because the whole-matrix nested-energy screen is still unmet; it is not a projector failure. The [resource record](d1_shell_common_metric_x4_resource_20260929.json) shows the existing 180 s / 1 GB cap was respected. Source at run: HEAD `6333ec9568cbccf09d4914dbf8642cce23fedd20` plus uncommitted development probe/builder changes. SHA-256: probe `2CED0C457662D7804FAB5E168FB5F030785D7B99F37FCFEAACD92765412F530D`; builder `2D81844210C9FB0E35BBB35A4A21633CED6696A298FB41467F82182CF816D005`; raw result `E752C0E16EF5A9D73EAE62C2F58C28C1F7FD5536427934C39B3892DE5068F6AC`.

**Decision.** Do not call the active space reference-converged or infer mesh-uniform stability from the 32×8 result. Stop this x-only reference branch under the decision-oriented development budget; another refinement would require a new discrimination and resource rationale. The D1 pressure-space qualification still needs the pressure/front criterion and reference convergence over structural, pressure and integration refinements, including deformable-target work. No production pressure basis or acceptance gate changes here.
