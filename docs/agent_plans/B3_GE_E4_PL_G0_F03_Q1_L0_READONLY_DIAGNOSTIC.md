# F03 Q1_L0 saved-case read-only diagnostic

23 September 2026. The clean integration source at
`125a1eb3dad773824b859fbf6912e2ffe5d13d78` read the immutable
attempt-C `Q1_L0` archive with the **unchanged** registered scientific
budgets. `_compute_case` ran without writing a case receipt or changing
attempt C. It returned `PASSED_CASE_NUMERICAL_SCREEN`, no reasons, and all
11 predicates passed: evidence, execution, condition/backward certificate,
positivity, state scaling, rank, trace, equilibrium/energy, integration,
composition, and balance. The installed F03 test selection passed 1,341 tests
with four Windows symlink-privilege skips after the reader fix.

The new diagnostic artifact is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-q1l0-readonly-diagnostic-20260923/diagnostic.json`,
SHA-256 `8bdba2bdd76b26dfc667b33fb007f0b132d6734f12c867e5dc05179cb67ab9db`.
An independent reviewer verified its hash, source commit, case, empty reasons,
and all 11 passed predicates. The reviewer separately rehashed attempt C's
aggregate receipt to
`a37f3a27c0a82558d20844d3222822005278c5b2759f858c6e43a36b40ed0b95`
and confirmed its `FAILED_EVIDENCE` status is unchanged.

This result isolates the lifecycle snapshot and inverse-block reader fixes.
It is a diagnostic from a later source commit, not a registered replay or a
retroactive pass for attempt C. The other four cases, the cross-case screen,
physical line-coupling selection, and G0B remain open.
