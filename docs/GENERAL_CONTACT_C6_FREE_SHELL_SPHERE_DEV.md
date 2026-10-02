# Guided Q4 / free sphere impact — development profile

Source-tested development capability; engineering acceptance and release remain open.
Run `examples/general_contact_free_shell_sphere_impact.py` with ANYsolver installed.
The example presses a physical bottom skin, opens after impact, and reports both-body
force/momentum, equilibrium and the independently enclosed represented path gap.

Use ordinary `solve_transient_contact` and `TransientConfig`, explicitly selecting
`ContactTransientSolverControls(allow_free_sphere_dev=True,
allow_free_shell_sphere_dev=True)` and `ContactSolverSettings(pair_motion='general')`.
Supply one `ContactFreeRigidBody` with positive mass, isotropic centre inertia and
initial linear/angular velocities. Its centre starts at the named sphere point.
The profile is `PLANAR_GUIDED_Q4_FREE_ISOTROPIC_SPHERE_NEWMARK_DEV_V1`.
Existing callers retain their selected route.

Admission requires planar-reference qualified Q4, isotropic elastic material,
fixed zero rotations and fixed in-plane translations under the actual constraint
transformation. Independent nodal normal motion remains deformable. Every free
direction is checked independently of its reduced-coordinate scaling. S3, finite
rotation, anisotropic inertia, friction, multiple bodies and section/material
extensions are outside this profile. Its history suffix is developmental and has
now passed a shell-specific driven two-body/work/active-restart test.
Use `--load-history` on the example for a piecewise-linear force ramp. Its
`...NEWMARK_HISTORY_DEV_V1` identity binds history and swept-check controls into V6.
Every work row is checked against independent force-times-velocity integration;
applied impulse accounts for changed momentum. Changed history, enclosure tolerance
or split cap rejects restart. Body fields agree numerically; bitwise identity is
not claimed. [Driven evidence](d1_review_support/C6_FREE_SHELL_SPHERE_HISTORY_20261003.md)
reuses the unchanged installed wheel after verifying all208 imported-source hashes.

The existing sphere nodal-pressure penalty potential is retained: face support and
weighted gaps are aggregated before applying the normal law. This is neither a new
pointwise penalty law nor a Hertz-pressure model. Three sphere-centre coordinates
join the same constrained Newmark equilibrium system. Both-body residual and
tangent derive from the same work, including shell physical offsets and sphere
cross blocks. Central frictionless traction gives no centre torque; isotropic spin
advances exactly and does not affect spherical geometry. No restitution is assigned.

The shared driver retains state transactions, bounded cutback, cancellation,
rejected-trial cleanup and V6 restart. Identity binds geometry, constraints,
material, mass/inertia, initial velocities, profile and numerical controls.
Incompatible continuation rejects. The maximum reduced size remains 512.

Two complete path checks precede acceptance. Exact rational tensor Bernstein
controls enclose both Q4 coordinates and the cubic endpoint-Hermite time field
relative to the moving sphere. A separate cubic certificate retains the owner's
selected-side domain at each face centroid. It cannot be inferred from radial
distance. Both checks share `maximum_beam_swept_subdivisions` (512 by default);
`beam_swept_gap_tolerance_m` controls distance-enclosure width (1e-10 by default),
distinct from the explicitly dimensioned physical interaction gap budget.
These inherited control names apply to this shell profile too. Unresolved bounds
fail explicitly; sampled positions never supply a lower collision certificate.
The certificate covers the declared interpolation, not the continuum trajectory.

The symmetric fixture passes independent 24×24 continuum quadrature/two-body
Newmark response, virtual work/tangent, force/moment balance, impulse/momentum,
active split restart and rejection/cleanup checks. Translational energy defect
is 0.4623% at dt=0.0005 s and 0.1133% at dt=0.00025 s; spin is checked separately
and excluded from that error denominator. This toy's 2 mm penetration budget is
an explicit development setting, not the programme qualification budget or an
application recommendation. A nonuniform normal-motion case verifies retained
shell modes and normal momentum, without establishing spatial accuracy.

[Slice evidence](d1_review_support/C6_FREE_SHELL_SPHERE_SLICE_20261003.md) records
source, effective runtime, historical test defects and review limitations.
