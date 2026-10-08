# E01 linear material-frame work feasibility

Identity: `R8_E01_LINEAR_POLAR_SPIN_INDEPENDENT_DIRECTOR_WORK_V1_DEV`.
Source development only. This diagnostic changes no connection, product dispatch,
checkpoint, historical fixture, tolerance or acceptance criterion. Candidate
physical interpretations require root adoption. No external solver is launched.

## Existing physical question

E01's saved panel is 2 m by 1 m, thickness 0.07 m, with its edge member at
y = -0.5 m and eccentricity z = +0.1 m. The saved torque fields use 8 by 4
Cartesian Q4 cells, 45 shell nodes, nine edge stations and a +100 N m beam-tip
torque. The opposite eccentricity remains mandatory for final acceptance.
Shell root nodes 1, 10, 19, 28, 37 fix all six coordinates. Reference axes are
global X/Y/Z; paired beam and shell reference frames are identity.

The existing native six-row point map uses independent **nodal** rotation:
`u_b = u_s + theta_s cross e`, `theta_b = theta_s`.
Its signs agree with `b3_e4_e01_matching_point_canary.py::bond_rows`.
OpenSees's saved rigid links use that same nodal map, but its ASDShellQ4
drilling/membrane operator differs from E4-PL. The saved reciprocal-work
allocation closes to 4.1554e-13; membrane/drilling contributes 102.2491% signed
and plate contributes -2.2491%. These are cross-work contributions, not positive
energy fractions or proof that either shell model is physically correct.

CalculiX expanded faces instead expose translation samples and a through-thickness
director. Existing `b3_e4_f03_ccx_expanded_seam_trace.py` reconstructs a projected
line tangent and face-pair director. That triad does not recover the original
shell drilling coordinate. A line-tangent yaw and a two-dimensional polar spin
also differ under symmetric in-plane shear. The existing expanded work probe
uses `delta u = t + omega cross r + eta r`; its seventh isotropic expansion
coordinate is distinct from this diagnostic's explicitly named **thickness**
strain. No previous probe or formal F03 campaign is copied or executed here.

## Explicit small-displacement candidate

Only ordered Cartesian XY Q4 rectangles and stations inside a specified host
are admitted. Let N_i be the bilinear shape values and Dxi/Dyi their physical
derivatives. For each corner, q_i contains translation u_i and independent
rotation theta_i. At the reference station:

```
t     = sum N_i u_i
omega_x = sum N_i theta_xi
omega_y = sum N_i theta_yi
omega_z = 1/2 sum (Dxi u_yi - Dyi u_xi)
u_port  = t + omega cross e
p       = [u_port, omega] = B q
```

The yaw formula is the first-order polar rotation of the in-plane deformation
gradient about the identity. It is not a finite-pose quaternion/rotation recovery.
The director increment is `(omega_y, -omega_x, 0)` and stays independent of the
surface-normal increment `(-w_x, -w_y, 0)`. Their difference is transverse shear
`(w_x + omega_y, w_y - omega_x)`. Equating the director to the normal suppresses
this shear and is a different physical restriction.

For a Cartesian expanded face pair at each corner, with explicit ordered lower
and upper translations u-/u+ separated by positive reference thickness h:

```
u_mid = (u+ + u-)/2
omega_x = -sum N_i (u+_yi - u-_yi)/h
omega_y =  sum N_i (u+_xi - u-_xi)/h
omega_z = 1/2 sum (Dxi u_mid_yi - Dyi u_mid_xi)
eta_h   = sum N_i (u+_zi - u-_zi)/h
p7      = [u_port, omega, eta_h] = B7 u_faces
```

This reproduces the shell candidate when the supplied face translations have
the declared midpoint/director field. It does not establish that CCX's expanded
element equations, additional modes or constitutive work equal E4-PL's.
In-plane stretch and other warping modes are not connection coordinates; their
work cannot be inferred from this seven-channel projection.

## Adjoint and controls

For physical port force F and moment M, the full nodal covector is exactly
`B.T @ [F, M]`. Hence `f_nodes.T delta q = [F,M].T B delta q`.
Transferring the wrench to the midsurface station gives `M_station = M + e cross F`.
Support entries are retained; zero supported virtual motion is imposed only
when pairing with an admissible variation. Dropping support forces would lose
reaction provenance. The seventh generalized force is conjugate to dimensionless
eta_h and has units joules, rather than newtons or newton-metres assigned to an
ordinary moment channel.

