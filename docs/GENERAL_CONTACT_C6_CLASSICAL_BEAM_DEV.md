# Classical round-beam Newmark impact — development profile

Implemented and installed-tested; not independently accepted engineering capability
or release. Requires exact classical B2/B3 elastic scalar von Karman elements,
one fixed analytic plane, one declared round-centreline surface covering every
model element, explicit radius/line stiffness/gap tolerance and no end caps.
The existing straight-reference B3 guard remains; its deformed quadratic field
may curve and contact in its interior. No native beam insertion is enabled.

Use the ordinary `solve_transient_contact` and `TransientConfig`. Select
`ContactSolverSettings(pair_motion='general')` and
`ContactTransientSolverControls(allow_classical_beam_dev=True)`. Existing callers
retain their profile. The new profiles are
`CLASSICAL_B2_B3_ROUND_TUBE_VON_KARMAN_FIXED_PLANE_NEWMARK_DEV_V1` and its
`...NEWMARK_HISTORY_DEV_V1` counterpart for `ContactNodalLoadHistory`.
The actual structural mass, including rotary inertia, must be positive definite
after constraints; at most512 free coordinates are admitted. No mass, springs,
damping or restitution are added.

The existing distributed line potential and force map are reused. A tensor
Bernstein enclosure bounds the complete B2/B3 curve and declared Hermite time
path. Exact rational arithmetic treats finite binary64 data as exact inputs;
returned bounds round outward. `beam_swept_gap_tolerance_m=1e-10` controls the
numerical enclosure width, separately from the interaction's physical penetration
budget. `maximum_beam_swept_subdivisions=512` bounds refinement across all cells.
Unresolved, nonfinite or unrepresentable enclosures fail explicitly. A sampled
position never supplies the admission lower bound. This certifies the represented
polynomial path, not exact continuum collision times.

The shared solver handles material transactions, cutback, cancellation, dead nodal
loads, affine load-history work and split restart. Beam controls and definitions
bind the analysis/contact fingerprints. Historical constant/history schemas1/2
remain; incompatible profiles/settings fail. Contact summaries expose line energy,
active length, physical beam/plane forces and moments; the overall result identifies
the temporal profile. Rotational inertia is retained for admitted free rotations.

Run the explicit development examples:

```text
python examples/general_contact_beam_plane_impact.py
python examples/general_contact_beam_plane_impact.py --quadratic --deformable
```

The toy fixtures' .002m gap budget and1e4N/m² line stiffness are development inputs,
not application recommendations or qualification settings. Full enforcement/time
refinement and inherited1e-3-radius qualification starting budgets remain required.
Large finite rotations/corotational dynamics, beam pairs/shells, caps, friction,
nonlinear materials, free/moving rigid bodies and broad C6 acceptance remain open.
See [results](d1_review_support/contact_c6_classical_beam_20261001/results.md).

## Multiple explicit fixed planes

Add `allow_multiple_beam_planes_dev=True` to the classical beam controls to use
two or more explicitly named line interactions. Every body must be a fixed plane;
every selected surface declares a radius and no caps. The union of surfaces covers
all structural elements. Interactions may share a beam against distinct bodies;
duplicate element/body ownership is rejected. This composes distributed line
potentials, with each body's reaction retained under the named pair. Coincident
distinct bodies intentionally add their declared penalties; they are not deduplicated.

Each endpoint and complete represented path must meet its pair's dimensional gap
budget. The minimum over pairs is a summary, not a replacement for those gates.
The subdivision cap is shared across pairs and cells within each path evaluation;
unresolved enclosures fail explicitly. Existing aggregate candidate caps remain.
Profiles are `CLASSICAL_B2_B3_ROUND_TUBE_MULTIPLE_FIXED_PLANES_NEWMARK_DEV_V1`
and `...NEWMARK_HISTORY_DEV_V1`. Restart binds these controls and all pair contracts.
Results expose `contact[i].pairs` as `(interaction_name, pair_result)` tuples;
`to_dict()` also reports summed forces/moments and individual pair fields.

```text
python examples/general_contact_beam_plane_impact.py --quadratic --multiple-planes
```

This extension remains development only. It does not admit radial obstacles,
moving/free bodies, automatic pairs or beam-beam impact. See the
[slice and checks](d1_review_support/C6_MULTIPLE_BEAM_PLANES_SLICE_20261002.md).

## Prescribed plane translation

Supply `rigid_translation_histories=(history, ...)` to the same transient solver:

```python
from anysolver.general_contact.transient import ContactRigidTranslationHistory
history = ContactRigidTranslationHistory(
    "plane", ((0., 0., 0., 0.), (.013, 0., 0., .0026)))
```

