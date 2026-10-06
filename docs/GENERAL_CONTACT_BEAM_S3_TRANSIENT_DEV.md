# Elastic beam / deformable S3 impact development route

Use the ordinary `solve_transient_contact` with `TransientConfig` and explicit
`ContactTransientSolverControls(allow_deformable_beam_s3_dev=True)`.
The example `general_contact_beam_s3_transient.py` supplies a fully declared
model. This is development verification, not C6 qualification or admission of
general beam/shell impact.

## Mechanical scope

One classical B2 or B3 round beam and one E4-PL S3 V2D elastic skin comprise
all elements. The existing moving-normal line Jet2 potential, physical skin
side/offset, complete both-body residual and tangent are reused. S3 rotational
coordinates and rates must be exactly zero; the actual model constraints must
annihilate these rows of the reduction. Actual reduced physical mass must be
positive definite. There is no added inertia, damping, spring or restitution.
The first profile supports initial impact and constant external dead loading;
time histories, friction, genuine caps/rims, finite rotations, native retained
beams and multiple faces remain unsupported.

## Complete represented path

For each accepted proposal the two endpoints and rates define the actual cubic
Hermite motion. All four Bernstein controls of both bodies are mapped through
the physical skin chart. B3 spatial Q2 controls and cubic time controls form a
complete tensor hull. Subdivision uses de Casteljau, bounded by existing finite
controls; unresolved intervals reject the proposal and use the ordinary finite
cutback path.

At an exact anchor let C=e1 cross e2. Vertex displacement enclosures give
edge uncertainties delta1/delta2. The cross uncertainty is
|e1| delta2 + |e2| delta1 + delta1 delta2. A positive normal magnitude floor and
reference orientation floor are required. Exact stored-coordinate Fraction
arithmetic and directed norm conversion enclose the mathematical hull;
128 epsilon times the uncancelled reference/chart magnitude supplies the
separate binary64 chart/Hermite allowance for this bounded profile. Unit-vector
conversion errors are explicitly included.

The gap enclosure uses n(t) dot delta-r + (n(t)-n0) dot r0, with true unit n(t).
The anchor extent bounds r0 and the first term is bounded by |delta-r|, so no
omitted displacement-normal product remains. The same decomposition bounds
each inward unit rim direction. Hidden target motion, normal collapse and rim
crossing are covered by the full controls, rather than checking hull edges.

## State and consumer contract

The existing shared Newmark residual, general tangent solve, material candidate
commit/rollback and cancellation services are used. New opt-in profile and V17
checkpoint bind the contributor contract and path budgets. Old profiles retain
their schema and analysis-contract keys. Resume does not restore an executable
object from data. The existing transient archive adds one exact known inert
`DeformableBeamS3Results` record; old result fields and numeric wire tags remain.

## References and reporting

The matched uniform-normal fixture is strain free by explicit constraints.
Its independent masses are rho*A*L and rho*t*area, and effective stiffness is
line_stiffness*L. The independent discrete Newmark and flight/sine/separation
references quantify response and temporal sensitivity. Its energy is kinetic
plus the unchanged line potential; the fixed gate is 1%. This formula does not
assert that general von Karman stored energy equals one-half u Kref u.

Unequal target nodal motion is a separate genuinely deforming case. Its checks
recover actual structural internal work, mass inertia and generalized constraint
reactions at accepted states, then form each body's physical force and moment
about global origin, including position cross force. Forces and moments use
separate 0.5 N / 0.25 Nm scales, gate 1e-6. Local virtual work and directional
tangent use 1e-5. The fixture physical gap gate is 10 micrometres. Generalized
reaction components are not automatically physical moments without the node and
skin work maps. No general deforming-body energy acceptance is claimed here.

## Separate actual flexural B3 fixture

`general_contact_beam_s3_transient_flexural.py` uses the same installed public
solver/profile and physical inputs. Its B3 nodal z and ry coordinates are free;
other beam coordinates and S3 rotations remain declared model constraints.
The beam's uniform-normal MPC is absent. Initial normal rates have a quadratic
interior bow and matching ry rates equal to minus the initial w-rate slope.
The beam's genuine rho*Iy rotary mass remains unchanged. Unequal S3 normal
rates produce target deformation. The earlier uniform fixture/results remain
separate evidence.

Bending is demonstrated by nonzero ry derivative and the independent bending
storage integral, with shear storage reported separately. An interior quadratic
point becomes active while both physical beam endpoints remain open; this
discriminates actual Q2 curve integration from endpoint chord substitution.
The completed path opens, and splitting at an exact accepted time preserves
the B3 continuation checkpoint and displacement arrays exactly.

