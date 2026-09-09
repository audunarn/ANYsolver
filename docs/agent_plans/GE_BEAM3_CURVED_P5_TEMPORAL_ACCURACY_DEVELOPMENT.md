# P5 temporal-accuracy separation — preparatory reference

Base `f687f46de61b5498567b6d647ca4fad6ee873524`, tree
`a3ebbe22f516a7767875620b1e0c0135679d5bb0`. Preserve all existing mechanics,
integration probes and evidence. Add one standalone standard-library axial
time reference, its small comparisons, and this result record.

The 24-coordinate beam has an exact uncoupled axial subspace on a straight
reference with diagonal section/inertia. For two unit rod halves, a clamped
left vertex leaves two translations. Integrating linear shape products and
their derivatives gives, without importing beam matrices:

```
K = EA [[2,-1],[-1,1]]
M = rho/6 [[4,1],[1,2]]
lambda = 6 EA/(7 rho) (5 +/- 3 sqrt(2))
mode = (1, -/+ sqrt(2))
```

Use EA=100, rho=2, tip force 0.1 on [0,0.08], zero thereafter, final time 0.16.
All time partitions align the force switch. Modal sines/cosines give the
closed semidiscrete response from rest and Duhamel subtraction gives the
pulse response. This is an exact *spatially discretized* axial reference, not
a continuum/modal qualification claim for the complete beam.

First verify the backward-Euler recurrence and its dissipative work identity:

```
E1-E0 - h F1.v1 = -(dv.M.dv + h^2 v1.K.v1)/2.
```

Also implement the independent linear implicit-midpoint recurrence as a
temporal comparison only; it is not yet the finite-rotation beam integrator.
Midpoint preserves the linear quadratic energy/work identity. Compare both
methods with the closed modal solution on 4/8/16/32 partitions, using the
relative joint displacement/velocity energy norm. Do not confuse decreasing
time error or favorable midpoint results with existing beam qualification.

Run the actual single-macro backward-Euler beam on 4/8/16 partitions and
require its states to match the separate linear recurrence under the same
force schedule. Check the beam energy/work loss from its own returned elastic
and kinetic energies. These short single-macro correctness fixtures are not
performance, large-mesh or formal qualification runs. No resource request,
retry of consumed authority or threshold relaxation is allowed or needed.

The result will guide a properly constrained higher-order dynamic successor.
No final time-step policy, error ceiling, energy conservation or full transient
qualification is granted. General finite-rotation, curved, coupled, material,
multielement, restart and beam-shell connection gates remain open.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Observed temporal results

Relative joint displacement/velocity energy-norm error at t=0.16:

| Steps | Backward Euler | Linear midpoint reference |
| ---: | ---: | ---: |
| 4 | 44.6373% | 9.49591% |
| 8 | 29.5678% | 2.56651% |
| 16 | 17.2265% | 0.654939% |
| 32 | 9.29023% | 0.164589% |

The last halving gives approximately first- and second-order behavior,
respectively. At 16 steps the backward-Euler energy at the final time is
25.3221% below the exact pulse-response energy. The linear midpoint value is
0.342737% below that reference: it conserves its own discrete energy after
the force switches off, but its earlier discrete external work is not exactly
the continuous pulse work. These different statements must not be conflated.

The actual 24-coordinate beam reproduces the independent two-coordinate
backward-Euler displacement, velocity and dissipative work identity on all
4/8/16 partitions. The discrepancy is therefore temporal damping/error in
this diagnostic method, not evidence of a new axial spatial-mechanics defect.
All beam steps meet the unchanged 1e-11 residual rule and fresh replay checks.
The 32-partition results in the table are the tiny linear reference only;
no 32-step beam run or broad transient qualification is implied.

The focused temporal suite passed **9 tests in 8.39 s**. With unchanged
implicit-transaction and finite-inertia suites, **51 tests passed in 17.84 s**.
`git diff --check` passed. The reference imports only `math`, reconstructing
its stiffness, mass and analytic eigenpairs without beam code or cached
operators. It is separately implemented but still same-author verification;
independent scientific review remains pending.

## Consequence for the next successor

Do not adopt the first-order path as the final dynamic integration policy or
hide its damping by loosening an engineering tolerance. Preserve it and the
reference as regression evidence. Implement a second-order retained-spin
successor with compatible finite-rotation updates, analytic stage equations,
and endpoint recovery of the massless vertex-trace equilibrium. Simply
averaging endpoint trace rotations would leave nonlinear algebraic constraints
unproven. Retain full dynamic cell inertia, atomic state receipts, fixed-origin
replay, bounded Newton/recovery loops and explicit failure.

The finite-rotation successor must reproduce the linear midpoint reference and
then demonstrate curved/coupled temporal convergence and appropriate energy/
momentum behavior. Linear reference success alone cannot qualify it. No
existing integrator, mechanics, scientific evidence, default, API or package
was changed in this step; no heavy/formal run was launched.
