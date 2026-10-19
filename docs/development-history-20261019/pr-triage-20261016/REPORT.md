# Open PR triage — 16 October 2026

Read-only investigation: determine whether the five pictured PRs contain useful work absent from current main, are superseded, or conflict with retirement. Use current GitHub metadata/check results, ancestry, patch equivalence and source comparison. No PR, branch or product changes; no numerical runs. A red historical check alone does not establish invalidity.

## Result

Compared with local and GitHub main `8475718b9262e120607c9d3861923f9c79f13e55`.
All five remain open; four are drafts. All have failed checks on their old heads.
Only #65 is currently mergeable; #64/#62/#57/#35 report conflicts.
None should be merged as-is. Recommend closing #65/#64/#62 as superseded,
archiving #57 as an unaccepted experiment, and preserving #35 for a narrowly
scoped salvage decision. No closing, commenting, merging, branch deletion,
CI rerun or product edit was performed. Existing dirty work was not edited.

| PR | Current head | Checks success/failure | Disposition |
| --- | --- | --- | --- |
| [65](https://github.com/audunarn/ANYsolver/pull/65) S3 surface recovery | `974f283a253cbf5119b5ded78f0ce29003c7582e` | 23/26 | Close: complete three-file content is already on main. |
| [64](https://github.com/audunarn/ANYsolver/pull/64) Modal rigid classification | `a666c9558a1ddb96e40061472d9c63997057c9c1` | 21/28 | Close as superseded; retain historical branch. |
| [62](https://github.com/audunarn/ANYsolver/pull/62) Common consolidation | `99cf90a4b3490534c25cbb800281fb66c2083f2a` | 16/9 | Close as superseded by the later common baseline; retain optional old tooling/evidence. |
| [57](https://github.com/audunarn/ANYsolver/pull/57) Follower validation | `56c5b384f811355c42a0db30c41527f7825a5d39` | 22/3 | Archive/close: formal NO-GO, experimental code unmerged. |
| [35](https://github.com/audunarn/ANYsolver/pull/35) Warm batch identity | `090e2c9756fd2d5e7f8378a6379b87b477b39fbe` | 20/4 | Preserve for separate salvage/review; not safe to discard as duplicate. |

## Source evidence and limits

**#65:** Current main and the PR head have identical Git contents for all three
changed paths: `src/anysolver/e4_pl_s3_v2d_element.py`,
`tests/test_e4_pl_s3_v2d_linear_native_parity.py` and
`tests/test_e4_pl_s3_v6e_final_parity.py`. The original PR commit is not an
ancestor, but its delivered content is present. Stale failed CI does not make
that incorporated recovery implementation invalid.

**#64:** Main contains `7a0e1667` (modal repair) and `da1ba2e9` (its integration).
Both `src/anysolver/modal.py` and `tests/test_modal_rigid_classification.py`
are identical between the PR head and main. Four later PR commits are not
ancestors of main. Their contact-manager fix is covered by main's `b95f4aca`:
main obtains `manager_law = getattr(manager, "law", None)` and uses it at both
pressure-basis sites. Main's preparation-reuse fixture also supplies the
profile/projected-work fields. Other residual changes concern old BL5/F03
test fixtures and exact checkout bytes; preserve them as historical evidence,
not a reason to merge this obsolete modal vehicle or reactivate retired tests.

**#62:** Main's `cff55d95` explicitly establishes the shared stiffened-shell and
contact baseline through PR #63; `cebdb005` records later common-main repairs.
Of the 171 product paths changed from this branch's current merge base, all
exist on main: 112 are identical and 59 differ. Presence does not prove every
old hunk is equivalent. This is a superseded integration vehicle, not a claim
that every historical file was cherry-picked. Two non-merge commits remain
off main: `80db5d64` and `99cf90a4`, carrying bookkeeping, documentation and
development-test tooling. Some optional profiles/inventory/compilation-cache
and integration tests are absent on main. Retain these commits for reference;
any desired tooling should be extracted separately under current selection
and retirement policy. Do not merge the old consolidation wholesale.

**#57:** The head's committed
`docs/reference_cases/nonlinear_static_combined_s3_component_v3_closeout.json`
records `decision: NO-GO`, `pr_57_merge_allowed: false`, no formal campaign,
and S3 candidate reverts `2a37f905`/`fdb371e7`. Retained follower code remains
experimental. Its original aggregate promotion result was below the 10%
criterion despite the reported targeted follower speedup. Main lacks the
branch's `_assemble_builtin_load_vector_under_existing_lease` and
`reused_follower_validation_guard` implementation; this is not a duplicate.
The PR body still describes older green head `61ec9723`; current head is
different and has three failed checks. Preserve raw evidence and branch;
closure does not establish performance acceptance or authorize another run.

**#35:** The description is no longer a complete scope statement: current
branch has 21 unmerged commits over 17 changed paths, adding Q4 batch/recovery,
cache and kernel-warmup work beyond the original S3 identity fix. It is 3290
commits behind main by current ancestry. Main lacks
`_is_canonical_immutable_float64_array`, still recreates frozen vector arrays
in `_freeze_qualified_element_vector_inputs`, and lacks the branch's
`q4_reference_batch.py`. Original bounded fix `a8428e0d` and its identity
regression are plausible salvage candidates. Static absence establishes
unmerged work, not a current supported-route failure, speedup or acceptance.
Do not merge all 21 commits. Decide relevance on current supported routes,
then port/review/test only an explicitly bounded slice. Do not reopen retired
programme checks implicitly.

## Method and retained records

GitHub connector search, PR metadata, changed-file lists and discussions were
read; all five discussions were empty. `gh pr view --json` supplied current
head/check/mergeability records (`pr-*.json`). `gh api .../branches/main`
confirmed current main. Local Git ancestry, merge bases, tree/path equality,
commit messages and committed source were inspected without switching branches.
No numerical import, solve, benchmark or test was run. No CI log root-cause
diagnosis or general code-quality approval is claimed. Head checks are old
branch results, not verification against today's main.

`pr-*-git.json`, product patches, original #35 fix/test patches, PR metadata
and unmerged-commit lists preserve exact inspected inputs. A local metadata
summary initially encountered null GitHub file/commit arrays for the large
PR; raw responses were retained and Git comparisons supplied the actual
current merge-base extent. An incorrect documentation lookup was abandoned;
the consolidation finding rests on committed Git history and product mapping.
This report is local evidence only and is not committed or pushed.

## Authorised disposition completed — 16 October 2026

User authorised closing #65, #64, #62 and #57 while preserving branches and
evidence, and keeping #35 open with a bounded salvage plan. All four are now
closed, unmerged. `git ls-remote --heads` verified that all five branch refs
remain at the exact heads recorded above. #35 is still open at `090e2c97`.
Original PR bodies, discussions, commits, checks, branch refs and local
investigation records remain preserved. See `CLOSURE_RECEIPT.json`.

The next task is planning only: choose one small current-main salvage from
#35, retain the broader branch as reference, and exclude implementation,
numerical execution, CI reruns and retired-programme resumption. Mistral is
assigned a bounded read-only source assessment; OpenAI owns final scope and
acceptance criteria. No old execution budget is renewed by this plan.

The bounded plan is now saved at
`docs/agent_plans/PR35_IMMUTABLE_VECTOR_SALVAGE_PLAN_20261016.md`.
Mistral completed 12 read-only inspections; the current signature binding
means the original cache defect still needs a current supported-route
reproducer. Its initial turn limit ended before a final handoff, so a two-turn
continuation delivered the preserved planning assessment. The adopted plan
allows one relevance gate, one isolated candidate, one total repair pass and
a proposed 300-second future check cap with 120 seconds reserved. No code,
test execution, commit, push, branch deletion or retired-test reactivation.
#35 remains open, including if the future relevance gate gives a no-change result.
