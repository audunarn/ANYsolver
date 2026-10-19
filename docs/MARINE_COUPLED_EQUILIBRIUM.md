# Coupled marine equilibrium (development)

`anysolver.marine_coupled_equilibrium` exposes `evaluate_marine_static` and
`solve_coupled_marine_equilibrium` under
`marine_coupled_equilibrium_development_v1`. It consumes the same immutable
`MarineMechanicalModel` used by the common transient solver. Static rates and
accelerations are zero. Full six-DOF body charts, exact material fairleads,
mechanical links and all free line nodes are solved together.

## Physical ownership

The public potential-flow `evaluate_static` method evaluates reference
buoyancy/preload minus incremental restoring in its fixed equilibrium
hydrodynamic coordinates. The existing work-conjugate pullback includes all
baseline/follower derivatives. Gravity is excluded from that data contract;
only the model-selected `DryGravityContribution` adds it, once at the body's CG.
Wave excitation, radiation, added inertia, clocks and radiation history are not
static loads. Potential-flow dynamic arrays do not affect this static trial.

Public Morison `evaluate_static` uses stationary distributed buoyancy and steady
current through its existing environment, geometry, ownership and force law.
It refuses active waves rather than freezing a wave phase. Body/node rates and
accelerations must be zero. Unknown dynamic/history providers have no inferred
static contract and are refused, not dropped. Existing whole-layout ownership
checks remain in force; line/member physical overlap remains inadmissible.

## Initialization and continuation

When lines exist, the public fixed-fairlead staged line initializer/solver runs
first (catenary, net weight, current, contact). It preserves all original wetting
and fluid-domain admission. Bodies initially remain at the caller's poses.
The full physical static force at that state defines temporary constant WORLD
holding wrenches at the body origins. They represent explicit continuation
supports, including each body's force and moment, and are not penalty springs.

The coupled solve ramps removal of those holds (default.25/.5/.75/1). At every
iteration all physical body, link and line forces are re-evaluated. Holds use
the public `WorldWrenchContribution`, so chart pullback/follower tangents stay
exact as bodies rotate. Their force/tangent vanish entirely at final release;
the final audit re-evaluates the physical model without any support provider.
Gravity, buoyancy/preload and current remain the actual full declared loads.

The static residual is minus external force and K is its position derivative;
Newton therefore solves `K*delta=force`. Compatible singular mechanisms use
bounded least-norm Newton on the same row-scaled physical operator, with a
linearized range-residual check. No mass, compression or artificial stiffness is
added. Admissible residual-decreasing line search handles branch changes. Body
chart and declared hydrodynamic motion bounds remain; failed trials are discarded.
Exact rechart of stationary bodies is audited before each accepted stage. No
dynamic velocity/history transport or memory commit is necessary.

## Residual evidence and failure

Body chart covectors are converted to WORLD wrenches at the body origins for
the convergence criterion. `CoupledStaticSpec` gives independent force scale(N),
moment scale(Nm), force absolute tolerance(N), moment absolute tolerance(Nm) and
relative tolerance. Limits are `atol + relative_tolerance*scale`. Node residuals
use the force limit. The maximum ratio to each applicable limit must be<=1;
normalized residual uses the corresponding scale. Nonfinite derived limits,
metrics or normalizations cannot be accepted. These are prospective development
solver controls, not W6 qualification criteria.

Successful results retain immutable accepted stage poses/nodes, metrics and
final audit. The latter includes WORLD body residuals, node residuals, physical
force components, real compliant penetration and zero remaining support fraction.
The component decomposition is also audited against force/moment limits. Sparse
trial tangents are fresh disposable matrices, not authoritative retained state.
Failure/cancellation preserves completed stages and line-only evidence; no
unconverged trial becomes an accepted result. Inputs and data remain unchanged.

## Hydrodynamic geometry binding

The final pose is hashed using the original coefficient-frame conventions and
compared with the source's equilibrium hash. `coefficient_rebind_required=True`
means the equilibrium body geometry changed. No coefficient frames or source
hashes are silently updated. A consuming application must invalidate dependent
coefficients and regenerate/re-admit them before treating the new equilibrium
as a qualified hydrodynamic reference. The static candidate itself remains a
development calculation about its declared original source frames/bounds.

## Remaining acceptance

Development tests include an independent closed-form two-body surge root,
finite-rotation support/rechart invariance, both bodies plus one link/three lines/
two current-loaded Morison braces, full force-tangent finite differences,
baseline/restoring isolation, force/moment criteria and preserved cancellation/
failure evidence. Synthetic full coupled coefficient fixtures remain explicit.
This does not admit a real full-six BEM source, large-excursion hydrodynamics,
contact stability/uniqueness, W6 catenary/contact/refinement qualification, friction,
partial wetting or W8/W9/W10 acceptance. Qt static jobs/persistence/replay are the
next application integration step. No BEM or transient campaign ran in this slice.
