# F03 saved-state spatial residual: bounded design for independent review

This is a proposed postprocessing study, not execution authority. It applies
only after the separately registered exact-pose representation diagnostic
passes its own integrity checks. Its three inputs are the **original** saved
classical Ritz states at `n=12,16,24`: physical shell/beam coefficients `q`
and root multipliers `eta`, plus their independently reconstructed exact
represented-constant pose polynomials. Preserve the original numerical
decisions and failed evidence. Do not assemble or solve an equilibrium,
project another pose, evaluate the old pose/shell operators, increase `n`, or
change the finite-pad law. The study reports the spatial distribution of the
saved states' strong balance defect; it does not estimate a solution error.

## Frozen represented model and signs

Let `Omega=[-0.5,1.5] x [-0.5,0.5] m`, with supported vertical edges
`Gamma_L` and `Gamma_R`, and free horizontal edges `Gamma_-` and `Gamma_+`.
The beam station is `s in [0,L]`, `L=1 m`. The four square-pad offsets are
`(xi,eta_y)` centered at `(+-dx,+-dy)`, with halfwidth `a`; here
`dx=0.2 m`, `dy=0.23 m`, `a=0.05 m`. Lift the *stored binary64* constants
to exact rationals for geometry and saved coefficients. Define

    S = (4a)^2,   J_geom = E_pad[xi^2+eta_y^2],
    J = the original binary64 result of dx**2+dy**2+2*a**2/3,
    gamma = J_geom/J.

The area average and yaw of a shell displacement `z` are

    A_s z = E_pad [ (z_x,z_y,(xi*z_y-eta_y*z_x)/J) ]

at translated pad coordinates `(s+xi,eta_y)`. The third entry is a physical
angle, conjugate to `Nm`, not a length obtained by dividing a moment by
`ell=0.46 m`. Consequently `A_s(-y,x)=(0,s,gamma)`, while translations map
to `(1,0,0)` and `(0,1,0)`. Keep the represented `J` even though the exact
geometry gives `J_geom`; do not silently set `gamma=1`. This first study has
one represented-constant geometry stream, no nominal-decimal comparison.

