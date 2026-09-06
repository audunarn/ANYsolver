# P5 separate symmetric arch reference — 2026-09-06

Successor to `57a42be4b35717ea82cba4a089782d590be20e0a`, tree
`fda3dd51b3f1d5c9c8fd12dab3bd12febff27cca`. This record establishes a separately
implemented continuum reference for the next discrete arch comparison. It is
not independent authorship/review, an accepted GE-B3 comparison or production
qualification. No discrete beam mechanics are imported by the reference.

## Theory source and original development fixture

The continuum balance and constitutive basis is
[Bali et al., DOI 10.1002/nme.6994](https://pmc.ncbi.nlm.nih.gov/articles/PMC9543773/),
Section 2, equations 6-7 (spatial balance), 10-11 (strains and initial curvature),
15-17 (linear hyperelasticity and material/spatial resultants). The HTML source
was inspected. This is not a claim to have newly hash-bound its PDF or to have
reproduced one of its numerical benchmarks. Formal source-packet review remains
required before qualification use. The implementation below is a new planar
specialization and symmetric BVP, not the article's finite-volume algorithm.

The development fixture has full horizontal span 2 and stress-free reference
curve y0=h*(1-X^2), X in [-1,1]. Both ends are clamped at their original
positions and material directions. The default h=0.1, EA=1000, GA=400, EI=0.01.
A downward crown displacement d is prescribed; its conjugate concentrated
downward force P is an unknown result. The branch is restricted to symmetry
about the vertical crown plane. This restriction may exclude an earlier
antisymmetric or out-of-plane instability; it cannot establish full stability.

## Explicit reference equations and signs

Solve the left half, X=t in [-1,0], with state [x,y,theta,M] and constant
spatial force [Fx,Fy]. Here theta is the absolute planar director angle, not
an accumulated production rotation vector. Define

    J0=sqrt(1+(2*h*t)^2), theta0=atan(-2*h*t),
    N=Fx*cos(theta)+Fy*sin(theta),
    V=-Fx*sin(theta)+Fy*cos(theta),
    vx=(1+N/EA)*cos(theta)-(V/GA)*sin(theta),
    vy=(1+N/EA)*sin(theta)+(V/GA)*cos(theta).

The arclength equations are transformed to reference parameter t:

    x_t=J0*vx, y_t=J0*vy,
    theta_t=-2*h/(1+(2*h*t)^2)+J0*M/EI,
    M_t=J0*(vy*Fx-vx*Fy).

Initial curvature is subtracted by the explicit theta0 derivative. Zero load
therefore preserves the curved, stress-free shape. Six boundary conditions
determine four state functions and two force parameters:

    (x,y,theta)(-1)=(-1,0,atan(2*h)),
    (x,y,theta)(0)=(0,h-d,0).

Symmetric force jump gives P=-2*Fy. The full arch is reconstructed by reflecting
the left half: x changes sign, y is even, theta changes sign, M is even, Fx is
unchanged and Fy changes sign. For a later discrete comparison, the deformation
rotation is Rz(theta-theta0), not Rz(theta); end deformation rotations are I.
The same physical material-plane/section-axis convention must be retained.

The controller solves this BVP with analytic state/force Jacobians. A second,
linear variational BVP differentiates the equations with respect to crown drop;
its right boundary sensitivity is [0,-1,0] and gives dP/dd=-2*dFy/dd. No
production tangent, frame differentiation or discrete stiffness is used.
Integrating N*dN/dd/EA + V*dV/dd/GA + M*dM/dd/EI over both halves independently
checks dU/dd=P. M+x*Fy-y*Fx is also checked as a spatial moment first integral.

## Numerical profiles, diagnosed cap failure and correction

This is binary64 SciPy collocation, not multiprecision or rigorous interval
evidence. `BVP7` uses collocation tolerance 1e-7 and at most 1,025 nodes;
`BVP9` uses 1e-9 and at most 4,097 nodes. Both retain boundary tolerance 1e-11,
at most 2,000 counted BVP callbacks and a 60-second cooperative deadline.
Fixed field samples have 129 points. Differential checks sample two off-node
positions in every collocation interval, not just points where the collocation
equations enforce a small residual. Pointwise normalized residuals must be
below ten times the selected collocation tolerance. This is a reference
discretization diagnostic, not a changed element qualification tolerance.

The first fine-profile implementation gave both solves a 1,025-node cap. At
d=0.025 the primary solution converged with 577 nodes; the sensitivity solver
stopped at 623 nodes before a refinement that would exceed its cap, with RMS
residual 1.2282576873925402e-8. Reusing the primary mesh did not resolve that
cap failure. Those failures are preserved as development incidents, not passes.

An explicitly declared implementation revision assigned the finer profile a
fixed 4,097-node cap. It did not change equations, physical inputs, tolerances,
the callback/deadline bounds or add automatic retries. The corrected fine pair
and twenty-bisection limit calculation completed together in about 1.14 seconds.
This timing is diagnostic, not a performance gate. The fine sensitivity still
starts on the primary resolved mesh to avoid rediscovering its coefficient
knots. These are small correctness calculations, not consumed formal resource
requests; no accepted authority or evidence was modified.

## Observed limit-point reference

For the fine profile:

| Crown drop d | P | dP/dd | Work identity error |
|---:|---:|---:|---:|
| 0.025 | 0.028037338225214842 | 0.2009831484966034 | 2.2519139331045324e-13 |
| 0.05 | 0.02698655468862975 | -0.19138899886304353 | 7.361125597959983e-14 |

Twenty bounded sign bisections on this connected symmetric branch produce:

- displacement interval [0.03346867561340333, 0.033468699455261236];
- endpoint loads 0.02881081291259526 and 0.02881081291259103;
- endpoint slopes +3.631311924773022e-8 and -3.9132167744713666e-7.

This is an observed positive-to-negative slope bracket (a symmetric load
maximum), not an interval-certified exact root or proof excluding every earlier
mode. A coarse trace also shows the branch rising again beyond approximately
d=0.125; that second turning point has not been qualified here.

The `first_limit_point` helper is deliberately restricted to the above default
family and [0.025,0.05] bracket. It has at most 24 bisections, a whole-call
60-second deadline and rejects a final width above 1e-6*h. Each successful
intermediate state is used as an explicit next initial guess; a failed solve
is never automatically retried.

## Tests, scope and next action

The new suite passed **17 tests in 1.23 seconds**. It covers analytic Jacobians
against complex-step differentiation, stress-free geometry, positive initial
stiffness, coarse/fine agreement, off-node and sensitivity residuals, load-slope
and energy derivatives against separate displacement perturbations, spatial
moment balance, the sign bracket, standalone deterministic serialization,
import isolation and finite callback/time/parameter/width failures.

The existing straight postcritical reference suite separately passed **22 tests
in 0.51 seconds**. There is no combined qualification count. All numerical
reference statements above refer only to this fixture and symmetry branch.

Reference SHA-256:
`5F259A3EA47CDA7371F8E719F008C3D4387C1C3CA39B4B8974A44FA62C145E17`.
Test SHA-256:
`3E18A72D6832AFA495886A066380447C2EE6363885572B962B3DE733222531A5`.

Next compare the actual GE-B3 curved assembly with this branch using correctly
transformed nodal directors and a continuation method able to traverse the
limit point. Do not substitute load-control failure for a slope/stability
measurement. Start with a small bounded mesh and record any discrepancy before
expanding or running a formal resource wave. Full spatial stability, refinement
accuracy and independent review remain outstanding.

The larger goal remains active: broad nonlinear section parity, coupled/slender
coverage, robust local stationarity, prestressed modes/dynamics, production
integration and objective beam-shell joints are not closed by this reference.
Only this record, reference and test are added. Existing production mechanics,
B2/B3/Q4/S3 defaults, packages and accepted evidence are untouched. No push,
merge, release or activation. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
