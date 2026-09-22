# F03 continuous finite-pad primal reference derivation

22 September 2026. Original derivation for the **classical in-plane
finite-pad diagnostic only**. This is not the native B3-GE/E4-PL model,
an executed reference, a multiplier selection or a passed G0B gate.
Independent mechanics review is required before numerical implementation.

## Exact physical law and admissible fields

The panel is Omega=(-.5,1.5) x (-.5,.5)m. Its displacement is
us=(ux,uy) in H1(Omega;R2), with both components zero on x=-.5 and1.5;
y edges retain their natural conditions. Let V denote that space.
The beam occupies I=(0,1)m and has independent Timoshenko fields
b=(u,v,theta) in the full space B=H1(I;R3). The supported subspace is
B0={b in B:b(0)=0}. Its slope v'(0) is not
restrained. No absolute tip restraint is added. Hermite nodal slopes in
the diagnostic discretization represent v'; they are not a fourth
continuous physical field or an additional essential root condition.

Let Q be the union of four fixed material offset squares with centres
(+/-.20,+/-.23)m and halfwidth a=.05m. Each area is4a²; total area is16a².
For rho=(xi,eta) define the area average

    <f> = (16 a²)^-1 integral_Q f(xi,eta) dxi deta,
    J = <xi²+eta²> = .20² + .23² + 2 a²/3.

The physical shell pose at station s is the linear operator

    (A us)_u(s)     = <ux(s+xi,eta)>,
    (A us)_v(s)     = <uy(s+xi,eta)>,
    (A us)_theta(s) = <xi uy(s+xi,eta)-eta ux(s+xi,eta)> / J.

This averages displacement over the actual pad areas and fits infinitesimal
physical yaw. It is not the four-point rail law, a geometric-normal lock,
or an artificial drilling degree of freedom. It agrees with the existing
finite-area operator definition, whose host clipping is only one numerical
way to evaluate these integrals. The independent reference must integrate
the same physical areas by another method.

Every translated square remains strictly inside Omega. In coordinates rho,
the integration domain and moment arms are fixed. Consequently, in the
weak sense, (A us)' is given by the same formulas with ux,uy replaced by
their x derivatives. There is no extra derivative of xi: xi is a material
offset from the moving station, not an independently fixed global x.

Cauchy-Schwarz bounds each area average by the L2 norm over its translated
support. Integrating in s and using the bounded overlap of these translated
supports gives

    ||A us||_H1(I) <= C(a,J,Q) ||us||_H1(Omega),

with a finite constant for the fixed positive-area pads. Thus A:V->B is
bounded. Endpoint evaluation is continuous on H1(I), so A us(0) is a valid
bounded three-component functional. This argument does not take a->0,
establish a uniform point-port limit, or qualify a three-dimensional shell
director map.

For these fixed rectangular pads a stronger property also holds. For each
vertical pad interval Yj, define one-dimensional averages

    F(x)=integral_Yj u(x,y) dy,  H(x)=integral_Yj y*u(x,y) dy.

Fubini and Cauchy-Schwarz give F,H in H1(-.5,1.5). For fixed horizontal
pad limits l=dx-a and r=dx+a define J0(s)=integral_l^r F(s+xi) dxi and
J1(s)=integral_l^r xi*F(s+xi) dxi. Their weak derivatives are

    J0'(s)=F(s+r)-F(s+l),
    J1'(s)=r*F(s+r)-l*F(s+l)-J0(s).

Both derivatives belong to H1(I), since their shifted arguments remain
inside the panel. Apply the same argument to H. Every component of A is
a fixed linear combination of these averages, proving the bounded map
A:H1(Omega;R2)->H2(I;R3). No trace of a two-dimensional displacement
derivative on a line is assumed. This stronger statement requires the
fixed positive rectangular pads and does not extend automatically to a
shrinking footprint, arbitrary shape or native finite-rotation pose law.

In an Eulerian boundary-flux implementation, differentiating the yaw
moment arm x-s contributes -mean(uy)/J. That term is already accounted
for in the reference-coordinate formulas and must not be omitted or
added a second time.

As a work/rigid-motion check, us=(tx-omega*y,ty+omega*x) gives
A us=(tx,ty+omega*s,omega). It is an operator check, not an admissible
nonzero field under the fixed panel supports.

## Energy and exact elimination

Use the same plane-stress bilinear form as the declared classical panel:

    as(u,z) = t integral_Omega eps(u).T Dplane eps(z) dOmega,

where eps=(ux,x,uy,y,ux,y+uy,x), t=.07m, E=210GPa and nu=.3.
For b=(u,v,theta), w=(p,z,psi), use the physical Timoshenko energy

    ab(b,w) = integral_I [ EA u' p' + EI theta' psi'
                          + G As (v'-theta)(z'-psi) ] ds,
    lb(w) = integral_I 1e6*(1+.25 cos(2 pi s))*z(s) ds.

A=.01m², As=.008m², I=8.333333333333333e-6m4 and G=E/[2(1+nu)].
There is no shell distributed load in this diagnostic. The small finite
element beam uses P2 u/theta and Hermite v as an approximation of these
fields; the reference must not inherit those trial spaces.

The exact constrained problem minimizes

    .5 as(us,us) + .5 ab(b,b) - lb(b)

over V x B with b=A us and b(0)=0. Its feasible set is in one-to-one
correspondence with

    V0 = {us in V : A us(0)=0}.

