# G2 concrete constraint implementation freeze

Parent is accepted G1 closeout c8408eb509fdd2346f5aec2aa53ed262a3d07e7c,
tree 7880bae8200251836c428ee6008ece4fafbfbe96. Inherit the general-static
contract and G1a law without modifying them. This is an implementation freeze,
not independent scientific acceptance. The companion fixture JSON binds concrete
dimensions, loads, perturbations, acceptance scales and named tests before coding.

## Extent and semantics

Add only `_ge_beam3_g2_constraints.py`, `_ge_beam3_g2_analysis.py`,
`tests/test_ge_beam3_g2_constraints.py`, a bounded development runner, this
contract/fixture binding and later development status. All pre-existing files,
mechanics, evidence, public interfaces, defaults and versions stay unchanged.
Use the actual G1 elastic elements, FE assembler, native shared rotation store,
issued material validators and analytical second-order SO(3) primitives.
No fake stiffness, penalty springs, plastic surrogate or finite-difference tangent.

Constraint definitions are immutable canonical captures with explicit node IDs,
reference positions and physical node frames. Validate proper frames, orthonormal
selected-log axes, finite values, exact schemas, shape and topology before trials.
The graph contains one/two elements and at most six nodes. No mixed families.

AFFINE_TRANSLATION rows contain dependent global translation DOF, unique masters,
coefficients, constant offset and control rate: q_d=sum(a_j q_j)+b+c*lambda.
No rotational slot may enter an affine row. A deterministic dependency-first
expansion constructs q=T*z+u_bar(lambda) using rational arithmetic for the
captured binary64 coefficients. Reject cycles and duplicate dependent/master
DOFs, invalid IDs, booleans and nonfinite values. The actual global solve retains
all multipliers; T provides an independent condensed-comparison route and does
not replace nonlinear orientation constraints.

ORIENTATION_SUPPORT is B.T*Log(target.T*D), with 1/2/3 orthonormal axes and
D=Exp(theta-theta_committed)*Q_committed*R_node. Physical node frames are supplied,
not inferred from element roll. Targets are explicit proper frames at each load
point. No interpolation of accumulated rotation vectors is allowed.

RELATIVE_POSE has x_s-x_m-D_m*a and B.T*Log(C.T*D_m.T*D_s), including eccentric
translation work and the analytic Hessian. Empty B explicitly means translation
tie only. Relative Log must remain strictly below 0.9*pi; a common global
rotation is unrestricted. Invalid charts raise the existing typed cutback error.

The Newton residual is [r+J.T*mu,g], tangent
[K+sum(mu_i*H_i),J.T;J,0]. Reactions on the body are -J.T*mu; expose chart and
spatial work-conjugate moments separately. Affine prescribed-control work rate
is mu.T*g_lambda. Target-frame work is tested through the actual constraint
Jacobian, not an invented target interpolation. Rank guard uses the explicit
numerical resolution floor 64*eps*max(J.shape)*max(1,sigma_max); failure rejects,
never drops equations or changes constraints. All accepted residuals <=1e-11.

Use 24 Newton updates and nine line-search candidates, same local solver guards
and 600-second outer deadline. Constraint/rank checks precede assembly. Recheck
captured constraints after callbacks and within native material preparation.
Failure/cancellation preserves the accepted prefix and discards every trial.
Do not expose or use the inherited G1 zero-support solve on a G2 owner.

New restart schema GE_BEAM3_G2_ELASTIC_RESTART_V1 binds definitions, constraints,
target/control/load history, multipliers, accepted state and runtime. Require
external SHA-256 and deterministic replay; reject duplicate/nonfinite JSON,
tampered/resealed history and foreign G1 checkpoints. Reuse exclusive staged
publication. Recovery must be read-only and use accepted internal coordinates.

## Test details

S09: exact rational nested/multimaster affine expansion, cycles/conflicts and
nonzero axial displacement with independent EA/L force and control-work checks.
S10: 1/2/3 selected axes, unconstrained tangent directions, all three registered
finite-difference steps for J/H verification only (not implementation).
S11: two prescribed noncommuting target frames, replay/continuation, chart
cutback and common rigid rotation larger than the local relative-chart bound.
S12: eccentric tie with a=(1,.2,-.1), C=Exp(.1,-.05,.03), full first/second
variation, force/moment balance and virtual-work checks.
S13: independently formed constrained full multiplier and affine nullspace
systems agree; redundant orientation/pose equations reject without state change.
S14: node-ID permutation, connectivity reversal and proper global covariance,
including transformed target frames, force/moment and constraint row transport.
State tests: final callback and last-element prepare mutation, cancellation,
no-change accepted bytes/generations/history, unsupported model-channel rejection,
restart mutation, and deterministic complete development packets.

Smoke precedes a full rehearsal; every child has one numerical-library thread,
24 GiB/tree, 600 seconds, 120-second CPU/output inactivity limit. Wave <=1800s,
at most three children, no automatic retries. Preserve failures externally.
This task implements/development-tests G2; a frozen independent implementation
review and two separately authorized formal cycles are still required before
claiming G2 acceptance. Do not relabel development tests as formal qualification.

Next after successful implementation: independent G2 review and formal
confirmation, not G3 or full domain-parity claims.
