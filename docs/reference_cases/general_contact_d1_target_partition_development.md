# Planar S3 target-partition discriminator

**Status:** bounded development, 28 September 2026. This is a target-mesh
partition comparison, not a general mesh-convergence or pressure-space gate.

## Question and setup

The accepted distributed full-cycle evidence uses eight Q4 source faces
against a fixed planar target represented by two S3 triangles. Its source
pressure field changes under 8→16→24 Q4 refinement. To measure one possible
target-discretization effect, split the same target plane into two rectangular
columns, each with two S3 triangles. Preserve the target extent
`[0,1.3] × [0,1] m`, physical top side, 0.05 m thickness, 0.01 m reference
surface offset, fixed target constraints, eight-Q4 source and the three-step
0.3 N distributed press. Normal regularization, Schur caps, pressure and gap
tolerances and augmentation budget are unchanged.

The target has six physical vertices and four positively oriented S3 facets;
the original two-S3 case has four vertices. Both span the same flat plane and
physical offset. No extra pressure unknowns are introduced on the target:
the Q4 source remains the pressure side.

## Observation

The four-S3 raw solve is
`reports/general_contact_d1_distributed_8q4_4s3_target_press_dev_20260928.json`.
It completed three steps in 131.6 s. At full press, the integrated upward
source force is 0.103479815155208 N, the same saved value as the two-S3
eight-Q4 full-press case to the shown precision. The four-S3 solve met its
physical-gap gate (minimum -0.0804 µm versus 50 µm), pressure-change gate
(4.03e-14 Pa versus 1e-5 Pa), and 18/18 supported pressure rank. It used
four augmentations and ended with 1.46e-9 N reduced residual.

The independent read-only piecewise-bilinear source-pressure comparison is
saved in
`reports/general_contact_d1_distributed_8q4_target_partition_pressure_compare_dev_20260928.json`.
Its relative reference-surface L2 difference from the original two-S3
eight-Q4 pressure field is `5.06e-13`. The postprocessor uses the saved
physical source pressure values and exact common-refinement quadrature; it
does not call the contact integration kernel.

## Decision

At this flat pose and source resolution, splitting the target into four S3
facets has no measurable effect on the integrated reaction or pressure field.
This narrows the principal uncertainty toward source pressure resolution,
enforcement and contact geometry under genuinely changing overlap. It does
not establish target-mesh independence for curved, warped, sliding or
partial-overlap configurations. No capability status changes.

The saved 8/16/24-Q4 two-S3 full-press reports also have maximum absolute
nodal pressure-minus-committed-multiplier differences of 3.47e-14,
2.10e-14 and 3.44e-14 Pa; their maximum active normalized weighted gaps are
3.47e-18, 2.10e-18 and 3.44e-18 m. This says the final *weak* multiplier
updates are resolved at those states. It does not certify pointwise zero gap:
the independently sampled minimum physical gaps remain about -0.080,
-0.019 and -0.020 µm. Together with the target-partition comparison, these
saved observations direct the next investigation toward source pressure
resolution and an independent pressure-field reference, without another
automatic augmentation-budget increase.
