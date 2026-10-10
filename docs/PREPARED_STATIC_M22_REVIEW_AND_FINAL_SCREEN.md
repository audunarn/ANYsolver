# M22 — independent review of M16-M21, in-flight repairs and speed-ups, final screen

2026-10-09. Owner: Claude (Anthropic). Reviewer: a separate Claude Fable 5.1 agent
at extra-high effort, independent of the authoring session but the same model
family, so the handover's different-family review gate remains unmet. Full review:
`../../evidence/m22-independent-review.md` (reviewer checks 27.787 of 90 s).
Pre-M22 comparator: `../../m22-baseline`. Not merged, committed or published.

## Review outcome

No BLOCKER: no wrong admitted results, no unsafe acceptance under the frozen
criteria, no breach of Option A. The reviewer reproduced all seven recorded holdout
results field by field on the final M21 source and showed the array envelope folds
exactly like the canonical accumulator (40 random blocks with many exact ties).
Four SHOULD-FIX defects, eight clarifications, four optional notes.

## Repairs

| Finding | Repair | Evidence |
|---|---|---|
| F1 crash for an element-free (node-only) envelope in the vectorized route | Vector recovery is always built in that mode (empty groups allowed) | `test_node_only_envelope_runs_in_vectorized_route` |
| F2 a compiled-load sample that failed source agreement was solved with the compiled load | On disagreement the native load is evaluated and decides agreement, certificate, any fallback solve and reactions; counted as `compiled_disagreement_cases`, labelled `native_after_compiled_disagreement` | reviewer's scenario: fallback displacements bitwise equal to a native direct solve |
| F3 bindings and late imports of the new classes were not pinned | Module-level imports; `VectorEnvelope`, `VectorRecovery`, `CompiledPressure`, `ReactionPlan` methods are visited by the response guard | rebinding `prepared_static_vectorized.evaluate_load_vector` is refused |
| F4 vector maps allocated before the memory check | Zero records and schemas first, then `memory_check(estimate)`, then probing | `test_vector_memory_checked_before_allocation` |
| F8 labelling | Pattern cases solved canonically outside envelopes count as `pattern_canonical_solves`; native cases in the vectorized route carry `load_execution` | M22 tests |

## Speed-ups implemented (all output-identical)

| Item | Change | Identity evidence |
|---|---|---|
| S1 | Blocks whose loads never run the native pressure kernel enter an owned scope without the 5,349 pressure-recipe owners; the empty scope still runs the global authority checks at entry and exit | scope choice does not touch arithmetic; counters `compiled_load_scope_blocks` / `native_load_scope_blocks` |
| S2a | `ReactionPlan` + `planned_constraint_force_diagnostics`: prepared index arrays and record templates, ordered `ufunc.at` accumulation, first-touch node order, same norm calls | deep equality including key order, types and float bit patterns against `constraint_force_diagnostics` on a two-constraint weighted-MPC model and the mixed model; A1-A4 C4 bitwise reactions |
| S5 | One `LoadCase` pressure probe per load evaluation (the pressure helpers never write to it, checked by AST) | pressure-verification suite (bitwise full loads) |
| S8 | Envelope fields used as views when one schema group supplies every element in order | M17 envelope-structure test and the M22 assessment |

Not implemented (owner decisions): S2b lean selected-reaction diagnostics (output
content); S3 bracketing stage compile and warm-ups with the native trusted scope
(guard usage); S4 deriving load families from declared sources (capability); S7
digest by array bytes (provenance format). Not done: S6 storage-accounting cache
(small, accounting identity risk), S9 reuse of phase pressures (removes an
independent witness), S10 different batched product (rounding change, small gain).

## Verification

Correctness checks 98.67 of 150 s: M22/M20/M21 tests 14 passed; formal assessment
GO (`m22-assessment-01.json`, worst ratios unchanged from M20/M21, A1-A4 zero
reaction mismatches); solver regression 146 of 149, ANYfem 74 of 76, failures all
pre-existing authority tests.

