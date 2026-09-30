# D1 development review notes - 30 September 2026

These are early development assessments, not independent capability acceptance.
No frozen or consumed evidence authority is renewed.

## Preparation and instantaneous gap cost slice

Read-only reviewer: `/root/candidate_budget`; integrating author: `/root`.
The private preparation sink is fresh for each synchronous manager construction,
populated only after valid admission, then consumed immediately. No global model
cache or pose reuse. Existing work maps, polarity, reference geometry, resource,
initial penetration and D1 coverage checks remain.

Projected-prism pruning is valid for instantaneous overlap-local bounds. Physical
Q4 points project into the convex hull of projected corners along the kernel's
corner-plane normal. S3 points are convex combinations of target corners. The
full target-depth prism contains every matching projection, even at non-nodal
normal separation. Varying source normals affect gap after overlap eligibility.
Empty candidates mean no represented instantaneous surface overlap, not a swept
crossing guarantee. Swept code is unchanged.

The reviewer identified an early-return defect for singleton side selections:
remote degenerate geometry could be pruned without validation. The shared face
checker now validates before returning; the explicit singleton control passes.
[Seven focused checks](d1_preparation_reuse_checks_v2_20260930.log). Initial new
fixture failures from omitted derivative tolerances are retained in v1.

[Same-pose profile](d1_radial_preparation_profile_v4_20260930.json): residual is
exactly equal to v2, gap-gradient relative discrepancy1.14e-16, count1772.
The first-order zero-weight prototype remains available but disabled by default
after its profiled cost exceeded batched Jet2. Prototype derivative/activation
checks remain development evidence.

[Complete cycle comparison](d1_preparation_cycle_compare_v8_20260930.json): all
eight saved displacements, pressures, source/target wrenches, gaps and generalized
reactions are exactly equal. One elapsed comparison234.35 to216.71s and memory
375.71 to416.01MB does not establish a reliable twofold route or memory improvement.

## Spatial force-bin and reaction-work recovery

Read-only reviewer: `/root/radial_observables`. Source-bin helper author:
`/root/candidate_budget`; wrench helper/runner author: `/root`.

Within fixed XY, zero-director, complete-coverage and whole-face source bins,
the actual conversion `(ns.n0)*nt_z/(nt.n0)`, projected/reference measure,
two-sided slope allowance and pair work `p.dW-(p*g).dS` are consistent with the
nodal-force formulation. Numerical quadrature errors are estimates, not interval
certificates. A production-bin claim requires measured production comparison,
per-bin uncertainty/conversion budget and summed-bin parity with independently
reassembled source Fz. `not_checked` remains missing evidence. No target-bin or
moment claim follows from this source-bin helper.

The reviewer identified cancellation in combined source-plus-target wrench checks.
The corrected helper projects the joint constrained reaction once, then partitions
nodal work by disjoint covering body selections. Each body's physical certificate
wrench is transported to the same origin; balance, conversion and structural
defects each enter the retained1e-6 predicates. The equal/opposite defect control
now detects the error that the global sum hides. [Ten focused checks](d1_guided_wrench_body_checks_v3_20260930.log).
Follow-up read-only review found no remaining mathematical/scope blocker in these
new body checks for the saved zero-rotation radial fixture. Actual saved-pose
measurements and final independent assessment remain required.

## Prospective radial assessment review

Read-only reviewer: `/root/radial_observables`; no new numerical runs. The
fixed guided fixture and its declared scales are usable, but emitted diagnostics
alone cannot establish its spatial predicates. The final assessment must require
complete finite evidence, measured physical source bins, per-bin uncertainty and
conversion budgets, same-state source force parity, source displacement, moment
and resultant-position predicates, independent gap and per-step complementarity.
Contact action/reaction needs its own force and moment predicates; recovered
support reactions can otherwise compensate a nonzero contact net wrench.

The physical position may be explicitly defined as the moment-equivalent wrench
point at z=0, x=Ox-My/Fz and y=Oy+Mx/Fz, above the registered force threshold.
Retain the residual vertical couple and full moment check; this is not a pressure
centroid. The matched saved linear QP may assess observed final-state nonlinear
discrepancy after checking identical fixture data and independently reassembling
its equilibrium/complementarity. Include measured discrepancy and reference,
quadrature and conversion uncertainty in the unchanged 0.2% budget. This finite
comparison is not a uniform nonlinear error bound or a general shell admission.
No claim-bearing source/specification freeze has occurred.

## Conservative affine swept search

Kernel author: /root/candidate_budget; owner integration: /root; independent read-only reviewer: /root/radial_observables. The Bernstein enclosure uses the parent corner projection normal over the complete affine corner path, with outward coordinate boxes and endpoint/child error enclosures. All original parent and physical-corner angular/polarity guards remain over every target; union coverage and global geometry checks remain outside pruning. Unresolved bounds fall back to exhaustive enumeration; invalid geometry rejects the proposed path. No endpoint-only search certificate is used.

