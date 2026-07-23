# FE Solver Theory Notes

This note records the theoretical basis and validity limits for the production
`anysolver` package.  The implementation target is an ANYsolver
beam-shell solver, not a general-purpose nonlinear FE code.

## Units and DOFs

- SI units are used internally: m, N, Pa, kg.
- Every node has six DOFs ordered as `ux, uy, uz, rx, ry, rz`.
- Shells, beams, boundary conditions and MPCs share the same global DOF space.
- Fixed DOFs and beam-shell MPC slave DOFs are eliminated by the transformation
  `u = T q + u0` before static, buckling and transient solves.

## Shell Element

`ShellElement` is a 3/6-node triangular or 4/8-node quadrilateral
Mindlin-Reissner shell. At each integration point the element builds a local
orthonormal frame from the surface tangents:

```text
local x = projected xi tangent
local z = shell normal
local y = local z cross local x
```

Global nodal translations and rotations are transformed to that local frame
before evaluating membrane strain, bending curvature and transverse shear.
The elastic constitutive blocks are:

```text
D_membrane = E h / (1 - nu^2) * [[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu)/2]]
D_bending  = E h^3 / (12 (1 - nu^2)) times the same plane-stress block
D_shear    = kappa G h I, kappa = 5/6
```

The 4-node shell uses an MITC4-style assumed natural shear interpolation.  The
covariant shear strains are sampled at the four edge midpoints and interpolated
to the 2x2 integration points.  This avoids the excessive thin-plate shear
stiffness of a fully integrated displacement Q4 without introducing the
one-point reduced-shear hourglass mode.

The 8-node shell uses full 3x3 membrane/bending integration and reduced 2x2
transverse shear integration.  When `ShellElement(..., reduced_integration=True)`
is used for S8R/Q8R, membrane/bending, mass, geometric stiffness, and stress
recovery are evaluated at the reduced 2x2 rule.  The S8R/Q8R path adds a small
nullspace-projection hourglass stiffness: the reduced-integration free-element
nullspace is computed, the six rigid-body modes are projected out, and the
remaining modes receive a small positive stiffness scaled from the element
stiffness.  The intent is to remove spurious zero-energy modes while keeping
rigid motion and reduced-point patch behavior unchanged.  Broad production use
still requires external benchmark coverage for representative distorted shell
panels.  Both shell topologies include a small drilling stabilization strain:

```text
theta_z - 0.5 * (dv/dx - du/dy)
```

This gives the otherwise free drilling rotation a finite stiffness while
leaving rigid rotation about the shell normal strain-free.

### Stress output frames

`compute_stresses` returns membrane/bending/shear components in the
**per-integration-point local shell frame** (local x follows the projected xi
tangent) by default.  On rectangular and parallelogram elements that frame is
constant; on skewed or distorted elements it rotates from point to point, so
default components must not be compared against global-axis expectations.
Frame-invariant outputs (von Mises, principal values) are unaffected.  Pass
`return_global=True` to additionally obtain `global_*_top/bot` surface stress
components in the global frame; the S4 constant-strain patch metrics compare in
that frame.  The 3-node/6-node triangle shells follow the same convention.

## Mass and Pressure Loading

Shell mass is integrated consistently with the shell shape functions.  The
translational mass scales with `rho h`; rotary inertia scales with
`rho h^3 / 12`.  Beam mass uses translational lumping plus section rotary
inertia for torsion and bending rotations.

Shell pressure is assembled as a consistent nodal load:

```text
f_i = integral_A N_i p n dA
```

where `n` is the element normal implied by the element node order.  Follower
load moments are not included in the linear load vector.

## Linear Transient Dynamics and Slamming V1

The transient solver advances the constrained/reduced linear system:

```text
M qdd + C qd + K q = F(t)
C = alpha M + beta_R K
```

The default method is Newmark average acceleration:

```text
beta_N = 1/4
gamma_N = 1/2
```

`TransientConfig(hht_alpha=...)` activates the Hilber-Hughes-Taylor alpha
method with `-1/3 <= alpha <= 0` (`alpha = 0` reproduces plain Newmark).  The
equilibrium is enforced in the alpha-weighted form

```text
M a_{n+1} + (1+alpha) (C v_{n+1} + K q_{n+1}) - alpha (C v_n + K q_n)
    = (1+alpha) F_{n+1} - alpha F_n
```

