# Slice 3 implementation checkpoint

Written by the Mistral implementation owner. Living checkpoint; updated as
work proceeds. Policy ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 rev
2026-09-24.2. Current assignment: SLICE3_UNBLOCK_DELIVERY.md (same owner,
MaxTurns80, checkpoint by turn12, handoff by turn60, final15 reserved).

## Status: unblock-and-deliver run — CLOSED, FINAL HANDOFF SAVED

Budget: 1486.0224586999684 s used of 3600 s; 900 s final reserve untouched.
THIS assignment permits at most 450 ADDITIONAL process-wall seconds of
product numerical checks through harness.py (shared ledger, not renewed
authority; no --allow-reserve). Per diagnostic 120 s; pytest regression up
to 600 s only if remaining assignment and task allowance permit. One
numerical child at a time. No mesh/arc/final25 runs. No Git mutations,
siblings or workers. 0 additional seconds spent so far this assignment.

### Findings so far (this run)

1. DC1 and DC2 are FIXED in src/anysolver/nonlinear_static.py (syntax-
   verified by ast.parse; not yet numerically verified):
   - DC1: the subdivision retry now requires a strictly positive finite
     attempted span (np.isfinite, > 0.0), keeps the geometric min-span
     floor, and adds an explicit per-interval cutback-count bound
     (cutbacks_this_step < max_control_cutbacks). A zero-span request runs
     its bounded Newton attempt and exits through the finite
     minimum_control_step_reached/stopped_at_limit path.
   - DC2: step_iterations resets after each accepted publication when a
     subdivided interval continues, so per-record iteration counts describe
     only their own accepted increment; solve-wide totals remain in
     total_iterations and the cumulative control_attempts/control_cutbacks
     fields.
2. Recorded evidence slice3-continuation-achievable-1 (junit.xml, no new
   numerical cost) is already discriminating for item 3:
   - half[direct] at -0.10 PASSES the complete oracle including the physical
     support-vs-applied wrench balance at 1e-6 relative (applied scale
     61917 N/Nm).
   - half[interp] at -0.10 fails ONLY the wrench balance:
     12.876526860967095 vs 1e-6*61917.19850912096 (2.08e-4 relative), while
     its independently reconstructed reduced residual passed the 1e-7 gate
     and the solve completed at the target.
   The identical transfer/recovery machinery passes for direct and fails
   only for interp, whose sole kinematic difference is the weighted
   rotation-vector average theta_bar = sum w_i theta_i across two masters
   with distinct finite rotations. This is consistent with cause (a)
   (non-covariance of the linearly averaged rotation vector) and weighs
   against cause (b) (a constituent work-map/recovery defect), which would
   affect direct equally.

### Rigid-spin objectivity derivation (item 3, before any mechanics change)

Contract adopted by Astra: under a superposed rigid rotation Q the weighted
deformed attachment point and the slave orientation must transform as

  x_b(u^Q) = Q x_b(u),   R_b(u^Q) = Q R_b(u),

with the existing linearized weights and the exact direct/identical-rotation
limit retained.

Current map (corotational.NonlinearRotatingMPCMap):

  x_b = sum_i w_i x_i + (R(theta_bar) - I) r_0,  theta_b = theta_bar,
  theta_bar = sum_i w_i theta_i  (linear average of rotation vectors).

Under a superposed spin Q (rotation vector psi), master states transform
equivariantly: x_i -> Q x_i, R(theta_i) -> Q R(theta_i), i.e.
theta_i -> log(Q exp(theta_i^)), which is NOT theta_i + psi unless all
rotations share the axis of Q. Therefore

  R(theta_bar(u^Q)) = R(sum_i w_i log(Q exp(theta_i^)))
                != Q R(sum_i w_i theta_i)   in general,

because exp(sum w_i log(Q R_i)) != Q exp(sum w_i log R_i): the log map is
only affine on commuting rotations. The translation part sum w_i x_i is
equivariant (translations are linear), so the attachment point x_b fails
equivariance only through the (R(theta_bar)-I) r_0 term, and the
orientation theta_b fails directly. For a single master (direct, w=1)
theta_bar = theta_1 and R(theta_b(u^Q)) = Q R(theta_1) exactly: the map IS
equivariant, matching the recorded direct pass. For interp with distinct
master rotations the failure is O(|psi| x master-rotation contrast x lever
arm); the reduced residual J^T(imbalance) can still be driven to 1e-7 (the
constraint holds in the reduced metric) while the transferred physical
wrench retains a non-objective residual moment (12.8765 Nm at 61917 scale)
that cannot cancel the applied wrench at 1e-6.

Discriminating check to implement (cheap, no FE solve): a global rigid-spin
equivariance probe of the map itself. Construct a master state with distinct
finite master rotations, superpose Q = exp(psi) with generic psi, and
measure e_pos = ||x_b(u^Q) - Q x_b(u)|| and
e_rot = ||log(R_b(u^Q)^T Q R_b(u))||. Direct: machine precision. Interp:
significantly nonzero, growing with |psi| and master-rotation contrast.
Plus a virtual-work covariance probe: the transferred master wrench of the
spun state must equal the Q-transform of the original transferred wrench;
the non-objective average violates this for interp only. This converts the
circumstantial direct-vs-interp evidence into direct kinematic
discrimination before any mechanics change.

