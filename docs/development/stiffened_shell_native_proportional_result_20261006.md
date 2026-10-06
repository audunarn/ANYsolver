# Native proportional arc screen — 6 October 2026

The installed experimental GE owner completed twelve proportional-load arc
increments from the verified force-control prefix at factor0.5. This is a
working continuation and lifecycle result, not scientific qualification.

Source candidate: `151cb3d452dd6b08d4b8c36747e0637c40dce371`.
Unchanged ANYsolver0.4.7 wheel SHA256:
`6464174eb675c4eafd72f01a8ac707bb44d39946c5a7919126e316bc148a63c7`.
The entry verified all430 source/wheel/site Python modules and actual imports.
The exact fixture, actions, controls, input copies, settings and receipts live at
`.qualification/b3-ge-e4-pl/r8-native-proportional-capacity-dev-20261006-v1/`.

## What changed and what ran

The explicit new example route uses `F(alpha)=(0.5+alpha)F_full`, restoring the
verified generation3 checkpoint. It retains the existing matching8x2Q4 strip,
two eccentric native stiffeners, retained variables, BL5 connection, material
laws and director metric. Radius0.01 and positive tip-z orientation were fixed.
No force seed was rerun and no parameter or mesh sweep was performed. The
previous opposite-probe force-seed failure remains separate historical evidence.

Focused tests:34passed,3full numerical tests deselected. The actual installed
screen accepted12arc increments and persisted13complete checkpoint/state pairs,
including its restored origin. Equilibrium, constraint, force and moment balance
checks passed at every saved endpoint. Maximum normalized discrepancies were
3.162e-9,7.486e-15,8.591e-12 and5.724e-12 respectively, against frozen thresholds
1e-8,1e-9,1e-8 and1e-8.

A load-factor direction change was observed while tip displacement increased:

| Generation | Proportional factor | Tip z (m) |
|---|---:|---:|
| 13 | 0.8081016856728431 | 0.1826747840284934 |
| 14 | 0.8089701254508224 | 0.19664128222672247 |
| 15 | 0.8084092970853850 | 0.2103705115747401 |

This is an **unvalidated turning candidate**, not a verified first limit point
or engineering capacity. No material-history/update activity was observed.
The preloaded origin is a loaded state, not a stress-free geometric imperfection.
No external reference, mesh convergence, stability or physical-connection
qualification follows from this result; G4D and the complete programme stay open.

## Lifecycle and execution

Installed checks verified full public recovery and checkpoint equality after
restore, changed direction/controller refusal, pre-step cancellation, corruption
refusal on a fresh owner, accepted-prefix cancellation, restore and continued
replay of already observed early endpoints. Root independently checked all13
saved byte hashes/sizes and state/inventory equality. Independent OpenAI Read
review found no evidence mismatch; different-family acceptance remains unmet.

Both runs verified CPU0, single-thread numerical pools and disabled JIT.
Focused source process wall:20.3669359s; installed screen including early replay
and lifecycle checks:198.5712466s. Combined218.9381825s before near-turn verification. The separate savedg14->g15
one-step replay passed complete recovery/byte parity, precancel and refusal
preservation in29.1011479s; final248.0393304s of approved600s.
Installed sampled process-tree peak214011904B; limit2GiB. These are development
execution costs, not a speedup or comparative performance claim.

The supervisor's original cleanup and post-child hashing defects were repaired
before execution. Versioned failed findings, preparation and raw outputs remain
preserved. The one primary physical screen is consumed; unused allowance permits
only its scoped verification/repairs, not extension, tuning or another screen.