## Corrections to earlier claims (from the review)

- F5: the M21 statement "suites pass" relied on a run that predated the M21 guard
  fix; the reviewer's checks and M22 runs close it.
- F6: reaction and displacement envelope entries and associated fields are outside
  the frozen criteria (C5 covers stress values and governors only).
- F7: the remaining load-phase cost was mostly the block scope over all pressure
  recipes, not arithmetic (addressed by S1).
- F9: the M16 check ledger omitted m16-claude-10-stride; the correct total is
  105.81 of 120 s.
- F10: the M21 reorder changes the error type for a degenerate Q4 Jacobian during
  envelope capture (native ValueError becomes PreparedStaticCapabilityError);
  numerics unchanged.
- F11: in the vectorized route, direct and fallback cases also get vectorized
  stresses at their canonical-solve state; only the library route recovers them
  canonically.
- F12: "default behaviour unchanged" holds for numerics and accounting; guard
  cadence (M17 routing hoist, M20 per-case skip, M22 scope selection only in the
  vectorized route) and diagnostic keys changed.
- F13-F16 (optional) are recorded in the review; label retention in the array
  envelope and approximate accounting remain.

## Final barge screen (epoch m22, 1,437.00 of 1,800 s)

Matched cold processes, 300 cases each, lean consumed output, block 4, 2048 MiB
policy; primary at even and distinct holdout at odd saved positions (M18 design).

| 300-case history | Primary vectorized | Primary canonical | Holdout vectorized | Holdout canonical |
|---|---:|---:|---:|---:|
| Built model to consumed output | 139.2 s | 588.1 s | 130.1 s | 568.8 s |
| Preparation | 93.4 s | 89.0 s | 86.9 s | 79.4 s |
| Case evaluation | 41.8 s | 495.0 s | 39.2 s | 485.3 s |
| Load evaluation phase | 2.4 s | 84.0 s | 2.2 s | 82.1 s |
| Recovery phase | 29.3 s | 396.7 s | 27.6 s | 389.4 s |
| Peak RSS | 1,195 MB | 1,184 MB | 1,194 MB | 1,183 MB |

**Complete-workload ratio 4.23x primary and 4.37x holdout** (M18 2.21x/2.05x; M20
3.14x primary). Case evaluation about 12x. S1 removed most of the remaining load
phase (25.4 s to 2.4 s per 300 cases); S2a removed only about 2.5 s, far below the
reviewer's estimate, so the remaining recovery time (about 0.1 s per case) is most
likely the per-case metadata copies of the selected diagnostics (unprofiled; S2b is
the owner decision that would address it). Preparation varies by about 10 s between
runs of the same route. Memory is unchanged.

All 600 cases reconstructed with no fallbacks (worst source ratio 5.2e-15). The M22
vectorized outputs are byte-identical to M21's (selected histories and whole-model
envelopes) and the canonical outputs byte-identical to M20's, so every M22 repair
and speed-up is output-neutral on the barge. Differences against the canonical route
are as before: displacement 6.0e-13 / 5.5e-13 of maximum, selected stresses
1.5e-11 / 1.4e-11 of element maximum, envelope values 7.3e-10 / 6.6e-10 of entity
maximum; all 43,518 / 46,001 governing-identity differences are same-phase exact
ties. Evidence: `../../evidence/m22-analysis.json`, `m22-primary-identity.json`,
`m22-holdout-identity.json`; runs m22-primary-canonical 590.788 s,
m22-primary-vectorized 141.976 s, m22-holdout-vectorized 132.739 s,
m22-holdout-canonical 571.500 s.

## Still open

Different-family review; barge-scale evaluation of the frozen criteria; MPC holdout
for the master-equivalent C4' path; reaction/displacement envelopes outside the
frozen criteria; the five pre-existing authority-test failures; owner decisions S2b,
S3, S4, S7; integration (commit/merge) decision.
