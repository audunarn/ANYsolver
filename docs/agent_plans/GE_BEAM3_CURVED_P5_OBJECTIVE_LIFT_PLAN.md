# P5: objective curved mixed mechanics — preparatory derivation

This successor continues the complete GE-B3 programme: straight and curved
standalone mechanics, nonlinear sections and state, loads and dynamics,
packaging, and an objective finite-rotation beam-shell connection. Its first
task is to establish a viable curved discrete functional. A reference-frame
pass alone cannot establish those mechanics or the complete programme.

Base: `b4317fb6153b38045f511ec3245b093f9e6bcb60`, tree
`304da60a1bd2d1c9faf28c923a838f3fe566ef8b`. Accepted P4 closeout:
`e59670ec1e69c0aba4e4027aaa271efa91e46b8d`, tree
`a55c7bdd2e4a431d4db275d30ba6fbd35d4890fa`. The P3/P4 preservation refs,
canonical evidence, and external request records remain authority inputs.

Proposed candidate: `CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_V1`.
Study: `study_ge_beam3.curved_objective_lift_preparation_v1`.
This is a derived candidate, not an assertion that the publication prints this
three-node curved packaging. The name distinguishes it from the reserved P4
reference identity. No qualified formulation ID is issued here.

## Source and derivation status

Use the already preserved Humer–Steinbrecher–Pechstein v3 PDF, 2,646,466 bytes,
SHA-256 `76AA9EDDDAE2EE16B47BF4E8255BDAA81678164B899E663E0B882B11C39BDB1E`.
Its printed PDF equations (30)–(31), (43)–(46), pages 8, 10–12, supply the
mixed complementary energy, discrete moment work, hybrid vertex rotations,
and multiplicative rotation framework. The arXiv HTML equation numbers
differ from this frozen PDF and must not silently replace its equation map.
Source: https://arxiv.org/abs/2605.04573v3 .

The interpolation below, its coupled-section extension, exact elimination,
reversal, and load derivatives are repository derivations. They require an
independently authored equation reconstruction and review before candidate
implementation freeze or formal execution. Preparatory algebra probes are
permitted and cannot issue a scientific qualification terminal. All initial
records must honestly mark independent review as pending.

## Proposed objective lift

Keep the accepted P4 quadratic curve `r0(xi)`, physical nodal triads, and
piecewise smooth material frame `R0(xi)`. On each half `[-1,0]` or `[0,1]`,
write linear endpoint interpolation as `I_c`, with interval width `h=1`.
The 18 external variables are positions `x_i` and authoritative physical
vertex rotations `Q_i`. Introduce one spatial relative rotation `U_c` per
half and six material moment coordinates per half.

Define

```
r_h = I_c x + U_c (r0 - I_c X)
Q_h = U_c R0
z_c = (U_c^T (x_R-x_L) - (X_R-X_L)) / h
gamma(xi) = R0(xi)^T z_c / J0(xi)
kappa_interior = axl(Q_h^T Q_h,s0) - kappa0 = 0
ell_L = -Log((U_c R0_L)^T Q_L)
ell_R = +Log((U_c R0_R)^T Q_R)
```

`r_h` reproduces the endpoints, is quadratic on each half, is continuous
at node 2, and reproduces the exact P4 stress-free curve. Under a superposed
proper rotation `G` and translation `a`, use `x_i'=G x_i+a`, `Q_i'=G Q_i`,
and `U_c'=G U_c`; then `r_h'=G r_h+a`, `Q_h'=G Q_h`, with invariant
material strains and jump work. This is an explicit interpolation, not a
fitted chord-length correction or empirical stabilization.

At a straight reference with equal halves, the lift vanishes and the
functional must agree with the accepted P3 two-cell formulation after the
local-rotation coordinate change `Q_cell=U_c R0`. Agreement must include
coupled sections, moments, energy, residual, tangent, and recovered fields.

The alternative `r_h=sum N_i x_i`, with one relative constant rotation per
half, is a diagnostic control. Test its linear force-strain nullspace before
selecting it: retaining a quadratic reference does not itself guarantee a
suitable thin-beam limit. Neither diagnostic result may relax acceptance.

## One coupled-section functional

For a fixed symmetric positive-definite elastic section
`C=[[A,B],[B^T,D]]`, moment interpolation is `m=L_L m_L+L_R m_R` in the
physical material frame. Use the partial Legendre transform

```
Pi_c = integral [gamma^T A gamma/2
                 -(m-B^T gamma)^T D^-1(m-B^T gamma)/2] ds0
       + ell_L^T m_L + ell_R^T m_R.
```