Elimination therefore gives

    Pi_primal(us) = .5 as(us,us) + .5 ab(A us,A us) - lb(A us),
    as(us,z) + ab(A us,A z) = lb(A z),  for every z in V0.

This equivalence is exact at the continuous level; it introduces no penalty
and makes no choice of finite line-multiplier space. The three root
conditions survive elimination. Dropping them, imposing v'(0)=0, or fixing
A us(1) would change the physical problem.

The panel Dirichlet boundary has positive measure; the plane-stress energy
is coercive on V under the usual Korn inequality. The beam term is
nonnegative and bounded through A. V0 is closed. The resulting positive
coercive variational problem has a unique displacement solution for the
declared load. This does not claim that a particular finite Ritz sequence
converges sufficiently fast to meet an engineering tolerance.

The root map has three independent components on V: prescribe any rigid
planar pose over the four root pads with a smooth cutoff equal to1 there
and0 at the supported panel edges. Its averages give arbitrary tx,ty,omega
at s=0. Thus the three root conditions are not a redundant surrogate for
the panel edge conditions.

## Work, root reaction and interface functional

Fix the orientation c=b-A us. A physical multiplier functional mu acts
on B with work <mu,c>. In the numerical diagnostic the gap is scaled by
D=diag(1,1,ell), ell=.46m. If Lambda acts on D c, then

    <mu,w> = <Lambda,D w>.

The third physical component is a moment; it includes ell exactly once.
Density coefficients and endpoint atoms are distinct measures. Raw scaled
coefficients are not automatically spatial moments or a unique physical
pointwise traction distribution.

Introduce a root multiplier rho through rho.T b(0). Stationarity on
unrestricted B reads

    ab(b,w)-lb(w)+<mu,w>+rho.T w(0)=0.

After elimination, retaining the root condition with eta gives

    as(us,z)+ab(A us,A z)-lb(A z)+eta.T A z(0)=0,  z in V,
    A us(0)=0.

The consistent recovery is rho=eta and

    <mu,w> = lb(w)-ab(A us,w)-eta.T w(0).

It is an element of B*, which can include endpoint atoms. This variational
definition is valid without presuming smooth densities or differentiating
an insufficiently regular stress field. A density-plus-endpoint formula
requires its own regularity and integration-by-parts justification.

For this specific rectangular-pad law, the stronger mapping above supplies
that justification: b=A us belongs to H2, hence N=EA u', Q=G As(v'-theta)
and M=EI theta' belong to H1. Their endpoint values exist and their first
derivatives lie in L2. Integration by parts then gives the physical
interface density and endpoint atoms

    mu_density=(N',Q'+q,M'+Q),
    mu_root=(N(0),Q(0),M(0))-eta,
    mu_tip=-(N(1),Q(1),M(1)).

Here q is the applied smooth transverse line load. Scaled-gap densities
and atoms divide the third component by ell. In a scaled root constraint
eta_phys=T.T eta_scaled with T=diag(1,1,ell). The total physical beam-root
reaction equals -(N0,Q0,M0)+mu_root=-eta; do not add the root atom again
to that recovered total. A tip interface atom balances elastic endpoint
traction without adding an absolute tip support.

Sharp fixed-band indicators are not H1 test functions, so a general B*
functional alone would not define their resultants. The L2-density plus
endpoint-atom representation just proved does define them for this law.
Small H1-dual differences still do not, by themselves, bound sharp-band
differences. Both quantities must retain their separate numerical checks.

With residual convention r=Kq+C.T lambda-f, the beam-root support reaction
is -eta. The multiplier residual contributions are +mu on the beam and
-A*mu on the panel. If displayed as externally applied interface forces,
their signs reverse. Declare the convention and recover moments about a
common origin. Do not identify a root atom alone with the root support
reaction or omit an eccentric force's lever arm.

The eliminated and mixed virtual-work expressions must agree for arbitrary
admitted variations. Root and panel support reactions must be recovered
by restoring excluded variations or their declared dual boundary
functionals, not inferred only from total force balance.

## Independent evaluator contract and further gates

A bounded higher-order/Ritz reference is a suitable next candidate,
subject to review and a new registration. For example, vector polynomial
fields with the x-boundary factor (x+.5)*(1.5-x) and independent y modes
can satisfy the panel essential conditions without constraining the free
y edges. Retain the three exact root conditions, with explicit reaction
recovery. Do not reuse the existing Q4/CST assembly, beam interpolation,
clipped-host pad integration or a P1/hybrid/enriched multiplier matrix
as the numerical reference algorithm.

Independent polynomial pad moments/antiderivatives may evaluate A and A'
directly. Any integration of panel/beam energy and cosine loading must
have a frozen quadrature/error contract. Increasing basis degree or
quadrature after inspecting results requires a new reviewed registration.
Dense operations are admissible only for this bounded independent oracle,
never as the sparse production mixed owner.

Before physical comparisons require: rigid-pose and polynomial moments,
derivative/work checks, exact root-constraint rank, energy identity,
independent reaction balance, admissible conditioning, and a registered
systematic basis/integration convergence series. Then compare the same
signed root results, energy splits, fixed bands and complete interface
functional used in the joint-refinement diagnostic. A total tip match
alone remains insufficient. External executed comparisons and native
full-vector/shear/drilling qualification remain separate mandatory work.
