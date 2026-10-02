# B3-GE / E4-PL / B2 current acceptance matrix

**Current arc lifecycle status (supersedes historical open-public-surface notes below):**
Public solver and installed ANYfem Project/checkpoint continuation are
IMPLEMENTED_NOT_QUALIFIED. Capacity/E04 remains open; no executed mixed first-limit-point
reference has been identified. [Current evidence](development/r8-arc-public-20261002/results.md).


**2 October adaptive private arc selection â€” IMPLEMENTED_NOT_QUALIFIED:**
Fixed1e-5radius remains failed;5e-6retry returns an uncommitted equilibrium with
requested/actualradius and full failed-work accounting. Same accepted predecessor,
cancellation/stale guards and20/12per-attempt limits preserved. Source15checks plus
final11affected checks pass; independent source review closed. Public atomic arc
publication/checkpoint/controller and installed/capacity acceptance remain OPEN.
[Evidence](development/r8-arc-prototype-20261002/results.md).


**2 October private arc prototype â€” IN_PROGRESS / native trial FAILED:** explicit
fixed-mesh physical chord metric and general sparse border implemented privately.
Actual-chart derivative and stale/radius guards pass. Native coupled radius1e-5
still fails (sphere Newton / plane backtrack limits); failing test retained.
Saved-direction evidence supports a nearby shell active-set transition; bounded
adaptive arc cutback is next, not a claim of passing that radius. No public controller,
restart identity, installed check, continuation or capacity acceptance.
[Failure and next discriminator](development/r8-arc-prototype-20261002/results.md).


**2 October coupled material excursion/branch:** implementation unchanged at
33f7ba7c. Installed local unload/reload regression passes with exact paired-field
and checkpoint restart. Bounded âˆ’70/âˆ’72um continuation also passes; actual
compression reduces to485.652/483.431N. This supports observed equilibrium
softening only; originalâˆ’500N force-history failure, full cyclic qualification,
physical stability and capacity remain OPEN. No aggregate gate closes.
[Evidence and limitations](development/r8-event-material-excursion-20261002/results.md).

**2 October BL5 public example:** objective/historical P0/coarseP1 reference
operator parity passes. New public-API3Q4/2B3 signed staged example passes source
and installed cancel/rebase/restart/continuation on unchanged wheeld506e3f3.
User documentation reflects explicit Q4 policy and exclusions. Consumer line
persistence was completed by the later slice below; physical M2 acceptance remains open.
[Evidence](development/r8-bl5-staged-loads-20261002/results.md).

**2 October distributed material-history extension:** source and installed
two-stiffener force-only route verifies simultaneous Q4 J2/physical-fibre yielding,
yielded-prefix cancellation, snapshot/identical unload-reload continuation and
failed-next-step preservation.397module wheel5cd1df65,218onsiteimports,actual1thread.
Scientific tolerances unchanged. Signed/staged external reversal rejected before
execution; distributed-couple yielding and full combination coverage remain OPEN.
This is scoped G3/G4A evidence, not aggregate acceptance or pressure-policy change.
[Evidence and retained failures](development/r8-ge-native-distributed-20261002/results.md).

**2 October distributed native consumer delivery:** ANYfem9d302cb preserves
GEBeamDistributedLoad through native Project, legacy-compatible strict format and
existing linear/explicit-finite dispatch. Installed98consumer/395solver pair:
91initial checks plus2final affected checks cover92unique checks; full on-disk
save/reopen/cancel/restore/continue workflow passes. Independent review cleanup
finding fixed/injection-tested.282onsiteimports,actual1thread/JIToff. GeneralizedQ4
consumer example only; solver-family coverage does not substitute for additional
consumer qualification. Remaining G4/G6/external/scale/platform obligations OPEN.
[Evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-distributed-consumer-20261002/results.md).

**2 October native distributed GE loads:** public model-bound reference-arclength
force/couple densities now run through the existing point owner, preserving native
42-coordinate work, conservative force potential and nonconservative spatial
couple semantics. Installed wheel395modules:60focused tests,1additional curved
owner derivative and public checkpoint/continued panel example passed. Actual
1thread/JIToff,219onsiteimports. Generalized/fibre/mixed families and Q4/mixed/S3
ownership/reactions/restart checked. Independent source review clear. Scoped
M4/G4A implementation only: consumer persistence, loaded line/footprint/combined
programmes, new-load active yielding, engineering/external/scale/platform envelope
remain OPEN. F03 UNCONSUMED. [Evidence](development/r8-ge-native-distributed-20261002/results.md).

**2 October GE gravity native consumer delivery:** ANYfem83d41b1 adds strict
body-input persistence and linear/explicit-finite Project dispatch. Installed67/67
on the bound98consumer/393solver module pair verifies save/reopen, cancellation
at accepted0.25, disk checkpoint restore and identical0.5/1 continuation. Independent
Read review clear; actual1thread/JIToff,280onsiteimports. Legacy/staged formats
preserved. This is scoped M1/M4/G6 behavior, not full G4 or aggregate acceptance.
Line/footprint/combined gravity, full material/external/scale/platform obligations
remain OPEN. F03 UNCONSUMED. [Evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-gravity-consumer-20261002/results.md).

**2 October native GE gravity development:** model-bound uniform acceleration
now executes reference-linear and conservative finite point-owner work, including
native retained-cell curvature/offset work. Isolated new wheel393modules:
37focused tests and public eccentric-mass twoQ4/twoGE example pass. Physical
mass admission, Q4/mixed/S3, adaptive cancellation, chart/restart and affected
staged regressions exercised. Objective Q4 finite map required; elastic S3 stable
arithmetic is bound to the new checkpoint identity. Failed tests/build retained;
independent source review clear. Material-enabled history/restart parity is tested,
not verified yielding under gravity. This is scoped M4/G4A implementation evidence,
not aggregate acceptance. Line/footprint gravity, native consumer persistence,
full material/external/scale/platform envelope remain OPEN. No F03 consumption.
[Evidence and boundaries](development/r8-ge-native-gravity-20261002/results.md).

**2 October native mixed-material consumer delivery:** ANYfem b831411 now has
a runnable native Project save/reopen workflow for the two-stiffener Q4 J2 /
physical-fibre/generalized case. Final installed1/1 verifies explicit completed
prefix1 and full programme4, actual simultaneous/reversed material activity,
fresh-owner restore and identical continued checkpoints. Initial passed run and
review-driven prefix-status repair retained. Independent Read review clear;
unchanged98consumer/391solver modules,277 onsite imports, actual1thread/JIT off.
This adds scoped M1/M4 consumer/lifecycle evidence, not aggregate G3 acceptance.
[Consumer evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-simultaneous-material-consumer-20261002/results.md).

**2 October simultaneous material-history development:** two parallel native
stiffeners with mixed physical-fibre/generalized sections and two Q4 J2 shells
show actual simultaneous shell/fibre updates at positions1/3/4. Final installed
lifecycle test and public staged example pass; rejection/exception/cancellation,
real chart rebase, complete compensated histories, physical balance, independent
fibre dissipation and restart checked. Separate Read review clear. No product
equation or threshold change; initial inactive-shell fixture failure retained.
This is scoped G3/M4 development evidence. General biaxial/large-rotation/S3
simultaneous histories, full material/attachment envelope and aggregate acceptance
remain OPEN. ANYfem native Project integration follows; F03 UNCONSUMED.
[Evidence and limits](development/r8-ge-simultaneous-fibres-20261002/results.md).

**2 October native rigid-carrier normal-spin decision:** three prescribed levels
complete with correct port pullback, work, release and wrench controls. Tip error
3.0164% ->.48517% ->.10052%, but integratedFy error23.5946% ->8.4450% ->2.5023%
and rootMz transfer24.8854% ->8.9086% ->2.6397%; highest moment remains2.9135%.
Retain law/c2 candidate for development; boundary-layer transfer resolution stays
OPEN, no fourthmesh or extrapolated1% acceptance. Tipwork/spin are one observable;
this is normal-spin/bending, not beam-axis torsion or elastic coupled accuracy.
Independent Read finding addressed with saved station/reaction data, no extra
solve. Two analytical checks pass; initial import failure retained/repaired.
Unchanged391module installedwheel4c14d094,211 onsite imports/run, actual1thread/
JIT off; largest sampledRSS332464128B. FormalF03 UNCONSUMED; M2/G0B and complete
mechanical/external/scale obligations remain OPEN.
[Full interpretation, raw identities and review](development/r8-bl5-rigid-carrier-20261002/results.md).

**2 October acceleration consumer integration delta:** ANYfem now persists
explicit physical mass/density and ordered acceleration cases in separate Q4,
mixed/S3 and Q4-footprint schemas; fresh public owners retain typed load context
and selected equilibrated fields. Installed286/286 and all12 Project examples
(four routes Ã—1/10/100,onefactor) pass with consumer02a41991...5bab4 and unchanged
solver4c14d094...d3b7c. Compatibility finding repaired; callback test failures
retained. Independent Read review clear; no aggregate qualification promoted.
Loaded interior pose, finite/GE gravity and practical-scale/resource acceptance
remain M4/G4A/G5. [Consumer delivery/evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-body-acceleration-consumer-20261002/results.md).

**2 October equilibrated body-section development delta:** typed B2 body loads
now preserve model-bound context through static/batch solves and return separate
equilibrated resultants/strains with actual interior attachment wrenches and
sided jumps. Raw nodal equations, recovery and energy meanings are unchanged.
Independent derivation/Read review and final installed263/263 plus three public
1/10/100 examples pass; wheel4c14d094...d3b7c binds391 modules, actual1thread/JIT
off. Two provenance findings repaired; fixture and endpoint mixed-load failures
retained. B2_ENDPOINT_POINT_MIXED_LOAD_RESOLUTION, loaded interior pose, GE
gravity, consumer load persistence and physical acceptance remain M4/G4A work.
No aggregate gate is promoted; F03 UNCONSUMED; no push.
[Exact delivery, raw and review](development/r8-b2-equilibrated-body-sections-20261002/results.md).

**2 October B2 body-load implementation delta:** experimental reference-linear
uniform acceleration now prepares owned equivalent nodal loads across Q4/mixed/S3
and point/admitted nodal footprints. Independent physical work/wrench and
ownership controls pass; final installed127/127 and three public1/10/100 examples
reuse one factor. Underflow/density findings repaired, failed evidence retained.
Wheel0c4d6edb...03e15 binds391 modules, actual1numerical thread/JIT off. No member
particular-field recovery or GE gravity; these remain named M4/G4A obligations.
No consumer persistence, scientific qualification or aggregate status is promoted.
[Delivery, limits, raw and separate Read review](development/r8-b2-body-acceleration-20261002/results.md).

**2 October paired modal development delta:** matched virgin plate Q4/US3 at
16x4 and32x8 has dominant physical mode matches and consistent cross-grid tracks.
The in-plane frequency gap reduces8.2494% to2.4201%; native/external frequencies
change-.5619%/-6.5022%. Fine native equations<=3.4e-15; actual GE representative
local parity and physical inertia controls pass. This identifies a discretization
contribution, not converged2% accuracy, drilling causality or a failed formulation.
Stop the bounded diagnosis; no automatic64 run or formalF03 consumption.
F07/F12/G4B/M4 and all aggregate statuses stay OPEN.
[Exact raw fields, interpretation and limitations](development/r8-b2-mixed-reference-modes-20261002/results.md).
Credential-bearing historical metadata requires cleanup before any push;
future recorder and new archive use allowlisted/sanitized runtime metadata.

BL5 actual8:1 endpoint, completed2 October: nine retained mixed solves at the
three registered grids pass unchanged controls, onefactor/threeRHS each.
Finest Mz equilibrium9.516e-9 is close to its1e-8cap; last Mz work change-1.354%
is not converged1% accuracy. Existing completion derivative materially aligns
with the root partition discrepancy despite small tip-work sensitivity; no
causal allocation, coefficient tuning, drilling independence or exact point
tie follows. Candidate retained, bounded batch stopped; F03/M2/G0B unchanged.
Formal F03 authority remains UNCONSUMED. [Raw results and limited review](development/r8-bl5-endpoint-response-20261001/results.md).

B2 footprint numerical slice,1 October: original40-Q4 Fz/Mx/My obstruction
repaired without changing geometry/section/load. Narrow active-row rational
certificate and separately declared capped footprint gap admission; point-only
route unchanged. Source136/136, installed176/176 and solver/consumer Project
examples pass. Wheel d99c59ac...,391solver/98unchangedconsumer modules bound.
New nine B2 cases over the existing three E02 grids agree with GE within6.8211e-11;
finest external work+.148%/-.620%/+.120%. Torque1.36% refinement, thickness,
externalprecision, signed eccentric/full-law evidence remain open. Independent
Read review has no development blocker; failures preserved. No E02/F04/F03 or
aggregate status is promoted. [Current repair and bound evidence](development/r8-b2-panel-resolution-20261001/results.md).


