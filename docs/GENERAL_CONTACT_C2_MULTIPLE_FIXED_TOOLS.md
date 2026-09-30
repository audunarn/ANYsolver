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
