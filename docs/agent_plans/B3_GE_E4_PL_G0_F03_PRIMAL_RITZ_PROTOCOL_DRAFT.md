# F03 independent continuous-primal Ritz reference: proposed contract

22 September 2026. Independent mechanics review draft, not an execution
registration. This file proposes a bounded numerical reference for the
classical rectangular finite-pad law in
`B3_GE_E4_PL_G0_F03_CONTINUOUS_PRIMAL_REFERENCE.md`. It authorizes no solve,
changes no consumed result, selects no production multiplier space and
does not close F03/G0B or permit G1. The implementation and final runner
still require independent review and a clean committed source freeze.

## Exact inventory and independence

Use physical coordinates X=(x-.5m)/(1m), Y=2y/(1m), and the vector basis
whose scalar factors are (1-X²) P_i(X) P_j(Y), with i=0,...,n-2 and
j=0,...,n. Register exactly n=4,8,12,16,24. The respective primal counts
are 30,126,286,510,1150; there are exactly three additional root duals.
The two displacement components are independent. No y-edge displacement,
beam slope, or absolute tip condition is added.

These spaces are nested and satisfy both vertical panel edge conditions.
The physical trace A and its first two s derivatives are evaluated by
independent rectangular-pad polynomial moments. Do not import candidate
Q4/CST assembly, clipped-host integration, beam FE interpolation, or finite
line-multiplier matrices. Preserve shell and eliminated-beam stiffness,
the physical root matrix C=A(0), load vector, basis indices, coefficients,
root duals, integration metadata and all recovery arrays.

Use one canonical equilibrium per n. Always assemble a second integration
description at the same n; it is an integration crosscheck, not a second
equilibrium or an adaptive retry. Primary tensor orders are n+1 for shell,
pad and beam polynomial integrals, with load order48. Crosscheck orders
are n+3 and load64. Perform both descriptions for all five n values.
Shell/beam polynomial energy has degree at most2n in each integration
coordinate; pad yaw moments have degree at most n+1. Thus these orders
are degree-exact for the polynomial portions. The cosine load still needs
its separate check. No failed level may be dropped or rerun at a new order.

The degree cap alone does not ensure physical resolution. Rectangular pad
loading can leave slow convergence of the global polynomial shell field.
Any failed finest-level settling criterion yields an unresolved reference;
there is no automatic n>24 extension or extrapolated continuum result.

## Numerical scaling and integration gate

Keep L0=1m, F0=1MN, M0=F0 L0, ell=.46m,
U0=F0/(210e9*.07), E0=F0 U0. With K=Ks+Kb and positive Kii use

    Dii=sqrt(E0/Kii), R=diag(1/U0,1/U0,ell/U0),
    Kbar=D.T K D/E0, Cbar=R C D, fbar=D.T f/E0,
    H=[[Kbar,Cbar.T],[Cbar,0]], z=[D^-1 a,eta_hat],
    eta_phys=E0 R.T eta_hat.

This equilibration is a solver coordinate change, not a mesh-dependent
physical norm. All reported physical comparisons retain the fixed scales.
Apply the primary D and R to both quadrature descriptions; independently
rescaling the crosscheck would conceal differences.

Proposed mandatory limits, frozen before any reference solve:

| Quantity | Limit |
|---|---:|
| Relative Frobenius skew of Ks, Kb and K | 1e-12 |
| Relative Frobenius difference of scaled Ks, Kb and K across integration descriptions | 1e-11 |
| Cbar integration difference / max(1,norm(Cbar,F)) | 1e-11 |
| fbar integration difference / max(1,norm(fbar,inf)) | 1e-11 |
| Cbar smallest/largest singular-value ratio | at least1e-10 |
| Full unmodified scaled KKT condition number kappa2(H) | at most1e10 |
| kappa2(H) times normwise solve backward error | 1e-8 |
| Scaled stationarity infinity residual / max(1,norm(fbar,inf)) | 1e-10 |
| norm(R C a,inf) | 1e-10 |
| abs(2U-W)/max(E0,2abs(U),abs(W)) | 1e-10 |

Require a successful positive-definiteness check of the unmodified Kbar,
positive finite diagonal scales, and exactly three independent root rows.
Use full-matrix singular values for the KKT condition check; do not use a
one-triangle eigensolver on an unchecked asymmetric matrix. These are
numerical reliability gates, not a continuum inf-sup acceptance threshold.
Do not clip eigenvalues, add regularization, symmetrize a failed matrix,
remove root rows, or silently use a pseudoinverse.

