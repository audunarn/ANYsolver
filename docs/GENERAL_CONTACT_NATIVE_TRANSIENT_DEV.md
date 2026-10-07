# Native beam–beam common-stage contact development candidate

Status: **working development fixture; focused installed V3k projection-feature
repair checks PASS**. Broader programme qualification, independent engineering
acceptance and release remain open. Prior nonprincipal authority does not apply.

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
executed smoke fixture uses two `.003 s` steps over `.006 s`, with two moving
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
The factory explicitly opts into V14 pooled physical-gap quadrature, built on
resolved ownership/moving-boundary admission (`certify_curved_ownership=True`,
`pooled_quadrature_budget=True`). The normal potential and native pullback remain
unchanged. Results bind the exact kernel fingerprint and service
`NATIVE_RETAINED_WHOLE_Q2_PAIR_DEV_V14_POOLED_PHYSICAL_GAP_QUADRATURE`.
Error components use 30 unique physical control-point coordinates in metres
(five three-coordinate points per body), with force/tangent limits in that chart.

One exact nonrenewable quadrature ledger reserves Q <= T/2 componentwise;
boundary contributions separately satisfy B <= T/2 and aggregate E <= T.
Accepted quadrature differences or complete absolute omission bounds charge Q
exactly once. Boundary and aggregate sums use outward arithmetic and exact
prospective reserve comparisons, including sub-ulp charges. Certified owner
branches use exact constrained projection KKT and strict convexity, then the
existing envelope derivatives and a factored gap with an outward station-residual
certificate. This changes neither the normal law nor any explicit error/search/
integration cap. The V4/V13 historical default paths remain unchanged.

The new owner still requires exact straight reference and zero physical lift.
No curved native reference is admitted by these service flags. Earlier V4
ownership and V13 integration-cap failures and their private artifacts remain
preserved; this opt-in repair requires its own analytic and complete-direction
checks before a working development claim. Certified unresolved junction bands
use the existing complete half-weighted physical30 bulk plus moving-root Hessian
omission enclosure, charged once to B/E before zero approximation; no rounded
midpoint projection is required for an already enclosed band. Pooled ownership
first uses an exact endpoint/cone/strict-convexity inventory with explicit all-visited
debit; unsupported cases retain the mature ownership engine and refusals.
This service selection is explicitly bound in the kernel fingerprint. Entire
open intervals require certificates for both represented target cells: exact
Q2 Bernstein hull-box separation, or the existing exact strict-convexity distance
floor. All-inactive Gauss samples alone never admit an open interval. Each complete
native source cell uses the existing fixed material-domain inventory on [0,1];
all four source/target curves remain present. Independent complete ownership,
activation, moving-boundary and quadrature proofs replace redundant detection
tessellation. This opt-in service is explicitly fingerprinted; old scan defaults
remain unchanged.

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

## Development evidence and remaining programme work

The separately authorized `C8_NATIVE_PAIR_DEV` development run used 750 measured
seconds, at most 60 seconds and 953 MiB per process tree, one job at a time,
JIT disabled, Numba one thread and observed BLAS/OpenMP pools one thread. All
attempts, failures and timeout output remain preserved. Accounting conservatively
charges measured wrapper wall time including preflight/postprocessing and also
records exact child launch-to-wait time. No old numerical allowance was reused.

Preserved v3h baseline evidence (2026-10-07):

| Check | Outcome |
| --- | --- |
| Public two-body impact, two steps dt .003 to .006 s | PASS |
| Open-contact structural/inertia equivalence | PASS |
| Exact fresh two-step versus authentic prefix1 + resumed1 restart, tamper refusal | PASS |
| Initial penetration, incompatible config, native-capsule endpoint admission/rollback | PASS |
| Clear-endpoint through-crossing refusal | PASS |
| Contact/radius identity mutation, curved/lift admission, finite event limits | PASS |
| Bounded cutback replay, actual in-flight cancellation/receipt cleanup | PASS |
| Complete 84-coordinate arbitrary-direction tangent, eps 1e-6 and 1e-7 | **NONPASS: conservative ownership-depth refusal before derivative comparison** |
| Analytic parallel-line energy/force/stiffness, exact reserve and physical30 strip bound | PASS |
| Saved perturbation connected-junction inventory and zero/one-cell cap checks | PASS; unsupported source remains on mature fallback |
| Saved full open-span certificate, rational box oracle and near-threshold/bowed refusals | PASS |
| Six legacy work/mass/graph/controller/public-route checks | PASS |
| Matched legacy axial producer full result and checkpoint | PASS; canonical saved-result bytes and original capsule bytes identical |
| Actual public example CLI (`--steps 2 --dt .003`) | PASS |

The genuine second stage stores 1.5992802429271303e-5 J of normal contact energy.
Maximum stage equilibrium norm is 5.630560744459157e-16; maximum endpoint algebraic
norm is 4.830641798752094e-23. Both bodies respond. Final kinetic energy is
.039952025191092734 J, contact storage 4.897480890726621e-5 J, and reported total
.040001 J. Momentum, exact stage work, forces/moments and path bounds are recorded;
no exact angular-momentum or energy conservation claim follows from this fixture.

