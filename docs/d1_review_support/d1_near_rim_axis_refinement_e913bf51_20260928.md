# Independent near-rim Q1 axis refinement — development evidence

This source-only scalar obstacle comparison uses the unchanged independent
`d1_rim_oracle.py`, the saved 16×8 coupled-comparison inputs and the same
FV256×320 reference on fixed 8×9 support-aligned force bins. The execution
source is `e913bf51`; the [raw result](d1_near_rim_axis_refinement_e913bf51_20260928.json)
binds the oracle and saved-input hashes. The [bounded resource record](d1_near_rim_axis_refinement_resource_e913bf51_20260928.json)
retains the command and 180 s / 1 GB limits.

| Source-only Q1 mesh | FV bin L2 error | Minimum physical Q1 gap | Active unit-diagonal compliance eigenvalue ratio |
|---|---:|---:|---:|
| 16×8 | 0.3344% | −19.3 nm | 9.77×10⁻⁵ |
| 32×8 | 0.4811% | −17.9 nm | 2.34×10⁻⁵ |
| 16×16 | 0.3056% | −41.6 nm | 6.69×10⁻⁵ |
| 32×16 | 0.3944% | −22.0 nm | 2.16×10⁻⁵ |

All four scalar solves passed the script's equilibrium, complementarity,
nonnegative-pressure and bin-reaction checks. The physical gap samples every
Q1 grid corner inside the obstacle and the interpolated `y=0.9` rim; these
are the extrema candidates for the clipped bilinear cells. The two saved
source-only bin fields were reproduced before adding the off-diagonal cases.

Refining x worsens the bin error at either y resolution; refining y improves
it at either x resolution. The vector-valued x/y interaction on the common
bins is 0.0259% relative to the 32×16 bin norm. This explains the small
16×8-to-32×16 reversal without a larger coupled solve. The response-space
ratios are positive but fall with x refinement and do not establish uniform
pressure stability. Each mesh change refines structural and pressure spaces
together. The independent reviewer found no concrete arithmetic or identity
defect in the earlier two off-diagonal calculation and requested these
four-corner physical-gap and compliance checks. This extension has not been
independently accepted.

The scalar fixed-target oracle cannot qualify the nonlinear deformable-target
workflow. The obstacle rim has a concentrated line reaction, so pointwise
pressure peaks are not used as a convergence oracle. This record is a
development discriminator, not D1 qualification.
