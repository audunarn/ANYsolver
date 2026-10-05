# Native point arc development decision

Decision sought: reuse the existing physical tangent-plane continuation route
for native generalized/fibre and Q4/S3 accepted material histories, without
changing mechanics or omitting retained equilibrium variables.

Established: actual shell additive/spatial-left beam update metric is already
implemented; algebraic coordinates do not enter the path norm. Assembly directly
subtracts the affine nodal-dead-translation pattern, so the existing sparse load
border is its derivative. Native displacement codecs/history adapters already
preserve fixed predecessors and charted material state.

Discriminator: paired Q4/generalizedJ2 and all-S3/fibreJ2 endpoints, both ordinary
and rebased, through native continuation, cancellation, fresh restore and repeated
continuation; corrupt native/predecessor payloads must fail without publication.
Legacy arc tests check unchanged identities and event behavior.

Action: retain the extension if scoped lifecycle/material parity and impacted
legacy checks pass; repair an identified defect without changing laws/tolerances.
Do not infer capacity or first-limit-point acceptance from a small arc advance.
Follow with a bounded explicitly defined native turning-point/descending-branch
case and installed verification at the meaningful integration boundary.

Limits: one numerical job, 600s/2GiB/affinity1/pools1/JIToff. FormalF03 unconsumed;
protected references/canary untouched. Supporting OpenAI review is not required
different-family scientific acceptance. No merge/push/publication authority.
