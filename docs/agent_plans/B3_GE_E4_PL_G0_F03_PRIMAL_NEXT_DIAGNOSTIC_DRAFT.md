# F03 next primal diagnostic: independent mechanics draft

22 September 2026. Read-only design following the consumed primal Ritz v1
run at source `e7908c1ad3dcff1cf9bc957ba8fd0fe1fe49b5b5`. This document
does not authorize execution, change a threshold, repair old evidence or
select a production approximation. The original `FAILED_EVIDENCE` record
remains immutable; a separate saved-state audit must retain the n16/n24
numerical failures. F03/G0B remains open.

## Recommended bounded question

Use the three existing n12, n16 and n24 states to answer two separate
questions, without equilibrium solves or stiffness/operator assembly:

1. Which part of the discrepancy between the stored pose polynomial and
   stored direct pose derivatives comes from coefficient reconstruction?
2. Where does the resulting polynomial displacement fail the physical
   shell balance law, and which omitted spatial features could explain
   the slow approximation trend?

The first question is numerical representation and should be the immediate
three-state registered diagnostic. The second is spatial approximation;
its derivation can be reviewed now, with numerical residual postprocessing
registered separately after the representation question is resolved.
Neither may be answered by weakening the original 1e-11
saved-action limit. Provisional total-energy changes of 4.52% and 2.60%,
and full-functional changes of 2.87% and 3.16%, already prevent treating
the sequence as a settled reference independently of that limit.

## A. Independent exact polynomial reconstruction

Let the horizontal marginal be the uniform distribution on the two
intervals centred at +/-d_x with halfwidth a, and the vertical marginal
the corresponding distribution centred at +/-d_y. The four-pad union is
their Cartesian product, with area S=(4a)^2. For either marginal,

    E[t^m] = sum_intervals (r^(m+1)-l^(m+1)) / (4a(m+1)).

Odd moments vanish exactly. For p_i(x)=(1-(x-.5)^2)P_i(x-.5), define

    B_i(s) = E_xi[p_i(s+xi)],
    C_i(s) = E_xi[xi p_i(s+xi)],
    Y_j    = E_eta[P_j(2eta)],
    Z_j    = E_eta[eta P_j(2eta)].

For each tensor basis function, its x-displacement contribution to
physical pose (u,v,theta) is

    (B_i Y_j, 0, -B_i Z_j/J),

and its y-displacement contribution is

    (0, B_i Y_j, C_i Y_j/J).

Contract these expressions with the saved displacement coefficients in
the registered component/i/j order. Expanding p_i in powers of
tau=s-.5 and using the exact marginal moments gives a polynomial
directly, without Gaussian nodes, sampled projection, clipped-host
integration or any stored pose matrix. An exact rational power-to-Legendre
conversion supplies an independent complete coefficient representation.
The polynomial and its first two derivatives can then be evaluated at
the nine existing rational stations s=k/8.

Use exact binary64 q values lifted to rational numbers. For attribution
to the original computation, separately lift the represented binary64
constants d_x, d_y, a and the original computed J to exact rationals;
hold that represented J fixed. This describes the mathematical integral
using the original represented constants, not every intermediate rounded
Gaussian operation. A second, optional and explicitly registered stream
may use the intended decimal geometry, with J=2837/30000. Its difference
from the represented-constant stream is geometry representation, not
projection error. Do not mix the two streams.

In the represented-constant stream define J_geom=E[xi^2+eta^2] exactly.
The held source J may differ from J_geom. Its rigid yaw gain is therefore
gamma=J_geom/J, not identically one. Preserve this factor in exact rigid
motion and adjoint torque identities. The nominal rational stream has
gamma=1. Forcing unit gain in the represented stream would silently change
the operator being audited.

Prefer exact rational arithmetic for the bounded degree<=24 construction.
If finite precision is chosen instead, its independent error enclosure
and two fixed precisions must be specified before execution. A second
precision alone is a consistency check, not a rigorous rounding bound.
Exact rational results may be rounded once for display; retain exact
numerators/denominators or a lossless representation for adjudication.

### Required discrepancy decomposition

Let p_S be the exact polynomial defined by lifting the saved coefficient
bits to rationals, and p_O the independently reconstructed oracle
polynomial. Let p_F,k(s) denote the original floating differentiation and
evaluation result of those saved coefficients, and d_F,k(s) the original
floating station_Ak action on saved q. These are four distinct objects.
Writing [v] for the exact rational lift of a resulting binary64 value,
preserve this three-term signed decomposition at k=0,1,2 in every channel:

    [p_F,k]-[d_F,k]
      = ([p_F,k]-p_S^(k))
        + (p_S^(k)-p_O^(k))
        + (p_O^(k)-[d_F,k]).

