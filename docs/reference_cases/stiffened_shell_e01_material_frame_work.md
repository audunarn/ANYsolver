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
