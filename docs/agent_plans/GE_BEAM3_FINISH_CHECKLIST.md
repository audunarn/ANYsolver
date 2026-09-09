# GE-B3 finish checklist

Current navigation checkpoint, 2026-09-09. This is not scientific evidence,
a new formulation, an authorization record, or a replacement for any accepted
or failed result. Use this single checklist for completion updates rather than
creating another exploratory programme for every interface change.

The user has asked to finish after more than four days. Preserve the existing
work and close required application gaps; do not restart passed campaigns.

## Preserved baseline

- The original straight standalone P3 gate and its explicit `ge-beam3` selector
  remain separate from the newer native straight/curved candidate. See
  `GE_BEAM3_MODEL_HANDOFF_CHECKPOINT_20260905.md` for the accepted P3 scope.
- Native force-current integration is preserved at `3bb5249`, with the exact
  implementation at `d38f653`. Its 91-test replicas and 43 byte-identical
  scientific records must not be rerun simply to produce another closeout.
- The N32 spectra, complete inertia, model-owned replay and larger-modal
  consumption are completed subsets. Their unstable equilibria must not be
  described as stable postbuckling. The completed Euler point-wave is a
  straight cantilever reference subset, not a general buckling API certificate.
- Existing B2/B3/Q4/S3 mechanics, defaults, main and historical evidence stay
  unchanged. The current native candidate remains `production_qualified=False`.

## Required completion, in order

1. **Standalone workflow audit.** Generalized nodal-force and combined-couple
   ownership are now integrated and verified below. The captured-state buckling
   route is also implemented and verified for its declared scope; do not rebuild
   these routes. Finish the continuation/public routing audit for supported
   straight/curved section families. Audit evidence against the
   requested engineering requirements; run only genuinely missing checks or
   regressions affected by a correction. Do not infer full parity from modal
   subsets, manufacture accepted histories, or relabel unstable states.
2. **Standalone delivery.** Bind the current core to an explicit public entry
   point only after its gates pass. Obtain independent-author review of the
   actual frozen delivery candidate, build its wheel once and check installed
   behavior outside source trees. The older accepted wheel is not this build.
3. **Objective beam-shell connection.** Complete and qualify the required
   finite-rotation connection, including eccentric and curved attachments.
   This remains required for the overall goal, but must not hold up a genuinely
   qualified standalone delivery. Keep shell mechanics unchanged.
4. **Final handoff.** Verify the complete requirement/evidence mapping,
   supported-use documentation, clean checkpoint and remaining restrictions.
   Do not declare the overall goal complete while any required gate is open.

A separate heterogeneous generalized/fibre standalone-driver project is not
an additional prerequisite invented by this checklist. Different materials
within each admitted family already have model ownership. Any cross-family
integration actually needed by the required connection belongs to that gate;
do not remove existing rejection guards without an authenticated owner.

## Completed safety integration in this checkpoint

The model-owned nodal and distributed force routes now expose the existing
cancellation token and progress callback. Cancellation is checked before
initialization/restart capture, propagated into Newton, and checked before
returning a checkpoint. It is cooperative: a native factorization is not
claimed to be instantaneously interruptible. Existing process-tree watchdogs
remain in force for test execution.

Separate passing inventories:

- Focused safety tests: **12 passed**, 142.78 seconds.
- Existing affected model-owned regression suite: **33 passed**, 152.15 seconds.

Both workers exited successfully with empty child trees under the existing
600-second/24-GiB bounds. Focused tests verify cancellation before decoding,
discard of actual unaccepted material/rotation trials, cancellation at the
final progress callback without issuing a checkpoint, lock/programme cleanup,
unchanged supplied restart authority, and byte-identical scientific checkpoint
output with and without observation. No retry or broad qualification rerun.

The 23 external files, exact tested source, commands, logs, JUnit reports,
receipts and emitted checkpoint records are bound by
`docs/reference_cases/ge_beam3_owned_force_cancellation_manifest.json`.
This is integration regression evidence, not independent review or completion
of the remaining scientific gates. Full goal remains active and incomplete.

## Buckling interface verified

`NativeBeamAnalysis.buckling_modes` captures the actual generalized or physical
fibre force checkpoint, without state advancement or state-owner conversion.
It solves the original-factor material versus negative effective-geometric
pencil, including conservative external-load work. All free nodal and cell
rotation coordinates remain in the multiplier problem; a current-load static
lift must not be reused for all multipliers. Physical mass does not determine
the returned multipliers.

