# B3-GE / E4-PL stiffened shells: Revision 8 development plan

**Status 4 October 2026: planning update adopted; explicitly resumed by the user.**
This is the current Revision 8 development basis. The user delegated pending
planning decisions; those decisions are recorded below. This edit authorizes
no numerical run, product edit, formal F03 execution, merge or publication.
The companion [goal](B3_GE_E4_PL_REVISION_8_GOAL.md) defines the objective,
decision rights and completion conditions. These two documents in
`C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001/docs/agent_plans/`
are canonical. The older worktree paths are forwarding references, so the
existing goal link reaches this basis without maintaining competing copies.

This is a development plan, not mechanics qualification. Review it against the
live worktree before relying on source-specific statements; later evidence does
not retroactively change a frozen registration.

## 0. Basis, precedence and change of route

The principal objective remains native B3-GE / E4-PL multi-element stiffened
shells. The separate physical B2 option remains mandatory. Deliver useful,
explicitly experimental milestones while completing the full programme.

Use these authorities without copying their history into new plans:
- [Complete programme](B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md): G0–G6,
  F01–F13, V01–V28, B01–B18, quantitative tolerances, required engineering
  applications, external comparisons, scale and final delivery.
- [Active state](B3_GE_E4_PL_ACTIVE_STATE.md): actual delivered behavior,
  failures, exact paused source ownership and next action. Scheduling in this
  update supersedes earlier next-action lists; historical outcomes remain valid.
- ANYopenSoft/governance/ECOSYSTEM_PHILOSOPHY.md:
  ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1, revision 2026-09-24.2.
- Historical registrations and execution records: immutable for their original
  candidates and claims. This plan amends prospective work only.

**Prospective transition:** use ordinary Level-A development, one concise
acceptance contract per milestone with any necessary linked case tables, and
the existing living note and acceptance matrix. Experimental releases may occur
before the complete programme; production acceptance still requires M5.
Section 9 explicitly records scientific and delivery amendments. All other
programme obligations remain.

A milestone has separate states: development, implemented, acceptance passed,
release-ready and released. The first executable vertical slice is an
implementation checkpoint: it needs focused correctness checks and truthful
experimental admission, but need not wait for the milestone's complete
acceptance package. Producing a usable development artifact is progress even
while acceptance or publication awaits. It does not establish acceptance.
No publication, merge to main, changed legacy default or release is authorized
by this document alone.

## 1. What exists and what is preventing completion

Reviewed preceding solver HEAD `adc98d4b`, branch `codex/stiffened-main-reconcile-20261001`,
in the canonical worktree above. ANYfem is at `6013db0` (product `9b7482b`) in
`C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer`. The four-file
consumer slice now has 42 source/42 installed checks and an installed example;
its exact evidence is linked by the active note. No numerical job is running. Main was not refreshed in
this planning review; the historical `be41a77a` baseline is not current-main evidence.

| Area | Established current state | Remaining boundary |
|---|---|---|
| GE owner and consumers | Multi-Q4/S3 point workflows, admitted material histories, loads, chart/restart, scoped displacement/arc and modal implementations have installed development evidence. | Each combination retains its own admission; physical accuracy, capacity and aggregate acceptance are incomplete. |
| B2 | Physical static/batch execution, selected recovery, persistence and scoped supported/free-modal consumer routes exist. | Complete attachment, prestress, scale, external and release acceptance remain. |
| Foundations | Scoped F05, F08 and F09 have recorded PASSED dispositions; further point/static/elastic-chart portions are accepted within their stated boundaries. | Do not relabel scoped passes as complete aggregate gates or repeat the obsolete claim that no foundation has passed. |
| BL5 | All 21 saved auxiliary-norm cases passed their scoped predicates; actual mechanical inventory is 13 positive, one unresolved, seven unassessed. | Auxiliary beta does not settle the mixed mechanics or physical transfer. Closed inverse/positive-part certificate routes remain CLOSED_UNRESOLVED. |
| Distributing attachment | Same reference-linear area law supports 2–128 conforming Q4 hosts/256 shell nodes with six rows; historical two-host bytes/checkpoints remain exact. 130 source/130 installed and 42 installed consumer controls pass. Fixed-pad three-level CalculiX torque/shear comparison executes. | Finite pose, fully converged physical fidelity and full F04 remain open. |
| Scale and cost | A 10,000-Q4/1,000-B3 point model completed a persisted reference route. Seven paired installed runs measured 55.97% improvement on the declared 400-Q4/120-B3 warm reference workflow; other scoped gains are recorded. | No overall development-speed measurement, full G5 qualification, nonmatching/nonlinear scale claim or release date follows. |

The [acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) and linked
reports bind these claims. In particular, see the
[scale/reuse result](development/r8-q4-reference-reuse-20261003/results.md),
[BL5 disposition](development/r8-bl5-projected-assessment-20261003/results.md) and
[distributing implementation](development/r8-distributing-reference-linear-20261004/results.md).
Do not rebuild these working routes from the September descriptions below.

The principal delivery risk is now accumulation of implemented capabilities
without closing their physical and external acceptance. More code and more
certificate machinery alone will not resolve it. Reuse the completed usable
consumer slice, then spend the primary engineering effort on a matched physical
comparison and the smallest remaining acceptance blocker it exposes.

## 2. Milestones and accountable outcomes