Focused analytic controls cover rigid translations/rotations, both offset signs,
origin transfer, unit wrench resultants, translational yaw couples, independent
director/shear counterexamples, explicit face-pair/thickness work, unit scaling,
supported virtual work and the constant linear derivative. A nodal theta_z-only
field moves the native nodal-pose port but leaves the recovered-frame port fixed:
this is an explicit incompatibility witness, not an error corrected by tuning.

## Saved-field use and limits

`scripts/r8_e01_material_frame_work.py` accepts existing 8x4 E01 capture JSONs
with one supplied expected SHA256 per input. The preserved cross-work record
binds native capture `2411b64903ed16a5cd7ac5f788b21497975d14df038a3563e9e85e45f5db42bd`
and external capture `b599bba7822f98e6bcac80785bf694eb833aa10cb6c77aa457cb0e4ee28b331c`.
The reader verifies bytes before interpreting fields. Existing output is never
overwritten. No capture is regenerated and no missing field is inferred from a
summary. Lower-edge stations use the host to their right, except the last uses
the host to its left. This explicit one-sided recovery is a diagnostic choice;
incident-cell averaging would define a different discrete map.

## Executed source development evidence

One fresh supervised job ran the 15 focused analytic checks and both original
hash-bound saved captures: **15 PASS in 0.30 s**; whole job 0.846 s, sampled
process-tree peak 61,382,656 bytes. Existing supervisor limits were 600 s/2 GiB;
affinity was fixed to one CPU before child execution, measured OpenBLAS pool
size was one, and sampled numerical/unresolved maximum was one. Numba and the
solver package were not imported; the environment requested JIT off, but there
is no effective Numba/JIT claim for an unimported runtime. The inherited
supervisor's thread ceiling is eight; effective single-pool evidence is recorded
separately rather than claiming that ceiling was changed.

The initial job's three failures/12 passes are retained. All failures were the
new rigid-shear fixture's rounded-decimal cancellation (1.040834e-17 against
1e-17). The final fixture uses binary-exact motions and station coordinates;
the assertion remains 1e-17. No product or scientific tolerance changed.

With explicit one-sided hosts, the nine saved edge stations give maximum absolute
nodal-yaw minus recovered spin 9.039310466e-7 rad (native) and 3.612418391e-6 rad
(external). Maximum absolute director-minus-normal component is 4.289428499e-6
(native) and 5.843587722e-6 (external), dimensionless. These values exhibit
different kinematic channels; they do not establish which engineering law is
correct or an external error percentage. Root-coordinate maxima are zero and
3.968317941e-22 respectively.

Raw [execution/logs](../../.qualification/b3-ge-e4-pl/r8-e01-material-frame-work-dev-20261005-v1/focused-v2/),
[JUnit](../../.qualification/b3-ge-e4-pl/r8-e01-material-frame-work-dev-20261005-v1/junit-v2.xml),
[source/input bindings](../../.qualification/b3-ge-e4-pl/r8-e01-material-frame-work-dev-20261005-v1/binding-v2.json),
[effective runtime](../../.qualification/b3-ge-e4-pl/r8-e01-material-frame-work-dev-20261005-v1/runtime-v2.json)
and [saved diagnostics](../../.qualification/b3-ge-e4-pl/r8-e01-material-frame-work-dev-20261005-v1/saved-fields-v2.json)
remain together. The source/input binding predates this results prose; the
tested script and test bytes are unchanged. No different-family scientific
acceptance or mandatory E01 closure follows.

Outputs report nodal-yaw minus recovered spin and independent-director minus
surface-normal channels. They do not transform saved shell forces into a new
matched model, score a 1% comparison, or qualify a finite footprint. The saved
root-coordinate guard is inherited from the existing cross-work discriminator,
not a new equilibrium/support tolerance.

The next reserved decision is the physical material-frame recovery and sampling
law for the mandatory CCX comparison, including sided force recovery and root
treatment. After that decision, a matched small executable/output/work check can
be scoped. E01's complete observable/floor set, both offset signs, three systematic
two-direction refinements, independent scientific review and full platform gates
remain mandatory. No external execution or new refinement authority follows.

