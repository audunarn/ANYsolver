# GE-B3 P5 retained-spin midpoint development

## Scope and preserved baseline

Parent: `2655aded29f4ffd2d12c50699b570679a12757f0`, tree
`36a96d951a717a66b9fd9fba870bbfe6de1404d3`.
This successor adds a research module and small correctness tests. It preserves
the backward-Euler implementation and temporal comparison, prior evidence,
production mechanics, public routing, versions and defaults. It is not a
qualification record or permission for production finite-rotation dynamics.

The separate axial reference demonstrated first-order temporal damping, not
an axial mechanics defect. Its linear midpoint recurrence is a comparison,
not evidence that the nonlinear beam already has a midpoint implementation.
No existing tolerances are relaxed.

## Discrete method

The physical dynamic variables remain nine nodal translations and six spatial
cell spins. Nine nodal rotation traces have zero inertia. For a step h, unknowns
are total translation increments dx, stage trace increments psi, and total cell
rotation increments phi. With committed x0, Q0, U0, v0, w0:

    xm = x0 + dx/2             Qm = Exp(psi) Q0
    Um = Exp(phi/2) U0         vm = dx/h           wm = phi/h
    am = 2(vm-v0)/h            alpham = 2(wm-w0)/h
    Rm = Felastic(xm,Qm,Um) + Finertia(xm,Um,vm,wm,am,alpham) - Fmid

Fmid is an explicitly supplied spatial dead nodal force evaluated at the step
midpoint. There are no follower loads, couples or hidden load-time sampling.
Elastic forces come from the existing retained 24-coordinate potential with
moment elimination only; no static cell-spin equilibrium is imposed.

With P selecting translations and cell spins, the exact stage Jacobian is

    J = (Kelastic + Kinertia_configuration) G
        + Cinertia_velocity P/h + 2 M P/h^2

G has translation blocks I/2, trace blocks Jleft(psi), and cell blocks
Jleft(phi/2)/2. Kelastic is the spatial force derivative, including the existing
minus-one-half-skew(moment) BCH correction on every rotation block.

Endpoint physical fields are x1=x0+dx, U1=Exp(phi)U0, v1=2vm-v0 and w1=2wm-w0.
Free endpoint traces Q1 are then solved from Felastic_trace(x1,Q1,U1)=0,
initialized at Qm, without moving x1 or U1. Clamped traces remain fixed.
The stage forces and inertia remain separate from endpoint elastic forces and
endpoint energy in the receipt. Endpoint trace equilibrium is not inferred
from midpoint equilibrium or imposed by adding trace mass.

This is a proposed second-order Lie-midpoint development method. It is not
claimed to be variational or exactly energy/momentum conserving on nonlinear
trajectories. General temporal order, nonlinear energy/momentum, multi-element
behavior, material history, restart codecs and beam-shell joints remain open.

## Transactions and bounds

Use a distinct method schema and model fingerprint. Reuse only the existing
bounded Newton/transaction framework and immutable state layout, never relabel
backward-Euler states as accepted midpoint input. Every evaluation recovers the
endpoint traces, so replay has no hidden accepted trace cache.

Stage bounds: at most 16 Newton updates, 128 evaluations, ten line-search
attempts per update. Each endpoint trace recovery is capped at eight updates,
64 elastic evaluations and ten line-search attempts. Rotation increments must
remain below 0.9 pi. Existing relative-frame guards also remain active. Step
size is finite, positive and at most 0.1 in this small development profile.
Both stage and free endpoint trace residuals must satisfy normalized 1e-11.
There is no automatic retry or cutback. Failed trial/reconstruction leaves the
committed checkpoint unchanged; commit requires fresh deterministic replay.

These are small correctness tests, not resource/performance runs. Any later
heavy wave requires a separate immutable request and administrator ledger
approval under the workspace resource policy.

## Checks before acceptance as a research checkpoint

- Reference effective matrix and full nonzero-state analytic stage Jacobian.
- Actual straight axial steps against the separately authored math-only
  midpoint recurrence at 4, 8 and 16 steps, including work and temporal error.
- Curved coupled loading, reversal/unloading, retained spin inertia and
  independently checked endpoint algebraic balance.
- Observer covariance, free translation, deterministic fresh runs and replay.
- Schema separation, altered receipts, late endpoint failure, bounded solver
  failure, discard, and unchanged committed state on failure.
- No modifications to prior implementation/evidence or production paths.

The reference and new implementation have the same agent author. Separate
equation reconstruction is useful testing, not independent scientific review.

## Observed development result

The initial 20 midpoint tests passed in 29.40 seconds. After adding explicit
endpoint update/line-search failure injections and comparing actual canonical
receipt bytes (not just hashes), the combined midpoint, temporal-reference,
backward-Euler and finite-inertia suites passed **73 tests in 46.48 seconds**.
The midpoint suite contains 22 of those tests. These are ordinary small unit
tests, not a performance benchmark, resource wave or formal two-cycle run.

The actual retained-spin beam agrees with the separately implemented axial
midpoint recurrence on 4/8/16 steps. The joint displacement/velocity errors
against the analytic semidiscrete pulse response are respectively about
9.49591%, 2.56651% and 0.654939%. The last two partitions exhibit the expected
second-order axial behavior. This does not establish general curved nonlinear
temporal order. Endpoint energy and midpoint external work satisfy the axial
work identity; this is not a nonlinear energy-conservation claim.

Straight and curved trials retain nonzero elastic cell torques balanced by
inertia. Free endpoint trace forces were reconstructed from the elastic
potential and checked separately from stage forces. A small curved/coupled
step passes velocity-reversal symmetry, and a constant observer transformation
preserves both stage and endpoint fields. Two fresh model instances in one
process produced byte-identical four-step curved receipts; this is not a
fresh-process qualification cycle or an independent checker comparison.

Changed/rehashed endpoint receipts, incompatible backward-Euler states,
foreign transactions, exhausted step budgets, injected endpoint solver
failures and late commit reconstruction failures are rejected without changing
the committed checkpoint. Existing production and prior research files have
no delta relative to this step's parent. Only this plan, its new research
module and its new test are added. No resource request was consumed, no heavy
run launched, and no canonical qualification aggregate produced.

Next: a separately specified small curved/coupled temporal-convergence and
energy/momentum study, including noncommuting rotations and a separate
reference calculation. Preserve this checkpoint before any resulting method
correction. Dynamic multi-element assembly, material-state parity, restart,
general loads and beam-shell connections still require further work and
independent review. Production use remains unauthorized.
