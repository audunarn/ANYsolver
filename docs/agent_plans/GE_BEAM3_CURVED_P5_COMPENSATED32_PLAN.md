# P5 bounded compensated-coordinate comparison

Parent `8058cbb95d4cbd2a5712c056b1fdfe55ffd5acec`, tree
`a78d1f1acfe547bbaf1a95e5ca2166cfac4cbca9`.
Exactly three new paths: this plan, compensated32_diagnostic runner, and
compensated32_diagnostic tests. No existing source or historical record changes.

## Scope

One explicitly compensated 32-element arch, targets 0.1 and 0.095 only.
The first state must commit/replay before the second trial. The second may
converge or fail; preserve the genuine outcome without retry. No onset grid,
eigenvalue analysis, bisection or qualification aggregate is part of this run.

Use the frozen compensated mixed evaluator, assembly and controller. Retain
1e-11 global residual acceptance, 1e-12 total estimated local-force budget,
16 updates, 10 backtracks and 8192 counted mixed evaluations per trial. Carry
coordinate high/low parts into every evaluation, trial, committed checkpoint,
element response and failure snapshot. Exact clamps and targets have zero low
parts. No old failure is reinterpreted or upgraded to an accepted state.

## Authority and resource controls

Before numerical imports, validate clean HEAD, exact direct parent/three-path
extent, environment and sibling identities. Bind all 37 historical external
files: eight original failed-run files, nine controller observations, ten
force-accuracy records and ten centered-chord records. Their consumed requests
and claims remain immutable and unusable for this successor.

After a clean freeze, create one new immutable resource request with the exact
module command and a fresh external output directory. Obtain administrator
APPROVED ledger authority, acquire its exact global slot, invoke the stored
command once and release in finally after all child processes are terminal.
One numerical thread, 24-GiB Windows Job tree limit, 600-second child limit,
300-second inactivity and 890-second coordinator watchdog. No concurrent
heavy work, automatic retry, request reuse or timeout extension.

## Strict diagnostic records

Use `GE_BEAM3_P5_COMPENSATED32_DIAGNOSTIC_V1`, assembly identity
`GE_BEAM3_P5_COMPENSATED_ASSEMBLY_FORCE_ACCURACY_V1`, and coordinate identity
`GE_BEAM3_P5_COMPENSATED_COORDINATES_V1`. Reject missing/nonfinite/unnormalized
parts, inconsistent element-to-node mappings, nonzero prescribed low parts,
foreign schemas, duplicate or noncanonical JSON, dirty inputs and changed
hashes. Bind low parts in the initial checkpoint digest. Candidate progress
includes nonnegative position_low_change_max as well as high-part changes.

Retain and reconstruct a failed trial's actual last successful evaluation,
if any, with `GE_BEAM3_P5_COMPENSATED_FAILED_LAST_EVALUATION_V1`. It is an
uncommitted diagnostic, possibly a rejected candidate. Never invent target
data when the target failed. Revalidate authority and lease before publication.

`RESEARCH_COMPENSATED_COORDINATE_COMPARISON_CAPTURED` may contain either
`TARGET_CONVERGED` or `FAILED`. Process/identity/schema/replay errors block
publication of that diagnostic success. A zero process exit with solver FAILED
is diagnostic capture only. Every result retains production_qualified=false
and `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

The inspector checks structural integrity and consistency, not an independently
authored full mechanics oracle. This comparison cannot qualify the beam. A
converged result supports only preparing a separately frozen onset successor.
The remaining nonlinear/material/mass/dynamics/restart and objective beam-shell
connection requirements remain open.

## Small rehearsal

Two-element success and forced-budget failure, byte identity, complete input
hashes, guard-before-capture, strict parsing, rehashed observation/coordinate
mutations, request consumption and synthetic resource-failure checks precede
freeze. They do not run the 32-element case. Run the compensated assembly/local
regression alongside this rehearsal before requesting resource execution.

Pre-freeze result: all 156 tests in the seven-file small rehearsal passed in
31.95 seconds, including 56 runner checks. All 37 historical byte/hash bindings
passed read-only validation. `git diff --check` passed; no 32-element execution
occurred during this rehearsal.
