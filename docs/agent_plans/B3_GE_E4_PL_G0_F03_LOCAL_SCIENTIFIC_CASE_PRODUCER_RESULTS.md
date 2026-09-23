# F03 local scientific child producer results

**Date:** 23 September 2026

**Status:** `IMPLEMENTED_NOT_QUALIFIED`

**Reviewed source:** `2b4f2e84742973854fcadd7927ff833a8ba05eaf`

## Result

The exclusively-writing single-case producer is implemented and independently
reviewed. It creates no registration, supervision, terminal receipt, case
receipt or scientific adjudication. No registered scientific case was launched
while implementing or reviewing this batch.

The producer now enforces this lifecycle:

1. Read only the bounded plan envelope.
2. Exclusively write `start.json` before topology or model construction.
3. Validate the retained envelope against the exact case inventory and source.
4. Re-read `plan.zip`, fully validate it, and require canonical equality with
   the retained envelope before any resource preflight or model work.
5. Perform the primary and alternate assemblies and scalings with the primary
   scaling reused by the alternate route.
6. Perform one KKT factorization/candidate RHS solve, one positivity
   factorization, and one pass over every planned inverse block.
7. Persist the numerical, port, prolongation, saved-observation, composition
   and balance evidence in the frozen order.
8. Write `evidence_index.json` last.

Failures preserve the exclusive start marker and any partial evidence. The
producer contains no retry or cleanup path.

## Verification

- Producer-focused synthetic lifecycle and ownership tests: **21 passed**.
- Parent broad affected storage/lifecycle/replay suite: **208 passed in
  69.61 seconds**.
- Independent producer-focused suite: **21 passed**.
- Independent bounded dependency sweep: **135 passed in 52.34 seconds**.
- Parent JUnit record:
  `C:/Users/AUDUNA~1/AppData/Local/Temp/f03-case-producer-broad-final-20260923.xml`.

The tests use mocks and bounded synthetic matrices. They do not assemble,
factor or solve any registered scientific case.

## Independent review

The first review found one P1 lifecycle issue: the initial envelope used for
`start.json` was not itself validated, so replacing a stale plan with the
expected plan between reads could consume an attempt under the wrong start
identity. The fix validates the retained envelope and requires canonical
equality with the post-start reread before budgets or model construction. A
synthetic plan-swap test covers the corrected boundary.

Final independent code and mechanics review reported **no remaining
findings**. It confirmed exact write ordering, one-use inverse streaming,
factor and solve counts, inverse-gather semantics, common-state binding,
partial-evidence preservation and the absence of scientific lifecycle roles
outside evidence production.

## Gate decision

This closes the child-producer implementation prerequisite only. G0B remains
open and G1 remains barred. Registration and scientific execution remain
barred until the top-level one-use coordinator, its bounded lifecycle tests,
preflight demonstrations and independent review are complete on clean
committed sources.
