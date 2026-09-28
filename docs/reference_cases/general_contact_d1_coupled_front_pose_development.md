# Coupled distributed-press contact-front pose comparison

**Status:** read-only development diagnostic, 28 September 2026. This is
neither a new solve nor a pressure-stability acceptance case.

## Question and inputs

The fixed-pose affine-front mortar field approaches its local-plane reference,
while the coupled 24→32-Q4 pressure-field change grows near contact onset.
This comparison asks whether the saved coupled source poses themselves change
substantially in that region.

The input states are the completed 16-Q4 two-step distributed press
(`general_contact_d1_mixed_16q4_interior_distributed_0p3n_cartesian_roundoff_press_20260927.json`)
and 32-Q4 three-step distributed press
(`general_contact_d1_distributed_32q4_fine_press_dev_20260928.json`). Both use
the same 0.3 N final load, flat two-S3 target, fine Q1 pressure, normal
regularization and Schur limits. The difference in load-step count remains a
comparison limit. At 16 Q4, the saved two-step terminal pressure differs from
the three-step four-phase run's *first* full press by at most 2.21e−11 Pa;
their integrated forces agree to saved precision. This check cannot prove
path independence at 32 Q4.

The read-only script rebuilds the case geometry, maps the saved final
displacements to physical Q4 bottom-skin nodes and fixed S3 top-skin plane,
and checks initial gap. It integrates squared differences of the two source
rows' piecewise linear nodal gap and displacement fields on common-refined
reference intervals. This reports physical nodal geometry; it does not
re-evaluate the nonlinear contact law or material state.
Independent read-only scrutiny found no concrete defect in state selection,
skin mapping or L2 integration. The reviewer confirmed that the nodal plane
gap includes source nodes outside finite target overlap and cannot substitute
for the separately evaluated physical contact gap certificate.

## Result

The raw comparison is
`reports/general_contact_d1_coupled_front_pose_16_32_dev_20260928.json`.
Both reconstructed initial nodal gaps are 40 µm. Final nodal gap minima are
−19.40 nm (16 Q4) and −17.91 nm (32 Q4). First positive-pressure source
modes begin at reference x=0.6875 and 0.65625, respectively. Both rows give
the same first-active coordinate.

| 16→32 field difference | Full strip L2 | Front x∈[0.625,0.75] L2 |
|---|---:|---:|
| Physical nodal gap | 4.42e−8 m | 6.86e−9 m |
| Source vertical displacement | 4.42e−8 m | 6.86e−9 m |
| Source horizontal displacement | 4.42e−12 m | 1.15e−12 m |
| Normal multiplier | 0.02573 Pa | 0.02552 Pa |

The L2 measure uses the dimensionless one-meter source reference coordinate
and averages the two source rows. The front interval holds about 98.4% of
the squared multiplier difference. Final active normalized weighted gaps are
below 1e−17 m in both saved states, and pressure agrees with the saved
multiplier to approximately 1e−13 Pa. These are weak nodal quantities;
independently checked physical gaps remain finite.

## Decision and limit

The large local pressure difference accompanies small changes in physical
source pose and an earlier first-active pressure node at finer resolution.
This is consistent with a coupled pressure response sensitive to front
location or structural/contact compliance, but does not identify its cause.
The weak multiplier residual is already negligible in these states, so more
augmentation at the same source meshes is not the next automatic action.
Before claiming complete C1 pressure stability, a new candidate needs a
justified front-aware reference or pressure-space response analysis that
separates structural resolution, multiplier representation and loading path.
Do not treat small integrated-force change as proof of pressure-field
convergence.
