# F03 local scientific coordinator: reviewed implementation result

23 September 2026. The serial one-use coordinator and its bounded execution
path were committed on `codex/b3-ge-e4-pl-integration` at
`6ed4017787cd37c7529358483b225e131fa4e5fa`. Accepted local main and
`origin/main` were both observed at `be41a77a62e1cd7e1767bda6e955253af0819f91`.
This is an implementation and review checkpoint, not a scientific registration,
executed F03 result, G0B acceptance, or release qualification.

The coordinator prepares an exclusive registration only from a clean committed
candidate and matching accepted-main refs. It binds source, runtime, packages,
hardware, cases, plan archives, limits, threads, tolerances, and exact child
commands. Execution claims the registration once, launches the five frozen
cases serially, enforces the pre-launch cutoff and process-tree limits, and
closes failure/cancellation and the available aggregate without a retry.
It checks the registered source and package identity throughout execution.

Child stdout and stderr are bounded to 8 MiB each. Drainers retain bounded
memory while a child runs; after exit or a bounded drain timeout the supervisor
freezes the captured prefix before the coordinator writes logs. A drain timeout
is a supervisor failure, not a successful execution. The terminal receipt
hashes the resulting log bytes and its reader verifies them. The scientific
index remains child-owned, so post-index interpreter output cannot invalidate
scientific data. The 512 MiB complete case archive reserves the maximum plan,
logs, lifecycle, index, and case-receipt bytes before admitting scientific
evidence. The exact case runner has not been exercised on a real scientific
child.

Verification: the complete local-scientific test selection passed **356 tests**
with **4 Windows symlink-privilege skips**. After the final bounded log-snapshot
fix, affected supervisor, coordinator, and lifecycle checks passed **42 tests**
with **1 such skip**. `git diff --cached --check` passed before commit. An
independent read-only code review found no remaining actionable issue after
the log-accounting, premature-indexing, drain-liveness, and captured-prefix
findings were resolved. Synthetic tests do not constitute a scientific case.

The current Python process imports ANYsolver from `C:/Github/ANYsolver/src`
with installed metadata version `0.4.6`, not from this candidate worktree.
Registration correctly rejects that environment. The next step is an isolated
installation of this exact candidate, installed-package checks, then a fresh
one-use registration and serial five-case run under the frozen protocol.
Preserve all raw outputs and independent adjudication. G0B remains open and G1
is barred until the required mechanics and scientific decisions pass.
