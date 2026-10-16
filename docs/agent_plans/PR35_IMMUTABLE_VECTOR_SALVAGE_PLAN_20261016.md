# PR35: bounded immutable-vector salvage

Status: SECOND USER-AUTHORIZED REPAIR PASS COMPLETE, 16 October 2026. The
focused candidate check passed (29 passed), the final production replay
passed, and the existing active regressions passed together (62 passed);
the raw retirement-manifest metadata assertion failed (exit 1) solely on
Git checkout LF/CRLF byte differences, and the parent adjudicated the
manifest identity as unchanged (`MANIFEST_IDENTITY_ADJUDICATION.json`).
Accepted by the independent parent review for this bounded correctness slice.
PR35 remains open; the accepted local salvage branch is separate from its
original remote branch. The prospective slice below was
executed in the isolated worktree `pr35-immutable-vector-salvage-20261016`
under the authorized execution record; see the execution records at the end
of this note and `.development/pr35-execution/HANDOFF.md`. No commits or
pushes were made by the worker. The earlier stopped archival snapshot remains
historical and unaccepted; the corrected candidate is accepted below. The
first-pass failure history below is preserved as history and is not
rewritten as successful.

## Decision and scope

Consider only the original idempotent immutable-vector normalization from
`a8428e0dada73a7d377ec31f0c18fe1da5e27e1f`, not the complete 21-commit branch.
Reference head: `090e2c9756fd2d5e7f8378a6379b87b477b39fbe`; inspected main:
`8475718b9262e120607c9d3861923f9c79f13e55`. Recheck identities if execution
is later authorised; use a fresh branch from then-current main and preserve
the original PR branch, source and evidence. Do not rebase or merge it wholesale.

Potential outcome: stop recreating an already canonical immutable vector when
that recreation demonstrably disrupts a current required identity/cache
contract. No runtime speedup, structural accuracy or convergence claim.
No public API, physics, element law, tolerance, cache authority or admission
change. The retirement manifest and frozen programme source/tests stay intact.

Mistral's read-only inspection confirmed that the old helper is absent, while
current S3 plan validation binds revisions/material state rather than explicit
vector identity. This does not prove current cache invalidation. The old
regression and historical pass counts are reference evidence, not acceptance.

## 1. Resolve relevance before coding

One Mistral owner traces existing callers of
`_freeze_qualified_element_vector_inputs` through a currently supported shared
element/recovery workflow. Use one small, predetermined fixture and controls;
do not rename or copy a retired programme fixture to bypass retirement.
Freeze the permitted active checks and effective settings before execution.

Demonstrate on current main both a reachable canonical-input recreation and
its consequence for an existing required identity/cache contract. Record
actual input identities and cache hit/miss evidence; a source-code difference,
an extra allocation alone, or an artificial direct-helper example is insufficient.

Stop without a patch if the old problem is absent, already handled by current
revision binding, reachable only through a retired/unsupported route, or cannot
be established within the gate allowance. Record that result; keep #35 open
for the owner's disposition. Do not switch to another optimization candidate.

## 2. One isolated candidate, only after the gate passes

Product ownership is limited to `src/anysolver/fe_core.py`: recognize the
existing canonical immutable representation and retain its object identity.
Every other input follows the unchanged normalization path. Add one new active
shared-contract test module, provisionally `tests/test_qualified_vector_identity.py`,
and update this note. Do not edit frozen historical S3/GE tests or change their
selection. If production integration requires another product file, stop and
report that boundary rather than expanding this slice.

Preserve values, dtype, shape and existing error behavior. The fast path must
prove immutable backing, not merely a non-writeable flag. Restrict it to exact
supported ndarray/vector forms; read-only views of mutable buffers, owning
arrays with mutable storage, subclasses, wrong dtype/byte order, noncontiguous
or unexpected shapes fall through to existing handling. Include scalar/shape
normalization so the shortcut cannot silently change the old conversion result.
Preserve model ownership, copy isolation, revisions, invalidation and refusals.

## 3. Fixed verification set

Use exact identity/backing assertions and the existing applicable numerical
criteria. Compare normalization values/dtype/shape to the original path.

1. Canonical immutable `reference_normal` and `material_direction`: repeated
   normalization retains identity and contents; mutation remains refused.
2. Fixed fallback cases: writable ndarray, owning read-only ndarray, read-only
   view of a writable array, bytearray-backed memoryview, nonnative dtype,
   subclass, strided view and unexpected/scalar shape. Preserve old outcomes;
   do not weaken or introduce public admission to make the check pass.
