# Private affine Q4 stable chart: source-authority addendum

Status: DRAFT_PENDING_INDEPENDENT_REVIEW. This document
authorizes no implementation or execution until its complete evidence bindings
and independent design review are accepted. It changes numerical evaluation
plumbing only, not the discrete potential, chart map, recovery representation,
scientific scope, fixture recipe, tolerance or public source.

## Preserved authority and incident

The unchanged numerical contract is
GE_BEAM3_Q4_AFFINE_NUMERICAL_RECOVERY_CONTRACT.md, SHA-256
21cec54b2469e291c8f90a2c042e3cf693a14f7bc10efd5111ea842ca65a218c.
Its accepted design review, exact-affine evidence, extension lemma and original
source hashes remain immutable. This addendum is an explicit successor to the
original helper-selection rule, not an edit of that contract or its history.

Preserve executed freeze eb84fd581bfeae267a644e7800465659d9e5f686, tree
dab8b2bfc0451dd3588bb041f206d9ae8dc520d2. Its separate square ZERO/MIXED smoke
passed. Its full rehearsal stopped in its first batch: SQUARE::0.01 MEMBRANE
chart second derivative differed from the independent derivative by normalized
8.175879658173228e-10, exceeding the unchanged 1e-11 threshold. The previous
ZERO context passed. Another child exposed a test-only coupling-orientation
mismatch (24x35 versus35x24), which is corrected independently and is not a
reason to change the mechanical stationary convention. This is BLOCKED
process/evidence, not an accepted typed scientific NO_GO. All children drained;
no full canonical aggregate, rehearsal acceptance or formal cycle exists.
The earlier ee3b41e serialization-blocked smoke and all its evidence remain
preserved as well. No consumed attempt is retried.

Bind the independently inspected evidence record
eb84fd5-smoke-rehearsal-evidence-review.json, SHA-256
ea7268a4083e893b0ce8c1bfe3e664f0eb4f35d612decf244eeb7a1cc7eae776,
and complete raw-file manifest eb84fd5-smoke-rehearsal-files.json, SHA-256
00ce4c821d932ac0bf493cc76a0ee1d186043b9badfb94ef8f309586e2f911d9.
Reviewer-readable copies are under
C:/Github/ANYsolver/.perf2-worktrees/.beam-core-review-20260913/.
The verified durable archive roots are
C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/beam-q4-affine-eb84fd5-smoke-20260913/
and beam-q4-affine-eb84fd5-rehearsal-20260913/ under the same parent;
each contains18 raw files checked by byte count and SHA-256. Review and raw-file
manifest are additionally preserved in the rehearsal archive.

Smoke run dfda4a98-6f72-467f-9149-6992a0a272ed has12187-byte scientific.json,
SHA-256 882ecf7ffafde511c89a54323bf42fffd0439766af369e1c7269c74986e5aa8b,
and process.json SHA-256
1e8d8f4224ded1385090a84938d14c3af5dd1dce89091fa3c478adebf5209ef4.
Rehearsal run0be67944-c48c-4bd7-9c65-ff784d1b515a has no aggregate;
process.json SHA-256 is
fa150b30b512aad3b090e7be4d7a6ae9c1fd87815f72444f272fab280214a72b.
Its3597-byte node-01/stdout.log SHA-256 is
78234c3919b47e1acd2909b227f191aa71165d12c91e533c2178d7bb6d0c5fcd.
The coordinator recorded node01 ABORTED_PEER_FAILURE after node02's failure;
the logged derivative discrepancy is not canonical acceptance or a typed
scientific counterexample. Only three of15 rehearsal nodes launched.

## Accepted private evaluator authority

Use the existing immutable private evaluator, not a new fitted approximation:

| Bound source/evidence | SHA-256 |
| --- | --- |
| src/anysolver/_ge_beam3_g3c_so3_numerics.py | 588ace39570658f1a83c0110d3a019ebad770d6091b271ff4bbc40b97f96e12e |
| docs/GE_BEAM3_G3C_SO3_NUMERICS_CONTRACT.md | 269bcd4e1fda151e7c22c396a70c43498e8450b222c263dd2655b9ca45998496 |
| docs/reference_cases/ge_beam3_g3c_so3_numerics_implementation_review_v1.json | 4debde89b44c990478487dda4852d7734b852ca01dfb2d3626e782c2328756f1 |
| docs/reference_cases/ge_beam3_g3c_so3_numerics_confirmation_receipt_v1.json | aa7225cae347662bf92b3c02f8a1ff541d40e67f13db21900d0ad3269f88b91f |
| docs/reference_cases/ge_beam3_g3c_so3_numerics_result_v1.json | c8b938bbdbcce329aa83afc00037905d158142d7d2e417acee159bab95aba6fd |