## Finite projected-polar trace proposal

The separate `scripts/r8_e01_objective_polar_trace.py` identity is
`R8_E01_OBJECTIVE_PROJECTED_POLAR_INDEPENDENT_DIRECTOR_V1_PROPOSAL`.
The linear V1 results above remain unchanged. This new map is an unadopted
physical proposal with local derivative controls, not a production connection,
CCX correspondence, supported finite-pose domain or E01 acceptance result.

The reference host is still one explicitly selected Cartesian XY Q4 rectangle
and an inside station. Reference shape values N and the two physical material
derivatives gradN are frozen. Inputs own four current positions x_i, four unit
physical directors d_i, and a physical beam position/rotation r_b/R_b. No native
beam-coordinate reconstruction or retained-variable elimination occurs here.

```
dbar = sum N_i d_i; d = dbar / |dbar|
F = x_current.T gradN
P = I - d d.T; E = P F; G = E.T E
Q = E G^(-1/2); R_s = [Q_1, Q_2, d]
```

For SPD G, Cayley-Hamilton gives `G^2 - tr(G) G + det(G) I = 0`.
Setting s = sqrt(det G) therefore gives
`(G+s I)^2 = (tr G+2s) G`, and the positive square root is
`S=(G+s I)/sqrt(tr G+2s)`. The implementation differentiates the analytic
2x2 inverse of S; it does not fit eigenvectors or alter symmetry. Q is the
two-column polar orthonormalization of the projected tangents, minimizing
their Frobenius distance over orthonormal two-column frames. It differs from
a single projected line tangent under symmetric in-plane shear.

With a declared shell-frame port offset a, the positions/reference pose are

```
r_s = sum N_i x_i + R_s a
e0 = R_s0.T (r_b0 - r_s0)
A0 = R_s0.T R_b0
c_t = R_s.T (r_b - r_s) - e0
c_R = Log(A0.T R_s.T R_b)
Pi = lambda_t.T c_t + lambda_R.T c_R
```

R_s0 is identity for this flat reference. Offsets/reference alignment are bound
once. In particular, the reference translation Jacobian uses the full initial
beam-to-midsurface arm `a+e0`, matching V1's eccentric rigid-arm linearization;
it is not the derivative of a in isolation. The six multipliers are covectors
of these declared constraint coordinates, not presumed printed nodal moments.

Under a common proper spatial rotation U and translation t, d -> U d,
F -> U F, E -> U E, G is unchanged, Q -> U Q and R_s -> U R_s.
Both c_t and c_R are invariant. The director remains independently specified:
projecting F does not impose d equal to the geometric surface normal.
Node positions are centered before forming F to remove a common spatial origin.

### Derivative coordinates and physical work

The 30 local increments are `[delta x_i(3), delta theta_i(3)]` for each of four
nodes followed by `[delta r_b(3), delta theta_b(3)]`. Actual updates are
`d_i(delta)=Exp(delta theta_i) d_i` and
`R_b(delta)=Exp(delta theta_b) R_b`: **left spatial physical updates**.
Existing Jet2, SO(3) exponential/logarithm and small matrix primitives compute
c, its Jacobian and each component Hessian from the same frozen base state.
The returned covector is `Dc.T lambda`, and the multiplier Hessian is the full
`sum lambda_i D2c_i`, including polar, director, offset and logarithm curvature.

At zero increments, the covector acts on physical translation/left-rotation
variations. At nonzero increments, it acts on the parameters of the same
anchored exponential chart. Re-centering at the perturbed state changes that
rotation-coordinate differential. Finite differences of the Hessian therefore
differentiate the same anchored gradient; they do not subtract physical
covectors from two different moving charts. The work-balance helper explicitly
rejects a nonzero-increment chart result mislabeled as physical wrenches.

The common-motion work identity implies zero total force and zero moment about
any spatial origin, using node translation covectors, director rotation
covectors, and the beam pose covectors. At the flat reference a normal moment
on the recovered frame generates a translational couple and no shell theta_z
covector; it does not create or tune a nodal drilling penalty. Translation
increments are metres, rotation increments radians, and Pi is joules.

### Prospective domain and verification limits

