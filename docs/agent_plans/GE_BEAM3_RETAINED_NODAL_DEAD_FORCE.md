# Retained nodal dead-force successor

Base `9a49ea8dc5a6bfc82636f47f2cdd08e8afcad052`. Preserve all existing
element/section mechanics, historical evidence and public/default routes.

Add a private exact nodal dead-force tuple, sorted by unique physical node ID,
with three finite binary64 spatial force components only. Reject duplicates,
unknown IDs, booleans, nonfinite values and moment-shaped rows. The force is
assembled once globally, including a shared node; external rotations/cells see
no added residual or tangent. Work is F dot (current-reference position), using
the compensated coordinate pair. Force gradient is constant; Hessian is zero.

Use a separate load policy and accepted-chain schema. Each record retains the
existing per-element line-work entries followed by one global nodal-work entry.
Its complete program binds the point forces, targets and frozen model. Reuse
issued-state/contiguous-history validation and transactional Newton without
fabricating a distributed-only checkpoint or changing the old schema bytes.
The old private Context gains explicit program/schema/policy hooks; the shared
controller and modal implementations are factored through private helpers.
Old distributed entry points still accept only their original exact Program.

The nodal successor has its own modal policy. Subtract the exact accepted nodal
force from the assembled current-rest residual before equilibrium validation;
conservative stiffness, current committed-history elastic-interior policy,
physical cell inertia and paired spectral arithmetic remain unchanged.
No nodal moments, follower loads, new state-store mutation or public integration.

Verify independent linear work/directional derivatives, exactly unchanged
tangents, once-only shared-node loading, actual point-force/reaction balance,
moment balance, complete-chain restart, mutation/cancellation/failed-step
rollback, cross-schema rejection, analytical signed axial F/EA fields and
current-rest modal capture. The next engineering gate will port prestress/Euler
reference cases; these point cases alone do not qualify buckling.

Run signed axial smoke before expanding to local and connected tests. Verify
old distributed port/guard/modal scientific bytes against their archived outputs.
After passing rehearsal, run the new cases twice in fresh directories and require
byte equality. One numerical-library thread, 24 GiB and 600 seconds per child,
at most three concurrent children, 1800 seconds/wave, 120-second CPU inactivity,
exclusive outputs and terminal tree accounting. No automatic retry. Keep the
120-second cooperative Context bound. Independent review, full environment,
engineering/material/fibre, public packaging and objective connection remain open.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