with the HHT-optimal Newmark parameters `gamma = 1/2 - alpha` and
`beta = (1 - alpha)^2 / 4` derived automatically when `beta`/`gamma` are left
at their defaults.  HHT-alpha is second-order accurate and unconditionally
stable in this range, and introduces controlled high-frequency numerical
dissipation, which suppresses the non-physical stiff-mode ringing that plain
average-acceleration Newmark preserves in impact and slamming responses.  The
same alpha-weighting is applied to the sphere-impact solvers: the linear path
weights the structural external+contact load, and the nonlinear path weights
the internal force and damping terms in the Newton residual with the tangent
scaled by `(1+alpha)`.  The rigid sphere itself keeps the plain Newmark
kinematics; the alpha-weighting acts on the structure side of the contact.

For constant `dt`, `K`, `M` and Rayleigh damping, the solver reuses the sparse
factorization of the effective stiffness:

```text
K_eff = K + a0 M + a1 C
```

The slamming v1 load model is prescribed pressure over selected shell elements.
`PressurePatch` supports explicit element IDs, a centroid-selected rectangular
or circular area, or a custom selector callback.  Pressure magnitude is a
constant, a time table or a callable.  This is a structural response model to a
given pressure history; it is not fluid-structure interaction and does not add
hydrodynamic added mass.

Validity limits for v1 slamming:

- linear transient response about the undeformed structure,
- prescribed shell-normal pressure only,
- centroid inclusion for patch area selection,
- fixed time-step integration,
- no cavitation, water-entry kinematics or pressure feedback.

The limited rigid-sphere collision mode is a structural transient contact
extension, not a general contact solver. A single rigid sphere has user
supplied mass, radius, initial point, travel vector and speed. Contact is
detected against shell surfaces and, when explicitly enabled, beam-axis
segments using the current deformed translational geometry. The normal contact
force is frictionless, compression-only penalty contact:

```text
F_n = max(k_p g - c_n v_n, 0)
```

where `g` is penetration, `v_n` is relative normal velocity from the contact
target to the sphere center, `k_p` is penalty stiffness and `c_n` is optional
contact damping. The equal and opposite shell load is distributed with shell
shape functions at the closest projected surface point. Beam contact splits
the reaction between the segment end nodes.

Production controls add internal event substepping for fast sphere travel,
automatic penalty recommendation from impact inertia and representative shell
stiffness, optional top/bottom/signed shell-thickness contact surfaces, and
duplicate adjacent-element reduction to the deepest active contact point by
default.  The linear impact solver additionally auto-substeps while contact is
active to keep the step below a fraction of the penalty period
(`0.2 sqrt(m/k)`), capped by `max_event_substeps`, so a coarse `dt` with a
stiff penalty stays accurate and convergent instead of producing spurious
forces; free flight and post-separation are not refined.  The nonlinear
implicit path relies on its time-step cutbacks for the same protection.
`validate_contact_configuration` provides structured preflight diagnostics for
unsupported target meshes, missing density, excessive travel per step and
time-step/contact-period warnings. After nonlinear Newton cutbacks, a bounded
distress carryover can pre-subdivide subsequent base steps and then decay as
convergence recovers; `preemptive_substep_count` makes that behavior explicit.

`SphereContactConfig(beam_contact=True)` additionally enables direct
sphere-to-beam contact: each 2-node beam contributes one contact segment and
each 3-node quadratic beam two, with a circular section proxy radius
(`cross_section["contact_radius"]`, defaulting to the equivalent-area circle).
Contact is closest-point-on-segment penalty contact against the deformed beam
axis, with the reaction split linearly between the segment end nodes.  This
covers edge-on strikes on stiffeners and girders; it remains a line-contact
engineering model, not profile-resolved surface contact.

Validity limits for sphere impact:

- one rigid sphere,
- shell midsurface targets plus (opt-in) beam axis segments,
- frictionless normal contact only,
- no rigid-lid, MPC or shell-shell contact targets,
- no spin, rolling, friction or crack propagation.

`NonlinearTransientConfig(kinematics="corotational")` runs the nonlinear
impact equilibrium with the corotational element response (large rigid
rotations with plasticity in the corotated frame); the default remains von
Karman.  The nonlinear impact energy diagnostics account for structural
kinetic energy, an internal work measure from the committed internal force
(exact strain energy while elastic), and the sphere kinetic energy; the
instantaneous penalty-spring energy during contact is the only term outside
the balance.

Material-nonlinear impact:

- `NonlinearTransientConfig(enabled=True)` activates an opt-in implicit
  Newmark/Newton impact path.  The equilibrium uses structural inertia,
  damping, nonlinear element internal force, and iterated sphere-shell penalty
  contact in each time step.
