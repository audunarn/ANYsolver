# Native generalized displacement continuation development

Base: 471feacaa53814c2f554510b7bf0a1f1b99d6b76.

Implement a private translation-control programme around the accepted analytic
load column. Solve the general full bordered system, never K-inverse load
sensitivities. Signed and nonmonotone load factors are allowed; only finite
binary64 effective loads are admitted. Keep exact affine translation control
in every trial. Use existing native state-store transactions and unchanged
distributed and nodal work maps. Do not alter existing mechanics or defaults.

A separate checkpoint envelope binds exact programme, targets, signed load
parameters, iteration records and a complete stress-free genesis/state chain.
The unchanged combined codec validates effective loads using unit inner
coordinates; those are not the outer path parameters. Recompute that mapping
at encode/decode. Require external SHA-256, strict canonical JSON and unchanged
2-MiB/65-snapshot limits. Before commit validate and stage the entire checkpoint.
Never infer missing history. Failed/changed/nested programmes preserve the last
accepted checkpoint. Restart must reproduce uninterrupted bytes.

Rehearse a signed analytical elastic bar, complete prefix restart, checkpoint
mutations, a synthetic singular-K bordered algebra check, factorization failure,
live input mutation and nested-entry rejection. The singular-K algebra check is
not beam postbuckling qualification. Then exercise curved and connected plastic
combined-load paths with recovery and prefix continuation. Frozen targets at
node 3 ux are (.03,.06) and (.06,.12), respectively. Prior force-control records
in the deb0d97 archive inform only target selection, not classification.

Use unchanged 1e-12 normalized solve merit, 1e-11 accepted-equilibrium validation
and analytical reference tolerance. Do not tune loads or tolerances after
observing results. Run separate local/geometry inventories and smoke before the
full rehearsal. After a clean implementation freeze run each inventory twice
in fresh external directories and require byte-identical scientific output.
Keep an additional safety inventory for failure/cancellation after an accepted
prefix and preflight controls. Each geometry's single node is its complete
bounded rehearsal, including solve, decode, recovery and resumed solve; do not
repeat it under an extra smoke label. The small analytical smoke precedes all
complete rehearsals. No generic beam postbuckling claim follows from these paths.
Each child uses one numerical thread, 24 GiB, a 600-second wall ceiling and
120-second CPU-inactivity bound; at most three workers and 1800 seconds per
wave. No automatic retry. Preserve failures and partial logs externally.

This is not production qualification, arc-length integration, a demonstrated
limit-point/postbuckling branch, dynamic reduction or spectral authority. The
existing private model/support bounds remain. Nodal translational point loads,
constant preloads, general support/initial-field/MPC parity, scalable history
and arc-length are successor work, not silently inferred capabilities.

## Preserved initial smoke incident

The first signed-bar smoke stopped safely at the second target because the
new effective mapper retained negative-zero transverse load components under
negative lambda. The existing unit-coordinate codec adds a zero origin and
therefore reconstructs positive zero; pattern signatures disagreed. Preserve
the failed command/logs and initial four-source snapshot. Normalize only zero
components in the new mapper and add an exact signed-zero equivalence test.
Also reject a nonfinite assembled external norm explicitly before forming the
solve merit. No previous codec, mechanics, load value, target or tolerance is
changed. Rehearse the corrected source in fresh directories before freezing.
