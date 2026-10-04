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
