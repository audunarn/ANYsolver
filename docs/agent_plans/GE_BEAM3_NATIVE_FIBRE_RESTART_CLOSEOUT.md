# Native physical-fibre restart and recovery development closeout

Frozen implementation `bb75ce36f999d2db1b1433c552dd6a5a4d53d7bd`, tree
`0fc7bc5fa879f1e3c131eb4957a06a9d5df4fb85`, passes this private development
gate. The five-path implementation adds a typed supported-model checkpoint,
accepted physical recovery, tests/plan, and two exact-private-candidate input
branches in the existing static driver. It preserves the frozen native adapter,
static Schur boundary, physical operators, existing B2/B3/Q4/S3 mechanics,
historical evidence, public selectors, defaults and packages.

## Separate test inventories and preserved failures

- Initial smoke: one setup error, 17 deselected; 25.467 seconds supervised.
- Corrected smoke: one failure, 17 deselected; 26.066 seconds.
- First full rehearsal: 17 passed, two failed; 30.279 seconds.
- Integration rehearsal: 20 passed, two failed; 49.118 seconds.
- Exact-coordinate rehearsal: 23 passed; 41.906 seconds.
- Existing Q4 current-state input-ownership regression: 12 passed; 21.661 seconds.
- Frozen cycle A: 23 passed; 37.093 seconds.
- Frozen cycle B: 23 passed; 39.096 seconds.

A separate one-case snapshot diagnostic took 16.646 seconds. It is not a test
inventory or a qualification cycle. The initial 1e-10 driver tolerance accepted
the curved half-load snapshot at residual 6.420418655440868e-11, correctly
rejected by the 1e-11 restart gate. New development solves use 1e-12; no old
test or acceptance threshold was relaxed. The next smoke caught NumPy scalar
terms at the frozen compensated-sum helper; only the new wrapper's boundary
conversion was corrected.

The first full rehearsal exposed rejection of typed CellHistory by the generic
solver input copier. A narrow branch now captures only the exact private native
element: guarded canonical observation, owned typed reconstruction and complete
local response replay. All other elements retain the unchanged generic copier.

The integration rehearsal completed both continuations but failed bit identity.
A read-only audit traced this to LSQR free-coordinate projection offsets:
5.421010862427522e-20 straight and 3.469446951953614e-18 curved. For the exact
private candidate and its admitted homogeneous selection-only support map,
restart now extracts free coordinates directly and verifies exact reconstruction.
Existing formulation paths retain their prior coordinate reconstruction.

## Demonstrated scope

All 24 scientific JSON packets are byte-identical between the frozen cycles.
Both cycles passed exact clean-commit/configured-runtime guards before and
after execution. These guards are not a complete dependency-graph qualification.
Every child terminated within its one-thread, 24-GiB, 600-second wall and
120-second CPU-inactivity bounds, with zero active children on exit. No automatic
retry occurred; the failed attempts remain separately preserved.

Straight elastic and curved plastic two-increment cases survive strict JSON
encoding/decoding into fresh models, then resume in the actual nonlinear solver
with byte-identical full final displacement/state packets. Both final material
epochs are two; the plastic result has 32 accumulated-plastic history rows.
The checkpoint binds the complete supported model, nodal force pattern, genesis
and accepted chain, including predecessor/origin/internal-seed links, native
multiplicative rotation updates, shared-node rotations and supported equilibrium.
Resealed mutations, invalid schema/JSON/number types, hashes, supports and
coordinate maps are rejected. Connected two-element genesis is tested; loaded
multi-element actual-driver restart remains a next gate.

Recovery uses accepted internal coordinates and the fixed material origins,
returning physical paired fields, section-supplied fibre stresses, frames,
positions and global resultants without advancing history. Work conjugacy passes
1e-11. A separate read-only Q2 nodal-polynomial reconstruction of the frozen
outputs agrees with recovered positions within 2.220446049250313e-16. This is
an additional check, not an independent formulation review.

## Preservation, restrictions and next step

The manifest/status bind 158 data files plus the manifest copy at
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-native-restart-bb75ce3-20260907`.
All byte counts and SHA-256 hashes are verified, including five frozen source
copies, raw successful/failed attempts and regression logs. Original temporary
outputs remain. Only the exact verified transfer duplicate may be removed.

The private codec admits at most 16 elements, 512 nodal DOFs, 65 snapshots and
2 MiB, with a 60-second chain-validation budget. Supports must be homogeneous,
with no partial rotational supports, MPC, point mass, activity or disconnected
nodes. Loading is an explicit fixed nodal-force pattern. Caller-verified external
SHA-256 provenance is mandatory; self-hashes do not authenticate the creator of
an entirely replaced valid chain. Single-state solver capture is not equivalent
to complete chain/provenance validation.

Next prove connected loaded actual-driver restart and distributed-load work
routing, then complete general section and solver-workflow parity. Independent
review remains PENDING. Full restart qualification, mass/dynamics, modal and
prestressed/buckling workflows, production selector adoption, packaging and the
objective beam-shell connection remain unfinished. Static internal-coordinate
elimination grants no dynamic reduction authority. No push, merge, release,
activation, default change or overall goal completion is claimed.