Inputs and outputs are owned copies; inputs require finite real data, unit
physical directors and proper beam rotations (numerical validation 1e-12).
The local map rejects director cancellation, projected metric rank loss or
unresolved conditioning, negative frame orientation, unresolved frame
orthogonality, nonfinite derivatives and the existing principal-log chart
boundary 0.9*pi. These are explicit candidate-domain restrictions, not changes
to product admission or scientific tolerances.

The prospective arithmetic margin is `64*eps` for director squared norm and
`det(G)/tr(G)^2`; the latter bounds reciprocal spectral conditioning in 2D.
Frame orthogonality is checked against 1e-9 without symmetry repair. These
representability choices are proposal inputs for independent/root review;
successful tests do not establish a universal roundoff/error bound near these
boundaries. No domain threshold is selected from measured results.

Controls use an independent NumPy eigensystem/SciPy rotation-log value oracle,
V1 reference Jacobian agreement, common finite-motion covariance of covectors
and Hessians, symmetric-shear/director counterexamples, both eccentricity signs,
physical force/moment work and origin transfer, local actual-update derivative
plateaus at three preselected step sizes (2e-4/1e-4/5e-5, <=1e-6 relative), and
conservative Hessian skew <=1e-9. The derivative norm uses the synthetic control's
fixed 1 m translation/1 rad rotation coordinate scales. These local checks do
not supply a constitutive, structural, CCX or physical accuracy oracle.

Unresolved adoption choices include physical director recovery from the external
expanded field, polar versus line-tangent interpretation, station/footprint/root
sampling, sided wrench provenance and a defensible admitted deformation/error
domain. Production six-row nodal-pose points and BL5 remain unchanged. Independent
review precedes any integration; no external execution authority follows.

### Executed finite-candidate controls

The first bounded finite-candidate job completed **31 PASS in 2.14 s**: 16 new
finite controls and the prior 15 linear controls. No finite-job failure or retry
occurred. At the preselected three step sizes, both constraint-Jacobian and
fixed-chart potential-Hessian directional relative errors satisfy 1e-6; the
multiplier Hessian satisfies the 1e-9 skew criterion. Independent value-oracle,
V1 reference-linearization, common-motion covariance, wrench/origin/sign,
director/shear, normal-moment and negative-domain checks all passed. This is a
sampled local derivative result, not a uniform finite-domain error theorem.

The supervisor recorded 3.134 s, sampled process-tree peak 177,270,784 bytes,
one-CPU affinity before child execution, and sampled numerical/unresolved
maximum one under the existing 600 s/2 GiB bounds. Both measured OpenBLAS pools
and Numba report one thread; Numba JIT is disabled. Every imported ANYsolver
module was within this source checkout; there were zero runtime-record errors.
The inherited supervisor thread ceiling remains eight; effective pool and
affinity measurements are recorded separately. No structural assembly/solve,
external solver, reference campaign or fixture generation was executed.

Raw [JUnit](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/junit-v1.xml),
[execution/logs](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/focused-v1/),
[source bindings](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/binding-v1.json)
and [effective runtime](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/runtime-v1.json)
bind this development result. The binding predates this final results prose;
tested script/test bytes are unchanged. The candidate is not adopted, and its
independent mechanics review, external correspondence, physical admission and
different-family scientific acceptance remain pending.

### Independent cancellation finding and algebraic repair

Independent Read review found a real defect missed by the 31 passing V1 controls.
The implementation formed `R_s.T (r_b-center-R_s a) - e0` explicitly. In the
flat reference, a_x = 2^54 can erase an actual 1 m beam shift by cancellation
although the returned derivative remains one. All candidate domain guards can
pass. This is a numerical implementation defect, not an accepted approximation
or a reason to restrict the physical offset or weaken a tolerance. V1 source
bindings and passing evidence remain preserved with this adverse finding.

For the flat reference R_s0=I, the same constraint simplifies exactly to
`c_t = R_s.T (r_b-center) - (r_b0-reference_station)`.
The shell-frame offset a is a port gauge and cancels together with its reference
value; the repaired evaluator never subtracts large a terms in c_t. The reported
physical shell-port position still includes a once. There is no connection-law,
domain-threshold, derivative-coordinate or product change.

