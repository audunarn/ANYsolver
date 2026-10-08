# Independent D1 pressure-space admission review

**29 September 2026. Read-only mechanics assessment; no acceptance or
production change.** The reviewer inspected the fine nodal Q1 primal
mortar candidate, [D1 gap map](../GENERAL_CONTACT_D1_ACCEPTANCE_GAP_MAP.md),
[prescribed-edge null proof](d1_prescribed_edge_null_20260929.md) and
[balanced cut-front scalar record](d1_balanced_cut_scalar_20260929.md).
The integrating lead did not ask the reviewer to author the pressure
kernel or run another coupled case.

An away-from-clamp profile is a coherent **candidate boundary**, but
the existing evidence cannot admit its pressure stability. At each
pose, let `A_h` contain the strictly positive-force, positive-support
fine-Q1 pressure hats whose entire physical support stays a fixed
distance from the prescribed x=0 transverse edge. An admitted profile
would reject active clamp-touching hats. It must retain every
positive-support mode, however small its support. The actual positive
baseline permits sufficiently small perturbations of either sign
within `span{φ_i : i∈A_h}`; a nonnegative-coefficient check or
single-hat checks do not test the relevant stability space.

The needed condition is a mesh- and cut-phase-uniform lower bound
for the signed active-span work operator
`W=diag(S)Dgbar`, measured in the physical pressure norm against
an independent two-body shell energy-dual reference, including
front fractions `θ→0+`. Matching source Q1 test functions away
from the clamp give positive clipped Gram matrices at each finite
pose. Saved active ranks 48/48, 96/96 and 10/10, and the fixed
10%-cut scalar results, show finite detection only; they cannot
provide the required uniform bound. The exact `M_x^{-1}e_0` modes
have nonzero work on continuous admissible motions, so they cannot
be removed as a physical quotient.

**Smallest decisive mathematical check:** on a shape-regular two-row
Q1 patch away from the clamp, derive exact clipped work
`B(θ)` for the last full row and cut row and analyze the smallest
signed-span discrete/continuum energy-dual ratio for all
`0<θ≤1`, particularly its `θ→0` limit. Use an independent
continuum `H^{-1}` reference with analytic/asymptotic bounds or
certified intervals. An explicit sequence with ratio tending to zero
rejects unchanged Q1 for the proposed unrestricted positive-front
profile. A positive local result still needs a global assembly
argument and a bridge from the scalar energy to actual E4-PL
two-body shell work before D1 admission. No eigenvalue at one
saved pose can decide this.

If the uniform bound fails, a separately derived enrichment or
stabilization of the displacement-pressure pairing, or a stable
mixed pressure space, is needed. Removing tiny positive supports,
calling clamp nulls physically redundant, or increasing an iteration
budget is not a valid mechanics repair. A revised method would
require new pressure/front, work-rank, coupled response and timing
evidence; unaffected geometry/oracle checks could be reused after
impact analysis.

**Disposition:** pressure-space stability remains open. The next
work item is the bounded analytic `θ` check, with no larger coupled
mesh campaign or production-law change before its result.
