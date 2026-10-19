# Parent review criteria (prospective)

- Nonlinear equilibrium uses actual accepted internal/contact force minus external
  force, not tangent-times-displacement. Linear Ku-F diagnostic helper may only
  be used for its documented linear/local manufactured wrench identity.
- Tangent reduction parity alone shares the same element kernel; the independent
  residual central-difference check is required. Never finite-difference a buffer
  that is aliased and overwritten before the difference is formed.
- Fixed T kinematics only supports reference-map wrench/work identities. Do not
  impose finite deformed-coordinate moment objectivity or claim rotating offsets.
- At least one mixed variation must activate nonzero eccentric lever terms and
  genuinely nontrivial interpolated weights. Shared positive control has no MPC.
- End-to-end recontact must inspect results/snapshots through the actual solver,
  not only repeated evaluations of the contact manager.
- Rejected-trial/cancellation checks must observe last accepted data or persisted
  state; fresh-solve parity alone does not prove rollback. No checkpoint mutation
  by unverified callbacks and no artificially accepted failed trial.
- Changed weight/offset restart test must remain a valid model and fail specifically
  on identity before iteration, not an unrelated invalid-model or setup exception.
- Smooth derivative probes remain strictly on the same active branch; opening/
  closing assertions use correct one-sided/nonsmooth behavior separately.
- Existing finite-MPC refusal is retained. Static source review is evidence only
  for unchanged guard, not an executed refusal test; final report must say which.
