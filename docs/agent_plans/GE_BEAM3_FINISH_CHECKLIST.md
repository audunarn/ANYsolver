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

1. **Standalone workflow closure.** Finish the current native application
   interface for supported straight/curved section families, load/state
   ownership and buckling workflows. Audit existing evidence against the
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

## Buckling interface now implemented; frozen verification next

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

Next verify that frozen source twice, and process the already accepted N8 Euler
factor packets with `ge_beam3_buckling_saved_euler.py`. That script verifies the
old archive and actual preload checkpoint hashes before numerical processing;
it must never rerun those preload solves. Record these as numerical/interface
verification, not reclassification of the historical Euler campaign or full
standalone qualification.
