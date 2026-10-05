# D6 native midpoint contract independent review — 30 September 2026

## Prospective disposition

No design blocker was identified for the stated single-element, contact-free, elastic, homogeneous-clamp development slice, conditional on the contract's nonsingular endpoint algebraic Jacobian and positive free physical mass. This is prospective equation/interface scrutiny, not a tested integrator or timestep acceptance. The worker may implement within the declared ownership, exclusions and one bounded check. Full D6 qualification, public admission and release remain open.

Reviewed contract: `D6_NATIVE_MIDPOINT_CONTRACT_20260930.md`, SHA256 `1f90e347fa4a572689a3e4ae2877b270c0be2da685805644d7c70adec27b1287`. This review read necessary existing source only and ran no numerical case, test or solver. This new review note is its only write.

## Stage and force derivative

Contract lines 15–34 consistently use endpoint translation increment and spatial left cell increment: midpoint positions are half the endpoint increment, midpoint cells are `Exp(phi/2)U0`, and endpoint cells are `Exp(phi)U0`. The prescribed stage fields `v_m=Delta r/h`, `omega_m=phi/h` and endpoint reflection `v1=2vm-v0`, `omega1=2omegam-omega0` define a Lie midpoint discretization; they do not imply exact finite-step momentum or energy conservation.

The finite owner evaluates force derivatives with spatial velocity/acceleration fixed under left configuration variations. Therefore the stated unpulled spatial-row derivative `(J_s+I_q)A+I_v V+M B`, with cell map `0.5 J_left(phi/2)`, nodal algebraic map `J_left(eta)`, velocity map `I/h` and acceleration map `2I/h^2`, follows the chain rule. The existing `spatial_jacobian` correction must be retained. A potential-Hessian symmetrization, missing gyro term, substitution of rest mass, or a chart-transposed row residual without its additional derivative would be a different algorithm. None is authorized by this contract.

Stage algebraic nodal frames and resultants are independent unknowns. The 42-coordinate ordering and physical/algebraic separation agree with the reviewed finite owner: translations9 plus cell spins6 are physical; nodal traces9 plus resultants18 are algebraic. With the six-component node1 clamp, 12 physical and 24 algebraic coordinates are free.

## Endpoint DAE and velocity meaning

Endpoint algebraic projection at fixed physical position/rotation and velocity is consistent when `C_z` is nonsingular. It defines algebraics locally as functions of physical coordinates; physical acceleration then comes from the free physical mass equation, including gyro force. It does not require static physical equilibrium, and it must not change or condense physical cell rotations to force endpoint consistency.

The contract correctly makes rank-deficient `C_z`, nonpositive physical mass and inconsistent supports fail closed. Their validity must be checked for the actual initialized/stage/endpoint states, not assumed from a converged stage or from static solvability. If a hidden physical constraint appears because `C_z` is singular, endpoint-only algebraic lagging or arbitrary stabilization cannot substitute for the separately required DAE/velocity-consistency design.

Implementation clarification: the nine zero nodal-frame entries in the finite owner's 24-velocity vector are inertial placeholders. They do not assert that the algebraically solved nodal frames have zero time derivative. Their path is determined by `C=0`; only translations and cell spins are kinetic variables. The exact single centered generalized-element/42-coordinate fixture must be admitted before using the one-element indexing; the existing broader `NativeBeamAnalysis` type alone is not that restriction.

## State, material and transaction ownership

The existing static `Context.make/histories/assemble/guard` can validate and evaluate the full mechanical/material state, with its original 120-second lifetime. Its `record/stage` impose static physical equilibrium and cannot issue dynamic states; `advance` is a Newton retraction. The new owner must issue and validate its own accepted/candidate state, using accepted immutable material origins throughout and rejecting non-ELASTIC responses, changed histories or nonzero dissipation. No private constitutive override or renewed static Context may bypass those limits.

State identity includes complete high/low coordinates, frames, resultants, origins, physical velocity, time, epoch/predecessor and native definition/support/inertia/load identities. Candidates must be issued by the exact context and tied to its current accepted predecessor. Publication should use the native analysis operation lock or an equivalent owned atomic boundary, rechecking identities and cancellation before a single accepted-state update. A stale competing candidate, mutation, foreign state, failed solve, exception or discarded candidate must leave accepted canonical bytes unchanged. Initialization likewise must reject nonzero constrained physical velocity and inconsistent mechanical supports.

The contract's full dynamic stage/endpoint checks, correction gates and rollback obligations cover the right acceptance boundaries. An implementation must apply its 1e-11 scaled gates to the full dynamic residual, not reuse static residual norms that omit inertia. Full fixed-support reaction couples must be retained in the instantaneous momentum balance. The original public rest/modal and static codec guards remain outside this new owner.

## Source correspondence and remaining evidence

The retained state, structural boundary and retained operator hashes in the contract match current files and their managed-worktree counterparts. The cited native restart-boundary hash belongs to `_ge_beam3_native_generalized_restart.py`. The reviewed finite owner remains SHA256 `3334699c5a4c14ef67cbfcef3ad54c3be8c80a15b98f2c34aa6840be70d32f84`; its local development review supplies no timestep validation.

The proposed complete-stage/endpoint directional tests, singular-mass descriptor block comparator, exact algebraic zeros, endpoint consistency, rollback and independent instantaneous momentum balance are appropriate discriminators for this first implementation. Useful perturbations and genuinely nonzero initial cell spins are required as declared. Report discrete energy/impulse defects without grading them as exact conservation or extrapolating the small-amplitude comparator to nonlinear qualification. No execution result is accepted by this prospective review.
