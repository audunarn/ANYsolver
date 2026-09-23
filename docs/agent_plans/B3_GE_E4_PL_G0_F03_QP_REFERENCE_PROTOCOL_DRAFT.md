# F03 conforming Qp classical-reference gate: draft protocol

23 September 2026. **Draft only: no one-use execution authority and no
scientific result.** This proposes a new, independently reviewed gate for
the unchanged classical finite-pad shell/beam problem after the earlier
polynomial Ritz attempts failed. It does not amend or replay their raw
evidence. The conforming Qp reference is not the native B3-GE/E4-PL line
attachment and cannot by itself close F03 or G0B.

**Current disposition:** Do not register the Q1/Q2/Q3 sequence below as a
one-use scientific gate. The unregistered solved-state preparation with
high-precision one-ulp coefficient recovery gave full-functional pair
changes of `6.279584%` (Q1→Q2) and `1.114597%` (Q2→Q3). Both exceed the
proposed 1% limit. The coefficient route passed focused numerical checks.
Independent mechanics review found no preparatory formula blocker, but
default-grid end-to-end work/resource checks remain pending. Subsequent
independent Decimal reconstruction from the nodal state agrees with the
float-cell-coefficient path at most `3.50e-16` normalized on the solved
Q1/Q2/Q3 states. Exact Fraction arithmetic finds no displaced interior
event on this frozen grid; the one `2^-53` tip-boundary discrepancy changes
the independently evaluated endpoint resultant at most `4.92e-17`
normalized. Both routes share the same Decimal density mechanics, so a
separately implemented high-precision mechanics oracle remains desirable.
Select and freeze a genuinely better-resolved h/p sequence
under a later version of this draft; retain these exploratory results and
the earlier failed Ritz evidence. Do not relax the physical criterion.

A subsequent unregistered Q3/Q4/Q5 screen has full-functional
adjacent changes of `0.2937464%` and `0.1205903%`. However, Q3→Q4
still fails the proposed 1% signed-scalar screen on beam energy,
section resultants, tip atom and a near-root band wrench. Q4→Q5 meets
1% on the checked scalar inventory. The separate
[high-order screen](B3_GE_E4_PL_G0_F03_QP_HIGH_ORDER_SCREEN_20260923.md)
records source tests, raw signed outputs and the expensive custom-grid
spatial check. It has not exercised the complete default-grid spatial,
restart or per-case resource inventory. A revised protocol must use a
better-resolved systematic sequence and pass all prerequisites and reviews;
the Q1/Q2/Q3 case inventory below is retained as the earlier failed draft
proposal. Q3/Q4/Q5 also remains exploratory failed-scalar evidence.

An exploratory Q6 solve brought all 49 checked Q4/Q5/Q6 scalar pair
differences below 1%, but two band-force components fail the draft
absolute-change rule: `[0.5,0.75]` Fy changes `103.106→202.258 N`,
and `[1/32,1/16]` Fy changes `30.951→177.243 N`, versus an allowed
`10 N` increase. The [Q6 screen](B3_GE_E4_PL_G0_F03_QP_P6_SCREEN_20260923.md)
retains raw values and other limits. Q4/Q5/Q6 therefore also remains
unregisterable under this draft. Investigate the band behavior and
obtain independent mechanics review before selecting a successor or
proposing any acceptance-matrix change.

An unregistered fixed-Q6 X0→X1→X2 h pilot subsequently passed the
unchanged 49-component signed screen, absolute-change rule, and complete
functional rule. The [pilot result](B3_GE_E4_PL_G0_F03_QP_H_PILOT_RESULT_20260923.md)
preserves the raw cases and the earlier X1 Q4/Q5/Q6 p failure. This is a
feasibility signal, not a one-use scientific pass. Before replacing this
draft, bind all three h-level states to independently reconstructed
outputs, verify actual-case h-embedding and complete area/spatial/support
work, measure full-route resources and installed behavior, freeze an exact
source/environment/case registration, and obtain independent mechanics
review. Rerun all three levels under that registration. A classical
reference pass would still leave the native F03 formulation open.

## Candidate and case inventory to freeze

Use the original flat panel, material constants, beam section, smooth
signed transverse beam load, two supported shell x edges, four physical
finite square pads, held represented `J`, and exactly three beam-root pose
constraints. No slope clamp, absolute tip support, penalty, or new
interface law is admitted. Preserve every represented station crossing,
including adjacent binary64 events separated by one ulp.

The proposed systematic p sequence is Q1, Q2, Q3 on the same geometry-
fixed 9-by-5 rectangular partition. It has 96, 374 and 832 free shell
coordinates. A separate custom-grid sequence remains a code/mechanics
check, not a substitute for these physical cases. If the p sequence
fails, retain the raw failure and register a revised h/p candidate
separately; do not reinterpret the 3-level screen as passed.

Freeze before execution: exact candidate commit, all imported source and
dependency hashes, Python/NumPy/SciPy build identities, case definitions,
runner/adjudicator hashes, thread pools, OS/hardware, memory/time budget,
reference scales, all numerical and physical criteria, raw evidence root,
and terminal precedence. The registration must identify a clean isolated
source checkout and a one-use supervisor. No existing failed evidence root
may be overwritten or reused as fresh authority.

