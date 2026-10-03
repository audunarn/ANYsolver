# Saved-kernel source review v2

Supporting OpenAI Read delta review, repository C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001. No numerical jobs/tests, source edits, Git operations or workers were launched by this reviewer. This separate report preserves v1 and its HOLD evidence.

No false-positive mathematical defect identified in the reviewed congruence or directed-Decimal implementation. Both v3 saved assessments now certify strictly positive quadratic work on their actual constrained saved-K Schur kernels, in the originally declared scaled physical Euclidean norm. This remains development evidence, not scientific qualification, full-K SPD/inertia, a measured minimum eigenvalue, or validation of larger envelope cases.

Reviewed SHA256:
- scripts/r8_bl5_sparse_kernel_saved_dev.py: 0fd2572ffe4fc8ba585b799f9c8f559c401eafa8674189467e8a03287c0d3c51
- scripts/r8_bl5_sparse_kernel_interval_dev.py: 47adfa44533b08c33aac8879d231b63d1b900ac2b50cf7d9e3427b52428d0199
- tests/test_r8_bl5_sparse_kernel_saved_dev.py: b7aaba09f74ebf13bc90b42710926cb37ba5f2050c4059f73cc026aaeb677104
- tests/test_r8_bl5_sparse_kernel_interval_dev.py: 76242eee9e0f9de5c61112afe75ac02cacd3e0f8dc070f6f6be6f04526465520

## Delta correctness

Saved source328–341 treats the finite strictly positive binary64 T as exact chosen column coordinates. The provisional rounded diagonal only chooses T; it is not used as a positivity proof. Actual target W*=Z* T retains the same complete kernel because T is invertible. scaled_data supplies elementary multiplication boxes, and line339 bounds ||What-W*|| by max(T)*eZ plus scaling-rounding error. It does not reuse the pre-scaling identity-row singular-value bound.

Lines342–353 recompute graph/operator perturbation, sparse products, triangle/skew error, epsilon and the graph metric after scaling. With the independently certified representative-shift*I positive and shift=up(2*epsilon), the actual work lower bound is (shift-epsilon)/||W*||². Lines379–384 divide by the outward upper metric, correctly converting back to the original declared scaled physical norm; they do not substitute the equilibrated coefficient norm. Nonsymmetry of actual saved K remains included by the earlier stationary/triangle bounds, so the conclusion concerns quadratic work/coercivity.

Interval helper231–304 imports each stored binary64 coefficient and shift exactly with Decimal.from_float. Contexts use fixed50-digit FLOOR/CEILING and trap Underflow/Subnormal. Lines291–297 correctly bound all four product endpoints, both positive pivot endpoints in division, and opposite update endpoints. Comparisons and stored string endpoints do not round back to binary64. Positive lower pivots prove the same shifted symmetric representative. The complete structural pattern and independent initial/clique guards remain intact; no backend pivot verdict is borrowed.

Saved source368–377 preserves the binary64 pivot evidence and invokes Decimal only after HOLD_INTERVAL_PIVOT, using precisely the same representative, pattern, permutation and shift. It does not retry a certified nonpositive shifted representative. Error budget, physical target and zero-crossing HOLD semantics remain unchanged.

## Observed source-bound evidence

Both whole_half-saved-proof-v3 and whole_double-saved-proof-v3 assessment JSONs match the reviewed source/dependency hashes. I rehashed all five declared inputs and the paired assessment NPZ for each case: zero mismatches.

- physical625/kernel585: binary64 HOLD retained; Decimal completes585 positive pivots. epsilon8.277189640626467e-10, shift1.6554379281252937e-9, graph metric13.125647096000549, physical lower bound6.306119294604964e-11.
- physical1057/kernel1017: binary64 HOLD retained; Decimal completes1017 positive pivots. epsilon6.800297894767238e-9, shift1.3600595789534477e-8, graph metric26.468378116367045, physical lower bound2.5692159394391416e-10.

These conservative lower bounds are much smaller than the earlier dense minima. They need not reproduce those eigenvalues: their purpose is a sound positive bound after all error and physical-metric terms.

I read the root-run test logs: changed-test-v4 reports30 passed/1 failed solely because a budget-rejection message did not match the expected regex; decimal-test-v5 reports3 passed/28 deselected, including exact Fraction pivot comparisons, indefinite rejection and missing-pattern/budget controls. Earlier uncertain-inverse-control and initial fill failures remain retained. No reviewer-run test claim.

The two supervised v3 executions exited0 in2.26s/4.69s, sampled peak process-tree bytes73,449,472/80,998,400, sampled numeric/unresolved maximum1; recorded effective NumPy/SciPy BLAS pools both report one thread. Those are observations for these cases, not measured savings or a larger-case resource guarantee. Decimal resource estimates and local time/update/fill ceilings remain bounded; total process supervision is still required.

No complete composed-certificate synthetic regression specifically exercises T error plus the physical-metric conversion; component Fraction controls and the inspected algebra support this delta, while a future formula-changing edit should add such a small independent control. Current CLI restriction to the two saved reciprocal fixtures, existing order ceilings, accepted-predecessor physical inventory dependency, mandatory external/scientific criteria and different-family acceptance remain unchanged.