New discriminating controls compare values/Jacobians/Hessians with and without
the 2^54 gauge at the flat shifted and genuinely finite states. A separate
nonidentity reference beam rotation control checks A0 handling, the reference
rotation Jacobian, independent finite value oracle and common-motion derivative
covariance. Root has adopted only this algebraic repair; the physical law stays
an unadopted proposal. A new affected finite-suite run is required; unchanged
linear controls need no repetition.

The affected finite-suite V2 job completed **18 PASS in 1.81 s**, zero failures
or runtime-record errors. It included the two new discriminating controls and
all existing finite controls; the unchanged 15 linear controls were not rerun.
Whole supervised execution was 2.743 s, sampled process-tree peak 177,070,080
bytes, affinity one CPU, sampled numerical/unresolved maximum one, both measured
OpenBLAS pools one thread, and Numba one thread/JIT disabled under the unchanged
600 s/2 GiB bounds. No structural or external execution occurred.

Tested repaired script SHA256 is
`06f65b5edc07357be39ca78a512f62e9f70778c12a70057cc4452a8c9b4f0313`;
test SHA256 is
`0dd16ccddd9a06f742017251a3515349570612bd60c56a9486b954331e8ad770`.
V1 bindings/results remain unchanged. V2 [JUnit](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/junit-v2.xml),
[execution/logs](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/focused-v2/),
[source bindings](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/binding-v2.json)
and [effective runtime](../../.qualification/b3-ge-e4-pl/r8-e01-objective-polar-trace-dev-20261005-v1/runtime-v2.json)
preserve the repaired evidence. Binding V2 predates this result prose; tested
code is unchanged. Independent review of the repaired slice remains required,
and neither the passing controls nor algebraic repair adopts the physical law.

## Actual native half-cell local composition proposal

`scripts/r8_e01_native_polar_work.py` has identity
`R8_E01_NATIVE_HALF_CELL_PROJECTED_POLAR_WORK_V1_PROPOSAL`. The physical polar
law remains unadopted. The adapter uses actual `NativeHalfCellPort` reference
lift/frame, endpoint indices, cell identity and active native slots. It does
not average beam nodal rotations, reconstruct a new beam trace, condense a
retained variable, change a history or supply full native element work.

For port weight t, endpoint high/low positions rL/rR and retained rotation Rc,
the authoritative pose is `r=(1-t)rL+t rR+Rc lift`, `Rb=Rc reference.frame`.
`NativeHalfCellPort.pose_pair` computes this at the compensated split-sum
boundary. The adapter obtains that exact base high/low pair and computes
`fsum(r_high,r_low,-shell_origin)` before rounding the relative position.
Its reference arm is bound from the reference pair by the same relative sum.
No displayed single-component port position substitutes for these low parts.

The local chart has 33 coordinates: shell translations/left physical director
rotations (24), endpoint translations (6) and one retained half-cell left
physical rotation (3). The increment of the beam position is
`(1-t)delta_rL+t delta_rR+(Exp(delta_theta)-I)Rc lift`; the beam frame is
`Exp(delta_theta)Rc reference.frame`. Rodrigues difference coefficients evaluate
the lift change directly, without adding/subtracting identity or two large
rotated lifts. The shared bounded polar AD seam differentiates this pose, so
the constraint gradient and multiplier Hessian include lift curvature.

Independently, let J be the map from these 33 coordinates to the previous 30
physical-pose coordinates. Its endpoint blocks are `(1-t)I,tI`, retained
rotation block is I, and port-translation/rotation block is `-[Rc lift]x`.
Then the covector is `J.T g30`, while
`H33=J.T H30 J+sum f_port_j D2r_port_j`. The latter retained-rotation curvature
is explicitly `1/2(e_a cross(e_b cross lift)+e_b cross(e_a cross lift))`.
Omitting it does not give the full multiplier work Hessian.

Shell global slots are explicitly supplied; native global slots are an explicit
native-base offset plus the actual port's nine active slots. Overlap is rejected.
Nodal beam rotations, the other half-cell rotation and 18 resultants per native
element remain explicit and unchanged. The update helper returns a copied
Mechanical using split_sum on endpoint high/low pairs and the native physical
rotation update pattern. It does not issue or commit an owner state. A midpoint
retains its chosen cell side, including different left/right cell rotations.

