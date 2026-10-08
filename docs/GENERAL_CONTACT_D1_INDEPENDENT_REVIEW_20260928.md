# General contact D1: independent review

**Date:** 28 September 2026. **Reviewed:** `codex/general-contact-core` at `be5ea482`. The brief commit `9087a0ba` only adds the brief. Sources read: the brief, the capability ledger, the D1 gap map, the living note, the archive and history (targeted), the five named reviews, the continuum-obstacle record, the bin comparator, the profiles and the relevant source modules (`q4_s3_overlap_derivatives`, `s3_patch_augmented`, `s3_patch_mortar_energy`, `static_path`, `supported_schur`, `linearized_pivot`, `augmentation`).
**Nature:** Level-A development review. I executed no ANYsolver solver and replayed no frozen or consumed case. I changed no tolerance and claim no acceptance. Every number I computed comes from new code in a separate sandbox, listed in §8.

---

## 1. Bottom line

1. **I found no evidence of a mortar geometry or pressure-transfer defect.** I wrote an independent implementation that uses no ANYsolver code: scalar Q1 FE with clipped Q1 mortar pressure, plus a separate cell-centred FV reference. It reproduces your source-only numbers exactly: FV 0.103804402 N, and bin L2 errors of 36.34 / 25.29 / 22.41 / 22.23 / 18.01 %, with 80.4 % of the error in the two rim rows. The same oracle also reproduces your **coupled** production results to nine digits: 8-Q4 gives 0.103479815 N, and the accepted 24-Q4 full-load force is 0.103878837 N. In the one-row regime, the coupled solver converges to the independent discrete KKT point.
2. **The 18 % rim discrepancy comes mostly from the observable, not from the pressure field.** The exact reaction has a *line load* along the obstacle edge y = 0.9. In the FV reference the last supported cell row carries 0.0103 N, which is 10 % of the total reaction. Your 16×16 bins cut the support 0.025 m below that line, which is less than one element width for every mesh tested. On bins that respect the support boundary, the same saved fields drop from 18.0 % to **2.35 % (16×9) and 0.84 % (8×9)** at 32×32, and to 0.47 % / 0.10 % at 64×64. The FV reference self-converges to 0.09 %.
3. **The stall is caused by cost and algorithm structure, not by mechanics.**
   - The Q4/S3 pair kernel costs 0.25–0.42 s per pair. It evaluates about 14,000 scalar Python `Jet2` products per pair, and 73 % of the integrand jet products are Hessians that are then discarded.
   - The augmentation loop contributes almost nothing to convergence. At k = 10⁴ Pa/m the Uzawa map's spectral radius is 0.9992 at 8×1 and 0.99998 at 32×40, so all real convergence comes from the heuristic supported-Schur proposals. The convergence tests are max-norm **Pa** tests on nodal pressures, and rim and sliver nodal pressures grow like 1/h, so these tests get harder as the mesh refines.
4. **A 5× kernel speed-up needs no change in mechanics.** A batched-jet prototype of the production kernel runs at 0.083 s/pair versus 0.416 s. It has 3.9×10⁻¹⁶ relative parity, identical branch signatures and identical integration-triangle counts. A compiled kernel plus a monolithic semismooth Newton should bring a 16×16 two-dimensional coupled solve comfortably inside 180 s. On the same discrete problem, SSN needs 5–22 iterations from a cold start, with no safeguards.
5. **The process is spending most of its throughput on evidence, not on the principal uncertainty.** Between `c55c3860` and `be5ea482` (about 13.5 hours) there were 82 commits. Only 12 touched `src/` (+1.2 k lines). About 155 k lines went to docs, reports, scripts and tests. There are 63 profile identifiers in `general_contact`, 17 in `static_path.py` alone. The adopted policy already forbids most of this pattern; the practice has not caught up.

**Shortest sound route to a first D1 delivery:** redefine the partial-width observable (§3.1), speed up the kernel (§5.1), replace the augmentation and Schur machinery with a monolithic SSN (§5.2), then verify the 2D coupled solver against the discrete oracle on the same mesh. Do that before any further large coupled solve.

---

## 2. Independent checks performed

