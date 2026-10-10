# Whole-chord S3 material-gap geometry

`S3MeshWholeChordGapFrictionSettings` is a separate explicit development route.
It inherits the required dimensional `finite_material_gap_error_m` and adds
`maximum_material_gap_evaluations` (positive integer, default 65536). Existing
endpoint-only weak and hard full-contact profiles remain unchanged.

Every original fixed-map trial chord must certify absolute perpendicular gap
for every source-face corner and stored dense point against every target facet,
independently of numerical pressure activation. The existing union, coplanarity,
orientation and both projection-domain guards remain mandatory. Unresolved
parts and evaluation exhaustion refuse before admission; no sampled-pose fallback.

The public example is `examples/general_contact_s3_mesh_swept_gap.py` with
`--through-step`, `--restart` and `--output`. New profile checkpoints are required;
old endpoint-profile checkpoints cannot be resealed or transplanted.

This is **geometry safety only**. Pressure/history events, continuous friction
energy, rounded Jet2 projection values and engineering acceptance are not
qualified by the squared-distance bound. See [OUTCOME.md](OUTCOME.md) and
[IMPACT.md](IMPACT.md). Full evidence is retained at
`C:/ANYworkspaceWork/contact_s3_mesh_swept_gap_20261009`.
