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
