# P5 conservative energy seed development — 2026-09-06

Successor to `6ed4fb7ff2f6e3c7d5a404d2443232f3b72600c0`, tree
`2d1128dd233fbaa0633fbeb0a9cb82a412b8f9f7`. The preceding diagnostic handoff
and all failed solver experiments remain unchanged. This is research by the
same author, not independent review, production integration or qualification.

## Diagnosis completed before the successor attempt

The unchanged two-element continuum-shape seed is specified in
`test_ge_beam3_curved_p5_seeded_equilibrium_probe.specimen(2)`: length 2,
EA=1000, GA=400, EI=1, tip angle 0.6, compressive spatial dead load
0.6449785996190569, order 8 and virgin elastic histories.

A separately bounded four-state diagnostic applied three full bordered
corrections while holding the tip angle fixed. It did not run the full failed
two-phase algorithm, commit histories or return to the original load.

| State | Load factor | Physical residual | Angle gap | Bordered condition estimate |
|---:|---:|---:|---:|---:|
| 0 | 1 | 1.3381954246673584 | 0 | 809457.4297173003 |
| 1 | 1.012521276746201 | 0.00016350844733111394 | 0 | 54393.25647599464 |
| 2 | 1.0123195973282055 | 6.879948317327695e-7 | 0 | 54383.017051435505 |
| 3 | 1.0123196042924412 | 4.3315646272992326e-13 | 0 | 54383.03258655339 |

All three full corrections decrease the old shape-phase merit and therefore
would be accepted by that phase's backtracking rule. This establishes that the
observed angle-controlled equations can be solved within the old bounds. It
points to the subsequent load-return phase as the failure location; it is not
a reconstruction of the unrecorded full failed two-phase trace.

A separate six-state diagnostic at the original load applied only five full
Newton corrections, without history commit or a convergence claim. Residuals
alternated between small and large values (approximately 1.338, 0.0271, 1.820,
0.00238, 0.566, 0.000200). Full-step energies sometimes rose, so simply removing
backtracking is not adopted. The diagnostic motivated inspecting total energy
as a merit function rather than insisting on monotone force residuals.

Both commands completed in under three seconds. Results above were captured
from command output, not external raw scientific packets or resource receipts.

## Solver-only successor

The new helper is `ge_beam3_curved_p5_energy_seed_probe.py`. It calls the
unchanged mixed potential, local stationary solver, section law, assembly
scatter, spatial residual derivative and accepted-origin replay validator.

For the explicitly supported nodal spatial dead forces, the merit is

    Pi(x,U) = internal_potential(x,U) - sum_i f_i dot (x_i-X_i).

The search path uses additive translations and left-multiplicative rotations.
Its initial energy derivative is the assembled residual dotted with the Newton
correction. Finite nonnegative slope fails closed with a request for an explicit
branch strategy; this helper does not shift stiffness or replace the direction.

Backtracking starts at the full step, halves at most nine times and accepts
Armijo decrease with c=1e-4. Objective-based backtracking is a standard option;
see [PETSc SNESLINESEARCHBT](https://petsc.org/main/manualpages/SNES/SNESLINESEARCHBT/).
This is a small native implementation, not PETSc integration or copied source.
The coefficient controls the iterative algorithm, not element mechanics or
scientific accuracy. No numerical-library dependency is added.

Near equilibrium, if both the predicted energy change and measured energy
difference are within 32 machine epsilons times the larger sum of absolute
internal energy and external work, acceptance instead requires strict decrease
of the original physical residual norm. Unresolved energy alone cannot accept
a step. This floating-point merit guard does not relax final stationarity:
the existing normalized physical residual must still be at most 1e-11.

The original limits remain sixteen global updates, ten backtracks, 256 mixed
evaluations per element and a 0.9*pi increment cutback bound. No automatic
retry, load subdivision, adaptive budget increase, gradient fallback or branch
switching is implemented. All supplied data are checked; a virgin assembly and
exact clamps are required. Plastic activity is rejected because a shape seed
does not specify a plastic loading history. Nonconservative loads and unstable
equilibrium continuation are outside this conservative initializer's scope.

Every evaluated candidate records its iteration, backtrack, consumed mixed
evaluations, energy, residual, slope and acceptance disposition. Errors carry
the available diagnostic checkpoints/count, never a partially accepted model.
All state changes occur on a deep copy. Success must pass the existing atomic
commit and exact accepted-origin replay checks.

## Explicit two-element attempt and accuracy distinction

After nine small tests passed, one explicitly declared development attempt used
the unchanged original two-element seed and bounds:

- COMPLETE in **12 updates / 90 mixed evaluations**.
- Final physical residual: **5.141804364589066e-12**.
- Tip angle: **0.5124260742877697**.
- Tip-response relative error against the continuum seed: **0.14763081177139395**.
- Final total potential: **-0.001761317345153432**.
- Accepted-origin replay matched exactly; supplied model stayed unchanged.

At the second update the full step was rejected on energy. The half step
decreased energy from -0.0015365792350718749 to -0.001588596954792465 while
raising the force residual from 0.027085390842010146 to 0.4684193906155529.
The old monotone-residual rule would reject this useful step. Later accepted
energy-decreasing steps also temporarily raise residuals. The final correction
uses the roundoff-residual guard and satisfies the original 1e-11 criterion.

This resolves the bounded solve for this case under a successor algorithm;
it does not retroactively pass any failed old solver. The **14.76% coarse error
does not meet the 2% engineering accuracy gate**. Successful solution and mesh
accuracy remain distinct requirements.

## Tests and remaining work

The completed successor suite passed **18 tests in 10.81 seconds** with one
numerical thread. It checks Armijo/roundoff logic, nonfinite rejection, positive
energy scaling, independent dead-load virtual-work differentiation, the old
small curved/coupled equilibrium, original bounds and atomic budget failure.
Two/four/eight-element postcritical solutions improve monotonically; two and
four remain above 2% tip-response error and eight is below 2%. A separately
executed repeat of the successful two-element case produces identical state,
replay and diagnostic checkpoints; it is not a retry of a failed request.

The suite also checks a positive free second variation at the final coarse
state (binary64 Cholesky, not an exact/domain-wide certificate), rigid reference
re-expression covariance, elastic-only history admission and failure after a
private commit without publishing partial state. Tests are small correctness
checks; their timings are not performance claims or a formal qualification wave.

The final two tests additionally reject nonfinite internal potential and
overflowed external work before any convergence publication. Before those
guards were added, the sixteen-test version passed in 10.89 seconds. Existing
diagnostic and seeded-equilibrium regressions passed **20 tests in 12.86
seconds**, reported separately from the successor inventory.

Source SHA-256:
`55D5A56280B124ED4AC75116A766CD5F196647DD093C1088951C3C7F35D2DB8B`.
Test SHA-256:
`FF7FB6F596861180AE1092A1533BA96898DB9637C70EE54790623CEA880938BF`.

Next, verify conservative globalization through committed load continuation,
including load reversal/cutback and initially curved postcritical cases. Do not
apply this minimum-seeking seed policy indiscriminately to unstable branches,
plastic state histories, follower loads or arc-length equations. Those need
their own consistent objectives/merits and independent engineering references.
Full section parity, prestressed modes/dynamics, robust extreme coupled local
stationarity, production integration and objective beam-shell joints remain
open. The full goal is active, incomplete and not blocked.

Only this development record, its research helper and test are added. No src,
B2/B3/Q4/S3 mechanics, defaults, recovery/state laws, packages, dependencies,
workflows or accepted evidence changes. No push, merge, release or activation.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
