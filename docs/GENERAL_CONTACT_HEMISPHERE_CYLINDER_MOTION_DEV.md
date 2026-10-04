# Prescribed translating cylinder with actual hemisphere caps — development

`CLASSICAL_B2_B3_HEMISPHERE_TRANSLATING_CYLINDER_STATIC_DEV_V1` uses explicit
`RigidContactBody(..., kind="cylinder", path_translation=(dx,dy,dz))` and
`beam_end_cap_work="hemisphere_support_dev"`. Run
`examples/general_contact_hemisphere_cylinder_motion.py`. Ordinary force
continuation prescribes axis-point translation through its load parameter; the
axis direction and radius remain fixed. Displacement control, free/rotating bodies,
multiple moving obstacles, friction and dynamics remain rejected/unadmitted.

This separate profile reuses the
[fixed actual-cylinder-cap geometry](GENERAL_CONTACT_HEMISPHERE_CYLINDER_DEV.md),
all authoritative beam/tangent-node work and the existing prescribed-tool owner.
`set_path_factor` updates the point used by both distributed line and endpoint
work. Body reactions include the complete cap contribution. The inherited signed
reaction-work trapezoid and opposite actuator work are reported separately from
line/cap regularization storage and elastic material work. The work quadrature is
an approximation; it is not a potential identity for arbitrary nonlinear paths.

Full-radius conservative enclosures follow the represented affine nodal/axis-point
path and actual curve regularity. Common translation and hidden crossing are
checked. Rejection/cutback remains finite under existing controls; tool translation
is not frozen during certification. State identity binds the path vector and a
new kinematic revision. Fixed profile identity and its direct owner guard stay.
Open/active restart, incompatible path/profile rejection and real interruption
replay are checked by the development programme. Application admission stays false.

## Current development cost

The four-target axial tool fixture generates **284 accepted states** through the
inherited conservative load cutbacks. The source batch timed out at180.068s after
five successful test prefixes; its last interruption check was incomplete. That
check subsequently passed alone (32.969s); no old failure is regraded. Installed
work is grouped by coherent solve/work/state cases under unchanged180s/953MiB
process limits. This is a functional prototype, not a claimed speed improvement.

The next cost question is whether coupling the load-stage predictor to the
structural/contact tangent can avoid unnecessary fixed-pose tool cutbacks while
certifying the actual coupled path. It requires a separate bounded candidate and
hidden-crossing/activation checks. No larger gap budget, weaker law, hidden physical
substeps or automatic switch is authorized by this guide.

## Installed results

**26 passed** across two bounded groups:139.169s/198733824B and110.420s/338456576B.
All514package Python files and219loaded solver modules match candidate bytes;
JIT disabled, effective Numba/numerical pools one thread. Private wheel SHA256:
`c92f303bd5d3c002bde3d832440725dfc0adff276786d2900a5d6f51b7f45b52`.
These groups include multiple complete solves per test; their elapsed times are not
single-solve timing claims. Unaffected fixed-kernel scientific checks are reused
from the exact matching source, with fixed/mixed and lazy no-contact checks here.

B2/B3 displacement errors against independently assembled axial/line equilibrium
are at most6.506e-18m. Minimum gap−9.99950e-8m meets the explicit1e-5m fixture
budget. Reactions, separate line/cap storage and independent per-step actuator
work pass; work/storage defect5.842e-6 is measured, not claimed exact conservation.
Both fixtures retain284force-history states. Curved B3 rim body-translation virtual
work, tool-work factor restoration, common motion/hidden crossing, open and active
fresh restart, changed-path/fixed-profile rejection, actual public displacement-
control rejection, cancellation and later-candidate exception replay pass. The
public example and affected fixed/mixed/no-contact routes pass.

[Evidence](d1_review_support/contact_hemisphere_cylinder_motion_20261004/summary.json)
retains the source01 timeout, separate remaining-cancellation check and source/
installed input identities. Raw root:
`C:/ANYworkspaceWork/contact_hemisphere_cylinder_motion_20261004`.
No independent engineering acceptance, application admission or release is claimed.


## Opt-in coupled load seed — 4 October 2026

Select `beam_end_cap_work="hemisphere_coupled_tool_dev"` for the same supported
single translating cylinder, elastic concentric B2/B3 and force-continuation scope.
The existing example accepts `run(coupled_load_seed=True)`; its default stays on
the previous conservative algorithm. The new profile/restart identity is
`CLASSICAL_B2_B3_HEMISPHERE_COUPLED_TRANSLATING_CYLINDER_STATIC_DEV_V1`.

An already active physical origin can propose one complete constrained Newton
correction when the new-tool/fixed-structure preflight fails. The temporary force
pose must certify the exterior domain of both radii. The correction counts inside
the existing Newton budget. Every full and backtracked seed path is certified from
the committed structural/tool origin; final gap, equilibrium and work gates remain.
Rejected proposals cut back. Cancellation, exceptions and precommit tool-work
failure discard trial state and restore the committed tool factor. First approach
uses the existing event policy. No mechanical law or gap budget is changed.

