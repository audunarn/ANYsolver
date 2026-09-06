# P5 compensated-coordinate comparison — target converged

Request `4d4cbecbbba445a4a9656976f1e2dee8` ran exactly once. Immutable request:
665 bytes, SHA-256
`C36880A0784E2B9224497A43829F60F00A299B82ECE4F97D63AA86018A191ACC`.
Approved freeze `29b0d4e06ba4a1275411b3dd39b8843e6cb9c457`, tree
`8597be55bcb040b86d913f06b0034dba30ff4876`, direct parent
`8058cbb95d4cbd2a5712c056b1fdfe55ffd5acec`.

## Outcome

`RESEARCH_COMPENSATED_COORDINATE_COMPARISON_CAPTURED` with actual
`TARGET_CONVERGED`. Initial target 0.1 and target 0.095 both committed and
passed accepted-origin replay. The previously failing first increment reached
residual `5.506791506773546e-12`, below the unchanged `1e-11` threshold, after
three updates and 416 mixed evaluations. There are 3 INITIAL and 13 TARGET
observations. No failed-last snapshot was needed or fabricated.

The accepted 65-node state retains nonzero low coordinate parts, largest
`5.540713562152415e-17`, with zero low parts at clamps and the controlled target.
The 32 elements contain 512 physical station records. Their summed estimated
local-force error is `4.2130458845588706e-14`. No plastic activation occurred in
this elastic diagnostic. The low-part fields remain bound in trial, element
response and committed-state identity, not discarded after convergence.

This resolves the two-state diagnostic hurdle. It does not establish full
onset convergence, broad engineering accuracy, modal/dynamic qualification,
general material parity, production restart or an objective beam-shell joint.
No independent full mechanics qualification is claimed.
`production_qualified=false`; `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

## Resource and evidence

The administrator APPROVED ledger row 640 preceded exact lock acquisition and
stored-command execution. Worker exit 0; wall 14.201930600000196 seconds; CPU
14.0625 seconds; peak process-tree memory 178257920 bytes. Child PID 24224 was
independently absent afterward and the lock was released in finally. No retry,
second execution or larger sweep occurred.

External root:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-compensated32-20260906-530101a9fd6a4c1cbf864484571fc219`

Ten files, 2,378,664 bytes, retained. The accompanying static closeout test binds
every file's byte count and SHA-256. Selected identities:

| Record | Bytes | SHA-256 |
|---|---:|---|
| diagnostic.json | 5854 | FC5E4F12B361C023B7B72C4F81AAE0335770339F0C0374DE931931A91C62D12F |
| compensated32/complete.json | 5967 | 3FC422671EA4FD86F5F38F7F517F778213E9F35E5993E3BE32F55EC7A2E06A66 |
| compensated32/initial.json | 1159786 | 10A13FD5CE0C5867FD86C87EBE4E7C10FE8D431122FEFBE8CBC99ACB3F62CA0F |
| compensated32/target.json | 1194913 | AFC4D21EEACD3212F34A6CB2809F398510B079241AAADB0C624E048B9463DB75 |
| compensated32/progress.jsonl | 5639 | D9A918428546F24EC4818646802A1F042382DF46821149BD5751B942A29A8529 |

Read-only inspection revalidated the new records and all 37 bound historical
files. The earlier failed outcomes remain immutable. The elapsed time is this
run's diagnostic, not a paired performance qualification or general speed claim.
The result was sent to the resource administrator for independent accounting.

The administrator subsequently recorded `COMPLETED_PASS` after independently
checking the reported artifact identities/bindings, ten-file inventory, process
limits, target convergence, absent failed snapshot/PID/lock and retained claim.
That notice explicitly grants no independent mechanics qualification or onset
execution. Three static closeout tests passed in 0.32 seconds with no mechanics
rerun; `git diff --check` passed.

## Next gate

Prepare a separately frozen compensated 32-element onset refinement using the
existing case, support, engineering reference and stopping criteria. Extend
its raw records and integrity checks to the explicit coordinate low parts;
preserve the existing 4/8/16 and failed-32 evidence unchanged. A new request,
resource approval and complete small rehearsal are required before execution.
Do not execute the onset sweep merely under this completed request.

No production source, existing beam/shell mechanics, default, package version,
push, merge, tag or publication was changed by this comparison.
