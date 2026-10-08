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
publication, incompatible controls and material histories. The 17 focused source
controls **passed** at source commit `985eb9eb2bb226d0e15821b92b65a4c07a236a79`
in `source-new-controls-v1`, under original manifest SHA256
`5701cd4d72515e6f682811fc6e36d1e8a2c84badb6d38b966f9429f571aba41d`.
This source verification does not establish installed-artifact verification or
qualification. Isolated wheel, installed controls and public-example verification
remain **pending**. Required follow-up
also includes the existing finite distributing public/material/native/cyclic tests
and legacy BL5, curved and native point displacement/checkpoint regressions.

Installed development verification completed on 7 October 2026 for product
6399be68 and source-control identity 985eb9eb. Wheel SHA256:
abc87da6987961edc4eec35f641be018aa148103eb319af0b2a876288ad61087.
All 431 installed Python files match source, and solver imports came exclusively
from the isolated site. The 17 new controls, 13 affected controls and two cyclic
generalized/coupled unload/reload/restart controls passed. The public example
completed force seed, displacement, checkpoint, restore, continued solve and
physical recovery: equilibrium 1.162664177e-12; compatibility 1.002599187e-17.
Effective settings were CPU0, one numerical thread, JIT disabled and a 2 GiB limit.

The first example attempt timed out before final validation and remains failed.
Its charge was retained in the same 400-second allowance: 223.8072112 seconds used,
176.1927888 remaining, with a 60-second reserve. Evidence remains in
`.development/distributing-displacement-installed-20261007/`: execution receipts,
`installation-v1.json`, `handoff-v1.md` and `root-terminal-result-v1.json`.

Supporting independent OpenAI review found no concrete product defect. Required
programme reviews, actual-zero-load/signed plastic reversal, consumer completion,
scale, external qualification and aggregate G0-G6 acceptance remain open. These
checks establish experimental behavior; they do not establish qualification or release.