The terms isolate floating polynomial differentiation/evaluation,
coefficient/integral reconstruction, and direct-action evaluation relative
to the independent represented integral. The signed convention here is
polynomial minus direct; the original metric uses an absolute discrepancy.

This identity closes exactly between the lifted endpoint values. Separately
retain and reproduce the original floating subtraction, physical/angular
scaling and normalization, including their arithmetic order. If closure
against a rounded subtraction or scaled result is also required, retain
its final arithmetic-rounding remainder explicitly. Do not substitute an
exact-arithmetic surrogate for the original failed numerical metric.
No newly reconstructed coefficient replaces an original array.

For the exact difference of the saved and oracle Legendre coefficients,
delta c_j=c_S,j-c_O,j on x_b=2s/L-1, the middle term's endpoint second
derivative obeys

    delta b''(L) = sum_j>=2 w_j delta c_j,
    w_j = (j-1)j(j+1)(j+2)/(2L^2),
    |delta b''(L)| <= sum_j>=2 w_j |delta c_j|.

At s=0 the signed weights additionally contain (-1)^j. The first
derivative weights at L are j(j+1)/L. For j=24, the second derivative
weight is 179400/L^2. Thus small coefficient discrepancies can be greatly
amplified at an endpoint. These weights describe only the exact coefficient
term; they do not absorb the floating evaluation term. The exact signed
sum and triangle bound, not a verbal roundoff diagnosis, should establish
the coefficient contribution.
Angular coefficients use ell=.46m exactly once when comparing against
the existing force-conjugate pose scaling.

Require exact rational identity closure, finite bounded outputs and
complete arrays. Reproduce the old normalized failures unchanged.
Record whether the independent integral agrees with the direct and/or
projected route under the existing 1e-11 action criterion; this is a
diagnostic comparison and cannot retrospectively pass either old case.

## B. Physical adjoint traction and shell residual

Use the sign convention from the continuous-primal derivation:

    <mu,w> = lb(w)-ab(b,w)-eta . w(0),
    as(u,z)-<mu,A z> = 0,  z in V.