| Milestone | Usable outcome | Acceptance coverage | Initial effort allowance |
|---|---|---|---|
| M1 | Matching-station GE panel: construction, preflight, solve, physical recovery, checkpoint, restore and continue; ANYfem example | Relevant G1 foundations; V01–V06, V17, V18 subset, V28; E01; material rows for any advertised plasticity | 5 effort days |
| M2 | Straight nonmatching attachments on flat Q4/S3; BL5 is the selected bonded-line modelling target | Applicable F01–F03/F08; G2 line scope; V03–V08, V14, V26; matched external transfer | 8 effort days |
| M3 | Separate physical B2 static profile, point attachments, 1/10/100 compatible loads, selected results and consumer persistence | F09–F11/F13; B01–B08, B13, B17; E01 B2 variant | 8 effort days, concurrent where useful |
| M4 | Remaining materials, attachments, topology, loads, conservative stability, imperfections and capacity | Remaining G0–G4 foundations and V/B obligations | Estimate from M1–M3 results |
| M5 | Practical-scale, complete consumer/platform/external evidence and coordinated production release | G5/G6 and every mandatory remaining programme row | Estimate from integrated workloads |

M1–M3 start as independent workstreams when their actual prerequisites permit.
The integration owner can change order, combine slices, borrow available
capacity or advance ready M4 work. At most three workers, including the owner,
are active at once; delegation is useful only with independent file ownership.
A fixed staffing chart must not leave workers idle or cause duplicate work.
Independent reviewers must not be sole implementers of what they accept.

For each milestone, finish and show the smallest coherent working route first,
then close the evidence needed for its stated acceptance claim. A failed
independent comparison or one open foundation does not trigger a rebuild of the
already working owner. It identifies the exact claim or interface that remains
open. Track the critical path as one next deliverable and one next scientific
decision, with an owner and a bounded discriminator for each; do not maintain
a second task register.

Every milestone delivers a runnable example through the existing public facade,
clear preflight and numerical failure status, typed results, relevant persistence
and accurate capabilities. Preserve the two profile identities and existing API.
A new attachment law gets an explicit attachment/capability identity and any
needed checkpoint compatibility change, rather than silently replacing an old law.

**Scope flexibility:** the owner may defer an unready feature to a named later
milestone and keep its acceptance row open. It may release a coherent accepted
subset with approval. It may not delete mandatory final scope, defer a defect
that invalidates the subset, or call a collection of passing fixtures a general
supported domain. A milestone narrowed repeatedly without usable delivery is
a stall, not progress.

### 2.1 Current delivery order and decisions — 4 October

Use at most two active deliverables: one implementation completion and one
physical-acceptance question. The third worker may review or take a bounded,
independently owned task inside either deliverable; it must not open a third
feature stream. Finish or explicitly park a deliverable before opening another.
Keep tightly coupled edits with one owner and serialize numerical jobs under
the existing restriction. Worker headcount is a ceiling, not a staffing target.

| Order | Decision and useful exit |
|---|---|
| 1 — completed | ANYfem reference-distributing consumer is locally delivered:42 source/42 installed checks, supporting source/runtime review and installed save-reopen/recovery/checkpoint/resume example. Reuse that evidence without adding another attachment/API or rerunning an unchanged campaign. |
| 2 — physical acceptance | Reuse the existing E01/E02 inventory and build the smallest missing, physically matched eccentric GE connection comparison on the mandatory CalculiX route. Prioritize physical torque/shear and work transfer; another axial-only refinement does not answer the connection question. Use offset signs and registered observables/refinement requirements where applicable. First resolve geometry, frames, supports, load measures and connector semantics; an unmatched model is not an accuracy oracle. Share reference infrastructure with B2 only where the idealizations agree. |
| 3 — act on the result | A source/work-map defect gets a targeted repair; a physical mismatch gets a documented modelling decision within existing scope; a passed comparison closes only its eligible row. If execution or equivalence is obstructed, name the missing executable/output/equation and move the implementation lane to the highest-priority ready mandatory gap. Do not replace CalculiX acceptance with supplemental OpenSees results. |
| 4 — finish remaining M4/M5 | Prioritize a usable completion of an existing mandatory operation over new optional profile combinations. Promote the next item from the existing matrix by prerequisite readiness, acceptance impact and effort; no new backlog document. Keep bonded-line, footprints, materials, spectra/capacity, scale and complete consumers visible until accepted. |

Decisions resolving the present queue:
- **BL5:** retain the current experimental physical law and unresolved records.
  The closed inverse-majorant and positive-part certificate campaigns stay
  closed. Do not extend their shifts, orderings, precision, meshes or budgets.
  Numerical mixed-system assessment remains the permitted prospective method
  in section 4.5; frozen certificates and predicates are not replaced or waived.
  Resume a scientific ticket only for a new discriminator that changes an
  engineering decision, not merely to obtain another positive certificate.
- **Distributing attachment:** the consumer and multi-host reference compiler
  are complete within their experimental admission. Matched10x4/20x8/40x16
  torque work differences decrease4.249→2.233→0.813%; shear3.472→1.290→0.364%.
  Retain this law for further assessment: no defect or persistent discrepancy
  is established by this batch. Do not declare the1% converged criterion passed:
  native torque still changes1.518% on the last doubling, while solid thickness
  stays at two layers and shell/solid kinematic assumptions differ. Next identify
  which remaining convergence/model assumption affects the required physical
  claim before authorizing another diagnostic. No isolated solid/axial refinement
  or law rejection from one difference.
  [Grouped implementation and physical evidence](development/r8-distributing-reference-linear-20261004/results.md).
  The matched reference check and supporting finite-map review now permit
  experimental owner integration of the private projected-director/thin-polar
  candidate (22 focused source controls). This is not physical qualification.
  Reuse the existing owner; prove actual chart/spatial work, sparse curvature,
  reactions and atomic restart before public experimental finite admission.
  Give the candidate an explicit finite law/model/checkpoint identity and
  preserve the current reference-only identity and unused-option contracts.
