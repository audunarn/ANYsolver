# Astra independent analytical review

Reviewer: gpt-6-astra, high effort, independent from Mistral's implementation
assignment. Read-only source/equation assessment; no numerical commands,
imports, tests, edits or workers. Parent separately verified source/equations.

## Finding

The existing beam frame is not energy-objective for general nonzero small
local mixed bending with unequal bending stiffnesses. The suspected effect
survives cancellation of the torsional rigid mode. A full work-conjugate
pullback differentiates that same energy; it cannot repair this objectivity
failure while preserving the deformation map and local potential.

Sources: corotational.py:170-184 (_beam_rigid_rotation),238-285 (deformation
map); elements.py:3866 (_local_linear_stiffness),4577-4664 (ordinary elastic
Beam2 local potential). Native-corotational element, generalized-section and
fiber branches are excluded from this finding's local-law derivation.

## Exact counterexample family

Reference/current straight chord along x, no translations or attachment
offsets, section axes aligned with y/z. Choose identical nodal rotations
R1=R2=Exp(v), v=(0,b,c), r=sqrt(b*b+c*c)>0. Initially extracted twist is zero,
local translations vanish and local rotations are v. With unequal effective
bending stiffnesses, the existing local energy is

    W = Cy*b*b+Cz*c*c,
    Cy = 6*E*Iy/(L*(1+phi_w)),
    Cz = 6*E*Iz/(L*(1+phi_v)).

Here phi_w/phi_v are existing beam shear correction parameters, not rotation
coordinates. Common axial nodal rotation has zero torsional strain and energy.
Equal transverse rotations with fixed chord translations are not a rigid mode.

Superpose Q=Rx(gamma),0<gamma<=pi/6. Positions on x stay unchanged; nodal
rotations become Q*Ri. The code's extracted twist is

    alpha = 2*acos(cos(gamma/2)*cos(r/2)),
    t = alpha*sin(gamma/2)*cos(r/2)/sin(alpha/2).

Consequently delta=gamma-t is nonzero, with expansion

    delta = ((gamma-sin(gamma))/(8*sin(gamma/2)^2))*r*r + O(r^4) > 0

for sufficiently small nonzero r. The residual nodal rotation is
Rx(delta)*Exp(v), rather than Exp(v). Its logarithm's transverse components
obey the exact relation

    [b',c'] = lambda*Rot2(delta/2)*[b,c],
    lambda = (eta/sin(eta/2))*(sin(r/2)/r),
    eta = 2*acos(cos(delta/2)*cos(r/2)).

For b=c=epsilon and Cy!=Cz, the energy change has leading term

    W'-W = 2*((gamma-sin(gamma))/(8*sin(gamma/2)^2))
           *(Cz-Cy)*epsilon^4 + O(epsilon^6),

which is nonzero. Small epsilon can obey the agreed local-rotation/strain
envelope; this failure is not contingent on large local deformation.

This is analytical non-invariance, not a measured test/tolerance failure.
The review's illustrative numerical suggestion epsilon=.02 was outside the
agreed local-rotation envelope and is NOT adopted or executed. No numerical
witness is needed to apply the analytical unchanged-frame STOP.

## Exact sign confirmation (same reviewer, bounded follow-up)

The parent checked the expansion and requested confirmation without tools or
numerical evaluation. The reviewer confirmed the following strict argument:

For small positive gamma,r, alpha>gamma. Rewrite the extracted twist as

    t = alpha*cot(alpha/2)*tan(gamma/2).

Since x*cot(x/2) is strictly decreasing on the relevant interval,
0<t<gamma, hence0<delta<gamma and sin(delta)>0. Also eta>r, and
x/sin(x/2) is strictly increasing for0<x<pi, so lambda>1. Choose Cz>Cy and
b=c=epsilon>0. With rho=(Cz-Cy)/(Cy+Cz)>0, the exact relative energy change is

    (W'-W)/W = lambda^2*(1+rho*sin(delta))-1 > 0.

Thus no cancellation or uncontrolled asymptotic remainder is needed to prove
the non-invariance. It persists for arbitrarily small epsilon, including
local rotation magnitudes below0.01rad; gamma may be the fixed15degree pose
so the total nodal rotation stays well below30degrees. An illustrative
epsilon=5e-4rad was discussed analytically only; no numeric strain, energy
magnitude or threshold exceedance is claimed or measured.

## Recommendation

The local potential pairing and the full pullback formula are compatible.
Objectivity is a distinct prerequisite and is false for this admitted beam
family under the existing frame. Apply the user's unchanged-frame STOP;
do not change the frame, restrict to circular sections/pure-axis bending,
relax criteria, or start a new formulation inside this task.

The original review distinguishes an optional later numeric witness from the
analytical result. Parent does not launch that witness after the STOP. No
numerical inference, uncertainty bound, or measured accuracy claim is made.
