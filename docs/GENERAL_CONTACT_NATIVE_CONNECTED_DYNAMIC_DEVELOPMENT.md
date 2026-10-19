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

## Prospective independent connected physical balance candidate — 18 October 2026

Status: **implemented source candidate; numerical and installed assessment
UNRUN**. The current source assignment is `D6_CONNECTED_PHYSICAL_BALANCE_V1`.
All historical attempts, including the single-element one-mode V2 energy
failure and its finer-step/amplitude variants, remain unchanged and unclosed by
this different connected assessment. The historical 9.103422799613327-second
balance above is CLOSED and cannot fund any new check.

`examples/native_connected_balance_reference.py` derives a separate bounded
reference for the existing two straight elements, five shared nodes, identity
reference triads, diagonal elastic tensor `(1e5,3e4,3e4,30,20,10)` and section
inertia `(2,2,2,.02,.01,.01)`. It reads raw physical inputs and accepted public
state records, never the owner's station cache, material response or reported
energy as its reference. Exact polynomial integration of each straight
halfcell gives kinetic energy, physical linear momentum and angular momentum
about global zero. The complementary elastic energy is independently integrated
from constant cell force and linear section moment. Reported mixed variational
energy is compared to `Pi=p.k-Psi`, while **stored** elastic `Psi` enters the
physical energy balance. `Pi-Psi` and independent resultant compatibility/work
witnesses remain separate evidence; off-constraint states are not conflated.

The fixed new case has nonuniform translational velocity
`(.01,.02+.03*x*x,.01)` and four spatial cell spins
`(1.5,.4,-.3),(1.8,-.2,.5),(1.2,.3,-.4),(1.6,-.4,.2)`.
The clamp case zeros only the root translational velocity. Neither amplitude
nor solver settings are tuned. Four coarse steps of `.00025` and eight fine
steps of `.000125` have the **same .001-second horizon**. A fresh-owner prefix
of two coarse steps and resumed full trajectory must reproduce every result
and checkpoint byte exactly. Public trajectory supports, corruption,
cancellation, atomic prefix and unsupported load/contact/time-method guards
remain the existing ones.

The independent clamp reaction includes the root consistent translational
inertia, actual elastic cell force and constrained nodal-frame couple obtained
from SO(3) log virtual work. Its global moment includes the root orbital arm;
there is no fictitious algebraic frame inertia. Homogeneous support work is
zero. Physical momentum change is checked against these independent stage
impulses, separately from parity with reported support records.

New prospective development predicates are parity `1e-10` and per-step plus
cumulative physical energy/linear/angular balance `1e-6`, pending final root
scientific adoption. The fixed analytic initial energy is `E*=.05230416666666667J` (free) or
`.0516J` (clamped), with actual public initial rates/energy/momenta verified; `M*=4kg`, `L*=2m`, `P*=sqrt(2M*E*)`, `H*=L*P*`. No near-zero floors are
introduced. Refinement reports common-time trends without inventing a ratio
gate. Existing `1e-5` directional tangents, `1e-11` rigid translation, exact
restart and all stricter original assertions are untouched. These new cases do
not qualify all C7 sections/spatial domains, close the historical single-element
gates, admit loads/contact or establish C8 impact.

The explicit public candidate is
`python -m examples.native_connected_transient_dev --balance-output <new-dir>`
and the same command with `--clamped`. Each writes completed raw trajectory and
checkpoint before independent predicates; `ASSESSMENT.json` identifies scoped
development evidence only. The installed assessment must bind the current
artifact and helper sources, authenticate actual imports, and prohibit a source
package fallback. No installed artifact has been built or executed under this
source-only assignment. All C0–C9/D0–D8, current CI and different-family final
acceptance obligations remain required.
