# Retained refinement capacity: bounded validation complete

Frozen implementation `2d4a8866488fc78904bc7aefa33cc53ba90c9e61`, tree
`2545339f5847689a9379786225fce04a5799fd88`, parent
`da4826c0cd6245ce4007dd4de4484d1f8b933b56`.

The private retained route now admits at most 24 elements, 512 nodal DOFs and
1024 full retained unknowns. Translation-owned factor capture is capped at
512 coordinates. The condensed native driver keeps its sixteen-element limit;
other spectral paths keep their existing bounds. Model identity contents,
element equations, section laws, nonlinear algorithm, tolerances, mass,
recovery, state schema and all public/default routing are unchanged.

Separate test inventories:

- Capacity/old-size equivalence: **30 passed**, twice in fresh directories.
- Existing translation-controller and translation-modal suites: **57 passed**.
- Existing retained-generalized-state suite: **30 passed**.

The fixed N4 programme, executed using native same-Programme prefix replay in
fresh Contexts, reproduced the archived bb40689 checkpoint and physical factor
packet **byte-for-byte**. The new partition reproduced the historical partition
at that size. Complete prior state was independently restored by each Context;
no foreign checkpoint was extended, cast or resealed.

The actual N24 virgin model had 870 retained unknowns and 438 factor coordinates.
Its original-factor planar/lateral partitions passed independent Decimal80/100
zero-shift inertia audits: no negative direction, positive algebraic trace and
positive physical mass in both families. The numerical control is not a
physical support. Upper-size authority mutation and cancellation were tested;
over-limit models/dimensions, boolean dimensions and arbitrarily small nonzero
cross-family factor entries were rejected. Existing rollback/restart and
state-mutation tests passed.

Both capacity cycles produced identical scientific artifact bytes. All four
workers completed with empty process trees and no retry. Peak concurrency was
three, longest child 142.950417s, peak process-tree memory 530608128 bytes.
No 600s child, 1800s wave, 24GiB tree, one-thread, CPU-idle or native120s Context
limit was changed. This is capacity validation, not a speed claim.

## Evidence

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-refinement-capacity-2d4a886-20260909`

- Manifest: 96 entries, 14051 bytes, SHA-256
  `162896892C7790B52C85D7F36F675DF4E997D677B39076AEBCCDE6C9D413605F`.
- Audit: 4680 bytes, SHA-256
  `BB20B10DB03C4D201713604176647094BDF53903156EAC81F04AE342AB274C1F`.
- Capacity artifact-hash record (both cycles): 1208 bytes, SHA-256
  `107C52BD53F4ED4CE42B46180CA53B8F8855F7F27BCF6DE69AB062CEFCEC825D`.

All raw checkpoints, factor packets, test outputs, process receipts, source and
helpers are retained. Every file was hash-validated before publication and
compared byte-for-byte during publication. Independent review remains PENDING;
independent arithmetic is not independent authorship review.

## Scope and next action

The prior N12 `NO_GO_FINEST_CONTROLLED_ONSET_COMPARISON` is unchanged. No loaded
N16/N20/N24 search or repeat of that failed campaign was executed here.

Next prepare a separately frozen small loaded refinement smoke using full
spatial N16/N20/N24 arches and one common prescribed crown drop. Use exact native
same-Programme target-prefix checkpoints, separate bounded processes for each
prefix/capture/audit, and preserve every accepted history. Measure replay and
capture cost before freezing a larger critical-point search. Do not raise time
limits, reuse consumed requests, transfer checkpoints between Programmes, tune
mechanics, or relax the 2% displacement AND load criterion.

The full straight/curved production beam and objective eccentric/curved
beam-shell joint goal remains active. Loaded onset convergence, full spatial
postbuckling, active plastic arc history/state safety, solver/material/load/
mass/recovery/restart parity, environment authority, independent review and
installed explicit production integration remain incomplete. No production
qualification, alias/default change or release is authorized by this gate.
