# Conservative distributed-load spectra — private integration

Parent: `d31539d95e0ac3fda249b26d833f66e6e40e4138`.
Do not edit the existing native force, moment, line-load, material, kinetic,
factor-chain or public beam/shell mechanics. Add a separate private spectral
entry point for actual accepted line-load checkpoints; do not convert them into
nodal-force or displacement-control histories.

## Operator

At the accepted load parameter, retain the complete discrete potential
`Pi(q,p) = p.k(q) - Psi*(p;history) - lambda W(q) - lambda f_nodal.x`.
The separate nodal-force potential has zero Hessian. The curved lifted line
potential generally does not: its cell rotations change physical line positions.
After eliminating the retained stress coordinates, keep the split material
factor and the complete geometric/external term:

`K = J^T C_p^-1 J + G_internal - lambda H(W)`.

The external term is constructed by the accepted load-only analytic derivative,
stored separately in the immutable operator packet, and bound into its identity
along with the load pattern, accepted parameter, checkpoint, quadrature,
section inertia and coordinate budgets. Do not replace this symmetric second
variation with the nonequilibrium spatial residual Jacobian.

Reuse the actual current lifted kinetic field. Nodal rotation traces have exact
zero inertia and their algebraic equations are eliminated. Do not introduce
artificial rotational mass. Physical cell-rotation inertia remains present.
The at-rest linearized problem excludes finite-velocity dynamics.

Material policy must be explicit. Frozen accepted plastic coordinates give an
elastic perturbation about the accepted loaded state, including its constitutive
offset. The last accepted increment's algorithmic operator remains a diagnostic,
not physical vibration authority. No history is advanced. All signed eigenvalues
are retained, not clipped or converted to real frequencies. This does not prove
a critical buckling load, a branch, continuum modal accuracy or qualification.

## Checks and preserved inputs

Read the exact one-, two- and four-macro checkpoints from the completed curved
line-force comparison and the previously saved straight plastic and
common-rotation line cases. Bind exact byte counts/SHA-256. The complete test
module forbids native nonlinear solve calls, so accepted history is replayed,
not re-executed. Check:

- Full stationary-system Schur complement against the split spectral operator.
- Independent rational-Q2/closed-derivative reconstruction of `-lambda H(W)`.
- Moderate-contrast signed eigenvalues against a separate dense generalized
  pencil calculation, plus `1e-11` native spectral and signed Ritz residuals.
- The omitted external term changes the actual spectrum.
- Frozen/algorithmic physical-plastic policies and exact unchanged checkpoint.
- Large common-rotation covariance and unchanged zero-inertia trace treatment.
- Input, load, inertia, cancellation, coordinate-limit and publication guards.

Preparation: 21 passed, 10.90 pytest seconds (12.432 supervised seconds), directory
`C:/Users/AUDUNA~1/AppData/Local/Temp/ge-beam3-line-spectra-preparation-1o_jg1ih`.
After freeze, run this same inventory twice in fresh directories and require
all seven saved operator/mode packets to be byte-identical. These are bounded
development cycles, not independently reviewed qualification cycles.

Each process: one numerical thread, 24 GiB process-tree job limit, 600-second
wall limit and 120-second CPU-inactivity limit. Constructors keep the existing
120-second cooperative guard and exact sign operations their existing bound.
Admitted coordinate budgets remain explicit (spectral 80/128/256, retained
256/512, exact sign dimensions 64/96/160); no default budget is enlarged.
Exclusive external outputs, no automatic retry, full tree cleanup, no resource
request reuse. No aliases, public defaults, version or publication changes.
