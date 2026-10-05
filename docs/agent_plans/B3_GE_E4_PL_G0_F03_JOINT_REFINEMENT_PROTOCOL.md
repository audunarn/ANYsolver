# F03 classical finite-pad joint-refinement diagnostic

22 September 2026. This source-bound diagnostic follows the accepted pure
analytical-norm study. **It cannot select a production space or close G0B.**
The endpoint comparison v1 remains `UNRESOLVED_AUXILIARY_NORM`; its 32/64
rule is not changed, and no old execution authority is retried.

## Physical model and inventory

Keep the one-metre classical in-plane beam/shell fixture, four .10 by .10m
material pads with .05m halfwidth, pad centres at offsets (+/- .20,+/-.23)m,
smooth beam load, sections, axes and supports from the endpoint comparison.
Beam root translations and section angle are fixed; Hermite slope is free.
Gap channels remain `(bx-Tx, by-Ty, .46*(theta-Theta))`, in metres.
P1 uses every line hat; hybrid uses interior hats plus exact endpoint gaps;
enriched uses every line hat plus endpoint gaps. All use exact multipliers.

| Level | Ns | Ny | Nb | Nm | Equilibrium source |
|---|---:|---:|---:|---:|---|
| Coarse | 4 | 8 | 8 | 4 | New |
| Middle | 8 | 16 | 16 | 8 | Saved endpoint-comparison baseline |
| Fine | 16 | 32 | 32 | 16 | New |

Cross all levels with Q4 and CST-CB, and all three families. This gives
**12 new equilibria plus six reused-state evaluations**. Middle states are
read-only, copied and hash-bound. Reconstruct physical observations and
the analytic Schur diagnostic without any equilibrium factorization or
solve. Sparse structural inverse actions for Schur construction still run
and are distinct from an equilibrium solve. Failure to reuse never falls
back to a fresh solve. The registration binds both prior evidence roots,
exact snapshot hashes and unchanged physical operator/dependency identities.
The reviewed loaded-driver changes are explicit alternatives; historical
FE32/64 defaults and outputs remain unchanged.

## Auxiliary norm and inspectable numerical evidence

Use the validated piecewise-analytic free-end full-H1 scalar dual Gram,
normalized by the physical row measures, L0=1m. Its nine Nm=4,8,16
P1/hybrid/enriched validations have maximum relative operator error
1.666e-13 versus independent Decimal Green quadrature. Bind its unchanged
source to analytical-norm-v1 registration and adjudication hashes. This
is a floating calculation, not an interval-certified enclosure.

Use Kbar=D.T K D/E0 and Cbar=diag(1/(U0*measure)) C D, with L0=1m,
F0=1MN, M0=1MN m, U0=F0/(210e9*.07), E0=F0 U0. The three-channel Gram
is the normalized scalar Gram tensor I3. No FE-resolution delta is assigned
to this analytic path. No artificial inertia, stiffness, symmetry repair,
clipping or regularization is allowed. Structural matrices remain sparse;
only interface Schur and Gram matrices are dense and bounded.

Save owned S=Cbar Kbar^-1 Cbar.T and G per family, together with q, physical
multipliers and observations. Adjudication reopens these small matrices,
checks symmetry/Gram identity/SPD and reproduces the entire generalized
spectrum. Schur spectra/minimum positive square-root quotients are finite
model diagnostics only, with no invented continuum inf-sup threshold.

Numerical limits remain: free equilibrium and force/moment balance1e-8,
normalized compatibility1e-9, work identity and within-mesh enriched
energy ordering1e-8, structural inverse-action residual1e-8, relative
matrix skew1e-9, and no nonpositive Schur modes. Reused physical state
arrays must be exactly equal. Recomputed historical physical observations
use relative1e-10 plus absolute floors1e-15 for coordinates/scaled values,
1e-12 for energies and1e-5 for force-like coefficients. Their normalized
parity ratios must be at most1. Combined dual norms and spectra deliberately
change with the norm and are excluded from that historical physical check.

## Frozen physical trend screen

Retain signed values and both successive changes for every channel. For
scalar x use r=abs(xfine-xmiddle)/max(abs(xfine),abs(xmiddle),1e-3*S).
Require r<=.01 and abs(last change)<=abs(first change)+1e-5*S for screened
channels. S is F0 for forces/atoms, M0 for physical moments, U0 for scaled
pose and E0 for energy. The near-zero allowances are10N,10Nm,
6.802721088e-10m and6.802721088e-4J. These are preregistered descriptive
settling measures, not a relaxation of physical-reference tolerances.