- **Pressure assessment:** do not adopt the proposed vector-only amendment.
  Its documented shared-node masking weakens a protection of the current
  contract. This resolves the outstanding approval request as a decision to
  retain the current assessment; affected nonconvergence remains explicit and
  G4A remains open. A future response-resolution or assessment design needs its
  own scientific justification. No more blind precision substitutions follow.
  Preserve the [proposal and counterfactual evidence](development/r8-ge-pressure-work-20261002/pressure-assessment-amendment-proposal.md).
- **Forward nonlinear Q4 examples:** explicitly select the already implemented
  algorithmic pullback where required for demonstrated physical balance. Keep
  legacy defaults/checkpoints and their recorded failures intact.
- **Reviews and delivery:** supporting available-model review may unblock
  development, but does not satisfy an unmet independent-family or external
  acceptance requirement. Record that gap once; do not repeatedly probe known
  unavailable workers. After explicit resumption, the sequence needs no further
  routine design approval. Formal F03, main merge and publication retain their
  own authority.

### 2.2 Concrete next slice and reference feasibility

**Resume ownership:** the integration owner takes the four pending ANYfem files
as the starting candidate. An interrupted worker's acknowledgement is not a
prerequisite. Inspect the actual diff and retained findings, complete the
necessary review of the candidate and fix only consequential defects. Reuse
preliminary findings when their inputs match; do not describe them as a finished
review. Tests and installed-example checks remain required before delivery.

**Consumer exit:** a recorded installed run must complete input construction,
standalone and native Project save/reopen, solve, physical selected recovery,
checkpoint/resume and unsupported-request rejection. The complete slice then
gets normal review and a scoped recoverable commit when ready. A new optional
operation, law or generic persistence layer is outside this slice. Stop adding
consumer functionality once that exit is met and switch the primary effort to
the physical question. Keep aggregate qualification explicitly open.
This exit was met on 4 October by the committed consumer; it is not a new
requirement to execute the same checks on every resumption.

**Reference exit:** before a refinement campaign, reuse existing decks, runner
and parser, and execute one small development comparison that can recover the
required support wrench, connection-side force/moment and representable work.
Use a physically defined connection, fixed offsets, matching loads/supports
and explicit scalar/field measures. First establish that its outputs actually
distinguish the disputed torque/shear transfer; a finer mesh cannot repair a
missing conjugate action. Only then advance the applicable registered ratios,
refinements and physical thresholds. This feasibility comparison is not formal
F03 and cannot confer external accuracy acceptance by itself.

On resumption, check external executable/runner availability once if it is
unknown. If unavailable, or if the output/work mapping cannot yet be made
equivalent, record the precise blocker and one bounded remedy in the existing
note. Park that comparison while completing a ready mandatory implementation
or acceptance item. Do not wait through repeated availability probes, generate
another unexecuted deck campaign, or substitute a different solver's evidence
for the mandatory CalculiX row. No download, resource increase or scientific
amendment is authorized by this scheduling decision.

**Completion accounting:** after each completed slice update only its affected
rows in the existing matrix: scope, current status, evidence and smallest unmet
requirement. Preserve dated failures and dispositions. A requirement with no
actionable next check gets a named blocker, not another generic investigation.
Select the next ready item by whether it closes a mandatory row or repairs a
shared defect, then by implementation effort and reusable evidence. Acceptance
closure and working behavior outrank additional optional combinations.

## 3. M1: consolidate the working GE panel

### 3.1 Capability and admission

Consolidate the existing owner and consumer; do not build another framework.

Use the existing objective six-channel point law at explicitly paired beam and
shell reference stations. Eccentric paired stations need not have identical
coordinates: their fixed offset and frames define the connection. Define the
matching rule using entity IDs and material/reference correspondence, including
native beam midpoint nodes where relevant; do not infer connectivity from
coordinate coincidence or merge nodes automatically. Reject unpaired locations
in a declared matching bond. Nonmatching line enforcement belongs to M2.

Required M1 core:
- Multiple Q4/S3 shells and multiple native B3 members with retained variables.
- Reference-linear and scoped finite force-control routes.
- Reactions, physical point wrenches and selective recovery.
- Accepted/trial ownership, rejection, cancellation and checkpoint/restore/continue.
- One installed headless panel and the ANYfem save/reopen workflow.

Elastic support is the first usable core. Add plastic combinations only when
family-level evidence defines an enforceable material/kinematic/load-history
domain. The existing 1 MPa and S3 fixtures are useful controls, not a universal
admission rule. A 40 N success in one model cannot become a public force cutoff
or justify calling arbitrary histories of that material supported.
Known nonconvergence remains a truthful numerical outcome; known wrong
equilibrium, state or tangent behavior blocks affected capability claims.

### 3.2 Acceptance

Freeze one concise M1 acceptance contract using existing tests and evidence
where applicable. The working panel and consumer can be consolidated and shown
with explicit experimental status before this entire contract is closed:
- V01: old/new one-shell agreement within 1e-10 where equations, variables,
  constraints and material scope are equivalent. A different released
  rotational law is not an exact-parity oracle.
- V02: bounded independent dense/sparse assembly and solution parity.
- V03–V05: rigid-motion, physical work/balance and actual-update derivatives,
  with the programme tolerances and finite-difference plateau requirements.
