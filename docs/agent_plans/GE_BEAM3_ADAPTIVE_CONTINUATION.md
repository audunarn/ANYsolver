# Adaptive arch and nonlinear restart development gate

Base 3825ffc0701f845abd1c9ef2944ea64aa1784a66. Freeze exactly this plan and
tests/test_ge_beam3_adaptive_continuation.py. No production source, mechanics,
tolerance, quadrature, selector, default or version change.

Bind native adaptive status SHA-256
2751196FBB083E9D333A27D6FA680A0A4E1698FB853A82DCAC7B6D108B01C778 and
its accepted archive manifest. The existing hash-bound sixteen-macro source
reader remains unchanged. All selected archive files must match manifest byte
counts and SHA-256 before numerical evaluation.

## Nonlinear restart inventory: two cases

Read the exact cycle-A curved-plastic and plastic-rejection source/completed
packets. Reconstruct their original programmes and models; do not rerun
translation targets or rejected trials. Full accepted-history validation
and equilibrium/predictor replay remain mandatory.

For the accepted-step case, create a fully validated first-accepted-step
prefix and resume the remaining step. For the recorded-cutback case, create
the validated source-only prefix retaining the first CUTBACK record, then
resume the smaller pending step. Require exactly one new committed step in
each case, unchanged cutback history, eight positive plastic stations,
native recovery and full decode/re-encode identity. Both final packets must
be byte-identical to their respective archived completed packets.

## Adaptive arch inventory: one case

Use the unchanged sixteen-macro source (2372889 bytes, SHA-256
C65730E97EC1097832C95DA21312EC67162A8B0B2422274C701BE4131B1EFCA0).
Run AdaptiveArcProgram with three accepted steps, initial .12, min .03,
max .24, length scale .01, load-parameter scale .1 and explicit HISTORY8M.
Retain existing defaults of eight cutbacks / 128 attempts. This is a new
adaptive programme, not a retry of a historical failed programme.

The expected accepted schedule is .12, .12, .24, from the frozen controller
and the accepted earlier iteration counts. Require that growth actually
occurs; do not change the schedule, thresholds or references after execution.
Require seven snapshots, exact source prefix, full canonical roundtrip and
the unchanged 8-MiB and 60-second validation bounds.

At actual accepted crown drops, compare the unchanged BVP9 reference directly
at all 128 native stations. Require zero plastic history, <=1e-11 constitutive
agreement, <2% load-density error, increasing drops, positive first and
negative final native slopes, an accepted load decrease and negative final
continuum slope. Preserve remaining field/slope errors as diagnostics.
No finite sample establishes complete spatial stability or qualification.

## Execution and interpretation

Freeze before one rehearsal per inventory. Only if both pass, run two
fresh-directory repeats per inventory and require byte-identical scientific
JSON within each inventory. Keep inventory counts separate.
Use one numerical thread, 24 GiB process-tree memory, 600-second child wall,
120-second CPU inactivity, at most three children and <=1800-second waves.
Exclusive fresh output roots, complete process-tree cleanup, no automatic
worker retry. Emit progress before archive decoding, prefix construction,
native restart, every native iteration/commit and field/reference phase.
Preserve all actual failure packets/logs; fabricate no absent result.

A pass is development evidence for these adaptive continuation/restart cases,
not full beam qualification. Independent review remains PENDING. Wider
slenderness, postbuckling/spatial stability, practical scale, broader material/
load/state and cutback parity, physical mass/modal/prestress/buckling, installed
public integration and objective beam-shell connections remain open.