Earlier E02 physical rigid-tip development at solver39d2ae3a,1 October: matched installed GE/CalculiX
out-of-plane Fz/Mx/My cases run at three fixed in-plane levels, plus coarse
signed-port parity. Actual membrane/drilling decoupling and negligible free-stub
work hold. Finest work differences+.148%/-.620%/+.120% are not converged1%
acceptance: native torque's last refinement is1.36%, solid thickness resolution
is fixed and seven-digit output cannot certify1e-8 balance. Independent Read
review supports retaining the restricted candidate and stopping the batch.
At that prior source B2's40-cell public resolution guard fails; its accuracy
was not compared. No normal-spin, F03, F04 or aggregate pass follows.
[Combined physical evidence and failures](development/r8-e02-rigid-tip-reference-20261001/results.md).

ANYfem supported B2 footprint-mode consumer,1 October: consumer350c980 and
wheel11728ab8...fa56e use the unchanged solver27660d...f47ec. Distinct strict
experimental modal schema and existing Project dispatch preserve old static
payloads. Installed134 focused checks and both save/reopen examples pass;
391+98 modules match source/wheel/site. Separate Read review has no blocker;
local review timeout supplies no opinion. Modal factors exclude fresh-owner
static construction. This is experimental consumer delivery, not spectral
physics, checkpoint or aggregate G4B/G6 acceptance.
[Evidence and boundaries](development/r8-anyfem-b2-reference-modal-20261001/results.md).

B2/F07/F12/G4B development,1 October: existing physical B2/Q4 descriptor now
supports virgin selected-node rigid footprints with explicit physical mass,
coordinate supports detecting all six common rigid fields and zero offset.
Typed full multiplier/source-frame provenance preserves true point-prefix fields;
normal spin locked, mechanical qualification incomplete. Bounded QR/SVD support
audit corrects factor-success admission; no global dense operator/invented inertia.
One final installed wheel27660d...f47ec binds391 modules,76 affected checks and
public example pass; independent Read review clear. All previous empty-footprint
modal/static behavior retained. Free-free/prestress, drilling/torque physics,
external/scale/consumer and aggregate F07/F12/G4B/G6 remain OPEN. Initial collection
failure preserved. No tolerance/default/version/authority change.
[Implementation/evidence/boundaries](development/r8-b2-footprint-reference-modes-20261001/results.md).

BL5 bounded completion derivative, 1 October: two failing constraint rows in the
retained V2 solve are repaired by one unchanged sparse factor and one additional
compensated correction. Backward error is 1.34897e-13; all original physical
controls and exact rational confirmation pass, with complete independent Read
review. The local normalized applied-work slope is -3.83549e-4 at alpha=1.
Six focused source admission/ownership checks pass; the historical-artifact
assessment uses zero further factors. V1/V2 remain failed. No finite removal,
drilling independence, external-cause allocation or M2/F03 acceptance follows.
Stop completion tuning; advance independent ready capability. The 26-file
verified repair archive supplements unchanged historical evidence.
[Controls, raw bindings and limited decision](development/r8-bl5-completion-sensitivity-20261001/repair-results.md).

M4/F06/G6 footprint V2 development,1 October: explicit increment-origin chart
policy has independently reviewed Q4/mixed/all-S3 elastic solver assessment and
ANYfem persistence/consumer delivery. Old/current default solver observables,
checkpoints and V1 consumer payloads match exactly. Four installed successor
position predicates,87 consumer checks and13 final-artifact checks pass; earlier
impact evidence is reused with its original identities. Historical V1 strict
postrebase failure remains preserved; V2 is a separate policy. Full plastic,
drilling/shear/torque, continuous/distributing/weld, external/scale and aggregate
F06/M4/G6 obligations remain OPEN. No default/version/authority change.
[Delivery and independent reviews](development/r8-footprint-v2-delivery-20261001/results.md).

M4/G6 GE modal consumer development,1 October: strict distinct modal input record
owns explicit supported/free-free policy, native inertia and optional verified
identity; input save/reopen does not assemble/factor. Existing Project selectors
dispatch to public modes and reject incompatible controls. Paired installed37new
and149legacy checks pass,391+98 modules match, seven old GE schema payloads byte-
identical and public Project example runs both policies. Independent consumer
review clear. Input persistence/verified requested fields are not full spectrum,
physical-frequency, accepted-state checkpoint or aggregate qualification; full
F07/G4B/G6/external/scale obligations OPEN. No authority/default/version change.
[Delivery/evidence](development/r8-anyfem-ge-reference-modal-20261001/results.md).

M4/F07 free-free GE development,1 October: explicit modal-only boundary policy
on the existing owner returns six physically verified rigid fields and requested
flexible pairs for connected virgin Q4/generalized six-pose points. Full native
descriptor and only6D physical-mass projection; no artificial mass/condensation.
Installed46 modal+116 affected legacy checks pass,391 bound modules,15 exact
default static bindings and public free-free example. Independent physical
volume/particle work and bounded descriptor controls corroborate these fields.
A resolved extra-mechanism control rejects without partial publication; absence
of all unexcited mechanisms/exactly-six nullity and spectrum completeness are
NOT certified. F07/G4B/repeated-space/physical reference/consumer/external/scale
and aggregate acceptance remain OPEN. No scientific limit or authority changed.
[Delivery and evidence](development/r8-ge-free-reference-modes-20261001/results.md).

M4/F07 supported GE modes, 1 October: canonical public modes(request) now
returns bounded finite pairs for connected supported virgin elastic Q4/native
generalized six-pose point panels. The full sparse descriptor preserves inertial
cell6/member and massless resultants/traces/spin/multipliers; explicit physical
spatial admission, immutable cached mass and full equations/gaps are checked.
Installed29new+116legacy checks pass,391 source/wheel/site modules match,15
default static/JSON/checkpoint bindings are byte-identical, public example runs.
Independent review closed overflow/disconnected-component admission findings.
Complete descriptor/raw QZ corroboration is not all-root or physical-frequency
qualification. Full F07/G4B, free-free/repeated spaces/prestress/consumer/external/
scale and aggregate gates remain OPEN. No authority or scientific limit changed.
[Sources, artifacts, failures, provenance limits and review](development/r8-ge-reference-modes-20261001/results.md).

B2 nodal rigid footprint, 1 October: separate reference-linear six-pose node law
and requested physical wrenches reuse the existing sparse affine/factor/batch
owner. Installed35 unchanged+1 repaired predicate and38 legacy predicates pass,
with complete independent review; initial collinear-success fixture failure stays
preserved. Exact old/current13 operator arrays and default observable/ten-case
JSON agree. Headless public example completes with factor1. Full F04/F10/F11/M4,
normal-spin/drilling physics, finite/S3/spectral and complete consumer obligations
remain open; new spectral requests reject. ANYfem cc9a490 adds a distinct strict
B2 consumer and a legacy rejection guard. Installed37new+112legacy checks pass,
1/10/100 examples reuse one factor each, and old/current payload/results are
byte-identical;488 source/wheel/site modules bound, independent review clear.
This is experimental input/Project roundtrip, not complete native persistence
or aggregate acceptance.
[Consumer evidence](development/r8-anyfem-b2-nodal-footprint-20261001/results.md).
[Artifacts, limitations and raw review](development/r8-b2-nodal-rigid-footprint-20261001/results.md).

Nodal rigid footprint, 1 October: experimental selected-node six-pose locking
and complete selected-cell patches supply sparse reference-linear/nonrebased
finite solves, physical group wrenches and ordinary restart. Final installed
solver 49+4 and paired ANYfem 23+89 predicates pass with complete independent
reviews; 26 preceding-wheel legacy predicates are reused by explicit impact
analysis, not relabeled as current-wheel execution. Public Q4 consumer example
completes save/reopen, solve, recovery, checkpoint and continued stepping.
New policies bind S3 stable arithmetic and native retained F6/M12 work scales
only for nonempty footprints. Legacy default Q4 observables/checkpoints match
the prior wheel exactly on the fixed control. Strict rebase successor parity
failed for Q4/mixed/S3 and remains preserved; new public rebase/chart restore
are explicitly unsupported pending repair. M4/F04/F06 footprint chart transport,
distributing/area behavior, torque/drilling/shear, plasticity, external and full
programme obligations remain OPEN. No aggregate acceptance or release follows.
[Exact artifacts, failed evidence and reviews](development/r8-nodal-rigid-footprint-20261001/results.md).

Staged material history, 1 October: installed point-owner load/unload/reversal/
reload, atomic rejection/cancellation, plastic-state chart reset and checkpoint
continuation pass for selected-Q4 yielding physical fibres, S3 shell J2 with
elastic mixed beam families, and simultaneous selected-Q4/generalized-beam J2.
Same-substep simultaneous advances are directly inventoried. Two retained V5
passes plus the affected V7 pass have complete independent review; no all-green
V5 claim. All failed versions and explicit status/policy/unit/recovery/safe-point
test corrections remain preserved. Product/wheel unchanged, 388 byte-matched
modules and 210 onsite imports. Small rotations do not meet large plastic F06
floors. Existing elastic F06 retained-role normalization is corrected by read-only
re-adjudication of 44 snapshot hashes/26 pairs; its original bound still passes.
Aggregate G3/F06, simultaneous fibre/J2, wider material and attachment scope,
total energy, external and full programme obligations remain open.
[Complete scoped results and immutable raw/review inventory](development/r8-staged-material-history-20261001/results.md).

Controlled external P0 discriminator,1 October: exact non-equation inventory
parity and independent complete review support external enforcement sensitivity.
Strongâ†’40-row P0 Mz work increases13.054405%; native/P0 differs-0.271358%,
with common beam/shell nodal L2 differences.497691%/.907274%. All14 recovery
checks pass. Retain law/P0 candidate for required matched growing-space three-level
convergence; no multiplier selection, converged1% or F03/M2 acceptance. Sampled
single-CPU execution does not verify effective library settings/lifetime threads.
Original stopped execution and historical evidence unchanged.
[Complete supplemental evidence](development/r8-bl5-matched-comparison-20261001/p0-v2-results.md).

Matched growing-space family,1 October: three installed native owners/nine RHS
and nine external cases (eight new/one exact reuse) complete with reviewed full
states/actions. One eligible native factor per geometry; all eight old16/Mz array
roles bit-identical. Finest cross work gapsâ‰¤.060712%, beam/shell nodal L2â‰¤.484905%,
shrinking across levels. Shared final Mz work changes exceed1.3%; some regional
moments and root partitions remain unresolved (Fy degree-zero gap2.787207 N).
Read-only fixed-distance integration localizes most of that gap near the clamp,
without excluding it. Retain law/P0 candidate; bounded saved-state end-port/
support-work review is next. No space/converged1%/F03/M2/G0B acceptance follows.
[Complete results, raw records and independent review](development/r8-bl5-matched-comparison-20261001/refinement-v1-results.md).

Saved end-port/support review, 1 October: all nine root decompositions, all 55
input bindings, full retained rigid-work contractions and signed endpoint-work
predictions independently verified. No support or endpoint-work defect found.
Internal/attachment moment differences can cancel; algebraic shares do not
identify a causal error. The same physical P0 action on both discrete domains is
the next bounded discriminator, subject to verified channel/support ordering,
work measures and isolated-beam rigid-spin compatibility. No new refinement,
law repair, space selection or F03 acceptance follows.
[Analysis and independent review](development/r8-bl5-matched-comparison-20261001/endport-support-independent-review.md).

Finest-grid common-action control, 1 October: zero-LU work/compatibility screen
and the three distinct saved loads complete with unchanged sparse operators.
All 160 action-basis maps agree; native self-replay and full original-free/gauge
stationarity pass. With the same physical P0 action, beam nodal rotations agree
near roundoff and shell director rx/ry differences are about 0.0074â€“0.0107% in
sampled-vector norm. Released normal spin dominates aggregate shell rotation
differences and remains in raw outputs. No coupled yaw, integrated-L2 accuracy,
drilling independence or root/reference convergence is inferred. Retain law/P0
candidate; stop port/mesh tuning in this slice and advance staged material history.
Remaining scientific, CalculiX and complete M2 obligations stay open. Complete
independent review has no consequential admitted-control finding. The canonical
[raw archive and decision](development/r8-bl5-matched-comparison-20261001/common-action-v1-results.md)
preserve all component differences and limitations; no aggregate acceptance.