3. `None`, nonqualified elements and independent model/copy ownership retain
   current behavior. Supported vector replacement still invalidates stale
   prepared state, and existing mutation/refusal controls still trigger.
4. The single relevance-gate production sequence demonstrates the corrected
   identity/cache behavior and unchanged physical outputs. Helper tests alone
   do not establish this integration result.
5. Run the frozen affected active shared element, recovery and preparation
   checks, including relevant copy/invalidation refusals. If required coverage
   is frozen/retired or cannot fit the allowance, stop with that unmet gate.

Do not execute any of the historical benchmarks or retired modules from #35.
This is a correctness/identity slice, not a performance qualification campaign.

## Ownership, bounds and completion

Mistral owns the future connected relevance/implementation/check/repair/handoff
slice. OpenAI adopts contract decisions, independently reviews the resulting
diff and evidence, and owns final acceptance and Git delivery. A Read worker
cannot authorise edits or execution. Preserve unrelated work in an isolated
checkout; remove the disposable checkout/environment after an approved handoff.

Proposed fresh check allowance, effective only after implementation is requested:
300 seconds cumulative process-wall, including failed attempts and subprocess
trees, one serial job. At most 60 seconds for the relevance gate; preserve
120 seconds for final verification. One candidate and at most one focused
repair pass in total. These bounds do not renew any historical run allowance.
Record exact commands, source/input identity, effective settings, outcomes,
precise process-wall time, cumulative usage and remaining allowance; retain
failures and partial timeout output. No sweep, automatic extension or repeated
passed check without changed input or unresolved concern.

Accept only when the demonstrated production defect is resolved, all fixed
checks pass under unchanged criteria, and independent review has no unresolved
finding. Stop if a boundary is crossed, the repair pass leaves a required case
failing, or remaining verification cannot fit the allowance. Preserve evidence;
do not partially merge or lower the gate. No further optimization follows.

Deferred: Q4 recovery/mass batching and guard rebinds; kernel warmup; verification
result caches; recovery thread changes; CI cleanup; benchmark changes and the
remaining branch commits. Reconsideration requires a separate bounded proposal,
not automatic fallback when the identity candidate stops. #35 stays open.

## Planning evidence

Local record: `C:/Github/ANYsolver/.development/pr-triage-20261016/`.
`REPORT.md` and `CLOSURE_RECEIPT.json` record the four authorised PR closures
and preserved branches/evidence. `MISTRAL_TOOL_OUTCOMES.json` records 12
completed read-only tool outcomes. The first worker exhausted its turn bound
without a final handoff; a two-turn read-only continuation supplied
`MISTRAL_PR35_PLAN_HANDOFF.md`. No implementation or numerical verification
occurred. OpenAI tightened its suggested per-check repairs to one total repair
pass, added the explicit wall cap, and retained the user's requirement that
#35 remain open even after a no-change outcome. Plan adoption is not candidate
acceptance, publication or authority to resume the retired programme.

## Execution record — 16 October 2026 (authorized candidate + single review repair pass)

The prospective slice above was executed in the isolated worktree
`pr35-immutable-vector-salvage-20261016` (branch
`codex/pr35-immutable-vector-salvage`, base
`8475718b9262e120607c9d3861923f9c79f13e55`; no commits, no pushes, no
branch/index/history changes).

Changed files: `src/anysolver/fe_core.py` (canonical recognizer gains
dtype-metadata and alignment rejections; both helper docstrings reworded to
recovery plan preparation), `tests/test_qualified_vector_identity.py`
(factory-based readonly params replacing invalid `.setflags(...) or None`
entries, immutable-terminal-owner check instead of `chained.base is
canonical`, scalar fallback shape corrected to the unchanged old normalizer
result `(1,)`, and readonly-bytearray / metadata-bearing / unaligned
fallback regressions), this note, and `.development/pr35-execution/**`.

Candidate check (single authorized run, via
`.development/pr35-execution/run_check.py candidate 90`):
`scripts/run_portable_ci.py --development
tests/test_qualified_vector_identity.py --jit off --timeout-seconds 80
--memory-limit-mib 2048` — FAIL: 28 passed, 1 failed. Unresolved failure:
`test_freeze_keeps_unexpected_shapes_on_original_normalizer` —
`float(scalar)` raises TypeError because NumPy 2.4 no longer converts
1-element arrays; the corrected shape `(1,)` itself passed and the
compatible assertion is `scalar[0] == 2.0`. Per the single-repair-pass
contract the failure is preserved unrepaired; evidence in
`.development/pr35-execution/CHECK-candidate-20261016T113257157366Z`.