- Shells use the existing layered plane-stress J2 plasticity and beams use the
  existing nonlinear/fiber response where configured.  The geometric scope is
  the current solver nonlinear element theory, not full updated-Lagrangian
  shell impact.
- `PlasticImpactDamageConfig` drives softening/erosion from committed plastic
  state after a converged nonlinear substep.  Failed Newton trials do not
  commit plastic state or damage.  Three criteria are available:
  - `"fixed"`: element fails when max equivalent plastic strain exceeds the
    manual `threshold`.
  - `"mesh_scaled_gl"`: same trigger, but the critical strain is computed per
    shell element as `0.056 + 0.54 * (thickness / element_length)` (GL /
    RP-C208-style linear mesh scaling with `element_length = sqrt(area)`), so
    coarse elements that cannot resolve necking fail earlier.
  - `"rtcl"`: RTCL (Rice-Tracey / Cockcroft-Latham, Tornqvist 2003) ductile
    damage accumulation on top of the same mesh-scaled critical strain.  Per
    integration point (Gauss point x thickness layer), the damage increment is
    `dD = w(eta) * d(eps_p) / eps_cr` where `eta` is the stress triaxiality of
    the return-mapped plane-stress state and the weight `w` is 0 for
    `eta <= -1/3` (compression), the Cockcroft-Latham branch for shear-
    dominated states (`w(0) ~ 0.577`), 1 at uniaxial tension (`eta = 1/3`)
    and `exp(1.5 eta - 0.5)` beyond (`~1.65` at equibiaxial tension).  The
    element softens/erodes on `max_point D`.  Beam fiber sections use the
    uniaxial limits (tension fibers weigh 1, compression fibers 0).  This is
    the criterion validated in ship-collision studies; compared to plain
    plastic-strain thresholds it does not erode the compressed side of a dent
    and accumulates monotonically, which is markedly more stable.
  - `"rtcl_modified"`: RTCL with the critical strain recalibrated by the
    plane-strain weight `w_ps = exp(sqrt(3)/2 - 1/2) ~ 1.4424`, so plane-
    strain tension (`eta = 1/sqrt(3)`, the governing state for plate necking
    and the state the GL curve derives from) reaches utilization 1 exactly at
    the mesh-scaled limit.  Uniaxial tension then fails later than plain RTCL
    by the same factor.
- The contact tangent is currently approximate: active contact forces are
  updated within Newton iterations and convergence is protected by line search
  and cutback rather than an exact contact active-set tangent.

Impact fracture / contact erosion:

- `ImpactFractureConfig` optionally erodes contact targets in
  `solve_transient_sphere_impact` after a converged contact substep.  Its
  triggers are contact observables (normal force, penetration ratio or a
  sphere-area contact-pressure proxy) and are therefore geometry-agnostic, so
  both shell midsurface targets and (with `SphereContactConfig(beam_contact=
  True)`) beam segment targets can fracture.  The `max_deleted_fraction` guard
  counts all erodible contact targets.
- `ImpactDamageConfig` is the capacity-based impact screening layer.  It
  estimates local contact patch area from sphere radius, penetration, shell
  thickness and a configured minimum area, then evaluates contact pressure,
  impulse per area and an equivalent-plastic-strain demand proxy against
  yield, ultimate-proxy or user capacity.  This is an area/contact-pressure
  model and therefore screens shell midsurface contact only; beam line contact
  is out of scope (a preflight warning is emitted when beam contact targets are
  active) — use `ImpactFractureConfig` or the nonlinear
  `PlasticImpactDamageConfig` for beam erosion.
- Damage may be accumulated across repeated contact substeps or applied as an
  instant threshold.  Above `softening_start`, element stiffness, mass and
  contact participation are reduced toward the residual fraction; elements are
  eroded when damage reaches `delete_at`.  Optional neighbor smoothing holds a
  one-step isolated spike until repeated contact evidence is present.
- Eroded elements (shells or beams) are removed from later contact searches and
  contribute only residual stiffness/mass to later transient solves; the
  residual-scaling matrix rebuild is element-agnostic.  Nodes, DOFs, MPCs and
  connected members remain in the model.
- Diagnostics separate simple threshold fracture triggers from capacity-based
  damage triggers, while `erosion_summary` reports the combined eroded/softened
  element set used by the transient matrices and contact search.
