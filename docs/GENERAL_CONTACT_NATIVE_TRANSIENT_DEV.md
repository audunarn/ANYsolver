# Native beam–beam common-stage contact development candidate

Status: **implemented source candidate; numerical execution prohibited and
unverified**. This additive profile has no engineering acceptance or release
claim. Prior nonprincipal execution authority does not apply here.

## Public workflow and admission

`anysolver.general_contact.create_native_transient_pair_analysis` requires the
exact selector `ge_beam3_native_whole_round_pair_transient_dev`. Supply two ordered
immutable native beam definitions and an empty boundary tuple. Both bodies are
free, separate complete three-node/two-physical-cell native beams. The exact
centered elastic resultant section, positive diagonal centered physical inertia,
straight reference and zero physical half-cell lift are required. There is no
generic node-count inference, shared material node, fixed target or child
integrator. Maximum retained coordinates and owner lifetime remain 512 and 120s.

`solve_native_transient_pair(owner, TransientConfig(...))` uses the existing
native controller. Physical initial vectors contain sorted-node translations
followed by both physical cell spins for each element: 30 physical coordinates
for this pair, within the complete uncondensed 84-coordinate owner. No nodal
frame or resultant inertia/rate is added. Loads, damping and incompatible time
integration controls retain existing explicit refusal.

The new example prospectively selects the existing optional
`GE_BEAM3_CENTERED_STABLE_SO3_AND_PRECISE_WORK_DEV_V1` definition arithmetic
policy to retain small-deformation work precision. The factory preserves the
definition's supported policy; no legacy arithmetic default is changed. The
unexecuted smoke fixture uses two `.003 s` steps over `.006 s`, with two moving
bodies and an actual active second stage. This is development verification,
not temporal-convergence or impact acceptance.

Required factory controls include each radius [m], line penalty stiffness
[N/m²], distance/feature tolerances [m], energy [J], force [N], tangent [N/m],
dimensionless material search tolerance, finite search/integration limits,
maximum penetration [m] and maximum swept intervals (1–4096). Maximum penetration
must exceed distance tolerance and remain strictly below the radius sum.
Newton/backtracking/inertia controls reuse the existing bounded native choices.

Endpoint policy must be `CLOSED_CENTRELINE_DISTANCE_LINE_MEASURE`: symmetric
distributed line penalty uses nearest points on the closed physical centrelines,
including endpoints. It adds no cap-area force and establishes no dedicated
endpoint-force accuracy or admission. The static whole-curve pair service covers
both retained physical cells on each side and retains its geometry/error refusals.

The analysis profile is `NATIVE_B3_GE_WHOLE_ROUND_PAIR_MIDPOINT_DEV_V1`; native
state and trajectory schemas are separately bound V1 identities. Radius,
stiffness, endpoint policy, all contact/search/event controls, exact definitions,
physical curve routing and shared mechanics settings enter the owner identity.

## One complete midpoint equilibrium and work map

The connected midpoint implementation is a private shared retained assembly.
The exact legacy `ConnectedDynamicAnalysis` still requires its connected graph
and retains its historical profile, definition, journal and capsule fields. Its
public exact-type guard does not admit the contact owner. The new owner has an
explicit disjoint two-body admission; there is one global Newton system.

For each native body, complete structural residual and spatial tangent are
assembled with centered finite inertia. The pair kernel returns conservative
contact gradient `r_c` and chart Hessian `H_c` in all 84 native coordinates.
Each own-body 42×42 block is converted with `spatial_jacobian(r_c, H_c)`;
off-diagonal 42×42 blocks remain present. Both native Boolean component maps
assemble these contributions into the global structural residual/tangent.
No element or body is condensed before contact.

The shared stage evaluates

`R(u) = r_structural(q_stage) + r_contact(q_stage) + f_inertia(q_stage,v_stage,a)`

and

`dR/du = (K_structural + K_contact + Dq_inertia) C_stage + Dv_inertia V + M A`.

For physical coordinates, endpoint increment is `d = dt*v0 + dt²*a/2`, stage
positions use `d/2`, cell frames use `Exp(d_cell/2) U0`, stage velocity is
`v0+dt*a/2`, and acceleration is `a`. Existing massless nodal-frame/resultant
stage coordinates and their full chart are preserved; contact physical curves
depend on node translations and physical cell rotations through
`NativeRetainedCurveCell`. Every contact derivative goes through `C_stage` before
the complete equilibrium solve. No hidden trace mass, damping or restitution
appears. Endpoint algebraic equilibrium and physical acceleration are recovered
by the same shared services after the physical midpoint update.

## Actual path, activation and refusal

The declared physical path is `x(s)=x0+s*d_x`,
`U(s)=Exp(s*d_cell) U0`, `0<=s<=1`. It is the stage configuration chart, not
constant-acceleration/Hermite interpolation. Nodal positions retain high/low
parts. Since exact admitted reference lift is zero, internal cell rotations do
not move the physical contact curve; every half-cell material point is an
affine convex combination of its moving endpoint nodes. Curved references and
nonzero internal lift are refused until a rotation/lift path enclosure is added.