Matched balanced source runs reduce the four-target guided fixtures from 284 to
16 accepted states and 844 to 40 Newton iterations. B2 median solve time changes
11.5243 to 0.7540 s (15.28x), B3 19.3231 to 1.0854 s (17.80x). These are fixture
measurements; B2 baseline runs span 9.47–13.57 s. General nonlinear line contact
may reject a one-correction seed and retain bounded cutbacks. No universal speed
or twofold shell-route improvement is inferred. Two named 16-B2 no-contact routes
measure median changes +2.24% axial / +0.50% bending, within their 5% budget.

The combined fresh installed artifact verifies 31 outcomes in 105.996 s with
336,527,360 B peak process-tree memory, JIT disabled and numerical pools one.
All 515 package Python files and 219 loaded solver modules match candidate bytes.
Wheel SHA256: `4d6e2040299124059a92138e915fd5a1f70e71ebe65d09ea6bd225d0b12a0dde`.
Checks include response/work, inactive and active origins, exterior radius order,
complete hidden crossing, rejected full/backtracked seeds under decrease/Armijo,
iteration budget, singular/nonfinite systems, cancellation/exception replay,
precommit failure, open/active restart, incompatible algorithms and the public
example. Source/default compatibility and installed lazy no-contact checks pass.

The same integration adds fixed-cylinder spatial/enforcement evidence using an
independently derived axial continuum bar with distributed unilateral line contact.
B2/B3 meshes 1/2/4 and line strengths 1e9/4e9/16e9 N/m² agree within 5.55e-6 relative
response error against the 0.1% target. Distributed contact carries nearly half the
0.02 N applied load. Independent polynomial gap/quadrature checks pass; penetration
falls approximately 4.488 to 2.246 to 1.123 micrometres, within the registered
10 micrometre budget. This checks the shared **fixed** cylinder mechanics, not the
moving algorithm, spatial convergence order or resolved pressure/active length.
Curved coupled response and broader section/material/profile acceptance remain.

[Summary and source review](d1_review_support/contact_coupled_tool_staging_20261004/summary.json)
bind source hashes, resource/runtime records, measurements and remaining scope.
Raw evidence: `C:/ANYworkspaceWork/contact_coupled_tool_staging_20261004`;
prospective continuum decision: `C:/ANYworkspaceWork/contact_cylinder_convergence_20261004/decision.md`.
Retain source01 dispatch failure, source03 runner-selector failure, source04 boundary
fixture defect and source09–11 budget/backtrack test defects. Corrected source
scrutiny and analytic references support code verification; independent engineering
acceptance, normal application admission, release and full C0–C9 remain incomplete.

## Guided curved-interior response — 4 October 2026

Fixed and translating cylinder cases now verify a genuinely curved B3 interior
contact solution. Only mid-node UY is free; all curve vertices and both physical
hemisphere caps remain open. Independently derived shear/axial scalar virtual work
and direct polynomial line integration agree at every accepted state. Final
displacement is about-63.963um, independent minimum gap-1.317um within10um, and
force/moment balance defects are <=2.4e-12N/5.1e-13Nm. The reported conservative
gap-1.535um lies within its declared1um enclosure accuracy. Fixed/moving routes
use4/11states and20/67Newtoniterations. This fixture weakly exercises the cubic
structural force; it is curved contact/shear evidence, not general nonlinear proof.

Initialization can now stop when an exact conservative full-curve bound certifies
nonnegative gap. It retains the original accuracy, depth and rejection threshold
for negative/unresolved bounds. Penetration between clear vertices still fails.
Installed15 affected checks pass;5changed tests repeat after adding per-state
reference checks.515package files match source; effective JIToff/pools1.
Private wheel SHA256 `f6a1b3dc3318d4e8ec5faea8c4b26c933a61970c0e2cbe422440b19df185dfab`.
[Summary and supporting assessment](d1_review_support/contact_curved_cylinder_response_20261004/review.md).
Active-rim coupled response, pressure/active-length adequacy and independent
engineering acceptance remain open. Prior acceptance scopes and failures remain.

The subsequent guided translating-tool case closes **active-rim coupled code
response**: all10accepted signed-coordinate states match independent planar cap
and line virtual work. Physical rim/curve gaps-4.898/-5.896um meet10um. Separate
energies and complete force/moment mappings pass; directional tangent errors over
three perturbations are4.41e-7/4.87e-8/7.93e-9. Direct quartic roots check active
width in all curved fixtures. The planar reference explicitly rejects other
geometries.8installed affected checks and3later modified response checks pass;
source/wheel unchanged,515files match. This closes the named code-response gap,
not general rim/pressure engineering qualification.
Saved fixed-continuum lengths differ by0.0824–0.0825%; this adds descriptive
accuracy evidence without a new acceptance threshold or convergence-order claim.
[Assessment and remaining scope](d1_review_support/contact_curved_cylinder_response_20261004/review.md).
