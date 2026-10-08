# Supporting incidence-error review V1

Scope: read-only review of new incidence_bound and stationary_incidence_error in C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001/scripts/r8_bl5_sparse_envelope_kernel_dev.py. No numerical job, test, Git operation or worker was run by this reviewer. Supporting OpenAI input only; no scientific acceptance, qualification or F03 authority.

Verdict: no correctness blocker identified in these functions under the unchanged primitive arithmetic assumptions and enclosing caller's existing actual-inventory/locality validation. They are not yet wired into assess (line326 still uses bound.stationary_error). Thus this source change does not resolve or reclassify the preserved ns16_b8 HOLD.

## Exact target and local enclosure

At240–242, the exact-real saved Kxx scaled on both sides by the stored positive physical scale is enclosed by scaled_data; the same rounded base starts the reconstruction. Lines245–256 retain the old local inverse/lift/update enclosure verbatim in substance. In particular, the true scaled P=Kpx diag(scale) is enclosed before bounding D lift+P; the inverse residual proof bounds ||D^-1||2; the resulting lift-error Frobenius bound multiplied by the true scaled Kxp Frobenius majorant covers the omitted exact local update. The interval dot product covers the true Kxp times the stored lift versus the rounded update. Different Kpx and Kxp are both retained, so nonsymmetry is not silently removed.

The neighbour union at246–247 is formed from both saved coupling sides before scaling. Therefore each exact local-update error is confined to I_j x I_j even when rounded update entries cancel or become zero. Per-member support, lift error and local Frobenius delta are retained at257/261–262. Artificial outward boxes around an exact zero inside the selected support are conservative; zero coordinates outside the union remain exactly excluded from the true operator.

## Incidence theorem and rounding

For local ||E_j||2 <= delta_j with E_j supported on I_j x I_j,

|u.T sum(E_j) v| <= sum_j delta_j ||u_Ij|| ||v_Ij|| <= sqrt(sum_j delta_j ||u_Ij||² sum_j delta_j ||v_Ij||²) <= max_i sum_{j:i in I_j} delta_j ||u|| ||v||.

No symmetry, sign or full-rank assumption is needed. The existing local Frobenius deltas are valid induced2 majorants. incidence_bound:220–230 validates finite nonnegative deltas, unique ordered integer supports, actual domain and local 24 cap. Positive per-coordinate additions are rounded outward. Counting complete original supports preserves errors even if signed local operators cancel; it does not use final nnz. Empty support contributes no operator. Outward rounding of zero deltas may slightly enlarge a weight, which is conservative.

The returned total at263–273 is an induced2 upper bound. It adds the unchanged base Frobenius bound, local incidence bound, whole-block-count assembly Frobenius bound and reconstruction-discrepancy Frobenius bound. Frobenius bounds dominate induced2, so these mixed majorants can be added. Existing conservative gamma(2*(len(blocks)+1)) is retained; no sharper assumption about native CSR addition has been introduced. The independent signed reconstruction and positive absolute accumulator remain intact. The original sum of local Frobenius bounds is also recorded for comparison, without replacing it by a cancellation-dependent number.

## Integration conditions and controls

When wiring, name the total stationary_operator_error_induced2_upper, rather than retaining stationary_operator_error_fro_upper. The subsequent ||Z_true||2² multiplication is valid for this induced2 bound. Save the returned identity/base/local/assembly/difference record and actual per-member support/delta details, plus incidence_weights/incidence_counts as NPZ arrays, before proof predicates. Keep the original output and HOLD files and the fixed shift 2*newly-derived-epsilon rule; do not choose a bound after inspecting the pass verdict.

The tests at132–146 cover overlapping nonsymmetric errors, disjoint supports and malformed supports/deltas. The cancellation comment is stronger than its implementation: the matrix e at138 still includes the first contribution and does not explicitly form an aggregate with the third cancelling it. A useful correction is to construct all three embedded local matrices, sum them with the cancelling pair, and assert the unchanged supports/counts/deltas. This is a control gap, not a theorem defect, and no tighter backend addition claim depends on it.

Test149–163 uses exact Fraction force-method work for an actual nonsymmetric local Schur and checks retained support/assembly count. It currently uses unit scale and one member; it does not numerically exercise nontrivial rounded scaling or actual overlapping member updates. The enclosure operations are unchanged from the previously reviewed primitive. If broader integration controls are added, nonuniform non-power-of-two scales and overlapping asymmetric neighbours are the relevant discriminators. Quadratic work controls alone do not detect a pure skew operator error; a bilinear or induced-norm control supplies that distinction.

## Evidence and hashes

Read test-v4/stdout.log: 35 passed in 0.61s. Supervised execution terminal exit 0, elapsed 1.0764845s, sampled peak 87,982,080 bytes, sampled numeric-or-unresolved maximum 5 under the unchanged limit 8. Do not describe this suite as observed one numerical thread. No new saved-operator incidence assessment has been reviewed.

Caller source SHA256:dd1df8e1351e28582ad0b5526e025d32a35f2bf8ca85c1e0ed096716f2ad016f. Caller tests:355eefa5d7f9656a4372c6c28acc3784d7f5467542e44dac8017c05e0af6f7a3. Saved primitive unchanged 064a0d8d36dca6db916d9a8eb2563620cf8c72cb82920bd4dc0c7182b6d1c138; interval primitive unchanged 47adfa44533b08c33aac8879d231b63d1b900ac2b50cf7d9e3427b52428d0199. Current quantitative lower-bound metadata at344 explicitly identifies the dimensionless scaled physical-coordinate target.