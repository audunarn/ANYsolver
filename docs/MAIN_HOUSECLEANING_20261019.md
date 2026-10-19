# Main reconciliation and CI handoff — 2026-10-19

The user assigned this owner responsibility for **all edits on main**, then
authorized push and fixes for fixable CI issues **without starting development**.
This supersedes the earlier contact task's no-push restriction for this main
integration. It does not authorize new solver features, scientific tolerance
changes, renewed historical runs, PyPI publication or changes to sibling repos.

Baseline: main `49d2536c233f0987bbd4968ed06bb07dcc550d90`, after the contact merge.
The 13 remaining tracked edits and 942 untracked files were inventoried in
`C:/ANYworkspaceWork/main-housecleaning-20261019/`. Existing main source edits
were adopted, not discarded: prepared static recovery/response/staging, result
capsules and NumPy-only results runtime, optional native authority guard,
development marine/Sestra tools, associated examples, tests and documentation.
This reconciliation does not qualify all those development capabilities.

## Cleanup and evidence

820 untracked historical diagnostic/output/temp files (55,538,575 logical bytes)
were preserved in the individually rehashed ZIP
`C:/ANYworkspaceWork/main-housecleaning-20261019/preserved-development-output-20261019.zip`.
Archive size: 17,974,386 bytes. SHA256:
`bff21d38c5efebb2ad7aafbd2cbe1749352c9b909a49719d5c43e965d6020f3a`.
Only verified redundant originals were removed. Readable top-level historical
handoffs are copied in `development-history-20261019/`; their old paths/authorities
are historical. The complete [archive manifest](MAIN_HOUSECLEANING_20261019_ARCHIVE.json)
maps exact original paths, sizes, hashes and recovery instructions. No contact
evidence, environment, tracked source or historical numerical lock was selected.
Generated output/results-wheel/test-temp locations now have narrow ignore rules.

## CI wiring repairs

- Install the same-checkout `packages/results` runtime before installing ANYsolver
  editable/wheel distributions; make the resolver see its built wheel. Preserve
  the full original matrix, two workers and 2,400-second command limit.
- Version the unchanged SESTRA three-case input under `tests/fixtures/` instead
  of requiring an ignored workstation report tree. The test oracle is unchanged.
- Two development test modules require optional marine providers; absence is an
  explicit collection skip, consistent with the existing Morison module. This
  is not optional-provider verification or a scientific pass, and changes no
  frozen contact gate.

The earlier GitHub main run at `b0202d335` had native replay/field/source-binding
failures and command timeouts. See the new-run CI disposition below; do not assume
the main merge or this cleanup fixes scientific failures.

## Verification and publication state

The reconciled latest results are **576 passed, 109 skipped, 22 failed**. The 22
remaining failures are SESTRA development checks requiring behavior in five
uncommitted ANYfileIO source files; the dependency's committed HEAD remains
`db73950`, matching CI's pinned baseline. No sibling files were edited, no failed
scientific assertion was skipped, and these failures remain tracked for the
ANYfileIO owner rather than starting cross-repository development here.

All initial failures/setup errors and subsequent affected-only checks are retained.
Temporary-directory ACL and child-interpreter NumPy-path problems were corrected
in local disposable execution setup. Missing optional ANYloads/ANYhydro and ANYpost
consumer installations produce explicit skips; installed-provider/API errors still
fail. Native CPP/archived-wheel checks requiring unavailable artifacts also remain
skipped, not passed. No passed broad batch was repeated.

93 adopted Python files compile; both same-checkout wheels build offline, with
727 solver and six results files matching source exactly and no results package
leaked into the core wheel. Source and core-wheel license compliance checks pass.
These are packaging checks, not an installed/full/native qualification. The fresh
900-second local allowance is CLOSED; unused time is forfeited. See the compact
[check results](main-housecleaning-20261019/RECONCILIATION_RESULTS.json) and
[execution closure](main-housecleaning-20261019/EXECUTION_CLOSURE.json). Full command,
process-wall, sampled RSS, stdout/stderr and JUnit receipts remain in the task folder.

