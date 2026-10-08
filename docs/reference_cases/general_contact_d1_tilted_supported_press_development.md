# Supported tilted-target Q4/S3 press and source-x tangent

**Status:** bounded development, 28 September 2026. This is a prospective
planar shell-static case, not a new accepted C1 row.

## Decision and case

The earlier local target-tilt screen had meaningful tangential contact work
but no structural equilibrium. This case builds `dz/dx = 1e-5` into the S3
target reference geometry and uses its facet-normal reference director.
Both S3 target elements are fixed; the eight-Q4 source keeps the existing
left support and in-plane guide. Source and target use their physical bottom
and top skins. The distributed downward source load reaches 0.3 N in three
steps. All contact settings match the earlier flat fine-Q1 press: 10,000 Pa/m
normal regularization, 50 µm physical-gap tolerance, 1e-5 Pa multiplier
change, seven augmentation updates and 250/200 Pa Schur caps.

The first builder attempt put the tilted S3 nodes under the old `(0,0,1)`
reference normal. The formulation correctly rejected it before a solve with
`NativeParityCapabilityError: S3 V2D reference normal is not facet-normal`.
The case builder was corrected to use the normalized
`(-dz/dx, 0, 1)` director. This was a fixture error; no contact or S3
mechanics were changed. A fresh stiffness assembly passed before the bounded
solve.

## Results and limits

The raw press report is
`reports/general_contact_d1_distributed_8q4_tilted_target_press_dev_20260928.json`.
It completed all three steps in 126.3 s. At full press:

| Quantity | Result |
|---|---:|
| Integrated upward source force | 0.1069171230 N |
| Minimum physical gap | -0.1374 µm, within 50 µm |
| Supported pressure rank | 18/18 |
| Active pressure modes | 6 |
| Final multiplier change | 5.67e-14 Pa |
| Final reduced equilibrium residual | 4.72e-9 N |
| Full-press augmentation count | 4 |

Source/target integrated forces and moments are opposite to saved numerical
precision. Area and weighted-gap integration errors are 2.60e-16 m² and
2.40e-19 m³. The tilted and flat cases are mechanically different: the flat
full-press force is 0.1034798152 N. Their 3.32% difference is not an error
against a common reference. This one mesh does not establish response or
pressure-field convergence.

At that **equilibrated** tilted full-press state, the source-x direction on
material nodes 8 and 17 has a smooth observed pressure/support/overlap and
pair-derivative branch at both symmetric perturbation sizes. The raw coupled
probe is
`reports/general_contact_d1_distributed_8q4_tilted_target_coupled_tangent_dev_20260928.json`.

| Perturbation | Mapped contact action | Mapped contact relative error | Coupled relative error |
|---|---:|---:|---:|
| 1 µm | 0.0024578974 N/m | 1.22e-8 | 8.19e-16 |
| 0.5 µm | 0.0024578974 N/m | 2.55e-8 | 1.69e-15 |

The saved pressure and supported pose replay exactly. This is a meaningful
coupled tangential-force direction at a supported finite-area equilibrium.
Rotational degrees of freedom are fixed in this case, so the earlier separate
local moment screen remains the moment derivative evidence. Complete-tangent
admission still needs independently frozen directions, source/target work and
moment coverage, formulation review, and pressure-space qualification.

An independent read-only development review checked the S3 facet normal,
surface offset, saved press gates and separate mapped-contact derivative.
It found no concrete defect in these observations. The reviewer identified a
future-use step-count restriction in the probe; its metadata guard was
generalized without changing the tangent calculation or rerunning this
already passed case.
