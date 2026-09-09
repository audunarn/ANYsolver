# Physical-fibre modal integration regression completed

Frozen implementation c90859992f240d327960f72fdf816b5fec7d5f29,
tree dbe89d86c67d21ec50fc680e63e96b77e52910cb. Physical-fibre reference and
accepted-translation current-rest modes now run through NativeBeamAnalysis.
Unloaded plastic histories remain exact; active/nonsmooth yield states fail
closed. The original material/geometry operators and modal kernel are unchanged.

Two fresh isolated regression replicas each passed119 tests, with no failures,
errors or skips. Pytest times279.07/279.25 seconds; bounded process times
281.319388/281.922825 seconds; peak266178560/265846784 bytes. Both were
launched concurrently with one numerical thread,600-second/24-GiB bounds and
the existing inactivity watchdog. Session83445 exited0; both complete process
trees are empty. Earlier development inventories remain separate:28pass and59pass.

Six scientific output files are byte-identical between the two replicas:

| Record | Bytes | SHA-256 |
| --- | ---: | --- |
| Free-body reference modes | 234754 | 516376aa684bb17373c6bff89126f8b2c4cbeb9df36c3deeed2c6abf6ea70077 |
| Model-owned accepted checkpoint | 46675 | 5119f4c32a4c34378b2b358fcec28297406e1b6818144898d37636257f4fc08b |
| Model-owned prestressed modes | 235283 | a91311473b4037bb83680a3e473928e82ab73139d05d0c0ff83c5744d53be791 |
| Supported reference modes | 225942 | 7db405baed43068be311a7b53721c34bc15a04dd4ccadd27968e644066e9ee82 |
| Full stationary Schur comparison | 224360 | ed66161a262874ebe746baa8c9f0245fd00e4a2bf96062b248c36158fb918a53 |
| Original unloaded-plastic checkpoint | 44810 | 47bd3a099ea29b98c863dc71064e58fccad876bcaa81b470172658a8936bf921 |

The unloaded history is obtained from an actual curved two-element physical-
fibre load/unload sequence, not a relabelled generalized-section or virgin state.
Full-system comparison, massless trace elimination, complete physical-pencil
eigenvalues, six free-body zero modes, positive elastic modes, common-rotation
covariance and material/model/packet/inertia mutations are covered. These remain
small integration/regression fixtures, not a complete engineering campaign or
independently authored qualification.

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-modal-c908599-20260909`

86 files plus manifest12856 bytes; manifest SHA-256
fa16d9f34a3594ea566f98cc547d786aab25ab8d04e3e4215ee5c2e25c1102b6.
Aggregate SHA-256 d31dc3c5dd242c91783d90f62b126dbf1906a5f02e1e14cfad6239f72404daf3.
Read-only audit checked per-file byte hashes, JUnit counts, replica equality and
all terminal process receipts. The archive includes original checkpoints, raw
test outputs, logs/commands/receipts, frozen source and helper copies. No retry.

## Continue toward full completion

Next close larger-model modal consumption against the preserved N32 packets;
do not rerun the passed N32 continuation/spectrum campaigns. The existing paired
kernel still caps its coordinates at256, and the N32 research Decimal solver is
not yet a general production modal backend (notably repeated-mode clusters).
Remaining work also includes mixed-family and full force/current-state/buckling
interface parity, remaining engineering acceptance, independent-author review,
final explicit current-core straight/curved selection and package qualification,
and objective eccentric/curved finite-rotation beam-shell integration.

The preceding installed wheel remains evidence for20528db, not this successor.
Batch remaining interfaces before the final wheel rebuild. No new public selector,
default, package version, tag, release, push or merge. Main, user files, existing
B2/B3/Q4/S3 and concurrent ANYmesh work remain unchanged. Goal ACTIVE, not complete;
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
