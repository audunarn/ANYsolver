# General contact: deformable round beam / S3 development profile

**Status:** implemented and locally tested; no scientific acceptance, installed
verification or release. This profile is additive; existing beam-shell defaults
remain `translated_planar`.

Run the public source example from the general-contact checkout:

```powershell
$env:PYTHONPATH='src;tests;.'
C:/Python/Python314/python.exe examples/general_contact_deformable_round_beam_s3.py
```

Select `ContactSolverSettings(beam_shell_geometry='jet2_deformable_s3_dev',
beam_shell_maximum_swept_intervals=128, pair_motion='general',
beam_shell_rim_clearance=0.02, line_integration_relative_tolerance=1e-8)`.
The interaction explicitly declares radius, `line_stiffness` (N/m²), and
`gap_tolerance` (m). No pressure stiffness is inferred.

## Bounded mechanics

One straight-reference B2/B3 cell contacts the interior of one S3 V2D top/bottom
skin. Its actual displaced B2/B3 curve is integrated against the changing normal
of the actual physical triangle. Target translations may differ; target rotation
coordinates must remain zero. Physical thickness/reference offset and support
force couples come from the S3 formulation adapter. The classical beam/shell
structural route is elastic, concentric and von Karman, with no endpoint caps.

The potential is `1/2 * line_stiffness * integral(min(gap,0)^2 dL_reference)`.
Existing Jet2 supplies the complete positional gradient/Hessian, including
normal changes. Three Gauss points integrate the degree-four polynomial over
each exact active interval; reported zero quadrature error means this polynomial
rule has no truncation error, not that floating arithmetic is exact. Derivative
arrays remain local; authoritative residual/tangent assembly is sparse and acts
on both bodies before boundary-condition reduction.

The affine authoritative-coordinate path uses bounded cross-product/edge
Bernstein enclosures and Lipschitz gap/rim controls. Candidate paths that exhaust
the declared interval budget are cut back or rejected. Endpoint sampling alone
is insufficient: local controls include hidden intermediate face/rim crossings.
This is a development enclosure, not general director-rotation CCD admission.

Restart binds this separate profile, work-map revision, physical definitions,
line/gap/rim settings and both swept limits. Checkpoints from incompatible
settings reject. The manager has no physical contact history to commit: the
existing static driver owns material/increment transactions.

## Evidence and limits

Seven local work/geometry checks pass. The integrated small-load fixture has
beam tip `uz=-0.001025473m`, deforming target node `uz=-0.002914522m`, and
minimum gap `-3.970251um` with explicit `line_stiffness=1e5N/m²`. Independent
scalar plane/line integration matches the contact forces; the linearized
structural comparison differs by about4.4e-6 relative. That reference reuses the
existing structural stiffness and does not independently qualify the elements.
Full versus JSON split restart agrees, incompatible continuation rejects, and
the public source example passes. Full affine loading requires512 subdivisions
in the independent diagnostic; four accepted increments work at128 per path.
No silent budget increase occurs in the solver.

Retained failures: the original large-motion fixture missed its linearized
structural comparison; its small-load successor with1e4N/m² genuinely exceeded
10um. A scalar-reference initialization and a UTF8 preflight also failed, and
an example exposed missing beam metadata after the line-unit correction. Raw
records remain in `d1_review_support/d3_deformable_beam_s3_*_20261001.*`.

Open: scientific/installed qualification, nonlinear materials, free target
rotations, Q4/warped targets, multiple faces, rims/end caps, automatic/self
contact, friction and dynamics. The profile does not imply these capabilities.
