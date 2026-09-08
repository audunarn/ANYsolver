# Retained generalized physical translation control: private gate

Base: `b891c08ceea340307bbcda6da1769a3b6e543de2` (completed Euler closeout).
This additive controller uses the existing retained generalized operators and
spatial dead nodal forces. It changes no section/element equations, quadrature,
legacy mechanisms, shell mechanics, defaults or public APIs. It is not an arc
controller, engineering postbuckling result or production qualification.

For physical node c, frozen spatial unit direction a and reference position Xc,
prescribe a dot (xc-Xc) = d. Compensated positions are retained. The accepted
load factor lambda is an independent state field, not a displacement target
reinterpreted as a force-program parameter. Only spatial dead nodal forces are
admitted here; distributed loads, couples and follower patterns are not routed.

At every Newton iterate, solve the complete bordered system
`[J, -f; a.T, 0] [delta_u; delta_lambda] = -[r; a.dot(xc-Xc)-d]`.
J is the existing actual spatial retained residual Jacobian, with all internal
cell rotations and section resultants present. Never invert J separately to
derive a force sensitivity. An unbordered singularity need not be a bordered
singularity. A singular full border fails closed.

Convergence requires equilibrium, compatibility, normalized control error and
the complete remaining bordered correction at most 1e-11. Scale translations
by reference length, rotations by one, retained resultants by their current
norm with floor one, and load-factor correction by max(1,abs(lambda)). Use a
projected frozen-border correction merit for line search; final acceptance
always recomputes the current full border. Preserve spatial multiplicative
increments, compensated coordinates and fixed accepted material origins during
all trials. Retain the existing 24-iteration, eight-backtrack and 120-second
cooperative Context limits; no automatic retries/cutbacks.

Own a distinct exact Program, State and checkpoint schema. Strong issuance
binds every accepted state and its full record bytes to the creating Context.
Reject cloned/foreign/mutated states, forged or discontinuous local records,
force/control cross-schema restarts, rehashed reaction/work/recovery/history
mutations and dirty live model/program/control maps. Reconstruct every state
and material origin at external-SHA-bound restart. Never cast control capsules
into the earlier force schema or claim a force programme ran.

Initial bounded tests: analytical straight axial load/unload/reversal and
restart; curved/coupled nodal-force solution ports with independently measured
physical targets; full-border fold algebra; exact load column; ownership,
rollback, cancellation, remaining-correction and serialization mutations.
The fold algebra is not a beam postbuckling result. Verify old force/scientific
bytes separately. Freeze source before bounded smoke/rehearsal execution.
Each child: one numerical thread, 24 GiB, 600 seconds, 120-second CPU-inactivity;
at most three children, 1800 seconds/wave. Logs and science stay in fresh external
directories, failures preserved and never retried automatically. Repeats follow
only after a passing rehearsal; independent review remains explicitly pending.

Broader controlled nonlinear histories, objective covariance, arches, real
post-limit comparisons, arc length and controlled-state modal adapters remain
successor gates. No full qualification, publication or activation is claimed.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

## Preserved first rehearsal and comparison-authority correction

Initial freeze `fd42d3e84d82a3a65418fad5d3b29a7189caf371` passed 34 smoke
checks, two analytical checks, three rollback checks, and 22 old nodal checks
(separate inventories). The curved port had one pass and one failure. Preserve
that failure; do not relabel it as a passing rehearsal.

The two-macrocell port failed its unchanged 1e-11 load-factor comparison:
the inferred factor differed by 4.829318056565057e-10. Read-only saved-state
diagnosis found the original force-state residual 3.5637793271954375e-12 and
remaining correction 3.897332510161963e-12, both within its original 1e-11 gate.
At the identical accepted geometry, the full control border predicts a factor
correction -4.827535166001761e-10. This is amplification of comparator-state
error by inverse compliance, not evidence of changed element mechanics.

Two explicit fixed-load Newton corrections with the SAME material origin bring
the comparison residual to 5.187102689079677e-19 and its factor correction to
1.795405870947635e-15. Freeze this stricter comparison preparation for BOTH
registered curved ports: two corrections, then residual/compatibility/remaining
correction at most 1e-14 before measuring the displacement target. Keep the
original force capsule immutable; the refined trial is unaccepted comparison
data, not an executed or issued force history. Keep every original port gate,
including the 1e-11 factor and full-state comparisons. No controller or physical
operator change is needed. Save actually created comparison/control capsules
before assertions so any subsequent failure retains its complete raw data.

The original failed port logs are under external temporary directory
`ge-beam3-translation-rehearsal-ports-vg2h7y4g`; stdout SHA-256
`B462635386462A6B996666E636EB21E61F3220584A6DFF403D778880F2488402`,
process receipt SHA-256
`F68242A72334EE8CBBEBDB2A3E7A7180594153375B05344819CD79600E223A90`.
Saved-state diagnosis is `ge-beam3-control-sensitivity-diagnostic-gkq1661e`;
preserve it with the failed evidence before closeout. It did not rerun the
failed controller programme or modify the original accepted force checkpoint.
