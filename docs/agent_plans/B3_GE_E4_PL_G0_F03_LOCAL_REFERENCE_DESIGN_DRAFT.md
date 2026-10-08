# F03 local classical reference: design draft for independent review

This is a proposed successor in the **classical in-plane finite-pad
research fixture**, not a numerical authorization or a native product
change. The registered spatial residual diagnostic completed three
numerically passing cases. Its descriptive totals were
`V_12,V_16,V_24=21.69397,17.02412,11.53795` and
`B_12,B_16,B_24=.0264247,.00961514,.00454445`. The largest n24
volume contributions are cells 12 and 30, the pad-edge strips
`x in (.15,.25), y in (+/-(.18,.28))`; the free-edge defect is concentrated
on `x in (1.25,1.5)` near the right supported/free corners. These are
signed/normalized **strong-defect maps**, not solution-error fractions,
energy-error bounds or proof of local convergence. The global polynomial
Ritz states and the relevant signed physical reactions have not yet
established a settled independent reference. No automatic increase in
global degree, uniform refinement, or change of an acceptance limit follows.

## Keep the continuous constrained problem fixed

Use exactly the panel, four positive square pads, plane-stress membrane,
Timoshenko beam, smooth line load, and two fully supported vertical panel
edges of the [continuous-primal derivation](B3_GE_E4_PL_G0_F03_CONTINUOUS_PRIMAL_REFERENCE.md).
In particular, `V=H1(Omega;R2)` with `u=0` on `x=-.5,1.5` and free
horizontal edges, `Omega=(-.5,1.5)x(-.5,.5) m`. For station `s in(0,1)m`,
the same finite-square operator `A` averages translation and the physical
yaw moment `(xi*u_y-eta_y*u_x)/J` over the four moving squares. Eliminate
the independent beam fields exactly at the continuous level:

    V0={u in V:A u(0)=0},
    H(u,z)=a_s(u,z)+a_b(Au,Az),     G(z)=l_b(Az),
    H(u,z)=G(z) for all z in V0.

The only root restrictions are those **three** average pose values.
`(Au)_v'(0)` remains free; the tip has no absolute support. Use either
three physical root multipliers `eta` or a demonstrably equivalent exact
three-row elimination at each finite level. Do not install a beam slope
condition, point ties, a penalty, a drilling coordinate, or a discrete
P0/P1/hybrid/enriched interface multiplier in this independent primal.

For a candidate conforming `V_h subset V`, the finite problem is

    (K_s+A_h^* K_b A_h) q+C_0^T eta=f_h,     C_0 q=0,
    C_0 q=(A u_h)(0).

`A_h` is the **same physical area map restricted to V_h**, not the native
shell/beam coupling assembly. The root map must have rank three, verified
with a separately represented freely varying root derivative; a
well-conditioned scaled KKT or mathematically exact rank-three
elimination may be used. This weak formulation needs only `u_h in H1`.
For the fixed nonzero rectangular pad width, the proven bounded mapping
`A:H1(Omega)->H2(0,1)` gives a continuous beam pose with the derivative
and endpoint values required by the beam energy and interface functional.
It does **not** require pointwise traces of two-dimensional displacement
gradients on a moving line. A global `C1` shell approximation is not a
physical admissibility condition.

For numerical comparison with the accepted represented-binary64 studies,
freeze their evaluated constants first and then do exact geometry/moment
algebra: use the held binary64 `J` and
`gamma=J_geom/J`, not an asserted `gamma=1`. In particular the rigid
rotation trace is `(0,s,gamma)` for that stream. A separate nominal-decimal
physical stream could be derived and registered later, but must never
replace or relabel these represented inputs. Keep the physical yaw in
radians and its conjugate in `Nm`; apply `ell=.46m` exactly once only when
converting a separately scaled gap/reaction presentation.

## Candidate conforming spaces

| Option | What it resolves | Main cost/limitation |
|---|---|---|
| Geometry-aligned, globally `C0` tensor polynomials with local conforming `h` refinement and modest fixed `p` | Independent displacement variations beside the observed pad edges and right corners while allowing the natural stress gradients | Extra cell boundaries create numerical stress jumps that must be recovered; local balancing and translated-pad event bookkeeping need proofs. |
| Same fixed 9-by-5 base partition with a small `p` comparison, no local splits | An independently implementable base and integration/rank control, with nested spaces if constructed accordingly | Resolves smooth within-cell behavior but cannot preferentially shorten distances at a pad edge/corner. |
| Global polynomial plus conforming compact bubble supplements | A cheap diagnostic of missing interior cell variations | Bubbles with zero cell traces cannot by themselves represent intercell trace changes or corner singular behavior; this is not a complete local reference hierarchy. |

