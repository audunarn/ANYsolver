# Independent analytical review — Slice 3

State: scientific review of the proposed reference, 2026-10-18. No product or
test edits, imports, FE solves or pytest runs were performed. The calculations
below use section geometry and elementary rod virtual work independently of
production assembly and MPC reduction. Supervisor adoption remains required.

## Decision

The circular arc is a valid reference for an explicitly **cylindrical,
plane-section strip benchmark**, including eccentric cases. It is not an exact
reference for the free-width shell with one attached beam line solely because
the applied end resultants equal a composite pure moment.

Adopt the supervisor's proposed benchmark constraints prospectively: at every
shell longitudinal station all nodes share ux, uz and ry; set uy, rx and rz to
zero. Leave the common ux, uz and ry independent between stations; clamp only
the root station. Retain the real finite-rotation eccentric beam MPC and, for
nonmatching meshes, its actual interpolation. With nu=0 these width constraints
supply only the missing width redistribution, without Poisson restraint changing
the intended axial/bending law. Their reactions have zero work on the admitted
row motion. This defines a constrained strip benchmark, not a claim that the
original free-width stiffened plate has an exact circular-arc solution.

The final-state dead load prescription below is sufficient. A follower-force
API is unnecessary if only the terminal state is compared. The load ramp does
not then follow the circular-arc family and must not be reported as doing so.

## Convention and section assumptions

Reference shell midsurface: (s,y,0), 0<=s<=L. Beam centroid: (s,y_b,e).
Positive rotation phi about global +y bends the cantilever toward negative z.
The 0.01 x 0.002 m beam rectangle means 0.01 m in y and 0.002 m in z;
changing that orientation changes the oracle. The constituents are additive
energetic shell/beam components, including at e=0; geometric overlap does not
subtract material in this idealized model. Use linear elasticity, not the S355
plastic curve used in the separate continuation gate.

Let

    As = W*t;                  Is = W*t^3/12
    Ab = b*h;                  Ib = b*h^3/12
    zbar = Ab*e/(As+Ab)
    B = E*[Is+Ib+As*zbar^2+Ab*(e-zbar)^2]
      = E*[Is+Ib+As*Ab/(As+Ab)*e^2].

B is the composite bending rigidity about the neutral axis. For different
moduli use EA-weighted zbar and EI terms, but that generalization is not needed
for this assignment.

For E=210e9 Pa, W=0.1 m, t=0.001 m, b=0.01 m, h=0.002 m:

    As=1e-4 m^2; Ab=2e-5 m^2
    Is=8.333333333333e-12 m^4; Ib=6.666666666667e-12 m^4
    E*Is=1.75 N m^2; E*Ib=1.40 N m^2
    e=0:       zbar=0;                 B=3.15 N m^2
    e=0.002:   zbar=0.0003333333333 m;  B=17.15 N m^2.

The initial x-axis beam frame in elements.py::_beam_rotation_matrix has local
y=global y and local z=global z when no exceptional orientation is supplied.
Thus the required bending inertia is Iy=Ib above.

## Independent kinematics and constitutive derivation

Use curvature per reference longitudinal length k=Phi/L and phi(s)=k*s.
Let t=(cos(phi),0,-sin(phi)), n=(sin(phi),0,cos(phi)). The cylindrical
Kirchhoff kinematics are

    r(s,y,z) = r_s(s) + y*ey + z*n(s)
    r_s'(s) = lambda_s*t(s)
    lambda(z) = lambda_s + z*k
    epsilon(z) = lambda_s-1 + z*k.

Zero total section axial force gives lambda_s=1-zbar*k, hence

    epsilon(z)=k*(z-zbar),
    Ns=E*As*(-zbar*k),
    Nb=E*Ab*(e-zbar)*k=-Ns.

An equivalent independent derivation minimizes, over lambda_s,

    U/L = E/2*[As*(lambda_s-1)^2
                    +Ab*(lambda_s-1+e*k)^2+(Is+Ib)*k^2].

It gives U/L=B*k^2/2 and M=B*k. This is the extensible rod law with
engineering axial strain, reference-length curvature and linear section
constitutive response. Small material strains coexist with arbitrarily large
rigid rotations. Shell and beam centroid axial strains are generally nonzero;
setting both to zero is incompatible with e*k != 0 and the rotating offset.

The neutral-axis radius is 1/k, shell midsurface radius Rs=1/k-zbar and beam
centroid radius Rb=1/k+e-zbar. All share the same angle, not the same arc length.
For either centroid with initial z=zj, its exact tip displacement is

    ux_j = [1/k+zj-zbar]*sin(Phi)-L
    uz_j = [1/k+zj-zbar]*[cos(Phi)-1]
    uy_j = 0; theta_j = (0,Phi,0).

