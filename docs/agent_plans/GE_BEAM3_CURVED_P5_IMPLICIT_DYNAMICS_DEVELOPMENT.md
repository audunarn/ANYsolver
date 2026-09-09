# P5 retained-spin implicit transaction — preparatory development

Base `4f7e48d1a3a81d5e33f1449068fb936beed2c07a`, tree
`e1bf410ff3cf88cebe144484ffa10f413b671bc3`. Add a research-only single-macro
implicit path, tests and this derivation. No existing source, accepted evidence,
mechanics, defaults or kinetic model changes.

## Why this first integrator

Use a first-order backward-Euler Lie update as a bounded implementation and
transaction check, **not** as the final production time-integration policy.
It enforces the massless vertex-trace equations at each accepted endpoint and
retains cell-spin inertia. It provides a direct check of the unified residual
and derivatives before higher-order time integration and independent review.
It is dissipative, not energy/momentum conserving or a variational integrator.
No transient engineering qualification follows from this preparation.

Full unknowns are 24: nine nodal translations, nine algebraic vertex rotation
increments and six retained cell rotation increments. Configurations are
authoritative matrices, not accumulated rotation vectors. With step h:

```
x1 = x0 + dx;   Q1 = Exp(psi) Q0;   U1 = Exp(phi) U0
v1 = dx/h;     omega1 = phi/h
a1 = (v1-v0)/h; alpha1 = (omega1-omega0)/h
F = F_elastic(x1,Q1,U1) + F_inertia(x1,U1,v1,omega1,a1,alpha1) - F_nodal
```

F_elastic is the existing elastic P5 complementary potential with moment
variables eliminated exactly, but **without** statically solving/eliminating
the six cell rotations. The analytic 24x24 energy Hessian is converted to the
derivative of spatial moment components with the existing BCH correction
`H_rotation -= 0.5 hat(moment)` for all five rotation blocks.

For increments z, let G map increment changes to current spatial rotation
increments using the left Exp Jacobian. Let P select only nodal translations
and cell spins, excluding algebraic trace rates. The exact Newton matrix is

```
dF/dz = (K_elastic_spatial + K_inertia_configuration) G
         + C_inertia_velocity P/h + M P/h^2.
```

The method uses no numerical frame differentiation, static dynamic mass
condensation, pseudoinverse or artificial trace inertia. Spatial force/length-
scaled moment residuals retain the 1e-11 criterion; derivatives are tested at
1e-7. Increment norms at every rotation block must remain below 0.9 pi.

## Transactions and bounded scope

Initialize a stress-free straight/curved reference with zero velocities.
Allow whole-node clamps and spatial dead nodal forces only in this first
probe; other load/state/section interfaces remain explicit future work.
The section is linear coupled SPD 6x6, not a history-bearing plastic adapter.
Each step is at most 0.1 time units, at most 16 Newton updates, ten backtracks
and 128 evaluations. No automatic retry or step adaptation. Initial material
chart guards remain in force. Trial state includes matrices, physical velocity
fields, time/epoch and a model fingerprint; no fabricated trace angular rate.

Commit requires ownership, unaltered trial hash, current origin identity and
fresh reconstruction of the same step from its retained origin. State publishes
atomically only after equilibrium and reconstructed bytes agree. Discard,
failure and exceptions leave the committed checkpoint unchanged. Replay checks
the accepted origin and committed state; no production restart loader is added.

## Small verification plan

Check zero-state effective matrix, nonzero-increment directional Newton matrix,
pure axial response against the linear backward-Euler pencil, curved/coupled
one-step equilibrium, frame covariance, massless trace balance and true dynamic
cell balance (elastic cell torque need not vanish by itself). Check failed-step
rollback, discard/retry-by-explicit-caller, foreign/stale/altered/rehashed trials,
fresh replay, deterministic bytes and invalid bounds. These are ordinary small
correctness fixtures, not a resource/performance wave.

Remaining: second-order/geometrically consistent time-integration choice,
energy/momentum and step-refinement studies, free-body/spinning cases, material
history integration, multielement assembly, loads/couples, dynamic restart,
prestressed modal and beam-shell joints. Preserve the original complete goal.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Implemented result

The research path now solves one macro's full retained-spin implicit balance
with a consistent analytic Newton matrix. It never calls the static local spin
solver. Trial/commit/discard and accepted-origin replay are implemented with
atomic publication, independent copied receipts, complete model/state hashes
and bounded iteration/evaluation counts. Stored physical velocities comprise
nodal translations and cell angular velocities; no fictitious trace rate or
inertia is stored. Time must advance in its represented floating-point value.

The focused suite passed **20 tests in 7.14 s**. The final targeted run including
finite inertia, existing mass/modal-chain and immutable onset-closeout checks
passed **77 tests in 13.12 s**. `git diff --check` passed. Small correctness tests
only: no formal authority request, heavy wave, push, release or default change.

Verified development cases include:

- Exact reference-linear effective matrix `K+M/h^2` and spatial Exp Jacobian.
- Nonzero-increment directional derivative of the complete dynamic equations.
- Pure axial multistep response matching the linear backward-Euler pencil.
- Curved coupled loading, reversal and unloading using the prior velocity.
- Dynamic cell torque balanced by inertia rather than statically forced zero.
- Massless free vertex-trace balance at the accepted endpoint.
- Constant observer-frame covariance and unconstrained free-body translation.
- Fresh accepted-origin reconstruction, deterministic discarded-step repetition,
  public-copy isolation, failure rollback, and foreign/stale/changed/rehashed
  state or metadata rejection.

These checks are same-author research evidence, not an independently authored
mechanics/time-integration review. The finite-rotation energy/momentum drift,
time convergence and long-time stability of this first-order method are not
qualified. No such claims are inferred from the single-step residual checks.

The path uses the ordinary-coordinate single-macro elastic potential; it does
not replace or claim qualification from the compensated fine-mesh static
assembly. Compensated multielement dynamic state, nonlinear station histories,
distributed loads/couples, dynamic restart codecs and shared beam-shell rotation
constraints remain explicit integration work. The 18 external DOFs remain the
intended interface; local dynamic spins require proper time-step-aware internal
condensation/solver orchestration before production exposure.