The v3h full tangent gate retained its 1e-5 criterion and both original arbitrary
perturbations, failing closed at a slightly kinked near-endpoint target union.
No expected-failure mask, uniform-only substitute, cap increase or tolerance
waiver was applied. The subsequent exact endpoint-KKT discriminator used both
signs and both original epsilons, complete quadratic endpoint/critical extrema,
positive target stationarity convexity and identical native/physical30 shared
endpoint work maps. It found a shared-vertex cone plateau or one-sided dominance,
with no genuine two-interior competition in those source3 curves.

The pooled-only v3i/v3j endpoint inventory debits all consumed root-search work
before mature fallback, including optional nonclassical/precision refusal. Tiny
root strips bound both targets' full half-weighted physical30 energy, force and
Hessian contributions and charge B/E once. The old optional connected helper,
whose failed call did not expose visited work, is not invoked by this identity.
Historical default profiles remain unchanged.

Fresh privately installed V3k evidence:

| Affected check | Outcome |
| --- | --- |
| Fixed start/end/interior feature, zero/root refusal and strict winner with its own endpoint-root counterexample | PASS |
| Exact endpoint inventory, complete root-strip bounds and work-map refusal | PASS |
| Original complete84 arbitrary-direction work/tangent, eps 1e-6 and 1e-7, unchanged1e-5 criterion | PASS |
| Actual two-step impact, both-body response, storage and certified path | PASS |
| New-identity full2 versus genuine prefix1/resumed1 restart, exact capsule/state equality and tamper refusal | PASS |

Review identified a generic V3j proof gap after its derivative/impact passes:
the fast whole-owner dominance branch could skip the winning cell's own
endpoint/interior root strips. V3k now requires exact complete BOTH winning
endpoint-KKT ranges to prove fixed start/end/interior projection feature before
that fast return. Any zero/root/uncertainty uses complete accounted endpoint
inventory or mature fallback. The new strict-dominance counterexample has a
horizontal winner whose endpoint phi crosses zero while the vertical loser's
shared-vertex KKT is strictly positive; bounded root strips or fallback are
required. No winning-root bypass, root limit increase or gate change is used.

V3k genuine impact stage/endpoint norms are 5.710376640021784e-16 and
5.518952735445791e-23. Reported endpoint energy/force/tangent error bounds in the
physical30 chart are [1.8989823203627635e-20 J,3.189871482947048e-16 N,
9.613949174130494e-13 N/m]. Certified path minima are
[-.00040000000506164356,-.0009997300658258028] m, within the explicit-.003m
penetration budget. Final kinetic .039952025191092734J, structural elastic
-7.383792047029578e-42J (roundoff) and contact4.897480890726621e-5J sum to
.040001J. These diagnostics do not imply exact energy/angular-momentum conservation.

The original V3j restart18s timeout and seven prepared records are preserved.
The later V3k selector completed setup/call/teardown, genuine resumed/full capsule
and state equality, and tamper refusal. Earlier V1/V2b/V3/V3b/V3d/V3e conservative
failures, V3f timeouts and V3i optional-root precision failure also remain intact.
The unchanged legacy/CLI/admission/cancellation rows above are historical evidence;
they were not reexecuted on V3k. The scoped repair changes only the opt-in contact
ownership/feature proof and fingerprint, preserving historical defaults/shared
controller/product contracts. It does not establish wider qualification.

Evidence root: `C:/ANYworkspaceWork/contact_native_c8_pair_20261007`.
Tested source V20 and `execution_manifest_v21.json` bind unchanged V3k product;
wheel `dist_v3k/anysolver-0.4.7-py3-none-any.whl`, SHA-256
`487af8778274b5fcf8efaf082e8d57299bdf67af1ef7ef52409000fef01cb88e`.
Kernel identity `9b64e06251e9931522de41470b63ba330d2da28eb8b40bd9f3b785a4cf60b60f`.
Both completed groups verified207 actual private module imports with zero
hash/path errors, JITdisabled, Numba1 and pools[1,1,1]. Final source/installed
comparison and all53 attempts are recorded in the author handoff.

The explicit90s extension preserves the original750s grant/history and provides
840 aggregate measuredseconds. Exact conservative wrapper charge is
739.9227660997963 seconds;100.07723390020374 seconds remain, including the held
60s reserve. All original grants/runners/manifests remain immutable. The exact-KKT oracle is test-local and requires no external raw directory in an
ordinary checkout; its two affected selectors passed after that portability repair.
No further numerical job is proposed. Guide edits after execution do not change
tested product.

Required broader rows remain open: curved native physical lift/path admission,
dedicated true endpoint/cap treatment, native friction, native/shell common-stage
coupling, shell work/restart, multibody broadphase and programme acceptance.
This two-complete-native-beam slice does not close those dependencies.
