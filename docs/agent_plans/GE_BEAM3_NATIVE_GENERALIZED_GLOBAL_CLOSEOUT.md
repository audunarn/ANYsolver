# Native generalized global force, restart and recovery closeout

Implementation: `f200b90a037867efb5593f832537da6600d3bdf2`.
Tree: `c603202b76078cfc0dde86dcbbab47421f6dfe51`.
Base: `6cab6d24cdd22a028c628e951447b0229daef3dc`.

The private development gate passes. The six-resultant ellipsoidal section
now participates in the actual native global force-controlled Newton solver,
externally authenticated complete-chain restart and accepted-state recovery.
This is not full beam qualification, independent review, public integration,
modal/buckling authority, finite-rotation dynamics or a default change.

## Separate test inventories

| Lane | Passed | Collection errors | Deselected | Supervisor seconds |
| --- | ---: | ---: | ---: | ---: |
| initial-smoke | 0 | 1 | 0 | 3.815 |
| smoke | 1 | 0 | 95 | 9.027 |
| smoke-curved-plastic | 1 | 0 | 95 | 58.135 |
| smoke-connected-plastic | 1 | 0 | 95 | 121.878 |
| rehearsal-straight-elastic | 32 | 0 | 64 | 22.658 |
| rehearsal-curved-plastic | 32 | 0 | 64 | unavailable |
| rehearsal-connected-plastic | 32 | 0 | 64 | 278.467 |
| q4-regression | 12 | 0 | 0 | 7.625 |
| legacy-regression | 5 | 0 | 0 | 4.619 |
| prior-distributed-straight-elastic | 25 | 0 | 50 | 20.050 |
| prior-distributed-curved-plastic | 25 | 0 | 50 | 26.066 |
| prior-distributed-connected-plastic | 25 | 0 | 50 | 164.191 |
| cycle-a-straight-elastic | 32 | 0 | 64 | 22.659 |
| cycle-b-straight-elastic | 32 | 0 | 64 | 22.855 |
| cycle-a-curved-plastic | 32 | 0 | 64 | 137.720 |
| cycle-a-connected-plastic | 32 | 0 | 64 | 283.866 |
| cycle-b-curved-plastic | 32 | 0 | 64 | 146.951 |
| cycle-b-connected-plastic | 32 | 0 | 64 | 271.830 |

Each geometry has 32 tests and 44 canonical scientific files per frozen cycle.
Both cycles and the corrected rehearsal are byte-identical, including accepted
states, complete checkpoints, continuation, unloading, recovery, deterministic
load-programme events and rejection diagnostics. The three separate historical
physical-fibre restart lanes contain 25 tests and 37 scientific files each;
their bytes exactly match the preserved ecfb8cf development archive.
The Q4 current-state ownership lane has 12 tests; legacy B3 nonlinear has five.
These are targeted regressions, not full old-element requalification.

The initial smoke remains a failed collection attempt. No mechanics ran.
Its six source snapshots and raw stdout/XML are preserved; only the obsolete
test imports were corrected before freeze. The four source implementation
files are byte-identical to their initial snapshots. No fixture, constitutive
law, coefficient or tolerance was changed.

The curved-plastic rehearsal's stdout, XML and all 44 scientific outputs are
intact and passing, but its supervisor summary was consumed before restart
and could not be recovered. Its exit, supervisor wall, CPU and peak-memory
metadata are explicitly null. No rerun or fabricated replacement metadata was
used. Both later frozen curved replicas have complete resource metadata.
This administrative gap is not silently treated as a full resource certificate.

## Implementation and scope

The force programme binds exact element/section types, model identities,
supports, distributed load patterns and any authenticated initial chain.
Raw initial states and unsupported direct solver entry are rejected before
stiffness evaluation. Spatial distributed couples require GENERAL
factorization; no artificial symmetric tangent is introduced.

