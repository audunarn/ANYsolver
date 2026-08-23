# E4-PL-Q1B: Nonintrusion stability and locking qualification plan

## Authority and purpose

Q1B is the separately reviewed plan authorized by merged Q1AA terminal
`PROVISIONAL_GO_E4_PL_Q1AA_Q1B_PLAN`. It starts from commit
`be64f1d7f284bfa044e8dd4b40bece29e7311f44`, tree
`b412998399c3fa0bc5d40bd4658dbea77ab945ab`. Q1AA closes the registered
local transport, algebra, support, KKT, reaction, and recovery obligations;
Q1B addresses only their behavior after multi-element assembly.

This commit is plan-only. It does not execute Q1B, construct candidate
matrices, import mechanics, or authorize production. Future Q1B execution
requires a separate user request after this packet is independently accepted
and merged.

## Frozen scope

The future campaign is research-only. Candidate assembly, checking, runners,
and evidence remain under `docs/reference_cases` and `tests`. The production
`ShellElement`, public APIs, selectors, serialization, recovery, dependencies,
workflows, and defaults remain unchanged.

Q1B covers:

- assembled stiffness symmetry and supported positive definiteness;
- a mesh-independent supported energy/coercivity quotient over frozen mesh
  families;
- affine assembled patch reproduction and non-affine refinement behavior;
- mixed/condensed assembled solution parity;
- transverse-shear and drilling-locking behavior through `t/L=10^-6`;
- numerical PL/hourglass energy and drill participation trends; and
- strict separation of numerical diagnostics from physical loads, reactions,
  resultants, and recovery.

Eigenvalue buckling, geometric stiffness, modal or transient dynamics,
nonlinear response, coupling, orthotropy, laminates, DNV qualification,
production integration, and public-interface changes are excluded.

## Frozen assembled campaign

The future implementation constructs the accepted Q1AA local operator once
per base element in source numbering and assembles numbered elements only by
the frozen transport/congruence maps. It may not reevaluate identical local
fields after renumbering or tune `gamma_PL=G` or `epsilon_hg=10^-3`.

The campaign uses six geometry families: affine square, affine
parallelogram, non-affine trapezoid, tapered skew, and both hostile asymmetric
families. Stability and patch meshes use refinements `1,2,4,8`; locking strips
use `4,8,16,32` elements and thickness ratios `10^-2` through `10^-6`.
Supports act only on physical `T5` coordinates. Loads lie in `range(T5)`;
direct drilling moments and nonzero prescribed drill rotations are forbidden.

The admissible continuous class is `G1_PLANAR_BILINEAR_SHAPE_REGULAR`: every
element map is `F_e(r,s)=sum_i N_i(r,s) X_i` on `[-1,1]^2`, has positive
Jacobian everywhere, `sigma_min(J)/sigma_max(J)>=1/4`, and centre-relative
Jacobian variation at most `1/2`. Each component is edge-connected,
conforming, and consistently counterclockwise. Its diameter is normalized to
one and `h_e=sqrt(area_e)`. Refinement is the exact uniform parent-space
one-to-four subdivision; shared child-edge coordinates must be byte-identical.
The six named families are mandatory regression samples, not a substitute for
the required domain-wide certificate.

For every component, remove its six analytical rigid motions with the frozen
lumped nodal metric `W_c`:

`q_perp=(I-R_c(R_c^T W_c R_c)^-1 R_c^T W_c)q`.

The candidate-independent Reissner-Mindlin/drill norm is the positive `2x2`
quadrature sum

`||q||_V,h^2=sum_e int_e(epsilon^T A epsilon + kappa^T D kappa + gamma^T A_s gamma + G t [delta^2+h_e^2 grad(delta).grad(delta)]) dA`,

where `delta=theta_n-0.5(v_,x-u_,y)` and all fields use the frozen Q1R
engineering ordering. On the supported, component-wise rigid quotient,

`alpha_h=min(q_perp^T K_h q_perp / ||q_perp||_V,h^2)`.

An interval branch certificate over the complete `G1` shape domain must prove
one outcome-independent `alpha_*>=1e-6`; every registered mesh must satisfy
`alpha_h>=alpha_*`. Finite sampled positivity alone cannot pass this gate.

