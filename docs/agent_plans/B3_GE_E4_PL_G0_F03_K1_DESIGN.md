# F03-K1: reduced-space rank inventory, design before registration

21 September 2026. **Design under review, not an executed or accepted gate.**
The K0 v2 screen found row-rank loss in all union/dual candidates and
unsupported trace modes even when P1-beam had full row rank. D1 showed a
finite-pose derivative plateau at larger central-difference steps and severe
forward-solution sensitivity in the poorly conditioned KKT cases. Neither
result changes the frozen K0 failures or selects a line space.

## Limited question

Before another expensive coupled KKT study, ask whether low-dimensional
exact multiplier spaces can retain independent rows across registered
beam:shell ratios, and quantify the tradeoff with unsupported physical trace
modes. Reducing multiplier dimension cannot by itself eliminate unsupported
trace modes of an unchanged primal discretization. This is
an **algebraic diagnostic**, not an inf-sup proof, nonmatching convergence
claim, or production-space selection. It must not be substituted for
full six-channel F03 work, physical load response, shear/director/torque
qualification, or the independent mechanics review.

Keep K0's physical E4-PL in-plane Q4/S3-V2D panels and native retained B3
reference fixture unchanged. Integrate on the union of all beam-half-cell,
shell-host/diagonal, and candidate-basis knots, with both two- and four-point
rules. The shell-host breakpoints are **quadrature subdivisions**, not
automatically multiplier DOFs. Compare these five exact spaces, each with
three planar multiplier components per scalar basis function:

| Name | Scalar basis and knots | Dimension |
|---|---|---:|
| `p0-beam` | Discontinuous constant on each native beam half-cell | `N_b` |
| `p0-shell-grid` | Discontinuous constant on each physical shell x interval clipped to `[0,1]` | `N_x` |
| `p1-shell-grid` | Continuous linear on that clipped physical shell x grid | `N_x+1` |
| `p1-beam-coarse` | Continuous linear on every second native half-cell knot | `N_b/2+1` |
| `p1-beam` | The unchanged K0 continuous beam-grid control | `N_b+1` |

The first four are new *diagnostic* choices, not asserted stable mortar
spaces. The earlier `dual-union` algebraic candidate is not a derived
biorthogonal mortar dual and is not relabelled as one. A genuine dual-space
derivation, if possible, remains part of the full F03 comparison.
The panel grid is `x=-.5+i/N_s` on `[-.5,1.5]`. `N_x` counts the intervals
after clipping its edges to `[0,1]`: normally `N_x=N_s` for the even
registered values, but `N_s=1` has an edge at `.5` and **two** intervals.
Do not construct a fictitious one-interval multiplier grid for that case.

## Proposed frozen inventory and observations

Core: `N_b=4,8,16`, `N_s/N_b=1/2,1,2`, both Q4/S3-V2D: 18 meshes and
90 candidate matrices. Ratio reach: `N_b=8`, `N_s/N_b=1/8,1/4,4,8`,
both topologies: eight additional meshes and 40 candidate matrices. Total
26 meshes, 130 candidate matrices. Ratio reach does not provide three
refinement levels; a passing candidate must later satisfy the final
reciprocal 1:8 refinement requirement separately.

For each candidate preserve complete mass-whitened/work-scaled constraint
singular values, row count/rank at K0's relative `1e-10` cutoff, weighted
trace singular values/rank at the *same* threshold, trace-rank-minus-row-rank,
mass definiteness, quadrature comparisons, station/row incidence, reference
gaps, and model dimensions. Distinguish row-rank loss from full row rank
with unsupported trace modes. Do not drop rows or add a penalty. If a
candidate has zero singular reference norm, classify it as invalid rather
than divide by a manufactured floor. Source, package graph, threads,
hardware, resources and one-shot evidence grammar must be bound to a clean
commit and reviewed before execution. Use a 7200 s external wall limit and
8 GiB sampled child RSS bound, report the sampled limitation explicitly.
Preserve K0's `1e-12` m/rad reference-gap cutoff and `1e-10` quadrature
comparison. A zero/nonfinite four-point quadrature reference yields an
invalid **candidate** record without hiding other evaluation errors.

The inventory will **prioritize** at most two candidates for a separately
registered KKT/physical-refinement study. A candidate is eligible for
prioritization only if it has full row rank on all 18 core meshes and all
eight ratio-reach meshes, finite positive multiplier mass, and valid
reference/quadrature results. Among eligible candidates, rank by the
observed unsupported-trace-mode inventory, dimension and sparsity, clearly
reporting ties and tradeoffs; these diagnostics alone cannot select a
production space. If none qualifies,
record the negative result and revisit shell-side trace/pose and interface
space derivation; do not weaken the test after observing data. Even an
eligible candidate is not accepted until patch, work, physical gap,
oscillation, norm-scaled inf-sup, convergence, six-channel and independent
reference checks pass the complete G0 contract.

Preexecution independent review must check basis definitions and partition
unity, index and knot interpretation, trace rank calculation, mass
normalization, quadrature subdivisions, resource scaling, and evidence
identity. The first product implementation remains barred until G0B passes.
The final F03 programme still requires curved/eccentric six-channel work,
physical torque and director/shear/thinning checks, true derived dual-space
comparison, reciprocal 1:8 refinements, and executed independent references.
