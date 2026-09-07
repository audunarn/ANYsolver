# GE-B3 constrained-fibre initialization — successor development map

Parent `6162e811fea24a99e15c3e1f47d1c4811ba3ccaa`, tree
`ce2c1e42b0ff3f16108f6bc38b646072f1e4ba95`.
The predecessor's high-contrast control failure and all of its source/evidence
remain unchanged. This is private development, not qualification or activation.
Independent scientific review remains PENDING.

## Same constitutive potential, opposite entry

The preserved cell uses `Psi*(p)=sup_x[p^T L^T x-W(x;origin)]`, where
`W=sum_j w_j W_j(S_j x;origin_j)` is the actual physical-fibre incremental
potential. Its gradient is the work-conjugate cell kinematics `k=L^T x`.
The new entry fixes `k` and solves

`min_x W(x;origin)` subject to `L^T x=k`.

Station equilibrium and the affine constraint give

`grad W-Lp=0`, `L^T x-k=0`, with Newton border `[A,-L;L^T,0]`,

where `A` is assembled from the current physical-fibre algorithmic section
moduli. The station strains, fibre returns, history laws, quadrature, section
conventions and retained geometric map are unchanged.

Use a geometry-only feasible initial point `x=L(L^T L)^-1 k`. At each point,
the projected gradient determines `p=(L^T L)^-1 L^T grad W`. Solve the full
constrained Newton system for a direction in `ker(L^T)`. Minimize the actual
piecewise-quadratic potential along the segment using the already defined
fibre yield/hardening breakpoints. Do not use a virgin elastic extrapolation
outside the yield surface as the constitutive initial state.

All local matrix/constraint work is in 80-digit Decimal arithmetic. The existing
60-second cell bound, 48-Newton-update bound, 4,096 line-partition bound and
bounded pivoted solve remain. Positive current tangents and the smooth reduced
Hessian are required; a singular perfect-plastic limit fails closed rather than
receiving an invented stiffness. Return paired resultants, potential, station
fields, proposed histories and the constrained sensitivity `dp/dk`.

The local checks compare this primal entry with the preserved complementary
entry, original strain-entry physical sections, work/Fenchel identities,
constraint satisfaction and first/second variations. These are separately
constructed checks by the same author, not independent authorship or review.

## Constitutive initialization, not history commit

The successor controller uses the same prescribed physical translation and
the same globally retained mixed unknowns. Once at each target, project the
accepted geometry onto the control plane and solve the local constrained fibre
problems from the prior accepted material histories. Initialize the trial cell
resultants from those solutions. Do not commit the local proposed histories.
All later Newton/line-search trials retain their full mixed resultant updates.

At a compatible current trial, solving the original full mixed Newton system
gives the same geometric direction as the Schur expression
`G+J^T C^-1 J`. The implementation continues to solve the full bordered system;
it does not form that condensed matrix or eliminate cell rotation unknowns.
An experimental variant restored resultants at every candidate geometry. That
constitutive projection did not change the potential, but stalled earlier in
the high-contrast case and is not the retained controller. Its failed output
and source variant are preserved, not reclassified.

The global state still stores binary64 resultants. After conversion, evaluate
the preserved resultant-entry cell and require its gradient to reproduce the
imposed kinematics to the existing `1e-11` gate. Never claim that discarded low
resultant components were retained or that the global problem was statically
condensed. All global Newton/backtracking trials still use fixed accepted
origins, and publication/replay retains the existing complete-chain checks.

The new constitutive trial policy and globalization identities are hash-bound into a
successor program/capture identity. Old and new checkpoints are not silently
translated or accepted across controllers. The old controller is unchanged.

## Chart-feasible line search

Unloading can propose an inadmissible full Newton rotation even after a good
initial material state. Bound the first trial fraction before evaluating it.
For nodal and cell spatial increments `a` and `b`, the SO(3) triangle inequality
bounds the new relative principal angle by `theta+alpha*(|a|+|b|)`.

Choose an initial fraction no larger than half the remaining `0.9*pi` chart
margin divided by that angular bound; also bound each nodal/cell increment.
Then perform at most the same eight backtracks from that fraction. The native
chart checks remain authoritative at evaluation. This does not widen a chart,
add target retries, relax an equilibrium tolerance, clip an accepted rotation,
or alter the discrete potential. Singular/unresolved full borders still fail.

The frozen-border natural-correction line-search merit and final equilibrium,
compatibility and control-plane gates remain unchanged. Controller/replay
deadlines, exclusive history publication and cancellation semantics are retained.

## Spatial residual derivative versus chart energy Hessian

For a spatial rotational residual `M`, the gradient of the energy in the
increment chart satisfies `g_delta=J_left(delta)^T M(exp(delta)Q)`.
Since `J_left(delta)=I+skew(delta)/2+O(|delta|^2)`, at zero increment

`H_exp = D_spatial M + skew(M)/2`.

The controller evaluates residuals in the updated spatial tangent frame,
therefore its consistent Newton derivative is
`D_spatial M = H_exp - skew(M)/2` in every nodal and cell rotational block.
This correction is generally nonsymmetric away from equilibrium. The original
symmetric energy Hessian remains unchanged and agrees at equilibrium where
these rotational residuals vanish. No force, strain, material, load or energy
coefficient changes. The full bordered solve already uses a general matrix.

A separate finite-difference check of actual spatial state advancement reduced
the directional discrepancy from `0.0005622868810336075` with the uncorrected
chart Hessian to `4.74247025337592e-11` with the derived connection term. The
normalized acceptance remains `1e-7`. This check is not a claim that the whole
nonlinear qualification is complete.

## Overall programme boundary

Neither a successful local inverse nor a successful bounded control sample
qualifies general nonlinear, buckling, post-buckling, material, dynamic or
beam-shell behavior. Mesh-converged straight/curved/arch/ring studies,
load-path-consistent stability and branch selection, broader constitutive
parity, installed-package/performance checks and independent review remain
required. Existing B2/B3/Q4/S3 mechanics, aliases, defaults and releases are
untouched. This successor must pass its high-contrast continuation and replay
checks before any further qualification claim.

## Preserved development checkpoint

The final four implementation/test sources passed two fresh-directory suites:
30 tests in 170.595 seconds and 30 tests in 171.820 seconds. All 17 JSON pairs
are byte-identical, including both contrasts' loading/unloading/reversal and
split-restart capsules, the local constitutive records, the coarse arch and
rotated-control diagnostics. The three failed intermediate variants remain
separate inventories with their original source snapshots and raw evidence.

The external archive contains 87 content files (2,098,545 bytes) plus its
13,585-byte manifest, SHA-256
`e20116d5b9e6313969cf1b696d97133a4bb7760dc3e6ce9dbe2632b5d9d7711d`.
The repository evidence record binds the archive, source identities and exact
scope. This is a development pass only; independent review is still PENDING.

Next, connect these accepted translation-control states to explicit
frozen-plastic and algorithmic current-state operator checks without replay
advancing or mutating their histories. The existing force-program modal
interface does not accept these control checkpoints. Mesh-converged
arch/ring response, branch stability, general load/material parity and
objective beam-shell joints remain programme requirements.
