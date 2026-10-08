# Physical B2 conservative reference-buckling development checkpoint

State: implemented experimental development candidate verified against the
assigned focused source checks. Root adopted the bounded law and controls
execution and acceptance; no F12/B14 qualification or production claim.

The actual Q4/S3 public owner is `ExperimentalB2Q4PanelAnalysis` in
`_stiffened_shell_b2_q4_panel_experimental.py`. The beam-only
`_stiffened_shell_b2_experimental.py` is not the shell workflow; root corrected
ownership to include the actual panel's buckling/capability seams. Existing
static APIs, profile/operator identities, stiffness, affine T/u0 and C remain
protected. The intended extension uses that same public factory and owner.

## Principal uncertainty and bounded decision

An existing member helper integrates constant N times transverse centerline
slope products. An existing point helper computes the objective joint Hessian
pulled through affine station/fit ports. Neither is a complete physical
reference-prestress operator: member sectional/director/shear terms and physical
port second derivatives are missing. Numerical agreement with an affine-only
candidate would not resolve this uncertainty.

The next useful decision is one complete second-order work/metadata contract,
not a parameter sweep. Once adopted, the discriminating controls are exact
reference first-derivative parity, actual common finite rigid motion, independent
scalar work second variations and the full supported constrained pencil. No
numerical run is authorized at this checkpoint.

## Objective physical beam station continuation

At a finite nodal state, let the two actual section rotations be R0 and R1.
Use their proper geodesic midpoint frame
`Qc = R0 Exp(0.5 Log(R0.T R1))` and the translated nodal midpoint as origin.
Unrotate nodal positions into Qc, subtract the reference centered positions,
and use `Log(Qc.T Ri)` as relative nodal section rotations. Apply the exact
existing physical B2 linear station trace to these local deformation coordinates,
then reconstruct the station centerline and section orientation through Qc.
This is a proposed spectral kinematic continuation, not a public nonlinear B2
constitutive law. A common left rotation and translation leave all local
deformations unchanged, so the reconstructed physical station transforms
objectively. `Exp(linear station rotation)` plus an affine station position,
without this removal/reconstruction, does not establish finite objectivity.

At reference, in the original local section frame, omega is the mean nodal
rotation. The geodesic midpoint's rotation-vector expansion is omega through
second order. If di is nodal translation minus mean translation and Xi is a
reference centered endpoint, the first deformation translation is
`di - omega cross Xi`; the first relative rotation is `theta_i - omega`.
For perturbations a,b the translation second derivative is
`-omega_a cross di_b - omega_b cross di_a`
`+ 0.5*(omega_a cross (omega_b cross Xi) + swap)`;
the relative rotation second derivative is
`-0.5*(omega_a cross theta_i_b + omega_b cross theta_i_a)`.
The existing trace preserves all six reference rigid fields, so removal and
reconstruction give the exact original first station derivative, including
the actual scalar/generalized shear-flexibility trace.

For a physical eccentric beam port at section offset d, its translation is
centerline plus R d. Besides the reconstructed centerline Hessian, its second
derivative contains
`phi_ab cross d + 0.5*(phi_a cross (phi_b cross d) + swap)`.
Its orientation chart also contains the relative/midpoint composition's
second derivative. Omitting either changes eccentric nonzero-multiplier work.

## Physical shell fit and attachment work

The existing shell port fits translation/rotation to nodal translations with
equal vertex weights. A proposed finite continuation is the proper orthogonal
polar rigid fit of the same vertices; it does not identify the unused nodal
drilling rotation with a physical port rotation. The reference centroid is
the mean of vertices, and `ri` are centered reference vertex positions.
Let `G=sum(skew(ri).T skew(ri))`. Then
`phi_a=G^-1 sum(ri cross dui_a)`, exactly the old first rotation fit.
For centered nodal perturbations, its reference second derivative is
`phi_ab=G^-1 sum((phi_a cross ri) cross dui_b`
`+(phi_b cross ri) cross dui_a`
`+0.5*(phi_a cross (phi_b cross ri)+swap) cross ri)`.
Centroid translation has zero Hessian. Noncollinear planar support gives
positive G under the same actual geometric prerequisites as the static fit.

