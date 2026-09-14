# G2 constrained exact-elastic static confirmation accepted

Terminal: **PROVISIONAL_GO_GE_BEAM3_G2_CONSTRAINED_ELASTIC_STATIC_ONLY**.
Independent implementation/runner review and final evidence review both accepted
with empty findings. Scope: S09-S14, private one/two-element exact-elastic owner.
This is not full general-static parity, G3, public integration or release.

## Frozen correction and preservation

- Original blocked review: `435f848d79ef5180e1fd7b8778bc7f2f935219e0`.
- Correction protocol: `f75046d`.
- Runtime/test implementation: `c73bf70e7b5176ad6f0071456875d1a62c7210fe`.
- Accepted execution candidate: `e309d977de56ab2dd408cefb796e84173911aa21`.
- Candidate tree: `b2eb030f6e693ad436fbefc4918087d24922f058`.
- Independent implementation review preserved before formal execution: `c4d3958`.

G2-IR-01 is closed by rejecting explicit G1 solve dispatch on G2 owners before
any evaluation or state mutation. Virgin and accepted-prefix regressions cover
both unbound and super-bound calls, preserved generations/journal/checkpoint,
no pending trial, authenticated replay and continued constrained solve.
Exact G1 owners retain their existing solve behavior.

G2-IR-02 through 04 are closed by explicit normalized invariant checks, loaded
noncommuting prescribed-target work, chart/spatial moments, accepted physical
rotation covariance, and full g/J/H/work-dual constraint transport. Supplemental
tests reverse actual element connectivity and compare the assembled constrained
operator. The existing G2 Newton expressions were extracted unchanged into the
private `_system` seam; nonzero multiplier curvature is checked against the full
residual derivative and independent nullspace elimination, including nonzero g.

The first rehearsal passed its 54 tests, then exposed a runner-only trailing-LF
validation defect. That failed rehearsal and incident are preserved. The
successor corrected the runner and its synthetic fixtures, not native
serialization or mechanics. A new complete rehearsal passed before formal runs.
No failed formal request was retried; exactly two formal cycles were executed.

## Separate verification inventories

| Inventory | Result |
|---|---|
| Runner/infrastructure | 36 passed; 2.43 seconds |
| G1 development regression | 49 passed; 45.28 seconds |
| Corrected G2 rehearsal | 54 passed; 27.10 seconds |
| Formal G2 cycle 1 | 54 passed; 27.61 seconds |
| Formal G2 cycle 2 | 54 passed; 31.38 seconds |

Formal cycles each contain exactly 162 passed setup/call/teardown records.
All 18 supplemental scientific records, test reports, checkpoint inventories
and the 4,232-byte development packet are byte-identical across cycles.
Each formal child had one numerical thread, 24 GiB/tree, a 600-second deadline
and a 120-second inactivity bound. Peak tree memory was 207187968 and 205500416
bytes; both exited 0 with zero active processes. Timings are diagnostics only.

The separate canonical aggregate is 8,367 bytes, SHA-256
`2122104eb2ece955ca8ccbe3d4654578cd3a53e340754bd7fa01c0c3be37f8ff`.
Its Git copy is byte-identical to the exclusively published original.
The development packet remains labeled `qualification=false`; it was not
relabeled as a certificate. The final reviewer independently checked 339 bound
files, Python identity, 317 distribution versions and the complete formal DAG.

## Durable evidence and clean handoff

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-g2-confirmation-20260910-e309d97`.
Its canonical 137,746-byte manifest binds 609 files with byte counts and SHA-256;
manifest SHA-256:
`234f6e0b93ab7ceb8ce5d067c5160032cd3d2ffa34aad344762403281150b8ef`.
All 54 formal files, including pytest scratch, match the original temporary
evidence. Initial cross-token Temp ACL failures during copying were resolved
through byte-verified workspace staging; no evidence was regenerated or
overwritten. The 610 workspace transfer copies (including the manifest) were
removed only after verifying the durable copies. Original temporary outputs,
all old evidence, the failed rehearsal and original blocked review remain.

The execution worktree remains clean at the accepted candidate. Closeout lives
on `codex/ge-beam3-g2-confirmation-v1`; no main update, push, merge or release.
The unrelated ANYmesher compatibility plan remains untouched. Existing element
mechanics, qualification evidence, public selectors, defaults and versions are
unchanged; only private G1/G2 orchestration and G2 verification were corrected.

## Recommended next gate

Freeze G3's concrete graph/junction fixtures: native branches and cycles,
deterministic sparse assembly, multiple-RHS isolation, mixed translation ties,
and explicit rejection of unqualified shared-rotation adapters. Qualify any
new common-pose adapter separately before admitting mixed rotational junctions.
Do not infer G3 or history-bearing G4 parity from this accepted G2 gate.