Screen separately: all root resultant components, tip scaled pose,
total/shell/beam stored energy, endpoint atom channels in hybrid/enriched,
and total physical band wrenches. P1's explicit atoms are structurally
absent, so their zero trend supplies no positive evidence. Retain all root
elastic/line/endpoint partitions and line-only band quantities. Do not
combine force and moment magnitudes, average families or drop P1 afterward.

Bands are all four physical quarters, plus [0,1/32], [1/32,1/16],
[15/16,31/32] and [31/32,1]. Integrate density and lever-arm moments
about the same origin; include the root/tip atoms exactly once in the
appropriate band. The independent fixed-band evaluator uses Gauss2 for
linear density and quadratic moment integrands, split at mortar nodes.
Shrinking first-cell quantities are not used as convergence evidence.

Compare the full multiplier functional, including density and atoms.
Embed each coarse nodal linear density exactly to the finer grid (even
rows copied, odd rows averaged); leave physical atoms unchanged. Form
P=diag(h/2,h,...,h,h/2,1,1)[lambda;alpha]. In the canonical enriched
normalized Gram compute D²=sum_channels DeltaP.T G DeltaP. Use the same
norm for each operand. Require D/max(norm(Pf),norm(Pm),1000N)<=.01 and
Dmiddle-fine<=Dcoarse-middle+10N. The third channel is already conjugate
to the length-scaled angle; do not multiply it by .46 again. Preserve
negative/nonfinite quadratic forms as failures, without clipping.

For gaps, compute actual RMS of g and the combined beam/shell motion,
using8-point quadrature per unchanged reference overlay and length L0=1m.
Record all three gap/motion channel RMS values and signed endpoint gaps.
Require finest gap RMS and maximum absolute endpoint component, each
divided by max(motion_RMS,1e-3 U0), <=.01. Neither may increase from the
middle level by more than1e-5 U0. Do not apply a relative-change-to-zero
test or impose an extra slope constraint.

At the finest level compare Q4/CST-CB and every pair of families at1%
using the same floors for common physical outputs (root resultant, tip,
energies, total band wrenches) and the full functional. Do not demand
cross-family agreement of explicit atoms or line/endpoint partitions:
P1 can represent concentration through its line density. Record those
decompositions without using them as cross-family acceptance quantities.

There is no cross-mesh energy-monotonicity rule: primal refinement and
constraint refinement compete, and the triangulations may not be nested.
Enriched energy<=P1/hybrid remains a check within each common mesh.

## Execution, adjudication and terminal decisions

Register only after focused tests, independent mechanics/code review,
and a clean source commit. Use b3_e4_f03_joint_refinement.py and the
existing supervisor with all five numerical thread caps1 in supervisor
and children. Run serially, each child limited to900s and8GiB sampled RSS,
with a2400s launch cutoff. A child launched before that cutoff may finish
afterward within its own900s limit;2400s is not a hard total-time cap.
Recognized cancellation stops the loop after its receipt is preserved.
No competing scientific workload,
automatic retry or overwritten output. Save completed-family artifacts
before proceeding to the next family. Preserve failure and partial output.

Canonical adjudication requires the complete six-case supervisor inventory.
Failure to finish the inventory remains incomplete evidence; it does not
consume adjudication or allow missing cases to disappear. Validate raw
receipts, events, source/thread/resource identities, all artifact hashes,
partial/final state parity and the physical/norm identities. Terminal order:

1. FAILED_EVIDENCE for corrupted/inconsistent evidence.
2. FAILED_EXECUTION for process/time/resource failure.
3. FAILED_NUMERICAL_SCREEN for violated fixed numerical checks.
4. UNRESOLVED_JOINT_REFINEMENT if any registered physical trend remains open.
5. PASSED_BOUNDED_TREND_SCREEN only when every registered screen passes.

Preserve per-family/topology outcomes. Adjudication returns nonzero for all
but the final bounded pass. Independent post-execution review checks raw
states/matrices and recomputes summaries without structural reruns.
Even a complete pass proves neither continuum convergence nor the native
full-vector/shear/drilling formulation. F03 and G0B stay open; G1 is barred.