The new restart schema validates canonical bytes, external SHA-256, complete
stress-free genesis, accepted loads, epochs and predecessor hashes, internal
seeds, six-component paired plastic history, shared nodal rotations and free
equilibrium. Restart continuation reproduces the uninterrupted accepted state
byte-for-byte; unloading retains history and a failed Newton attempt leaves
the preceding accepted state unchanged. A self hash alone is not provenance
for an entirely replaced otherwise-valid history.

Accepted recovery preserves the committed origin and internal solution.
It returns local/global generalized resultants, strains, frames, positions
and formulation/load/state provenance without advancing plastic history.
It explicitly supplies no fibre stresses: this is the resultant-ellipsoid
section law, not a physical-fibre or automatic 3D J2 material conversion.

Maximum tested free-equilibrium residual: 3.081041113358354e-15.
Maximum recovery work discrepancy: 4.5102810375396984e-17.
Maximum recovered-position discrepancy: 2.2215299868541707e-16.
Plastic stations: zero in straight-elastic, eight in curved-plastic and
sixteen in connected-plastic. These are numerical development fixture checks,
not all-geometry or continuum qualification.

Only two existing top-level solver definitions changed:
`_owned_initial_element_states` and
`_solve_static_nonlinear_under_lease`, through private type-gated dispatch.
All other existing paths are unchanged from the base, including physical-fibre
mechanics, B2/B3, qualified Q4/S3, public aliases, defaults and old evidence.
The implementation freeze contains exactly seven paths.

## Process and preservation

Each child command uses one numerical-library thread, a 24-GiB Windows Job
process-tree memory limit, a 600-second wall limit and a 120-second CPU
inactivity limit. At most three children run concurrently. The second replica
for each geometry starts after that geometry's first replica passes; pairs
may overlap across geometries. No automatic retry or uncertain-run restart.
Longest recorded child: 283.86580700000195 seconds.
Largest recorded process-tree peak: 309518336 bytes.
All observed jobs reached terminal states with no remaining Python processes.

The configured guard checks a frozen clean commit, Python executable SHA-256
and package versions. It is not a full dependency-file graph attestation.
Git global-ignore permission warnings remain preserved. The freeze commit
succeeded; a following unquoted PowerShell tree-query command failed, and
a separate read-only quoted query verified the commit/tree without repeating
the commit or any scientific run.

External archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-native-generalized-global-f200b90-20260908`.

648 data files plus the manifest preserve all 18 inventories, commands,
available tool/supervisor records, source snapshots, the collection failure,
intermediate checkpoint, administrative audit and raw scientific bytes.
All per-file byte counts and SHA-256 hashes were verified in staging and
the new archive. The older initial-source manifest's noncanonical key order
is preserved as historical administrative data; scientific outputs and the
new evidence remain strict canonical JSON.

Manifest: 112,668 bytes, SHA-256
`48A6A5D54BF058B60A4898BF2D19548D7D6E21DEE06DFF65A9F12A7B4C5A125E`.

Original temporary runs and all historical archives remain intact.
Only the completely verified transfer duplicate may be removed.

Main remains at `09351645ba17a0a5b130a1c7a48007d36dd08ada`.
The user's untracked ANYMESHER_05_COMPATIBILITY_CANDIDATE_PLAN.md remains
untouched (SHA-256
`645C92F567B542867B6C4F103AC0F4E58B6F06E9F96BA2950C7187D27A0EBBCF`).
No push, merge, tag, publication or other repository edit occurs here.

## Next gate and remaining goal

Next: extend this exact typed generalized-section path to combined nodal and
distributed spatial couples, with independent load-work/chart checks and
complete-chain continuation/recovery. Do not accept generalized histories
through the old fibre codecs or claim a conservative couple potential.

Broader solver/path/material parity, practical model scale, consistent
physical mass, modal/prestress/buckling, slenderness and curved engineering,
independent review, package/public integration and objective beam-shell
connections remain. Independent review is PENDING and the full goal remains
active. No production or default authority is granted by this closeout.