| Check | Method | Result |
|---|---|---|
| Discrete oracle | New scalar Q1 FE (D = 1602.5641 N/m, q = 0.3 Pa, g = 40 µm) with clipped Q1 mortar pressure on the same mesh. Dual LCP solved by primal-dual active set with a KKT certificate. New FV (cell-centred, active set). | Reproduces all saved source-only reactions and bin errors to the printed digits. Reproduces coupled 8×1 (0.103479815 N) and accepted 24×1 (0.103878837 N). |
| Observable sensitivity | Same fields, different binning: the original 16×16, support-aligned 16×9 and 8×9 (y edges at 0.1 k up to 0.9), and rim-aligned versus unaligned meshes. | See table A. |
| Kernel cost | Verified byte-identical copy (md5 `53d3370f…`) of `q4_s3_overlap_derivatives.py` at `be5ea482`, on a D1-like rim pair with the D1 script tolerances. Batched-jet prototype of the same algorithm. | 0.416 → 0.083 s/pair. Parity 3.9e-16 over 12 perturbed poses. Same branch/triangle signature. |
| Augmentation spectrum | Eigenvalues of k·∂ĝ/∂λ on the solution's active set, k = 10⁴ Pa/m (the D1 script value). | Table B. |
| Monolithic SSN | Primal-dual active-set Newton on (u, λ), cold start, weighted gap. | 5–34 iterations, same reactions as the LCP oracle. |

### Table A: bin-force L2 against FV256×320, source-only fields

| Mesh | Rim on node | 16×16 (current) | Share in rim rows | 16×9 support-aligned | 8×9 support-aligned |
|---|---|---:|---:|---:|---:|
| 4×8 | no | 36.34 % | 29 % | 26.9 % | 24.4 % |
| 16×8 | no | 25.29 % | 75 % | 3.86 % | 1.54 % |
| 16×16 | no | 22.41 % | 78 % | 4.04 % | 2.04 % |
| 32×16 | no | 22.23 % | 80 % | 3.14 % | 2.01 % |
| 32×32 | no | 18.01 % | 80.4 % | 2.35 % | 0.84 % |
| 16×20 | yes | 4.95 % | 46 % | 3.50 % | 1.08 % |
| 32×40 | yes | 11.75 % | 75 % | 2.19 % | 0.58 % |
| 64×64 | no | 4.57 % | 87 % | 0.47 % | 0.10 % |
| 64×80 | yes | 2.73 % | 79 % | 0.45 % | 0.03 % |

FV128×160 against FV256×320 is 0.103 % (16×16) and 0.090 % (16×9). With the current bins the metric is **non-monotone**: 32×20 gives 4.2 % and 32×40 gives 11.8 %. It measures where mesh nodes fall relative to the bin edge at 0.875, not pressure convergence. On support-aligned bins it converges cleanly.

---

## 3. Answers to the three review questions

### 3.1 Q1: Is conservative 2D bin force the right observable, and with what reference and threshold?

Bin forces plus independent gap plus integrated wrench is the right *family* of observable. The multiplier is a measure (in H^{-1/2}, or a line Dirac here), so only tested integrals converge. Pointwise Pa values do not. The current bin *geometry* is unsuitable. I recommend registering it prospectively as follows.

- **Bins that respect the physical support.** The obstacle edge must be a bin edge. Near the rim, bins must be at least 2–3 element widths wide. For D1: 8×9 or 16×9 bins on x∈[0,1], y∈[0,0.9], plus an empty [0.9,1] row as an integrity check.
- **A separate rim-band force.** Report the force in the last support-aligned bin row, integrated over x, as its own observable. It contains the line load of about q × 0.1 m × the contact length.
- **L1 alongside L2.** L1 is the natural total-variation distance for measures.
- **A two-tier reference:**
  1. *Code verification.* The coupled 2D candidate must match an independent discrete oracle on the **identical mesh and pressure space**: bin forces, nodal forces λᵢSᵢ and the active set, to ≤10⁻⁶ relative. The two discrete problems are the same strictly convex QP in the linear regime; von Kármán corrections are of order (w′)² ≈ 10⁻⁹. This is where a coupled defect would show, independent of discretization error.
  2. *Solution verification.* The oracle, not the expensive coupled solver, establishes the chosen mesh's discretization error against FV256×320. That reference self-converges to 0.1 %.