For this fixture the independent beam potential is
one-half integral [EA*(one-half*w-prime-squared)^2 + EIy*ry-prime-squared +
GA*kz*(w-prime+ry)^2] dx. Own Q2 shape functions and three-point Gauss
integration give the exact polynomial integral. Its gradient is independently
compared to actual structural work and its differentiated gradient to the
structural tangent in the actual free chart. Kinetic energy includes both
translation and physical rho*Iy rotary inertia.

The admitted S3 V2D native elastic response uses fixed small-strain operators
even when the outer assembler names its kinematics `von_karman`. In this
normal-only, zero-rotation, zero-offset fixture, membrane, curvature and PL
storage vanish. Direct shell storage is one-half*A*phi-squared*gradw.T*H*gradw,
H=(5/6)*G*t*I. MIN3 phi-squared=2*psi/(1+2*psi), with psi equal to the sum of
the physical rotational bending diagonal divided by the unrelaxed rotational
shear diagonal. The independent test builds shape gradients and the MIN3
L/M rotational shear polynomials and integrates three Hammer points. It reads
no production contact kernel, stiffness matrix or relaxation factor in this
reference. Comparison to the actual elastic shell force and baseline matrix
separately establishes the applicable linear recovery; this is not a generic
von Karman shell energy assertion.

Own Q2 gap coefficients, real roots, active intervals and the polynomial
square primitive supply the independent complete line potential and minimum.
The flexural fixture's 1% elastic energy gate uses these two structural
potentials, the independent line potential, and actual physical mass. Local
work/tangent tests use h=(1e-7,3e-8,1e-8) with the unchanged 1e-5 gate. Body
wrench and physical 10 micrometre gap gates remain unchanged. No new inertia,
admission profile, solver policy or qualification claim is introduced.

The reported beam mean-curvature metric is the endpoint ry difference divided
by reference length, maximized over saved time states. It is a spatial mean,
not the exact maximum of the Q2 rotation derivative. The bending-storage
integral uses the complete Q2 derivative. Historical raw records named this
mean metric `maximum_curvature`; their executed definition is preserved.

The same flexural fixture also runs at dt=5 microseconds with unchanged model,
initial conditions, law, supports, controller and gap budget. Its independent
structural/line plus physical-mass energy defect improves relative to the
preserved actual 10 microsecond case. This is a bounded temporal discriminator;
broader enforcement and spatial refinement/qualification remain open.


## Affine rotational descriptor development profile

`allow_rotational_beam_s3_dev=True` selects
`ELASTIC_B2_B3_AFFINE_ROTATIONAL_S3_ENDPOINT_HERMITE_DEV_V1` and V18
checkpoints. Existing fixed-director profiles/settings/identities remain unchanged.
S3 physical skin positions are exactly the formulation-owned affine map
`x_skin=x_node+h*d_ref+h*(theta cross d_ref)`, including eccentric nodal couples.
Rotations carry no artificial mass. Complete endpoint structural/contact equilibrium
is solved by the shared Newmark driver. Algebraic velocity satisfies the TOTAL
endpoint tangent equation `Z.T K_total v=0`; physical acceleration remains Newmark.
Null-coordinate acceleration is the finite endpoint-velocity secant numerical
record, initialized to zero. It is **not** a continuum C2 DAE acceleration.

The declared event segment is the all-coordinate endpoint Hermite polynomial
from accepted/candidate u/v, mapped through the affine skin map. Its complete
hull is bounded for gap/rim/orientation. This certifies that represented segment,
not a nonlinear DAE lift. Endpoints whose MINIMUM gap lies within geometry-scaled floating touch
uncertainty refuse, including isolated continuous-H interior minimum touch.
Other topology changes with strictly negative minimum need not refuse because
this rate contract uses only the continuous endpoint tangent, not its derivative. Full-line
one-sided ambiguity is never silently resolved using the open tangent.

New result records retain `shell_moment` as geometric skin moment about origin
zero and expose `shell_nodal_work_moment` and `shell_affine_moment_discrepancy`.
The latter is `sum(h*(theta cross d_ref) cross f)`. Forces are physical N,
moments N*m. This affine small-rotation distinction cannot establish finite
rotation/angular-momentum acceptance. Initial states must be virgin zero,
unforced, algebraically force/velocity consistent. General initial/preloaded,
finite-rotation, friction and true-rim impact remain unsupported.

V18 stores the preceding accepted reduced velocity and actual last duration;
resume cross-checks the null acceleration against that secant before assembly.
The zero-step initialization uses the declared zero null-rate seed.


