# P5 centered-chord comparison closeout — solver FAILED

The exact registered command ran once under resource request
`1b6bdcd793404eae8d19435b708701d7`. Request JSON: 663 bytes, SHA-256
`44848DC057F3185E93F472F483FB50B8610254E2F555CD49F3257C2EECA9EE73`.
Freeze: `ca472021b2a4557ec12cc9b6721358482cf33db2`, tree
`149b15d2016cb7730f61cacd7cf8f782f3da5caa`; parent
`b9b93afe07b05f6844c0c4e810965a9e450698de`.

The resource administrator explicitly approved the request in ledger row 638.
The exact stored command was invoked after frozen-authority validation and
global-lock acquisition. The coordinator returned zero and released the lock
in finally. Child PID 7192 was independently absent afterward. No request
was retried and no historical worker or larger onset sweep was started.

## Genuine outcome

`RESEARCH_CENTERED_CHORD_COMPARISON_CAPTURED` is a diagnostic capture result,
not solver qualification. `solver_outcome=FAILED`,
`production_qualified=false`, `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

The initial target 0.1 committed and replayed. Target 0.095 reached its
16-update limit without satisfying equilibrium and was not committed.
The last residual was `1.3856836297712436e-11`, above the unchanged `1e-11`
limit. There were 4448 mixed evaluations, 3 INITIAL observations and 81
TARGET observations. No `target.json` or qualification aggregate exists.

The actual last successful evaluation is preserved and independently
reconstructed by the worker, with residual `1.3856836297712436e-11`, summed
linearized local-force estimate `4.2758440815430935e-14`, largest estimate
`3.4645867258656403e-15`, and largest internal residual
`6.510803452364905e-17`. This is uncommitted diagnostic data, never a
substitute for an accepted trial. In this particular update-bound failure it
matches the final iterate; other failure snapshots may be rejected candidates.

The earlier force-accuracy attempt stopped at `1.0956756401139303e-11`.
Although centering improved the saved scalar cancellation audit, it did not
improve this assembled stopping residual. Neither the smaller scalar error
nor the very small internal residual proves an assembled roundoff bound.
Do not claim a convergence fix, element NO-GO, absent equilibrium, or exact
diagnosis of the remaining error source from this comparison alone.

## External evidence and process

Root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-centered-chord32-20260906-e919f22758c948f5b22dbfcbd0b1fd3a`

Ten files, 2,395,849 bytes, all retained. Complete per-file byte counts and
SHA-256 hashes are bound in the accompanying static closeout test.

| Record | Bytes | SHA-256 |
|---|---:|---|
| diagnostic.json | 4614 | 3EE2E125EEC84984A3823105BB997741E83D906DDBC9EA1D0D52CBD58FED0166 |
| centered-chord32/complete.json | 6727 | 1808350FFFA265535F3A40AB0115AEB3F8B1701AA8AB8D237ECD0078CB1C2E65 |
| centered-chord32/initial.json | 1157002 | AE047A650282BA7F6870BF7B471372E85A6B2BBD831AEC00D5EB4807C09E8CFA |
| centered-chord32/failed_last.json | 1185851 | 08329F11B7D7DD17566446F02DA922FA008A9EB84CE7C709B264B4F293AB4422 |
| centered-chord32/progress.jsonl | 36429 | EADC50BAB49CD41027A8D89D5867AD8B8DCBC90F5C61DAB422245426701F8FCC |

Worker wall time: 72.71888729999773 seconds; CPU: 72.484375 seconds; peak
process-tree memory: 176660480 bytes; exit zero. All approved resource bounds
were met. Zero-byte stdout/stderr logs are preserved. Terminal read-only
inspection revalidated the complete packet and all 27 historical bindings.
Resource completion was reported to the administrator for independent
accounting, expressly distinguishing capture success from solver failure.

The administrator subsequently recorded `COMPLETED_PASS` for diagnostic
resource execution only after independent hash, inventory, process and lock
checks. Its notice explicitly retained the FAILED solver outcome and granted
no rerun, onset sweep or successor execution authority. The three static
closeout tests passed in 0.33 seconds without any mechanics rerun.

## Next development boundary

Do not extend iterations, relax the residual, tune coefficients or launch
another mesh sweep merely to seek a pass. The next useful investigation is a
small, independent precision audit of the saved state: distinguish represented
configuration/increment rounding, local chord arithmetic, force assembly and
true stationary residual. Any higher-precision or compensated state successor
must preserve objective rotations, first/second variations, rollback and
replay, and receive its own tests and bounded execution authority.

The broad straight/curved GE-B3 qualification, nonlinear/material parity,
mass/dynamics, production restart and objective beam-shell connection remain
open. Existing B2/B3/Q4/S3 mechanics and defaults were not changed by this
comparison. No push, merge, publication or activation was performed.