- **A defensible threshold.** ≤2 % L2 (and L1) on 8×9 support-aligned bins and ≤2 % on the rim-band force, at the declared mesh. This is consistent with your 2 % representative-response gate. It sits 20× above the reference's own uncertainty. The oracle predicts 16×16 at 2.0 % and 32×32 at 0.8 %.

  Selecting the mesh and threshold from an independent oracle is solution-verification planning, not retrofitting to the candidate. The coupled candidate's result remains unseen. Disclose that source-only runs informed the choice, as §5 of your policy requires.

### 3.2 Q2: Defect, expected discretization behaviour, or FV mismatch? One discriminating bounded check

**Diagnosis: expected discretization behaviour of a physical line load, made worse by the choice of bins.** It is not a mortar geometry or transfer error, and not an FV idealization mismatch.

- The rotation-fixed guided shell is a shear membrane. Where it is flat on the obstacle, −DΔw = 0, so **p = q = 0.3 Pa exactly**, which the oracle reproduces. The 0.1 m overhang is carried by a kink in w at y = 0.9, which is a line load.
- A Q1 displacement can kink only at a node. The Q1 multiplier therefore represents the line load as a nodal spike: 3.5 Pa at 32×40 and 6.2 Pa at 64×80, growing like 1/h. It also produces a zero-pressure undershoot at the neighbouring nodes, and a larger spike on a cut node with a small clipped support (14.2 Pa at 64×64). That undershoot is the "row 13 deficit / row 14 excess" dipole in your 32×32 comparison: −0.0036 N / +0.0033 N.
- The FV discrete support is exactly [0, 0.9] (320 rows, cell centres below 0.9). Your source-only structure equals the scalar operator to 6×10⁻¹⁶. There is no idealization mismatch.

**Discriminating check.** It costs seconds and needs no new solve. Re-evaluate the *saved* 16×16, 32×16 and 32×32 source-only fields and the saved FV bins on support-aligned 16×9 and 8×9 bins. Your `integrate_q1_bins` needs arbitrary y edges on [0, 0.9]; the FV side is an exact 32-cell partition.

- If the discrepancy collapses from 18–22 % to about 2–4 % (my result), then the observable, not the transfer, was responsible. Close the question.
- If it does not collapse on your fields, your production-side source path differs from the oracle, and the per-node difference against `d1_rim_oracle.py` will localize it.

**Follow-up code-verification check before any large 2D run.** Run the coupled 4×8, or 8×8, fixed-target case and compare it node by node with the oracle on the same mesh. A match to ≤10⁻⁶ clears the coupled contact assembly in 2D. A mismatch is a concrete defect with a location. At the current kernel speed this costs roughly 400–600 s; after §5.1 it is under a minute.

### 3.3 Q3: What needs fresh evidence, and does the first 2D candidate fit 180 s / 1 GB?

**Source impact since the accepted identities.** From `c55c3860`/`1cde0b43` to `be5ea482` there are 13 contact files and +1182/−74 lines.

| Area | Change | Impact |
|---|---|---|
| Pair kernel (`q4_s3_overlap_derivatives`) | Third-Newton early exit (≤10⁻¹² residual gate) | Roundoff-level. Reuse the local Jet2 and fixed-pose pressure-space evidence after a parity replay of the fixed-pose probe (≤100 s now, seconds after §5.1). |
| Projected law (`s3_patch_augmented`) | Prepared pair-state reuse on the default route. Macro/selected basis is opt-in. | Parity shown on 8-Q4 (pressure 3e-14, displacement 3e-20 m). Reusable by impact analysis for the one-row claims. |
| Solution control (`static_path`, `supported_schur`, `augmentation`) | Schur backtrack, secant retry, relinearization and trial restoration (+411 lines) | **Needs fresh evidence** wherever the D1 candidate enables them. They manipulate trial and rollback state, which is exactly what the restart/rollback claim covers. |
| `transient`, `contact_search`, `pressure_basis` | New or opt-in | Not on the D1 static route unless selected. |

**Needs fresh evidence for the D1 candidate in any case:**

- The complete both-body mapped force and tangent on the 2D mesh with the deformable S3 target. The 98-row check was a subset at an older source.
- The four-phase path with the exact production solution algorithm.
- Rejected-trial rollback and cutback, and active/open/active split restart.
- The installed wheel of the final source.