- This is an engineering erosion model for impact screening.  It is not ductile
  fracture mechanics, crack growth, cohesive damage, tearing, remeshing or
  arbitrary-contact impact.

## Buckling and Nonlinear Statics

Linear buckling solves:

```text
K phi = lambda KG phi
```

with positive `KG` representing destabilizing compression in the supplied
reference stress/resultant state.

The incremental nonlinear static path uses von Karman shell kinematics,
beam-column geometric coupling and optional layered J2 plane-stress plasticity
with DNV-RP-C208 style material curves.  It is suitable for restrained
plate/stiffened-panel response and pre/post-buckling capacity checks in the
implemented range.

### Corotational kinematics (large rigid rotations)

`solve_static_nonlinear(..., kinematics="corotational")` activates an opt-in
element-independent corotational formulation for large rigid rotations with
small elastic strains.  Per element, the rigid-body rotation `R_rig` is
extracted from the deformed geometry (shell midsurface frame at the element
center; beam axis alignment plus mean axial twist), the nodal displacements
are pulled back to the reference configuration,

```text
u_d (translation) = R_rig^T (x - x_c) - (X - X_c)
u_d (rotation)    = rotvec(R_rig^T exp(skew(theta)))
```

the element's linear-elastic reference stiffness acts on the deformational
part, and forces are rotated forward: `f = E K_ref u_d` with
`E = blockdiag(R_rig, ...)`.  Verified anchors: internal-force invariance
under rigid rotations up to 170 degrees (machine precision, where von Karman
produces GN-scale spurious forces), and the cantilever roll-up under end
moment matching the analytic circle through 180 degrees of tip rotation.

Validity limits:

- small strains and small deformational rotations per element; the
  deformational displacements are routed through the elements' own nonlinear
  local responses, so layered shell J2 plasticity, beam fiber plasticity and
  the local von Karman coupling are active in the corotated frame (plastic
  state is objective under rigid rotation); fiber shear/torsion stay elastic
  as in the von Karman path, and fracture/erosion remains unsupported in
  corotational mode;
- the tangent is the rotated local tangent `E k_local E^T`; frame-sensitivity
  geometric terms were found to destabilize the symmetrized Newton map near
  equilibrium and are not used — plain Newton without line search converges
  in a handful of iterations instead (the residual-norm line search is
  disabled automatically in corotational mode because the frame-rotation
  excursion of the first iterate would otherwise be rejected);
- the pull-back has an intrinsic residual roundoff floor of roughly
  `eps * ||K_e|| * L` per element; use relative tolerances of 1e-5 to 1e-6 and
  realistic load magnitudes;
- eccentric beam-shell MPC couplings keep fixed eccentricity directions and
  should not be used across strongly rotating regions;
- the default `kinematics="von_karman"` path is unchanged and remains the
  route for plastic capacity analyses.

### DNV-RP-C208 Capacity Workflow Anchors

The nonlinear capacity workflow is aligned with the DNV-RP-C208 guidance
reviewed from the supplied PDF:

- key parameters such as element type, mesh, material curve, imperfections and
  residual-stress representation should be selected conservatively or
  calibrated against a comparable standard/test case,
- true stress / true plastic strain material curves should be used consistently
  with the element formulation,
- permanent loads should be applied before environmental/proportional loads in
  nonlinear analyses,
- buckling capacity checks should include equivalent imperfections and may use
  scaled eigenmodes or standard imperfection patterns,
- displacement control is useful when the force-controlled run must be driven
  beyond the load limit to identify the peak response.

Implemented interfaces:

- `dnv_c208_steel_curve(grade, thickness, fractile="low")` returns the built-in
  low-fractile S235/S275/S355/S420/S460 section 4.6.6 curves.  Mean curves are
  deliberately not guessed; supply explicit data through `curve_from_properties`
  when a mean-capacity study is required.
- `ImperfectionField`, `EigenmodeImperfection`, `StandardImperfection` and
  `CompositeImperfection` describe stress-free nodal reference-geometry offsets.
  `apply_imperfection()` modifies coordinates before the nonlinear solve, so
  zero displacement in the imperfect model has zero internal force.
- Standard deterministic imperfections include member bow (default `L/300`),
  plate sinusoidal half-wave (default `s/200`) and flange/outstand twist
  (default `0.02 rad`).  The defaults correspond to the reviewed DNV table, but
  users should still calibrate or override amplitudes when the failure mode or
  tolerance class requires it.
- `NonlinearLoadProgram` applies ordered stages.  The common DNV sequence is a
  permanent stage first and an environmental/pressure/compression stage second.