- V06: eccentric transformed-section response for both offset signs and three
  refinements, using the programme energy including the EA_b e cross term.
- V17/V18/V28: rejected work, cancellation, owned inputs, stale generations,
  corrupt/incompatible snapshots and continuation on the same accepted path.
- E01: executed eccentric panel comparison with matched section, offset,
  loads, supports and nodal connection semantics; <=1% on registered
  converged physical quantities with appropriate absolute floors. The existing
  one-cell-wide x-refinement is a diagnostic, not mesh convergence. Reuse it,
  then compare at least three systematic two-direction refinement levels and
  the full preregistered physical observable set. Diagnose persistent shell
  formulation and connection-law differences under matched actions before
  applying the cross-solver threshold. Do not discard discrepant secondary
  observables by calling only the axial tip response representative.
- Installed Windows wheel, Linux CI, relevant legacy regression, capability
  documentation and independent review of the complete candidate.

E01 decision after the three-level two-direction comparison: if the declared
physical differences converge within the frozen limits, prepare the formal
comparison; if a discrepancy persists, identify whether a shell idealization,
point-link work map or load/support mismatch explains it using the smallest
same-action check. Record the obstructing observable and seek focused mechanics
review if still unresolved. Do not start a fourth refinement merely because
the third is inconclusive. Keep M1 acceptance open and advance unaffected M2,
M3 or M4 work rather than restarting the owner.

These are acceptance requirements, not an instruction to replay an existing
three-level campaign. Reuse the latest exact applicable result and its terminal
decision before considering further execution. The October priority is the
missing matched external acceptance, not automatic refinement of an old screen.

Compare a six-row nodal chain and an explicitly distinct BL5 nodal variant if
useful for the intended lateral response. A difference above 1% is a sensitivity
finding, not proof that one overconstrains. Choose only from the intended physical
law, convergence and matched reference evidence. Keep the existing six-row law
by default; a five-row variant cannot be substituted silently. Support-Jacobian
rank checks are necessary diagnostics, not proof of absence of physical
mechanisms, locking or wrong stiffness.

### 3.3 Bounded low-yield ticket

Allowance: one effort day within M1. Reuse the accepted 40 N state and preserved
45 N failure; do not restart a refinement campaign.

Distinguish increment/globalization difficulty from local update or derivative
failure. Examine one relevant failed/advanced trial from the same accepted
predecessor, its active sets and actual-update derivative. Attempt a bounded
cutback path if that addresses the finding; retain accepted-prefix/restart checks.

- Completing the registered path with smaller increments supports that stepping
  requirement for the case. One smaller accepted increment does not close it.
- A wrong derivative, nonfinite accepted response or partial commit requires
  repair or withholding all affected capability, not merely excluding this test.
- A limit point or instability requires mechanical evidence; failed Newton
  iterations alone do not establish one.
- If unresolved, preserve a specific failure ticket for M4 and proceed with
  unaffected accepted M1 scope. Do not silently narrow the material law.

The direct virgin 50 N and S3 500–1000 N failures remain recorded. Reopen them
only for an advertised material range, shared defect or required acceptance case.

## 4. M2: declared physical connection and bounded qualification

### 4.1 Design decision

BL5 is the selected modelling target: bond the attachment position and shell
director to the beam section, while releasing relative spin about the director.
It is a deliberate physical release, not a claim that dropping a row repairs
all previous stability issues or is equivalent to a six-channel welded pose.

The yaw derivative channel explains some previous obstructions. The saved
Fy/pitch mode and other modes require their own interpretation. Removing yaw
cannot be declared successful because an old fixed field has a smaller score.
Matched physical tests determine whether BL5 is useful for the intended
application. Preserve the original six-channel point identity.

### 4.2 BL5 work law and required checks

Let p_s be the declared top-surface point, d_s the unit physical shell director,
and (r_b,R_b) the native beam-section pose. Reference quantities are fixed:

    a_b = R_b0^T (p_s0-r_b0)
    nu  = R_b0^T d_s0
    b_1,b_2: fixed orthonormal beam-frame vectors perpendicular to nu

    c_t = R_b^T (p_s-r_b)-a_b
    c_d = [b_1 dot (R_b^T d_s-nu), b_2 dot (R_b^T d_s-nu)]
    Pi  = integral_Gamma0 (lambda_t dot c_t + lambda_d dot c_d) ds

This is a suggested objective representation within the declared semantics.
The owner may choose an equivalent differentiable representation and document it.

Required before assessment:
- Exclude the antipodal zero of the two director components. Use an explicit
  admitted orientation chart, such as nu dot (R_b^T d_s)>0, with validated
  guard margin. Reject degenerate director interpolation and chart violations.
- d_s is the shell's physical director. Do not set it equal to the geometric
  surface normal or constrain admissible transverse shear.
- Check reference consistency, finite rigid-motion objectivity, first/second
  variations through actual updates, multiplier curvature and physical
  wrench recovery including lever arms.
- Preserve native half-cell fields, retained coordinates and reference lifts.
  Use the same coordinate and work maps in assembly, recovery and restart.
- Check the intended free spin with a physical rotation about the attachment
  point, including the corresponding beam-axis translation for an eccentric
  arm. Holding the beam centre fixed is generally a different variation.
- Keep fixed reference correspondence. No Newton-time reprojection.
- Test force, torsion, both bending directions, shear and eccentric coupling,
  thickness/refinement behavior, drilling independence and missing/extra modes.