## Mandatory numerical preflight in every case

1. Check shell energy positivity, tangent symmetry where required, three
   independent scaled root rows, six scaled root pose/derivative rows, and
   finite arrays before solving. Preserve 4/6, 5/7 or 6/8 beam-order and
   48/64 load-order comparisons on every represented station interval.
2. Return only a state with scaled free equilibrium, root compatibility
   and energy/work defects no greater than `1e-10`. Verify the actual
   solution is generated by the registered source and belongs to the
   registered Qp definition.
3. Independently audit finite-pad pose, first and one-sided second station
   derivatives, signed beam density and endpoint atoms, physical virtual
   work, and the nonduplicated root reaction. On one-ulp intervals, recover
   the local polynomial from the represented physical cell coefficients
   at higher precision, check the exact geometric crossing inventory,
   held interior points, and stability at two arithmetic precisions.
   Count every such interval. The older two one-sided constant choices are
   diagnostics only and cannot bound the unsampled polynomial.
4. Assemble the physical pad-area adjoint and compare it with a separate
   line/atom nodal projection, global force, origin moment and nonrigid
   virtual work. Before support or spatial results are accepted, compare
   area quadrature orders `p+5` and `p+7` in x at `2e-10` scaled load and
   wrench discrepancy. Store both raw orders and the observed difference.
5. Recover shell cell `div(T)+f_mu`, supported/free outer tractions and
   interior jumps with their signs. Check the complete work identity,
   six physical supported-edge reactions and their two distinct interior
   liftings, beam-root reaction, force and origin-moment balance. Use
   `1e-8` scaled balance/reaction-work limits, without treating balance
   as proof of accuracy.
6. Verify 48/64 quadrature for signed full H1-dual density-density and
   density-atom terms, analytic endpoint Gram, and coefficient-space
   subtraction on the merged exact represented partition. The angular
   channel is divided by `ell` exactly once. Preserve any negative or
   nonfinite squared norm as failure. A numerical comparison floor must
   be recorded separately from a physical settling tolerance.
7. Check exact-space p1→p2 and p2→p3 embeddings, load/root/tip actions,
   monotone stationary energy, and the nested energy-distance identity
   at `1e-10` scaled. This is an algebraic check, not continuum error.

## Physical quantities and proposed settling decision

Record the full accepted state arrays and hashes, shell/beam/total
stored energy, external work, physical and scaled tip pose, all three
root reactions, six shell-edge wrench components about the same origin,
root and tip section resultants, root/tip interface atoms, and complete
line and total wrenches on the four quarters and on `[0,1/32]`,
`[1/32,1/16]`, `[15/16,31/32]`, `[31/32,1]`. Preserve cell residual,
free-edge and interior-jump channels separately. Include area/line
projection and support-lifting comparison arrays, not just maxima.

Use the earlier classical reference's signed-scalar normalization as the
proposed physical screen: for each p1→p2 and p2→p3 pair,

`abs(x_f-x_c)/max(abs(x_f),abs(x_c),1e-3*S) <= 0.01`,

with `S=F0` for forces/atoms, `M0` for moments, `U0` for scaled pose,
and `E0` for energies. Require the final absolute change to be no larger
than the preceding change plus `1e-5*S`. The complete functional
difference must be at most 1% of `max(operand norms,1000 N)` on both
pairs and its final difference no larger than the preceding difference
plus `10 N`. These are proposed limits to freeze *before* a scientific
run. Failure of any mandatory quantity is failed evidence, not permission
to drop that quantity or relax its tolerance.

The eliminated beam gap is zero by construction and earns no independent
gap-convergence pass. Strong residual localization is diagnostic, not an
unregistered solution-error percentage. Even a passed Qp classical
reference would still leave native line multiplier stability, shell
torque/drilling/shear behavior, attachment topology, plasticity and the
remaining G0/G1 gates open.

## Resources, records and terminal status

Proposed per-case bounds are 900 s and 8 GiB sampled child RSS, with
single-thread pools, serial cases and a 3,600 s launch cutoff. Record
startup separately from solve, area projection, recovery, functional
conversion/norm, and adjudication; preserve failed work and exact case
identity. The current custom-grid preparatory p1–p3 nodal suite took
268.16 s before a streaming change. That is not evidence that the
default-grid high-order spatial/functional route fits these bounds.

Before promotion of a revised draft to a registered one-use protocol,
require a newly selected and frozen systematic h/p sequence capable of
meeting the unchanged physical screen, complete runner/adjudicator
implementation, independent validation of the high-precision coefficient
path, default-grid smoke/resource screen, immutable case and source hashes,
and independent mechanics and execution review.
Then run the registered cases once under the registered supervisor, preserve
all raw outputs, and adjudicate independently. A process/resource failure
is `FAILED_EXECUTION`; a numerical or physical criterion failure is
`FAILED_EVIDENCE`; missing or altered registration identity invalidates
the run. No failing status may be replaced by a second run under the
same registration.
