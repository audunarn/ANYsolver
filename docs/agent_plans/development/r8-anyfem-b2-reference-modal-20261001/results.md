# B2 footprint reference-modal consumer — experimental delivery

1 October 2026. Consumer source `350c98016b35e861bfb0a43e2c24fe1c0ee48039`
on the isolated ANYfem consumer branch; solver source `41b25c03` unchanged.
`ExperimentalB2ReferenceModalPanel` stores explicit physical mass, selected-node
footprints and typed supported virgin modal controls in a distinct strict
experimental schema. Construction/save/reopen owns detached inputs and never
assembles or factors an analysis. Standalone and existing Project dispatch use
the same public owner, preserve its result/status and close on every exit.

The schema excludes static cases, recovery selections, prestress, free-free,
MPC and nonzero-offset controls. Project finite/batch controls reject before
owner creation. Historical point, mass-enabled point and static-footprint
schemas retain their existing meaning; no new API/framework or mechanics is
introduced. Normal spin remains locked and mechanical qualification incomplete.
Saved inputs are not an accepted-state checkpoint.

## Actual artifacts and checks

Consumer wheel SHA256
`11728ab84a2c2b290d37651c455d9f6b7d63110e4804cb9263686c37511fa56e`
is paired with the unchanged solver wheel
`27660d7357eedf36a2d96a73282b9ede974fd3219903b2492d32553c118f47ec`.
All 98 consumer and 391 solver modules match source/wheel/site byte-for-byte.
Actual imports resolve to isolated sites: 275 modules during tests and 274
during each example. Python 3.14; numerical pools/Numba one thread, JIT disabled,
plugin autoload disabled. Dependencies and exact commands are retained.

| Run | Result | Supervised time / sampled process-tree RSS |
|---|---|---|
| Final focused source | 134 passed, including 41 new checks | 17.05s / 178,720,768B |
| Installed new B2 modal, B2 static footprint/point and GE modal consumers | 134 passed, zero failures/errors/skips | 8.230s / 191,897,600B; pytest 5.61s |
| Installed standalone save/reopen example | Completed | 1.958s / 152,576,000B |
| Installed Project save/reopen example | Completed | 1.931s / 152,621,056B |

Installed jobs run serially outside source checkouts under the owned-process
180s/1GiB supervisor. The two example outputs agree: frequencies
0.2871898701/0.5427959695 Hz, 24 constraint rows, residuals below 6.8e-16,
one modal factor and 21 inverse actions. The examples use explicitly illustrative
section/mass data; their frequencies are not engineering reference values.
One modal factor does not include the fresh owner's static constructor factor.
Likewise pre-cancelled zero modal factors do not mean no constructor work.

Initial source collection failure (reserved pytest parameter name) and two
status-expectation failures (modal owner correctly returned `ok`) remain
preserved. Failed source versions were not copied completely; their recorded
hashes/logs are historical evidence, not reconstructed source snapshots.
The final installed fixture/source bytes are retained. Previous broad campaigns
were not repeated; unchanged solver evidence is reused by exact artifact identity.

[Independent Read review](review.md) found no blocking correctness finding.
A queued local source review timed out after two successful reads and supplied
no opinion; it is not an independent pass. Separate OpenAI review and root
source/artifact inspection completed the slice. An earlier small queued local
lookup succeeded, but its proposed causal partition was not justified by the
referenced evidence and was not adopted. Queue/routing/tool/failure logs are
retained; no unmeasured tiering or development savings are claimed.

One optional parser boundary remains fail-closed: duplicate CSR entries can
pass persistence's temporary canonical selector but fail solver coordinate
admission. No invalid model is numerically accepted. This is not a physics or
ownership blocker and old encodings are not silently rewritten.

## Decision and next scientific work

Retain the experimental input/Project workflow. Consumer, installed-platform,
spectral physics, external/scale and aggregate G6/F07/F12/G4B obligations remain
open. No publication, main merge, default/version change or authority renewal.

A separate [CalculiX control-node feasibility check](reference-wrench-feasibility.md)
establishes a usable route to complete support moments and work coordinates.
It does not compare native/continuum stiffness, select BL5/P0, accept E02/F03 or
remove output-precision requirements. Next: define a physically matched rigid-
footprint panel/beam reference using explicit origins and connection extent;
account for precision before applying scientific balance/accuracy criteria.

[Raw archive identity](raw-v1-identity.json) binds final consumer wheel, solver
reuse identity, fixtures, runners, imports/settings, XML/logs, source failures,
local-worker partial evidence and both external control runs. No communication
with the other task. All owned numerical jobs are terminal.
