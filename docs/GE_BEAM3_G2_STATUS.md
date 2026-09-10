# G2 constraint integration implementation handoff

Status: **IMPLEMENTED_DEVELOPMENT_VERIFIED_PENDING_INDEPENDENT_REVIEW**.
No formal G2 acceptance or full general-static parity is claimed.

Fixture/test-contract freeze: `48ceb3cc9178e84e971fc500cc26a200aeb36772`.
Candidate: `3e89a5e30ba86103bad6c236356d700229d2820f`.
Tree: `b945ddcb02ed5d17ada718ec69424027195b7055`.
Branch: `codex/ge-beam3-g2-constraints-v1`, local only.
Parent: accepted G1 closeout `c8408eb509fdd2346f5aec2aa53ed262a3d07e7c`.

## Implemented

- Exact rational nested/multimaster affine-translation expansion, including
  nonzero prescribed translations and explicit control rates.
- Physical partial/full orientation supports with analytic first and second
  SO(3) derivatives, explicit target frames and the unchanged relative-chart bound.
- Eccentric relative-pose/translation-tie constraints and their work-dual forces.
- Full multiplier Newton system, constraint curvature, rank rejection, reactions
  in chart and physical coordinates, and affine prescribed-work rate.
- Actual G1 assembly/native-state reuse, immutable constraint capture, callback
  and commit-preparation authority validation, atomic rejection/accepted-prefix
  preservation, authenticated G2 restart/replay and exclusive publication.

The new owner is private, exact-elastic and limited to one/two native elements.
It has no public selector or implicit route. G1, existing beam/shell mechanics,
qualification evidence, source files, defaults and versions are untouched.
This task added files only; it did not edit existing runtime/test/contract files.
Adding a runtime module changes the deliberately source-bound runtime digest;
old checkpoints still require their original frozen runtime, not resealing.

## Separate verification inventories

Two fresh-directory runs of the frozen candidate each passed **35 G2 tests**:
18.93s and 19.04s. Both emitted byte-identical development packets, 4,232 bytes,
SHA-256 `1ace3a2033ea83227014d44c9f8c93297b2f6a009c771987a2bc5cb9e2f04a9e`.
That packet covers the registered axial-prescription/recovery/restart example;
it is not a complete formal scientific aggregate or G2 qualification certificate.

The separate **49-test G1 regression inventory** passed in 38.68s against the
new source tree. These are regression results, not replacement G1 evidence.
Initial/expanded smoke checks and intermediate rehearsals also passed and remain
archived. Every child had one numerical thread, a 24-GiB process-tree bound and
a 600-second deadline. All ended normally with zero active processes. No failed
request was retried; timings are diagnostics, not performance qualification.

S09 checks independently formed axial equilibrium and exact affine expansion.
S10 exercises 1/2/3 selected axes and genuinely free remaining rotations in the
assembled model. S11 verifies noncommuting target continuation/replay and chart
cutback. S12 checks eccentric force/moment/work and derivatives plus an assembled
rigid tie. S13 compares actual-operator multiplier and independent nullspace
solves and rejects redundancy. S14 tests proper-global transformation, changed
node numbering and reversed connectivity under combined tip force/moment.
All registered derivative steps are checked, without selecting a best step.
Other tests cover mutation during callbacks/actual commit preparation, accepted
prefix preservation, restart corruption and atomic publication faults.

Durable evidence: `C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-g2-development-20260910-3e89a5e`.
The companion result binds six source/fixture/test inputs and byte counts/SHA-256
for 26 archived output files. Original temporary outputs remain preserved.
Only byte-verified workspace transfer duplicates were removed after archiving.
Main's unrelated ANYmesher compatibility plan remains untouched. No push, merge,
release, default activation or publication occurred.

## Next gate

Independently review the frozen G2 implementation, constraint/work semantics,
state safety, restart and S09-S14 coverage. Address any findings in a successor;
then freeze a formal G2 confirmation runner and run two reviewed, bounded,
fresh-directory formal cycles. Do not relabel these development packets.
G3 general/mixed graphs and G4 history-bearing section parity remain subsequent
gates, not capabilities inferred from this implementation.
