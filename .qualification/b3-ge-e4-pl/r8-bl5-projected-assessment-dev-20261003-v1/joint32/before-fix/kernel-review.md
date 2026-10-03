# Joint32 kernel parity review

Read-only source and saved-JSON diagnosis; no numerical case, saved-array calculation, factorization, or worker was executed. Source SHA matches kernel.json: cefaab39b841ba22b26fec2d624bd729845d38e058378d32b759c870c5588f8d. No tolerances were changed.

## Observed failure

Only solution_parity is false. Every full_vs_owner quantity is exactly zero for Fy, Mx and Mz. The failing pairs are full_vs_reduced and reduced_vs_owner, with identical errors. Worst scaled multiplier discrepancies: Fy 2.717544321043057e-8; Mx 5.444307702134806e-9; Mz 7.542646195725546e-9 against 1e-10. Reactions, resultants and domain/interface wrenches also exceed the target; Fy/Mz physical and shell fields exceed it slightly. This is not an isolated multiplier denominator artefact.

Fy corrected full/owner equilibrium is 6.362734720010396e-11; reduced equilibrium is 6.001420087708428e-12. Both pass the separate 1e-8 physical equilibrium gate, which does not establish 1e-10 forward parity. Raw unrefined maximum comparison errors are Fy 0.0128042385, Mx 0.00157458151, Mz 0.00294835438; one compensated correction greatly improves the ill-scaled full solve, but that observation alone does not prove adequate forward accuracy.

## Source inspection

In scripts/r8_bl5_projected_joint_kernel_dev.py:
- Lines 247-251 retain the correct 576 resultant and 2305 physical coordinates, with zero resultant constraint columns.
- Lines 262-285 use L=-D^{-1}Kpx and S=Kxx+Kxp L; signs are correct. Saved work pullback error is 2.063990740184188e-16, constraint/identity errors zero, stationary backward residual 1.623204805588405e-28.
- Lines 357-368 load bound owner states and verify exact tip165 load slots. No indexing difference was found; exact full_vs_owner equality supports this.
- Lines 377-395 perform one full sparse compensated-residual correction with the unchanged matrix/factor.
- Line 396 solves the scaled reduced saddle using the lower symmetric triangle, without an analogous accurate residual correction.
- Lines 411-412 reconstruct q_free=L*(scale*y) and physical lambda=mu/row_norm. These match the scaling in lines 308-312.
- Lines 155-169 compare complete roles using the same coordinate/constraint scales; lines 444-445 retain the strict 1e-10 criterion.

Kernel positivity (minimum 4.335051146768393e-6 versus uncertainty 1.255513392737139e-10), inertia and passing work/balance predicates are separate evidence. They do not repair failed state parity.

## Discriminating saved-array check

For each case, reconstruct the unchanged full saddle A and RHS from saved K, C, free and load. Evaluate compensated A*v-RHS for BOTH corrected_full_solution and the lifted reduced state. Separately evaluate compensated residuals of reduced_solution against the actual scaled saddle and its lower-triangle symmetric completion. Report weighted physical/multiplier blocks and absolute defects; retain every failed value.

This check requires no owner rebuild, element evaluation or new mesh. It distinguishes sparse correction insufficiency from reduced solve/backward error and triangle-completion perturbation. Check the reconstruction residual independently in local resultant rows too. If correction is later authorized, assess each path against its own unchanged operator and the existing parity criterion; do not select or normalize toward the preferred answer.

No precise algebraic defect is established by the current evidence. Remaining full-KKT forward error after a single correction is plausible given the very large raw discrepancy; reduced-saddle rounding/completion is also possible. Full/owner agreement is not an independent accuracy oracle. Preserve kernel.json/npz as UNRESOLVED_DEVELOPMENT_CHECK until the discriminator resolves this uncertainty. No formal authority or different-family acceptance is implied.