The supported material factor must admit a verified positive-energy whitening.
Symmetry, whitening, material orthogonality and original-factor residuals use
the existing 1e-11 tolerance. Active/nonsmooth yield, nonconservative couples,
invalid ownership, singular material support and failed numerical witnesses
are rejected. The multiplier window is explicit. These are frozen-current
linearized predictions, not nonlinear critical loads or stable postbuckling
certificates. Existing static/modal mechanics and shell buckling are unchanged.

Two early smoke failures are preserved: exact-bit symmetry admission was too
strict for the already accepted roundoff-scale Hessian defect; the next
failure was a test using the fibre Hessian field name on a generalized state.
The corrected 17-test smoke and the stricter 19-test integration rehearsal
passed. The final source additionally includes direct regression for the
incorrect fixed-static-lift shortcut and explicit input-roundoff witnesses.

Frozen implementation `47cbcd51f04e7f287c78c712a6bba971d40e5373` passed 21 tests
in each of two fresh replicas (43.89/43.33 seconds). All ten scientific output
files are byte-identical. The new explicit fixed-lift regression demonstrates
that holding the current static lift fixed would produce the wrong critical
multiplier. Both original-factor and original stress-resultant saddle-pencil
comparisons pass; straight/curved, connected, coupled, covariance, mass
independence, state preservation, mutation and unsupported-state checks pass.

The initial saved-Euler checks stopped at an installed-versus-source import
binding error. No numerical result was produced by either failed checker.
Runner-only correction `ad1593e0b19ff9ec0d4b179fdc06836d740d64b0` has no `src/`
or test delta from the tested implementation. It binds and verifies the frozen
source package after checking the saved archive. The passing tests were not
rerun for that runner-only correction.

Two corrected N8 saved-factor checks completed in 2.32/2.42 seconds and emitted
byte-identical scientific records. Neither reran a preload solve. Two
compressive preloads give both bending predictions within 0.074% of their
Euler references (required: below 2%); the tensile point has no positive
multiplier in the explicitly tested window (0,4]. All original-factor mode
residuals are below 3e-12. This is numerical/interface verification, not
reclassification of the historical Euler campaign or full beam qualification.

The 98-file archive, all failures, passing records, commands, source and hashes
are bound in `docs/reference_cases/ge_beam3_native_buckling_verification.json`.
All launched process trees are terminal and empty. Preserve this completed
work; do not rerun the Euler, N32 or buckling waves as a substitute for the
remaining delivery gates. No independent-author review or default activation
is claimed. Overall goal remains active.

## Combined spatial-couple API verified

The model-owned API now exposes `solve_spatial_couples`,
`recover_spatial_couples` and `spatial_couple_checkpoint_prefix`. These call the
existing native generalized distributed-force/distributed-couple/nodal-couple
solver and its complete authenticated history protocol. Section operators,
work maps, tolerances and rotation/material laws are unchanged. On continuation
the supplied patterns are load increments from the accepted point, matching
the underlying protocol; they are not absolute target loads.

A distinct workflow envelope binds the definition graph and combined backend.
Existing V1 envelopes retain their schema and serialization. A combined history
cannot be silently resumed, recovered or spectrally evaluated through a V1
conservative-force route. Nonconservative spatial work remains nonconservative.
The actual native chain owns every accepted predecessor, effective load,
rotation update and material origin. Controls include existing adaptive
cutback/line search, progress and cooperative cancellation.

The complete 24-test development inventory passed in 490.08 seconds. It covers
straight elastic, curved plastic and connected plastic models; byte equality
with direct native solves and checkpoint encoders; physical recovery/work;
prefix continuation and unloading; failed-step preservation; strict envelope
and control rejection; cancellation; and a prescribed rejected factorization
whose cutback returns exactly to the fixed-step accepted history.

