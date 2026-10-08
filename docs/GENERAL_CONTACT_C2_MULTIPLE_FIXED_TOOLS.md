# Multiple explicit round-beam contacts with fixed tools

Development profile: `MULTIPLE_EXPLICIT_ROUND_BEAM_FIXED_RIGID_STATIC_DEV_V0`.
This is implemented and locally tested. Scientific acceptance, installed-package
qualification and release remain separate.

Use one `ContactDefinition` with named round-beam surfaces, fixed plane/sphere/
infinite-cylinder bodies and two or more explicit interactions. An interaction
names its beam surface and rigid body. One beam may contact several bodies;
different beams may contact the same body. The existing concentric elastic
B2/B3, von Karman and original single-pair geometry restrictions still apply.
This profile requires `beam_end_caps="none"` and `pair_motion="general"`.
Radial bodies also require an explicit line-integration tolerance.

Each interaction declares `line_stiffness` in N/m² and a dimensional
`gap_tolerance`. Do not supply surface-pressure stiffness or infer a beam radius
from section area. Every pair must pass its own gap and swept-path checks.
Residuals and tangents act on the shared structural coordinates; rigid forces
and moments are the opposite pair contributions about the global origin.
Potential, reactions and diagnostics are summed while per-pair fields remain
available under `general_contact["pairs"]` and `pair_enforcement`.

The ordinary `solve_static_nonlinear` force/displacement routes and versioned
restart own equilibrium, material transactions and cancellation. Pair names,
geometry, each law and aggregate limits bind restart compatibility. Repeating
an element/body feature pair, exceeding the aggregate candidate cap or leaving
a declared surface/body unused fails explicitly. No contacts are discarded.
Moving tools, caps, automatic/self pairs, friction and mixed shell/native
composition are not admitted by this profile.

Run [the two-tool example](../examples/general_contact_multiple_round_beam_tools.py)
with this source checkout or a development package containing the profile. The
previous accepted shell artifact is unchanged. Focused tests cover independent
two-plane potential/work, directional tangents, mixed cylinder/plane contact,
per-pair budgets, simultaneous coupled activation and split JSON restart.
The separate cantilever/foundation checks measure B2 mesh and enforcement
sensitivity; neither example alone establishes general beam qualification.

## Simultaneous sphere/plane lifecycle — development control

One actual B3 mid-node loads both a fixed sphere and plane. Independent scalar
radial and plane line-work integrals agree with both generalized forces; both
body wrenches and equilibrium pass. Cancellation raises the existing exception,
leaves the model reusable, and a same-.25-partition prefix on that model supplies
a complete JSON checkpoint. Fresh continuation reproduces both displacements
and **all canonical checkpoint bytes** exactly. V3 passes4.295s/260.50MB.
Evidence:`d1_review_support/d3_multiple_beam_sphere_lifecycle_summary_v1_20261001.json`.

The sphere's localized active line is5.7756mm versus281.847mm for the plane.
Use explicit1e7 and2e5N/m2 line regularizations for this fixture. Its inherited
1mm/.8mm illustrative gap budgets are not the10um qualification target; no
scientific/installed admission follows. V1 physical gap failure at1e5 and V2's
incorrect harness cancellation-return assumption remain NONPASS. V3 changes
only the latter API expectation after the explicitly new law, with no solver,
resource or physical-gate relaxation. Checkpoint integrity field (not separately measured raw-byte SHA):E68C1ED25F83B86BE0A44A6B4A65C93DFCECB0B543ADE4D1FFBBA1859A5AE3F4.