Force/moment balance uses endpoint forces at their actual high/low positions
and the retained-cell rotation covector, together with the shell covectors;
using the interpolated port position for both endpoint forces loses this work
interpretation. Nonzero anchored-chart gradients are not relabeled as physical
wrenches. Both new/native and affected finite checks remain development evidence.

The combined analytic control uses symmetric in-plane shear g and independent
director `d=Ry(beta) ez`. Projection gives a tangent-plane matrix with rows
`cos(beta)*(1,g)` and `(g,1)`, whose polar angle satisfies
`tan(phi)=g*(1-cos(beta))/(1+cos(beta))`; thus `Rs=Ry(beta)Rz(phi)`.
This is a declared consequence of the proposed trace, not physical endorsement.

The native pose remains a binary64/compensated boundary. The tiny-rotation,
large-lift control checks the analytic lift increment; it does not establish
that a fresh floating `Rc@lift` resolves arbitrary sub-ULP motion for huge
physical lifts. Uniform error/admission limits, external director/frame recovery,
physical law adoption and full native material work remain separate obligations.

### Executed native local controls

The bounded native/affected-finite job completed **31 PASS in 2.69 s**: 13 native
controls and 18 affected finite controls. No failures or retries occurred; the
unchanged linear suite was not rerun. Curved-reference lift/frame and both
cells/reversed references, actual native base pose and slots, independent chain
gradient/Hessian including nonzero lift curvature, compensated endpoint updates,
1e16 common-origin low-part preservation, physical wrench/origin balance,
common-motion covector/Hessian covariance, sided midpoint rotations, inactive
variable preservation and combined shear/director-tilt frame controls passed.
The actual-update Jacobian and anchored-Hessian directional checks satisfy 1e-6
at the same three prescribed step sizes, with conservative skew <=1e-9.

`NativeEvaluation` reports the authoritative **base** beam high/low pose and
frame used to anchor its derivatives. A nonzero `increments` argument changes
the local chart evaluation; it does not issue an updated native state or replace
those base-pose metadata fields. Use the copied actual-update helper and then
evaluate at zero increments for a new physical-wrench interpretation.

Whole supervised execution was 3.771 s, sampled process-tree peak 178,155,520
bytes, affinity one CPU, sampled numerical/unresolved maximum one, both measured
OpenBLAS pools one thread, and Numba one thread/JIT disabled under existing
600 s/2 GiB bounds. Runtime source imports remained inside the checkout with
zero runtime-record errors. No structural assembly/solve, external execution,
refinement, history change or qualification campaign occurred.

Raw [JUnit](../../.qualification/b3-ge-e4-pl/r8-e01-native-polar-work-dev-20261005-v1/junit-v1.xml),
[execution/logs](../../.qualification/b3-ge-e4-pl/r8-e01-native-polar-work-dev-20261005-v1/focused-v1/),
[source bindings](../../.qualification/b3-ge-e4-pl/r8-e01-native-polar-work-dev-20261005-v1/binding-v1.json)
and [effective runtime](../../.qualification/b3-ge-e4-pl/r8-e01-native-polar-work-dev-20261005-v1/runtime-v1.json)
remain grouped. Exact pre-run snapshots preserve the new native script/tests and
the shared polar AD seam; older finite V1/V2 records and snapshots remain intact.
Bindings predate this final prose; tested script/test bytes are unchanged.
Independent review and root adoption remain pending; this is not E01 closure,
an accepted finite deformation/error domain or different-family acceptance.

Supporting independent OpenAI source/evidence review confirmed the cancellation
repair and found no further implementation blocker in this bounded slice. It
identified an adoption-relevant combined-field behavior: for symmetric in-plane
gradient `[[1,gamma],[gamma,1],[0,0]]` and uniform director `Ry(beta) ez`, the
projected-polar frame is `Ry(beta) Rz(phi)` with
`tan(phi)=gamma*(1-cos(beta))/(1+cos(beta))` on the positive-orientation branch.
Thus director tilt and symmetric shear together induce recovered yaw, even though
the separate flat-director symmetric-shear control has zero yaw. This follows
the declared law; it is not a failed objectivity check or an adopted physical
assumption. A combined-field/native-port control belongs in the next connected
slice. No test execution of this combined field is claimed by V2. The review is
supporting evidence, not the mandatory different-family scientific acceptance.

### Native update primitive correction (development V2)

