# B3-GE / E4-PL stiffened shells: Revision 8 goal

**Status, 29 September 2026:** active development. The user explicitly resumed
implementation after approving this planning basis. The original document
review did not itself authorize a run; subsequent user resumption did. The
living [active state](B3_GE_E4_PL_ACTIVE_STATE.md) holds current source identity,
delivered behavior and remaining decisions.

At reviewed integration source `5ba6a77a`, the M1/M3 experimental routes
operate but are not acceptance-complete. E01 has an executed point-link screen.
Shell-only and same-action diagnostics explain part of its rotational
discrepancy; full two-direction mesh convergence is still untested. The E01
scripts and active note contain uncommitted work. A separate dirty F03 script
belongs to another investigation. Reconcile ownership on resumption; do not treat
these files as accepted results or launch the F03 script by implication.

Use this goal together with the [Revision 8 plan](B3_GE_E4_PL_REVISION_8_PLAN.md).
The complete programme remains the final scope, with only the explicit
prospective amendments in plan section 9. Historical evidence, consumed
authorities, failures and scientific dispositions retain their meaning.

## 1. Objective and success

Deliver the complete native B3-GE / E4-PL stiffened-shell workflow and mandatory
separate physical B2 option through useful, independently accepted milestones.

| Milestone | Working outcome |
|---|---|
| M1 | Multi-element Q4/S3 and native B3 panels with matching-station eccentric point bonds, solve/recovery/state/restart and an ANYfem workflow |
| M2 | Straight nonmatching attachments on flat Q4/S3; BL5 is the declared bonded-line modelling target, subject to its mechanics and physical acceptance |
| M3 | Physical B2 static operator with point attachments, compatible 1/10/100 load cases, selected recovery and consumer persistence |
| M4 | Remaining attachment/topology/material/load/stability/imperfection/capacity obligations |
| M5 | Full scale, artifacts, platforms, consumers, external comparisons, independent acceptance and coordinated production release |

Consolidate the working owner and adapters. Prefer the simplest implementation
that satisfies the intended physics and current milestone. Deliver a coherent
accepted subset when appropriate, but carry every deferred mandatory capability
to a named later milestone. Neither a smaller permanent target nor an indefinite
investigation satisfies this goal.

Experimental milestones may reach release-ready independently. Publication
requires the user's approval. Only the complete accepted M5 outcome can carry
the programme's production qualification.

The full goal is complete only when the amended G0–G6 requirements, F01–F13,
V01–V28, B01–B18, mandatory external references, GE/B2 practical-scale workloads,
consumer/artifact checks and independent reviews are accepted, the authorized
production release is verified from published artifacts, and local main is clean
and matches remote main.

## 2. Meaning of progress and milestone completion

A milestone is acceptance-complete when:
1. Its usable end-to-end workflow operates through the intended public API
   and relevant consumer/persistence route.
2. Its applicable foundations, cases and programme tolerances pass under a
   frozen acceptance contract on the actual installed artifact, with permitted
   evidence reuse based on unchanged relevant inputs.
3. Independent review leaves no unresolved correctness finding affecting the
   claim. Analytic, external and independent mechanical evidence cover the claim.
4. Capabilities, preflight, failures, documentation and limitations describe the
   actual supported domain. No unqualified behavior is presented as accepted.

It is release-ready after its artifact/platform/release checks pass, and released
only after approval and verified publication. Waiting for publication approval
does not prevent authorized development of the next independent milestone.

Progress is a working behavior, a closed acceptance obligation, a repaired
consequential defect or evidence that changes a decision. Tests, commits,
documents and refined meshes are means, not progress targets.

The near-term critical path is one consolidated M1 installed/consumer route,
one bounded E01 two-direction comparison followed by its decision, and one
mechanically defensible M2 law/space decision. Run the independent B2 admission
and batch route when its ownership and numerical resources permit. These are
priorities, not new gates or independent execution authority.

## 3. Autonomous decision rights

Within this plan, the integration owner may act without repeated permission:
- Choose implementation, reusable services, tests, fixtures, work order and
  internal representation consistent with the declared mechanical contract.
- Simplify or replace an unproductive approach, make compatible correctness or
  performance fixes, and change bounded development experiments.
- Stop a diagnostic that cannot change the next decision; reuse valid evidence.
- Select the exact objective BL5 representation and an eligible complete
  multiplier-resolution candidate, subject to the plan's mechanics checks.
  This development choice does not qualify BL5, make it equivalent to a
  six-channel welded bond, or erase any unamended final obligation.
- Develop Option B as a distinct distributing attachment when its physical
  declaration fits. It cannot be renamed a bonded line or inherit BL5 acceptance.
- Defer an unready feature to a named milestone, keep its mandatory row open,
  and advance a usable unaffected subset. Do not hide a shared correctness defect.
- Reassign up to three concurrent workers, including the integration owner,
  where independent ownership improves throughput; remain solo when it is simpler.
