# B3-GE / E4-PL stiffened shells: Revision 8 development plan

**Status, 29 September 2026:** reviewed and revised planning basis.
**Implementation is paused.** This document becomes the forward execution basis
on explicit user resumption; completing this review does not resume work.
The companion [goal](B3_GE_E4_PL_REVISION_8_GOAL.md) defines the objective,
decision rights and completion conditions.

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
  failures, evidence and next actions. Its Revision 7 scheduling is superseded
  by this plan only on resumption.
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

Repository reference for this review: integration commit 5ba6a77a, following
the Q4 precision fix at 55e79c19 and bounded E01 external-reference work, on
codex/b3-ge-e4-pl-integration in
C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling.
The historical main baseline is be41a77a, version 0.4.7; it is not a claim
that remote main remains there. Verify changed inputs when resuming.
The current worktree also contains uncommitted E01 diagnostics and an unrelated
dirty F03 script. They are provisional work, not accepted evidence or permission
to run the F03 script. Preserve their ownership and reconcile them on resumption.

Existing experimental behavior includes:
- Multi-Q4/S3 native B3 point models, sparse assembly, finite stepping,
  recovery, atomic state, cancellation, checkpoint/restore and continuation.
- Several Q4/S3 J2 and generalized-beam material histories, with bounded
  derivative and lifecycle evidence.
- Separate physical B2 batching, selected recovery and factorization reuse.
- An experimental ANYfem construction/save/reopen consumer and scoped installed
  solver/consumer verification.

These are starting assets, not reasons to rebuild the owner or declarations
that entire material families are qualified. The native S3 finite-rotation
scope, attachment combinations, physical fibres, spectra and practical scale
still need their own evidence. None of F01–F13 is fully accepted in the current
record, and aggregate G0/G1 acceptance is incomplete.

Three useful recent findings change the next action:
1. The low-load Q4 cancellation fix passed 49 source and 5 installed checks.
   The 20 kPa mixed-shell path then accepted 5 N increments through 40 N but
   failed at 45 N. This is a separate unresolved material/driver case.
2. On the saved 2:1 field, corrected common-action L1 shell/native work is
   0.101298630920 / 0.031510722569 J. The 0.1 m finite patch gives
   0.038308332396 / 0.031510722569 J. These are signed virtual-work pairings,
   not energy or compliance reductions. The laws are distinguishable.
   The earlier 0.66% torque and 0.067% shear tip differences on another
   fixture cannot establish law equivalence or physical correctness.
3. Executed OpenSeesPy E01 point-link comparisons agree on primary axial tip
   quantities within 1% in the tested x-only sequence, but secondary rotations
   differ. Shell-only and same-action development screens localize much of the
   roll difference to different shell operators; removing the native drilling
   action leaves that roll finding. These screens do not qualify the point law
   or E01. The 2/4/8 sequence has one shell cell across the panel: next compare
   full two-direction refinement and the complete declared observable set.

The main process correction is to stop making every capability wait for one
line-law investigation. Modelling choices can be declared, but their claimed
engineering fidelity still needs evidence. Numerical qualification over an
explicit envelope does not require a universal theorem. Neither document
volume nor counts of commits, tests or meshes measure delivered progress.

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
identity and intended local freedom. The current 0.1 m box patch is a prototype;
its dimensions are not automatically the engineering connection dimensions.

It needs its own first/second variations, endpoint/overlap treatment, torque/shear
and physical reference checks before claiming nonlinear use. Earlier
first-variation and tip-response screens do not complete those requirements.

The owner may pivot to Option B when evidence or limited effort favors it,
provided geometry and use match its declaration. An accepted Option B may be
delivered as M2-D with its actual distributing capability. It does not close the
mandatory bonded-line row. Unresolved BL5 work moves visibly to M4/M5.
A timeout permits a work-priority change; it does not select or accept a law.

### 4.4 One design slice, then a decision

Initial allowance: two effort days within M2 for the law/metric screen and
decision, not the entire acceptance envelope.

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
Complete a declared F09 physical/unit/conditioning range with independent
force-method or physical oracles, including coupled sections, both bending
planes, reversal, fixed-magnitude mixed loads and small response components.
The old public B2 equation and its recorded differences retain their meaning.

Complete:
- F10/F11 reference-linear point work, offsets, reactions and affine/KKT parity.
- F13 owned inputs, dependency invalidation, failure status and cancellation.
- 1/10/100 compatible RHS, one eligible factorization and bounded selected
  recovery; persistence and an installed ANYfem example.
- B01–B08/B13/B17 and the B2 E01 comparison for the admitted static domain.

Mass, prestress/buckling, line/footprint additions and remaining B rows are M4/M5.
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
- Compile unchanged geometry, maps and patterns once; copy mutable trial state.
  Factor unchanged eligible linear systems once; invalidate factors on changed
  operators. Use focused tests during work and consolidated installed checks
  at meaningful integration/acceptance points. Optimize measured costs.
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

**This review edits only the Revision 8 plan and goal.** It launches no workers,
tests, experiments, builds or product changes; it creates or resumes no task goal.

On explicit resumption:
1. Verify relevant current worktree/process ownership and source identities.
   Reconcile only changes affecting the next action, including the uncommitted
   E01 work; do not re-audit all history or take over the unrelated F03 script.
2. Link these documents from the living note and update the one acceptance
   matrix with M1–M5 dependencies and known deferrals. Leave the historical
   complete programme and evidence unchanged.
3. Integration owner: consolidate the already working M1 panel/consumer, then
   identify its smallest missing acceptance item. Use the bounded material
   ticket only where it affects the claimed scope. Complete the E01
   two-direction discriminator and make its stated decision.
4. When independently owned work is useful and permitted, advance the BL5
   design/metric decision and B2 physical admission/batch route without waiting
   for an unrelated E01 result. Do not launch formal F03 until its prerequisites
   and exact authority match. Schedule numerical work under the common ceiling.
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