If the solution algorithm is replaced by SSN (§5.2), all state and restart evidence must be regenerated. However, the converged discrete states are *the same KKT points*, so the accepted 24-Q4 cycle becomes a **regression oracle**: all 12 rows must reproduce to ~10⁻⁹. That is a strong reuse argument and a cheap test.

**Budget.** With the current kernel and algorithm, **no** transversely discriminating 2D candidate fits 180 s.
- The 4×8 case costs 12.7 s per residual/tangent. The one-row runs used about 31 derivative evaluations per two-step solve (8-Q4 profile), so 4×8 would take roughly 400 s or more before Schur and float-geometry costs.
- Memory is not binding: 275–310 MB peak in the current runs, and a dense active compliance of 432 modes is trivial.

Projected costs:

| Stage | 4×8 (42 pairs) | 16×16 (~300 pairs) |
|---|---|---|
| Today | ~400–600 s | ~3,000 s+ |
| Batched kernel only (§5.1a, ~5×) | ~100 s | ~800 s |
| Batched kernel + SSN (~10 evaluations) | ~30 s | ~200 s |
| Compiled kernel (≤10 ms/pair) + SSN | <10 s | ~30–60 s |

These are estimates from measured per-pair costs and iteration counts. The 2D candidate fits the existing 180 s / 1 GB limits without weakening any gate once §5.1 and §5.2 are in place.

---

## 4. Why development is stalling: root causes

### Technical

- **T1. The kernel is too slow to explore 2D.** One pair evaluation is 70 quadrature points: 2 root triangles × (coarse + 4 children) × 7 points. Each point runs a jet Newton inverse and 44 jet integrand products; 32 of those are Hessians of the Nᵢ·Nⱼ mass entries, which `_evaluate` never returns. The 8-Q4 solve (132 DOFs) takes 170 s. Structural factorization accounts for 0.004 s of that; the rest is contact.
- **T2. The augmented Lagrangian is outer-loop Uzawa with a fixed penalty.** At k = 10⁴ Pa/m, k·μ_min is 8×10⁻⁴ at 8×1 and 2×10⁻⁵ at 32×40, so the fixed-point rate is between 0.9992 and 0.99998 and degrades like h². Convergence therefore depends entirely on the supported-Schur proposals. Those are a dual Newton step computed outside the Newton loop, protected by pressure caps (10/250 Pa), step caps (5/200 Pa), attempt counters, a 19-point backtrack grid, secant backtracks and re-equilibration. Each safeguard is reasonable locally; together they are a hand-built, fragile version of what a semismooth Newton does in one KKT solve.
- **T3. The stopping tests use mesh-dependent units.** `max|Δλ|` in Pa (1e-5 Pa in the D1 press script, 0.2 Pa in the 64-Q4 case) is dominated by rim and cut nodes whose nodal "pressure" is force over a small support and grows like 1/h. The rejected 64-Q4 step (1100.58 Pa against 0.2 Pa, gap passed, equilibrium 1.3e-8) fits this pattern. Because the trace was not retained, I cannot confirm how much *force* that 1100 Pa represents; that remains a hypothesis.
- **T4. The observable does not match the physics.** See §3.1–3.2. The 2D decision has been waiting on a metric that cannot converge smoothly on the meshes tested.
- **T5. Clipping ties are rejected.** A Q4 vertex on a target edge raises `UnsupportedQ4S3Branch`. This blocks rim-aligned and conforming meshes, which are common in practice. The integrals are continuous across the tie; only the derivative is one-sided, and semismooth Newton accepts any element of the generalized Jacobian. Fix this with a deterministic half-open convention plus a one-sided derivative test.
- **T6. There is no search on the production path.** `pair_laws` is the full source × target Cartesian product (`s3_patch_mortar_energy.py:164`). That is fine for 2 target faces, but quadratic for the deformable-target D1 claim.

### Process

