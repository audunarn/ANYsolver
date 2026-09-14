# G3a correction and bounded formal confirmation protocol

## Cancellation-observation successor

Candidate `28af8a4a4641cdebf85315dd7fb82fb3bc6e93a6` and its passing
101-test rehearsal remain preserved but are not formally accepted. Independent
review G3A-IR-03 found that callback number two was a line-search callback,
not necessarily the final acceptance callback: solve resets multipliers even
when reapplying an accepted nonzero load. This successor changes tests and
this protocol only relative to that candidate. No runtime/runner change.

For every prepublication cancellation, observe unchanged native system calls.
Require the first KKT residual to exceed the frozen convergence threshold,
then two consecutive converged returns at exactly identical displacement and
multiplier inputs (accepted line search and main-iteration reevaluation).
Cancel only afterward and assert the calling code is solve -> check -> cancel,
not system -> check -> cancel. Record residual norms and call counts. Preserve
the existing snapshot, no-trial, authenticated replay and continuation checks.
The older single-graph final_cancel case uses the same verified observation.
The ordered 101-test and 54-record inventories remain unchanged. Repeat the
corrected smoke, full rehearsal and independent review before formal execution.

Parent: blocked review `edad651af3460aa33283686e4f9345190a3b0094`.
Original candidate `5a4a4ac`, development evidence and independent review v1
remain immutable. This successor changes only the private G3 restart preflight,
G3 tests and additive confirmation infrastructure. It changes no native element
mechanics, constraint equations, tolerances, defaults, public routes or versions.

## Corrections and fixed inventories

G3A-IR-01: all four frozen native graphs receive full stationary/Schur
comparisons with nonzero internal residual, all three physical covariance
transports, and explicit per-step shared-Q/element-owned-triad comparisons.
G3A-IR-02: all four receive cancellation at entry and immediately before
publication plus virgin and nonzero accepted-prefix final-element preparation
rollback. Restore only the deliberate test mutation after verifying unchanged
committed state, then verify authenticated replay and continuation. N_BRACED5
exercises stale/foreign tokens against commit, discard and state submission,
requiring no disturbance of either owner's committed or valid pending state.

The early restart preflight reconstructs graph IDs, incidence, components and
counts from serialized connectivity, authenticating exact graph schema,
native-only policy and empty adapter allowlist before any element construction.
Twelve metadata mutations must reject before element or native-state work.
A second consistency comparison with real element topology occurs before owner
construction. Native state replay and existing serialization semantics remain.

Freeze exactly 101 ordered G3 test IDs in
`ge_beam3_g3a_confirmation_inventory.json` and 54 supplemental scientific
record names in `ge_beam3_g3a_correction_records.json`. The supplemental names
cover four pose histories, four Schur comparisons, twelve covariance cases,
eight preparation failures, eight cancellation cases, six token cases and
twelve restart-preflight mutations. They are not 54 additional test passes.

## Execution and evidence

First run the targeted correction smoke, the separate infrastructure tests,
G1 and G2 regressions, and a complete G3 rehearsal. Freeze the exact candidate
commit/tree and obtain independent acceptance of implementation, coverage and
runner. The accepted five-key review must bind that commit/tree and have empty
findings and an independent reviewer. Its externally supplied SHA-256 is
required before formal output directory creation or any mechanics import.

The formal coordinator performs two serial fresh-process cycles, each with
one numerical-library thread, 24 GiB per complete process tree, 600 seconds
wall time and 120 seconds without CPU/output progress. The wave bound is
1,800 seconds; no child starts without 600 seconds remaining. No automatic
retry or output reuse is permitted. Up to three workers may run in separate
development lanes, but formal cycles are serial. Time and RSS are diagnostics,
not performance acceptance thresholds.

Bind candidate commit/tree, every runtime source file, all runner/test/helper/
fixture/contract inputs, Python executable/version and installed distribution
versions. Check identity before and after each cycle and before publication.
All files use exclusive creation. Failure retains external diagnostics and
never publishes a partial accepted aggregate.

Every cycle must have the exact ordered test inventory, 303 passed
setup/call/teardown reports with no skips, six completed-operation checkpoint
categories, the original branch development packet (still qualification=false)
and exactly 54 canonical supplemental files. Require byte-identical packets,
reports and supplemental scientific files between cycles. Source normalization
uses LF; generated evidence is compared as raw bytes, without normalization.

Publish the distinct canonical aggregate only after all checks pass through
a verified same-volume pending file and atomic no-overwrite link. Record the
input/review hashes, inventories and supplemental hashes. Independently review
the finished evidence before recording acceptance. Archive raw logs and files
with byte counts and SHA-256; preserve rehearsal failures if any.

## Decision and scope

Any authority, process/evidence, state/restart, constraint/work or graph failure
blocks formal confirmation; do not waive a correctness finding based on its
review priority. A rehearsal result is REHEARSAL_ONLY. Successful independently
reviewed formal evidence may record only:
`PROVISIONAL_GO_GE_BEAM3_G3A_NATIVE_GRAPH_ELASTIC_STATIC_ONLY`.

This closes the frozen private native exact-elastic graph slice only, not
mixed-family G3b/G3c, history-bearing G4, public-integration G5 or full beam
qualification. No merge, release, default change or new element formulation
is authorized by this protocol.
