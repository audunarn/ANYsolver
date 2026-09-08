# Sixteen-macro seeded three-step arc crossing

Base eb0c4714ca17e284d6772d4f1ea5944524d6838f. Research-only development
gate: exactly this plan and tests/test_ge_beam3_arch_seeded_crossing.py.
No mechanics, quadrature, coefficients, tolerances, public routes or defaults
change. Independent authorship review remains PENDING.

## Frozen inputs and programme

Bind the accepted sixteen-macro pre-peak status and archive manifest. Read
its cycle-A source checkpoint: 2372889 bytes, SHA-256
C65730E97EC1097832C95DA21312EC67162A8B0B2422274C701BE4131B1EFCA0.
Bind the cost-status file SHA-256
BFA0897280679A20A2FEE2B8DC5866310DB82B5C95DFBE38FC90BDD80F53A2AB.
Check these inputs before mechanics. Reconstruct the exact existing model,
section, reference-arclength distributed load and translation programme.

Use TranslationArcSource, forward sign +1, explicit HISTORY8M and
ArcProgram((.12,.12,.12),.01, ..., parameter_scale=.1). Start from the exact
source, not from a rerun of translation or a post-peak history. This is a new
three-step programme, not a retry of the failed historical two-macro case.
No automatic step reduction, retries or tuning after observed results.

## Checks

Require three completed arc steps and seven total snapshots. Validate the
whole source and combined history with unchanged validators, preserve all four
source snapshots exactly, and require full decode/re-encode byte identity.
The 8-MiB envelope and every existing 60-second validation bound remain.

At all three accepted states read the actual crown displacement (node 17 uy);
never substitute a prescribed translation target. Compare to the existing
BVP9 continuum at that displacement, evaluated directly at all 128 native
stations. Preserve position, frame, strain, physical resultant and
compliance-norm diagnostics; require zero plastic history and constitutive
agreement <=1e-11. Require each load-density error <2%. Use the unchanged
analytic bordered accepted-state slope helper (not an independent oracle).

Require increasing accepted crown drops, positive first and negative final
native drop slope, at least one decrease in accepted load density, and
negative final continuum slope. Record a development crossing only if all
conditions pass. These tests do not establish full spatial stability,
modal/buckling qualification, all beam parity or public integration.

## Execution and adjudication

Freeze before one bounded rehearsal. If it passes, run two fresh-directory
replicas from the same frozen commit, at most two concurrently, and require
byte-identical scientific JSON, including the complete checkpoint and fields.
Keep raw timestamps and resource diagnostics outside scientific outputs.

Each child: one numerical-library thread, 24 GiB process-tree memory,
600 seconds wall time and 120 seconds without CPU progress; entire wave
<=1800 seconds, no automatic retry. Complete tree cleanup in finally.
Emit native predictor/iteration/commit checkpoints and field/reference phases.

On a process, serialization, or numerical failure preserve all actual logs,
packets and incidents; do not fabricate absent canonical evidence or relax
gates. Do not run replicas unless rehearsal passes. A short programme that
does not cross is a genuine failed development gate, not a qualified beam.
Rehearsal and replica inventories remain separate. All prior source and
NO-GO evidence remains immutable.
