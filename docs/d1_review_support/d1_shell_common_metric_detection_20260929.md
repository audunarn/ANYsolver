# Same-energy shell pressure detection — development discriminator

At the saved 16×8 near-rim Q4/S3 pose, the previous [enriched-shell probe](d1_enriched_shell_nested_work_20260929.md) found that pressure work prolongates accurately, but the full coarse and fine E4-PL stiffness matrices differ. The [component probe](d1_shell_energy_component_discriminator_20260929.md) traced that difference to the condensed E4-PL core. This check asks whether the *pressure-relevant* active compliance difference comes from that energy change or from added fine-grid displacement motions.

Let `P` inject the coarse admissible displacements into the 32×8 fine space, `W_c,K_c` denote coarse pressure work and stiffness, and `W_f,K_f` denote fine pressure work and stiffness for the **same 153 pressure functions**. The check computes:

- `C_c = W_c K_c^-1 W_c^T`;
- `C_r = (W_f P)(P^T K_f P)^-1(W_f P)^T`, with the coarse motions measured in the fine energy;
- `C_f = W_f K_f^-1 W_f^T`.

It compares `C_r` and `C_f` on the 48 settled active modes, and separately compares `C_c` with the restricted fine energy using exactly `W_c`. Because `C_r` uses `W_f P`, `C_f−C_r` must be positive semidefinite for an admissible full-rank `P`; this is checked numerically. Full supported coarse and restricted matrices are singular, so no full-space generalized ratio is reported.

| Check | Result |
|---|---:|
| Prolongation minimum/maximum singular value ratio | 0.7086 |
| `W_f P` versus `W_c` relative pressure work error | 5.05e−10 |
| Restricted versus coarse-work compliance bridge error | 2.28e−12 relative |
| Smallest scaled eigenvalue of `C_f−C_r` | −3.94e−16, numerical zero |
| Active enrichment ratio range `eig(C_r,C_f)` | 0.854752 to 0.999958 |
| Active metric ratio range, identical `W_c` | 1.000000 to 1.000000, within about 2e−13 |
| Bounded run | 34.81 s; 237.86 MB peak process-tree RSS |

At this pose, the nonnested stiffness difference lies in directions that do not materially change the measured active pressure compliance. The 0.855 minimum is therefore attributable to additional fine structural test motions under one fixed fine energy, within the recorded work/solve errors. This is a finite-reference detection ratio for one active set and x-only enrichment. It does not prove reference saturation, pressure-space stability under mesh refinement, nonlinear coupled response, partial-front convergence or D1 acceptance. The coarse full space still has the nine previously identified null combinations while the enriched work detects them.

Independent read-only review found no defect in the restricted work, energy, rank or projector calculations. It interpreted the 0.85475–0.99996 squared ratio as 85.5% to nearly 100% of fine dual response detected by the restricted trial space over this frozen active subspace (minimum amplitude ratio about 0.92453). It agreed that the metric bridge's near-unity result is pressure-specific at this pose and does not establish matrix equality or mesh-uniform stability.

The [raw result](d1_shell_common_metric_20260929.json) deliberately retains status `development_enriched_shell_energy_non_nested`, inherited from the earlier whole-matrix nesting screen. This status correctly prevents a nested-Galerkin or acceptance interpretation; it is not a failure of the same-metric projector check. [Resource record](d1_shell_common_metric_resource_20260929.json) reports child exit 2 for that declared development status. Source at run: HEAD `6333ec9568cbccf09d4914dbf8642cce23fedd20` plus the modified probe, SHA-256 `6685AE8787C9512EB45FF349B4AE7795372AE03BC01E70994FB2B75DB886C9E0`; raw JSON SHA-256 `3DD25F784B4F6186349820179ACC6DAD9CE2A1D6829948541013FF618BECD5E6`.

**Next decision.** The next informative pressure-space check is reference resolution of this active detection ratio, without a new coupled solve. It needs a separately preflighted second structural reference level and the same physical pose/pressure functions. Register cost and independent method review before running it. Do not change the production basis or declare a universal numerical threshold from this single case.
