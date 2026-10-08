# User-requested pause: F03 registration schema draft

23 September 2026. The user requested a pause for an app restart. Do not
continue implementation, tests, review, registration, or scientific execution
until the user resumes the task.

Worktree: `C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling`

Branch: `codex/b3-ge-e4-pl-integration`

Last committed HEAD: `a67ac2e21e4d4961eab7ada2de2d0cd8f8175f30`

Main remains untouched. G0B remains open and G1 remains barred. No scientific
case was registered or launched.

## Completed and committed immediately before pause

Commit `a67ac2e2` adds the canonical F03 failure-receipt factory and adversarial
tests. It distinguishes failed evidence from failed execution, preserves
validated producer work, writes exclusively, rejects a successful lifecycle
that requires full adjudication, and propagates memory/programming faults.

Verification completed before the pause:

- Focused lifecycle/receipt/adjudicator/supervisor suite: 43 passed.
- Complete synthetic F03 local-scientific suite: 252 passed, zero failures or
  errors. JUnit:
  `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/f03-failure-factory-broad-20260923.xml`.
- Independent review: no findings; 11 focused and 65 bounded tests passed.
- No scientific case was launched.

## Uncommitted draft owned by the parent

New file:

- `scripts/_b3_e4_f03_local_scientific_registration.py`

This file was added immediately before the pause and has **not** been compiled,
tested, reviewed, or committed. It proposes a bounded canonical registration
schema covering source roles, source and accepted-main commits, runtime and
package identities, hardware, thread limits, process/resource contracts,
tolerances, five case/plan identities, exact child commands, and terminal
precedence. Treat every detail as draft until verification.

No test file for this draft exists yet. No process is pending.

## Exact resume action

1. Read this checkpoint and inspect Git status; expect only this checkpoint and
   the registration module to be uncommitted.
2. Review the draft registration module for schema errors before executing it.
   In particular, check canonical decoding, timestamp strictness, source-role
   completeness, command binding, digest sidecar atomicity/partial-write
   behavior, path/symlink handling, and whether every protocol tolerance is
   represented without duplicating a conflicting authority.
3. Add synthetic registration tests. Do not create a real registration and do
   not launch a scientific case.
4. Run focused bounded tests, correct findings, then obtain independent review
   before committing the registration batch.
5. Continue the previously reviewed coordinator sequence only after this batch
   is closed: child post-start identity/thread verification, typed cancellation,
   read-only case replay, cross-case aggregate adjudication, and coordinator.

Registration and scientific execution remain barred until every coordinator
prerequisite is implemented, tested, independently reviewed, and committed on
a clean source identity.