**Updated:** 1 October 2026. **Candidate:** current integration branch;
exact development-screen source identities are recorded with their raw evidence.
This is the forward status index, not an
amendment to frozen registrations or historical results. The
[complete programme](B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md) defines
requirements; the [active note](B3_GE_E4_PL_ACTIVE_STATE.md) identifies
current evidence and failures. No aggregate gate or milestone is accepted.

F06 scoped loaded point-owner portion,1 October: prospectively declared
independent-direction staged Q4/S3 paths pass control/reset/direct restart and
same eight accepted positions. Actual physical rotations/commutators clear the
unchanged .05rad/1eâˆ’5rad floors in every shell/beam branch. Two installed cases,
388 byte-matched modules and210 canonical imports; independent raw SO(3),
material and reaction review has no finding. The integration owner accepts this
large-elastic point-owner foundation portion only, under Revision8 Â§6.
Earlier curved/proportional failures and the old closure review remain unchanged.
Aggregate F06/V18 is IN_PROGRESS: plastic/cyclic, partial-support, curved/line/
topology breadth, branch ownership and native-energy obligations remain open.
[Exact evidence and disposition](development/r8-f06-staged-transport-20261001/results.md).

BL5 matched physical comparison,1 October: external strong160-row and native
weak40-row16x4/32-station five-channel models satisfy their own reference/work/
equilibrium/recovery checks. Native applied work differs+2.232981% Fy/+12.747623%
Mz; common nodal fields differ3â€“7%. Independent review finds no consequential
collector/recovery defect; cause is not uniquely allocated among enforcement,
shell and beam operators. All poses, cell variables, cuts and smooth/atomic
transfer measures remain. External numerical threads are unverified, and this
OpenSees supplement does not replace CalculiX or converged1% accuracy. One
fixed-operator external enforcement discriminator was the bounded next action
at this record; its completed supplemental disposition appears above.
[Exact results and limitations](development/r8-bl5-matched-comparison-20261001/results.md).

Initial P0 execution record (superseded prospectively by the supplement above):
the fixed-operator external P0 comparison was prepared, not completed. Its
first supervisor stopped on root's stricter total-OS-thread guard (9observed),
not a demonstrated numerical-thread breach or mechanics failure. Import-only
thread/API observations are retained; numerical resource admission remains to
be justified before a fresh run at that point. No limit or criterion changes, and no formalF03
consumption. [Execution obstruction](development/r8-bl5-matched-comparison-20261001/runtime-obstruction.md).

Staged ANYfem consumer,1 October: commit0f0981de adds an explicit staged-v4
envelope and finite Project dispatch without assembly for save/reopen. Current
installed solver/consumer bytes bind388+98 modules. Fifty unchanged V2 passes
plus one affected V3 S3 workflow pass verify metadata, existing Project/legacy/
B2 routes and real Q4/S3 staged save/reopen/solve/restart/continuation. V2's
original S3 small-load backtrack failure remains unresolved; V3 uses the exact
previously passed F06 staged history, not a convergence repair or tolerance change.
Independent complete review has no consequential consumer finding. Experimental
tested behavior only; broader load/material/consumer gates remain open.
[Full provenance, failures and reviews](development/r8-anyfem-staged-20261001/results.md).

Staged translation dead loads,1 October: the existing finite point-owner facade
accepts an immutable model-bound absolute endpoint programme, continuous affine
force paths, forward positions and mandatory stage boundaries. Accepted progress,
force, constitutive/configuration state and controller publish atomically. A new
programme envelope/augmented inner identity binds future stages and rejects stripped
or changed checkpoints. Installed wheel0c456666... passes119/119 affected checks
(56 descriptor,8 staged owner,16 observer,23 finite,13 controller,3 S3 binary).
Prior-wheel legacy checkpoint bytes and seven physical array fields agree exactly
on the bounded control. Complete independent code/evidence review has no finding.
This is experimental tested behavior on the small elastic staged fixture, not
F06 loaded-history coverage, staged yielding or broad G4A acceptance. Moments,
follower/line programmes, consumer programme persistence and zero-force numerical
completion remain outside this slice. [Results](development/r8-staged-load-20261001/results.md).

Positive reference-norm controls,30 September: independently reviewed sparse
beam/shell analytical inverse actions, unit/coordinate-basis congruence and
scalar resolved/unresolved/duplicate-action controls pass the preset predicates.
Finest dual errorsâ‰¤5.93eâˆ’5 beam/1.15eâˆ’4 shell. This does not verify native BL5
work/Q/gauges or beta criteria, consume F03 or close M2/G0B.
[Ordinary development results](development/r8-bl5-riesz-controls-20260930/results.md).

Native BL5/reference pairing,30 September: all40 density basis columns including
supported rows match independent physical covectors; all222 omitted kinematic
slots have C entries zero. Q and reciprocal row-basis work parity pass. Seven
auxiliary inverse actions converge monotonically, but reference-error bounds
and stability criteria remain open (mixed final increment0.21055%). Independent
review is clear for this bounded map/quotient, not mechanical gauge removal,
F03 or M2 acceptance. [Results](development/r8-bl5-native-reference-work-20260930/results.md).

Reference-bound development,30 September: independently reviewed shell modal
tail and beam flux majorants bound all40 action combinations with relative
Loewner error0.000624289. Independent scalar Q1/P0 lifting across seven ratios
and three levels gives prospective finite-family product floor0.4302334;
one-interval controls deteriorate. Independent scalar review is clear; prospective
finite-family criteria include reference/arithmetic allowances and absolute0.43
floor before native spectra. Saved c1/span2 anchor is outside this c2 family;
its corrected floor0.0768685 cannot inherit0.43. Binary64 bounds are not certificates;
actual KKT/locking/transfer remain open. No F03/M2/G0B acceptance follows.
[Results and retained failure](development/r8-bl5-reference-error-bounds-20260930/results.md).

Native finite-family development,30 September: all21 explicit HALF-CELL:shell
c2 cases pass complete physical work and frozen reference-relative predicates,
beta0.793239â€“0.917197; complete-family independent review clear. Whole-B3-element
8:1 endpoint supplement is separate and now passes at all three levels:
beta0.886553/0.874043/0.867138. Original32/64 reference-precision failures remain
preserved. Independently reviewed same-equation residual compensation and
first-eligible auxiliary preparation repair the reference without changing
native meshes, norms or criteria. The largest case meets total error0.000926481
and inverse7.25611e-12. Actual mechanical kernel, locking and physical response
convergence remain open. No F03/V08/M2 acceptance follows from these24 cases.
[Raw results](development/r8-bl5-native-stability-20260930/results.md).

Actual mechanical kernel development,30 September: one16x4/32-halfcell/c2
fixture retains769 supported physical/cell coordinates and locally checks288
negative stationary resultants. All729 kernel/809 saddle modes retained; kernel
minimum1.738e-5 exceeds composed uncertainty3.106e-11. Implied native inertia
769positive/328negative/0zero modes and three-load role parity<=3.17e-12 pass
independent review. This is bounded support/kernel/work evidence, not whole-domain
mechanical, locking, converged physical accuracy or F03/M2 acceptance.
[Mechanical supplement](development/r8-bl5-native-stability-20260930/mechanical-results.md).

Finite-family local supplement,30 September:44 complete local mode inventories,
22translated pairs and24definition/connectivity inventories resolve the stated
local energy/rigid-kernel premises. Actual supports/C detect the remaining beam
yaw; independent actual review is clear. V1 serialization failure is preserved;
V2 numerical modes are byte-identical. Together with the separately bound native
row-independence evidence, this supports only a conditional nominal finite-family
argument. No exact PSD/global coercivity, locking/accuracy or F03/M2 acceptance.
[Results](development/r8-bl5-native-stability-20260930/local-kernel-results.md).

F06 loaded development,30 September: original installed Q4/S3 V1 has two retained
failures. Q4 misses0.05rad/1e-5 noncommuting coverage; S3 whole-origin fingerprint
differs only after separately recomputed successors. Same-state reset/restore
hashes pass. A complete S3 recorder finds only derived coordinate/strain/stress
roundoff plus corresponding integrity digests; irreversible histories stay exact.
Physical differences are~1e-15 and stress difference<=0.000257Pa. This explains
the hash diagnostic but does not confer F06 acceptance or repair missing coverage.

The same stronger V2 pattern accepts prefix/reset/restore but exhausts the direct
final Newton budget in Q4/S3. With the new postcommit accepted-state observer,
V3 adaptive continuation completes both, preserves identical accepted factor
paths, and passes every physical/material successor comparison. S3 meets the
rotation/noncommutation floors; Q4 commutator9.913424e-6 misses1e-5. This remains
failed Q4 coverage, not a relaxed pass. The V3 runner's8.3-directory import guard
also fails; separate no-solve canonical route validation passes209imports and
387source/site modules, with the narrower validation scope retained. Observer
source and installed results are independently reviewed;55current checks pass
across retained runs with explicit unchanged-input reuse. Earlier stale/overloaded
fixture failures remain. [Results](development/r8-f06-loaded-transport-20260930/results.md).
No new F06 or aggregate acceptance follows.

Development update, 29 September 2026: the objective S3 J2 algorithmic owner slice passes 49/49 source and 49/49 exact installed-wheel checks with independent review. Failures and exact inputs are preserved at `.qualification/b3-ge-e4-pl/r8-s3-j2-algorithmic-dev-20260929-v1/`. This does not close F05, V03/V17/V18/V28 or an aggregate gate.

Native fibre-linear integration,30 September: product `6b0b1131` admits existing
physical fibre sections and mixed native elastic families in the reference-linear
Q4/S3 point owner. Fresh installed54/54 plus three public examples and separate
ANYfem input save/reopen2/2 pass independent review. This is verified experimental
behavior only; finite fibre histories/stresses and ordinary persistence remain
open. [Exact results, retained failures and review](../../.qualification/b3-ge-e4-pl/r8-ge-fibre-linear-dev-20260930-v1/results.md).

Native finite-history integration,30 September: product `7adee4f5` retains
physical-fibre predecessors/results atomically in the existing point owner,
with native accepted strain/stress/plastic-increment recovery and distinct V7
restart. Source41/41, fresh installed62/62 plus two Q4 history examples and
installed ANYfem4/4 pass. Positive physical histories are partial-yield Q4
pure/mixed and elastic Q4/S3 mixed; pending pure-fibre S3 failure-contract
checks do not constitute physical-case acceptance. Strong-yield and S3 failures,
J2/fibre combinations and integrated energy/dissipation remain open. No gate
or milestone closes. [Results and retained failures](../../.qualification/b3-ge-e4-pl/r8-ge-fibre-finite-dev-20260930-v1/results.md).

Native energy/coupled-history integration,30 September: product `565685c1`
adds paired beam stored energy/last-increment dissipation and native V8 shell-J2
plus fibre predecessor/accepted snapshots. Source10/10; fresh installed124/124
plus two public examples; installed ANYfem7/7 selected pass. Independent code
and artifact review found no remaining consequential finding in this slice.
Positive cases: Q4 fibre yielding with elastic shell-J2-defined response, and
mixed all-S3 shell yielding with elastic fibres. The initial Q4 active-shell
coverage failure is retained; simultaneous active yielding, strong yield and
pure-fibre S3 remain open. Native energy is not total-system energy. No aggregate
gate closes. [Results, raw evidence and review](../../.qualification/b3-ge-e4-pl/r8-ge-native-energy-coupled-dev-20260930-v1/results.md).

Adaptive native stepping development,30 September: optional typed cutbacks and
durable V10 complete unchanged partial-fibre S3 loading/unloading(.5,1,.75,.5),
with exact physical/fibre-energy parity to fixed identical accepted increments.
Final installed88/88 and focused ANYfem1/1 pass. Strong Q4 still exhausts after
an elastic(.0625,) prefix; simultaneous yielding and full G3 remain open.
Default stepping, physical tolerances and old V7 behavior are preserved.
No aggregate gate or speedup claim. [Exact evidence and review](../../.qualification/b3-ge-e4-pl/r8-adaptive-native-increments-dev-20260930-v1/results.md).

Statuses describe acceptance, not prototype progress. `IN_PROGRESS`
includes incomplete or failed required cases; it never means a numerical
pass.