Independent scrutiny found no concrete blocker in this restricted development path. Twenty-one distinct kernel checks, fourteen owner/rounding checks and a separate old-checkpoint rejection check pass. Contact restart now binds affine_union_outward_swept_search_v2 on overlap_local_dev. This is development review, not capability acceptance.

The identical saved admissible path measured154.13 to52.66s, with swept calls41,472 to968 and their kernel cost109.00 to7.39s. Endpoint gap and coverage costs are unchanged. [Before](d1_radial_saved_swept_profile_v6_20260930.json), [after](d1_radial_saved_swept_profile_v7_20260930.json). Full coupled v8 subsequently completed2/2 in891.87s/570.46MB; this establishes bounded executability, not a twofold whole-route speed claim.

## Closed reference-uncertainty and assessment findings

Saved-reference helper author: /root/candidate_budget; read-only reviewer:
/root/radial_observables. Reference v2 incorrectly used a componentwise contraction
bound without component coupling and omitted coefficient-error times solution-error
from inactive-gap propagation. Preserve v2 and aggregate v11 as unsuitable for
uncertainty claims. V3 uses `b + eta*max(b)/(1-eta)` and
`(abs(G)+gap_error)@u_error`. The original49-mode branch, observable values and
positive sign margins remain; checked contraction is3.29058e-10. Force uncertainty
is1.87829e-7N. Three affected focused checks pass. Review found no remaining
concrete blocker in those changed equations for this fixed fixture; this is not a
uniform nonlinear-model error bound or capability acceptance.

The aggregate assessor now rejects NaN/infinite physical gaps before penetration
conversion, wrong force/moment scales or origin, and scalar moment broadcasting.
Four gap and four scale/shape controls pass. Physical-bin assessment includes the
independent exact-disk arithmetic estimate. Data-only v12 passes34 predicates;
independently accepted and released remain false.

## Closed actual-path admission finding

Author: /root; read-only reviewer: /root/radial_observables. The previous physical
prescribed-normal guard considered model constraints but omitted solve-path
controls. A rank-aware SVD now projects the physical normal covector onto the
actual free span after `controls@T`; both monolithic and nested path branches
supply those rows. Source-only prescription rejects; target-only, dependent,
coupled and zero-row controls preserve the appropriate source freedom. Seven
focused checks pass. D1 restart binds `model_and_path_constraints_v2`, so old
D1 checkpoints intentionally reject under this candidate. Review found no
concrete blocker in these changed lines. Contact equations, geometry derivatives,
structural solve coordinates, public signatures and no-contact defaults are
unchanged; the radial fixture's active interior modes remain physically free.
The retained measured fields remain development evidence under their recorded
source identities. Final qualification requires a prospective source/specification
freeze and actual current-artifact execution; no historical run is regraded.


## Installed force lifecycle and complete normal work

Independent reviewer /root/radial_observables verified all442 frozen hashes and433
installed source files, full8-pose body/gap/director/source parity and actual active2
and open6 forks. Both restart comparisons have ALL11 gates true, zero field/state
and diagnostic differences, exact raw prefix provenance, actual installed imports
and resource compliance. Scoped PASS for .018N/.04m/4x4 force workflow; globalD1 open.
Two namespace invocation failures occurred before numerical work and remain retained;
adding worktree root AFTER installed target fixes helpers without using solver/src.

Reviewer found that scalarz error is mortar-force-coordinate error, not structural
nodal work. Frozen original independentKKTproducer remains unchanged. New wrapper
measures -zDgbar at the respective two poses for every authoritative DOF, including
both bodies/rotations, at h=(1e-7m,1e-5rad) and half values. Normalized difference
9.2477e-8 and FDchange2.3677e-11; proposed .04N/.04Nm relative norm retains
1e-6 gate and charges FDchange<=1e-7. Active-support branch filtering is valid;
excluded faces carry identically zero active pressure basis. Helper roundoff
consistency failure (scaling operands before subtracting) retained, corrected
without numerical rerun. Finite positive pose norm and exact discrete identity
controls added following review.44 controls now pass; formal source/input freeze
and independent evidence disposition still required for this reference row.

## Reporting-cost discriminator after formal radial timeout
The formal radial V2 invocation exhausted 900.074s/568.14MB; no complete result.
Its last traced NCP at349.568s and prior successful v8 tail of540s distinguish
solver iteration from untraced recovery/reporting. One bounded saved-v8 final-pose
experiment compares the exact installed87c boundary predicate with a single
in-memory patched padded-box predicate, same prepared manager/pose/pressure.
Question: is remote point-segment work the reporting bottleneck, and does skipping
only provably distant boxes preserve complete force/certificate/branch counts?
The full projected-face validation and overlap evaluation remain exhaustive.
One experiment at900s/4GB, no Newton advancement or pressure/mesh tuning. Exact
parity and meaningful reduction lead to a new installed candidate and affected
spatial run; failure gets one classified correction. This cannot establish a
whole-route speedup or revive the consumed formal authority.