### Candidate design: objective SO(3) mean (proposal for Astra review)

If the probe confirms cause (a), replace the non-objective average on the
ACTIVE rotating-offset route only (legacy/linearized relations unchanged)
with an intrinsic weighted SO(3) mean:

  R_bar = argmin_R sum_i w_i ||log(R^T R_i)||^2,

by the standard barycentric fixed-point iteration in the mean's tangent
space, with theta_bar := log(R_bar). Connected treatment required by the
map's other members:

- apply_kinematics/to_linear_displacement: offset (R_bar - I) r_0 and
  slave orientation theta_b = log(R_bar); the inverse restart map uses the
  same mean.
- jacobian: du_b/dq gains dR_bar/dtheta_i through the mean's tangent
  weights W_i, composed with the existing lever-arm Jacobian A(theta_bar);
  the slave rotation rows gain sum_i W_i dtheta_i/dq.
- reduce_force: master rotation covectors receive the transpose of the
  mean's tangent block applied to the slave moment covector (in addition
  to the existing delta_A^T f_b term).
- geometric_tangent: rotating_mpc_geometric_hessian at theta_bar = log
  R_bar plus the mean-curvature hessian term.
- transfer_slave_imbalance_to_masters: distribute the slave moment through
  the mean's tangent weights (not the linear w_i) so the physical wrench
  oracle stays the transpose of the actual kinematics.
- Limits: exact for a single master (reduces to direct), exact for
  identical master rotations, consistent with the linearized weights to
  first order (small-rotation/public linearized relation unchanged).
  Constraint postchecks, inverse restart mapping and downstream nonlinear
  rotation dependency refusals must be re-admitted against the new map.

This is candidate design within the adopted objective; Astra reviews
scientific applicability before adoption. No mechanics change is made in
this run without that review; the probe only demonstrates the defect.

### Intended remaining edits (this run)

1. DC bounded residual line search on the adaptive rotating-MPC route only
   (trial evaluations replace the pending state candidate and are never
   committed; committed histories retained; bounded 8 halvings; fall back
   to the full Newton step when no reduction improves the merit).
2. Ordinary-resume lambda recovery as a Newton guess inside
   _solve_static_displacement_control (least-squares scalar from the copied
   initial state, rotating route, ordinary supplied initial-state route
   only; no public API/success-criterion change).
3. D1 declared-class spy regression (monkeypatched factorize recording
   MatrixClass and delegating unchanged; independent of optional PARDISO).
4. Bounded zero-span restart regression (EP fixture, restart at the current
   controlled value, max_iterations=1: must terminate with a finite failure
   status, not retry forever).
5. T2/T3/T4 acceptance-gap closures in the continuation module
   (every-snapshot reconstruction at achieved lambda with
   max(norm(J^T lam F),1) normalization, full GP/fiber history comparison
   at split/milestones/final, named deep copies observed on
   rejection/cancellation, milestone-based comparison, no empty conditional
   passes).
6. Rigid-spin equivariance probe as a diagnostic script + recorded run.

### Actual artifacts at assignment start (from evidence, not plans)

- 31 charged attempts in budget.json; latest was
  slice3-continuation-achievable-1 (EXIT_1, 39.234439099993324 s,
  cumulative 1486.0224586999684 s).
- tests/test_nonlinear_beam_shell_slice3.py: 16 passes
  (slice3-repairs-5) on the then-current source. Do not rerun unchanged
  source16.
- EP continuation module: 7 failed / 4 passed open (full/half interp wrench,
  full/resume stalls; see junit evidence).
- DC status: direct postyield stops uz=-0.18333333333333335
  (lambda2.66796710849, 14 accepts/26 attempts/11 cuts, min-step stop);
  interp stops uz=-0.1135417. No fold/collapse claim: unscaled augmented
  condition numbers are not evidence (dimensional scaling adjudication).
- Augmented factorization already declares MatrixClass.GENERAL (D1 present
  in product, spy regression missing). Harness v2 with active-phase
  accounting; Astra owns timeout admission (max120 diagnostic / max600
  pytest enforced before launch).

## Completed in prior runs (evidence retained; do not repeat)

- Baseline 22 + 39 passes; seven-case plastic attribution (partial-load
  plateau decided valid); clean-HEAD VK attribution; pre-yield controls;
  serialized Q4 checkpoint limitation documented (pre-existing).
- Harness v2; ep_attribution.py prose; R1 corotational guard; R3 n_red==0
  selector (corrected per supervisor recheck); R4 work_conjugate auto; R5
  full_u(q) DC admission; tests/test_nonlinear_beam_shell_slice3.py (16 pass).
- EP continuation module exists with corrected reaction oracle (T1 sound);
  T2/T3/T4 acceptance gaps open.

## Reserved decisions (for Astra)