B2 integrity and matched-support development,30 September: the single-Q4 owner
shares guarded affine-work projection and row-scaled physical acceptance; batch
case identities are owned before callbacks. The public supported BL5 strip
completes2 reference-linear loads with1 factor and exact snapshots. One own-factor
compensated correction resolves the retained/multiplier roundoff discrepancy
against the independently saved root-tie counterfactual under unchanged1e-10
role parity. Fresh installed134/134 pass (59B2,25GE,38L1,10fibre,2finite controls);
all386 solver/97 consumer modules match wheel/source/site. Independent review
is clear for scoped development. V1-v6 setup, example and parity failures remain
failed evidence. Wheel942460a1...,consumer unchangede3f755fe.... Added backsolve
cost is unmeasured at scale. Ground supports and endpoint transfer have distinct
reaction provenance. No physical-law, multiplier-space, M2/M3/F10/F11/F13 or
aggregate acceptance follows. [Results and raw versions](../../.qualification/b3-ge-e4-pl/r8-b2-integrity-ge-support-dev-20260930-v1/results.md).

Native elastic S3 precision development,30 September: product `86d3759a`
uses the existing stable translation map only in eligible native-fibre elastic
S3 finite owners, with a distinct V9 checkpoint policy. Unchanged monotonic
elastic/partial-fibre S3 loading, physical balance and restart pass; V7 restores
retain their original arithmetic and bytes. Source11/11 plus3 codec checks,
installed113/113 and focused ANYfem1/1 pass; independent review is clear for
this slice. Earlier helper/test/installed-collection failures and yielded S3
unloading failure are retained. Yielded unloading, strong full-section Q4 yield,
simultaneous active yielding and full G3 remain IN_PROGRESS. No speedup or
aggregate gate claim. [Exact evidence](../../.qualification/b3-ge-e4-pl/r8-stable-native-s3-dev-20260930-v1/results.md).

F05/F06 development: solver `0da6cd12` selects a distinct Q4 full algorithmic pullback without changing the historical default. ANYfem `b0185b4` persists it in experimental v3. Exact installed solver/consumer checks pass 91/91, including independent local work/active-branch derivatives and yielded Q4/mixed Q4/S3 unload/reload, physical balance, actual rebase and restart. Independent review reports no actionable defect in this slice. Evidence: `.qualification/b3-ge-e4-pl/r8-q4-pullback-dev-20260930-v1/`. The missing active selected-Q4/S3 assembled and one-sided yield predicates now pass a separate frozen 10-case installed assessment. Independent adjudication accepts scoped F05; see `.qualification/b3-ge-e4-pl/r8-f05-foundation-20260930-v1/` and the contract below. The earlier 91 cases are reused by unchanged dependency identity, not retroactively relabeled. No aggregate pass follows.

F06 development: product `ffc1afd0` adds actual owned shell-anchor resets, immutable state, atomic generation events and a distinct anchored checkpoint/restore contract. Source 33/33 and exact installed 77/77 pass with independent review findings closed; mixed Q4/S3 elastic/J2 continuation matches controls. Evidence: `.qualification/b3-ge-e4-pl/r8-owned-shell-chart-dev-20260930-v1/`. The fixed curved loaded-history discriminator is unsuccessful: v1 reference admission failed, v2 selected-Q4 rotations/commutators missed frozen coverage bounds despite completed reset/restore/continuation, and v2 S3 hit its first-step Newton limit. See `.qualification/b3-ge-e4-pl/r8-f06-noncommuting-dev-20260930-v1/`. Stop this fixture without automatic tuning/refinement; F06 remains open, not a formulation failure. Native total energy is unmeasured. The prior all-S3 `.5â†’.55` failure stays retained. Large noncommuting history, broader supports and chart/history qualification remain unfinished; F06/V18/G0B and aggregate acceptance stay IN_PROGRESS.

F07/F12 development correction: the distinct flat-Q4 director mass and corrected bounded descriptors pass 17/17 source and 17/17 exact installed checks, with independent review findings closed. Legacy mass and historical evidence are unchanged. Evidence: `.qualification/b3-ge-e4-pl/r8-physical-q4-mass-dev-20260929-v1/`. Sparse/public spectral qualification and aggregate acceptance remain open.

M4 reference-modal development: the existing B2/Q4 facade returns checked experimental finite pairs with explicit mass and coordinate supports, including retained zero-inertia primal variables. Original source/installed solver 54/54 and installed consumer 6/6 pass; independent findings closed. Original evidence: `.qualification/b3-ge-e4-pl/r8-b2-reference-modes-dev-20260929-v1/`. Completeness/repeated spaces, free-free, prestress/buckling/GE and G4B acceptance remain open.

B2 consumer mass/modal persistence development: ANYfem `a615c4b` adds explicitly selected mass-v2 inputs, preserving nullable shell density and complete beam mass source/origin/matrix. Static v1 remains default and unchanged. Static/affine models are retained; unsupported modal requests fail at public operation admission. Source 19/19 and exact installed 43/43 pass; all 384 solver and 97 consumer Python modules match source/wheel/site. Independent code and artifact review finds no actionable issue. Exact raw inputs, imports, resources, setup failures and review: `.qualification/b3-ge-e4-pl/r8-b2-consumer-mass-dev-20260930-v1/`. This implements experimental input modal persistence only; native-project persistence, full B17/G4B/G6 and aggregate qualification remain open.

| Milestone | Status | Main remaining obligation |
|---|---|---|
| M1 matching-station GE | IMPLEMENTED_NOT_QUALIFIED | Accepted spatial point-action recovery and ordinary native ANYfem input roundtrip now verified. Latest consolidated installed slice covers171 distinct predicates (V1 170pass/1 fixturefail; V2 corrected1/1). Matched E01, physical torque/drilling, complete V01â€“V06/V17/V18/V28 evidence and independent acceptance open. |
| M2 bonded line | IN_PROGRESS | BL5 physical law, multiplier resolution, F03 and ratios/refinement/transfer open. |
| M3 physical B2 | IMPLEMENTED_NOT_QUALIFIED | Multi-Q4/native-S3/B2 point-panel and installed ANYfem native Project save/reopen/selected 1/10/100 batches tested with one eligible factorization; historical Q4 route retained. Scoped F09 and F10/F11 point/static accepted; fixed E01 B2 reference executed with retained discrepancies. S3 mass/spectral/footprint routes, general F10/F11/F13, complete consumer workflow and converged E01 accuracy remain open. |
| M4 remaining mechanics | IN_PROGRESS | Selected-node rigid footprints have installed unrebased solver/consumer evidence; footprint chart transport and broader material/attachment/topology/load/spectral/imperfection/capacity requirements remain mandatory. |
| M5 scale/release | NOT_STARTED | Practical scale, platforms, external programme and authorized release remain mandatory. |

M2 bounded decision,30 September: independent local stationary elimination and
one nodal-root counterfactual identify termination enforcement as the leading
cause of the saved fixed native torque response difference. Root augmentation
matches strong-comparator compliance within0.00334%; nonroot action differences
remain. It constrains the nodal triad, not the retained endpoint director.
Match declared support/termination and preserve reaction provenance before
further physical comparisons; no port rewrite, space selection, external bridge,
law/gate acceptance or formalF03 consumption follows. Metadata, arithmetic and
rank-solver failures are retained with corrected results and independent review:
[decision evidence](../../.qualification/b3-ge-e4-pl/r8-bl5-port-boundary-decision-dev-20260930-v1/results.md).

M2 physical-transfer screen,30 September: matched ground supports retain BL5
ports. A +10Nm normal couple transfers entirely by distributed force arms with
zero direct normal couples/drilling constraint columns. Unchanged16-interval
isolated OpenSees Fy/Mx runs retain full poses/covectors and verified equation
work/root provenance; applied-work differencesâˆ’0.4650%/+0.0872%, but Fy shell
pose1.9279% and transfer-shape/root partitions remain different. Independent
review finds no work-map defect. Installed61559673 BL5 finite impact9/9 passed.
Proceed to growing-space/ratio and common-field, fixed-distance transfer
assessment, not a port rewrite or isolated axial campaign. No converged1%
accuracy, drilling-response independence, multiplier selection, F03 authority
consumption or aggregate acceptance:
[physical-transfer evidence](../../.qualification/b3-ge-e4-pl/r8-bl5-physical-transfer-dev-20260930-v1/results.md).

M2 aggregation slice,30 September: the same explicit P0 span now admits complete
positive-divisor supports. Independent review identified and repaired finite
zero-load acceptance/restore of a known single-support rigid mode. Wheel5079b270...
passes73 installed checks. Two complete uniform c_lambda1/2 policies were
screened at reciprocal ratios, then at three two-direction levels for beam:shell
2:1; rows grow40/80/160 versus20/40/80. Mz policy-work difference contracts
17.457%â†’6.244%â†’1.845%, with non-monotone transfer components still reported.
No policy is selected and no fourth mesh follows. Independently derived
[reference norm contract](B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md) resolves the
supported continuous-axis/cell-director function-space question; inverse-actions,
controls, enrichment, numerical criteria and actual KKT stability remain open.
[Candidate, failures and results](../../.qualification/b3-ge-e4-pl/r8-bl5-coherent-aggregation-dev-20260930-v1/results.md).
This is implemented/tested development, not M2/F03/G0B/G2 acceptance.

| Gate | Status | Boundary |
|---|---|---|
| G0A | IN_PROGRESS | Reconcile prior registration before a pass claim. |
| G0B | IN_PROGRESS | Scoped F05/F08/F09 passed; other foundations, including F03, open. |
| G1 | IMPLEMENTED_NOT_QUALIFIED | Experimental sparse owner exists; foundation and full G1 acceptance open. |
| G2 | IN_PROGRESS | Candidate line/footprint and topology incomplete. |
| G3 | IN_PROGRESS | F05 fixed-predecessor foundation passed; full material domain open. |
| G4Aâ€“G4D | NOT_STARTED | No aggregate load, stability, imperfection or capacity acceptance. |
| G5 | IN_PROGRESS | Development scale screens do not meet practical-scale qualification. |
| G6Aâ€“G6D | IN_PROGRESS | Focused installed/consumer checks exist; final graph, external, reviews and release open. |

F05, F08 and F09 are accepted only for their scoped foundations. Other
foundations remain open; the earlier bounded F04 distinction does not close F04:

| Foundation | Status |
|---|---|
| F01 | IN_PROGRESS |
| F02 | IN_PROGRESS |
| F03 | IN_PROGRESS |
| F04 | IN_PROGRESS |
| F05 | PASSED â€” selected Q4/existing S3 fixed-predecessor foundation |
| F06 | IN_PROGRESS |
| F07 | IN_PROGRESS |
| F08 | PASSED â€” native generalized/physical-fibre local extraction |
| F09 | PASSED â€” physical B2 section/local operator and station trace |
| F10 | IN_PROGRESS â€” finite-support Q4/S3 point/static portion PASSED; other attachments open |
| F11 | IN_PROGRESS â€” finite-support Q4/S3 point affine/KKT portion PASSED; broader scope open |
| F12 | IN_PROGRESS |
| F13 | IN_PROGRESS |

The preserved30 September F06 closure review found loaded noncommuting coverage
missing at its original identities. The separate1 October staged Q4/S3 path now
passes that named elastic point-owner portion with complete independent review;
see the current scoped disposition above. AggregateF06 remains IN_PROGRESS for
the remaining breadth. Historical failures and authorities stay unchanged.
[Independent applicability review](B3_GE_E4_PL_F06_CURRENT_REVIEW_20260930.md).

### F10/F11 finite-support point/static binding â€” prospective v1

This assessment is limited to `B2_FINITE_Q4_POINT_REFERENCE_LINEAR_V1_DEV`
and `B2_FINITE_S3_POINT_REFERENCE_LINEAR_V1_DEV`: physical vertex translations
define a least-squares rigid shell pose; shell nodal rotations contribute no
port action. The beam uses its physical station trace. This is distinct from
the GE nodal point law, BL5 line law and qualified rigid/distributing footprints.
Local S3 evidence does not imply an implemented public S3 B2 owner.

Unchanged product source `a5a698b5eb149ac8b62b358b0a1edcd921a77d32`;
installed wheel SHA-256
`942460a11d45ffe3dea3f32cae457f75d7c5ca283a60bce6a8f01041b817fb96`.
The new assessment test SHA-256 is
`1f9c1d2a644e1d7f53dcdcab6099adb48f52d5ede3f789e5f43ecad582e2e58a`.
Independent pre-execution scientific review `/root/bl5_consumer` cleared the
exact test and six rigid-field addition. No outcome is implied by registration.

Execution directory: `TEMP/r8-f10-f11-point-installed-v1`.
Frozen `contract.json` SHA-256
`6fef88bf07d4e23779c9b78f3cabe31859f40691a199c3594ceca30dd2969fd0`
binds all386 kernel modules, four test fixtures, wheel, runner/supervisor,
dependency versions, inventory and scientific limits. Runner SHA-256
`0618b1ea1d19fd52ee8bd77ba23228dc7b2b888e0eb307558b3920d4ec092081`;
unchanged existing supervisor SHA-256
`2c5320eb23747d687bdccfb98bb0d2751bfd1fd24e723238316bafd70dd464bf`.
Command: `python -u run_bounded.py` in that exclusive directory, once.
Python3.14.2, one effective numerical thread, JIT disabled;600s/8GiB process-tree
limits,100,000-row ceiling, one owned heavy job. No source-root fallback.