Recover the physical beam interface from exact reconstructed pose
polynomials and the **unchanged** saved `q,eta`:

    N=EA b_u',  Q=GAs(b_v'-b_theta),  M=EI b_theta',
    d=(N',Q'+q_load,M'+Q),
    alpha_0=(N(0),Q(0),M(0))-eta,
    alpha_1=-(N(1),Q(1),M(1)),
    <mu,w>=int_0^1 d(s).w(s) ds+sum_{e=0,1} alpha_e.w(e).

Here `d` has units `(N/m,N/m,N)` and the atoms `(N,N,Nm)`; `q_load` is the
original smooth `F0(1+0.25 cos(2*pi*s/L))/L` transverse load, with
`F0=10^6 N`. The beam root multiplier occurs **once**, in `alpha_0`.
Neither a second root load nor a beam root-slope constraint is permitted.
Do not replace the original saved functional or its evidence: archive the
independently reconstructed functional alongside its raw saved description,
and label their discrepancy separately.

Specify the represented material tensor before registration. Lift the
original computed binary64 plane-stress tensor, thickness, and beam
`EA,GAs,EI` coefficients to rationals **after** their stated source
arithmetic, rather than recomputing mathematically equivalent expressions
with different rounding. Evaluate the global polynomial shell displacement
and its derivatives directly from the saved coefficients with an independent
Legendre recurrence/polynomial construction. Define the symmetric membrane
resultant `T=t D_plane eps(u)` in `N/m`; its shear uses engineering strain
`u_x,y+u_y,x`. The exact-rational operations on represented coefficients
and geometry are distinct from the fixed floating quadrature used for the
explicit cosine below. Exact rational evaluation is not a certificate for
the physical continuum solution.

## Area adjoint and 45 fixed rectangles

For a pad horizontal offset `[l,r]` and vertical interval `Y`, set
`a_x=max(0,x-r)` and `b_x=min(1,x-l)`; an integral is zero if `b_x<=a_x`.
The line-density contribution to `f_mu=A*mu` on that pad is

    f_x=1_Y/S [int_a^b d_x ds-y/J int_a^b d_theta ds],
    f_y=1_Y/S [int_a^b d_y ds+(x int_a^b d_theta ds-int_a^b s*d_theta ds)/J].

At endpoint `e`, add its atom **once** on the translated pad:

    1_[e+l,e+r](x) 1_Y(y)/S *
      (alpha_e,x-y*alpha_e,theta/J,
       alpha_e,y+(x-e)*alpha_e,theta/J).

Sum over all four pads, retaining line and root/tip atom contributions as
separate signed channels. `f_mu` is an area force in `N/m^2`; endpoint atoms
on the beam are finite-area shell loads, never shell point/line loads or
internal stress jumps.

Derive and sort the cut coordinates as exact represented rationals:

    x: -.5;  -dx-a,-dx+a,dx-a,dx+a;
       1-dx-a,1-dx+a,1+dx-a,1+dx+a;  1.5
    y: -.5; -dy-a,-dy+a,dy-a,dy+a; .5.

They correspond nominally to ten x points
`[-.5,-.25,-.15,.15,.25,.75,.85,1.15,1.25,1.5]` and six y points
`[-.5,-.28,-.18,.18,.28,.5]`: exactly `9 x 5 = 45` open rectangles.
On each rectangle, all clipping branches and pad/atom indicators are fixed.
Retain one-sided limits at internal cut edges and the supported/free outer
corners as labeled diagnostics. Interface edges and corners have zero area
measure in cell integrals; no arbitrary value on them may affect a norm.
The free top/bottom edges each have nine fixed segments. There are no
physical material interfaces on the cuts. The smooth global polynomial
stress has no internal jump; mixed outer corners need no presumed `H2`
regularity of a continuum solution.

The shell strong and free-edge defects are

    r_Omega = div(T)+f_mu                 [N/m^2],
    r_N = T*n on y=+/-0.5                [N/m],

where `n=(0,+1)` above and `(0,-1)` below. For every supported test `z`
vanishing on both vertical edges, integration by parts fixes the signs:

    <mu,A z>-a_s(u,z)
       = int_Omega r_Omega.z dA-int_Gamma_free r_N.z dl.       (1)

The left side may vanish on the admitted Ritz space while the pointwise
residual is nonzero. Equation (1) supplies a numerical work identity, not
an a posteriori error bound.

## Fixed integration and test inventory

The scalar shell polynomials have coordinate degrees at most `(n,n)`.
Their stress divergence has coordinate degrees at most `(n,n)`.
`Q=GAs(b_v'-b_theta)` and hence the polynomial portion of `d_theta=M'+Q`
have station degree at most `n`; `d_y=Q'+q_load` has polynomial degree at
most `n-1`. Integrating `s*d_theta`, and multiplying its other primitive
by `x`, bounds the polynomial area load by degree `n+2` in x and at most
one in y. Thus on each rectangle the polynomial portion of `r_Omega` has
coordinate degrees no greater than `(n+2,n)`, and its squared magnitude
no greater than `(2n+4,2n)`. At `n=24`, this is `(52,48)`; tensor Gauss
orders 48 and 64 each integrate those polynomial terms exactly in exact
arithmetic because their one-dimensional exact-degree limits are 95 and
127. Construct rational polynomial antiderivatives independently wherever
possible. Clipped integration of the smooth cosine adds explicit sine or
cosine functions of x and makes its square trigonometric; neither Gauss
order is exact for these parts. Freeze **both** 48 and 64 tensor orders
for all 45 cells and both free edges; use independent one-dimensional
48/64 station integration on the trace side. Do not add adaptive orders
or replace a rule after observing a discrepancy. Agreement is a numerical
consistency check, never a certified quadrature bound.

Use three rigid tests `(1,0),(0,1),(-y,x)` and six fixed supported-edge
lifts. With `chi_L=(1.5-x)/2` and `chi_R=(x+0.5)/2`, each edge has
`chi_e*(1,0)`, `chi_e*(0,1)`, `chi_e*(-y,x)`. The rotation origin is
`(0,0)` in the panel coordinates. Also use exactly 18 supported tensor
polynomials: each of the two displacement components separately equals
`(1-X^2)P_i(X)P_j(Y)` for `i,j=0,1,2`, `X=x-0.5`, `Y=2y`.
They are contained in every declared Ritz space. For work comparisons,
scale translation tests and supported polynomials by `U0`; scale rigid
rotation and rotational edge lifts by `U0/L0`, with `L0=1 m` and
`U0=F0/(Et)`. Retain the unscaled lifts for physical reaction recovery.
Do not choose tests from a residual map.

## Independently checked work and reactions

Independently integrate the cellwise `f_mu.z` and the one-dimensional
`d.(A z)` plus both `alpha_e.(A_e z)` for every declared test. The latter
trace is built from direct exact pad moments of the test fields, not by
calling an old pose or constraint matrix. In particular, check the three
rigid force/wrench identities in physical units:

    int_Omega f_x = int_0^1 d_x ds+sum alpha_e,x,
    int_Omega f_y = int_0^1 d_y ds+sum alpha_e,y,
    int_Omega (x*f_y-y*f_x)
      = int_0^1 (s*d_y+gamma*d_theta) ds
        +sum_{e=0,1}(e*alpha_e,y+gamma*alpha_e,theta).         (2)

The last equality tests the held `J` and its `gamma`, not a nominal rigid
yaw of one. Preserve independent line and endpoint contributions on both
sides and separate actual signed force `(N)` and moment `(Nm)` differences.

For an unscaled edge lift `z_e`, independently evaluate

    R_e = a_s(u,z_e)-<mu,A z_e>
        = int_{Gamma_e} (T*n).z_e dl
          +int_{Gamma_free} (T*n).z_e dl
          -int_Omega r_Omega.z_e dA.                           (3)

The opposite supported edge contributes zero because `z_e=0` there.
For the x-force, y-force, and origin-moment lifts, the corresponding
`R_e` units are respectively `N,N,Nm`. Direct boundary traction alone is
generally **not** this finite-level reaction: retain the signed free-edge
and volume corrections. Compute the weak route from independent polynomial
strain integration and independent trace work, and the direct route from
boundary stress and cell residual integration. Compare them, then show
their difference from the original saved reaction as a descriptive
representation/roundoff diagnostic without changing the old decision.
For the 18 supported tests separately report each side of (1), including
the free-edge term, in joules; no new near-zero physical acceptance test
is introduced.

Freeze numerical-identity screens **before** registration: for each
scaled virtual-work equality in (1) and the area/trace adjoint use
`|left-right|/max(E0,|left|,|right|)<=1e-10`, `E0=F0*U0`.
For both sides of every physical reaction channel in (3) use
`|Delta F|/F0<=1e-10` or `|Delta M|/(F0*L0)<=1e-10`.
Apply the same force/moment scales to (2), with signed differences retained.
For every scalar integral entering these checks and every residual cell
measure, require 48/64 differences bounded by `1e-10` times the maximum
of its declared unit floor (`E0`, `F0`, `F0*L0`, or the squared-residual
scale specified below) and the two independently retained absolute
integral values. A cancellation near zero therefore uses the stated
physical floor. Also retain both
signed rule values and their difference. A failure means the diagnostic
integration is unresolved, not that an equilibrium or prior acceptance
criterion may be relaxed. Do not automatically retry with a third rule.

## Descriptive spatial output and limits of inference

For each fixed rectangle `K`, retain separate line/root-atom/tip-atom
load integrals, signed force `int_K r_Omega dA` in N, signed origin moment
`int_K (x*r_y-y*r_x) dA` in Nm, and

    V_K=(L0^2/F0^2) int_K |r_Omega|^2 dA.

For each fixed free-edge segment `E`, retain signed force/moment traction
integrals and `B_E=(L0/F0^2) int_E |T*n|^2 dl`. The squared-integral
48/64 comparison uses the dimensional floors `F0^2/L0^2` for a cell
and `F0^2/L0` for an edge, respectively (equivalently `1` after the
displayed normalization). Record totals, both edge sides, and one-sided
patch-edge limits. Finite nonnegative squares and complete cell/edge
inventory are integrity checks; there is **no** physical upper threshold
or observed-fraction cut for `V_K` or `B_E`. These are spatial defect maps,
not percentages of solution error, relative energy errors, convergence
rates, or upper/lower bounds. Strong `L2` defects need not decrease under
`H1` convergence. This global-polynomial study has no interior stress-jump
terms; a future `C0` piecewise trial would need its own jump terms.

An independently reviewed implementation and one-use registration must
freeze source/dependency hashes, exact parent state/evidence identities,
the arrays and per-cell schema, both fixed quadrature orders, unit scales,
limits, case/resource inventory, failure precedence, and independent raw
adjudication before execution. This design grants no run or reference
acceptance. Its result cannot choose a production approximation space,
qualify native shell/beam coupling, or trigger automatic uniform refinement.
