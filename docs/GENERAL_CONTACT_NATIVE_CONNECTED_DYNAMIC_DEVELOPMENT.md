# Connected retained native dynamics: tested development candidate

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
restore, singular mass and unrepresentable dt. Three assembled mechanics cases are now installed-tested; remaining owner-only
controls were not executed in this slice. The public shared TransientConfig
workflow is installed-tested as recorded below. Actual
clamped reaction/impulse balance, independent deforming response, finite-angle
energy/momentum/work and broader C7 acceptance remain open. Numerical passes
are confined to the recorded coverage; no release or engineering acceptance is claimed.

## Shared trajectory controller candidate

Public connected solve_transient accepts the existing TransientConfig. Initial
displacement/velocity order is physical3*N+6*E: sorted-node translations, then
element/cell spatial rotations/rates. Initial displacement uses compensated
reference increments and left SO3 multiplication; algebraic guesses/history
are never caller inputs. Only native midpoint-compatible default placeholders
are accepted; Newmark/HHT/damping/recovery/subsets/resource overrides refuse.
Applied loads/contact remain unsupported in this named connected profile.

The existing native time/cutback/cadence/cancellation/commit-prefix loop is now
a shared private transaction engine. Legacy settings/schema/results/validators
and literal step preparation remain unchanged. AST expansion of the common
loop plus legacy preparation exactly matches the original loop;17 other old
functions/classes and constants/imports have identical AST. This is source
equivalence. Two installed legacy checks also pass, and their saved full/resumed
JSON results are byte-identical to the earlier installed fixture; broader
compatibility is not inferred.

Connected candidate endpoint publication now uses the exact authenticated
issued object after complete validation; its mechanical bytes are unchanged.
Trusted prepared origin/restore closures and trial receipts stay inside native
atomic operations. Every journal/result/capsule byte prepares before commit;
authentic owner.current identity determines whether an interrupted commit
accepted the new prefix. Uncommitted receipts alone are discarded.

A distinct connected trajectory capsule binds origin/topology/settings and
retains full accepted stages/endpoints/reactions/support impulse/work/history
plus output cadence. Fresh restore cross-binds native and controller endpoints
before publication and replays complete stored stage/physical increment/rate,
accounting/support and equilibrium checks. Actual full-clamp force and fixed
frame couple use the assembled stage residual about compensated global zero;
homogeneous support work is zero. No algebraic inertia is invented.

examples/native_connected_transient_dev.py is the public workflow candidate.
New tests prepare full/split equality, physical SO3 origin, pre/post issuance
commit/cancellation/control interruptions, cutback, corrupted journal and
legacy smoke controls. Twenty-seven connected-controller and two legacy checks
now pass against the549-payload private artifact, with three assembled mechanics
checks and the actual two-step example. Independent physical energy/momentum/
clamp balance and full C7 acceptance stay open. The separate240-second connected
allowance is approved and accounted; the old loading wheel/evidence remain separate.


### Connected restart replay source repair

The connected adapter replays planned step sizes, permitted Newton reasons,
contiguous halving, cutback floors and the final next-step plan. Horizon-clipped
rows retain their plan and remain valid interior history after horizon extension.
Saved fixed midpoint coordinates must be exactly zero. Complete mechanical journal
replay, cancellation checks, native restore and publication preparation now share
one native-owned exclusive atomic lease; no nested lock or early visible origin
is introduced. Forged cadence/fixed-coordinate capsules, clipped-prefix extension
and in-replay cancellation controls now pass installed checks. Old single
adapter/schema/formula source equivalence remains recorded alongside the bounded
installed legacy comparison; neither establishes universal equivalence.


## Current execution evidence

See [the development delivery record](d1_review_support/contact_native_connected_transient_20261006/connected_shared_development.md)
for exact source/artifact identities,32 distinct passing cases, actual example,
test-only repair, retained timeout/failure, unchanged scientific scope and required
remaining mechanics evidence. Twelve jobs consumed230.89657720038667/240 seconds;
9.103422799613327 seconds remain in this connected scope. This guide's earlier
source-only chronology and prepared test docstrings are historical preparation
labels; they do not supersede the scoped execution record. No engineering
acceptance or release follows.
