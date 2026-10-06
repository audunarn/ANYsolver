# Native BL5 mixed shell J2 development route

`BL5_NATIVE_FIBRE_MIXED_SHELL_MATERIAL_V1` selects the development identity
`BL5_NATIVE_FIBRE_MIXED_SHELL_MATERIAL_V1_DEV`. It requires all-S3 or mixed Q4/S3
flat shells with the existing isotropic J2 curve, physical fibres and supported
BL5 director-bond lines. Admitted native generalized members can coexist with
physical axial or biaxial fibre members. Q4 uses its explicit objective pullback
when present. The old Q4 material and elastic mixed-shell policies keep their
existing meaning and guards.

The public entry point is
`examples/stiffened_shell_native_fibre_bl5_mixed_j2_displacement.py`. Its ordinary,
unrebased, nonadaptive nodal dead-translation force seed precedes fixed physical
translation targets. Recovery includes the actual Q4/S3 layer histories and native
member histories. Checkpoint, fresh restore and continuation replay both domains
from the same accepted predecessor before atomic publication. The new displacement
controller and mechanical framing are distinct from the earlier Q4 and POINT
formats. Native force checkpoints retain the existing V8 layout, bound to the
new model/policy identity; Q4 arrays and paired S3 blobs already have separate
fields in that layout.

S3 boundary capture uses the existing effective station operators and internal
constitutive station/layer order: `(Bm + z Bb) T0 D`. It records the external pose,
exact material predecessor fingerprint and 18-column differential. The unchanged
Decimal predictor calculation is shared with the 24-column Q4 capture. This is a
numerical switch proposal, not constitutive acceptance or a new event controller.
The residual and tangent preserve the existing algorithmic pullback, including
force contracted with deformation curvature and spatial-row chart corrections.

Adaptive displacement, branch events, chart rebasing, arc control, follower loads,
body consumers and frozen qualification campaigns are outside this route. This
slice does not establish scientific qualification, external accuracy, installed
artifact acceptance, release readiness or completion of Revision8. Source check
results and preserved failures are recorded under
`.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-mixed-j2-dev-20261006-v1/`.