The recommended **design candidate** is the first option, beginning from
the existing exact geometry cuts, with the second as a mandatory baseline
and parity/control comparison. This is not a selected production element,
a frozen degree, a mesh inventory, or authorization to calculate a new
case. A `C1` spline construction is mathematically conforming but would
impose additional finite-level smoothness across the very pad/corner
regions under study; its knot, support, conditioning and quadrature costs
would need a separate rationale. Neither the residual magnitude nor the
illustrative 9-by-5 tensor-grid dimensions in an earlier draft select `p`
or the number of local splits.

The candidate cuts below mean **axis-aligned rectangles** with polynomial
charts in their physical x/y coordinates. Inclined or general
quadrilateral cells would need a separate mapping, trace and clipped-pad
moment proof; they are not covered by the shifted-event formulas.

Build a connected conforming hierarchy: each trial field is continuous
across every cell edge, its two displacement components vanish strongly
on both supported x edges, and its free y-edge values and derivatives are
unconstrained. If local quadrilateral splits make hanging nodes, use a
genuinely conforming closure or prove and impose exact polynomial trace
constraint identities on every subedge; avoid penalty-only glue. A 2:1
neighbor balance limits level differences but **does not itself enforce
`H1` continuity** at a hanging node. Demand nested feasible
spaces, or explicitly declare and test any nonnested comparison, so an
energy trend has a defensible interpretation. Refinement targets may be
*predeclared* around the already observed two pad-edge strips and the
right supported/free corners. The initial geometry must also include the
unfavored regions and both signs of y, allowing an independent check that
the local choice has not merely hidden movement elsewhere. No marking
algorithm may use a new result to mutate the same one-use inventory.

## Exact geometry and moving-pad breakpoints

The original shell cuts are the rationally derived 10 horizontal and six
vertical coordinates of the [spatial design](B3_GE_E4_PL_G0_F03_SPATIAL_RESIDUAL_DESIGN.md):
the 45 rectangles use panel boundaries, translated root/tip pad edges,
and vertical pad strips. Preserve their represented rational coordinates;
any local additional shell cell edges require a *separately declared*
exact coordinate inventory. Integral subdomains also split at every
vertical shell knot crossed by a pad and at every horizontal shell knot
inside its fixed y strip.

For each shell vertical edge `x_k` and each pad horizontal offset interval
`[l,r]`, the polynomial formula for a station pad integral changes at

    s=x_k-r and s=x_k-l,

after clipping to the open beam interval `(0,1)` and sorting unique
represented rational values together with `0,1`. This is the needed
beam-station breakpoint set, not simply the shell x cuts copied onto
the beam. An added local vertical edge adds its own two shifted events;
a horizontal edge partitions the y integral but creates no moving station
event. Preserve the exact ordering and count of all **positive** rational
station intervals before any floating conversion. Distinct expressions
such as `2*(dx+a)` and `1-2*(dx+a)` can be distinct represented rationals
near `.5` yet map to an identical binary64 station. Do not snap them
together, omit an interval, or call it zero width. A reviewed local chart
or high-precision integration/evaluation and a quantitative roundoff
contract for these near-coincident events remain open pre-execution
choices. At these events the pad integral may change polynomial formula,
but the `H1->H2` result means `Au` and `(Au)'` have continuous traces.
Consequently `N=EA(Au)_u'`, `Q=GAs((Au)_v'-(Au)_theta)` and
`M=EI(Au)_theta'` have no fictitious *internal* endpoint atoms. Check
one-sided pose/first derivative and piecewise second-derivative work
identities rather than stitching arbitrary polynomial fits.

Implement independent tensor-cell polynomial moments and clipped
rectangle overlaps using these exact cuts; a fixed tensor-polynomial
antiderivative on each **axis-aligned rectangular** overlap avoids
borrowing old Q4/CST stiffness,
host clipping, existing global Ritz pose matrices, or FE beam fields.
The load's represented `omega=fl(2*pi/L)` remains in its analytic
cosine/sine primitive or in two preregistered fixed quadrature rules.
Physical integration and floating evaluation both require quantitative,
independently checked degree/order and work-agreement contracts before a
registered run. Exact geometry alone does not certify floating results.

## Cost, reactions and admissible evidence

