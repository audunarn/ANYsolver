# E4-PL energy nonnesting source — development discriminator

**Question.** On the saved 16×8 near-rim Q4/S3 geometry, does the 3.806% mismatch between the coarse admissible structural energy and the energy of the same motions on a 32×8 source grid come from the E4-PL physical core or its PL/hourglass stabilization? This matters before using the refined test space as a common pressure energy norm. The source and target geometry, material, boundary constraints and two prescribed controls are unchanged; no contact solve was run.

The [probe](d1_shell_energy_components.py) assembles each qualified Q4 element's `core`, `pl` and `hourglass` matrices, reduces them through the actual constraints, and prolongates the coarse motions to the fine source nodes. On both meshes, the component sum reconstructs the independently assembled total stiffness within 3.4e−16 relative Frobenius error. The admissible prolongation reconstructs exactly.

| Quantity | Result |
|---|---:|
| Restricted total stiffness difference / coarse total norm | 3.8062% |
| Core difference / coarse total norm | 3.8062% |
| PL stabilization difference / coarse total norm | 1.19e−17 |
| Hourglass difference / coarse total norm | 0 |
| Minimum / maximum fine-to-coarse energy ratio over coarse admissible motions | 1.0000 / 1.4497 |
| Bounded resource use | 3.59 s; 203.23 MB peak process-tree RSS |

The observed mismatch comes entirely from the element-local condensed E4-PL core in this fixture. It cannot be removed by omitting PL/hourglass stabilization from the diagnostic norm. The 3.8% Frobenius number also conceals a much larger difference in some displacement directions: the maximum generalized energy ratio is 1.45. This is a comparison of two discrete formulations on their respective meshes, not a failure of either structural formulation or a contact acceptance result.

Independent read-only review found no component-assembly or prolongation defect. It confirmed that the core is the formulation's condensed stationary bilinear form and that its mesh difference is not itself a continuum accuracy verdict. It also confirmed that the restricted fine energy is no lower than the coarse energy to numerical precision for this fixture, while the active pressure ratio remains unsuitable as a nested inf-sup claim.

The first attempt stopped before component assembly because the probe applied a dense Frobenius norm to a sparse matrix; its failure log is retained at `reports/d1_shell_energy_components_log_dev_20260929.txt`. The corrected bounded run is [raw JSON](d1_shell_energy_components_20260929.json) with [resource record](d1_shell_energy_components_resource_20260929.json). Run source: HEAD `6333ec9568cbccf09d4914dbf8642cce23fedd20` plus the uncommitted probe. Probe SHA-256 `5204737A28EDE3EC3FAD7B41B3BE40144BB7E939379B591A9FADCCB923F3AE5A`; E4-PL source SHA-256 `8AA0A6845804857C15D3CA30D883E1960386C00044D69A892F9BF35BB0110F33`; raw result SHA-256 `72342AD90164C5CC470C6F41583C9A7351EBC4309CA9EECF13B988143EC9D01D`.

**Decision.** Keep the actual total E4-PL energy for each mesh's pressure test; do not replace it with a stabilization-stripped norm. A ratio between coarse and refined pressure responses under different discrete energy metrics is a finite-reference comparison. The next pressure-space criterion must state its pressure norm and compare multiple mesh levels or independently demonstrate reference convergence. The present test does not authorize a larger coupled solve or pressure-basis change.
