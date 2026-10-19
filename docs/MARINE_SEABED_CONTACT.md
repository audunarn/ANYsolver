# Compliant frictionless line/seabed contact — development

`anysolver.marine_seabed` exposes immutable `SeabedContact` and the stateless
`seabed_contact_force` law. `MooringLine.contact_diameters` enables selected
segments; `MooringLineAssembler.seabed_contact` supplies the horizontal static
floor. The existing coupled body/node driver assembles its force, K and C at
trial states and stores contact evidence in accepted frames. It introduces no
extra endpoint DOFs, inertia, friction or committed history.

For each segment-end lump, projected contact area is `A = D*L0/2`, using the
**reference** material length. With z-up floor elevation `zb`, surface gap is
`g = z - zb - D/2` and penetration is `delta = max(-g, 0)`. Explicit stiffness
`kb` has units Pa/m and damping `cb` has units Pa*s/m. Effective coefficients
are `k=A*kb` and `c=A*cb`. For `g<0`, the elastic force is `Fe=k*delta` and total
normal force in legacy v1 is `Fn=max(0, Fe-c*vz)`; for `g>=0` both are zero. All normal forces
act upward. Adjacent segments contribute their own diameters, gaps and branches
before summation at a shared endpoint. Contact and hydro diameters must agree
when both are enabled on one segment.

The three-argument constructor and nested `marine_seabed_contact_v1` preserve
that legacy law. Opt-in `marine_seabed_contact_v2` requires explicit positive
finite `activation_depth_m`. Its damping multiplier is
`f=min(delta/activation_depth_m,1)` and `Fn=max(0,Fe-c*f*vz)` on penetrating
points. This continuous activation removes the legacy switch's demonstrated
finite-step no-root interval in the registered incoming fixtures. It changes
near-boundary damping/rebound: the depth is constitutive input, not a numerical
tolerance, calibrated property, universal default or timestep-derived quantity.
At active ramp points, normal K is `k-c*vz/activation_depth_m` and C is `c*f`;
saturated points use k and c. Select the saturated-side tangent at the ramp corner
and zero tangents on inactive/clipped branches. Storage and clipped outgoing loss
remain as below. No arbitrary coupled convergence guarantee follows.

The diagnostic damping component is `Fn-Fe`, including release clipping. Potential
energy is `U=.5*k*delta**2` and dissipation is `D=-(Fn-Fe)*vz>=0`. Thus normal
power satisfies `Fn*vz + dU/dt + D = 0`, including a penetrated endpoint opening
fast enough that its total normal force clips to zero. A positive elastic force
and negative damping component can then cancel; these are accounting components,
not independent physical contact tractions. At exact gap or raw-force zero,
the inactive tangent is selected. No smoothness across branch boundaries is
claimed. On the legacy active branch, endpoint `K=-dF/dp` and `C=-dF/dv` have `k` and
`c` normal entries. The common work-conjugate endpoint Jacobian and finite-rotation
follower/geometric corrections map these into mechanical coordinates.

Contact supports declared fixed anchors, free nodes and rigid-body fairleads.
Seabed reaction is the negative world sum of contact endpoint forces; fixed-anchor
reactions include their total assembled forces. Diagnostics retain segment and
endpoint indices, each lump's gap and force-active mask, maximum penetration,
potential energy, dissipation and world seabed reaction. Accepted driver frames
also store body and node `contact_elastic`/`contact_damping` force components.
Cancelled jobs retain only atomic accepted frames and their contact evidence.

The named inner schema `marine_mooring_contact_v1` contains `seabed_contact`
and optional per-line `contact_diameters`, plus the existing hydrodynamic
environment when applicable. Mechanical/hydrodynamic records without contact
retain their old schemas. Unsupported or malformed contact intent is refused;
serialization cannot silently remove it. Floor elevation must be below still
water and agree with an enabled hydrodynamic environment's depth/datum.

This is a compliant penalty model: finite stiffness permits finite penetration.
The diagnostics do not establish exact nonpenetration or a scientifically
admitted penetration tolerance. Public fluid kinematics still refuse endpoint
centers below the environment floor; deeply penetrated combined hydro/contact
trials fail rather than silently clamping/extrapolating water kinematics. Existing
fully submerged line restrictions also remain. Prospective stiffness, penetration,
mesh/time-step and energy criteria must be established for each qualification
case. W6 v4's registered frictionless numerical rehearsal has independent
assessment: 47 records and 524 predicates pass with the installed candidate.
The scope is those fixtures and explicit uncalibrated v2 inputs; legacy v1 incoming
contact remains unadmitted. Independent final assessment now admits the exact
registered frictionless slice, including eight installed saved application cases
(855 frames) and native GPU/software replay. Assessment and scope are recorded at
C:/ANYworkspaceWork/anymarine-evidence/w6-frictionless-final-assessment.md.
Partial wetting when needed, combined fluid/contact extensions and regularized
friction remain outstanding. This is not full W6 or production/release acceptance.

MoorDyn's public input documentation describes bottom stiffness/damping applied
over projected `D*L0` area. The explicit radius gap and no-tension release here
are declared choices; this document does not assert identical MoorDyn behavior:
https://moordyn.readthedocs.io/en/master/inputs.html