Required inventory:40 positive cases (Q4/S3 Ã— both eccentricity signs Ã—
scalar/coupled SPD section Ã— base/shift/rotation/equivalent-unit/support-winding)
and25 negative cases,65 JSON reports and65 executed pytest cases without
skip/error/failure. Geometry uses the existing2m member, station.4, eccentric
heightÂ±.2m and section offsetsÂ±(0,.08,-.03)m. Independent shell covariance/couple
algebra, B2 force-method boundary-value fields and bounded constrained-nullspace
solution supply the oracles. Actual left-rotation update steps are
`1e-4,3e-5,1e-5`; every entry must be finite individually (pre-execution runner
review correction; earlier unexecuted runner/contract retained). Pure common
translation/spin fields exercise all six axes.
Shell free bending is required, with normal drilling uncontributed by the port.

Frozen normalization:2m length,1N force,2Nm moment,1e-12 normalized absolute
floor; transform every physical channel back to these scales. Constraints,
ports, actions, displacement, multipliers and reactions require relative1e-10;
force/moment/virtual/support work and equilibrium1e-8; reference/rigid/accepted
gap1e-9; every actual-update plateau error1e-6. Constraint rank6 and solved free
bending norm>1e-8 are coverage predicates, not a stability certificate.
Nonfinite/malformed/degenerate geometry, station/offset/representation failures
and invalid affine plans must produce explicit expected rejection reports.

Reuse prior134/134 only as unchanged-source/artifact regression evidence,
never retrospective scientific acceptance. Any identity drift, incomplete
report, predicate failure or resource failure prevents acceptance and is retained;
no automatic retry. Independent source/artifact/scientific result review is
mandatory. A pass closes only this point/static portion; generalF10/F11,
F13 andG0B stay open. The callback-close owner lifetime gap keeps F13 open.

**Scoped acceptance,30 September:** the single frozen installed assessment
passed65/65 (40 positive,25 negative) with65 complete scientific reports.
Every386 source/wheel/site module matches;205 observed solver imports are onsite.
Maximum solve/dual/reaction error4.86e-14, virtual work4.61e-13, actual-update
plateau2.36e-9, six rigid fields1.13e-17; all frozen limits pass. Independent
mechanics/code/artifact review accepts only the declared point/static portion.
Route4.651896s, peak204963840B, effective1thread/JIT off; no resource failure.
[Results and independent review](../../.qualification/b3-ge-e4-pl/r8-f10-f11-point-foundation-20260930-v1/results.md)
bind unchanged sourcea5a698b5/wheel942460a1. Seal SHA-256
`15d8709371fd266167914358ffe974be174b3277b6216cee31737af3ebff7cb5`
covers94 files plus the seal. GeneralF10/F11, G0B, F13 andM3 stay open; local S3
proof does not imply public S3 B2 execution or finite B2 qualification.

**E01 B2 fixed development comparison,30 September:** both eccentricity signs,
six load channels; native12/12, six analytic external beam controls and12 isolated
external panels pass. Independent C rows agree4.4409e-16; sampled same-state24
beam covectors agreeâ‰¤5.69e-16/load, with remaining assembled-force differences
allocated to shell contributions (not unique drilling blame or all-state proof).
Worst full-pose6.8574%, tip2.0534%, energy2.8973%, physical multipliers10.2708%,
ground8.6424% discrepancies remain. No converged1% accuracy/M3 acceptance.
OpenSees3.8/Python3.12.14; same product wheel6a44... . Source/input reuse,
restraint-input failure, sequential factorization failure, fresh-process diagnosis
and complete comparison are [preserved and independently reviewed](../../.qualification/b3-ge-e4-pl/r8-b2-e01-finite-point-dev-20260930-v1/results.md).
122 files including seal SHA-256
`533a9e309a117b0a90c7c0cf4ce667dc48a8210f0a956a2c176a5406491fe662`.
Mandatory CalculiX, convergence, other reference families and full gates stay open.
Do not tune the connection or launch default refinement to erase differences.

**B07/F13 development,30 September:** signed selected displacement/reaction
envelopes preserve governing case IDs, first ties and complete prefixes. The
graph's accepted-zero cancellation defect is repaired with shared guarded
affine-work projection; unrepresentable and scaling-erased work fails explicitly.
Fresh installed127/127 pass, all386/97 modules match source/wheel/site,267 onsite
imports,1thread/JIT off;28.190429s/227471360B. Wheel6a44aa11...,383 other modules
unchanged; independent root-fix review and separate envelope review clear.
[Original failure, exact scope, logs and review](../../.qualification/b3-ge-e4-pl/r8-b2-work-envelope-dev-20260930-v1/results.md)
sealed48 files including seal SHA-256
`da8a8d07da0c18b54e958840999d70b9f0d70cbe2815dbb3d9276fb04ccf890a`.
General F13/M3 remain open; no member-resultant envelope, scaling/material
qualification, speedup or larger-domain acceptance follows.

**F13 lifecycle development,30 September:** completion-callback closure now
returns the complete selected prefix and scalar numerical counts. Incomplete
closure is cancelled with an explicit reason; final-case closure is completed.
No factor is retained by the operation or an original error traceback. Eight
new closure/cancellation/weak-reference/error tests and59 affected B2/consumer
regressions pass67/67 through fresh wheel
`0a7532a62f4b03ccc718a391f7a21d571dd917a2f01deac7cb745fee5ba87e8b`.
All386 solver/97 unchanged consumer modules match source/wheel/site;267 onsite
imports,1thread/JIT off,12.440432s/224030720B. Only the batch method changed;
385 other modules and mechanics primitives are unchanged. Independent source,
artifact and lifecycle review is clear; scoped point/static scientific evidence
and75 unaffected GE controls remain applicable by recorded impact analysis.
[Original failure, superseded V1, final V2 and review](../../.qualification/b3-ge-e4-pl/r8-b2-callback-close-dev-20260930-v1/results.md)
are sealed (81 files plus seal SHA-256
`f456f52102499d3bec85b565ec696371b15c89dee0088594e20779dd8f1b14f0`).
Aggregate F13/M3 remain open. General concurrent closure, new laws, physical
accuracy, scale or speedup are not claimed.

F09 development, 30 September: the fixed-wrench physical aspect family passes the public session (4/4 installed including its private control); independent cut-work, tip and station predicates pass. Solver `227d5ea8` enforces the reviewed exact basic-energy plus separate bounded rigid/cross certificate on emitted tangents, replacing the arbitrary pivot veto while preserving exact SPD and strict representation checks. Installed 200/200 and six-row exact-input threshold checks pass with independent review, retaining historical below-floor mismatch and parity only where laws agree. Prospective candidate binding and current-wheel preservation now support the scoped foundation acceptance recorded below. Historical nonphysical shear-soft local passes and graph failures remain retained. Evidence: `.qualification/b3-ge-e4-pl/r8-f09-admission-dev-20260930-v1/`, `.qualification/b3-ge-e4-pl/r8-b2-output-guard-dev-20260930-v1/`, `.qualification/b3-ge-e4-pl/r8-f09-foundation-20260930-v1/`.

### F09 candidate binding â€” frozen prospective v1, not a pass

Independently reviewed before candidate execution by `/root/anyfem_consumer`:
no missing input identity or consequential overclaim within this foundation.
The current-wheel preservation check uses the same ten historical selectors
(14 instances), prepared at TEMP/r8-b2-f09-legacy-candidate-v1; frozen input
list SHA-256 `d25dde9920ceac5eee80828f7603d39e226a429320a4f8222b6aff4de4183ccb`.
Run `python -u run_bounded.py` there; the retained runner verifies exact wheel,
source/site catalogs, test identities, effective settings and imported paths.
No F09 outcome is implied by freezing this contract.

**Claim:** the distinct physical elastic B2 section/local operator and physical
station trace foundation. This is not acceptance of attachments, arbitrary
assembled graphs, mass/prestress, global forward-error bounds or production
qualification. The full F09 inventory remains required; downstream F10â€“F13,
M3 and G0B are not inferred. Historical failed and nonphysical stress evidence
remains visible. Independent review must resolve whether this exact foundation
scope satisfies F09 before any PASSED disposition.

**Candidate:** solver product `227d5ea833231eddf306080cf787ec77fd2fb1bb`,
test/evidence checkpoint `09a0e029832af0bc2f204bddc54a23799fcdaf53`, operator
`B2_PHYSICAL_FLEXIBILITY_LINEAR_V1`, profile `B2_E4_PL_FAST_LINEAR_V1`,
output certificate `B2_BOUNDED_OUTPUT_REPRESENTATION_V1`. Solver wheel
`19e3235a35b69e14f322867bf224b164789163c6cc7e2e808c0bba584c3c441e`;
consumer `a615c4b2` and wheel `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`.
Both source/site module catalogs, test inputs and dependency/environment
identities are fixed in the guard and threshold identity.json records. A
changed relevant input invalidates its reuse; a rebuild receives a new identity.

**Mechanical and numerical admission:** straight finite positive-length SI
members with explicit owned proper frames and source IDs; public definitions
validate frame orthogonality at the existing 1e-10 limit. Scalar laws have
finite positive E/A/Iy/Iz/J/ky/kz and -1<nu<.5, with G=E/[2(1+nu)].
Generalized laws are finite exactly symmetric 6x6 SPD in declared
N,Vy,Vz,T,My,Mz ordering. Exact LDL proves SPD; a small positive pivot is not
an input defect. There is no artificial stiffness floor or empirical geometry
cutoff. Derived quantities and emitted responses must meet the existing
binary64 representability checks; nonfinite/overflow/nonzero-underflow and
inaccurate subnormal output fail explicitly. No stiffness metadata supplies
missing mass/shape information.

Every constructed local tangent must satisfy the exact implemented-law
basic-energy Loewner bounds at 1e-8 and separate rigid wrench/work and cross
work bounds at 1e-9/1e-8. Use the documented canonical right inverse R,
centroid rigid basis Z, L-scaled translation and unit rotation, and
F=max(section translational diagonals, rotational diagonals/LÂ²), M=FL,
E=FL. These bound normalized amplitudes <=1 separately; they are neither
one combined-energy bound nor all-amplitude relative error near rigid modes.
They establish output representation, not independent constitutive correctness
or graph stability. Wrong-law input, local representation and global numerical
failure remain distinct non-success categories; programming errors propagate.

**Evidence reuse, explicitly prospective:** the independently reviewed Level-A
installed 200-case campaign and six-row threshold supplement may support this
candidate only for their unchanged source/input/environment identities and
their actual recorded predicates. They remain development runs, not relabeled
formal executions. Relevant F09 cases cover unfloored scalar weak/extreme
energies, both bending planes, unequal inertias/shear factors, coupled SPD,
six basic rank/rigid modes, reversal/orientation, station work/derivatives,
private equivalent units and public SI, typed negatives, bounded physical
elbow/aspect families and exact-input historical threshold dispatch. Exact
Gauss-Jordan/cut-wrench/Castigliano and trace boundary-value oracles remain
independent of the implemented law. Existing tighter per-case tolerances take
precedence: scalar tiny energy/threshold 1e-12, elastic FD 1e-6, physical
graph work/station 1e-8 and registered component absolute floors. No unseen
case or continuous graph envelope is inferred from these finite checks.

The release-wheel historical installed 14/14 at G0A-B2 remains baseline
evidence. Its preservation on this candidate requires exact dependency-impact
justification or the same ten selectors on the current wheel, never another
baseline registration. The extreme 2^-80 mixed-elbow failure remains adverse
graph evidence; its local mode pass is not an assembled accuracy claim.

**Terminal rules:** F09 remains IN_PROGRESS while required input
binding, any scientific predicate or independent correctness finding is open.
No retroactive qualification, scope reduction or tolerance relaxation. Formal
candidate checks use isolated installed imports and exclusive outputs with
full logs, observed exits, Python/dependency/thread identities and 600 s /
8 GiB process-tree supervision, one numerical thread/JIT off unless separately
qualified. No consumed historical or F03 authority is renewed. Independent
mechanics/interface and artifact adjudication is required for any foundation
PASSED disposition; resource breach, missing inventory, identity drift,
unexpected success/failure or unresolved correctness findings leave it open.

