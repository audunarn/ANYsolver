# P5 reference kinetic fields and modal diagnostics — 2026-09-05

Author research successor to `06e9a3c95a1ad609ca9660ae93d0471d00d225b5`.
No dynamic policy, formulation, production mass API or qualification is frozen
by this record. Accepted P3/P4 evidence and previous P5 failures remain intact.

## Actual kinetic fields

The P5 lift is `r_h=I(x)+U*(r0-I(X))`, `Q_h=U*R0` on each half cell.
At the stress-free reference its velocity fields are therefore

```
v = I(v_node) + omega_cell cross (r0-I(X))
omega = omega_cell
```

Both velocities are expressed in the station's physical R0 frame before
applying the fixed SPD 6x6 generalized section inertia. Integrating this
quadratic kinetic energy gives a factored 24-coordinate mass (external 18,
internal cell rotations 6). There is no direct kinetic energy on the nine
hybrid vertex-rotation coordinates. Curved lift velocity must be included;
using only straight-chord nodal translational mass would omit it.

The full kinetic factor has rank 15 in the sampled straight/curved cases.
Applying the existing static local map `[I;T]` gives an 18-coordinate mass
of rank 15, leaving three algebraic trace modes. No artificial inertia,
eigenvalue floor, penalty, pseudoinverse or modified elastic coefficient is
used to conceal this kernel. These are structural properties of this kinetic
trial field, not a proof of the correct final dynamic discretization.

## Two distinct reductions

1. **Static cell-rotation map before kinetic evaluation.** This is a Guyan
   approximation to dynamics. The three remaining zero-inertia trace modes
   are identified from the kernel of the 6x9 nodal-rotation part of T and
   eliminated using their stiffness equations. The resulting free pencil is
   15-dimensional, with six sampled rigid modes and nine positive elastic
   eigenvalues. Clamping the first vertex removes the mass kernel and gives
   a positive-mass, 12-dimensional nodal pencil.
2. **Retain internal rotational inertia.** Start with the full 24-coordinate
   elastic and kinetic factors. Eliminate only the nine exactly massless
   vertex traces through their stiffness equations. This is exact algebraic
   elimination within the uncondensed semidiscrete model, not omission of
   cell inertia. It gives 15 free dynamic coordinates, or 12 after clamping
   the first vertex. Expanded modes are checked against the original full
   equations, not merely the reduced eigenproblem.

The distinction matters: static elimination is not generally exact dynamic
elimination. As background, NASA's discussion of Guyan reduction describes
its static transformation and modifications accounting for omitted inertial
effects: [Ganesan, A noniterative improvement of Guyan reduction](https://ntrs.nasa.gov/citations/19940013360).
That bibliographic record is background, not a hash-bound P5 formulation
authority, independent implementation or review.

The research eigensolver returns all eigenvalues, including negative or
near-zero values. It does not silently clip, discard or classify them. The
tests separately check rigid and elastic counts for the declared specimens.

## Material approximation error found

For `reference(0.4)`, the existing complete coupled elastic section and the
new test's coupled inertia (translation diagonal 2, rotary diagonal
0.2/0.1/0.15, with declared off-diagonal coupling), the first six clamped
frequencies retaining full cell inertia are approximately:

`[0.11038246,0.11547815,0.17515385,0.30653809,0.52007140,0.60789490]`.

Relative frequency differences introduced by the static reduction are:

`[0.0000618158,0.0000346505,0.000369425,0.0282306,0.00216952,0.0440023]`.

Thus the fourth and sixth frequencies differ by about **2.8% and 4.4%**.
The straight coupled specimen also has a fourth-frequency difference of
about 2.8%. These are differences between two semidiscrete formulations,
not errors against a continuum engineering oracle. Nevertheless, they rule
out treating the static reduction as an exact or already-qualified dynamic
replacement. A regression test preserves the discrepancy; passing that test
records a limitation, not a passing 2% qualification gate. No mass tuning
or coefficient adjustment has been made.

## Straight family refinement checks

Bounded chains of 1, 2, 4 and 8 macros use the same existing reference
elastic factors and the candidate kinetic reduction. The largest matrix is
102x102. Separate uncoupled axial and torsional fixed-free families are
compared with `omega1=pi/(2L)*sqrt(stiffness/inertia)` at L=2.

| Macros | Axial relative frequency error | Torsional relative frequency error |
|---:|---:|---:|
| 1 | 0.0258591 | 0.0547862 |
| 2 | 0.00643730 | 0.0130524 |
| 4 | 0.00160715 | 0.00322520 |
| 8 | 0.000401643 | 0.000803965 |

These selected first frequencies converge below 2%. This does not qualify
bending frequencies, curved continuum frequencies, complete spectra,
prestressed modes, transient dynamics, buckling or mass reduction accuracy
over the complete domain.

## P3 boundary

The accepted P3 straight element uses a piecewise linear nodal generalized
mass with rank 18. The new actual-cell-spin kinetic mass differs even in
the straight limit. A test explicitly checks the difference. The accepted
P3 code and evidence are unchanged; its dynamic qualification cannot be
inherited by this alternative mass. Independent reconstruction/review must
choose and freeze the eventual P5 dynamic formulation, including any internal
dynamic state or algebraic trace elimination, before production exposure.

## Validation and provenance

- New mass/modal development suite: **17 passed in 1.68 seconds**.
- Existing eleven P5 development suites: **174 passed in 17.84 seconds**.
- Tests cover separately evaluated kinetic work, full curved rigid velocity,
  closed straight rigid kinetic energy, mass ranks, massless-trace elimination,
  six rigid modes, complete clamped spectra, full-equation eigenvector residuals,
  mass normalization, covariance, reversal, invalid input, trace-inertia
  mutation, preservation of negative eigenvalues, and rod-family convergence.
- Fixed 24-point mass integration is cross-checked by 48-point direct velocity
  integration. This is same-author numerical checking with shared P4 geometry,
  not an independent quadrature certificate or domain-wide proof.
- Probe SHA-256:
  `489BAB570AD9B7E73217364C0DF27376C5370AADDF1B17A08C8A61B96E95BC4D`.
- Test SHA-256:
  `73A96CFC6E5285701472F8581937BCE6D6ADCDD68045E63C1F3F349D24B6D92E`.

Only this record, a research module and its test are added. No production
source, accepted B2/B3/Q4/S3 mechanics, recovery, defaults, dependencies,
package metadata or workflow changes. No formal run, resource request,
push, merge, release or selector activation was performed.

## Next work

The dynamic policy is now an explicit unresolved gate. Compare the retained-
inertia model and candidate reductions with independent curved and bending
references, then choose a source-reviewed dynamic representation without
hiding the extra algebraic/internal structure. The extreme finite coupled
equilibrium failure, nonlinear material history, precision-safe restart,
multi-element finite assembly, postbuckling, installed-wheel integration,
independent qualification and objective beam-shell joints also remain open.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