Do not compare the beam probe to the shell/neutral-axis radius. At e=0.002,
Phi=60deg the beam and shell uz differ by exactly -0.001 m.

## Constituent end loads and spatial moments

At the final tip use

    F_shell = Ns*t(Phi)
    F_beam  = Nb*t(Phi)
    m_shell = (0,E*Is*k,0)
    m_beam  = (0,E*Ib*k,0).

Shell force and moment are the width-integrated values. A consistent uniform
edge traction uses tributary weights [1/4,1/2,1/4] for ny=2; their sums must be
one. Under the adopted row constraints any distribution with the same admitted
virtual work is equivalent, but uniform consistent loads retain a clearer
physical interpretation. Beam values act at its centroid tip node. Do not add
another total M=B*k moment: that would count the eccentric force couple twice.

The total force is zero. The deformed separation is e*n(Phi), and n cross t=ey,
so the total tip moment about the shell centroid is

    M_y = E*(Is+Ib)*k + e*Nb = B*k.

The equality uses Ns+Nb=0; the same total moment holds about the neutral axis.
This also checks the eccentric load signs independently. With e>0 and k>0 the
beam centroid force is tensile and the shell centroid force is compressive.

Dead global nodal forces equal to these vectors have the same terminal virtual
work as follower tangential forces. At intermediate load factor lambda, the
current rotation usually differs from Phi; the dead forces are then not
tangential and their eccentric spatial couple differs from lambda*e*Nb. That
changes the loading path but not the specified terminal equilibrium. Convergence
and residual evidence are still required, and intermediate arc comparisons are
not valid under this dead prescription.

For an additive rotation-vector covector p and spatial moment m,

    delta_psi = J_l(theta)*delta_theta,
    p = J_l(theta)^T*m,
    m = J_l(theta)^(-T)*p.

This agrees with corotational.py::spatial_moment_from_rotation_covector (line
739 at inspection). For theta=(0,phi,0), J_l(theta)*ey=ey, so a moment only in y
has p_ry=My exactly at 30 or 60 degrees. This shortcut is invalid for general
multiaxis rotations/moments. Total reactions must use deformed force arms and
spatial moments, not raw rotation-vector covectors in a general state.

## Why the free-width eccentric shell is not exact

For the proposed uniform cylindrical field, Ns is a nonzero constant when e is
nonzero. Since t'=-k*n, shell membrane equilibrium needs an interface normal
load proportional to Ns*k distributed across its full width. The beam's
equal/opposite required normal load arrives through one coupling line. A shell
with y-independent curvature and no transverse bending/shear cannot redistribute
that line load into the required uniform normal load. End loads alone do not
remove this local equilibrium mismatch. Width bending/warping or interface
reaction redistribution must occur. The plane-section row constraints supply
the latter and make the integrated composite rod reduction legitimate.

An especially poor alternative is applying all composite moment to one shell
edge or to the beam tip in a free-width model: resultant equivalence does not
prevent torsion, shear lag or a local end boundary layer. Saint-Venant arguments
alone do not establish a 1% bound for this thin strip and a tip quantity.

The concentric e=0 case has Ns=Nb=0 and lacks this particular normal-transfer
obstruction. It still needs the appropriate constituent moment distribution
unless row constraints explicitly enforce the common section field.

## Small-strain and discrete-map limits

At e=0 the largest material strain magnitude is h*k/2: 0.05236% at 30deg and
0.10472% at 60deg. At e=0.002 it is (e+h/2-zbar)*k: 0.13963% and 0.27925%.
Thus the classical small-strain/large-rotation premise is reasonable for linear
elastic material. It is not a proof that every alternative finite-strain stress
measure, shear theory or discretization differs by less than 1%. In particular,
the 60deg eccentric elastic stress at the beam outer fiber is about 586 MPa;
an S355 plastic material would invalidate this linear elastic oracle.

The inspected corotational path removes rigid rotation before calling native
element response (corotational.py::_corotational_deformation_state and
::corotational_work_conjugate_response). Its centroid extension and local
curvature therefore have the required engineering-strain, small-local-rotation
continuum interpretation; this review does not establish a finite-mesh error
bound or certify every native element constitutive path.

The retained map is

    ub=sum(w_i*us_i)+(R(sum(w_i*theta_i))-I)*e_vector,
    theta_b=sum(w_i*theta_i).

On this planar single-axis family, linear interpolation of rotation vectors is
exact for phi=k*s and has no noncommuting-rotation error. Require partition of
unity and reproduction of the beam attachment's reference x coordinate.
Interpolation of translations between shell stations samples a chord rather
than the exact circle; the arc-chord position error is O(k*hs^2). Thus the
nonmatching discrete map is not exactly the continuum arc even when its
rotation is exact. Matching meshes also approximate arcs by element chords.
These are legitimate convergence errors to measure, not permission to derive
the oracle from the production map, adjust loads to the observed solution, or
relax the specified tolerances.