Saved-report probeV1 ended78.785s/263.08MB after its original report, then failed
while serializing a NumPy boolean. This is a helper failure and yields no complete
parity/cost assessment. V2 uses the same saved pose with explicit NumPy scalar
serialization and checkpoints preparation. Reviewer identified a valid subnormal
projection-fraction exception with normal edge lengths; strict NumPy raise policies
now retain the old segment loop.21 controls across two focused invocationsPASS.
The original4ae probe snapshot is archived; currentproductionA1D960C3 changes only
that strict-policy fallback. No contact equation or scientific tolerance change.

## Remaining tail discriminator
Saved reportingV2 preserved all2028force components and complete certificates;
38.925->33.998s (12.66% local), not the540s untraced tail. Reviewer identified
repeated Q4 accepted-response replay in final sealing, semantic validation and
checkpoint validation. One saved-state profile now measures exact sealing on a
disposable canonical432-state payload at the exact saved final pose/model, with
full input/output payload hashes and all normal validation calls intact.
Hypotheses: replay/sealing dominates, or this canonical stage is cheap and cannot
explain the original pre-seal tail. One900s/4GB profile, no Newton/mesh sweep.
Large replay cost supports sharing immutable same-input evaluation work while
retaining all validations; small cost points to the remaining original driver
stage. Saved canonical versus packed-input distinction limits inference.


## Checkpoint tail correction after SpatialV5
SpatialV5 on590d exhausted900.048s/596.00MB during checkpoint creation.
Observed checkpoint_begin428.014s; seal0.730s, recovery1.178s. No result
or postcheck authority consumed. This localizes at least472s to checkpoint.
Question: repeated full model scans while normalizing exact dicts versus model
fingerprint/semantic validation. Minimal candidate skips ONLY exact dict/exact
str-key mapping observation; every member and all outer lifecycle/semantic
checks remain. One bounded saved-state normalization comparison and focused
adversarial controls decide promotion; no mesh/pressure/tolerance change.

Saved canonical normalizationV1 completed50.431s/183.36MB, old48.223s/1307
full scans versus new0.114s, exact complete bytes. Thirteen focused controls
pass. Committed90baf01a installed433files match, only nonlinear_restart differs
from590d. Complete new-installed48-state active2/open6 checkpoint joins pass
35.829s/251.77MB with exact original/produced/reconsumed canonical hashes.
Independent read-only review closed that serialization boundary. SpatialV6 is
issued once with unchanged35criteria/900s4GB and coarse tail trace.

## SpatialV6 failure and checkpoint cost decision
V6 exhausted900.077s/570.73MB, checkpoint_begin525.788s, no complete result.
One unchanged saved active/open cProfile diagnostic completed79.011s/268.90MB
with complete canonical parity. Repeated full lifecycle guards consume63.992s
of78.526s; immutable authority signing consumes21.600s/12.38million calls.
This rejects sealing/contact recovery as the main checkpoint explanation.
Question: can proven immutable signature subtrees be reused without bypassing
live mutable/module authority or custom observations? One bounded source slice
and saved-input parity/mutation controls decide; no further coupled solve before
the remaining cost is measured. Cache eligibility must prove exact inert types,
strong ownership and finite retention. Unsupported/mutable branches stay live.

## Complete saved radial checkpoint preflight (development)
The local signing/array slice preserves complete active/open canonical roots.
Profiled route79.011->67.427s is developmental and not a solve speed claim;
final conservative lookup proof has scoped independent no-blocker. Final controls
are20/21 with one fixture construction defect, then repaired1/1; prior fixed-slot
signer controls and authority checks remain unaffected. Keep all raw failures.
Question: does the final source complete the432-state/2028-DOF producer plus
normal consumers at a cost that supports another spatial candidate? Competing
outcomes: producer cost fits the observed525.788s pre-checkpoint margin, or
live model scans still dominate and another solve would be premature.
One saved developmentv8 root, no equilibrium solve, no state stripping/bypass;
reconstruct exact12/-.113/1.297 model and complete original contract. Exclusive
command/source/input identity is in d1_checkpoint_radial_cost_v1_20260930.inputs.json.
Run d1_saved_checkpoint_roundtrip_dev.py --radial through source entry wrapper,
900s/4GB, alone. Preserve full canonical byte/hash parity, all432states and2steps.
This cannot substitute for failed SpatialV6 or authorize its four postchecks.
Radial costV1 rejected43.119s/207.42MB beforeconsumer/producer: modelidentity
matches, reconstructed analysiscontract does not. This is not checkpoint cost
or spatial qualification. Bounded source-history comparison must identify a
specific missing field versus genuinely changed definitions. No override/retry.
Final source review closes rawnamespace/property/metaclass callback gaps:
signerAEC299D8 / normalizer67EE3A63. Focused lookupV6:20PASS/1fixture-setupFAIL;
corrected malformed fixtureV7:1PASS, production unchanged. Preserve all failures.