For the existing objective pose joint and actual multiplier lambda, the complete
attachment curvature is
`J.T H_joint(lambda) J + sum(gradient_joint_i(lambda)*H_port_i)`.
Both shell and beam physical port Hessians enter. An affine C/static attachment
has zero static Hessian; that fact cannot replace this physical second variation.

## Member stress reconstruction and governing physical choice

For a section point rho=(0,y,z), a full sectional Green candidate places
`X(s,rho)=centerline(s)+R(s)rho`. The initial section traction is
`t=(sigma_xx,tau_xy,tau_xz)`. Its first work is exactly
`N u_x' + Qy*(u_y'-theta_z) + Qz*(u_z'+theta_y)`
`+ Mx theta_x' + My theta_y' + Mz theta_z'`, matching the existing six-channel
force-flexibility strain convention. Its second work includes centerline
`u_a' dot u_b'`, director-gradient stress-weighted moments,
`e1 dot second_variation(R rho)'`, and shear Green work. A transverse-slope-only
N candidate is a separately named lower-dimensional extension, not this law.

Current `GeometricMetadata` supplies positions of origin, centroid and shear
center and an optional geometric polar radius. It does not supply stress-weighted
Wagner data. Identical six resultants can have different self-equilibrated
section stresses and different `integral sigma_xx*(y*y+z*z) dA`. General bending
requires third area moments and a declared stress reconstruction. Neither
stiffness S nor mass can invent these data; missing terms cannot silently be zero.

A complete candidate datum is source-bound section quadrature: explicit y,z,
positive physical area weights and a physical 3x6 traction-reconstruction map
at each point. Its defining resultant contract is
`sum(weight * [I; skew(rho)] * traction_map) = I6`.
Applied to the actual reference section resultants, it supplies axial, bending,
torsion and shear stress-weighted work without stiffness-derived geometry.
Root must adopt the stress/strain measure, reconstruction meaning, validation
criteria and admitted stress fields before this becomes an implementation/API.

A narrower centered uniform-axial-stress law still requires explicit section
area and a 2x2 transverse area-second-moment tensor for complete Green sectional
work; an optional scalar polar radius alone does not provide both bending-plane
director terms. Such a subset must leave mandatory general bending/torsion
completion visible and refuse missing data.

Interior attachments also require a decision: the ordinary station port is the
unloaded member trace, while equilibrium section recovery can include point
traction jumps. Their prestress must not be mixed without a compatible field.
Endpoint-only POINT/nodal-dead-load admission would avoid that unresolved
loaded-port/bubble mismatch, but is a bounded subset rather than full F12/B14.

## Shell authority boundary and mandatory remaining breadth

Actual direct18 S3 V2D geometric stiffness explicitly admits only its frozen
uniform membrane-compression policy. Nonzero bending-compression or stress-
second-moment data raise `NativeParityCapabilityError`. Reusing that kernel
cannot establish general bending prestress, and this task does not authorize
bypassing the authority or changing the qualified S3 selector. Q4 has its own
qualified geometric-state kernel, whose actual prestress-state contract must
also be respected. An accepted GE state is not a B2 reference-linear state.

Root adopted the guard-compatible shell law and reference-linear state capture
on 2026-10-06. Q4 uses its actual native recovered N/M at four Gauss points,
and homogeneous physical second stress moment N*h²/12. Its existing
compression-positive kernel is negated exactly once into tensile-sign G.
S3 uses the separately named frozen thin/uniform-membrane approximation:
the physically nonzero through-thickness second moment is omitted, not zero.
Both use actual reference-linear preload recovery; no accepted history is made.

The reversible candidate admits endpoint POINT, zero prescribed displacement,
and Cartesian dead nodal forces only. Rotational RHS couples, nonzero prescribed
prestress, loaded interior ports and footprints refuse. Internal point moments
and their full objective coordinate Hessian remain included. Initially the shell
admission requires exact zero forbidden transverse-shear resultants, exact zero
S3 bending resultants and exactly uniform S3 membrane samples. This strict policy
claims no arithmetic-zero tolerance; roundoff can conservatively refuse a case.
No independently certified recovery-operation error bound has been implemented.