- **P1. The ratio of evidence to code is inverted.** 82 commits and ~155 k non-source lines against ~1.2 k source lines in one overnight window. Examples: a SHA-256 is required as a CLI argument to a *development* comparator; NaN guards were added to saved development JSON; an 1140 s formal restart run failed on a registration schema string; an installed-run duration was bounded "conditional on stable host clocks". Policy §3 and §6 already say not to do this.
- **P2. The code grows by adding profiles instead of replacing them.** There are 63 profile identifiers, 17 path profiles, and about 75 ledger rows marked "implemented, locally tested; C1 open". Every improvement becomes a new opt-in profile with its own admission, identity and restart contract, and nothing is retired. Complexity grows, and each new question must be asked across more variants.
- **P3. The feedback loop is too slow and too narrow.** The combination of a slow kernel and a 180 s cap means every informative experiment is one-row or tiny, so the 2D behaviour has never been seen. Formal runs take 900–1140 s and are one-use, so mistakes are expensive and caution compounds.
- **P4. Scope diffuses from the critical path.** On the night of 27–28 September, commits added transient loads, macro and selected pressure bases, and search adapters, alongside the D1 critical path.
- **P5. Reviews are aimed at bookkeeping.** The independent reviews verified hashes, indices, signs and NaN handling thoroughly, but none questioned the observable or the solution algorithm, which are the two things blocking D1.

---

## 5. Improvement options, new formulations and acceleration (ranked)

### 5.1 Kernel acceleration: no change in mechanics, parity-gated

| Step | What | Expected | Verification |
|---|---|---|---|
| a | Batch jets over the 7 points and over coarse + 4 children; accumulate mass entries as floats only. | **5.0× measured** (prototype supplied) | Parity ≤1e-13 against the current kernel on a pose corpus recorded from existing D1 runs; identical branch signature and triangle count. |
| b | Closed-form affine inverse map, with IFT/Newton only on warped poses. Float-only coarse/child *value* checks where the derivative tolerances do not require jets. | Another 1.5–2× | Same parity corpus. |
| c | Compile the kernel with fixed-size forward jets in numba (already the `accelerated` extra), or C++. Keep the Python kernel as the oracle. | Target ≤10 ms/pair (arithmetic is about 15–20 MFLOP per pair) | Same corpus and fail-closed fallback. |
| d | Also profile the float pair geometry (16.6 s) and the 62.6 s unwrapped time in the 8-Q4 profile. | Likely 2–5× on the remainder | Timing plus unchanged outputs. |

### 5.2 Solution algorithm: replace, do not add

**Monolithic semismooth Newton** (Alart–Curnier 1991; Hüeber–Wohlmuth 2005; Popp et al. 2009/2010) on (u, λ):

- NCP: Cᵢ = zᵢ − max(0, zᵢ − c·ĝᵢ), with zᵢ = λᵢSᵢ (nodal force) or scaled λ. Here c is purely algorithmic and does not change the solution.
- One KKT solve per iteration. Active-set changes and geometric nonlinearity are resolved together.
- Convergence is measured in **force units**, for example Σ|Cᵢ| / applied load ≤ 10⁻⁸, plus the existing normalized equilibrium and gap gates. This is stricter in physical terms and does not depend on the mesh.

This reuses what already exists: the Jet2 gap gradients (B), the contact Hessian, the general LU (`MatrixClass.GENERAL`), and the checkpoint machinery, which would store λ and the active set. It removes `augmentation.py`, `supported_schur.py`, most of `linearized_pivot.py` and about 400 lines of `static_path` control flow from the D1 route.

The oracle shows 5–22 iterations from a cold start on the D1 meshes, with fewer expected under load stepping and warm starts. Compare the 72 energy evaluations, 8 augmentations and 4 Schur proposals of today's 8-Q4 two-step run.

The old route should stay as an opt-in legacy route until SSN reproduces the accepted 8-Q4 and 24-Q4 results, then be retired. Replacing the stopping test is a new prospective decision for a new candidate. The 64-Q4 failure remains failed under its original criterion.

### 5.3 Pressure space and observables

- **Support-aligned bins, a rim-band force and two-tier verification** (§3.1). This carries the least risk and has the largest effect on the D1 decision.
- **Deterministic tie handling** (T5). This enables rim-aligned and conforming meshes.
- **Optional, medium term: dual (biorthogonal) Q1 multipliers.** They allow local condensation of λ, so SSN becomes a displacement-only system with a nodal active set. For the slave-extends-beyond-master rim, apply a boundary treatment in the style of Cichosz–Bischoff (2011). This is not required for D1.
- **Not recommended now:** more knot-selection or macro-pressure work on the 1D fixture. The living note already reached this conclusion.

### 5.4 Search