Write the physical interface functional as line density d(s) and endpoint
atoms alpha_e at e=0,L. Its components have units (N/m,N/m,N) for d,
and (N,N,Nm) for alpha. In particular,

    d = (N', Q'+q_load, M'+Q),
    alpha_0 = (N(0),Q(0),M(0))-eta,
    alpha_L = -(N(L),Q(L),M(L)).

The root multiplier is already included in alpha_0. Do not add another
root traction, use only the root atom as the support reaction, or clamp
the beam slope. These formulas use physical moments; do not divide the
third component by ell in the physical adjoint.

For a horizontal offset interval [l,r] and vertical interval Y, define

    a_x = max(0, x-r),  b_x = min(L, x-l),

with all integrals zero if b_x<=a_x. The contribution of the line density
to shell applied area traction is

    f_x = 1_Y(y)/S * [integral_a_x^b_x d_x(s) ds
                      - y/J * integral_a_x^b_x d_theta(s) ds],
    f_y = 1_Y(y)/S * [integral_a_x^b_x d_y(s) ds
                      + (x integral d_theta(s) ds
                         - integral s d_theta(s) ds)/J].

Sum over the four [l,r] x Y pads. The contribution of atom alpha_e is

    1_[e+l,e+r](x) 1_Y(y)/S *
      (alpha_e,x - y alpha_e,theta/J,
       alpha_e,y + (x-e) alpha_e,theta/J).

Together these define f_mu=A*mu as an L2 area load, in N/m^2, for this
fixed finite-pad law. An endpoint atom on the beam therefore becomes a
distributed patch load on the shell. It is not a point/line shell load
and does not introduce an internal stress jump condition.

Let T=t Dplane eps(u) be the symmetric membrane stress-resultant tensor,
in N/m; its shear entry corresponds to engineering shear ux,y+uy,x.
The shell strong residual and free-edge traction defect are

    r_Omega = div(T)+f_mu,
    r_N = T n on y=+/-0.5.

For every z vanishing on the supported x edges,

    <mu,A z>-as(u,z)
       = integral_Omega r_Omega . z - integral_GammaN r_N . z.

At the exact solution both volume and free-edge defects vanish in their
weak/distributional sense; no global H2 regularity of the shell at mixed
outer corners is presumed. For the saved smooth polynomial states all
displayed derivatives and boundary values are ordinary functions. For a
Ritz state the weak residual vanishes on its admitted finite test space;
it need not vanish on local variations omitted by that space. The residual
above is the augmented shell balance using the recovered root multiplier,
not automatically a norm of the reduced energy error on V0.

### Fixed geometry partition and observables

For the nominal geometry, the only required x partition points are

    -.5, -.25, -.15, .15, .25, .75, .85, 1.15, 1.25, 1.5,

and the y points are

    -.5, -.28, -.18, .18, .28, .5.

These give 45 rectangles. In a represented-constant calculation derive
the corresponding coordinates from those constants; do not round them
back to nominal decimal coordinates. All points are fixed by geometry,
not selected from a residual plot. Include one-sided patch-edge limits.
Endpoint atoms cause area-load jumps at patch edges; the line-density
convolution has horizontal clipping breakpoints and vertical strip edges.
The material law is unchanged across all of them. The mixed supported/free
outer corners are a separate possible regularity limitation.

For each case preserve the displacement/stress polynomials, raw and oracle
functional descriptions, line/atom traction contributions, and each cell's
signed residual moments and squared L2 contribution. Retain top/bottom
traction defects separately. Suitable dimensionless descriptive measures
are

    V_K = (L0^2/F0^2) integral_K |r_Omega|^2,
    B_E = (L0/F0^2) integral_E |T n|^2.

Neither their totals nor their spatial fractions are percentages of
physical solution error. Strong L2 residuals are not guaranteed to decrease
under H1 convergence, and these numbers are not certified upper/lower
energy-error bounds. No physical acceptance threshold is proposed for them.

Use exactly specified polynomial antiderivatives where possible and two
fixed, independently checked quadrature rules for the explicit cosine
terms; 48/64 is consistent with the existing smooth-load contract. Do not
add rules after inspecting discrepancies. Scalar and virtual-work checks
may reuse existing 1e-10 scaled numerical identity limits, explicitly as
integration/recovery checks rather than a physical qualification gate.

### Required sign, work and reaction identities

The adjoint must satisfy, including each endpoint exactly once,

    integral_Omega f_mu,x = integral_I d_x + sum_e alpha_e,x,
    integral_Omega f_mu,y = integral_I d_y + sum_e alpha_e,y,
    integral_Omega (x f_mu,y-y f_mu,x)
      = integral_I (s d_y+gamma d_theta)
        + sum_e (e alpha_e,y+gamma alpha_e,theta).

Here gamma=1 for the nominal physical law, and gamma=J_geom/J for the
faithful represented-constant stream. The latter stream must also use
A(-y,x)=(0,s,gamma) in the independent rigid-work test.

Also require virtual work integral_Omega f_mu . z = <mu,A z> for the
three rigid test fields, all six declared edge liftings and a fixed set
of supported tensor polynomials (for example i,j=0,1,2 in each component).
Integrate both sides independently; total balance alone is insufficient.
The low-order supported tests can bind against the corresponding saved
Kq+C^T eta-f entries without assembling a new matrix.

For any declared support lifting z_e, the recovered scalar reaction is

    R_e = as(u,z_e)-<mu,A z_e>
        = integral_boundaryOmega (T n).z_e
          - integral_Omega r_Omega.z_e.

Thus finite-level boundary stress alone is generally not the declared
support reaction. Compare its difference with the explicit volume and
free-edge residual terms. Keep signed force and moment channels and their
lever arms. This provides a useful independent explanation of support
reaction movement without silently changing reaction definitions.

## Decision after this diagnostic, not before it

If exact reconstruction isolates projection/differentiation error, design
a stable direct moment/coefficient implementation and verify it independently
before any future structural study. Keep the original failed arrays/results.
If residual work is concentrated near known load edges or outer corners,
derive a local approximation in the same continuous space V0; do not add
physical restraints, a penalty, or a different multiplier law.

A possible future candidate is an independently implemented conforming
piecewise polynomial Ritz space on geometry-fixed rectangles, retaining
exactly the three global root-pose constraints. C0 continuity is admissible:
the finite-pad map acts on H1 and supplies the required H2 beam trace.
For illustration only, tensor degrees p=1,2,3 on the 9-by-5 rectangle
partition have 96,374,832 free displacement coefficients after the two
supported x edges. This is not a proposed execution inventory. Its pad
integrals, moving-cell breakpoints, exact elimination, free beam slope,
root rank and numerical convergence contract need independent proofs and
review before choosing it. Existing Q4/CST assembly cannot serve as the
independent implementation path.

The displayed residual formula has no interior stress-jump terms because
the current displacement is one global polynomial. Any future C0 piecewise
approximation must include its interior normal-stress jumps in residual
recovery, despite the absence of a physical material interface or interface
line force there.

The immediate executable successor, if registered separately, is the
three-state representation diagnostic in section A. Section B provides a
mechanics contract for later residual postprocessing, not present execution
authority. Freeze sources, both geometry
streams if used, every input hash, arrays, fixed precision/quadrature choices,
time/RSS bounds, one-use evidence root and terminal precedence before work.
It may establish diagnostic integrity only. It cannot accept a reference,
select a production space, qualify the native model or close G0B.