### Prospective 1.5-ratio chord check

There is a particularly important deterministic refinement risk for nb=1.5*nx.
Let h=L/nx, delta=k*h, sinc(a)=sin(a)/a. Sample the analytical cylinder at shell
stations, interpolate its shell translations linearly, and use exact linear
single-axis rotation interpolation for beam nodes. Every two shell elements
contain three beam elements, at s/h=0,2/3,4/3,2. Set

    C=lambda_s*sinc(delta/2), D=e*k*sinc(delta/3).

The shell chord stretch is C. For the two outer beam elements the exact chord
stretch on that candidate state is

    lambda_outer=sqrt(C^2+D^2+2*C*D*cos(delta/6));

for the central beam element crossing a shell vertex it is

    lambda_mid=lambda_s*sinc(delta)+D.

Consequently the mean beam-minus-shell chord stretch is

    Delta=[2*lambda_outer+lambda_mid]/3-C,

where the continuum centroid stretch difference is e*k. At leading order in
delta and small e*k,

    Delta-e*k = -lambda_s*delta^2/24 + O(e*k*delta^2,delta^4).

The first term is a *differential* axial-strain error, which common axial motion
cannot remove. Using the exact formulas above at Phi=60deg, e=0.002 m:

|nx|Delta-e*k|bias divided by e*k|
|---:|---:|---:|
|8|-7.1392985830e-4|-34.0876%|
|16|-1.7862573077e-4|-8.5288%|
|32|-4.4665390427e-5|-2.1326%|

Here e*k=0.0020943951024 and lambda_s=0.9996509341496. The 16-to-32 change in
this bias alone is about 6.40% of the intended eccentric centroid strain
difference. At e=0 the same interpolation creates a nonzero mean differential
chord strain despite zero continuum centroid strain difference.

This is an independent geometric candidate-state check, not a prediction of the
nonlinear equilibrium error: actual FE energy, shears, local curvature and row
motion influence the response. In particular, 2.13% strain bias must not simply
be reported as 2.13% tip error. However, eccentric coupling contributes 14/17.15
of the composite rigidity, so this is consequential and provides no prospective
basis to assume the requested 1% analytical/0.25% refinement gates will pass at
nx=32. The matching case has a common chord factor and lacks this leading
differential term. If the nonmatching case fails, distinguish interpolation
discretization from the now-explicit continuum reference and from solver
equilibrium defects. Keep the gate open and preserve evidence; do not fit the
reference, alter physical inputs or silently add refinements beyond authority.

Comparing only the tip rotation when the tip rotation was prescribed would be
tautological. Prefer the force/moment terminal prescription above and compare
both shell and beam tip displacements and common rotation. Record whether errors
are componentwise or Euclidean before observing results; avoid percent errors
for reference-zero components.

## Scalar reference values

Positive My/ry convention above, displacements in m, moment in N m, force in N.

|e|Phi|M total|Nb=-Ns|shell ux|shell uz|beam ux|beam uz|
|---:|---:|---:|---:|---:|---:|---:|---:|
|0|30deg|1.6493361431|0|-0.0450703414|-0.2558726308|-0.0450703414|-0.2558726308|
|0|60deg|3.2986722863|0|-0.1730066569|-0.4774648293|-0.1730066569|-0.4774648293|
|0.002|30deg|8.9797190015|3665.1914292|-0.0452370081|-0.2558279726|-0.0442370081|-0.2560959218|
|0.002|60deg|17.9594380030|7330.3828584|-0.1732953320|-0.4772981626|-0.1715632812|-0.4782981626|

Own centroid moments are independent of e: at 30deg ms=0.9162978573,
mb=0.7330382858 N m; at 60deg both double. Reversing the bend must reverse
rotation and loads consistently; the eccentric axial stretch changes sign too,
so merely negating uz while keeping the same radius is not the signed solution.

## Required adoption before analytical acceptance

1. Explicitly adopt the constrained cylindrical-strip scope and row constraints.
2. Fix rectangle orientation, probe identity, elastic material and strain law.
3. Adopt constituent end forces/moments and terminal-only dead-load equivalence.
4. Keep 1% analytical and 0.25% refinement gates unchanged, with declared error
   normalization; assess actual FE evidence independently.

These clarify the benchmark physics; they do not add numerical execution
authority, establish qualification or prove acceptance of the implementation.

The referenced Abaqus benchmark supports the classical single-beam pure-moment
relation ML/EI=2*pi*n and illustrates end moments/force couples. It does not
establish the eccentric free-width shell/beam reduction made here. Source:
[Abaqus geometrically nonlinear cantilever benchmark](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEBMKRefMap/simabmk-c-nlgeocantilever.htm),
Loading and Results sections, accessed 2026-10-18. The composite extension and
counterexample above are this review's independent derivation.