**Disposition:** scoped F09 PASSED after independent scientific/code/artifact
adjudication. The frozen candidate preservation run passed all 14 historical
instances, exit zero, no skip/error, 3.609 s and 204,144,640 bytes RSS. The
existing installed 200+6 development cases are explicitly reused by unchanged
relevant identities, not relabeled as formal runs. The historical release-wheel
baseline and adverse graph failure remain distinct. No arbitrary graph,
attachment, mass/prestress, F10â€“F13, M3 or aggregate qualification follows.
See [exact evidence and independent verdict](../../.qualification/b3-ge-e4-pl/r8-f09-foundation-20260930-v1/results.md).
The pre-execution matrix is preserved as contract.snapshot.md, unchanged.

The individual V01â€“V28 and B01â€“B18 obligations below are all
**IN_PROGRESS for acceptance**; none is marked PASSED. Their exact cases
and criteria remain in the programme. Split a group when a row reaches
candidate adjudication; a failed required case cannot disappear within it.

### F08 candidate binding â€” frozen prospective v1, failed collection

Independent pre-execution review by `/root/anyfem_consumer` accepts the
scientific scope and corrected hash assertion: 28/28 fixture/config matches,
27/27 source test/helper matches, unchanged 17-case inventory. The initial
binding finding and its repaired preparation remain retained. No product
equation changed and no remaining pre-run correctness finding was identified.

**Foundation claim:** faithful local extraction of both existing native B3
generalized and physical axial/biaxial-fibre operators, preserving their
18 physical plus 24 retained coordinates and accepted material predecessors.
It does not independently qualify the inherited element/material equations,
the nonunique tangent at a yield switch, a scalable mixed owner, line law,
or G1/G3. The source suite explicitly retains the yield-switch central-FD
mismatch and checks its one-sided responses and nearby smooth active branch;
that mismatch is not relabeled a smooth tangent pass.

**Candidate/input identity:** unchanged native product in solver `7ae52d80`,
wheel `19e3235a35b69e14f322867bf224b164789163c6cc7e2e808c0bba584c3c441e`.
The two exact test suites are `test_b3_e4_g0_f08_local_operator_seam.py` and
`test_b3_e4_g0_f08_adapter_contract.py`: 17 parametrized cases after the added
current generalized accepted-predecessor and direct block assertions. They
and their 27-file fixture closure are prepared at
`C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-f08-adapter-installed-v1`.
Frozen 28-file fixture/config list SHA-256
`b61dda5d5a9a8016ea55b916e643d93dadcbd369b3850f853f233d0068a94d5e`;
installed runner SHA-256
`96f75bad6164fc4df31fb4e5f151508700040c34f55e04c41981d1d920eed15b`,
supervisor SHA-256
`527535441e819612a59c78326a0fc5c54f091265ee126df741693d54164bba56`.
Pre-review caught recorded rather than asserted fixture hashes; the corrected
runner asserts the frozen manifest and every fixture/config before pytest.
The original unexecuted preparation is retained as `inputs-before-review.json`.
The runner also binds the full 384-module source/wheel/site
catalog, dependencies/settings and import origins. No fixture depends on the
separately owned dirty F03 script. Imported helpers are definitions only;
no diagnostic CLI or consumed F08-D/F03 authority is invoked.

**Required inventory and oracles:** both families at virgin and perturbed
physical/retained configurations; generalized line force/couple work; actual
native multiplicative update derivatives; yielded fixed-predecessor fibre
parity, side-specific yield transition and smooth plastic branch; owned
response arrays/candidate histories; unchanged accepted origins/state/checkpoint;
invalid family/parameter/model/reference/state rejection. Current generalized
actual first accepted .5 target is restored and perturbed using the frozen
2e-4*sin(free_index+.3) step with its accepted histories. Current generalized
and yielded fibre trials must assert correct 18+24 cross/internal blocks,
both elements' six shared physical contributions and no coupling between
disjoint retained coordinates. Nonzero physical/cell rotations, retained
resultants and scaled compatibility are required for the generalized trial.
This removes dependence on transitive older validation evidence.

The bounded native dense owner and separately indexed old local gather are
assembly/representation oracles sharing the inherited native constitutive law.
For fibre, convert the independent dense left-Exp Hessian to its spatial
residual Jacobian using internal moments before nodal-load subtraction.
Generalized work corrections and cell couples follow the existing native
operators. Do not symmetrize either Jacobian or infer positive definiteness.
Preserve parity <=1e-12 for existing fixtures, and registered deformed-block
limits <=1e-9 max absolute / <=1e-11 normalized, nonzero blocks >1e-12.
Elastic actual-update FD requires at least two plateau steps <=1e-6; smooth
active fibre at least two <=1e-5. All histories/checkpoint comparisons are exact.
Use the existing frozen native scales; no unit-invariance claim from a mixed
raw norm. Two focused changed source checks pass 2/2; they are development
checks, not the installed assessment.

**Execution/terminal:** after independent contract/input review, snapshot this
matrix byte-for-byte and run `python -u run_bounded.py` once in that exclusive
installed directory. Verify actual one numerical thread, JIT off, source/wheel
and isolated imports. Enforce 600 s / 8 GiB process-tree memory and retain
native cooperative limits. Require 17 complete JUnit cases, no skip/error,
successful observed exit, scientific assertions and both small accepted-block
JSON reports. Missing inventory, mismatch, failed admission/solver, resource
breach or unresolved correctness findings leave F08 open. Preserve failures;
do not retry a consumed authority. Independent scientific/code/artifact
adjudication must accept every scoped requirement before marking F08 PASSED.
Protected historical F08-S/F08-D-v1/v2 records remain distinct, not replayed
or relabeled. No acceptance of independent material law, semismooth switch,
unbounded production size, attachment or aggregate gate follows.

- V inventory: V01, V02, V03, V04, V05, V06, V07, V08, V09, V10, V11, V12, V13, V14, V15, V16, V17, V18, V19, V20, V21, V22, V23, V24, V25, V26, V27, V28.
- B inventory: B01, B02, B03, B04, B05, B06, B07, B08, B09, B10, B11, B12, B13, B14, B15, B16, B17, B18.

V06 development evidence: the signed axial/bending/cross-energy patch and
independently derived boundary-load solves pass both offsets and three 2D
grids, with 6/6 source and isolated installed-wheel regressions on Windows.
The finest-grid force-like retained
coordinates show a 4.40e-9 scaled numerical drift. Representative
engineering-boundary centered-rib responses are now compared with executed
OpenSees cases on three grids: pure-load tip outputs differ by at most 0.1752%,
but local curvature profiles differ and a combined near-cancellation response
needs the registered absolute floor. The homogeneous 1D section formula is
not an exact oracle for that 2D model. Broader installed/platform checks,
independent mechanics review and complete V06 adjudication remain open. See
`.qualification/b3-ge-e4-pl/r8-v06-transformed-energy-dev-20260929-v5/`
`.qualification/b3-ge-e4-pl/r8-v06-installed-dev-20260929-v1/` and
`.qualification/b3-ge-e4-pl/r8-v06-centered-cantilever-dev-20260929-v3/`.

| External comparison | Status | Current boundary |
|---|---|---|
| E01 eccentric elastic panel | IN_PROGRESS | CalculiX six-row deck remains inert after an expansion-map defect. OpenSees signed point screens, including 2Ã—1/4Ã—2/8Ã—4 grids, pass link/work/wrench checks, but physical roll disagreement increases on two-direction refinement. At 8Ã—4 the external axial-load shell action replays its coupled field to 1.93e-17; the changed coupled action explains 93.6% of the roll gap at fixed native shell stiffness. Direct +100 N m torque gives a 19.0% native/external torsional-compliance difference, stable under sparse-solve correction. Four same-action torque replays show the changed coupled action explains 109.1% of that gap while the isolated external shell is slightly stiffer; physical Mx distribution dominates and Mz contributes zero on this fixture. Beam-only section compliance agrees to roundoff. Shell/point torsional-transfer cause and matched idealization remain unresolved; stop diagnostic refinement pending focused mechanics review. Formal observables/floors, accepted physical reference and independent review remain open. |
| E02 torque/footprint | IN_PROGRESS | Executed matched rigid-tip GE/CalculiX out-of-plane comparison at three in-plane levels. Finest Fz/Mx/My work differences+.148%/-.620%/+.120%; native torque convergence, solid thickness resolution and tighter balance precision open. Normal-spin/full-law equivalence not claimed. B2 public resolution guard fails; B2 accuracy untested. See development/r8-e02-rigid-tip-reference-20261001/results.md. |
| E03 curved stiffener | NOT_STARTED | No executed matched comparison. |
| E04 nonlinear GE/capacity | NOT_STARTED | No executed matched comparison. |

E01 follow-up,30 September: saved native/external torque cross-work closes
4.1554e-13; membrane/normal-spin gives102.2491% signed and plate-2.2491%.
Independent mechanics review accepts this allocation, not either engineering
idealization. Retain six-row points; require explicitly matched material-spin
work before further reference scoring. No new solve/refinement or threshold
change. [Grouped decision and raw hashes](../../.qualification/b3-ge-e4-pl/r8-e01-cross-work-dev-20260930-v1/results.md).

Known adverse evidence remains visible: F03's off-ratio mode and historical
timeouts do not select a multiplier; F05's 45 N and 42.5 N cases failed
without changing the accepted 40 N state. See the active note and
`.qualification/b3-ge-e4-pl/r8-f05-45n-ticket-dev-20260929-v1/`.
Formal F03 execution authority is unconsumed. This matrix changes no
scientific criterion, resource limit, release authority or final scope.

## Prospective F05 foundation assessment â€” 30 September 2026, v1

**Status: PASSED, scoped independent adjudication.** This Level B assessment answers whether
the selected Q4 and existing S3 full algorithmic pullbacks give the admitted
fixed-predecessor derivative, including their assembled owner composition and
one-sided yield limits. It does not accept G3 material breadth, F06 chart-history
coverage, attachments, F03, G0B or a release. Historical diagnostics, failures
and their consumed authorities remain unchanged. Revision 8 permits this new
assessment; no separate unconsumed F05 authority is recorded.

Candidate tests: `23cb71cd8d315dc536ce146ab3c165b1d6b81f49`; product remains
`0da6cd12b755ab78b9634e2a4b5b880058f2e457`. Policies are
`STIFFENED_SHELL_Q4_ALGORITHMIC_PULLBACK_V1` and the existing S3 algorithmic
pullback; the elastic-only historical variational adapter remains guarded.
Use the existing solver wheel SHA-256
`314ea0dffd9c5fa7f70b80538373e42ffd10b5083f231b69a8bd4784773b1a2d`.
All 384 wheel Python modules match the candidate source and isolated installed
site byte-for-byte. The prior [91-check evidence](../../.qualification/b3-ge-e4-pl/r8-q4-pullback-dev-20260930-v1/manifest.json)
is reused for local objective pose/work oracles, active smooth derivatives,
ownership, admission, guarded legacy behavior and selected-owner lifecycle.
Only two test files changed after that product; no wheel or consumer rebuild
is justified. This reuse does not turn its development disposition into a pass.

New inventory is **10 cases**:

- Two selected mixed Q4/S3/native-beam assembled derivatives, before and after
  an actual owned anchor reset. Accepted prefix `.5, 1`; trial target `2`, half
  Newton step plus supported axial strain `2e-5*x`; fixed shell/beam predecessors.
  Two directions, central steps `.01, .001`. Require active updating in every
  shell and native beams, stable sampled masks, nonzero multiplier curvature,
  and unchanged accepted checkpoint/predecessor bytes. Shell, beam and free-primal
  raw and work-scaled relative errors must each be <=`1e-5`; scaled constraint
  derivative error <=`1e-9`. Physical coordinate and constraint scales come from
  the unchanged owner. This unaccepted trial is not an equilibrium solution.
- Eight Q4/S3 Ã— virgin/yielded-reload Ã— elastic-left/plastic-right local limits.
  Centered unit polygons, E=210 GPa, nu=.3, t=.02, C208 100/105/110 MPa,
  plastic strains .005/.01, K=400 MPa, n=.2; Q4 three and S3 five layers.
  Independent biaxial constitutive and boundary-traction identities determine
  yield position, force and branch slopes. Outward second-order one-sided
  stencils use first-yield strain times `.02, .01`, outside the native guard and
  within the first linear hardening branch. Fixed native tolerance is `1e-10`.
  The analytically bounded stopping noise amplified by `4/h` must be below the
  unchanged derivative limit before evaluation: elastic <=`1e-6`, plastic
  <=`1e-5`. Tangent/analytic/stencil comparisons must all meet those limits;
  force, stress and strain oracles <=`1e-8`; plastic state rtol `1e-8`, atol
  `1e-12`; finite states, correct side masks and unchanged predecessors mandatory.
  No behavior inside the numerical yield guard is asserted. Earlier insufficient
  finite-difference resolution and inactive-S3 fixture failures remain evidence.