Initial scope is straight members, flat Q4/S3, normal offsets and a registered
shape-regular bond mesh. Curved/pre-rotated configurations and crease/seam
crossings are M4 work. Lateral arms require their own physical checks before
admission. The remaining programme topology is not deleted.

Finite bonded length alone does not prove that the released spin is controlled:
test short attachments, ends, overhangs, supports and disconnected components.
Reject unsupported single-point/release configurations precisely.
BL5 has no independent normal-spin multiplier. An in-plane couple may be
transferred by distributed force over finite bond length; a concentrated
termination transfer needs a separately qualified footprint or point law.

### 4.3 Alternative distributing attachment

Option B remains an authorized alternative development route: a physically
declared finite-width/finite-length distributing attachment, with a distinct
identity and intended local freedom. The historical 0.1 m box patch and the
current two-host director/polar reference-linear area law are distinct
candidates; their dimensions and semantics are not interchangeable. The latter
already has a public experimental owner and pending consumer; reuse it.

It needs its own first/second variations, endpoint/overlap treatment, torque/shear
and physical reference checks before claiming nonlinear use. Earlier
first-variation and tip-response screens do not complete those requirements.

The owner may pivot to Option B when evidence or limited effort favors it,
provided geometry and use match its declaration. An accepted Option B may be
delivered as M2-D with its actual distributing capability. It does not close the
mandatory bonded-line row. Unresolved BL5 work moves visibly to M4/M5.
A timeout permits a work-priority change; it does not select or accept a law.

### 4.4 One design slice, then a decision

The following is the original two-effort-day law/metric sequence, retained for
its mechanical requirements. Completed steps are not a new execution queue.
Current scheduling and closed-ticket decisions in section 2.1 take precedence;
the allowance does not restart on a planning update or new filename.

1. Reuse the corrected saved-mode screen and add its two review guards:
   reconstructed L1 total equals saved mean-row work; native work agrees at
   each station rather than only in aggregate. Preserve density/mean-row
   measure conversion and translation-sign mapping.
2. Derive the five-row first variation. Dropping the virgin L1 yaw row may be
   used as a cheap proxy only after frame, offset, signs, row scales and
   supported constraint-space equivalence are checked. It is not the finite
   BL5 implementation or evidence that other modes disappear.
3. Test actual BL5 objectivity, released motion, work and derivative controls.
   Recompute relevant modes for the changed operator. Use small 2:1 and 1:2
   cases before enlarging to the full matrix.
4. Compare one coherent P0 resolution rule, with c_lambda=1 or 2 as a
   complete alternative. No case-by-case channel tuning.
5. Review the physical law and numerical assessment together once. Repair a
   concrete local defect, advance a justified candidate, switch to Option B
   under its own semantics, or park the exact unresolved equation/reference
   and continue independent work. There is no automatic refinement campaign.

Outcome defaults apply to scheduling only. If neither candidate is defensible,
M2 remains open. M1/M3 and ready M4 work continue. Ask the user only when the
next meaningful action needs a changed physical requirement, final scope,
scientific criterion, resources or authority.

### 4.5 Discrete space and numerical stability contract

Start with low-dimensional P0. Compare P1/dual if P0 cannot satisfy the combined
accuracy, work, locking and stability requirements. This is an explicit
prospective change to the compulsory three-space comparison.

Define multiplier supports independently of quadrature subdivisions. Initial
P0 supports are unions of native half-cells and at least c_lambda times the
local shell-trace length. Split integration at all shell and beam boundaries
without remeshing either domain. Supports must refine with the meshes; a fixed
small multiplier space cannot establish refinement behavior. Check endpoint
supports and incomplete aggregation, and freeze one rule for all seven ratios.

Declare the bond-zone aspect ratio and local mesh-size restrictions; <=4 is an
initial candidate bound, not a passed domain. Unregistered anisotropic families
are excluded until qualified. Coarsening that hides gaps or loses physical
transfer is a failure even if a spectral number improves.

Use one short independently reviewed numerical contract, attached to M2:
- Define physical primal and multiplier variables, work pairing, row
  coefficient versus density conversion, units, scales and boundary conditions.
- For an inf-sup calculation, use explicit positive norm matrices H_h and M_h.
  On the admitted supported space, the generalized problem is

      B_h H_h^(-1) B_h^T z = beta_h^2 M_h z

  H_h is a justified norm matrix, not automatically the complete native
  indefinite stiffness. Apply inverse actions by solves. No global dense
  inverse or unverified SPD interpretation of the mixed KKT is permitted.
- If physical stationary reduction is used on bounded verification models,
  establish its mapping, nonsingularity and work parity first. The production
  native formulation still retains its required variables.
- Identify exact rigid/gauge modes and unintended nullspaces explicitly.
  Do not discard small eigenvalues merely to obtain a favorable positive beta.
- Separately assess the actual constrained mixed operator, including its
  physical null modes, stability on the admissible constraint kernel,
  locking and response convergence. Inf-sup alone is insufficient.
- A mesh-weighted multiplier norm, including the proposed extra h factor,
  requires an approximation/physical justification. It cannot be chosen to
  cancel observed deterioration or used to claim a stronger mesh-independent
  result than it measures.
- Freeze numerical floors, eigen-residual tolerance, absolute admissibility
  floor and allowed refinement deterioration using independent controls and
  intended accuracy before candidate assessment. Include a deficient-row/
  checkerboard control and a known admissible control; exercise equivalent
  units and basis rescaling.
- Use a clearly signed trend measure. For h_fine<h_coarse,

      p = log(beta_coarse/beta_fine) / log(h_coarse/h_fine)

  Positive p means deterioration on refinement. The original draft's
  slope >= -0.1 rule could accept decay and is withdrawn. No universal
  replacement cutoff is asserted here; freeze a justified upper bound on
  deterioration together with a lower floor and all physical checks.