Its accepted exact source version is commit
3defc6fa57fc106ef7d5b576b0a33433d6704035, tree
5d71910b4bcc64b328ebbdcffaad92212ad3db55. Policy is
GE_BEAM3_G3C_ISOLATED_SO3_NUMERICS_V1. Its prior confirmation established the
private kernel only, not affine-Q4 recovery. Do not rerun or reclassify that
historical evidence as this new graph of callers.

## Source diagnosis and identical mathematics

The original _ge_beam3_g3c_local_shell.deformation calls the original Jet Log
factor in _ge_beam3_mixed_ad. For the registered square MEMBRANE field the ideal
in-plane deformation gradient is [[1.012,.004],[-.003,1.007]]. Its polar angle is
atan2(-.007,2.019), approximately -0.00347; delta=1-cos(theta) is approximately
6e-6. This enters the original closed-form branch, not its delta<1e-7 series.
The second derivative

    F''(c)=-3c/s^4+acos(c)/s^3+3 acos(c)c^2/s^5,
    F(c)=acos(c)/s, s=sqrt(1-c^2),

subtracts terms of order1e10 to recover a value near4/15. This is a concrete
source instability consistent with the observed D2 discrepancy; it is not
a claim that all remaining numerical failures have been diagnosed.

Retain Q_i=Exp(eta_i) Q_a,i, the same equal-weight proper Davenport fit R,
d_translation=R^T(x_i-xbar)-(X_i-Xbar), and
d_rotation=Log(R^T Q_i). Keep every first/second derivative from analytic Jet2
chain rules. Change only evaluation of Exp/Log scalar factors through the
accepted stable functions. The original fit's simple-top-eigenvalue guard and
relative/increment0.9pi limits are unchanged; no normalization, clipping,
regularization, pseudoinverse or numerical frame differentiation is added.

The accepted evaluator uses degree16 factorial series for sinc/cosc at
theta^2<=1, with differentiated Horner value/first/second recurrences; outside
that range cosc uses its half-angle form. For Log it uses the degree40 series
a0=1, a_n=n*a_(n-1)/(2n+1) in delta=1-c when c>=1/2, and its analytic closed
form elsewhere. The bound contract proves second-derivative tails below3e-21
for Log and1e-35 for Exp on those intervals; its independent scalar/full-Jet
checks reported maximum normalized error8.857026259447574e-16. These bounds
justify the fixed existing evaluator, not a relaxed affine-Q4 tolerance or a
guarantee of this larger chart's numerical accuracy. Tiny physical responses
and every retained case must still pass their actual relative checks.
In particular, cancellation in R^T xc-Xc for MIXED amplitude1e-6, whose local
displacements are of order1e-8, remains an unresolved numerical-gate risk.
This addendum does not repair that subtraction or substitute another fit.
The next complete rehearsal must establish its actual accuracy. A remaining
failure needs its own source diagnosis and reviewed correction, never a norm
floor, weakened tolerance, skipped tiny context or arbitrary fit replacement.

## Exact caller-map and implementation extent

After independent acceptance, add one private module
src/anysolver/_ge_beam3_g3c_affine_q4_chart.py with identity
GE_BEAM3_Q4_AFFINE_STABLE_CHART_NUMERICS_V1. It may explicitly copy the short
existing deformation and spatial Exp-connection equations, with source
attribution, or wrap their pure constituents. No dynamic cloning, global
rebinding, monkeypatching, altered imported function globals or runtime source
execution is permitted. Do not import _ge_beam3_g3c_stable.shell wholesale;
that selects another fit module and expands the dependency change needlessly.

Freeze this complete mechanical caller graph:

