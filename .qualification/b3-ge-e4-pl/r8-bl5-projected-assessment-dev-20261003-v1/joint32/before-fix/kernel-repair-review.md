# Joint32 kernel repair delta review

Read-only source and saved-JSON review. No numerical run, factorization, saved-array computation or worker was launched. Reviewed scripts/r8_bl5_projected_joint_kernel_dev.py lines396-443 and residual-diagnosis.json, plus kernel-v2.json after it became available.

## Algebra and independence

The new correction is algebraically correct. Partition the original physical/resultant equations as Kxx dx + Kxp dp + Cx.T dlambda = rx; Kpx dx + D dp = rp; Cx dx = rc. With L=-D^{-1}Kpx, dp=L dx + D^{-1}rp, so the reduced physical RHS is rx-Kxp D^{-1}rp.

- Line413 computes particular=-cho_solve(-D,rp)=D^{-1}rp, with the correct sign.
- Line414 computes the required physical RHS subtraction.
- Line416 scales physical RHS by scale and constraint RHS by 1/row_norm, consistent with normalized Cx*diag(scale)/row_norm.
- Lines417-418 reconstruct the nodal/resultant correction as lifted*(scale*delta_y)+particular and lambda correction as delta_mu/row_norm.
- C[:,pp]==0 at line251 justifies omission of C*particular from the constraint RHS.
- Lines397-418 use an independent general reduced LU and local negative-block factors. They never use full_factor, owner answer, averaging, or a changed parity tolerance. The original full matrix supplies only the reduced path's own residual.

The general LU also removes the former reduced solve's lower-triangle completion. Local Cholesky completion remains covered by the unchanged local residual/error checks; no new algebraic defect was found.

The saved reduced_solution/raw_reduced_solution remain uncorrected scaled reduced coordinates. Corrected_lifted_reduced_solution and per-case reduced_q/multipliers are authoritative corrected states. Later reconstruction checks must include the saved particular term; re-lifting reduced_solution alone omits the repair.

## Observed diagnosis and v2 outcome

The earlier compensated full residual maximum is Fy4.9317e-12, versus lifted reduced2.7058e-10, despite a reduced-equation residual9.9734e-16. This motivates testing the original equations, not relaxing parity.

V2 still fails solution_parity. Fy multiplier discrepancy is2.7175229468e-8, almost unchanged from2.7175443210e-8. Reduced equilibrium improves from6.0014e-12 to5.7463e-13; reduced weakgap improves from1.4253e-20 to7.7852e-22. Full/owner remains at equilibrium6.3627e-11 and weakgap7.4814e-16. Mx/Mz show the same qualitative improvement of reduced backward error without resolving forward parity.

This evidence strongly shifts suspicion to inadequate full/owner forward accuracy after one correction, rather than reduced triangle completion or stationary reconstruction. It does not by itself prove an exact forward error bound. Full/owner bitwise agreement remains correlated evidence.

## Full compensated residual branch

The installed _accurate_sparse_residual implementation, source lines106-137, computes each original binary64 row using rounded product plus FMA product error and math.fsum, or exact Fraction products without FMA. RHS subtraction and residual sign are correct. No incorrect residual branch was found. The full solve receives only one such correction; ordinary physical gates after correction are weaker than the strict1e-10 state-parity requirement.

## Precise next discriminator

Apply the same independent reduced LU/local-particular correction map ONCE to the negative compensated residual of saved corrected_full_solution, without changing either saved state or interpreting that diagnostic as acceptance. Compare the predicted full-state correction to saved(corrected_lifted_reduced_solution-corrected_full_solution), for physical roles, resultants, multipliers and reactions. Save original residuals by physical/resultant/constraint blocks, predicted correction, observed difference and their discrepancy. This tests whether the offending forward difference is explained by full residual amplification; it is not another arbitrary iterative repair.

Strict parity remains failed; retain both kernel pairs and all original evidence. No qualification, uniform stability or formal authority claim follows.