Independent review found that V1's copied update helper used the general
corotational rotation primitive, while retained `Context.advance` uses
`_ge_beam3_p5.algebra.rotation`. For spin `(1e-9,1e-9,0)` and lift
`(0,2^54,0)`, the P5 quadratic series retains `R01 = 0.5e-18`; omitting it
loses approximately `0.0090072 m` in an initially zero x coordinate. This is
an observable update-helper error, separate from large-origin output resolution.
The helper now uses the exact retained primitive. No product law, tolerance,
coordinate layout or candidate physical assumption changed. Original V1's
31 passing checks and exact executed source snapshots remain immutable; they did
not cover this counterexample. A new control invokes the actual `Context.advance`
method through its layout/make boundary, compares all copied Mechanical arrays,
and compares the actual port's high/low position and physical frame.

The single authorized V2 affected-native job completed with **14 PASS**, zero
failures/errors (pytest 1.80 s; JUnit 1.752 s). The unchanged finite suite was not
repeated. Supervisor wall time was 2.7796673 s, sampled peak tree memory
177,745,920 bytes, affinity `[0]`, sampled numerical/unresolved maximum one;
both effective OpenBLAS pools and Numba reported one thread, JIT disabled.
The shared numerical slot was released. Raw binding, exact executed native
script/test snapshots, JUnit, runtime and execution/logs remain under
`.qualification/b3-ge-e4-pl/r8-e01-native-polar-work-dev-20261005-v2/`.
Current native script/test bytes and snapshots were verified against the pre-run
binding. This repair corrects the implementation/update claim; adoption of the
candidate physical law and scientific/different-family acceptance remain open.

### Native gather representability correction (development V3)

Supporting review found that unsigned shell-slot identities could wrap negative
when cast to `intp`, and that adding the native base in NumPy could overflow.
The constructor now validates each original slot and each base-plus-active-slot
sum as Python integers in `0..intp.max` before conversion, normalizes the combined
gather once, checks uniqueness, and retains the immutable normalized gather.
Controls include the actual unsigned `2^63` input, native-base overflow, and the
maximum valid native global slot. AD, coordinate/law definitions, tolerances and
product code remain unchanged. Earlier V1/V2 source snapshots and results remain
preserved; this is an input-validation repair, not scientific acceptance.

The single authorized V3 affected-native job completed **16 PASS**, zero
failures/errors (pytest 1.82 s; JUnit 1.770 s). Supervisor wall time was
2.7954013 s, sampled peak tree memory 178,126,848 bytes, affinity `[0]`, sampled
numerical/unresolved maximum one. Both effective OpenBLAS pools and Numba
reported one thread; JIT was disabled. The numerical slot was released.
Raw binding, exact executed native script/test snapshots, JUnit, runtime and
execution/logs are preserved under
`.qualification/b3-ge-e4-pl/r8-e01-native-polar-work-dev-20261005-v3/`.
Current native script/test bytes and snapshots match their pre-run hashes.
No finite-suite repetition, structural solve, external solve or qualification
execution was performed. Candidate physical adoption remains reserved.

### Prescribed homogeneous-field shear discrimination

This bounded tooling control uses one straight unit-length two-half-cell native
beam (42 retained coordinates), with an identity reference section frame and
zero lift, under the same Cartesian Q4 homogeneous midsurface field. Nodal and
retained cell frames are prescribed per each law; resultants are preserved.
The reference beam height is `thickness/2 + eccentricity`. L1 uses section offset
`-eccentricity ez` and shell top `thickness/2 d`, while projected-polar uses the
full beam-to-midsurface arm. Thus neither comparison introduces a reference
station, section-frame or offset mismatch. Both cells use their actual native
ports and their corresponding actual local constraints.

For independent director `ez`, let `F` denote the deformed material tangent
columns. On these positive-orientation fields the projected-polar yaw is
`atan2(F21-F12,F11+F22)` and L1 material-line yaw is `atan2(F21,F11)`.
For a unit reference x chord, physical section strain is independently
`U.T @ (F ex) - ex`. The actual retained `compensated_strain` primitive yields
length-valued integrated chord changes; division by each reference chord length
produces this strain. The twelve endpoint Log entries are also evaluated with
the unchanged retained kinematic primitives, without material response or solve.

At `gamma = +/-0.2` the predictions are:

| Shell field | Polar yaw | L1 yaw | Polar physical in-plane beam shear | L1 shear |
| --- | --- | --- | --- | --- |
| `ux=gamma*y` | `-atan(gamma/2)` | `0` | `gamma/sqrt(4+gamma^2)` | `0` |
| `uy=gamma*x` | `atan(gamma/2)` | `atan(gamma)` | `gamma/sqrt(4+gamma^2)` | `0` |
| symmetric in-plane shear | `0` | `atan(gamma)` | `gamma` | `0` |

Polar axial strains are respectively `2/sqrt(4+gamma^2)-1`,
`(2+gamma^2)/sqrt(4+gamma^2)-1`, and `0`. L1 axial strains are respectively
`0`, `sqrt(1+gamma^2)-1`, and `sqrt(1+gamma^2)-1`.
A common finite rigid rotation must give the same frame and zero chord/endpoint
strains for both laws. An independent-director control with `F ex=(1,0,h)` and
`F ey=(0,1,0)` must give frame `I` and actual transverse beam shear `h` for both
laws, despite the tilted geometric surface normal.

These are imposed-field kinematic consequences, not prescribed reactions,
global equilibrium, material energy or an instability mechanism. Inequivalent
section rotations/chord shear settle distinct coupling semantics; they cannot
select a physical law or justify automatic substitution. Root retains physical
adoption and external/scientific acceptance.

The authorized new-controls-only job completed **16 PASS**, zero failures/errors,
with 16 previously tested controls deselected (pytest 2.19 s; JUnit 2.141 s).
All 16 field/cell records are preserved in `homogeneous-results.jsonl`. Actual
local gap components across both laws were at most `1.66533453693773e-16`;
all twelve endpoint Log entries were zero. Both signed shear cases and both
native cells matched the independent strain/frame predictions.

For positive `gamma=0.2`, measured normalized strains were:

| Field | Polar axial | Polar in-plane shear | L1 axial | L1 in-plane shear |
| --- | --- | --- | --- | --- |
| `ux=gamma*y` | `-0.004962809790010958` | `0.09950371902099894` | `0` | `0` |
| `uy=gamma*x` | `0.01493793401418882` | `0.09950371902099894` | `0.01980390271855692` | `2.78e-17` |
| symmetric | `-1.11e-17` | `0.20000000000000007` | `0.01980390271855692` | `2.78e-17` |

Negative gamma reversed shear/yaw signs with the predicted even axial strains.
Both finite rigid-motion controls had zero chord and endpoint strains to the
existing `2e-14` control threshold, including nonzero thickness/eccentricity.
Both independent-director controls retained transverse beam shear `0.2`, without
substituting the tilted geometric normal for the physical director.

The concrete development disposition is **inequivalent laws; declare distinct
semantics and prohibit automatic substitution**. L1's projected material-line
frame aligns the beam section x axis with the prescribed projected chord, while
projected-polar transports the section with the recovered surface polar frame.
Their respective zero local constraints admit different physical chord shear
under the same prescribed shell field. Neither is selected by these outcomes.
The next reserved decision is which physical section-rotation/shear meaning the
intended E01 coupling and its external recovered material-frame reference must
represent; an external comparison must match that choice before scoring it.
There is no claim of global equilibrium, reactions, energy, instability or
physical/scientific acceptance from these prescribed fields.

Raw source bindings, exact executed source/test snapshots, JUnit, runtime and
execution/logs reside inside the existing V3 development record at
`r8-e01-native-polar-work-dev-20261005-v3/shear-v1/`. Tested script SHA-256 is
`85d613c5b8e6927508b13c4072d0710c4bc3db246477b5fe7ec311e236f531d4`; test SHA-256 is
`5ae4edcd53f8fbca9c39d259c63499799087ad9698536c1eb6fadb29d905d4a4`.
Current script/test bytes and saved snapshots were verified against the binding.
Supervisor wall time was 3.3108253 s, sampled peak tree memory 178,089,984 bytes,
affinity `[0]`, sampled numerical/unresolved maximum one; both effective OpenBLAS
pools and Numba were one thread and JIT was disabled. The numerical slot was
released. All earlier source copies/bindings remain preserved. No product law,
retained layout, scientific criterion, structural/external solver or campaign
was changed or executed.