Exact inputs, six copied fixtures, runner hashes and 384-module identity are
frozen in `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-f05-foundation-installed-v1/inputs.json`,
SHA-256 `2d8c63567791cddef73e2a0b282e81a3c83c294cabcfbe8c18b7e5f6756cd2f0`.
Selected test hashes: assembled
`7a24bec72a3c07dad2dd39ff3deb74fbd8c0244538816c624ed9a989c167de77`, yield
`fd64fb14c29272d8f490bdba3733e0344735a810df1b844136ab8efaced870b8`.
Command: `python -u run_bounded.py` in that exclusive output directory.
The retained supervisor launches `run_installed.py` against the existing isolated
site, enforces 600 s and 8 GiB process-tree memory, and checks actual imports,
Python/dependency identities, one numerical thread and disabled JIT. Maximum
assembled size must remain below 100,000 rows; one heavy programme job at a time.
Baseline dependencies remain Python 3.14.2, numpy 2.4.6, scipy 1.17.1,
pytest 9.0.3, numba .65.1, ANYmaterial .2.0 at
`d8a233ef4c5e38d25dbba0eb20e6cfa8d44ec5a2`, curves SHA-256
`0d090a1ddc19bdc788a129b5b2ba9261642d05f94378cf097f7220c9ed2bd12e`;
the input record binds imported package paths and remaining dependency versions.

Retain command/log, junit inventory, ten scientific JSON reports, effective
settings, imports, supervision outcomes, failed development evidence and an
independent adjudication. A skip, missing report, identity drift, resource breach,
failed scientific predicate or unresolved review finding leaves F05 open.
Only complete evidence and independent acceptance can mark the scoped foundation
PASSED. Unaffected scientific criteria and all downstream gates remain binding.

**Disposition:** installed execution passed 10/10 with ten complete scientific
reports, unchanged predecessors and accepted bytes. Independent review found no
unresolved correctness finding; source/wheel/site, fixture and runner identities
were independently rehashed. Assembled raw/work-scaled maxima `2.29903e-7` /
`2.29414e-7`; scaled constraint `4.23963e-15`; plastic yield `1.09125e-6`;
force oracle `7.25036e-11`. One numerical thread, JIT disabled, 19.988 s,
220,020,736 bytes observed process-tree peak RSS. See
[immutable results and review](../../.qualification/b3-ge-e4-pl/r8-f05-foundation-20260930-v1/results.md).
The frozen pre-execution matrix remains `contract.snapshot.md` in that evidence;
this disposition does not rewrite it. G0B and unrelated obligations stay open.
### F08 corrected execution binding â€” frozen prospective v2, not a pass

Independent repair review by `/root/anyfem_consumer` confirms complete static
closure, 32/32 matching fixture/config hashes, unchanged prior fixture bytes
and scientific inventory, and no diagnostic execution at module import.
Namespace-package directories match source semantics. No remaining pre-run
import-closure or scope finding was identified.

V1 ran once at source `af5048ba` under its byte-exact snapshot
`9eea7ff839fef160282ff3fdf7de89814c814bd22e4c231c886576fc375a6d20`.
It failed before any numerical case: two collection errors for missing
`docs.reference_cases.ge_beam3_station_resultant_cell`. Observed exit 2,
4.120 s, 216,625,152 bytes process-tree RSS. Its directory and outputs remain
unchanged. This is an isolation-fixture defect, not scientific rejection.

V2 changes only the exclusive copied import closure, adding four recursive
`docs/reference_cases` Python modules. No existing fixture, product, tolerance,
selected case, or claim changes. V1 execution is not replayed. Run V2 once after
independent repair review under the same 17-case scientific/terminal predicates,
one thread/JIT off/600 s/8 GiB and existing native cooperative limits.
Directory: `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-f08-adapter-installed-v2`.
Frozen 32-file fixture/config manifest SHA-256
`f52a7bc425bf6151cd76eb08c1288437bfdfecbfed40ad54a9e0ecbdccde6f7d`;
installed runner SHA-256
`32ba667603700c758465e5bd201cd9192142a5701503f6b804a444f88bd7219c`;
supervisor remains `527535441e819612a59c78326a0fc5c54f091265ee126df741693d54164bba56`.
Keep V1 raw failure and initial pre-review binding correction alongside V2.

**F08 disposition:** the distinct corrected installed assessment passed 17/17,
with both accepted-block reports, 32/32 frozen inputs and zero module mismatches.
Independent review accepts scoped native local extraction only. Preserve V1's
two collection errors and yield-switch limitations; no aggregate gate follows.
[Immutable results and review](../../.qualification/b3-ge-e4-pl/r8-f08-foundation-20260930-v1/results.md).

### M2 finite BL5 development â€” 30 September 2026

Product `2d9ab38dd4037eda5ad808ffe6e4eb000b326970` adds experimental elastic
nonmatching finite load/unload, actual station-port work, rejection/cancellation,
chart rebase and distinct V11 restoration to the existing BL5 law and owner.
Source55/55. Installedv2 retained140passes/3legacy-message failures; corrected
v3 passed16/16 and both public histories(.5,1,.75,.9), exact restart and oldV7
policy. Independent review accepts combined coverage with exact exception-only
impact, not a full143-case v3 rerun. Wheel82ea8d42...,386solver/97unchanged
consumer modules bound. [Evidence and limitations](../../.qualification/b3-ge-e4-pl/r8-bl5-finite-dev-20260930-v1/results.md).

This implements a finite experimental route, not M2/F02/F03/G2 acceptance or a
multiplier-space selection. Physical transfer, growing-space stability, ratios,
material lines, complete consumers and all aggregate gates remain open.
ANYfem product7cf1fd7e and wheele3f755fe add separate experimental BL5 input
persistence, public controls and restored continuation. Installed21/21 (seven
new/fourteen historical) pass with exact artifacts and independent review clear.
This verifies experimental input roundtrip, not native-project persistence or
physical/aggregate qualification; no speedup or release claim follows.

**2 October independent development deltas:** public experimental B2 mixed
Q4/native-S3 static point panels now pass28changed-source/180installed checks,
both1/10/100 examples and historical Q4 consumer roundtrip. GeneralM3 and
S3consumer/mass/spectral/footprint obligations remainopen.
[Exact artifacts, failures and review](development/r8-b2-mixed-panel-20261002/results.md).

One CalculiX U1/US3 five-row nodal-P1 canary executes with sixU,14equations,
free/nonzero beamrootyaw, positiveMxwork and DAT-rounding-compatible rows.
This resolves all-user reference-route feasibility only; no native-half-cell,
consistent U1 trace, RFwrench, physical torque accuracy or F03acceptance follows.
Memorysamples unavailable; no numerical rerun after reporting-guard fixes.
[Exact outputs, source identities and Read review](development/r8-bl5-u1-us3-canary-20261002/results.md).

**2 October integrated consumer and reference delta:** ANYfem26cc56eb now
persists explicit mixed Q4/S3 static B2 inputs through the existing native
Project bridge. Fresh installed167/167 and1/10/100 examples pass; one eligible
factorization per batch. All98consumer/391solver source/wheel/site module bytes
match. Failed negative fixtures, actual imports/settings and independent Read
review retained. No mass/material/checkpoint or aggregateM3 claim follows.
[Consumer evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-mixed-panel-consumer-20261002/results.md).

One independent US3 same-action plate model now completes the finest native
Fy/Mx/Mz shell actions, with unchanged nodes/supports and all six covectors.
Work differences-1.07386%/-.247769%/-1.15692% exceed printed uncertainty and
establish a shell-response contribution, without unique beam/connection or
drilling causality. V2 numeric-field failure retained; V3 explicitly bounds
serialization width and records decoded action differences. No coupled physical
accuracy, multiplier selection, refinement claim or formalF03 acceptance.
[Evidence and resulting decision](development/r8-bl5-us3-same-action-20261002/results.md).

**2 October supported completion and modal delivery:** one fixed-state sparse
spin relaxation retains the saved state and passes existing controls. Completion
work is below0.1% but action/root partitions are appreciable; no causal fraction,
drilling independence or BL5/F03 pass follows. Stop completion tuning/repeats.
[Exact supported action and reviewed decision](development/r8-bl5-supported-completion-20261002/results.md).

Explicit B2MixedReferenceModalDefinition now offers experimental mixed/all-S3
virgin supported descriptor modes with native translational lumped S3 facet mass
and no S3 facet rotary contribution. Shared nodes may retain Q4 director inertia.
Final installed429/429 (262solver/167consumer), both new public examples and
free/fixed-spin dense-pencil parity pass; wheel f41f07b2...16fc0 binds391solver
modules with unchanged15eb01d0...b76f6 consumer98modules. Independent source
findings resolved; source fixture and selector failures retained. Static schemas
unchanged. New modal consumer persistence, physical continuum/spectral accuracy,
free-free/prestress/footprints, full F07/F12/G4B/M3/M4/G6 remain OPEN.
[Implementation, exact artifacts and limits](development/r8-b2-mixed-reference-modes-20261002/results.md).

**2 October mixed reference-modal consumer:** ANYfem cabb6ed persists a distinct
experimental modal-only Project input schema. Installed224/224 and mixed/all-S3
save/reopen examples pass with one factorization each. Solver public Q4 policy
alias is a thin unchanged identity, wheel80ca5f5e; consumer93b21a20. Source failure
and focused repair retained; independent Read review clear. This closes the
development input/persistence slice, not physical spectral accuracy, F07/F12/G4B,
M3/M4/G6, external comparisons or complete acceptance.
[Exact installed artifacts and evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-mixed-modal-consumer-20261002/results.md).

One pinned CalculiX US3 plate modal canary returns6 ordered frequencies and
complete six-coordinate fields, with nonzero bending rotations. This resolves
modal observable feasibility; matched native comparison, convergence, actual
reference eigen-residual, physical spectral accuracy and G4B remain OPEN.
Failed NaN decoder control, review guard repairs and actual execution/settings
are retained. No formalF03 consumption or aggregate acceptance.
[Exact bounded canary and next decision](development/r8-b2-mixed-reference-modes-20261002/results.md).


**2 October shell pressure development (G4A remains OPEN):** typed native Q4/S3
reference pressure and current-surface follower candidate exists. Source checks
pass full Q4/all-S3 follower cancellation/restart/rebase/continuation, but mixed
follower remains FAILED at its original component-equilibrium threshold. Finite
S3 enhanced reference-dead work remains NOT_IMPLEMENTED, explicitly rejected.
No installed pressure verification or complete pressure acceptance. Local stable
fit correction641e05bb has48source checks and independent scoped review; pressure
trial-merit choice has separate independent review and unchanged commit limits.
[Current evidence, failures and next discriminator](development/r8-ge-pressure-work-20261002/status.md).


**2 October pressure consumer milestone:** ANYfem095b60c adds strict pressure input
and native Project persistence/dispatch.119source+119installed adapter checks and
2source+2final installed Q4 full workflow/cleanup checks pass. Exact wheel pair
ac2ea592...5199772 solver/a2739821...59a0e09 consumer,396/98modules,281onsiteimports.
Real Project route covers cancellation0.25, disk restoration and identical0.5/1
continuation. Source reviews complete within this experimental scope; no release.
Mixed follower still FAILED and finite S3 enhanced-dead still NOT_IMPLEMENTED;
no aggregate G4A/G6 acceptance. Evidence lives in ANYfem docs/development/
r8-ge-pressure-consumer-20261002/results.md and raw-v1.zip.

**2 October finite S3 dead-work decision:** native reference pressure does not
uniquely specify a finite enhanced surface. Full-log lift failed an unchanged-
director drilling-work test; evidence retained. A director-only tilt revision
passes11 distinct local consistency/physical-screen cases and2 existing owner
rejection checks. Independent Read review supports further private validation.
No public admission: internal finite-kinematics compatibility and matched physical
work remain open; mixed follower failure unchanged. G4A remains OPEN.
[Bounded derivation, decision and evidence](development/r8-ge-pressure-work-20261002/s3-dead-work-candidate.md).

**2 October explicit director-pressure integration:** separate experimental
reference_dead_director_v2 owns full work/tangent/rotation-anchor recovery and
versioned descriptor/checkpoint policy. Nonuniform manufactured bending and actual
owner derivative checks pass; independent source review clear within development
scope. Both finite histories still fail original component assessment with no
commit. Pressure-vector assessment amendment awaiting user decision; private
counterfactual lifecycle success is not acceptance. G4A remains OPEN.
[Current implementation, failures and decision](development/r8-ge-pressure-work-20261002/s3-director-integration.md).

