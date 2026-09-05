# P5 full-inertia chains versus continuum modes — 2026-09-05

Author research successor to `7c2f9f0263bf529f9978cb690d0f69b7037c87c0`.
This adds a continuum comparison for the unresolved dynamic policy. It does
not freeze a candidate, qualify dynamics, or change accepted P3/P4 evidence.

## Separate continuum construction

The new continuum module imports only NumPy and dataclasses. It imports no
ANYsolver/P5/P3/P4 mechanics, frames, matrices, recovery or modal helpers.
It directly represents the analytic parabola `r(t)=(t,h*(1-t*t),0)` and its
material frame `(tangent,global-z,tangent cross global-z)`.

Infinitesimal spatial displacement u and rotation theta are independent
conforming polynomial fields. The linear continuum strains and kinetic fields
are reconstructed directly:

```
gamma = R^T (u_s + tangent cross theta)
kappa = R^T theta_s
material velocity = [R^T u_dot; R^T theta_dot]
```

The full coupled SPD section and full coupled SPD section inertia are retained.
Each spatial field uses `(t+1)*P_j(t)`, which imposes the left clamp exactly;
the free-tip conditions are natural conditions of the weak potential. There
are no cell rotations, moment jumps, static condensation or fitted terms.

The bounded reference uses 4/8/12/16 polynomial terms and 48/64/96 quadrature
points. At most 96 coefficients are present. QR of the velocity-energy factor
and SVD of the transformed strain factor avoid squaring conditioning before
extracting the lowest frequencies. A preliminary normal-equation eigenvalue
calculation showed quadrature-comparison roundoff up to approximately 3.7e-11;
the factor calculation reduces that comparison to approximately 2.5e-14 or
less for the three specimens. The energy functional is unchanged.

For the first six frequencies, 12-to-16-term changes are at most about
2.15e-8 (height 0.7). The development test checks polynomial convergence at
1e-7 and fixed-degree quadrature comparison at 1e-11. These are numerical
reference checks, not certified error bounds. The zero-frequency tip compliance
is compared with the existing analytical continuum integral, with worst sampled
relative discrepancy about 3.6e-11. The polynomial-approximation check uses
1e-9, not an exact-equality assertion for a nonpolynomial solution.

This is separately constructed continuum code by the same author. It is not
independent authorship, an adaptive multiprecision oracle, a source-reviewed
dynamic formulation or a formal qualification reference.

## Full-inertia chain assembly

The new chain probe assembles the existing uncondensed stiffness and actual
kinetic-field mass before eliminating shared zero-inertia vertex traces.
All cell rotational inertia is retained. The first vertex is clamped, and
only 1/2/4/8 macros are supported. Eight macros have 150 uncondensed variables,
48 free algebraic traces and 96 dynamic coordinates. This is not an 18x18
production element-mass API or a completed dynamic solver integration.

Eliminated modes are identified by their exactly absent kinetic columns and
solved algebraic stiffness equations, not by discarding small eigenvalues.
Expanded mode vectors satisfy the original assembled equations. The probe
does not use arbitrary mass, eigenvalue clipping or coefficient changes.
Direct congruence is used for these moderate-section diagnostics; no new
high-contrast cancellation-safety claim is made.

## Physical frequency and mode comparisons

The specimens have h=0, 0.4 and 0.7 and use the existing complete coupled
elastic and inertia fixtures. All comparisons below concern the first six
modes of these particular clamped specimens, not a complete spectrum/domain.

At eight macros:

| Height | Largest first-six frequency error | Lowest corresponding kinetic-field MAC |
|---:|---:|---:|
| 0 | 0.00368168 | 0.99922964 |
| 0.4 | 0.00395327 | 0.99916205 |
| 0.7 | 0.00502284 | 0.99871799 |

Thus the largest sampled error is approximately 0.503%, and all corresponding
mass-weighted mode correlations exceed 0.9987. Mode comparisons integrate the
actual lifted translational and cell-angular velocity fields against the
continuum fields. They do not compare raw nodal vectors or assume a physical
match solely from sorted frequency indices. Each mode has its largest overlap
with its corresponding continuum mode in these samples.

For h=0.4, maximum first-six full-inertia frequency errors at 1/2/4/8 macros
are approximately 26.998%, 6.388%, 1.584% and 0.395%. Refinement is essential:
the coarse specimen is not within a 2% engineering comparison level.

Not every modal error improves on every refinement. At h=0.7, first-mode
error increases from approximately 0.1493% at one macro to 0.1633% at two,
then decreases to 0.0618% and 0.0169%. A test explicitly preserves this
nonmonotonic observation. No universal monotonic-convergence claim is made.

Both straight bending planes are additionally compared with the first
Euler-Bernoulli cantilever frequency in a declared shear-stiff, small-rotary-
inertia limit. The continuum and eight-macro full-inertia values satisfy the
2% engineering comparison. This is an asymptotic reference comparison, not an
exact equality for a shear-flexible/rotary-inertia model.

## Static reduction remains a separate approximation

The previous 2.8%/4.4% coarse-macro discrepancies remain preserved. At h=0.4
and eight macros, the static reduction also comes within 2% of this continuum
reference for the first six modes (largest error approximately 0.452%). It
still differs measurably from full inertia and is not thereby an exact dynamic
reduction. This turn does not select either policy for production or transfer
accepted P3 dynamic authority to a changed kinetic field.

## Tests and provenance

- New focused suite: **14 passed in 2.05 seconds**.
- Existing twelve P5 suites: **191 passed in 18.28 seconds**.
- Coverage includes polynomial/quadrature convergence, modal equation residuals,
  mass normalization, analytical static compliance, both bending planes,
  full-inertia assembly, physical kinetic-field mode correlations, preserved
  coarse nonmonotonicity, static-reduction discrepancy, source-import isolation,
  and invalid bounds/nonconforming input rejection.
- Continuum reference SHA-256:
  `45222199DDE01BA3D29FC1FB831439C52DEDD63092A1A45B4C1E7947FE53532D`.
- Chain probe SHA-256:
  `F8B774FD7B19910685ADFEC7DCEA360081C94302F233F641577504DB0C5EB1BA`.
- Test SHA-256:
  `F1A9CBC3FD2F7667BC97A1FED975C57DAEDA19D3C442242644C0221F43049244`.

Only two research modules, one test and this record are added. No production
source, B2/B3/Q4/S3 mechanics, defaults, recovery, dependencies, workflows,
package metadata or accepted evidence changes. No formal resource request,
qualification cycle, push, merge, release or activation was performed.

## Remaining programme

These checks support further development of the full-inertia curved model,
not full qualification. Dynamic representation/solver integration, independent
source/equation review, curved domain and slenderness coverage, prestressed
modes, transient dynamics and buckling remain unresolved. So do the extreme
finite coupled equilibrium case, nonlinear material state/restart, multi-element
finite paths/postbuckling, installed-wheel integration and objective eccentric/
curved beam-shell connections. The original goal remains active and unchanged.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