Outcome-independent gates are:

- supported assembled symmetry error at most `1e-12` and strictly positive
  supported energy quotient;
- affine patch relative residual at most `1e-10`;
- non-affine errors nonincreasing under refinement and at most `2%` on the
  finest mesh;
- locking-strip analytical displacement error below `2%` and response-ratio
  spread below `0.5%` across thickness;
- mixed/condensed solution and work residuals at most `1e-10`; and
- PL/hourglass energy fraction and drill participation nonincreasing under
  refinement and each below `1%` on the finest mesh.

The locking benchmark is the flat strip `[0,1]x[0,0.1]`, Q1R material
`E=15, nu=1/4`, clamped physical coordinates at `x=0`, free drilling
coordinate, and a consistent `x=1` edge traction of total transverse force
one. Its reference is `w_EB=F L^3/(3 E I)`, `I=b t^3/12`, and its response
ratio is `abs(w_FE/w_EB)`. Non-affine convergence uses the fixed physical
load `p(x,y)=1+x+2y`, left-edge physical clamp, and the energy-norm difference
between a level and the prolongated next level. Patch residuals are normalized
by the analytical physical boundary-traction norm; mixed/condensed solution
and work differences use the Reissner-Mindlin/drill norm and physical work.
Zero reference denominators require exact-zero numerators or yield BLOCKED.

Define `E_num=E_PL+E_hg`, energy fraction `E_num/E_phys`, and drill
participation `sqrt(E_delta/E_phys)`, with `E_delta=int G t delta^2 dA`.
For each sequence and the levelwise maximum, monotonicity means the next value
is no larger than the previous value plus `1e-12*max(1,previous)`.

Numerical reactions are not required to vanish. With
`K=K_phys+K_PL+K_hg`, report separately
`r_phys=K_phys q-f`, `r_PL=K_PL q`, `r_hg=K_hg q`, and
`r_total=r_phys+r_PL+r_hg`. The support multiplier reaction must have zero
`QD` projection; nonzero internal `r_PL` and `r_hg` are permitted diagnostics.
The exact categorical failure is contamination: numerical residuals appearing
in physical `N/M/Q`, stress, yield, fatigue, code-check recovery, or being
reported as physical support reactions.

## Execution authority and runtime

Future Q1B uses three parallel shards: assembled stability, locking/refinement,
and nonintrusion/recovery. Every child receives one numerical-library thread,
a 600-second wall limit, 24 GiB memory limit, a fresh external directory, and
exclusive output creation. There is no automatic retry. An independent
checker reconstructs assembly from frozen local evidence without importing
the producer.

Two complete fresh cycles are mandatory. Canonical cycle aggregates must be
byte-identical. Partial logs remain external and can never become canonical
evidence. No implementation, test, contract, case, tolerance, or authority
input may change after the first registered process begins.

## Stages and terminals

This preregistration uses exact `PLAN6`. The future program uses exact
`IMPLEMENTATION11`, `CONTRACT3`, and `OUTCOME11` extents frozen in the plan
contract. Every review is canonical five-key JSON and independent of the
artifact author. One plan-only correction, one static implementation
correction, and one contract correction are allowed; no post-execution
correction is allowed.

First-match terminal precedence is:

1. `BLOCKED_E4_PL_Q1B_AUTHORITY_OR_REVIEW`
2. `BLOCKED_E4_PL_Q1B_IMPLEMENTATION_CONTRACT_OR_NONDETERMINISM`
3. `NO_GO_E4_PL_Q1B_ASSEMBLED_STABILITY_OR_COERCIVITY`
4. `NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT`
5. `NO_GO_E4_PL_Q1B_NONINTRUSION_OR_RECOVERY_SEPARATION`
6. `UNCLASSIFIED_E4_PL_Q1B_BOUNDED_ASSEMBLED_EVIDENCE`
7. `PROVISIONAL_GO_E4_PL_Q1B_LINEAR_STATIC_INTEGRATION_PLAN`

The provisional GO authorizes only preparation of a separately reviewed,
opt-in linear-static integration plan. Every terminal retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; Q1B execution and production use
remain unauthorized by this plan-only commit.