Before the deformable-target part of D1, route pair creation through the existing broad-phase (`patch_broadphase` or the `contact_search` adapter) so that pairs are O(N log N), not a Cartesian product.

### 5.5 Process changes, within the adopted policy

1. **Replace rather than add.** An explicit owner decision should name one D1 production route, park everything else, and set a hard cap of three active development profiles in `general_contact`.
2. **Turn formal runs into regression tests.** Once the kernel is fast, the accepted cases (24-Q4 cycle, restart, fixed-pose pressure) and the discrete-oracle comparisons become CI tests that run in minutes. Impact analysis then means running the regression, not writing an argument.
3. **Set an evidence budget.** Keep the living note to two pages or less and update it only at decisions. Freeze `GENERAL_CONTACT_HISTORY.md` as an archive. Record development comparators in commits, with no hashes or registrations (policy §3). Produce one formal collection per candidate.
4. **Aim independent review at the principal uncertainty.** One review per decision point, asking whether the observable and the algorithm are right and whether parity holds. Stop reviews of each helper.
5. **Track three numbers weekly:** seconds per 16×16 coupled fixed-target solve, coupled-versus-oracle discrepancy, and open gap-map rows.

---

## 6. Proposed sequence (about 2–3 weeks), with exit criteria

| # | Action | Exit criterion |
|---|---|---|
| 1 | Re-bin the saved source-only fields on support-aligned bins (§3.2). Register the D1 partial-width observable, the two-tier reference and the thresholds prospectively. | Collapse of the rim discrepancy confirmed on your fields; registration committed. |
| 2 | Kernel step a (and b). | Parity ≤1e-13 on the pose corpus; ≥5× on the 4×8 profile. |
| 3 | Coupled 4×8 or 8×8 fixed-target run on the current algorithm, compared node by node with the oracle. | ≤1e-6 relative match, or a located defect. |
| 4 | SSN D1 route with force-unit stopping tests and tie handling. | Reproduces the accepted 8/24-Q4 one-row results to ~1e-9 and the oracle in 2D to ≤1e-6. |
| 5 | Kernel step c (compiled). | ≤10 ms/pair; 16×16 fixed-target two-step solve under 60 s. |
| 6 | D1a candidate: 16×16 (or 16×20 with ties) fixed rigid target, 2D partial contact, four-phase path, restart/rollback, installed wheel. One formal collection, then independent assessment. | Registered gates pass. |
| 7 | D1b: deformable S3 target with broad-phase search, as a separate claim. | Its own registration. |

Splitting D1 into D1a (fixed rigid target) and D1b (deformable target plus search) gives a usable first delivery without waiting on the hardest remaining item.

---

## 7. Decisions needed from the owner

1. Authorise **replacing** the augmentation and supported-Schur route with monolithic SSN for D1 production, with the old route kept only until parity is shown.
2. Adopt the **support-aligned bin, rim-band and two-tier** observable for the partial-width claim, with a prospectively registered threshold.
3. Approve a **compiled kernel path**, using the numba optional extra or C++, with the Python kernel kept as oracle.
4. Approve the **D1a/D1b split** and the cap on active profiles.

---

## 8. Limits of this review, and supplied material

- I did not run the ANYsolver coupled solver. The coupled 2D statements are predictions to be settled by the code-verification check (§3.2, step 3). The Uzawa spectrum is computed on the linearized source-only problem with the D1 penalty; production details, such as supported-mode handling, may shift the constants but not the h-dependence.
- The 64-Q4 criterion-scaling explanation is a hypothesis, because the augmentation trace was not retained.
- Kernel timings were measured in a Linux sandbox, where the production kernel took 0.36–0.42 s/pair; on your host it takes about 0.25 s/pair. Ratios, not absolute times, carry over.

**Supplied in `d1_review_support/`:**

- `d1_rim_oracle.py` is the independent scalar oracle (Q1 FE with clipped Q1 mortar, and FV) together with the review tables. It takes about 90 s and has no ANYsolver dependency. Its output is saved as `d1_rim_oracle_output.txt`.
- `q4_s3_batched_jet_prototype.py` is a review prototype, derived from the `be5ea482` kernel with two changes documented in its header.
- `bench_q4_s3_kernel.py` checks parity and timing against the production kernel. Run it from a `be5ea482` checkout. Its output is saved as `bench_q4_s3_kernel_output.txt`.