Assemble the shell bilinear form locally and sparsely. The beam part is
an exact restricted trace operator applied on each beam interval; its
support follows the finite pad footprint, but fixed **physical** width
does not bound the number of active trace degrees of freedom as the shell
mesh is refined. A sparse container alone implies no linear-storage
claim. Before registration, count active trace DOFs for every proposed
beam interval, restricted beam-coupling `nnz`, assembled/Schur factor
fill, peak matrix and factor workspace, and their growth along the
proposed hierarchy; set reviewed resource caps accordingly. This
incidence/fill gate may rule out a proposed local inventory even when
the shell stiffness is sparse. Solve the three-root sparse KKT with
explicit physical scales and conditioning diagnostics; never form a
dense global inverse.
A small dense independent oracle can verify selected unit operators,
adjoints or a deliberately tiny manufactured case, but is not a hidden
second scientific solve. Preserve rank, positive energy, equilibrium,
support work and independently recomputed action identities without
symmetry repairs or numerical regularization after failure.

Recover the complete physical interface functional independently from
the piecewise `H2` beam trace:

    d=(N',Q'+q_load,M'+Q),
    alpha_0=(N(0),Q(0),M(0))-eta,
    alpha_1=-(N(1),Q(1),M(1)).

The root multiplier appears once; total beam-root reaction is `-eta`,
not `alpha_0` alone. Recover left/right panel support wrenches by
independent virtual-work liftings (x force, y force and rotation about
the declared origin), and cross-check the explicit identity, for each
unscaled support lift `z_e`,

    R_e = supported-boundary stress work + free-boundary stress work
          - volume-residual work - interior-jump work.

The opposite supported edge has zero lift. This follows from the jump
sign convention below; direct supported-boundary stress alone need not
equal the finite-level reaction. Retain shell/beam energies,
external/interface work, signed root and tip wrenches, first-quarter and
other fixed bands, and both density and endpoint-atom channels. An
`H1`-dual comparison of the **complete interface functional, including
endpoint atoms**, and the sharp fixed-band
forces/moments are separate observables; neither substitutes for the
other. A piecewise density needs its own verified norm evaluation and
resolution contract; do not feed its coefficients to the frozen
global-degree trace-norm helper or assume its old numerical check applies.
Preserve the original signed physical acceptance criteria and
the independent Q4/CST-CB comparison inventory. A matching tip or
decreasing strong defect alone cannot accept the reference.

For a `C0` trial, define an interior edge normal `n` from the minus to
plus cell and the distributional jump

    j_E=(T_plus-T_minus)n    [N/m].

The supported-test integration-by-parts identity becomes

    <mu,A z>-a_s(u_h,z)
       =sum_K int_K (div T+f_mu).z
        +sum_E int_E j_E.z
        -int_Gamma_free (T n).z.

There is no physical material interface or shell line force at these
edges. Include signed jumps, their works and suitable edge-scaled
squared measures alongside volume and free-edge terms; omit the jump
term only for a truly global smooth polynomial trial. A large or small
strong/jump map is still **descriptive**, not a guaranteed energy-error
estimator or a convergence threshold.

For nested admissible spaces and the **same** exactly integrated
functional, the minimized potential cannot rise on enrichment; the
coercive energy difference between two discrete minimizers is an
internal consistency and observed-change measure. It is not a bound on
the still-unknown distance to the continuum solution. Require a
preregistered series showing systematic stability of signed physical
channels, full interface functional, fixed-band wrenches, energy/work,
and both support partitions under at least independently varied local
resolution and polynomial degree. Numerical consistency, independent
reactions, and the existing unrelaxed physical limits must pass before
calling any classical reference settled. No G1/native result follows.

## Proofs and choices required before any execution

Independent review must settle: (1) a shape-regular conforming nested
mesh/degree family and exact local-coordinate/hanging-node trace identities;
(2) a constructive three-root rank proof on its smallest admitted space,
including free root slope; (3) exact piecewise pad/beam breakpoint,
positive-interval preservation, moment, derivative, adjoint-work and
event-continuity proofs; (4) a
fixed integration, piecewise-functional norm, and scaling/conditioning
contract with strict failure
handling; (5) support reaction and stress-jump identities with common
origins and correct atom bookkeeping; and (6) an active-DOF/nnz/fill/
workspace/growth bound and independent raw-adjudication protocol. Tiny
manufactured tests should
cover rigid `gamma`, affine/polynomial pad moments, stress/jump signs,
root rank, compatible/nonnested counterexamples, and exact work before
any registered scientific case. The choices of `p`, actual local splits,
case counts and convergence inventory remain **open** for that review.
No new run, production-space selection or automatic global refinement is
authorized by this draft.