- `DisplacementControl` augments the Newton system with a scalar displacement
  constraint and a load proportionality factor unknown, allowing monotonic
  capacity tracing past a simple force-control limit.

### Arc-length continuation

`anysolver.arc_length.solve_static_arc_length()` adds a bounded Crisfield-style
spherical constraint to the same nonlinear element, material-state, load, and
constraint machinery:

```text
R(q, lambda) = F_constant + lambda F_reference - F_internal(q)
dq.T W dq + alpha^2 dlambda^2 = ds^2
```

It is intended to cross a first limit point and retain a small, guarded
descending branch. Controls limit the load increment, number of steps,
post-peak count or load fraction, and maximum nodal translation. It does not
perform automatic bifurcation branch switching, follower-load continuation,
nonlinear free-free continuation, or unrestricted collapse tracing. See
[`ARC_LENGTH.md`](ARC_LENGTH.md) for the API and acceptance limits.

Material modelling:

- Shells use layered plane-stress J2 plasticity through Gauss-Lobatto thickness
  layers.  Result diagnostics include equivalent plastic strain, compressed-side
  plastic strain and layer strain extrema when plastic state is available.
- Beam/stiffener plasticity is opt-in through `FiberSectionPlasticityConfig`.
  The beam fiber model integrates uniaxial axial/bending stress over a section
  grid scaled to the supplied `A`, `Iy` and `Iz`; shear and torsion stay
  elastic. If `web_height`, `web_thickness`, `flange_width`, and
  `flange_thickness` are supplied, the grid follows web/flange strips and is
  recentered/rescaled to preserve the section constants. Otherwise a generic
  rectangular grid is used. Both the 2-node and 3-node quadratic beam implement
  the von Karman beam-column coupling and fiber response: the 2-node element
  uses end-difference strain measures, while the 3-node element evaluates the
  same measures at its Gauss points from quadratic interpolation.

Simplified fracture / element erosion:

- `FractureConfig` activates a v1 nonlinear-static damage model based on the
  maximum equivalent plastic strain stored in committed shell/beam plastic
  states.
- Elements are softened only after a converged increment.  The default is
  residual stiffness (`1e-6`), not true topology deletion, so nodes, DOFs,
  MPCs and beam-shell coupling constraints remain in the model.
- Pressure loads attached to deleted shell elements are removed from later
  increments.  Ordinary nodal loads are unchanged and are reported as not
  fracture-aware.
- This is an engineering erosion screen for monotonic capacity studies.  It is
  not crack propagation, cohesive fracture, remeshing, impact fracture, fracture
  toughness assessment or a validated ductile-fracture model.

Residual stresses:

- v1 treats calibrated equivalent geometric imperfections as the practical
  residual-stress proxy for buckling capacity workflows.
- `initial_element_states` is reserved for future residual stress/prestrain
  fields.  A full residual-stress implementation must contribute to both
  internal-force equilibrium and tangent stiffness, and must report diagnostics
  separately from geometric imperfections.

## Verification anchors

The test and report suites protect, among other checks:

- DOF ordering, model revisions, separated K/M/C/KG/F assembly, matrix
  symmetry/finiteness, sparse factorization reuse, and provenance;
- fixed/prescribed supports, interpolated/eccentric MPCs, reactions, and
  connected-component rigid-body nullspaces;
- T3/T6/Q4/Q8/Q8R interpolation, rigid modes, membrane/bending/shear patches,
  pressure and mass resultants, distortion checks, and nodal stress recovery;
- linear/quadratic Timoshenko response, axis conventions, torsion, mass,
  geometric stiffness, nonlinear tangent, and fiber yielding;
- modal, Euler/Wagner/plate buckling, repeated roots, and sparse shift-invert;
- DNV curve anchors, plane-stress return mapping, imperfections, staged loads,
  displacement control, corotational objectivity, and arc-length limit points;
- Newmark/HHT-alpha response, pressure-patch impulse, sphere-contact momentum
  and energy, beam contact, nonlinear impact, RTCL weighting, and committed-state
  damage;
- selected/envelope recovery, memory policy, normalized geometry conversion,
  capacity workflow, SESAM round trip/import, and SIF load-case isolation.

CalculiX input decks and reference-case discovery support reproducible external
comparison. A generated deck without an executed result is not evidence of
numerical agreement. Verification commands and evidence interpretation are in
[`QUALITY_CONTROL.md`](QUALITY_CONTROL.md).