Numerical evidence over the registered domain is acceptable; a universal
h-uniform proof or certified infinite refinement tail is not a prerequisite.
Conversely three meshes or a nearly flat quotient alone do not prove stability.
If the numerical contract cannot be justified within the design slice, record
the specific missing property and leave M2 acceptance open. Do not turn this
into an unbounded analytic research programme.

### 4.6 Assessment and authority

The full M2 matrix retains ratios 1:1, 1:2, 1:4, 1:8 and reciprocals, growing
spaces and at least three systematic refinements. Include off-grid Q4/S3,
physical shell stiffness, complete native half-cells, thickness/shear,
physical transfer, pointwise gaps as well as weak residuals, and mixed-system
checks. Curved/pre-rotated scope is assessed in M4.

Formal execution requires the implemented law, local properties, numerical
contract, cases, external route, exact candidate and limits to be ready.
Use the once-authorized prospective F03 assessment recorded in goal section 6.
Before launch, bind the precise execution and any constituent cases/retry rule
to that authority; verify it is unconsumed. Do not reinterpret an old consumed
authority as renewed. A failed/aborted formal execution remains recorded;
another execution requires whatever additional authority its contract requires.
Ordinary authorized development screens do not consume that formal authority.

M2 acceptance requires:
- V03–V08/V26 and relevant support/overlap negatives for the admitted line law.
- A matched executed external case covering claimed offset and force transfer.
  Torque/couple claims need matched torque evidence before release. An unrelated
  external case cannot cover them.
- M1/M2 comparison only where physical law and idealization match. Otherwise
  report it as sensitivity, not a <=1% equivalence gate between different laws.
- Installed artifacts, accurate capability/checkpoint identity and independent
  acceptance review.

E02 components outside the milestone's claim may remain pending until M4/M5.
Evidence essential to the milestone's own claim cannot be deferred because a
deck is unavailable. All four programme external cases remain mandatory for M5.

## 5. M3: physical B2 in parallel

Reuse the physical flexibility operator and existing session services.
Preserve the scoped F09 PASSED disposition and its admitted range. Extend only
missing required coverage, using independent
force-method or physical oracles, including coupled sections, both bending
planes, reversal, fixed-magnitude mixed loads and small response components.
The old public B2 equation and its recorded differences retain their meaning.

Reuse completed batches, consumers and lifecycle evidence; complete only the
unmet portions of:
- F10/F11 reference-linear point work, offsets, reactions and affine/KKT parity.
- F13 owned inputs, dependency invalidation, failure status and cancellation.
- 1/10/100 compatible RHS, one eligible factorization and bounded selected
  recovery; persistence and an installed ANYfem example.
- B01–B08/B13/B17 and the B2 E01 comparison for the admitted static domain.

Mass, prestress/buckling, line/footprint additions and remaining B rows are M4/M5.
Supported/free-modal and footprint developments already exist; their open
physical and aggregate claims do not mean their implementations should be rebuilt.
This defers new capabilities, not regression checks for legacy behavior affected
by shared edits. No unused GE history or native retained-state overhead.
Measured speed claims require the programme's paired installed-artifact evidence.

## 6. Complete remaining programme, not a permanent reduced target

Maintain one acceptance matrix with implementation and qualification status
separate. Every deferral records its destination, dependency and acceptance
evidence still needed; no new shadow ledger.

| Remaining obligation | Destination |
|---|---|
| F01/F02/F08 point/local work and physical transfer foundations | M1 and M2 for claimed scope; remaining scope M4 |
| F03 nonmatching law, resolution and stability | M2 or explicitly deferred bonded-line completion in M4; mandatory before M5 |
| F04 footprints; F05 plastic pullbacks; F06 chart transport | Claimed portions before each relevant milestone; full breadth M4 |
| F07 constrained mass; F12 B2 mass/prestress | M4 stability blocks |
| F09–F11/F13 physical B2 and lifecycle foundations | M3 for point/static scope; remaining attachments M4 |
| G2 topology | Rigid/distributing footprints, releases, seams, multi-surfaces, curved/reversed members, rings, junctions, loops, terminations and mixed Q4/S3 in M4 |
| G3 materials | Generalized yield, physical axial/biaxial fibres, mixed native families, shell J2, cyclic/simultaneous yield, actual recovery, chart transport and durable restart in M4 |
| G4A | Staged/dead/follower/native loads, gravity, prescribed paths, displacement control and actual derivatives |
| G4B | GE and B2 conservative modes/buckling, physical inertia, algebraic variables, free-free modes, eigen/constraint residuals and prestress |
| G4C/G4D | Coherent stress-free imperfections, first limit point, declared descending branch and turning-point restart |
| G5 | Both >=10,000-shell/>=1,000-beam routes, GE multi-stiffener simultaneous plasticity, B2 1/10/100 loads and beam-rich control |
| G6 | Full artifact/platform/consumer/external acceptance, documentation, independent reviews and authorized publication |

Retain all V01–V28 and B01–B18 families and negative cases. Preserve the programme
tolerances, including residual/work/derivative criteria and matched 1% linear,
2% spectral and 5% limit-load comparisons with their normalization and convergence
requirements. Preserve scale ratios (assembly time <=2.5, memory <=2.3),
B2 warm-control limits (5% time/10% memory), overall resource budgets and required
measurement protocol. No extrapolated small model substitutes for large execution.