## Directional full-line source development candidate V19

`allow_directional_beam_s3_dev=True` selects a separate profile and V19
checkpoint. V17/V18 control identities and summary fields remain unchanged.
At genuinely exact full-line zero gap, velocity is selected from
`Z.T (K_struct*v + epsilon*L*integral B(s).T min(B(s)*v,0) ds)=0`.
Physical velocity modulo the actual mass-null basis is fixed. Stored binary
chart data are tested exactly as rational numbers: oriented C dot e is positive,
constant on the line, and its square equals radius squared times C dot C.
No positive/negative nearzero geometry is snapped to touch. Exact isolated
minimum point touch uses the continuous distributed tangent; unresolved
floating ties retain explicit refusal.

B includes moving-face normal variation and the actual affine skin A. Its
rational numerator is quadratic; the common normal-length square root cancels
from directional work/Jacobian. Complete quadratic rate-root inventory uses
finite exact sign brackets. Degree-four polynomial integrals are evaluated on
all negative-rate intervals, with root-strip/conversion bounds. The null solve
uses safeguarded Newton and finite iteration/halving limits. Supplied floating
contact H is removed before directional H is introduced, avoiding double count.
Numerical null acceleration remains the labelled endpoint secant with V18
history validation; represented Hermite and affine wrench semantics are unchanged.
The flat virgin assembled fixture can have B*Z=0; its public execution cannot
prove general rotational coupling. A separate nontrivial scalar quadratic-rate
oracle tests that coupling. Source-only checks do not replace installed or full
impact verification, temporal acceptance, finite rotations or a C2 DAE lift.


### Approved V19 installed coupling and first-touch extension

The frozen tilted local production adapter now has executed nonzero B*Z evidence
against a byte-matched installed package. Its mass-nullity is two, contact-null
rank one (uniform ry); it is off equilibrium and is not a dynamic initial state.
The ordinary public V19 fixture starts at exact flat full-line touch, then has
81 saved states to 0.8 ms, 32 active states and final physical gap +24.2928 um.
The minimum gap is -5.37376 um, within the unchanged 10 um gate. Actual target
rotation and rate are nonzero (max 3.28933e-7 rad / 4.37810e-4 rad/s), with
nonzero rotational contact couple. This is a small-motion development exercise.

Independent B3/defined MIN3/line/mass energy defect is 0.0315729% at 10 us and
0.00772189% at 5 us: both pass 1% and refinement improves the defect. Independent
Q2 polynomial line-potential discrepancy at selected states is <=3.60e-19 J.
Actual endpoint algebraic and per-body inertia/support/structural/contact work
wrenches pass the unchanged 1e-6 gates at separate 0.5 N / 0.25 Nm scales.
Fresh full/prefix/resume checkpoints are exact when the split uses the actual
accepted timestamp. A decimal split slightly before that timestamp changes the
physical final truncated step; the preserved failed comparison is not regraded.

First-touch and installed public example execution complement the local tilted
oracle. They do not establish nonzero null coupling at an equilibrated tilted
full-touch event, a C2 DAE acceleration, finite rotations or engineering acceptance.
No product changes, mass modifications, branch snapping or new wheel were needed.


## Equilibrated loaded initial directional profile V20

`allow_equilibrated_directional_beam_s3_dev=True` is a separate exclusive
DEVELOPMENT profile. It accepts only a supplied nonzero elastic initial pose
and a constant serializable nodal-only LoadCase, with genuinely exact full-line
touch, complete reduced structural/contact-minus-load equilibrium and consistent
true-null directional velocity. No time load history or callback is admitted.
The zero initial null-acceleration seed is numerical and allowed only after full
equilibrium; subsequent secant/represented-Hermite semantics are unchanged.
Load, initial pose, setting and profile bind a separate V20 restart; V19 guards
and all inactive-setting legacy identities remain unchanged.

The tilted example uses an explicitly manufactured equilibrium load from actual
structural/contact assembly. That construction is not independent validation
of structural constitutive laws. Work balance subtracts initial stored energy
and constant-load work, normalized by a positive frozen impact kinetic scale.
A half-u-dot-force number is labelled heuristic only; nonlinear storage uses
elastic radial work without commits and is source-justified, not an independent
structural formulation oracle. The independent directional reference uses
rational moving-normal coefficients and analytical negative-rate integration.
The affine nodal-work versus geometric-skin wrench distinction still applies.
No C2 DAE, finite-rotation or engineering-acceptance claim follows.