For every temporal interval `[a,b]`, the complete physical distance infimum is
Lipschitz with speed bound `V=max_node |d_A|_1+max_node |d_B|_1`. Conservative
whole-curve endpoint geometry lowers give the bound

`g(s) >= min(g(a),g(b)) - (b-a)*V/2 - 2*uniform_curve_range_error`.

Exact rational scalar arithmetic encloses speed and subtraction. A uniform
IEEE range envelope bounds product and compensated high/low interpolation:
per coordinate `8*eps*(|high|+|low|+|increment|)+12*minimum_subnormal`.
Physical curve control-point sums also round. Adding their bound and a factor
2 enclosure of the Q2 shape absolute sum (which is at most 5/4) gives the
complete-curve range envelope `24*eps*(|high|+|low|+|increment|)+32*minimum_subnormal`
per coordinate. The maximum nodal L1 envelope on each body bounds its whole
zero-lift curve; geometry search encloses the supplied rounded physical curve.
The first uniform envelope maps rounded endpoint samples to the exact affine
binary64-input curve family. The second maps each exact interior curve back to
the rounded `_advance`/retained-cell family. Thus the certificate covers both
the exact declared affine path and every actual rounded evaluated physical curve,
with both roles and their combined range error recorded explicitly.
Reported lower/error values are directed outward. Large coordinate ranges can
therefore exhaust this proof and refuse rather than silently lose clearance.

Intervals failing the lower test are bisected within the explicit finite limit.
Accepted paths satisfy `g>=-maximum_penetration`; since this budget is below the
radius sum, the proof prohibits passing through coincident centrelines. Initial
negative/unresolved gap refuses. A bounded negative gap activates penalty contact
without a zero-gap stall. Unresolved swept paths emit the explicit retryable
`native contact swept path unresolved`, causing the existing bounded dt-halving
controller to retry. Invalid contact geometry/material/resource failures fail
closed. No endpoint sample or sampled minimum alone certifies acceptance.

## Transactions, results and restart

Native receipts, stages, complete residual/tangent, histories and endpoints use
the same authentic object inventory and atomic lease. Path proof and all result
bytes prepare before commit. Failure/cancellation preserves the last published
prefix and clears disposable candidates. Publication after an interrupted
completed commit follows the existing controller semantics.

Genuine stage/endpoint records include structural `elastic_energy`,
`kinetic_energy`, separate `contact_regularization_storage`, their total,
momenta, pair forces/moments, conservative and sampled gaps, and contact error
and resource diagnostics.
The reported pair forces are physical forces on the bodies, the negative
physical potential gradients. Pair moments use `moment_origin_m=(0,0,0)` in
global metres and sum `position × physical_force`. The assembled native contact
residual is the internal positive potential gradient in equilibrium; its stage
work diagnostic has that internal-force sign.

Each accepted step records its conservative path
certificate and stage spatial internal-contact force dotted with the declared
endpoint chart increment. This work diagnostic is not an exact storage change.
No exact angular-momentum or energy conservation is claimed for this SO(3)
midpoint/penalty method.

Restart uses trusted external SHA-256 plus canonical bounded capsules/journals.
Direct native-capsule restoration separately checks the complete endpoint gap
against the penetration budget before any restored state can be issued.
The complete initial state, each predecessor, actual midpoint unknown, physical
endpoint, velocity, structural/contact accounting, residual evidence, path
certificate and contact work are reconstructed and checked before publication.
There is no custom restart callback or external stage oracle. Altered contact
settings require a new identity and cannot resume this journal.

## Prospective focused checks and remaining programme work

`tests/test_general_contact_native_transient_pair.py` covers the real stage
directional derivative and both-body cross blocks; algebraic zero mass; open
contact structural equivalence; moving two-body impact; storage/forces/moments;
actual path certificates; exact prefix restart; journal tampering; initial
penetration/config refusal; clear-endpoint through-crossing; bounded event
failure; cutback replay and cancellation cleanup. These tests have **not run**.
`examples/general_contact_native_pair_impact_dev.py` is the public CLI candidate.

Proposed execution order after separate lead authorization: installed-artifact
provenance/build as required; legacy connected selectors/guard/identity and
native no-contact regressions; common-stage tangent/open case; impact/restart/
refusal/transaction tests; public CLI. Use one bounded process at a time with
effective JIT/thread/memory settings, exact inputs, full failure logs and precise
process-wall accounting. Preserve failures and scientific criteria. Numerical
caps and total allowance require a prospective decision; no historical allowance
is reused and no numerical result is asserted here.

Required broader rows remain open: curved native physical lift/path admission,
dedicated true endpoint/cap treatment, native friction, native/shell common-stage
coupling, shell work/restart, multibody broadphase and programme acceptance.
This two-complete-native-beam slice does not close those dependencies.