Curvature resides in the weak jump pairing for this trial space. Physical
curvature recovery is `D^-1(m-B^T gamma)`, not the identically zero interior
rotation gradient. Physical force is `A gamma+B kappa`. The recovered moment
equals `m`. All six components participate in the same functional.

Before the nonlinear local solve, eliminate the 12 moment coordinates
analytically. Let `L=[L_L I,L_R I]`, `V=R0^T/J0`, and

```
F = integral V^T (A-B D^-1 B^T) V ds0
H = integral L^T D^-1 L ds0
J = integral L^T D^-1 B^T V ds0
e = J z + [ell_L;ell_R]
m_endpoints = H^-1 e
Pi_c_reduced = z^T F z/2 + e^T H^-1 e/2.
```

`H` is positive definite for an admitted reference and SPD section. This
exact algebraic elimination reduces the nonlinear local system to six
rotation coordinates, without changing the stationary solution. Derive
both first and second variations, including variation of the lifted
position field. Use analytic SO(3) derivatives or exact forward derivative
propagation; finite differences are diagnostic checks only.

The reference linearization has 24 displacement/rotation variables before
rotation condensation, expected rank 18 and six rigid nulls. The final
18-variable element has expected rank 12, six rigid nulls, and a positive
12-dimensional quotient. The full 36-variable mixed Hessian has expected
inertia `(18 positive,12 negative,6 zero)`. Verify these counts; do not
force them by projection or diagonal regularization.

## Transport, work, and transactions

Reversal interchanges nodes 1 and 3 and the two halves. Use the P4 proper
frame map `S=diag(-1,1,-1)`, `R0_rev=R0(-xi) S`, `Q_rev=Q_perm S`, and
`U_rev=U_other_half`. Strains/resultants transform by `T3=-S`, section by
`C_rev=diag(T3,T3) C diag(T3,T3)^T`, and endpoint moments by `T3` plus
endpoint permutation. Endpoint logarithms transform by `S` and exchange
their signed roles, preserving the scalar jump work.

Because `r_h` depends on `U_c`, distributed-force work creates internal
rotation loads. Those loads must be included in the local stationary
equations and consistent tangent, mass reduction, and recovery; nodal-only
pressure/load interpolation would be incorrect. This obligation is a
required later parity gate, not an optional optimization.

Local rotations are solved at every trial configuration, including load
work. Line-search/cutback/rejected-state paths must discard all trial
rotations and section states. The elastic elimination above does not
authorize using a plastic tangent in place of an elastic complementary
potential: nonlinear sections require their own consistent station
potential/state protocol before exposure.

## Ordered gates and execution

1. Prepare the equation map and small algebra probes. Bind exact source,
   base, protected files, probe inputs and results. Resolve implementation
   discrepancies and record pending review explicitly.
2. Independently reconstruct/review the derivation and freeze a candidate
   contract, cases, tolerances, solver bounds, and quadrature policy.
3. Implement the private finite functional and analytic derivatives.
   Verify stress-free curved state, arbitrary rigid motion, reference
   rigid modes, coupled sections, reversal, P3 straight limit, local
   stationarity and full/condensed Hessian equality.
4. Independently verify quadrature and mechanics, then freeze a runner and
   one-use resource authority. Rehearsal precedes two formal cycles.
5. Qualify curved arches, rings and compatible spatial chains, slenderness,
   nonlinear load paths and post-buckling, state/restart, loads, consistent
   mass, modal/prestressed modal, buckling, and physical recovery.
6. Qualify installed-wheel standalone exposure. Separately qualify the
   objective beam-shell connection, including eccentric curved attachments.

Preparation uses small normal unit tests only. Formal waves retain one
numerical-library thread per child, 24 GiB per process tree, 600 seconds
per child, three concurrent children maximum, and 1,800 seconds per wave.
Checkpoint inactivity limit is 300 seconds. Terminate complete process
trees, preserve partial logs, never automatically retry or reuse a request.
Resource-heavy tests require the workspace ledger and global slot.

No automatic PASS follows from an algebra probe. Pending independent review,
missing source derivation, unsupported routing or state safety, or a local
identity failure prevents implementation/formal qualification freeze.
Two deterministic formal cycles and empty independent correctness findings
are required before any qualification terminal. `main`, public selectors,
defaults, releases, and accepted beam/shell mechanics are outside this
preparatory extent. All stages retain
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` until explicitly superseded.