- Rigid-spin equivariance contract adopted by Astra; SO(3) mean
  applicability on the new active rotating-offset route is candidate
  design, reviewed by Astra.
- No physics, tolerance, success-criterion or public-contract changes made.

## Final status - assignment closed, handoff saved

Budget: 1876.2980378000066 s of the absolute 1936.0224587 s ceiling
(product_execution_ceiling.json); 59.72442089999345 s unspent, not renewed or
transferred. 46 charged attempts in budget.json. No mesh/arc/final25, no
baseline reruns, no load sweeps, no serialized checkpoint probes, no Git
mutations, no workers.

### Delivered and verified this run

1. nonlinear_performance.py wrapper: _solve_static_displacement_control_block
   accepts recover_initial_load_factor (default False), includes it in
   checkpoint_path and forwards it at both delegation sites. The parent's
   integration TypeError is closed; exercised by passing restart coverage
   (slice3-so3-split-restart-1).
2. Objective intrinsic SO(3) mean on the active rotating-offset multi-master
   route (corotational.py): _so3_weighted_mean Karcher fixed-point with
   stagnation accept, exact single-master and identical-rotation
   short-circuits, refusal guards (negative weights, partition of unity,
   non-convergence, chart boundary |psi|>=pi(1-1e-6), singular B). Connected
   map: forward u_b = sum w u_i + (R_m-I)r_0 - theta_lin x r_0, theta_b =
   theta_m; two-pass order-independent corrections; jacobian C_u = A M +
   skew(r_0) theta_proj, C_theta = M - theta_proj with M = sum G_i P_i
   (master_theta_projs); per-master reduce_force covectors
   G_i^T v + w_i(skew(r_0)^T f_b - m_b), v = A^T f_b + m_b; geometric
   tangent = symmetrized central FD (h=1e-6) of that exact covector;
   transfer w_i f_b + G_i^T(m_b + A^T f_b); inverse/restart, postcheck,
   downstream multi-master slave-rotation guard, negative-weight build
   refusal. Direct/zero-offset legacy bit-identical (reduced-tangent FD
   eccentric case passes unchanged).
3. Tests: tests/test_nonlinear_beam_shell_coupling.py (14 test functions; 7
   new objectivity tests including the supervisor_objectivity_review.md
   moment-defect discriminator: old-map Delta_M confirmed nonzero, new map
   equivariant; FD of J/reduce_force/geometric tangent with nonzero m_b;
   downstream rotation guard; negative-weight build refusal). FD step eps_j
   1e-7 -> 2e-6 in the reduced-tangent test only (mean fixed-point noise
   ~7e-10 vs atol 1e-10; not a tolerance weakening).
   tests/test_nonlinear_beam_shell_slice3_continuation.py: per-snapshot
   wrench balance extended from direct-only to both routes.

### Checks actually run (charged; evidence/<name>/)

- slice3-so3-mean-objectivity-3 EXIT 3.87 s: 7/7 new objectivity tests PASS.
- slice3-so3-reduced-tangent-interp-2 EXIT 7.22 s: reduced-tangent FD both
  routes PASS.
- slice3-so3-ep-half-1 EXIT 26.77 s: EP half direct+interp at -0.10 PASS
  including final wrench balance.
- slice3-so3-ep-half-persnap-1 EXIT 27.16 s: per-snapshot 1e-6 physical
  wrench balance both routes PASS. The adopted objective's discriminating
  acceptance is CLOSED (old failure 12.8765269 vs 1e-6 at 61917 N/Nm scale).
- slice3-so3-split-restart-1 EXIT 17.39 s: split restart both routes PASS.
- slice3-so3-slice3-module-1 EXIT 42.05 s: tests/test_nonlinear_beam_shell_
  slice3.py 17/17 PASS on the new map (includes the D1 declared-class spy
  test test_d1_displacement_control_augmented_factorization_declared_general).
- slice3-so3-coupling-module-1 TIMEOUT 240.28 s (charged): tests 1-10
  passed; test 11 force-interpolated finite-rotation case did not finish
  within its fixture budget (8 steps / 25 iters at -3.2e5 N, >30 deg).

### Failures / open items

- force-interpolated finite-rotation case (coupling module test 11) does
  not finish under the new correct kinematics; displacement-eccentric and
  displacement-interpolated finite-rotation cases never reached. Needs the
  intended bounded DC/force residual line search (never implemented) or
  fixture retuning, with fresh allowance.
- Full/resume EP targets still stall: direct -.1833333, interp -.1135417
  against -.20 (globalization unchanged; no fold/collapse claim from
  unscaled SVD).
- Zero-span regression (tests/test_nonlinear_static_armijo.py
  test_armijo_translation_only_zero_span_does_not_require_length) exists in
  source/tests but was NOT run this assignment - unverified.
- Mesh/arc/final25 untouched per brief.

### Reserved for Astra

- Scientific acceptance beyond the already-adopted rigid-spin equivariance
  contract; the open force-control fixture and any retuning; all Git
  delivery and cross-repository integration.
