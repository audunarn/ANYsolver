# E4-PL Q1M: Burn-in Hardening and Legacy-Q4 Retirement

## Purpose

Harden the production-default E4-PL four-node shell after Q1L activation,
while preserving a visible and reversible compatibility window. This stage
does not change the E4-PL formulation, tolerances, recovery, or state laws.

## Burn-in contract

- E4-PL remains the default for every production Q4 selector.
- Explicit legacy Q4 construction is deprecated and emits
  `LegacyQ4DeprecationWarning`.
- The legacy Q4 rollback remains available through the 0.4.x release line and
  cannot be removed before 0.5.0.
- Removal additionally requires two consecutive clean release gates covering
  the complete functional suite, representative model corpus, parity matrix,
  serialization/restart, and serialized performance checks.
- TRI3, TRI6, Q8, and Q8R remain on `ShellElement` and are not deprecated by
  the Q4 retirement.

## Evidence lanes

1. `quick`: selector, diagnostics, warning, serialization, parity, and focused
   workflow tests required for every change.
2. `functional`: the complete production-functional suite and representative
   model corpus, including the ANYfem solver adapter and closed-form plate
   reference, excluding immutable historical-study authority tests.
3. `package`: build the wheel without source-tree imports, install it into a
   fresh target, and verify the default Q4 and diagnostic API from that target.
4. `performance`: cold/warm and nonlinear batch gates, serialized through the
   repository resource manager.
5. `extended`: historical or research diagnostics, never a merge prerequisite.

All production benchmark and numerical-verification scripts route Q4 fixtures
through the public selector. Low-level compatibility tests use the explicit
`LegacyShellElement` alias, never an ambiguous direct `ShellElement` call.
The paired ANYfem adapter and stored engineering-reference gate are mandatory
for each clean release gate.

The serialized performance command also emits one canonical Q1M observation
after its pytest inventory passes. It records Q4 numerical parity, warm-cache
reuse, and batch-path equality as named hard gates. One warm-up and eleven
qualified-Q4 repetitions establish the gate-1 baseline; the evidence retains
every integer-nanosecond sample and recomputes median, MAD, and nearest-rank
p95. These timings are informational baseline data and authorize no speed
claim.

Legacy Q4 removal is a separate successor change after the burn-in gates are
recorded. A rollback incident resets the two-gate counter.

## Freeze and evidence authority

- Freeze the implementation and harness before running a registered resource
  request.  The bare commands
  `python scripts/run_e4_pl_burnin_gate.py quick` and
  `python scripts/run_e4_pl_burnin_gate.py package` are the exact
  non-resource authorities; the runner constructs the required source
  environment itself.
- The package lane accepts only tracked/index-clean committed `HEAD` inputs.
  It creates a Git archive for ANYsolver, ANYmesh, ANYgeometry, ANYmaterial,
  and ANYfileIO, excluding every untracked path, and binds each commit, tree,
  archive byte/hash identity, and extracted-file-graph hash.  Candidate
  ANYsolver and paired ANYfem must be fully clean including untracked paths;
  the four archived sibling inputs may retain unrelated untracked work.
- Resource commands are bound byte-for-byte through their immutable request
  JSON and command SHA-256.  Required external logs are nonempty and bind an
  exit code; `PASS` requires zero and `FAIL` requires nonzero.
- Execute lanes in the exact order quick, package, functional, ANYfem, and
  performance.  A failed lane is followed only by `NOT_RUN` records, which
  omit timestamps, exit code, and log identity.  A blocked result records at
  least one unique unresolved rollback incident, keeps the clean-gate counter
  at zero, and contains no fabricated package or performance evidence.
- A successful package lane preserves its canonical
  `anysolver.s4.e4-pl-q1m-package-lane-v2` result and ANYsolver wheel outside
  the repository.  Final `anysolver.s4.e4-pl-q1m-gate-result-v2` validation
  requires the real repository, request, executed-lane log, package-result,
  and wheel paths before exclusive evidence creation.

## Adjudication routes

Successful gate 1 uses commit subject
`docs: record E4 PL Q1M clean burn-in gate 1` and exactly:

1. `docs/reference_cases/e4_pl_q1m_gate_result.json`
2. `docs/reference_cases/e4_pl_q1m_status.json`
3. `docs/reference_cases/e4_pl_q1m_review.json`

Its status uses schema `anysolver.s4.e4-pl-q1m-status-v1`, terminal
`Q1M_CLEAN_GATE_1_OF_2_RECORDED`, clean-gate index 1, and keeps legacy removal
unauthorized.  Its accepted review verdict is
`ACCEPT_Q1M_BURN_IN_GATE_1_NO_P0_P1`.

A failed run uses commit subject
`docs: record E4 PL Q1M blocked burn-in gate` and exactly:

1. `docs/reference_cases/e4_pl_q1m_blocked_gate_result.json`
2. `docs/reference_cases/e4_pl_q1m_blocked_status.json`
3. `docs/reference_cases/e4_pl_q1m_blocked_review.json`

Its status uses the same status schema, terminal
`BLOCKED_E4_PL_Q1M_BURN_IN_GATE`, clean-gate index 0, and keeps legacy removal
unauthorized.  Its accepted review verdict is
`ACCEPT_Q1M_BLOCKED_GATE_NO_P0_P1`.

Both reviews use schema `anysolver.s4.e4-pl-q1m-independent-review-v1` and
exactly five top-level keys: `findings`, `reviewed_inputs`,
`reviewer_independence`, `schema`, and `verdict`.  Acceptance requires empty
findings; exact independence assertions that the reviewer did not author the
candidate, did not execute the resource lanes, and reviewed frozen evidence
only; and exact SHA-256 bindings named `contract_sha256`,
`gate_result_sha256`, and `status_sha256`.  No implementation, source, test,
contract, or unrelated path may enter either evidence-only adjudication
commit.