Main was pushed as `4074eb8b163c1d04cd5e1faed742a237680c01fd`; its
[first Actions run](https://github.com/audunarn/ANYsolver/actions/runs/39327963777)
confirmed license, resolver, both operating-system wheel smoke, ecosystem
compatibility and acceleration jobs. That run also exposed integration failures
and scientific/evidence failures. It is not an all-green acceptance receipt.
The grouped repair commit containing this update is a follow-up to that source
commit; consult the [main workflow runs](https://github.com/audunarn/ANYsolver/actions/workflows/ci.yml)
for its own exact SHA and outcome. No PyPI publication is authorized.

The grouped repairs pass **29 focused checks**: portable saved-cut evidence
(original raw SHA retained), the exact24-field registered full-path descriptor
(no saved solution/history used), prospective source-only Q4 binding and its
refusal controls, workflow/package-document golden expectations, updated fake
class-admission seam, independent stdlib deepcopy probe, and trusted warmup
instrumentation. Original Q4 admission/revalidation has real guard cost and is
separately counted; no overall speedup or guard-free capture is claimed. No
`src/` file or scientific tolerance changed in this follow-up. See
[CI repair results](main-housecleaning-20261019/CI_REPAIR_RESULTS.json).

The old Q4 binding record remains unchanged. Its new20261019 successor preserves
strict whole-file hashes and the original47-root/159-symbol mechanics payload,
with a separately reviewed disjoint beam/coupling carrier delta and previously
accepted `fe_core` identity-lifecycle repair. Historical41-case/123-phase evidence
remains historical; physical acceptance, C5 exception and CI credit do not transfer.
The [source review](reference_cases/Q4_SOURCE_BINDING_REVIEW_20261019.md) and
[new exact record](reference_cases/e4_pl_q4_source_binding_20261019.json) state this
boundary. The fresh200s repair allowance is CLOSED; earlier failed checks are
retained and unused authority forfeited.

## Remaining CI issues requiring a separate decision or development

- SESTRA development tests depend on five uncommitted ANYfileIO files:
  `__init__.py`, `sesam/__init__.py`, `sesam/document.py`, `sesam/semantics.py`,
  `sesam/sif.py`. That owner's committed baseline is still `db73950`. No sibling
  edits/publication or parser/physics changes were attempted here.
- C5's strict original reaction assertion still fails at
  `1.0312477801088957e-5`. The [original scoped acceptance](main-housecleaning-20261019/C5_SCOPED_ACCEPTANCE_20261016.json)
  accepts a named historical observation, expressly creates no future envelope,
  forbids skip/xfail/threshold edits and requires reassessment after identity
  changes. It is not an automatic current-CI waiver; the original FAIL remains.
- The full enriched seven-gate reference test is a fresh independent solve/work/
  gap assay, bound to18 files and3896 historical source identities. One of its
 18 immediate hashes already differs. Copying one binding JSON is insufficient.
  A current portable binding and fresh scientific authority need their own scope.
  The [Read review](main-housecleaning-20261019/ENRICHED_REFERENCE_REVIEW.md) proposes
  an opt-in/skip route; **that proposal was not adopted**. The existing full test
  and all seven assertions remain unchanged and failures visible.
- Native curved checkpoint bit equality and changed-definition replay failures,
  a connected construction120s lifetime failure, and an unresolved sliding-friction
  force predictor were observed. Do not rewrite old checkpoint identities, relax
  lifetime/physics criteria or tune solver behavior merely to obtain green CI.
  Current public full364 enriched-path execution may reveal further genuine
  failures once its portable input is available; its criteria are unchanged.

These remaining issues do not alter the already delivered scoped contact bundle.
They prevent claiming complete CI, full programme qualification or release.

## Deferred findings: do not silently claim completion

Supporting OpenAI Read reviews found these concerns outside ordinary CI wiring;
no new product development is authorized to resolve them here:

1. `sestra_verification.execute_reference` imports dev-only psutil during timeout
   cleanup after launch. A base installation without psutil may fail cleanup.
   Do not launch external reference tools without available cleanup support.
2. The benchmark visualization path requires undeclared matplotlib; standalone
   accuracy PDF generation requires reportlab. Those tools need their documented
   local dependencies, and neither is a qualification result.
3. The results project maps sources outside its project root. Checkout wheel
   builds and standalone extracted-sdist reconstruction are distinct; source
   distribution completeness is not established by a checkout wheel.
4. A possible detailed prepared-recovery formula-module rebinding admission gap
   was identified by inspection, not reproduced. Capsule registry guards provide
   separate protection; do not claim a demonstrated exploit or completed repair.

The reviews performed no numerical runs. Mistral/local availability remained
cached unavailable; this supporting assessment does not establish different-family
independence. Full reports remain in the task directory. For the general-contact
candidate's measured accuracy, operating limits and prioritized scientific work,
start with [the contact handoff](GENERAL_CONTACT_CANDIDATE_HANDOFF_20261019.md).