**2 October signed distributed programme (G4A remains OPEN):** experimental
GEBeamDistributedProgramme supplies absolute signed native densities at positive
programme positions, with distinct identity, cancellation and durable restart.
Installed elastic5 checks and simultaneous shell/fibre signed-history case pass
on wheelb636e6a8; independent source/evidence review found no blocking defect.
Negative-load activity at1.75/2 is recorded. Zero-total-load convergence still
fails unchanged relative assessment; accepted-prefix preservation is tested.
No consumer, mixed/S3 staged, zero-load or aggregate qualification claim.
[Evidence and remaining scope](development/r8-ge-native-distributed-20261002/staged-programme-results.md).

**2 October programme consumer/mixed-shell continuation:** two elastic mixed/all-S3
signed restart/balance cases and the runnable signed public example pass source
and installed checks using unchanged solverb636e6a8. ANYfem's new experimental
programme schema and Project/cancellation/disk-restore route pass139source and
139installed checks on consumerc67232b6. Root reviewed worker changes. Mixed/S3
plastic histories and zero-load convergence are not established; G4A/G6 remain open.
[Updated evidence](development/r8-ge-native-distributed-20261002/staged-programme-results.md).

**2 October mixed/S3 signed material histories:** source/installed tests extend the
same two-stiffener distributed programme to mixed Q4/S3 and all-S3 shells. Both
installed paths pass cancellation, restart, reversed loading and exact checkpoint
parity. Mixed activity is Q4+fibres with elastic S3; all-S3 activity is S3+fibres.
An observation-only ragged-array failure is preserved and corrected by keyed
native station comparison, with16helper checks and independent source review.
No numerical equations/criteria changed; aggregate G3/G4A remain open.
[Evidence](development/r8-ge-native-distributed-20261002/staged-programme-results.md).

**2 October continuation â€” signed couples/materials:** Q4 +/-100Nm/m couples
combined with +/-3000N/m forces pass source/installed cancellation, reversal,
physical recovery and exact restart; simultaneous J2/fibre activity is observed.
Unchanged wheelb636e6a8. This closes this scoped history check, not full combination
coverage, torque accuracy or G3/G4A. [Evidence](development/r8-ge-native-distributed-20261002/staged-programme-results.md).

**2 October connection reference decision:** source-derived U1 polynomial beam
trace has a different supported constraint kernel from the saved nodal-P1 canary.
Local energy/source-stiffness error1.495e-16; explicit old-kernel witness passes.
Independent OpenAI Read review found no blocking algebra error. Retain canary as
feasibility only. US3 trace and physical/native equivalence remain open; no external
rerun or F03 consumption. [Derivation](development/r8-bl5-u1-us3-canary-20261002/results.md).

**2 October reference disposition after0888da71:** US3 P1 physical trace and full
reference-linear work maps pass bounded rigid/wrench checks. A separate analytical
cantilever check finds the actual U1 discretization11.1423% below physical
Timoshenko tip-force compliance, despite pure-moment agreement. Independent Read
review confirms the limitation. Do not promote a corrected U1/US3 deck to matched
shear-reference status; no new external solve/refinement is warranted by these
checks. No native formulation rejection, acceptance relaxation or F03 consumption.
[Source, raw checks and decision](development/r8-bl5-u1-us3-canary-20261002/results.md).

**2 October objective-Q4 BL5 staged slice:** explicit algorithmic-Q4 policy now
admits elastic Q4 BL5 and staged translation forces. Source/installed3checks pass
signed stages, cancellation, restart, physical balance and P0 adaptive/chart path;
5focused compatibility checks pass. New wheel d506e3f3...14be90. Historical-policy
moment failures retained; its staged scope remains rejected. Independent review
clear within experimental scope. No M2/F03/G4 physical acceptance or criterion
change. [Evidence](development/r8-bl5-staged-loads-20261002/results.md).


**2 October BL5 consumer slice:** ANYfem8c411ec adds explicit objective/staged
BL5 inputs and distinct native Project persistence through public solver types.
49 source and70 installed checks pass; wheel f591ca10...d54ea7 paired with
solver d506e3f3...14be90. Cancellation/rebase/checkpoint continuation and historical
format regressions pass. Review found no consequential issue in this scope.
Implementation/test evidence only; no aggregate G2/G6 or physical acceptance.
[Evidence](development/r8-anyfem-bl5-project-20261002/results.md).


**2 October BL5 distributed-load integration:** objective elastic Q4 BL5 now
uses existing native force/couple and signed-programme operators. Both tested
line bases pass work/lifecycle and actual-update derivative checks; additional
mixed point/line scope is covered after independent review. Eleven installed
checks pass on wheel dd8ce52c...954cc74; all 398 module bytes match. Failed initial
test-fixture run is retained. No mechanics, tolerance or checkpoint-policy change,
physical acceptance or F03 consumption. ANYfem distributed-BL5 persistence remains
open. [Evidence](development/r8-bl5-distributed-20261002/results.md).


**2 October distributed BL5 consumer:** ANYfem330cb22 preserves strict fixed
force/couple or programme descriptors through standalone and native Project
records.17 source and53 installed checks pass on consumer091b5d74...c66b786 /
solverdd8ce52c...954cc74; unchanged historical formats, cancellation/chart/restart
and exact continued state verified. Independent review clear within this bounded
scope. Full G4/G6 and physical BL5 acceptance remain open.
[Evidence](development/r8-anyfem-bl5-distributed-20261002/results.md).


**2 October generalized-material BL5:** explicit experimental elastic-Q4 /
generalized-beam material policy and distinct history schemas implemented. Eight
installed checks pass, including yielded history and legacy compatibility.
Low-hardening1e6 convergence failure remains open; bounded1e8 evidence does not
qualify the material envelope. No aggregate G3 or F03 acceptance.
[Evidence](development/r8-bl5-material-20261002/results.md).


**2 October generalized-material BL5 consumer:** ANYfem eaed5ec adds strict v3
records and Project round-trip.4 source and17 installed checks pass, including
both line bases with yielding, cancellation, rebase and exact restart.98 consumer
and398 solver module identities verified. Experimental implementation only;
low-hardening failure, full G3/G6 and physical BL5 acceptance remain open.
[Evidence](development/r8-anyfem-bl5-material-20261002/results.md).


**2 October coupled Q4-J2 / generalized BL5 candidate: IN_PROGRESS.** P0
monotonic simultaneous yielding/restart source smoke passed; full signed reversal
failed near-500N; coarseP1 did not shell-yield at500N.3 ANYfem source checks pass.
Candidate uncommitted; no installed/aggregate/material-envelope acceptance.
[Preserved candidate/failure evidence](development/r8-bl5-coupled-material-20261002/results.md).


**2 October coupled candidate update:** native retained-role scaling corrected only
for this new policy with a distinct model identity. Five selected installed checks
pass on wheel87146a8c...bec6410, including monotonic simultaneous material lifecycle
and legacy isolation. Full signed reversal still fails; coarseP1 shell-yield
coverage remains absent. Tangent sensitivity is observed, physical instability is
not established. Status remains IN_PROGRESS, not accepted. See the same evidence
record; previous failures and source versions are preserved.


**2 October displacement-control foundation: IN_PROGRESS.** A private sparse
bordered corrector reaches an uncommitted equilibrium on the saved coupled branch
at-487.841N and preserves the accepted checkpoint. Four source checks pass.
Full predictor/fixed-displacement corrector contract independently reviewed.
No public controller, checkpoint publication, force-reversal completion, limit
point or G4 acceptance is claimed. Next: atomic publication and distinct restart.


**2 October displacement restore foundation:** separate signed-amplitude snapshot
framing and isolated mechanical endpoint validation implemented privately.
Eleven source checks pass including yielded-state replay and corruption rejection.
Atomic controller publication/public restart, independent review and installed
checks remain open. No G4 or full signed-reversal acceptance.


**2 October seeded displacement workflow:** typed public solve/recovery and
separate mechanical/controller restart delivered experimentally for coupled-Q4
BL5.15 installed checks pass, including rebased seed, cancellation, atomic failure,
exact restored continuation and force-route compatibility. Review findings fixed.
Full material/capacity, adaptive/rebase/selected recovery and consumer obligations
remain open; no -500N force-endpoint or G4 qualification claim.


**2 October adaptive displacement integration: IMPLEMENTED_NOT_QUALIFIED.**
Signed bounded cutback, failed-work accounting and durable spent budgets now run
through the public coupled-Q4 BL5 owner. Source8/installed23affected checks pass;
review fixes observer-after-commit handling and domain-rejection accounting.
Cancellation/restart and failure before first displacement acceptance are covered.
The -68um branch failure remains unresolved; no reversal/capacity acceptance.
Installed artifact and limitations: [results](development/r8-bl5-coupled-material-20261002/results.md).


**2 October selected finite recovery: IMPLEMENTED_NOT_QUALIFIED.**
GERecoverySelection selects ordered model nodes and accepted material records
without element evaluation/history replay; returns detached arrays and explicitly
labelled support coordinate covectors. Installed8checks cover coupled force/
displacement restart, ownership, unavailable IDs and legacy footprint selection.
No full-storage reduction or performance claim; no aggregate gate closes.
[Evidence](development/r8-selected-recovery-20261002/results.md).


**2 October displacement chart events: IMPLEMENTED_NOT_QUALIFIED.**
V1 remains unchanged when no chart event exists; V2 records positive chart events
separately from accepted displacement steps. Rebase retains physical endpoint,
loads, accepted material arrays and predecessor histories, and adaptive budgets.
Restore validates by replay then installs saved accepted histories exactly.
Source9checks passed; installed evidence and continuation parity are recorded in
[results](development/r8-displacement-rebase-20261002/results.md). No aggregate
F06/G3/capacity gate closed; no failed branch campaign was repeated.


**2 October generalized branch-event trial: private prototype, NOT QUALIFIED.**
Previously failed-68um endpoint reached within unchanged20/12limits and physical
tolerances; accepted prefix unmodified.9installed checks pass. Extra22cell responses
are counted separately from13global evaluations; no speedup claim. Public policy/
restart integration and the broader path remain open. No aggregate gate closes.
[Exact evidence and limitations](development/r8-branch-event-20261002/results.md).


**2 October public branch-event policy: IMPLEMENTED_NOT_QUALIFIED.**
Explicit selection from force seed, V3/ANYSSDCA2 compatibility, failed versus
accepted event-work counts, rebase and exact continuation now integrated.
35installed solver and2installed ANYfem checks pass. Public -66/-68um route
reproduces the private endpoint and restarts exactly. No later physical targets,
full reversal or aggregate qualification. [Evidence](development/r8-event-public-20261002/results.md).


**2 October cached generalized-beam recovery: IMPLEMENTED_NOT_QUALIFIED.**
BL5 material force/displacement results expose typed native station strain,
resultants, accepted plastic state, endpoint stored-energy density and last-step
dissipation density. Selected recovery is ordered/detached and executes no
constitutive update. Rebase preserves previous increment dissipation; restart
retains the saved accepted state. Constitutive identities and lifecycle are
covered by installed checks. No full material-range, global-energy or aggregate
scientific gate closes. [Evidence](development/r8-generalized-recovery-20261002/results.md).


**2 October public physical arc lifecycle: IMPLEMENTED_NOT_QUALIFIED.**
Existing owner now supports fixed-mesh Q4-J2/generalized BL5 tangent-plane
continuation, bounded cutbacks, cached recovery, atomic predecessor-bound commit,
and distinct restart with cumulative attempts/fixed-seed amplitude. Two-step
cancel/restore/continue passes on installed artifacts. Source23passed;
installed v3 27passed/1fixture failure, final v4 affected2passed with unchanged
unaffected module identities. No G4D, first-limit-point, stability, mesh-metric or
ANYfem arc qualification. [Evidence](development/r8-arc-public-20261002/results.md).


**E04 preparation, 2 October — geometry only, external comparison NOT_STARTED.**
Executable stiffened-roof candidate and four geometry/reference-measure checks
identify the prerequisite: curved elastic Q4/full-pose-point admission, followed
by elastic point arc lifecycle. The current flat guard remains. No equilibrium,
limit load or external reference executed; bare-roof values are not inherited.
[Definition and next seam](../reference_cases/stiffened_shell_e04_roof.md).


**2 October curved elastic point prerequisite: IMPLEMENTED_NOT_QUALIFIED.**
Explicit planar-Q4 curved-reference admission, existing generalized elastic B3,
translational dead loads, finite stepping and exact restart pass installed checks.
44 tests include legacy controls and honest zero-commit rejection of the failed
0.1 N control; positive curved path is 10–30 N. No E04 solve or gate acceptance.
[Scope, failure and artifact](development/r8-curved-reference-20261002/results.md).
