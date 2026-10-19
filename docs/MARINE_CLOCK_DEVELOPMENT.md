# Contribution clock and accepted-state context

`StepInformation` extends `marine_contributions_v1` without changing legacy
provider/model/spec signatures. Native `marine_mechanical_v1` now supplies it
to each initialization or fixed-step trial. It is not a real fluid-source
admission or full scientific W4 qualification.

Fields: integer step index, positive fixed dt, phase, computed target/prior time,
and immutable previous-state mapping. `time = index*dt`; normal prior time is
`(index-1)*dt`. Initialization has index0/time0/phase `initialization`, no previous
accepted states; its prior-time0 is only a convention, not an accepted-state claim.
Normal phase `step` carries the validated last accepted/recharted state. On step1
this is frame0 with consistent acceleration and the actual initial WORLD pose/rates,
even when input chart rotation/anchor is nontrivial or input acceleration is a guess.

`prepare_step_with_context(history, information)` and
`evaluate_trial_with_context(history, states, layout, information)` default to
the original `prepare_step(history)` / `evaluate_trial(history, states, layout)`.
Old direct `ContributionSet.prepare_step()` calls still pass no information and
retain their behavior. A timed provider must require explicit information rather
than infer time from call counts, pose, trial token or an implicit dt.

The same frozen information and committed-history snapshot reach every Newton
and line-search trial in a step. Caller-owned input mappings are copied; values
are immutable `RigidBodyState` records. Generic ContributionSet callers own the
truth of their clock/start-state declarations; native solver scheduling supplies
them from its actual accepted state. The owner validates body-layout agreement.
Initialization contexts cannot commit physical history, even through direct owner
calls. Native initialization validates output then aborts trials without advancing
history. Rejected/cancelled/failed normal trials preserve prior committed memory.

Radiation policy for the next fluid integration slice: integral at t0 has zero
elapsed duration. No initial trial advances physical memory. First normal step
seeds an empty source history from accepted frame0 velocity in previous_states,
then appends current trial velocity in its trial-local history. Commit only after
convergence/output/rechart/transport/cancellation validation. Use the source's
declared fixed equilibrium coordinate map for velocities; do not guess from an
initial acceleration or use a mutable preparation counter. Real kernels/source
force bases/equilibrium/motion envelopes still require explicit admission.

Fixed short development tests exercise time-varying4(2+t)N on a4kg sphere,
analytic acceleration/velocity, nonzero input chart and anchor normalization,
initial-memory seed versus discarded conspicuous trial history, same info across
trials, cancellation, stale tokens, initialization commit refusal, immutable
mapping copy and malformed phase/dt/index/layout. Existing short legacy failure,
history and diagnostic regressions are exercised separately. Limits/criteria,
independent review corrections and source/installed evidence live in
ANYmarine/TASK.md and `C:/ANYworkspaceWork/anymarine-evidence/marine-clock-*`.
