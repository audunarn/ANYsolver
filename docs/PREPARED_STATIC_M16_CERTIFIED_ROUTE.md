# M16 — certified response route (opt-in)

2026-10-09. Owner: Claude (Anthropic), after the M15 handover. Contract delta
adopted by the user ("Option A"). **Outcome: GO on the four formal holdout
fixtures under the frozen criteria. No performance measurement was authorised
or run, so there is no speed claim. Not merged, committed or published.**

## What changed and why

M9 showed that superposed stress outputs differ from the direct stream only by
floating-point rounding paths. M10-M15 tried to prove, case by case, that the
canonical direct solve could be skipped, and M15 showed the available native
relation cannot support that. PARDISO exposes no factors at all. Under the old
bitwise contract the response route could never remove per-case recovery,
which dominates recurring cost.

M16 changes the reference, not the tolerance philosophy. With
`stress_execution="certified_library"`, the response evaluator's stress and
envelope outputs are the outputs of a certified route, qualified by assessment
against canonical staged recovery at the route's own certified state. The
default `stress_execution="canonical"` keeps M8 behaviour exactly, including
library storage accounting. Default APIs and the direct stream are unchanged.

The full contract and the frozen criteria C1-C6 are in the living note,
`agent_plans/PREPARED_STATIC_IMPLEMENTATION_TASK.md`, section "M16 certified
response route". They were written before any M16 measurement.

## Implementation

`prepared_static_response.py`:

- Element output library. For every element recovered in detail or in the
  envelope, owned canonical recipes give Y_0 = rec(u_0) and
  Y_j = rec(u_j) - rec(0). Fields are classified as affine, constant or derived.
  Preparation verifies additivity, homogeneity and rigid-offset superposition at
  two amplitudes, constant stability and that `_derived_measure` reproduces the
  native derived values (normwise 1e-9, as `compile_affine_recovery`). Failures
  refuse the capability explicitly. Memory is checked before allocation.
- A case emits Y_0 + sum c_j Y_j for affine fields, copies constants and
  recomputes von Mises, equivalent and principal measures from the reconstructed
  components.
- Source agreement with an original-time packet is term-scaled:
  max|F_actual - F_c| <= 1e-12 max(|F0| + sum|c_j||F_j|). The actual load stays
  authoritative for the 1e-10 backward-error certificate and for reactions.
- Static cases, failed source agreement and failed certificates use canonical
  solve and recovery. Counters and per-case labels record which route ran.
- Envelope results are labelled `governing_identity_basis =
  certified_response_values`.

`prepared_static_shared.py`: `recover_shared_block` gains an optional
`record_source(eid, column)` hook. With no hook, behaviour is unchanged. The
envelope reducer, tie rule, transactions and reaction code are untouched.

## Formal holdout assessment

Holdouts A1-A4 were defined before measurement. Evidence:
`.prepared-static-evidence/m16-assessment-01.json`, run `m16-claude-04-assessment`.

| Holdout | Cases | Linear entries | Derived entries | Worst linear error / limit | Worst derived error / limit | Envelope entries | Identity differences (all near ties) |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1 supported S3, 3 patterns | 12 | 5,520 | 1,680 | 0.0058 | 0.000083 | 630 | 0 |
| A2 S3 rotated 0.37 rad about (1,2,3) | 6 | 2,760 | 840 | 0.0022 | 0.000094 | none requested | none |
| A3 free-free Q4/beam, whole envelopes | 8 | 6,624 | 672 | 0.0010 | 0.000034 | 1,368 | 18 |
| A4 beam, prescribed offset, constrained load | 4 | 48 | 16 | 0.00016 | 0.000034 | 24 | 0 |

All C1 displacement, C4 reaction (bitwise) and C5 envelope checks passed. All
30 cases reconstructed. For comparison only, the same route outputs versus the
direct-solve stream fail the old uniform 1e-12/1e-12 screen in 1,228 entries
and pass the scaled criteria in every entry.