M5 includes installed Windows/Linux checks across supported Python versions,
full impacted CI, ANYfem and ANYworkbenchAI consumer contracts, all required
demonstrators, native persistence, explicit unsupported exports and the four
executed external families: eccentric panel, torque/footprint, curved structure
and compatible nonlinear GE response. Cross-platform and legacy checks happen
earlier where a milestone release requires them.

Final production completion requires all amended G0–G6 obligations accepted,
independent code/mechanics reviews without unresolved correctness findings,
approved release, verified published use, and clean main matching remote main.
An experimental label, release or exhausted effort budget closes none of those rows.

## 7. Decision rights, pace and useful stopping rules

The owner acts within the [goal's decision rights](B3_GE_E4_PL_REVISION_8_GOAL.md).
Use the shortest defensible path to a working capability or resolved decision.
Reuse existing code and valid evidence, simplify internal designs, fix relevant
defects, combine implementation and verification, and stop experiments whose
outcomes cannot change a development decision.

Use milestone allowances as decision checkpoints, not technical pass/fail tests.
The goal defines effort days, stall triggers and escalation. At a trigger,
the owner must choose a bounded next action: a specific repair, a justified
alternative, a named deferral or ready independent work. It need not interrupt
the user merely because an estimate expired. Repeated extensions of the same
unresolved hypothesis under new filenames are not a change of approach.

Ask only when the required next action changes final scope, physical semantics
outside the declared alternatives, a frozen scientific criterion, resources or
authority; present the concrete evidence and a recommendation. A defect invalidating
already delivered behavior is reported promptly even when repair is authorized.

## 8. Development and evidence discipline

- Use the adopted tiered testing regime. During edits, run the smallest tests
  that expose the changed failure modes. At a coherent solver/consumer boundary,
  build once and run the affected installed workflow plus relevant legacy
  controls. Reserve broad platform/CI campaigns for the required integration,
  acceptance or release boundary; do not repeat passed campaigns without a
  changed dependency or unresolved finding.
- Finish complete-slice source review before the routine artifact build when
  practical. Consumer-only work reuses the verified unchanged solver wheel.
  A new solver artifact gets its own honest identity and impact-based checks;
  source-only passes are never reported as installed verification.
- Prefer the existing runner and ordinary pytest invocation. Add a runner only
  for a missing resource, numerical or provenance requirement. One slice log
  can contain commands, inputs, outcomes and failures; do not generate a new
  adjudicator, archive, helper review, module-wide hash walk or wheel for each
  small edit. Exact inventories remain required where already frozen or at
  the artifact boundary that needs them. Preserve historical evidence in place.
- Before a substantial diagnostic batch, add a brief question, alternatives,
  bounded discriminator and resulting actions to the existing note. Routine
  reads, repairs and focused checks need no six-field mini-registration.
- Level A: recoverable source, meaningful checks, commands and enough input/
  output/failure data to reproduce the decision. Use ordinary logs or existing
  evidence directories. No mandatory commit, standalone dossier, hash manifest
  or independent review for every helper. Do not replace useful raw failures
  with an unreproducible summary.
- Level B: one concise frozen milestone contract with linked case inventory,
  source/dependency/artifact identities, controls, criteria, raw results and
  independent adjudication. Length is set by clarity, not a one-page cap.
  Reuse valid results by dependency analysis; preserve old registrations when
  changing a prospective contract. Formal F03 authority remains explicit.
- Level C: installed/platform checks and the repository release process for the
  actual claimed scope, followed by the user's applicable approval.
- Review early where mechanics/state assumptions drive architecture; review
  complete slices and candidate releases. A reviewer proposes a blocking test
  by naming the failure mode; neither a reviewer nor owner silently changes a
  frozen criterion. Scientific independence comes from independent reasoning/
  references, not merely counting agents.
- Keep one short active note (target <=150 lines), one authoritative acceptance
  matrix, and links to immutable evidence. Preserve historical checkpoints
  byte-for-byte; do not add a new header to a protected historical file.
  The active note contains current decision, working behavior, blockers and
  next action, not copied campaign history. Keep a compact current index in the
  existing matrix; old dated dispositions remain historical, not competing
  current instructions. Record exact source hashes once where they are needed.
- On restart read the active note, sections 2.1–2.2 and only the plan/matrix
  sections governing the next action. Check applicable repository guidance and
  policy as required, but do not reread the full historical evidence inventory.
  Expand a linked record only for an identity, authority, criterion or finding
  that matters to the current decision. A plan refresh is needed only when
  priorities, dependencies or decisions change; it is not a recurring work gate.
- Compile unchanged geometry, maps and patterns once; copy mutable trial state.
  Factor unchanged eligible linear systems once; invalidate factors on changed
  operators. Use focused tests during work and consolidated installed checks
  at meaningful integration/acceptance points. Optimize measured costs.
- Do not start a new optimization campaign merely because a hotspot exists.
  Prioritize it when it blocks the next mandatory workload or materially
  shortens a repeatedly executed route. Preserve the registered paired-run
  rules for any speed claim; no claim of faster development follows from test
  counts, shorter notes, agent activity or unmeasured time saved.
- At most three workers and one heavy numerical job at a time. Diagnostic
  ceilings remain 100,000 rows, 600 seconds per run, eight numerical threads and
  8 GiB process-tree memory, with actual process settings checked. G5 budgets
  remain separately registered. External worker ownership and no-run rules
  remain intact.
- Preserve the unrelated dirty script b3_e4_f03_c1_fy_supported_reference.py.
  Its existence is not authority to execute it or take ownership.

## 9. Explicit prospective programme amendments

| Earlier rule | Revision 8 amendment |
|---|---|
| One release only after the complete programme | Accepted opt-in experimental milestones may be published with approval. One coordinated production release still completes M5. |
| Unresolved G0 blocks all G1 acceptance/delivery | Accept a scoped experimental milestone when its own foundations pass. Aggregate G0/G1 and production remain open until all their obligations pass. |
| No elastic subset release | A coherent accepted elastic subset may ship experimentally. Wrong or unverified behavior cannot be hidden by narrowing a fixture list. |
| Six-channel bonded line mandatory | BL5 with explicitly released normal spin is the selected bonded-line target. The original six-channel line becomes research; point-law identity stays unchanged. |
| Bonded line and distributing footprint both required | Both remain final obligations. Option B is a separately identified distributing capability, not a bonded-line substitute. |
| Compulsory initial P0/P1/dual comparison | Try P0 first with a frozen complete resolution rule; compare alternatives when needed. All rejection/physical/stability criteria remain. |
| Revision 7 analytic reference-tail/work-bound prerequisites | A justified empirical mixed-system assessment over an explicit admitted domain may qualify scope without a universal theorem; section 4.5 replaces the prospective method. |
| All curved/pre-rotated scope before early line delivery | Initial straight/flat envelope may be accepted separately; required curved/pre-rotated/topology scope remains M4. |
| Prior next-action scheduling | Sections 2–8 and the goal govern after explicit resumption. Existing evidence and scientific dispositions do not change. |
| Formal F03 execution | The once-authorized prospective execution recorded in the goal applies after its prerequisites. It does not revive consumed historical runs or authorize unregistered repeats. |

All unamended final capabilities, programme quantitative tolerances, external
cases, lifecycle requirements and release/authority boundaries remain binding.

## 10. Immediate use and resumption

**Planning update only; implementation remains paused.** This review updates
the current plan/goal, forwarding references and active planning state. It
launches no development workers, tests, experiments, builds or product changes
and does not resume the goal.

On explicit resumption:
1. Read the short active state; verify only relevant HEADs, four pending ANYfem
   files, current owner/process state and the pinned solver artifact. Do not
   re-audit all history or touch the protected F03 runner.
2. Reuse the completed consumer slice and its exact source/installed/example
   evidence. Verify only changed inputs affecting the next action; no repeat
   of the same consumer or preceding solver campaign is required.
3. Carry out section 2.1's physical-acceptance priority. Use existing case and
   acceptance records; identify the exact missing comparison before numerical
   execution. Reuse already completed E01/BL5/B2/foundation work.
4. Keep one implementation completion and one scientific decision in flight,
   with a third worker only for useful bounded work within those deliverables.
   Serialize owned numerical
   jobs under current limits. Formal F03 stays unconsumed until ready under its
   exact recorded contract; closed diagnostic authorities remain closed.
5. Continue without ritual approval between authorized slices. Report completed
   behavior, acceptance remaining and any actual decision needed from the user.

No further general plan-review cycle is required to begin authorized development.
Technical choices still receive their specified checks before capability acceptance.
Publication and merge remain separate user decisions.

## Appendix: planning review disposition and references

The original Revision 8 draft is revised for these substantive findings:
- A >1% difference between two connection laws is not proof of overconstraint.
  A small tip-response difference likewise does not establish equivalent transfer.
- A deadline cannot establish a physical law, eliminate a mandatory capability,
  establish a limit point or authorize a numerical pass.
- The two-component director constraint needs an antipodal/chart guard.
  Finite bond length and row rank alone do not exclude a mechanism.
- A native indefinite KKT is not an SPD norm matrix. Inf-sup and constrained
  physical stability need distinct checks. The proposed trend inequality had
  the wrong acceptance direction; mesh-dependent normalization needs justification.
- A saved-mode yaw deletion cannot prove that the reassembled problem has no
  other mode. Historical mean-row multipliers require their physical measure.
- Literal bans on development logs/reviews, fixed page limits, mandatory
  per-helper commits and automatic user escalation would recreate overhead.
- Passing specific material histories does not by itself define general
  material admission; experimental labels do not cure incorrect mechanics.
- Existing history must not be modified just to attach a new plan pointer.

Planning review found these resolvable by the edits above. Candidate mechanics,
admission envelopes and acceptance thresholds remain work; no new scientific
qualification or numerical result was produced by reviewing these documents.

Primary references used for interpretation:
- [Chapelle and Bathe, The Inf-Sup Test (1993)](https://web.mit.edu/kjb/www/Publications_Prior_to_1998/The_Inf-Sup_Test.pdf).
  Provides a numerical refinement test in its stated variational setting.
  Its norm matrices, nullspace treatment and separate ellipticity requirement
  must be respected when adapting the test.
- [Bathe, The Inf-Sup Condition and its Evaluation for Mixed Finite Element Methods (2001)](https://web.mit.edu/kjb/www/Principal_Publications/The_Inf-Sup_Condition_and_its_Evaluation_for_Mixed_Finite_Element_Methods.pdf).
- [Steinbrecher et al., beam–surface coupling preprint](https://arxiv.org/abs/2210.16010).
  A design reference; its shell/enforcement assumptions do not qualify BL5 or
  an exact-multiplier E4-PL adaptation.

Historical literature suggestions in the original draft are optional background.
No citation substitutes for deriving the implemented coordinate/work map and
verifying the claimed capability. Forensic commit/file counts are omitted from
mandatory review because they do not decide engineering acceptance or progress.