Also bound amplification of integration differences without a second
equilibrium. With H+,b+ the higher-order description in the primary
scales, b=[fbar,0], sigma=sigma_min(H), define

    alpha=norm(H+-H,F)/sigma,
    delta=(norm(H+-H,F)*norm(z,2)+norm(b+-b,2)) /
          (sigma*norm(z,2)).

Require alpha<1 and delta/(1-alpha)<=1e-6. Record its ingredients and
the residual H+z-b+. This is a conservative perturbation check of the
scaled coefficient/dual vector, not a physical output error certificate.
For matrix differences use each block's own nonzero norm in the stated
relative checks; a zero block requires an explicit absolute scaled check.

Before registered work, unit checks must cover rigid translations/yaw,
constant and mixed polynomial pad moments, A/A'/A'' (including the
Eulerian yaw subtractive mean term if that route is used), physical
coordinate chain factors, root rank, and virtual-work scaling. At fixed
s=0,1/8,...,1 compare both quadrature descriptions of
L0^k R A^(k)(s) D, k=0,1,2, at relative Frobenius1e-11 with denominator
max(1,norm(primary,F)).

## Physical interface and support recovery

Use physical b=A u=(u,v,theta), without a separate beam discretization.
Set N=EA u', Q=G As(v'-theta), M=EI theta'. Fixed rectangular pads give
A:H1->H2, so these resultants belong to H1 and the following recovery is
legitimate for this law:

    density=(N', Q'+q, M'+Q),
    atom0=(N0,Q0,M0)-eta_phys,
    atom1=-(N1,Q1,M1),
    beam_root_reaction=-eta_phys.

These are multiplier residual contributions: +mu on the beam, -A*mu on
the shell. External interface-force signs reverse. Retain signed physical
density and atoms separately. Root elastic traction plus atom0 gives the
total root reaction; do not add atom0 again. Atom1 is an interface action,
not an absolute tip support. Do not impose N1=Q1=M1=0.

Store the density's Legendre coefficients on 2s-1 and the explicit known
cosine contribution .25MN/m*cos(2pi s) to its Fy component. The constant
1MN/m contribution belongs to the polynomial coefficient. Store both
physical atoms, all three root resultants, tip physical/scaled pose,
shell/beam/total energy and external work. Store the polynomial b,b',b''
representation needed for an independent recovery audit.

Recover each shell-edge wrench through declared restored variations.
With chiL=(1-X)/2 and chiR=(1+X)/2, use for each edge e the lifts

    chi_e*(1,0), chi_e*(0,1), chi_e*(-y,x).

They prescribe unit translation or unit rotation about global origin(0,0)
on that edge and zero displacement on the opposite edge. The third result
is a moment about that same origin. Evaluate the shell reaction functional

    Rs(z)=as(u,z)-<mu,A z>
         =as(u,z)+ab(b,A z)-lb(A z)+eta_phys.T A z(0).

Both independently evaluated routes must agree to1e-8 after division by
F0 or M0. Also add a fixed declared lowest-order Ritz basis variation to
each lift: the reaction must be unchanged to the same limit by discrete
stationarity. The finite-level edge wrenches are defined by these lifts;
do not silently replace them by pointwise polynomial boundary stress.
Their convergence is screened below. Global force/moment balance is an
additional1e-8 check, not an independent accuracy certificate: restoring
rigid variations can make that identity hold even for an inaccurate field.

Verify recovered beam virtual work on the unrestricted one-dimensional
Legendre test fields of degrees0,...,n+2 in each of the three channels,
with translations scaled by U0 and yaw by U0/ell:

    <mu,w> + ab(b,w) - lb(w) + eta_phys.T w(0) = 0.

Require maximum absolute work defect/E0<=1e-10. Include constant and
endpoint-nonzero tests; testing only clamped variations misses root atoms.

Report line-only and total wrenches on the four quarters and on
[0,1/32], [1/32,1/16], [15/16,31/32], [31/32,1]. The physical line moment
integrand about origin(0,0) is mu_theta+s*mu_y. Add endpoint atom force
and its lever-arm moment exactly once in the band containing that endpoint.
Check polynomial/Cosine band antiderivatives against fixed48/64 quadrature
to1e-10 of F0 or M0. A small net work or full-dual difference alone does
not bound sharp-band or endpoint-reaction errors.

## Independent continuous full-functional norm

Use the same full free-endpoint H1 trace norm as the prior classical
diagnostic, integral(z*w/L0+L0*z'*w')ds, L0=1m. Its Green kernel is
G(s,t)=cosh(min(s,t))*cosh(1-max(s,t))/sinh(1). For each channel, evaluate
the complete density-density double integral, twice the density-atom
cross term, and the analytic two-by-two atom Gram. Scale the physical
third density/atom component by1/ell exactly once; sum all three squared
dual norms. No structural stiffness or finite P1 test space defines this
norm, and no projection onto the old mortar grid is permitted.

Split the double-integral square at s=t into triangles. Always compute
orders48 and64 for density-density and density-atom integrals. Require

    abs(Q64-Q48)/max(abs(Q64),abs(Q48),(1000N)^2) <= 1e-10.

Use the order64 value only after that check passes. Preserve negative or
nonfinite squared norms as failures; do not clip them. An identically zero
coefficient/atom difference may be recognized exactly before quadrature.
Analytic unit tests include constant density, both endpoint atoms and
their cross term (coth(1),csch(1)), and at least a linear-density case.

For comparisons subtract density coefficients, explicit cosine amplitudes
and endpoint atoms before norm integration. The common cosine contribution
cancels exactly between Ritz levels. Retain each operand norm and the
difference norm. This gate evaluates internal Ritz convergence only;
comparison against saved finite-element functionals is a separate later
registration after this reference has passed its own checks.

## Nested identities and frozen settling screen

Embed coarse polynomial coefficients exactly by their (component,i,j)
indices, without reinterpolation. For consecutive levels compute the
fine-space energy distance A=.5*(a_f-P a_c).T K_f*(a_f-P a_c). Because
these are nested spaces with the same exact root law and load, require
U_f>=U_c-1e-10 E0 and

    abs((U_f-U_c)-A)/max(E0,abs(U_f)+abs(U_c)+abs(A)) <= 1e-10.

This extra monotonicity applies to the eliminated primal reference; it
must not be retroactively imposed on the competing FE/mortar refinements.
Preserve A and the field difference, but do not call either the remaining
continuum error or infer a Richardson order from the unequal n increments.

For each signed scalar use
r=abs(x_f-x_c)/max(abs(x_f),abs(x_c),1e-3*S). Require r<=.01 for BOTH
n12->16 and n16->24, and require the final absolute change not to exceed
the preceding change plus1e-5*S. Record every earlier change as well.
S is F0 for forces/atoms, M0 for moments, U0 for scaled pose and E0 for
energies. These preserve the existing10N,10Nm,6.802721088e-10m and
6.802721088e-4J near-zero settling allowances.

Screen root three-component reaction, left/right shell-edge wrenches,
tip scaled pose, shell/beam/total stored energy, all endpoint atom channels
and every total fixed-band wrench. Preserve line-only band quantities and
root elastic/interface partitions without substituting them for totals.
For the full functional require difference/max(operand norms,1000N)<=.01
on both final pairs, and final difference<=preceding difference+10N.

The eliminated gap is zero by construction and is not independent evidence
of reference convergence. Keep root compatibility and independent A/work
checks as numerical checks; do not award a physical gap-convergence pass
for a field defined to be b=A u.

## Evidence, terminal decisions and next gate

The final runner must preregister exact source/dependency identities,
all five basis cases and both fixed integration descriptions, one-use child
authority, numerical thread caps, per-case time/RSS limits and a serial
launch cutoff. Resource values require implementation review:1150 unknowns
alone does not bound pad/station evaluation temporaries. Each dense
1150-by-1150 float64 matrix is about10.1MiB; all temporaries must still fit
the independently enforced child limit. Save partial/failure artifacts and
never retry a consumed level or change quadrature after observing results.

Canonical adjudication requires the complete registered receipt inventory.
Use precedence FAILED_EVIDENCE, FAILED_EXECUTION, FAILED_NUMERICAL_SCREEN
(including conditioning, integration and norm-resolution failures),
UNRESOLVED_RITZ_REFERENCE, then PASSED_BOUNDED_PRIMAL_REFERENCE. Preserve
the individual failed predicates, not only a single aggregate label.
Independent postreview must recompute summaries from saved matrices,
coefficients, actions, density/atom representations and receipts without
reassembling or resolving the scientific cases.

A bounded reference pass means this independent sequence meets the frozen
internal checks and settling screen. It is not a rigorous continuum error
certificate or native qualification. Only after that pass, preregister a
saved-evidence comparison against all declared FE families/topologies using
the same signed outputs, bands and complete continuous functional norm.
Keep the old endpoint and joint-refinement HOLDs unchanged throughout.
