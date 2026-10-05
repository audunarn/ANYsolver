# F03 sparse state binding and port-rank proof results

22 September 2026. **30 distinct synthetic tests pass. Independent review
is closed for this bounded batch. G0B remains open and G1 remains barred.**
No physical reference equilibrium or native element evaluation was executed.

Source: `7b017d08c29aaf4845e2fb71967d8b1bfb3859ec`, isolated branch
`codex/b3-ge-e4-pl-integration`. Main, existing product defaults, versions
and previously sealed scientific evidence were not changed by this batch.

## Implemented checks

The state verifier binds physical shell/beam stiffness, root constraints,
loads, scaling, scaled KKT matrix/RHS and saved physical/scaled state. It
reconstructs the fixed binary64 scaling order and compares every nonzero
matrix/RHS entry, including both root-coupling triangles. Explicit and
implicit zeros are equivalent; raw sparse hashes retain their identity.

The positive diagonal scaling is checked against its exact squared relative
interval, avoiding reliance on a rounded square root. The frozen limits are
unchanged: D relative `1e-12`, q/U0 and eta/F0 action errors `1e-11`, and
saved H_z absolute error `1e-11`. Exact rational contractions bound the
last check and can be stricter than a rounded dot-product comparison.
Missing H_z produces a partial result, never complete binding acceptance.
No binding status by itself establishes equilibrium or correct assembly.

The root verifier uses exact Gram matrices of the actual scaled three root
rows and their four-row extension with the free transverse-slope port.
Exact Sylvester tests and bounded eigenvalue enclosures certify the frozen
singular-ratio threshold `1e-10` without a numerical eigensolve. Rank
deficiency, a ratio below threshold, and an inconclusive bounded search are
distinct outcomes. The slope remains free; no fourth equation is imposed.
Only four-by-N port rows and at-most-four-by-four Gram matrices are dense.
Trace extraction and physical port meaning remain separate checks.

The connected tests bind an actual small synthetic candidate solve, repeat
saved admission while factorization is forbidden, and reject a stale scaled
candidate after a physical stiffness block changes. Passing these tests does
not alter the candidate owner's `NOT_QUALIFIED` status.

## Verification and review

| Final test group | Passes | Raw log |
|---|---:|---|
| Physical scaling and saved state | 12 | `f03-sparse-state-binding-action-fix-20260922.log` |
| Root and free-slope rank | 16 | `f03-root-rank-corrected-ea137e5e809c434b83d49320369a11db.log` |
| Connected candidate and saved checks | 2 | `f03-state-rank-connection-aa31e19ee45a490ca31735a833db147c.log` |

Independent reviewer `finite_pad_axis_review` accepted the mathematical
bounds, fixed scaling, ownership/resource checks and connected tests after
one correction: an out-of-tolerance supplied action must report `FAILED`,
not `VERIFIED`, even when the overall result already reports HOLD. The
regression now checks that field. The initial passing test log is preserved.

The initial rank test run had four test-fixture failures: the bounds settled
faster than those fixtures assumed, an intended inconclusive fixture already
passed, and unit entries did not exhaust a one-bit Fraction limit. Replacing
those fixtures with near-dependent rows and nontrivial exact values exercises
the intended conditions. That failed log is preserved. The rank implementation
did not change between the failed and final test runs.

All final commands exited zero with the five thread caps at one, temporary
logs/basetemps and pytest cache disabled. These are source-level synthetic
checks, not installed-artifact, physical or performance qualification.

## Closed evidence and remaining work

The new root `.qualification/b3-ge-e4-pl/f03-state-rank-proof-v1` contains
14 bound files plus inventory: seven source/document/test copies, five raw
logs, manifest and independent-review record. Full byte/hash read-back passed.
Do not overwrite or extend it.

```
inventory 31bafde0e254091e46f538ab525e9d00c425322633b58c93dbe0fd9ec5a49d6c
manifest  df624ce66a80dc8cfa079eb5b036692736eb2da9fe74d95e0fe1cc87ff092230
review    93bd5dc4a1f7bc52568655cb1077dd738c049cddf7080f7b5cd5010879e922d5
```

Next: bind extracted trace operators, check separate shell/beam integration,
stationarity and physical work/reactions, then complete the saved archive
and independent adjudicator. Freeze numerical method, resource limits and
the nested case family for independent review before a new scientific
registration. External factor memory supervision and quadratic inverse-column
evidence costs remain unresolved protocol considerations. Historical physical
HOLD results, other G0 foundations, the B2 option and mandatory external
comparisons remain open. No new release or promotion is implied.
