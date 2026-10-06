# Connected retained native dynamics: source development candidate

Status: IMPLEMENTED, UNVERIFIED. No solver/numerical imports, tests, builds or
installed execution are authorized or have run. Existing native single-element
selectors, profiles, guards, codecs and equations are untouched.

The separate ge_beam3_native_connected_dynamics.create_analysis selector admits
a connected graph of explicit native generalized elastic centered straight
zero-lift definitions. It uses the existing model-owned definition factory.
Reference coordinates and algebraic frames must agree exactly at shared IDs.
Free or homogeneous full first-sorted-node clamp is the initial support scope.
Existing element limits remain; the new512 global-coordinate limit is checked
before dense derivative arrays. Construction through all idle/use has a120s
lifetime; that setting confers no execution authority.

## Complete coupled mechanics

The global order is sorted-node6 blocks, all element physical cell-spin6
blocks, then all element algebraic resultant18 blocks:6*N+24*E. Each local42
restriction P_e contains the SAME globals for a shared node. Work, spatial
Jacobian, physical inertia and all configuration/velocity derivatives assemble
as sums P_e.T*local*P_e. Nodal-frame/resultant inertia stays exactly zero;
physical translations/cell rotations are never condensed or independently
stepped. Junction frame equations sum both element couples; neither local
junction residual must independently vanish.

One global acceleration-chart midpoint Newton follows the existing native
chart: midpoint physical increment h*v+.5*h^2*a, midpoint pose half that
increment, full algebraic frame/resultant increments, SO3 left multiplication
and exact exp-map Jacobians. Complete stage K is (J+I_q)*A+I_v*V+M*B.
Endpoint algebraics are solved globally; assembled free C_z must have full
rank and physical M must be symmetric positive definite. Endpoint acceleration
solves physical equilibrium with actual gyro/configuration terms. Histories
remain captured virgin and every local material station must remain elastic.

## Ownership and persistence

initialize/trial/commit/discard/restore are one native-owned atomic operation.
Issued current states/candidates authenticate object and canonical bytes;
mutation, forgery, stale candidates, cancellation and exceptions refuse with
old publication restored. Construction clock is excluded from restart identity
and guarded separately. No candidate is a committed state or checkpoint.
The separate2MiB canonical ASCII capsule binds profile/model/maps/settings,
complete physical/algebraic state, velocities/accelerations and histories.
Restore checks bounded nesting, duplicate keys, complete schema/digest, actual
saved-state rank/mass/finite conditions and physical/algebraic equilibrium
before publication; it does not reinitialize or replace saved acceleration.
Aggregate and stage arithmetic must remain finite; unrepresentable dt/time
increments refuse atomically. Diagnostics use existing kernels, not independent
reference evidence or scientific truth authenticated merely by a digest.

## Prepared integration evidence and remaining gates

examples/native_connected_dynamic_dev.py advances two elements sharing node30
in one owner. Prepared tests cover map/shared mass and rigid reference, complete
shared-work/tangent, discard/fresh restart, mutation/cancellation, corrupt
restore, singular mass and unrepresentable dt. They are all UNEXECUTED.
The example is a bounded owner workflow; shared TransientConfig trajectory
controller integration remains a subsequent connected requirement, using the
existing infrastructure rather than a second continuation stack. Actual
clamped reaction/impulse balance, independent deforming response, finite-angle
energy/momentum/work, installed execution and broader C7 acceptance remain
open. No numerical pass, release or engineering acceptance is claimed.
