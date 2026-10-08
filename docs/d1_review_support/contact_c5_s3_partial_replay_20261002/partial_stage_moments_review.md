# Partial stage moments — development record, 2 October 2026

Question: avoid repeated pressure Gram/shape-gradient work in intermediate S3
history stages while preserving the existing normal pressure and feature rules.
Profile input and measurements are in `partial_stage_moments_result.json`.

The first implementation clipped the source reference triangle by the convex
target boundary and integrated P1 support and affine-gap moments. Local parity
passed, but Read scrutiny by `/root/prepared_path_scrutiny` found two defects:

1. The patch admission tolerance can accept a very slightly concave triangle union;
   intersecting its boundary half-planes is not integration over that union.
2. Zero-tolerance union clipping differed from ordinary per-face vertex merging
   and zero-area ownership for positive overlaps narrower than its feature scale.

That implementation was discarded. The selected implementation uses the original
`PlanarFace` and `planar_projected_overlap` per target face. Source reference area,
actual projected polygons and shared pressure normalization remain unchanged.
Only unneeded stage Gram matrices and shape-gradient recovery are avoided.

Follow-up scrutiny found that directly computed affine coordinates bypassed the
ordinary projected shape-domain guard. The selected implementation now calls the
same `_shape_from_xy` routine for source and target coordinates, with the same
rejection threshold. The source/target transformations are prepared once per face.
No derivatives are claimed for this pressure-only stage routine; complete replay
tangents remain separately checked and bounded.

Focused checks include tilted-source/moving-target partial poses, constant pressure,
overlap widths down through1e-15/zero, the slight-concavity counterexample, both-body
tangent and the saved residual. The scale-disparity shape-rejection test initially
failed at fixture construction because a two-face patch is unsupported. Its corrected
three-face fixture reproduces ordinary rejection and checks the same rejection here.
Retain both logs: `contact-friction-partial-guarded-moments-20261002.log` (4passed,
1fixture failure) and `contact-friction-shape-guard-fixture-20261002.log` (1passed).

This is development scrutiny, not independent acceptance. The new full-workflow
run has its own prospective `stage_moments_full_v1_registration.json`; earlier
900-second and4096-stage failures remain consumed. Restart remains a required
separate comparison, not a claim from the new full-only test.

Final Read disposition: reviewer confirmed both source/target calls preserve the
original shape-domain guard and gap reconstruction uses the validated target
shapes. No execution by the reviewer; full-run/restart acceptance remains open.