## Owned-node observation correction and bounded cost comparison
RadialV1 incompatibility is genuine: old0dcb/v8 lacks current path-normal
admission revision and binds older swept certificate. No override or retry.
Currentmodeldescriptor full scans remain the largest savedcheckpoint cost.
The exactbuilt-in Node coords kernel is only np.array([self.x,self.y,self.z]).
Prove its live raw class/dictionary/function/code/default/global dependencies,
primitive stored coordinates and eight NumPybindings; then its coordinate and
DOF field reads cannot execute caller code. Other nodes/callbacks stay guarded;
DOF conversion and all outer/semantic checks remain.13 focusedcontrolsPASS;
oldfixtureconstructionfailures preserved. Capture builtinDOFgetter identity.
Question: does this remove enough quadratic guard repetition to justify the
next integrated same-mechanics run? One balanced savedactive/open comparison
against installed90baf, complete48-state/300-DOF bytes/hash, each180s/1GB alone.
Named outputs d1_checkpoint_owned_node_pair_v1/v2_20260930_{baseline,candidate}.*.
Select thisone candidate if measuredcost and review justify it; no more oldradial
or pressure/mesh tuning. No scientific or installedartifact promotion follows.
Balanced C/B/B/C savedcheckpoint runs pass complete48state active/open parity.
Median32.036633s baseline90baf ->22.946590s sourcecandidate; peakmemorymedian
252.15->249.18MB; combinedproducers15.043383->8.172893s. No fullsolvespeedclaim.
Selectthiscandidate, stoplocaltuning. Nextnewwheel/checkpointjoin and one same
35gate spatialcandidate900s4GB; no reuse of incompatiblev8 or V6authority.

## Resume 0b2ac9be installed closure
Build/install completed; all433 source/wheel/target Python files exact, wheel
97c3f4ca49c7b82a7efc06f03fdae9e2051126814faed8be34f56605b7e7867d.
Paired saved-route independent review supports full-root parity and measured
28.37% median decrease only. No more local optimization. Old radialv8 identity
is genuinely incompatible; no helper omission or hash override. Question for
the next bounded spatial run: does the measured checkpoint reduction allow the
unchanged35-criterion candidate to complete under900s/4GB? A successful result
permits its missing postchecks; failure is classified from the preserved coarse
trace, never interpreted as mechanical failure from timeout alone. Installed
checkpointV2 precedes SpatialV7. Fresh12-pair Q4 named no-contact timing is needed
for the changed signer; unchanged genericBeam previous timing is impact-reusable.
Prospective freezes: checkpointV2SHA9676a762c9e4226efbd8cf5dd7b44cb132f378af3bd1497cd8acfa5b142285b7;
SpatialV7SHA2d7f03bfff38d7908230764c54fd3302646e33fa9293f826e2e201cd89244313;
Q4SHA5f5851932c4b1ee22882bb202435eb6a24c3ffab8ac6688983f403c21b174bbc.
Separate prospective reviewer disposition required; historical consumed freezes
and all failures retain their original meaning. Source clean, prior dirty ownership preserved.

## SpatialV7 completed producer
Installed0b2 radial run completedexit0,733.1186719s/568.045568MB under900s/4GB;
2acceptedsteps/fullcheckpoint available. Checkpoint began541.0724659s and ended
728.2847239s,187.2122397s. PriorV5/V6timeouts remainNONPASS; this is completion
of the new candidate, not a trustworthy complete-solve speedratio. Four frozen
postchecks now eligible only on thisV7result. Wrench issued27547; others unissued.

## SpatialV7 completed postchecks / installed handoff issue
All4postchecks completed under180s/1GB: wrench88.553s/416.829MB, physicalbins
103.933s/426.238MB, linearreference5.549s/201.294MB, aggregate1.439s/159.379MB.
All35criteria true,0remaining; uncertainty-accounted binL1.9302935%,L2.9535883%,
targetmaxsample1.8872555%, independentgap.124422micrometre<=50micrometres.
Independent adjudication pending. Package impact normalized with src prefixes:
exactly3/433 changed since87c: e4_pl_s3_state, nonlinear_restart,
general_contact/s3_patch_augmented(touchbounds590d). New installedprefix2 public
solve fills specrow6 without repeating unaffected8pose science. Helper/source
review no-blocker forfreeze94a7b196; prefix issued58354 alone at180s/1GB; comparison
unissued untilcomplete. No8pose0b2execution claim or release.
