# Finite-domain deterioration rule — independent addendum

2026-09-30. Disposition: the proposed rule is honest and sufficient as an explicitly limited numerical-development predicate for finite-family noncollapse. It is redundant with the independently frozen floors and a checked variational upper bound. It does not separately demonstrate mild deterioration, asymptotic stability, convergence, locking control or full F03/M2 acceptance. No stricter raw-deterioration limit follows from the presently supplied inequalities.

## Exact implication and applicability

On the supported physical quotient, use the same physical work functional and exact reference norm in both problems. If the native positive primal norm is the exact restriction of that reference norm, then for every multiplier:
lambda.T G_h lambda = sup_(v_h) F_lambda(v_h)^2/h(v_h)
                    <= sup_(v) F_lambda(v)^2/h(v)
                    = lambda.T M lambda.
Consequently G_h <= M and beta_h <= 1. This upper bound is variational; it is not an assumed spectral scaling or a property of mechanical K.

Together with the independently obtained Fortin floor beta_fine >= f_fine > 0:
p = log(beta_coarse/beta_fine)/log 2
  <= log(1/f_fine)/log 2.

The denominator is valid for the registered adjacent grids whose declared mesh measure halves. The same argument permits negative p when beta improves. It requires the work/norm restriction, supports, units/Q scaling and physical quotient to be checked for each actual GE fixture. An omitted-coordinate C-null direction is not thereby a mechanical gauge. The reference boundary conditions and cell-rotation field declaration must remain consistent.

For numerically computed beta/reference quantities, use the prospectively fixed inverse/eigen/conditioning and reference-error budgets. Apply the ceiling to the quantity justified by those budgets, with the declared numerical margin, rather than assuming an approximate denominator makes beta<=1 exact. A value above one beyond that margin is a map/norm/numerical discrepancy to investigate; it is not justification to enlarge the ceiling afterward. Binary64 checks remain ordinary numerical evidence, not certified roundoff intervals.

## What the predicate does and does not establish

Root reports the 21-case scalar V2 lifting constants C_S² in 1.019005..1.350615 and product-floor envelope about 0.4302334. This addendum reviews the proposed implication, not a new execution or independent replay of those numerical cases.

Freezing case floors, their envelope minimum, beta<=1 applicability and the derived adjacent-level p ceilings before GE assessment is noncircular. These values are determined by the independent scalar lifting and product norm bound, not adjusted from candidate beta. Enforcing the absolute envelope and reporting raw beta and signed p makes the finite-domain claim explicit.

The p condition adds no independent strength once the relevant floors and variational upper bound hold. It can allow a substantial single-step decrease. It must therefore be named an implied finite-family noncollapse ceiling, not evidence that refinement is nearly flat or that response convergence has been established. The deficient c1 scalar sequence (reported C_S² about 167.23/667.44/2666.57) remains an independent adverse control; its worsening floor cannot be hidden by normalizing a candidate beta by that changing floor.

R8 §4.5 permits registered finite-domain numerical evidence and rejects an invented universal deterioration cutoff. This derived ceiling supplies a justified prospective allowed-deterioration rule for the stated limited development scope, without adding an h-uniform-proof gate. The independently declared norm/reference, actual kernel, locking, transfer/accuracy and broader qualification obligations remain unchanged.

## Stricter limits

The premises f_i<=beta_i<=1 alone cannot imply p<=log(f_coarse/f_fine)/log 2: f_coarse is a lower bound, not an upper bound on beta_coarse. Similar scalar lifting constants on two grids also do not bound the ratio of actual product beta values.

A stricter independently justified limit would require additional information, such as a proven coarse upper bound below one, a cross-level work-preserving comparison on consistently normalized spaces, or a separately justified intended-accuracy/refinement requirement. None is supplied by this floor calculation alone. Such a limit remains unestablished for any stronger stability/convergence claim; it need not be invented or imposed as a new prerequisite for this finite-family development record.

No numerical jobs, GE spectra, source edits or formal acceptance were performed. Only this addendum file was written.

