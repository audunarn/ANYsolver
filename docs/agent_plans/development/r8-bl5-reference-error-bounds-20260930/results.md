# Reference accuracy and scalar lifting — development results

30 September 2026. Base source `7cb1b16c`; three new root-owned development
scripts accompany this record. No product source changed, no new wheel, no
native beta, formal F03 or aggregate acceptance. Existing wheel `5079b270…`
continues to identify the preceding product only. Foreign F03 script untouched.

## Decision and result

Replace seven sampled reference increments with bounds for every combination
of the fixed 40-action space. Independently derived modal shell tail and beam
equilibrated-flux majorants give total relative Loewner error **0.000624289207**
(0.06243%), below the preset reference-only `1e-3` budget. Saved old mixed-action
total reference error is 0.08218–0.08446%; its shell part is 0.26857–0.26871%.
No candidate value or tolerance was used to calibrate these bounds.

The modal boundary-line oracle passed closed-mode, nonuniform-support, nested
sum and unit controls. Beam bounds passed constant-force and independently
manufactured coupled-arm controls. The full scalar matrices bind all action
cross-products. Their mathematical Loewner identities are independently reviewed;
the saved numerical values use ordinary binary64, not outward-rounded intervals.

The checked product Fortin map transfers continuous beam translation into a
supported shell lifting while retaining cell directors. It preserves all five
physical channels for the fixed flat/constant-arm/root-compatible scope. It
avoids the invalid assumption that beam compliance uniformly dominates shell
compliance. Actual indefinite mechanical KKT checks remain separate.

## Independent finite-family lifting screen

Scalar Q1 bulk norm and exact P0 boundary integrals are assembled independently
of GE constraint matrices. Modal reference upper Gram and variational discrete
lower Gram give `CS²=maxeig(Mupper,Gminus)` for **all** density combinations.

Half-cell:shell-segment ratios `1:8,1:4,1:2,1:1,2:1,4:1,8:1`, shell grids
`16x4,32x8,64x16`, common root and uniform supports use the fixed complete rule
`span=max(1,ceil(2*n_halfcells/n_shell_segments))`. All supports align and cover
at least two shell segments. Starting at 16 keeps every native half-cell count
even and at least two; the scalar family alone is not a GE fixture campaign.

Across 21 cases, `CS²` ranges 1.019005–1.350615 and the derived sufficient product
floor is at least **0.430233437384**. Inverse/eigen residual maxima are
`3.96e-14/1.76e-15`.
The one-shell-interval control deteriorates: `CS²=167.23,667.44,2666.57`,
showing why rank or small weak gaps alone are insufficient.

Do not call this a native stability pass, universal refinement theorem,
mechanical mechanism test or multiplier selection. Its complete constants and
scope may supply prospective criteria after independent implementation review;
raw native beta, deterioration, transfer, locking and physical accuracy are still
required. P0 c1 and c2 are not selected merely by this scalar screen.

## Runs, failures and review

All runs enforce one effective BLAS thread, 600 seconds and 8 GiB process-tree
memory. Raw runners, source copies, outputs and execution records are retained:

| Run | Result | Seconds / peak bytes |
|---|---|---:|
| modal-reference-v1 | Passed controls | 0.472 / 55,799,808 |
| reference-accuracy-v1 | Passed full-action bound | 0.474 / 61,415,424 |
| scalar-lifting-v1 | Failed modal budget on deficient 64-support control | 0.590 / 63,328,256 |
| scalar-lifting-v2 | Passed 21 cases, anchor and deficient controls | 0.593 / 75,907,072 |
| scalar-anchor-correction-v3 | Corrected saved-fixture applicability only | 0.485 / 57,974,784 |

V1 failure remains intact. V2 adds deterministic 4096/8192/16384 modal terms
until the **unchanged** tail budget is met; no physical mesh was refined to erase
failure. A preceding fixture-directory setup failure launched no process and is
recorded in V1 `setup-history.txt`. No performance gain is claimed.

Root applicability check found V2's named saved anchor actually used c2/span4,
unlike the saved 40-action c1/span2 fixture. V2 remains unchanged. Supplemental
V3 recalculates only the actual saved anchor (floor0.076868478), binding V2 bytes
for the unchanged family. Its hypothetical c2 value0.434201821 must not be
assigned to the older fixture. The 21-case family constants are unaffected.

Independent notes: `r8-bl5-reference-bounds-review.md`,
`r8-bl5-beam-dual-error-bound.md`, `r8-bl5-product-fortin-transfer.md`, and
`r8-bl5-finite-domain-floor-review.md`, `r8-bl5-scalar-lifting-review.md`, and
`r8-bl5-deterioration-review.md`. Reviewed finite-family noncollapse criteria
are in the existing trace-norm contract; source/fixture applicability and actual
GE numerical budgets must be checked before native spectra. Reference
scope excludes curved/current frames, nonzero lifts and changed support spaces.
