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

Publication: user-authorized main push and one current workflow assessment remain
in progress. Preserve scientific failures if they persist; only integration,
installation, packaging and CI wiring fixes are in scope. Final remote SHA/run
status will be recorded at handoff.

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
