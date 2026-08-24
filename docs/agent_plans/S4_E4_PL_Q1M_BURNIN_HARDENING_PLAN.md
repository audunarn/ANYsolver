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
  request.  The live contract records the exact quick and package commands,
  including the correction-5 clean ANYgeometry root; the runner constructs
  the remaining required source environment itself.
- The package lane accepts only tracked/index-clean committed `HEAD` inputs.
  It creates a Git archive for ANYsolver, ANYmesh, ANYgeometry, ANYmaterial,
  and ANYfileIO, excluding every untracked path, and binds each commit, tree,
  archive byte/hash identity, and extracted-file-graph hash.  Candidate
  ANYsolver and paired ANYfem must be fully clean including untracked paths;
  the four archived sibling inputs may retain unrelated untracked work.  A
  frozen source-root override is permitted only when its exact commit/tree is
  bound by the live contract; corrections 4 and 5 use the isolated clean
  `q1m-anygeometry-frozen` worktree so unrelated tracked development in the
  shared ANYgeometry checkout is never imported.
- Each pytest lane creates temporary distribution metadata from the exact
  name/version pairs in the five frozen `pyproject.toml` files and places it
  ahead of globally installed metadata.  This metadata-only overlay is
  deleted with the lane-local temp directory; imported modules still come
  exclusively from the frozen source roots.  It prevents an unrelated stale
  installed distribution from misidentifying the source under test without
  weakening ANYfileIO's semantic dependency check.
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

A correction-5 failure uses commit subject
`docs: record E4 PL Q1M correction-5 blocked gate` and exactly:

1. `docs/reference_cases/e4_pl_q1m_correction5_blocked_gate_result.json`
2. `docs/reference_cases/e4_pl_q1m_correction5_blocked_status.json`
3. `docs/reference_cases/e4_pl_q1m_correction5_blocked_review.json`

Its status uses the same status schema, terminal
`BLOCKED_E4_PL_Q1M_CORRECTION_5_BURN_IN_GATE`, clean-gate index 0, and keeps legacy removal
unauthorized.  Its accepted review verdict is
`ACCEPT_Q1M_CORRECTION_5_BLOCKED_GATE_NO_P0_P1`.

The first failed gate remains immutable under its original three blocked paths.
Its exact authority is preserved byte-for-byte as
`docs/reference_cases/e4_pl_q1m_burnin_contract_cycle0.json`.  The first
correction failure and its global-pytest-temp incident remain immutable under
`docs/reference_cases/e4_pl_q1m_burnin_contract_cycle1.json`.  The live
correction-2 ecosystem failure remains immutable under
`docs/reference_cases/e4_pl_q1m_burnin_contract_cycle2.json`.  The
correction-3 source-metadata failure remains immutable under
`docs/reference_cases/e4_pl_q1m_burnin_contract_cycle3.json`.  The live
correction-4 performance-diagnostic failure remains immutable under
`docs/reference_cases/e4_pl_q1m_burnin_contract_cycle4.json`.  The live
contract binds fresh correction-5 resource requests and never rewrites any
historical result.

Correction 3 closes only the observed compatibility gaps: fail-closed solver
quantity resolution, atomic/oriented mapped-face splitting, common-grid-corner
preparation, and conforming quality-compliant impact refinement.  It freezes
all five sibling commit/tree identities.  Protected integration follows the
dependency order ANYmesh, ANYsolver Q1M, then ANYfem; the paired ANYfem commit
is still executed locally before Q1M adjudication.  No E4-PL Q4 mechanics file
changes in this correction.

Correction 4 changes only the burn-in harness and its authority.  It derives
ephemeral metadata from the already frozen source graph so
`importlib.metadata` observes ANYmesher 0.2.5 rather than the unrelated global
0.1.0 installation that blocked correction 3.  It does not modify ANYfileIO,
any production package, or any E4-PL Q4 mechanic.

Correction 5 changes only the two performance assertions that still required
the retired `advanced_s4_stiffness` diagnostic after the functional corpus
was migrated to the qualified Q4 selector, plus this authority packet.  The
existing numerical matrix-equality assertions remain unchanged.  The updated
assertions require the production `qualified_e4_pl_stiffness` route and its
exact shared-geometry-cache counts; no tolerance, coefficient, source,
mechanics, or performance threshold changes.

All pytest lanes use a fresh ignored workspace-local `--basetemp` and remove
it after execution, avoiding user-global Windows ACL state without changing
the registered outer resource commands.

All adjudication reviews use schema `anysolver.s4.e4-pl-q1m-independent-review-v1` and
exactly five top-level keys: `findings`, `reviewed_inputs`,
`reviewer_independence`, `schema`, and `verdict`.  Acceptance requires empty
findings; exact independence assertions that the reviewer did not author the
candidate, did not execute the resource lanes, and reviewed frozen evidence
only; and exact SHA-256 bindings named `contract_sha256`,
`gate_result_sha256`, and `status_sha256`.  No implementation, source, test,
contract, or unrelated path may enter either evidence-only adjudication
commit.
