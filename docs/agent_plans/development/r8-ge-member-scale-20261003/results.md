# GE member admission and practical-size point-bond development

3 October 2026. Solver library unchanged from `f58abf96`; consumer source
parent `c78b55c`, committed locally as `4d6d4d0`. Experimental development
only. No aggregate gate closes.

## Delivered behavior

Removed ANYfem's inherited 16-member cap for the point/BL5 binding
parsers and their derived input schemas. Nonempty typed definitions,
per-definition payload/hash checks and the32MiB input-file limit remain.
The previous installed consumer rejects the actual32-member fixture; the new
installed consumer constructs it, saves/reopens standalone and native Project
inputs, solves, restores and continues through the same public facade.

The maintained multi-member example has four connected straight stiffeners,
32native B3 elements,24Q4 shells and explicit30mm point offsets. Mixed Fx/Fy/Fz
loads exercise the eccentric lever arm. It verifies equilibrium, force/moment
balance, eligible factor reuse, recovery and exact fresh-owner restart.

## Practical-size development probe

The unchanged GE library also completes these **reference-linear** routes:

- 100 x 100 Q4 shells; ten stiffener lines, each with 100 native B3 elements.
- 110 full-pose point connections, every tenth beam-element boundary.
- The entire 101-node shell edge is clamped; beam axes follow exact selected
shell rows with only the declared 30 mm normal offset.
- 97,320 mixed unknowns, including 24,000 native retained variables and 660
constraint rows; 4,972,608 stored sparse matrix entries.
- Standalone input and native Project save/reopen, two compatible load levels,
recovery, binary snapshot, fresh-process restoration and continued loading.

| Quantity | Observed |
|---|---:|
| Scaled equilibrium | `5.14182886629943e-10` |
| Scaled compatibility | `2.3243938810345e-14` |
| Force balance | `9.218606273361428e-10` |
| Moment balance | `9.648479862103706e-10` |
| Binary snapshot |1,561,799bytes |
| Eligible factorizations per unchanged owner |1 |
| Checkpoint-process wall time / sampled peak |370.787s /3,073,085,440bytes |
| Fresh restart-process wall time / sampled peak |373.073s /3,071,393,792bytes |

Both processes meet their separate600s/8GiB bounds. Compute pools and Numba
are verified at one thread, JIT off; seven process-tree threads were observed.
This is not a combined<=600s route claim. Snapshot reconstruction after fresh
compilation takes0.028s; compilation itself takes about350s.

Exact cross-process comparisons cover shell displacement, beam coordinates,
multipliers, reactions, snapshot re-encoding bytes and the next load's four
arrays. The restart consumes the earlier snapshot; matching its SHA does not
mean an independently regenerated first-solve snapshot.

## Cost diagnosis and next action

A separate compilation profile uses400Q4/120B3 elements. Of27.722profiled
seconds, shell assembly accounts for22.635s (about82%). Its qualified Q4
response takes19.194s;800inherited base-kernel calls for400cells take12.560s,
and400qualified zero-state corrections take11.471s. Frame sensitivity takes
1.351s and beam assembly4.118s. Cumulative times overlap and cannot be summed.

No repeated model-wide quadratic preparation was found. Investigate narrow
historical-flat, virgin-Q4 reference-state reuse first. It must prove local
force/tangent and assembled solution/reaction parity at the required1e-10,
cover elastic/J2 virgin and geometry/order/thickness variants, preserve rigid
modes and state ownership, and leave S3/algorithmic/curved dispatch unchanged.
Do not alter the global current-state correction contract. Python COO object
lists are a separate measured-memory candidate. No speedup is established.

## Verification, failures and review

Three maintained solver checks pass on final fixtures across focused runs,
including nondefault shell resolution/point stride and exact geometry checks.
Eight distinct consumer checks pass across focused installed runs: point/BL5
records, invalid inventory/bindings, file-byte bounds, shared modal parsing,
and the actual32-member native Project numerical/restart workflow. No claim
is made that these ran as one clean final aggregate suite.

All413solver and98consumer Python modules match source/wheel/installed-site
bytes. Solver wheel reused unchanged:
`c795a5da5476313a58463f36e84e05aecfa4930e6d338e7597bd97a40c3bcc7d`.
Consumer wheel:
`5f5c203cea8af60e285df8835cf27210e74718c4bbf1bf916711eb8751fd223a`.
Imported locations, dependency versions, runner/fixture identities and effective
settings are retained. Timed and profiling work ran serially.

Failed development evidence remains: the first32-member example wrongly restored
into a used owner; its fresh-owner correction passed. Initial largev1 solved but
failed an escaped checkpoint-header assertion after401.482s/3,068,837,888bytes.
The corrected persisted-process routes supersede that failed driver. The
temporary launcher quoting error started no numerical job. Independent OpenAI
Read review identified the initial eccentric-load blind spot, derived-parser
scope and final geometry-check evidence gap; all were addressed. This is
development review, not cross-family scientific acceptance.

The point-only probe does not qualify G5/nonmatching lines, mesh convergence,
drilling/shear transfer, nonlinear practical scale, material combinations,
performance scaling ratios, external comparisons or release. Those obligations,
physical criteria and formal F03 authority remain unchanged.

## Retained evidence

[Manifest and adjudication](summary-v1.json),
[raw inputs, wheels, arrays, logs and profiles](raw-evidence-v1.zip),
[independent development review](independent-development-review.txt).
Raw ZIP SHA256:
`367277a69075d98dce188a0376cbe93de1486e7fa3e7f827a7a968280badac7b`.
Fresh explicit source/generated inputs and whitelisted metadata only; no
inherited environment dump or protected historical archive is included.
