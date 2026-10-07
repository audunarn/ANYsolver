# Finite distributing fixed displacement source candidate

This development route is experimental and not qualified. It retains the existing
finite area-mean/director/projected-polar footprint law and its physical port maps
and curvature. Reference-only footprint records still admit reference-linear work
only. No scientific acceptance or release claim follows from this source candidate.

First accept an ordinary fixed-force endpoint through `solve(actions, factors)`.
Then pass `DisplacementControl("beam", node, component)` or its shell equivalent
to the existing `solve(..., displacement_control=control)` interface. Components
0–2 select a free physical translation. Targets are absolute signed translations
in metres from the model reference; each must differ from its predecessor.
The solved amplitude is an affine load increment relative to the accepted seed:
`applied_load = accepted_seed_load + amplitude * nodal_dead_load_direction`.
It is not a force-factor cursor. There is no implicit zero-state initialization.

The controller uses the existing bordered corrector and isolated endpoint replay.
Every trial shares one accepted constitutive parent. Complete endpoint mechanics,
material histories, controller history and recovery are prepared before atomic
publication. Cancellation, failed trials and rejected stale publications retain
the complete accepted prefix. Observer failure follows publication and preserves
that accepted step. Results expose detached evaluated physical footprint wrenches
with the accepted generation, including after checkpoint restoration/continuation.

The separate inner mechanical kind is `finite_distributing_displacement`; the
outer policy is `B3_GE_DISTRIBUTING_DISPLACEMENT_V1_DEV`. Legacy checkpoint schemas
and default material meanings are unchanged. Checkpoints preserve actual accepted
beam predecessor/history arrays and selected Q4 J2 predecessor/history arrays;
native fibre policies use the existing native-history codec and physical recovery.
Elastic distributing profiles continue to refuse yielded beam histories.

Fixed signed targets, generalized beam histories, selected native fibre histories
and coupled flat Q4 J2 histories are included in the source candidate. Adaptive
displacement, branch events, chart rebasing, arc continuation, external/staged
loads, rotational control and force stepping after displacement history are refused.
An adaptive force seed is also refused. Existing equilibrium and compatibility
criteria remain 1e-8 and 1e-9, respectively. The selected cyclic material policy
uses its existing immutable reference pattern only for an actual zero applied load.
That cyclic policy requires the complete displacement load direction to equal its
model-bound reference pattern, both on solve and on endpoint replay.
Its snapshot also retains the actual seed force factor as `cyclic_seed_factor`;
the affine base must exactly equal that factor times the same model-bound pattern.
The factor is retained unchanged through displacement continuation and restoration.

`examples/stiffened_shell_ge_distributing_displacement.py` demonstrates seed,
displacement, checkpoint, restore, continue and physical recovery. Focused proposed
controls are in `tests/test_stiffened_shell_ge_distributing_displacement.py`, covering
signed targets, replay, detached physical actions, cancellation, observers, stale
publication, incompatible controls and material histories. These controls and the
example were **not executed** during source-only preparation. Required follow-up
also includes the existing finite distributing public/material/native/cyclic tests
and legacy BL5, curved and native point displacement/checkpoint regressions.