Budget: 2.8064674 s baseline gate (spent, not rerun) + 7.0532334 s candidate
check = 9.8597008 s of the 300 s cumulative cap; 290.1402992 s remains; the
120 s final verification reserve is intact and not consumed. The single
focused review repair pass is used; no second pass follows a required check
failure. Parent final acceptance, the final production replay and the
existing active regressions remain pending. PR35 stays open.

## Final parent disposition — first pass (historical)

This section records the disposition after the first repair pass, before
the user-authorized continuation recorded at the end of this note; it is
preserved unchanged as history.

STOPPED, UNACCEPTED. The production defect is demonstrated, and the candidate
regression for recovery/warm stiffness passed, but the required scalar fallback
check failed after the one review repair pass. No further correction or numerical
verification is authorised by this slice. Final production replay and affected
existing regression suites were not run; their absence is not a pass.

Preserved evidence and restoration entrypoint:
`C:/Github/ANYsolver/.development/pr-triage-20261016/pr35-execution/`.
Read FINAL_REPORT.md, FINAL_RECEIPT.json, worker-evidence/HANDOFF.md and receipts.
A local archival candidate snapshot may be retained on
`codex/pr35-immutable-vector-salvage`; main and remote PR35 remain unchanged.
The disposable checkout is removed after byte-verified preservation. No pushes.

Precise harness accounting: 9.8597008 seconds. One additional NumPy-only probe
ran outside the required harness; its saved completed-tool interval is 0.200
seconds and is conservatively charged, for 10.0597008 seconds accounted. Its
exact process wall is unavailable; no rerun reconstructed it. The 300-second
cap was not approached, but the repair-count stop applies regardless of unused
time. Preserve this accounting limitation and do not renew unused authority.

## Continuation execution record — 16 October 2026 (user-authorized second focused repair pass)

After the first-pass stop the user explicitly authorized one additional
focused repair pass within the original 300 s cumulative cap; this
continuation used it. Two focused repair passes total; no third pass
follows. No commits, pushes, branch, index or history changes and no
dependency changes. Base remains
`8475718b9262e120607c9d3861923f9c79f13e55`.

Edit this pass: `tests/test_qualified_vector_identity.py` only — the
scalar fallback assertion in
`test_freeze_keeps_unexpected_shapes_on_original_normalizer` changed from
`assert float(scalar) == 2.0` to `assert scalar[0] == 2.0` (NumPy 2.4 no
longer converts 1-element arrays through `float()`); the shape `(1,)` and
immutability assertions are unchanged. Product source
`src/anysolver/fe_core.py` is unchanged this pass (the first-pass candidate
is retained). This note and `.development/pr35-execution/**` complete the
changed set.

Checks (single serial jobs via `.development/pr35-execution/run_check.py`;
JIT off, all thread pools 1, plugin autoload off, retired opt-in 0,
`PYTHONHASHSEED=0`; Python 3.13.9, NumPy 2.4.3, solver 0.4.7 from the
isolated worktree `src`; source sha256 at every check:
`src/anysolver/fe_core.py`
07549c53099a3f4b6ab91d3a4741bcda64a91126935450aa7e463ee0954932da,
`tests/test_qualified_vector_identity.py`
8cb96ab10d90b50a5f77b51c4d4d3710c813cf2eff6789e6e0ef505b4f42e21a):

1. Candidate: `scripts/run_portable_ci.py --development
   tests/test_qualified_vector_identity.py --jit off --timeout-seconds 80
   --memory-limit-mib 2048` — PASS, exit 0, 29 passed in 4.98 s (process
   wall 6.5789794 s); `CHECK-candidate-20261016T114312527088Z`.
2. Final production replay (fixed inputs, changed source only):
   `python -B .development/pr35-execution/production_gate_final.py
   {ATTEMPT}/result.json` — PASS, exit 0, 2.6852968 s;
   `NO_CURRENT_CACHE_DEFECT_ON_FIXED_PRODUCTION_SEQUENCE`: 0 changed normal
   identities, identical values/revisions, exact CSR stiffness, warm plan
   reuse after recovery, 128 elements / 1 translation group / 1 component
   evaluation, `speedup_claimed: false`;
   `CHECK-final-20261016T114324082996Z` (result.json).
