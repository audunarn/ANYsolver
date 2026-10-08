# Fixed-pose affine contact-front pressure discriminator

**Status:** bounded development, 28 September 2026. This does not amend the
accepted fixed-pose partial-pressure rank/force case or qualify coupled shell
pressure convergence.

## Question and calculation

The coupled distributed-press pressure-field change grew at the moving front
under 24→32 Q4 source refinement. To separate the base pressure interpolation
from structural feedback, the existing central Q4/S3 probe was held at the
same smooth affine pose for 8, 16 and 32 Q4 source columns with four rows. The
target is the rectangle x∈[0.24,0.77] m, y∈[0.21,0.73] m. The prescribed gap
is (g(x)=s(x-m)), with (m=0.505) m, (s=50\,\mu\mathrm m/0.53\,\mathrm m), and the explicit
penalty is 100,000 Pa/m. No coupled equilibrium or multiplier update occurs.

The independent oracle integrates each Q1 hat and (x) times that hat in
closed form over the rectangle. It computes each supported nodal pressure from
its analytic weighted mean gap. It also integrates the squared difference
between the saved piecewise Q1 pressure field and
(p(x)=\epsilon\max(s(m-x),0)) over the rectangle. Each cell is split at the
analytic front; two-point product quadrature is exact for that squared
piecewise bilinear integrand. A hand-computed one-cell case checks the oracle.
The continuum expression is a local-plane approximation: the actual moving
projection onto the slightly tilted source plane is distinct.
Independent read-only scrutiny found no concrete defect in the hat moments,
field integral, units, one-cell check or scoped interpretation. This is
development review, not an acceptance assessment.

## Result

The raw pose and pressure report is
`reports/general_contact_d1_fixed_front_8_16_32x4_dev_20260928.json`; the
read-only comparison is
`reports/general_contact_d1_fixed_front_pressure_oracle_dev_20260928.json`.

| Q4 columns × rows | Supported modes | Max support discrepancy (m²) | Max nodal pressure discrepancy (Pa) | Relative field L2 error | Integrated force (N) |
|---:|---:|---:|---:|---:|---:|
| 8 × 4 | 28 | 5.41e−10 | 5.46e−9 | 10.50% | 0.160946539 |
| 16 × 4 | 44 | 4.94e−10 | 8.08e−9 | 3.70% | 0.169761398 |
| 32 × 4 | 76 | 4.00e−10 | 9.39e−9 | 1.37% | 0.171773485 |

The analytic local-plane integrated force is 0.17225 N. The numerical force
approaches it over these three grids. The maximum nodal pressure discrepancy
is small relative to the approximately 2.5 Pa pressure scale. The pressure
field L2 error also decreases monotonically in this fixed-pose case.

## Decision and limit

The base primal Q1 pressure update and integration behave as expected for this
smooth affine fixed-pose front. This rules out a gross pressure-law or overlap
integration error as the explanation for the **same local-plane case**. It
does not distinguish coupled structural mesh response, moving-front geometry,
load path, or multiplier history in the distributed press. The next bounded
coupled diagnostic should compare source pose/gap and pressure at the front at
the existing saved meshes, and assess enforcement and structural refinement
separately. No automatic larger coupled run follows from this result.
