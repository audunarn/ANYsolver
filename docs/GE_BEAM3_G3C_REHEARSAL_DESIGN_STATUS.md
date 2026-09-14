# G3c rehearsal design accepted

Reviewed freeze c732190d0718c0dd25aa3c71653e132435aa2d6a, tree
20daa00f48caf36032df7f2bded5640c51adcf39. Independent decision:
ACCEPTED_G3C_HISTORY_REHEARSAL_DESIGN_ONLY, empty findings.
Review SHA-256 b527bd2835d4c8f8cd9ebaf5dc596dc67fe0f2317f332f69f02f5ea58b013903.

Separate static inventories: new rehearsal tests 4 passed by author and reviewer;
inherited design tests 4 passed by author; inherited inert preflight tests
8 passed by author. No numerical mechanics executed in this gate.

Frozen next implementation scope: ten complete histories, 70 genuine accepted
stages, 80 stored prefix packets (not 80 replay tests); two positive origin
replays; 142 negative member/origin probes. Negative split: 112 preflight,
26 genuine replay, two virgin-state and two runner-review probes.

Next: implement the bounded history producer, authentic mutation constructors
and exclusive external packet manifests, then independently review before
execution. Worker packet manifests and parent terminal receipts must form a
noncircular hash DAG. Exact expected rejection reasons must be reviewed; an
arbitrary exception or resource failure is not a successful negative test.

The 600-second child and 1800-second wave bounds remain binding. Full CM3 cost
is not yet measured. Do not extend limits, retry automatically, or promote
partial results. Preserve previous smoke/prefix evidence and all raw histories.

The new contract audit reproduces at the reviewed four-path freeze above,
not this evidence-only successor (its exact extent guard intentionally rejects
additional evidence paths). This successor adds only this status and the
canonical independent review. Independent rationale remains preserved at
C:/Github/ANYsolver/.perf2-worktrees/.g3b-independent-review-20260912/
G3C_REHEARSAL_DESIGN_REVIEW.md, SHA-256
4a6c25b891b3965db2eef81b4e7cff9051c6385c40717dd74a94bf192b607145.

Full G3c MO01-MO18, physical recovery/MO16, full histories/restarts/transport,
state-failure and formal cycles remain open. G4, G5 and full legacy parity are
unfinished. No production mechanics, shell qualification, aliases, defaults,
main branches, versions, publication or concurrent ANYmesh work changed.
