# Instantaneous six-DOF rigid-body mechanics

`anysolver.marine_rigid` is an experimental public API (`marine_rigid_v1`).
It supplies dry mechanics and exact point kinematics; it does not supply a
time integrator, mechanical link, trial-history protocol or hydrodynamic
source admission. W4 qualification is pending.

`RigidBody6D` owns explicit mass [kg], body-axis CG [m] from the reference
origin, and the full body-axis inertia tensor about the CG [kg m²]. Tensor
off-diagonals are actual matrix values. Inertia is never inferred from the
hull or a potential-flow backend. This nondegenerate six-DOF API requires
positive definite rotational inertia and principal triangle inequalities;
ideal degenerate point/line bodies are refused, never regularized.

`RigidBodyState` freezes input copies. Its coordinates are `(r, theta)` with
`R = Exp(theta) @ anchor`, a fixed explicit SO(3) anchor. Velocity and
acceleration fields are chart rates, **not** spatial angular rates.
`world_velocity = B qdot`, `world_acceleration = B qddot + Bdot qdot`,
`B = diag(I, J_l(theta))`. Stable series apply below 0.02 radians.
The local principal chart refuses `||theta|| >= pi - 1e-8`; this numerical
seam guard is not a qualified physical motion envelope. A new explicit anchor
can represent arbitrary orientations, but integrator rechart/predictor/history
transport belongs to the separate `marine_mechanical_v1` route. No silent
wrapping/orthonormalization occurs in this instantaneous API.

At a pose, `c = R cg`, `Ic = R Icg R.T`,
`Io = Ic + m ((c.c) I - c c.T)`. `mass_matrix(state)` returns the world
twist matrix `[[m I, -m skew(c)], [m skew(c), Io]]`.
`gyroscopic_force` returns `[m omega×(omega×c), omega×(Io omega)]`.
`inertial_force` is the **positive internal chart covector**
`B.T @ (M @ world_acceleration + gyro)`. A residual subtracts it once.
`acceleration_tangent` is exactly `B.T @ M @ B`; `dry_tangents` also supplies
analytic position and velocity derivatives, including geometric acceleration
and gyroscopic terms. The effective Newton operator belongs to the separate
mechanical integrator. Kinetic energy is
`0.5 world_velocity.T @ M @ world_velocity`.

`point_kinematics` returns position, velocity, acceleration, the additive-chart
Jacobian and its mandatory geometric acceleration bias for any body-fixed
attachment vector. `point_force` returns the work-conjugate external `J.T f`.
`gravity_force` applies dry gravity at the current CG, separate from buoyancy
and hydrostatic restoring. Output arrays are fresh and own no committed state.

Source checks use 32 instantaneous states, an independent SciPy exponential,
Newton-Euler CG force/moment and kinetic-energy oracles, work and reference-shift
identities, actual force derivative checks, gravity-potential finite differences,
near-zero/series-boundary/seam checks and typed refusal/immutability paths.
Prospective relative tolerances: algebra/work 1e-10, finite differences 1e-8,
with 1e-12 normalization floors. These are development checks, not trajectories
or a marine scientific qualification campaign. The existing `marine_linear`
route and structural transient assembly are unchanged.

Additive fixed-state checks in `test_marine_dry_blocks.py` use an independent
block matrix exponential for pose derivatives and a Frechet exponential for
the chart rate map. Four cases cover an offset CG, the 0.02-radian series
boundary with zero CG, a rotated anchor at zero chart and an approach to the
principal seam. Three further cases set velocity, acceleration or both to zero.
Each stiffness/damping/mass derivative is assessed in four separate 3x3
force/moment by translation/rotation blocks, at 1e-8 relative tolerance with
one-unit SI derivative floors. Force, moment and energy use 1e-10 with separate
SI floors. A local five-point independent energy derivative at h=1e-3 seconds
matches covector power at 1e-10 relative tolerance with a 1 W floor. These are
algebraic states, not trajectories. Source and installed checks passed all
seven cases; the legacy checks and their normalization remain unchanged.

The narrow independent source assessment found no source defect. Its original
moment-expression paraphrase was corrected in a separate preserved report:
`Ic alpha + omega cross (Ic omega) + c cross (m aCG)` equals
`Io alpha + omega cross (Io omega) + c cross (m aOrigin)`. Pairing `Io` with
`c cross (m aCG)` would double-count the parallel-axis contribution. Full W4
scientific acceptance, integrator/history assessment and legacy regression
obligations remain separate. Evidence: ANYmarine's living TASK.md and
`C:/ANYworkspaceWork/anymarine-evidence/w4-dry-*`.