The public owner exposes `reference_buckling_capabilities` and typed `buckling`.
The preload is solved by its existing static method. The compiled tensile-sign
operator obeys K + eta G; the full constrained sparse pencil uses -G on its
right-hand side and massless algebraic point coordinates. Returned physical
equation and compatibility residual budgets remain 1e-8 and 1e-9. The spectral
identity binds owner geometry/operators, preload, traction sources, port policy
and assembled G. No global dense inverse/nullspace or stiffness-derived stress
datum is introduced. Existing static and modal policies retain their identities.

Source datum is explicit physical quadrature in the member reference/constitutive
frame: positive area weights, rho=(0,y,z), and S11/S12/S13 reconstruction from
six local resultants. Its six-resultant certificate uses an elementwise backward
work bound 128 eps times absolute contribution sum, plus dimensionless forward
six-resultant identity at 1e-10. Moment rows and columns are normalized by the
explicit datum's transverse length; finite arithmetic is required. The member
first-work check separately normalizes moments by member length and uses a
stable relative norm at 1e-10; neither check has a dimensional floor.
This proves first work, not uniqueness of higher stress moments. A source with
self-equilibrated axial stress can have the same six resultants and a different
Wagner operator. Different datum conventions currently refuse.

The default example is a genuine two-member connected square-section Q4 public
workflow, with explicit source-bound traction records for both members. It uses
the existing keyword-only factory and static multi-element admission. The new
`reference_buckling_capabilities` exposes the actual Q4/S3 kernel policies;
the historical generic capability schema retains its existing meaning.

Focused development runs preserve every failure. V2 failed 12/15 instances:
11 factory calls incorrectly used positional arguments, and the first derivative
coarse step was incorrectly required to pass independently of its plateau.
V3 failed 11/15 because the initial example had only one member, violating
existing multi-element admission. V4 passed 11/16, including independent full
sectional scalar Green work (scalar and coupled), objective point work, beam
derivatives, datum/cancellation/refusal controls and two legacy public static
oracles. Its five workflows failed before geometric assembly because the new
caller expected spectral `ok` instead of the static owner's `completed` status.
V5 passed six affected/new instances (nine deselected), including Q4/S3/mixed
public spectra, full descriptor QZ and beyond-crossing shift, default workflow,
S3 bending refusal and failed-preload preservation. The default public workflow
returned load factor 24.60872920125391, policy
`B2_PHYSICAL_REFERENCE_GREEN_POINT_BUCKLING_V1_DEV`, and nonqualified status.
V6 passed two new controls (15 deselected): member/point common rigid-motion
path including gradient-acceleration work, and cancellation inside geometric
assembly before identity/spectral publication. Together V4/V5/V6 provide 19
unique passing instances by impact reuse, not a fresh 19-case campaign. All
V2/V3/V4 failures and bound source snapshots remain preserved.

All runs used Python 3.14 at `C:/Python/Python314/python.exe`, pinned NumPy
2.5.3/SciPy 1.18.1/Numba 0.68.0/llvmlite 0.50.0, CPU affinity 0, numerical
pools and Numba threads 1, JIT disabled, and unforced backend. The supervisor
bounded each job to 600 s / 2 GiB sampled process-tree RSS. V5 took 27.741 s
with 219,578,368 B sampled peak; V6 took 7.483 s with 219,811,840 B. These are
development supervision observations, not performance or memory qualification.
V5 recorded 245 actual source ANYsolver imports; this is not installed evidence.

Evidence and final manifest live in
`.qualification/b3-ge-e4-pl/r8-b2-reference-buckling-dev-20261006-v1/`.
Installed-artifact verification, physical reversal/reflection and equivalent
datum/unit covariance, reference/external/refinement evidence and required
different-family independence remain unmet. The isolated member and endpoint
stress/point terms have development controls; broader mechanical qualification
and the remaining attachments/shell fields are not thereby established.
Full line, footprint, interior loaded-point, general bending/Wagner, torsion,
reference-field and external/convergence F12/B14 obligations remain mandatory.
This checkpoint does not advertise any of them as implemented or accepted.

No body retry, F03 formal/closed campaign, canary read/run, external solver,
historical equation, sibling edit or worker Git operation was performed. Root
launched and supervised the explicitly authorized source development jobs.