1. AffineQ4PhysicalRecovery.evaluate -> new private chart.deformation.
2. chart.deformation -> original _ge_beam3_variational_shell.rotation_jets
   -> original Davenport eigenspace differentiation and unchanged Jet2.
   Bind the original fit source SHA-256
   b0db7a83633f4a835c06e940a6f0de36ab958f7e816c37a23c6ebc16259a2a60;
   no _ge_beam3_g3c_stable.fit substitution is allowed.
3. chart.deformation -> accepted private so3_exp/so3_log -> their stable
   coefficients -> unchanged Jet2/unary/arithmetic/matrix/sin/sqrt helpers.
4. chart.deformation -> original pure owned/array/rotations/Kinematics helpers
   only; it must not call original local_shell.deformation or original Exp/Log.
5. facade._spatial_connection -> new chart._exp_terms -> the same accepted
   private so3_exp and unchanged analytic extraction of J_left and dJ_left.
   Retain P^-T g and P^-T(H-Cconnection); no symmetrization is introduced.
6. Registry construction/pose/common_motion/rebase -> original registered
   _ge_beam3_pose_joint._exp_terms remains UNCHANGED, preserving exact recipe
   arithmetic and already pinned130 observed-state hashes. Registry generation
   does not supply the production chart derivatives. Do not regenerate state
   values with the new evaluator merely to improve comparisons.
7. Source family construction, unchanged qualified Q4 finite response,
   original35 stationary assembly, M/n/C physical reconstruction, full64 Schur,
   material/numerical separation, tensors and all output equations remain as
   bound by the numerical contract. No public source imports are redirected.

The private chart may import the old arithmetic module for Jet2 and elementary
operations, but no reachable mechanical call may use its old Exp/Log factor
functions. Merely scanning module names is insufficient: verify actual function
bindings for both deformation and spatial-connection paths. The original
matrix helpers import unchanged classes; do not create another Jet2 identity.

Add chart_numerics_id to the complete canonical facade descriptor. Its exact
expected value is GE_BEAM3_Q4_AFFINE_STABLE_CHART_NUMERICS_V1. Full authority
reconstruction rejects missing/old/wrong IDs before family work, even after
resealing. Prepared data continues binding the full definition SHA, so an old
cache cannot be associated with a new chart definition. Preserve all entry,
observation, cancellation, reentry, cache and final-publication guards.
The existing outer facade policy may remain as the physical-facade family
identifier only in conjunction with this mandatory new exact numerical ID;
V1 descriptor bytes without it are never interpreted as the successor.
This is an explicit new canonical definition identity, not silent reuse of
an old numerical definition. No restart integration is added at this gate.

Only the new chart, private facade import/descriptor plumbing, corresponding
private test/source-authority bindings, this addendum and the single completion
register may change for this numerical correction. Shared runner/test-only
coupling fixes are separately enumerated at the coordinated freeze. Public
source, existing kernel/chart files, registry arithmetic, original contract,
historical evidence and independent checker mechanics stay unchanged.

## Confirmation and unchanged adjudication

Retain the same15 named full numerical nodes, separate two-node smoke, all130
pinned observed-state identities, tables, poses, scales, D4/director variants,
graph references, tolerances and comparison semantics. Add source/provenance
regressions within the existing inventory: exact private evaluator bindings;
rejection of old/missing/resealed chart IDs and old-cache association; prohibition
of old Exp/Log entrypoints during a genuine private evaluation; preservation
of original fit binding and registry bytes. These are real interception and
authority checks, not asserted summary flags. No numerical case is removed.

Regenerate the source-bound manifest for the successor source graph while
requiring the registered input-state hashes to remain identical. Independently
review the frozen implementation before a fresh smoke and full rehearsal.
Only a complete passing rehearsal permits two formal cycles. The frozen
600-second/24GiB/one-thread child,120-second inactivity, max3 concurrency and
1800-second wave limits, exclusive outputs and no automatic retry remain.

Terminal precedence and scope are unchanged: BLOCKED process/evidence,
NO_GO variational/state only with a complete independently verified typed
contradiction, then PROVISIONAL_GO affine-local physical recovery only. An
unexpected assertion is not a typed scientific contradiction. Full G3c,
general geometry/material parity, G4/G5, public routing, defaults and releases
remain outside this correction. Source-authority acceptance is not execution
acceptance or qualification.