3. Existing active frozen regressions together, once:
   `scripts/run_portable_ci.py --development
   tests/test_e4_pl_s3_reference_batch.py
   tests/test_qualified_mutation_epoch.py --jit off --timeout-seconds 150
   --memory-limit-mib 2048` — PASS, exit 0, 62 passed in 22.29 s (process
   wall 24.0088253 s); frozen test sha256 match `FINAL_SELECTION.json`
   (c485ffd0..., e5c7beb6...); `CHECK-final-20261016T114339825342Z`.
4. Selection metadata: `python -B
   .development/pr35-execution/selection_metadata_check.py` — exit 1
   (FAIL), 11.5321145 s; `CHECK-final-20261016T114426964385Z` and
   `SELECTION_METADATA.json`. All actual selection predicates passed: all
   three target modules active in merge_test_modules (658 modules), empty
   retired intersection, retired opt-in 0, production runtime evidence
   present. The only failing predicate is `manifest_hash_matches_baseline`:
   the raw checkout sha256
   a5f8ed5767fbc5421bf7ca3f261dd115dbba5303cead89af87e80b53e902a1eb differs
   from the baseline
   33157ae2fef4441b6dbe1e851f35d52bb38e90bd80727d5e321d2ee73b7ee81e because
   Git checkout converted LF to CRLF.

Parent identity adjudication (adopted source-identity decision,
`.development/pr35-execution/MANIFEST_IDENTITY_ADJUDICATION.json`,
`RESOLVED_CHECKOUT_LINE_ENDINGS_ONLY`): the checkout's LF-normalized bytes
hash exactly to the main raw sha256 (33157ae2...), the text compares equal
after exact CRLF-to-LF conversion, and the Git blob
69c010a8216b9cb43c7a53fb9d01dda924125102 is identical at base, main and
the isolated checkout. The raw hash mismatch was caused solely by Git
checkout line endings; retirement content and Git identity are unchanged.
The failed metadata receipt and the script are preserved unchanged; no
raw-byte pass is claimed, and no rerun, repair or manifest alteration
followed. No candidate repair is needed.

Budget: cumulative accounted 54.8649168 s of the 300 s cap; precisely
measured checks total 54.6649168 s (baseline gate 2.8064674 s + first
candidate 7.0532334 s + second candidate 6.5789794 s + production replay
2.6852968 s + regressions 24.0088253 s + metadata 11.5321145 s) plus the
conservative 0.200 s prior NumPy-only probe charge; 245.1350832 s remains.
The prior probe-accounting limitation is preserved.

Status: verified against the assigned bounded criteria of this slice;
parent final ownership/hash/evidence acceptance and Git delivery remain
pending. No runtime speedup, structural accuracy or convergence claim.
PR35 stays open.

Evidence: the original planning and first-pass evidence remains at
`C:/Github/ANYsolver/.development/pr-triage-20261016/pr35-execution/`; the
second-pass evidence is under `.development/pr35-execution/` in this
worktree (receipts, `SELECTION_METADATA.json`, `FINAL_SELECTION.json`,
`MANIFEST_IDENTITY_ADJUDICATION.json`, `CHECKPOINT.md`,
`PRIOR_HANDOFF.md`, `HANDOFF.md`, `BUDGET.json`) and is to be archived by
the parent under `continuation-scalar-repair` when this worktree is
archived.

## Final parent acceptance and local delivery

OpenAI independently inspected the product diff, exact scalar-only test delta,
production result, both passing test outputs, effective runtime, worker command
audit and complete budget. The raw manifest failure is resolved by exact
line-ending comparison and matching Git identity, without another execution.
The bounded immutable-vector identity repair is accepted: 91 tests passed,
the fixed production sequence preserves warm reuse and exact stiffness, and
no consequential finding remains. This is a correctness repair; no measured
speedup or broader solver qualification is claimed.

Delivery is a local commit on `codex/pr35-immutable-vector-salvage` based on
`8475718b`; main, the original PR35 branch and unrelated work are preserved.
No pushes. Evidence, including failed attempts, is retained at
`C:/Github/ANYsolver/.development/pr-triage-20261016/pr35-execution/continuation-scalar-repair/`.
The disposable checkout is removed after byte-verified preservation.