- Prepare reviewable commits and acceptance/release candidates within existing
  repository authority. A local development commit is not a merge or publication.

Request a user decision only when the next meaningful action requires:
- Removing mandatory final scope or changing physical semantics outside the
  declared alternatives.
- Relaxing or replacing a frozen scientific acceptance criterion.
- Changing public defaults, historical mechanical/checkpoint identities or
  intentionally breaking released behavior. Compatible bug fixes within the
  authorized task may proceed with proportionate regression checks.
- Exceeding resource/execution authority or repeating an authority-bound run
  without an applicable repeat authorization.
- Publication, merge to main or release.

Give a concrete finding, the smallest decision needed, and a recommendation.
Continue unaffected work. Do not stop the whole programme merely because one
capability remains unaccepted.

## 4. Boundaries that remain binding

- Preserve legacy B3, released b3-ge and create_coupled_analysis meanings,
  historical B2, Q4/S3 policies, default selection and checkpoint contracts.
- New laws and profile operations have explicit identities and compatibility.
- Preserve programme numerical tolerances, physical accuracy criteria,
  mandatory final capabilities and external/scale/release requirements except
  for the specific prospective amendments in plan section 9.
- No artificial penalty/inertia, tuned drilling, disabled guard, concealed
  nonconvergence or fabricated result. Unsupported requests fail explicitly.
- A different response between different laws is not proof of error; a small
  difference or small residual is not physical qualification.
- Retain failures and frozen/consumed evidence. A new registration does not erase
  a previous failure or renew an old one-use authority.
- At most three workers and one heavy numerical job at a time; diagnostic
  limits remain 100,000 rows, 600 seconds/run, eight numerical threads and
  8 GiB process-tree memory. Check effective settings. G5 budgets are separate.
- Apply ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1, revision 2026-09-24.2,
  and applicable workspace/repository rules.

## 5. Pace, course correction and escalation

Initial estimates are M1 five effort days; M2 eight; M3 eight, concurrent where
useful. The low-yield ticket has one effort day within M1; the initial BL5
design/metric decision has two within M2. Estimate M4/M5 from delivered results.

An effort day is roughly eight cumulative working hours assigned to that
workstream, summed across its workers. Record a coarse effort estimate, not a
new time-accounting system. Paused time is excluded; distinguish effort from
elapsed compute/wait time. Do not count a brief status message as a day's work.

At two successive investigation cycles without a changed decision, or at the
bounded ticket allowance, review the combined evidence and change the next
action. At 1.5 times a milestone estimate, make an explicit delivery decision:
- complete one specific bounded repair with a stated reason;
- switch to a justified alternative;
- defer an unready feature while keeping final obligations visible; or
- advance a ready independent milestone.

The owner normally makes that decision under section 3 and reports it. Ask the
user only if a protected boundary must change. Do not silently reset the budget
by renaming the same investigation. An unresolved finding is not a scientific
failure conclusion, and effort expiry never produces a technical pass.

Default when a question remains unresolved: retain its evidence and precise
missing equation/reference, withhold the affected claim and move to useful
permitted work. Option B is a development alternative with its own acceptance,
not an automatically accepted timeout fallback.

At meaningful milestones or roughly every two effort days, report briefly:
delivered behavior; decisions taken; acceptance remaining; effort/blocker; next
action. Report new consequential defects promptly. Do not add daily reporting
ceremony that competes with implementation.

## 6. Recorded directions and execution authority

The incoming Revision 8 draft records these user directions, retained here:
1. Milestone delivery without calendar promises.
2. BL5 as the bonded-line modelling target, with a distributing alternative.
3. Experimental opt-in milestone releases, each still requiring publication
   approval.
4. B2 development concurrent with useful GE work.
5. One prospective formal F03 execution on the declared eligible law after
   plan section 4.6 prerequisites, without another routine approval request.

Their interpretation is explicit: no declared law is thereby qualified;
Option B does not satisfy an unfinished bonded-line obligation; old consumed
authorities are not replayed. The precise formal execution and constituent
cases/retry handling must match the recorded unconsumed authorization before
launch. A further authority-bound execution needs applicable authorization.

## 7. Resume and pause instructions

On explicit resumption, read the canonical policy, this goal, the Revision 8
plan and current active state. Verify only relevant source/process/ownership
changes. In the existing note record the policy revision, current milestone,
first useful action and unchanged boundaries. Follow plan section 10; do not
repeat completed campaigns or rebuild the delivered owner.

Use one short living note and one acceptance matrix. Preserve historical
checkpoints and evidence. On pause, launch no new work, finish or stop owned
activity as directed, record exact results/process state and next action,
then leave a usable restart point. Do not create a new task unless requested.

This planning review resolves the original draft's document-level findings.
It creates no new blanket plan-review gate. Scientific candidate review and
acceptance remain required at the stated boundaries.
