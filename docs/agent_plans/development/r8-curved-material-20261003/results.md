# Curved Q4/native GE material slice — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** Solver parent `0b21ed0e`, scoped candidate changes
captured in `raw.zip`; consumer commit `85ed953`. No aggregate G0, G3 or G4 gate
closes. Formal F03 remains unconsumed. Main, release versions and legacy defaults
are untouched.

## Delivered behavior and decision

The existing persistent point owner now admits the separate explicit
`CURVED_Q4_POINT_MATERIAL_REFERENCE_V1_DEV` reference policy: planar Q4 facets,
algorithmic Q4 pullback, optional isotropic shell J2, native generalized B3
yielding and full-pose points. The tilted material oracle uses fixed reference
facet axes and the same accepted predecessor. Covariance, smooth active-branch
actual-update derivatives/work, unloading, reverse yielding and chart rebasing
pass without changes to element or constitutive equations.

The two-Q4/two-B3 fixture loads to factors .5/1, unloads to .9 and reloads to 1.1.
Both domains yield. Fresh checkpoint restoration reproduces material fields,
native cell resultants and continued checkpoints exactly. Cancellation after
trial yielding and before publication preserves the accepted prefix. A corrupted
rebase material history is rejected atomically. ANYfem standalone and ordinary
native Project persistence preserve the separate schema, section bytes and model
identity; owners constructed after reopening reproduce the actual yielding path.

The original twelve-backtrack fixed reload failed. Adaptive stepping with its
existing six-cutback/twelve-backtrack limit also failed. A cached accepted-state
directional discriminator found no merit-norm defect: smooth active-branch
derivative errors were 5.7e-8/7.8e-7, but departure from the yield boundary first
improved below the twelve-halving resolution. The new policy therefore permits
an **explicit fixed-step** backtrack budget up to sixteen. Defaults stay eight;
legacy and adaptive limits stay twelve. The same endpoint passes with sixteen.
This is a changed work budget, not a pass under the failed budget, improved
globalization or a measured performance gain.

## Artifact checks and resources

Final solver wheel SHA256:
`7050679b062fde5cb3ef1e340953e56a7f9105005039ebc5b39378b0d4b18133`.
All 413 source/wheel/installed modules match. Twelve focused installed checks
passed: new material mechanics/history/guards plus old tilted elastic and bounded
mixed-panel controls. Complete supervised route: 61.474 s, 181846016 sampled peak
process-tree bytes. Initial solver wheel also passed twelve checks; subsequent
explicit displacement/checkpoint rejection required the final artifact above.

Consumer wheel SHA256:
`6435122e6aded71bcaa3b16a535c23efc15889367f85aa4810c77256d07e2b10`.
All 98 source/wheel/installed consumer modules match. Six consumer codec/legacy
checks passed in the initial paired run; its additional integration fixture failed
before solving because the test supplied the wrong standalone filename suffix.
The corrected actual native-project history passed. The final pairing reuses the
unchanged consumer wheel, verifies all 511 installed modules against current
source, and passes actual native-project continuation plus strict admission
rejection: 33.115 s, 186916864 bytes. Prior six checks retain their exact original
solver identity; they are not relabeled as final-artifact executions.

Effective NumPy/native pools and Numba use one numerical thread, JIT is disabled,
imports are from isolated installed sites, and supervised limits are 600 s/1 GiB.
Timing is diagnostic execution cost, not paired performance qualification.

## Review, failures and boundaries

Independent OpenAI foundation review identified the fixed-facet material-frame
contract and checkpoint tangent limitation. The separate ANYfem implementer
reviewed solver changes and identified a missing curved-material rebase-history
guard; both shell and beam guards were extended and the corruption check passes.
Integration-owner review additionally closed unverified displacement entry and
checkpoint routes. Worker consumer changes were inspected, their file scope
verified, and the actual installed behavior independently executed. Available
OpenAI review is development review, not cross-family scientific acceptance.

Force-control snapshots carry accepted Markov history. Detailed generalized beam
last-increment records remain empty; previous return-map tangent and incremental
dissipation are not reconstructed. Displacement control, material arc/spectra,
external/staged loads, material stress-free construction, fibres, S3 and broader
attachments remain outside this new policy. Their mandatory programme obligations
remain open. This small fixture is not the practical elastoplastic workload.

Failed source v1 setup, v3 fixed reload, v4 adaptive reload, v6 message assertion,
diagnosis v1 helper and initial consumer fixture logs are preserved. Diagnosis v2
and v3 and corrected source v5/v7 are also retained. The original v4 temporary
`failed-attempts.json` was no longer available after pytest's temporary-directory
cleanup; its process failure/logs remain, but no complete attempt-inventory claim
is made. Future failure fixtures must use retained base directories. No failed
scientific evidence is converted into acceptance.

`raw.zip` contains captured candidate/fixture/runner source, wheel identities,
fresh wheels, logs, results and whitelisted execution metadata. It excludes
installed-site copies and full environment maps. Archive SHA256:
`c20c2cd3b3205d8dff91520d82fa3b8836ac3be3383c41010b9e4826ce2aa584`.
See `summary.json` for compact costs and identities.

## Next decision

Complete predecessor-aware generalized station recovery/checkpoint semantics,
then verify the next admitted curved material operation. Broader curved fibres,
material imperfections/capacity, attachment qualification and independent external
nonlinear agreement remain separate dependencies. Do not repeat the small roof
refinements or claim the unresolved external model is a reference oracle.