Entries are `(time_s, dx_m, dy_m, dz_m)` relative to the named immutable body's
reference point. Offsets are affine between knots and start at zero. Every named
body is declared once and histories cover the solve. Normals stay fixed. This is
a physical-time input, separate from static `RigidContactBody.path_translation`.
It currently requires the classical beam opt-in; shell descriptor/rotating/free
tool admission is not inferred. Single and multiple pairs retain their own gates.

The driver lands on each combined tool/load knot. If nominal steps would leave
a sub-minimum remainder, it distributes feasible remaining steps; incompatible
`dt`/`minimum_dt` knot partitions fail before solving. Relative tensor Bernstein
bounds subtract affine plane motion across every represented curve/time path.

`prescribed_tool_work_j[i]` maps body names to cumulative input work
`-integral F_rigid dot dpoint`, separate from `external_nodal_work_j`.
`prescribed_tool_work_error_j[i]` accumulates numerical work-integration estimates.
Work partitions time using endpoint cubic and B3 interior-discriminant roots,
then uses bounded embedded 3/5-point Gauss integration. A geometry bound checks
zero-rule intervals against missed narrow support. Floating roots and embedded
estimates do not establish certified continuum integration error. Controls are
`tool_work_absolute_tolerance_j`, `tool_work_relative_tolerance` and
`maximum_tool_work_subdivisions`; exhausted limits fail without physical commit.
Temporary quadrature poses restore on exit. Only accepted increments add work.

The new temporal profiles identify `PRESCRIBED_TRANSLATION`; schema5 binds the
history, numerical settings, pair contracts and per-body work/error state. Old
fixed-plane checkpoint formats remain unchanged. Example:

```text
python examples/general_contact_beam_plane_impact.py --quadratic --multiple-planes --tool-motion
```

Independent scalar trajectory/impulse/polynomial-work checks, pulse probes and
restart tests support development. The scalar elastic energy screen improves
under time refinement; this does not qualify arbitrary geometry, enforcement or
C6 impact. [Slice](d1_review_support/C6_TRANSLATING_PLANES_SLICE_20261002.md).

## Coupled free isotropic sphere

Use the same `solve_transient_contact` with classical beam and free-sphere opt-ins:

```python
from anysolver.general_contact.transient import ContactFreeRigidBody
body = ContactFreeRigidBody(
    "sphere", mass_kg=.002, isotropic_inertia_kg_m2=8e-8,
    initial_velocity_m_s=(0., 0., .2),
    initial_angular_velocity_rad_s=(2., -3., 4.))
# solver_controls: allow_classical_beam_dev=True, allow_free_sphere_dev=True
# free_rigid_bodies=(body,)
```

The definition must declare one sphere, one round uncapped B2/B3 surface and one
penalty line interaction. `line_integration_relative_tolerance` is explicit.
The mass centre is the declared sphere point. Mass and each principal centre
inertia are supplied independently; neither is inferred from geometry. Isotropic
inertia, initial identity orientation and central frictionless forces permit exact
torque-free spin `exp(t[omega]x)`. This does not admit anisotropic gyroscopic work,
eccentric centres, friction, free planes/cylinders or prescribed and free ownership
of the same body. Shell/free-body coupling remains a separate development boundary.

Three sphere-centre coordinates join the same constrained Newton/Newmark system,
with physical `mass*I` inertia and full structural/body contact cross blocks from
the distributed potential. Structural assembly retains its original coordinates;
returned displacement/velocity/acceleration fields keep their structural shapes.
`free_rigid_bodies[i]["sphere"]` reports centre motion, rotation, angular velocity,
contact force, kinetic energy, linear momentum and angular momentum about the
stated global origin. These are physical body quantities, not prescribed tool work.
The immutable body inputs and named coupled state bind restart schema6.

The complete relative beam/sphere Hermite path includes both endpoint velocities.
Exact tensor Bernstein squared-distance and component-box lower bounds, feasible
point upper bounds and exact square-root brackets supply outward gap enclosures.
Split choice uses certified lower-bound gain; every cell remains represented.
The same finite split/resource budget applies and unresolved bounds fail explicitly.
This is an enclosure of the declared interpolated path, not a continuum guarantee.

```text
python examples/general_contact_free_sphere_impact.py
python examples/general_contact_free_sphere_impact.py --quadratic
```

Independent closed line-force/two-body Newmark, impulse, spin, virtual work/tangent,
B3 momentum and elastic-energy refinement checks support the development profile.
The isolated installed selection has171passes, including both examples and old
fixed/prescribed/shell regressions. [Results](d1_review_support/contact_c6_free_sphere_20261002/results.md).
General C6 engineering acceptance, finite rotations, nonlinear materials, caps,
friction, beam-pair impact and arbitrary rigid-body geometry remain open.