Development fixtures (M8/M9 cases, disclosed, not blind) also pass, with worst
ratios 0.0066 (linear) and 0.00006 (derived).

## What the criteria can and cannot detect

A negative control injects a relative error into the canonical reference.

| Injected relative error | Linear entries flagged (of 920) | Derived entries flagged (of 280) |
|---|---:|---:|
| 1e-15 to 1e-12 | 0 | 0 |
| 1e-11 | 124 | 0 |
| 1e-10 | 168 | 176 |
| 1e-9 | 228 | 196 |
| 1e-7 | 328 | 196 |

The first control version expected 1e-11 to be detected in derived measures
and failed (`m16-claude-05-controls`, preserved). The element scale is an
internal-magnitude scale (|H| U), which on this fixture exceeds the stress
values. The derived criterion therefore resolves about 1e-10 relative to the
measure itself, not the 1.8e-12 stated in the frozen rationale. Entries that
never flag are exact or near zeros, which a multiplicative error cannot move.
The criteria were not changed.

## ANYfem periodic source

`fem/tests/test_prepared_static_response_m16.py` runs the periodic adapter with
recurring samples (t = 3.0 and 2.0 on a 2 s period). All three samples
reconstruct; the largest source discrepancy ratio is 1.5e-17 against the 1e-12
threshold. Under M8 such recurrences fell back on bitwise mismatch (10 of 12
barge envelope cases).

## Regression and pre-existing failures

- 26 existing response tests, the accuracy and envelope suites and the new M16
  tests pass (61 tests in `m16-claude-02`, one failure, see below).
- Evaluator, shared and contract suites: 48 of 50 pass (`m16-claude-08-regression`).
- Three failures are **pre-existing** and reproduce identically on the frozen
  pre-M16 source in `../m16-baseline` (`m16-claude-03-baseline-envelope`,
  `m16-claude-09-baseline-authority`):
  `test_envelope_one_case_policy_counts_transaction_and_tile_before_factor`,
  `test_driver_constructor_alias_refused_before_private_plan` and
  `test_packet_memory_checked_before_numeric_copy`. Each patches a module global
  and expects its own refusal message. Since the M8 final authority hardening,
  the response guard pins those bindings for every evaluator and refuses first
  with "source response executable authority changed". No M8/M9 run combined
  these suites with the hardened source. Not fixed in this slice.

## Resources

Author correctness checks: **97.696126 / 120 process-wall seconds**, nine runs
`m16-claude-01` to `-09` under `../evidence/checks/`. No benchmark;
M8 ledger unchanged at 540.0326433999871 / 600. No Git operation.

## Open items

1. Performance is unmeasured. Preparation adds about m + 13 canonical
   recoveries per element; per-case recovery becomes one small combination per
   element plus derived measures. A barge screen needs a new benchmark epoch.
2. Library memory scales with outputs x columns; for the barge (61 columns) it
   is a few hundred MB by estimate, not measured.
3. Governors that are ambiguous within route accuracy are not labelled.
4. The derived-criterion rationale overstated its resolution; see above.
5. The three pre-existing authority-test failures need an owner decision.
6. Independent review of M16 is pending.

## Barge screen attempt (epoch m16, 600 s granted)

Incomplete. The library route timed out at 430 s while building the element
library; base preparation had finished at 93 s. The likely cause is one
authority safe point per element (about 33 ms each by earlier measurements,
8,490 calls). Repaired to one per 128 elements; the 16 M16 tests pass on the
repaired source. 430.18 s used, 169.82 s left unspent because no complete run
fits. A rerun needs a new allowance. Details in the living note.

## Barge screen (epoch m16b, owner-delegated allowance)

Completed on the repaired source. Library route versus canonical response
route, same settings: preparation 396.3 s versus 118.6 s; warm history 13.62 s
versus 14.08 s (1.03x); peak RSS 1,536 MB versus 1,316 MB. **Performance NO_GO**
as implemented. Outputs agree closely and no governing identity changed; see
the living note for the comparison table. 601.19/800 s used.
