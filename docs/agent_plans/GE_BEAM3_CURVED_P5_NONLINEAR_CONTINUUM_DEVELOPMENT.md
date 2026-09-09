# P5 controlled nonlinear continuum comparison — 2026-09-06

Author research successor to `09615aab9640c138e574759adcfed92a61d5cc77`,
tree `c5aecbe96c418ad80df58f27d578b6d0de1c8900`.
The previous turn established connected nonlinear assembly and preserved a
large coarse-mesh plastic response difference. This turn tests an identical
single increment on every mesh against separately implemented continuum
equilibrium. No candidate mechanics or qualification evidence is modified.

## Source and separate reconstruction

The continuum kinematics and balance equations follow sections 2.3 and 2.4
of [Humer, Steinbrecher and Pechstein, v3](https://arxiv.org/html/2605.04573v3):
HTML equations 15, 16, 20 and 21. These are HTML labels, not an assertion
about printed-PDF equation labels. The already-preserved v3 PDF was rehashed:
2,646,466 bytes, SHA-256
`76AA9EDDDAE2EE16B47BF4E8255BDAA81678164B899E663E0B882B11C39BDB1E`.
It remains at the existing external `ge-beam3-source-authority-20260905`
location, unchanged.

For the analytic reference r0(t)=(t,h(1-t^2),0), t in [-1,1], material axis
2 is global z, J=sqrt(1+4 h^2 t^2), and reference material curvature is
k0=(0,-2h/J^3,0). The new standalone module integrates

- r_t = J R(e1+gamma);
- R_t = J R hat(k0+kappa);
- spatial n=F and m=m_left-(r-r_left) cross F.

The left position and material frame are prescribed. Three shooting unknowns
m_left enforce zero right-end moment. Spatial resultants are pulled into the
current material frame, then inverted through the complete coupled section.

For the existing declared directed-hardening law, **from virgin history only**,
stress s determines z=sign(a.s) max(0,(abs(a.s)-y)/H) and strain=C^-1 s+z a.
The inverse derivative is C^-1 on the elastic branch and C^-1+aa^T/H on the
active branch. Incremental density is
0.5 s.C^-1.s + 0.5 H z^2 + y abs(z).
This nonlinear/coupled extension and the parabolic shooting implementation
are repository derivations, not claims that the source paper supplies this
plastic law or this diagnostic algorithm.

The module imports only dataclasses and NumPy. It does not import ANYsolver,
the discrete producer, geometry implementation, AD kernel, recovery, section
implementation or other reference-case mechanics. Tests explicitly inspect
imports. Nevertheless this is same-author work: algorithmic separation is not
independent authorship/review or formal oracle authority.

## Bounded reference algorithm

Fixed-grid RK4 integrates position, the full material rotation matrix,
incremental potential and analytical first sensitivities to all three
shooting moments. No numerical frame derivative, rotation-vector accumulation,
frame normalization or polar projection is used. Shooting uses its integrated
Jacobian, at most 12 Newton updates, eight line-search candidates per update,
and 32 total integrations. Allowed grids are 32, 64, 128, 256 and 512 steps.
Invalid/nonfinite or excessively large integrated states fail closed.

Zero tip-moment residual must be at most 1e-12. Rotation orthogonality and
positive determinant are checked; the 1e-7 frame-drift guard is a reference
health limit, not a qualification tolerance or numerical-error estimate.
No failed solve retries itself or silently refines its grid. Formal resource
and process watchdogs remain separately required before qualification.

For the actual comparison cases, both reference solutions needed two shooting
updates and three integrations. At 512 steps, maximum frame orthogonality
error was approximately 1.41e-13 elastic and 3.91e-13 plastic. Tip-moment
residuals were well below 1e-12. Position differences decrease by more than a
factor of eight on 128/256/512 refinement; the 256-to-512 tip difference is
below 1e-9. This is a binary64 refinement study, not multiprecision or an
outward interval certificate.

## Controlled comparison and finding

Every discrete specimen uses the same height-0.4 parabolic reference, coupled
6x6 section, direction [1,0.2,-0.1,0.3,-0.4,0.5], H=0.4 and force
[0.01,-0.03,0.02]. Every specimen starts from zero material history and takes
one increment. The elastic control sets y=1000; the plastic case sets y=0.02.
No unloading or final permanent-set comparison is mixed into this experiment.

The 512-step continuum tip displacements are approximately:

- Elastic: [-0.00198861,-0.04380808,0.03745713].
- Plastic: [0.03598138,-0.06390458,0.06154385].

Relative Euclidean tip-displacement errors against those references are:

| Macro elements | Elastic error | Plastic error |
|---:|---:|---:|
| 1 | 2.46828% | 34.02226% |
| 2 | 0.59267% | 16.70680% |
| 4 | 0.14653% | 5.52980% |
| 8 | 0.03653% | 1.50606% |

Both errors and incremental-potential errors decrease monotonically. The last
tip-error refinement slopes are approximately 2.00 elastic and 1.88 plastic.
The coupled response exercises all six strain components. Eight elements fall
below the requested 2% engineering comparison level for these two cases only.
The substantial coarse plastic errors are explicitly retained in regression
assertions, not concealed by comparison with a nearby discrete solution.

For four and eight elements, exploratory 8-versus-24-point-per-half comparisons
agree closely; the tests bind the eight-element comparison at 1e-11 for
positions, rotations and potential. The default-order eight-element specimen
has 384 stations. These virgin-increment cases do not resolve the previously
observed integration discrepancy in a different perturbed/history case.

The evidence supports coarse-discretization error as the explanation for this
controlled first-increment discrepancy; it does not establish the cause or
accuracy of the earlier complete-cycle permanent-set difference. That still
requires an independently checked continuum history evolution and identical
multi-increment schedules on every mesh.

## Verification and handoff

- New reference/convergence suite: **19 passed in 17.63 seconds**.
- Existing eighteen P5 suites: **311 passed in 44.77 seconds**.
- Checks cover isolated imports, full constitutive inverse/branch derivative,
  analytical shooting sensitivities against a directional difference, exact
  straight axial tension/compression plastic solutions, constant-couple
  circular bending of the continuum IVP, stress-free curved geometry,
  reference refinement, balance, byte-identical repeat in the same environment,
  controlled discrete convergence, quadrature sensitivity and bounded failure.
- The exact axial compression solution is not a stability or buckling proof.
  The constant-curvature test validates the reference integrator; it is not
  an exact finite constant-curvature patch requirement for the discrete beam.
- Reference SHA-256:
  `5CEF46FB165CE2AB6B5BCDC6BD38CC22070CD3D5E1576EF490B86D9EB0E1F8FC`.
- Test SHA-256:
  `675A749B458AB40153915FA84487E5D7108105C09F2593E207734E2AADE9930E`.

Only the new standalone reference, its test and this record are added. No
production source, B2/B3/Q4/S3 mechanics, defaults, recovery/state law,
dependencies, workflows, package metadata or historical evidence changed.
There was no candidate freeze, formal request, independent review, push,
merge, publication or activation. These remain small research checks, not
a performance campaign or formal deterministic qualification cycles.

Next, establish controlled nonlinear history-reference evolution and assembled
restart/continuation. Preserve the prior extreme coupled local failure and
history-dependent integration issue. General material adapters, arc length,
postbuckling, prestressed modal/buckling, finite dynamics, curved/slender
domain coverage, independent review, installed-wheel production integration
and objective eccentric/curved beam-shell connections remain incomplete.
The full objective remains active. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