Frozen implementation `e59154c9673d7362befb40ff6f922b673cff9e67` passed this
same inventory in three case shards of three tests each and one common-controls
shard of fifteen tests, twice in fresh processes. All 19 scientific files match
between replicas. The separate existing V1 inventory passed 33 tests; its seven
scientific files match the preserved pre-change regression byte-for-byte.
All nine workers exited successfully with empty child trees. The longest worker
took 339.83 seconds; the complete wave took approximately nine minutes, using
at most three workers and the existing 600-second/24-GiB child bounds.
No automatic retry, coverage reduction, or mechanical rerun of the completed
Euler/N32/buckling campaigns occurred. The 121-file archive, tested source,
smoke, receipts and logs are bound by
`docs/reference_cases/ge_beam3_owned_combined_verification.json`.

Generalized nodal dead forces use the distinct retained programme below, not
the physical-fibre `solve_nodal` owner. Independent review, final installed
delivery and the objective beam-shell connection remain required.

## Generalized nodal programme integration

The explicit `solve_nodal_program` route now owns the existing retained nodal
dead-force programme, with matching import, prefix, recovery and current-mode
methods. Its absolute target schedule is frozen in a distinct checkpoint
schema; continuation may resume only that same schedule. No accepted-state
conversion, force-law change, section change or rotation-law change is made.
Cancellation/failure returns only the native owner's last accepted capsule.
Cross-owner records, tampered hashes, changed programmes and model mutation
fail closed. Existing fibre nodal and generalized distributed interfaces stay
unchanged; neither is silently overloaded with another state's semantics.

Development smoke inventories passed separately: 24 integration/control tests
in 18.53 seconds; two additional curved/connected plastic loading, unloading,
reversal, recovery and prefix-continuation tests in 27.70 seconds. The complete
26-test integration inventory passed both frozen fresh-process replicas at
`1afdd570109d2996ea04aa1c844c99a5529b9c5f` (53.17/52.67 seconds). The separate
retained nodal-owner regression passed 22 tests in 24.54 seconds. All fifteen
scientific files match byte-for-byte by relative path between replicas. All
three child trees terminated empty within the existing bounds; the complete
wave took approximately 55 seconds. The 95-file archive includes both development
smokes, final wave, tested source, commands, logs and process receipts, with each
copied file verified against its original. Its binding is
`docs/reference_cases/ge_beam3_owned_nodal_program_verification.json`.
No retry, mechanics correction or completed campaign rerun occurred.

## Delivery audit: do not confuse completed subsets with overall qualification

The next work is a single current-candidate requirement/evidence audit and
delivery review, not a new exploratory mechanics programme. Reuse these already
completed subsets and preserve their exact scope:

| Required capability | Current evidence and remaining boundary |
| --- | --- |
| Straight/curved force, coupled generalized and physical-fibre ownership | Model-owned native analysis and translation inventories; cancellation, combined-couple and nodal-program closeouts above. All current entry points remain private candidates. |
| Accepted material/rotation history, recovery and restart | Actual force and translation owners, load/unload/reversal, failed-step and cancellation replay; no owner conversion or fabricated history. |
| Current-rest modes and buckling | Force-modal 91-test replicas; native buckling 21-test replicas; saved Euler comparison. Active/nonsmooth material states and nonconservative work remain excluded from conservative spectral claims. |
| Curved postcritical continuation | Completed N32 scoped branch at `221b4fe`, 23 workers; genuine three-target signed advances from accepted nonzero seeds. Not a loading path from rest. |
| Curved signed-spectrum accuracy | Completed N32 comparison at `9559f66`, worst signed-rate error 1.3895%, MAC at least 0.9999839. Both equilibria have one negative direction; no stable-postbuckling claim. Historical N24 failure remains unchanged. |
| Full reference/finite-state/slenderness acceptance | Map the preserved local and engineering campaigns to the actual current operator and admitted domain. A passing historical straight facade or a few endpoint spectra cannot substitute for this mapping. |
| Current public opt-in and isolated wheel | Still open. The existing `ge-beam3` facade is the older accepted straight P3 implementation; the last installed native wheel predates the latest interfaces. Do not silently redirect it or call that wheel current. |
| Independent-author review | Still open for the current complete delivery candidate. Internal tests and saved-data audits are not independent-author review. |
| Objective eccentric/curved finite-rotation beam-shell connection | Still open and required for overall completion. Existing shell operators and defaults remain unchanged. |

No production-qualification flag, default, version, tag, publication or public
selector has been changed by these interface closeouts. Overall goal remains
active; do not mark it complete while the delivery or connection gates are open.
