# S3 director-pressure integration — development only

2 October 2026, based on 8acec7fc. Explicit configuration
`reference_dead_director_v2` uses a separately identified, virgin-elastic S3
reference-area dead-load surface. Historical `reference_dead` remains unchanged
and finite-rejected for S3. No element law, acceptance threshold or default was
changed. The mixed follower-pressure failure remains open.

## Delivered implementation

The pressure context owns the native reference covector and reference geometry,
binds the normal through its local mutation guard, passes physical rotation
anchors, assembles the full external Jacobian and recovers conservative work
and spatial resultants. `STIFFENED_SHELL_GE_DIRECTOR_PRESSURE_LOAD_V2_DEV`
binds descriptor/checkpoint identity. Header/request policy substitution rejects.
Q4 rejects the S3-specific option; a request mixing old S3 dead and new laws still
rejects finite execution. Mixed current/director surfaces report their mixed scope.

Independent source review found no consequential integration blocker. Its narrow
conclusion is that differing assumed internal and external interpolations can
form a consistent discrete potential when both are fully differentiated. It did
not qualify the physical surface or finite response. Internal/full-log chart and
strain-domain restrictions still apply; the external lift does not remove the
internal formulation's sensitivity to large relative drilling.

## Checks and retained failures

- Nonuniform cylindrical-bending reconstruction passes a three-size positional
  and surface/director shear convergence screen. Its first test had a transposed
  coordinate-gradient mapping; v1 is invalidated for this claim. Corrected v2
  includes an affine-gradient identity control. This is a manufactured kinematic
  screen, not an executed external solver comparison.
- Initial source batch: 20 passed, four failed. Reference parity, linear restart,
  Q4 rejection and historical context checks passed. Two assembly tests exposed
  subtraction of small external terms from ~1e10 internal stiffness; the tests
  were corrected to amplify only their algebraic factor-linearity measurement.
  The independent external derivative retains relative norm error <=1e-6.
- Owner tangent v4: both mixed/all-S3 cases pass a three-step normalized
  directional-derivative plateau through actual state updates. Earlier component
  allclose failures remain retained; no product tangent was changed to fit them.
- Guard v3: policy substitution/mixed reporting, both existing S3 finite guards
  and the existing pressure-context suite pass (20 cases).
- **Both new finite lifecycle cases remain FAILED under the current assessment.**
  Applying the existing frozen-parent trial comparison to this configuration-
  dependent load did not resolve their final component checks. No false commit.

The bounded diagnostic records mixed global ratio1.9252e-14/gap2.647e-23 and
all-S3 global1.0142e-14/gap1.323e-23, but Cartesian active-row ratios above1e-8.
Both terminate at generation zero. It records actual OpenBLAS pools at one
thread. Other runs requested one thread/JIT off with600s/1GiB limits; no limit hit.

## Decision pending

The [pressure-only assessment proposal](pressure-assessment-amendment-proposal.md)
is awaiting the user's decision because Revision8 reserves frozen assessment
changes. In a private process-only override, all three previously failing routes
complete0.1/0.2/0.3, cancellation, identical restart, rebasing and balance checks.
Those counterfactual results are **not acceptance under the current contract**.
The original failures remain open; no installed qualification or release follows.

[Raw runs and diagnostic scripts](s3-director-integration-raw-v1.zip), SHA256
`b03239947a3d383eb1022972f91a159f4bc453470d75d990910bffe095f271f7`.

Next: if approved, implement the opt-in assessment with persisted identity and
consistent solve/restore/rebase checks, then run affected installed workflows.
If declined, keep these finite pressure routes unaccepted and advance independent
programme work. Either way, matched physical pressure validation remains required.
