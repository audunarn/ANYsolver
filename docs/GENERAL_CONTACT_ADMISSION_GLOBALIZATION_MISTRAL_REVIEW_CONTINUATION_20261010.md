# Mistral independent review: preserved partial context

Session52193 ended0 at40 successful effect records without final report. Incomplete, not accepted. Six product SHA bindings unchanged as of closure. These are exact Mistral partial thoughts, not parent conclusions. Finish the assessment; avoid repeated one-more-check audits.

## Preserved reviewer reasoning reasoning-6d240d55-4073-5daf-bd53-524fa89e0209-0

Driver tests: real solves on a small fixture, forcing the first macro attempt to refuse via a monkeypatched solve_semismooth_increment (returning a fake refusal with reason "contact_semismooth_stagnation"), then checking the continuation chronology, force ramp (substep reduced_external == tau * macro reduced_external — since previous_force_values at step 1... wait: sub_force_values = (1-tau)*previous + tau*force. For step 1, previous = force_values_at(0). The test asserts call reduced_external == tau_end * macro reduced_external. That implies force_values_at(0) == 0 (previous force is zero). For the interior-press fixture, presumably the initial load is zero. OK — consistent for this fixture, though the assertion `tau * macro` only holds when the previous force is zero. Fine for the fixture.

Hmm wait — actually there's a subtlety: the test asserts `call["reduced_external"] == substep["tau_end"] * macro["reduced_external"]` with atol 1e-16. sub_force_values = (1-tau)*prev + tau*force with prev=0 → tau*force. reduced_external = T.T @ external. macro reduced_external = T.T @ external_macro. So tau * macro. Yes given prev=0.

Also target: (1-tau)*target_at(0) + tau*target_at(1). Matches the production sub_target formula with previous_target = target_at(0). Good.

The rollback tests: report-boundary exception (manager.evaluate raises after the increment solved) → RuntimeError propagates, then a fresh half-run matches the reference — verifying the model/manager state was restored (no partial publication). Note: the rerun uses a FRESH _case() model? No — `model, definition, settings, program = _case()` then the failing solve on that model, then `rerun = _solve(model, ...)` — the SAME model object. So the test verifies the failed run left the model/manager usable and the result identical to a clean reference. That's a real state-rollback check. Good discrimination.

The cancellation tests: token raises at "contact_path.step:1.semismooth.iteration:1" (inside the first macro attempt — inside solve_semismooth_increment's iteration) and at "contact_path.step:1.continuation:1" (inside the substep loop). Both propagate and the rerun matches. Good.

The restart tamper tests: tau_end tampered to 0.3 → chronology invalid (0.3*128 = 38.4 not integer → raises). revision forged → incompatible. Halvings changed to 0 → contract mismatch. Clean restart completes. Good.

test_stagnation_controls_are_validated_before_any_work: calls solve_increment directly with patience=0 → ValueError. Note: it passes transform=None etc. — validation happens before any use of them. Checks the validation ordering. OK.

Now — the two small test files.

## Preserved reviewer reasoning reasoning-91ba642d-2f4a-502c-9e95-bd7fbd6a2976-0

All five test files read. Now let me do a few remaining verification items before writing the final report:

1. Check the restart/resume code path in static_path.py around line 909 (history validation) — I saw the diff hunk. Let me verify the exact placement and that `_validate_continuation_history_record` is invoked with the right program and that history records without continuation blocks pass (continuation None → return).

2. Check the `semismooth` flag and `solve_semismooth_increment` import in static_path — the closure references `solve_semismooth_increment`; the driver test monkeypatches `static_path.solve_semismooth_increment` — so it must be imported into static_path's namespace. Let me verify.

3. Check where `continuation_active` is defined relative to the restart resume — need to confirm it's defined before the step loop and after restart handling, and that on restart the eligibility checks run.

4. One more potential issue: in the continuation loop, when a substep is accepted, `attempt = sub_attempt` — so after the loop, `attempt` is the last accepted substep. But if the loop's LAST trial fails and exhausts, we break out with `attempt` being the last ACCEPTED substep — but the exhausted path restores and breaks the step loop, so attempt isn't used. OK.

5. Another check: `summed_iterations` etc. include the failed macro attempt's iterations (3 in the test) plus all substeps. The record's semismooth_iterations = summed. The test asserts 3 + sum(substeps). Good — "numerical work accounting/labels".

6. `total_iterations` accumulates across steps for the final result. Includes failed attempts' iterations. Accounting-only.

7. Now — one more careful look at a potential correctness issue in the continuation loop: the `else` branch (substep refusal) restores q/multipliers/normal_forces from boundary but NOT `manager` normal multipliers... it does: `manager.set_normal_multipliers(boundary["normal_multipliers"])`. OK.

But WAIT — there's one thing: on substep refusal, the code does NOT restore `committed_states` — correct since unchanged. But it also doesn't restore... hmm, what about `manager`'s other mutable state that attempt_semismooth touches? `manager.set_normal_multipliers(pressure)` — restored. `manager.evaluate` — read-only? `raw_certificate` — let me check it's read-only. `manager.validate_successor` — under continuation friction is None → moving_friction False → friction_successor None → manager.commit not called. OK.

What about `solve_semismooth_increment` itself — does it mutate manager state? It calls manager.admissible_step_fraction, manager.evaluate... and possibly manager.commit? Let me check quickly for mutations in semismooth_path solve_increment: it uses manager.stiffness, manager.law, evaluate... The old code had the same exposure on failure (the old failure path restored q/multipliers/normal_multipliers/set_normal_multipliers). So the rollback surface matches the old failure path's surface. The substep loop reuses the same surface. OK.

8. Check `_validate_continuation_history_record`'s `program.target_at(step_index)` — the record's target is the macro target at that step; the validator compares with atol 1e-12. But the record's "target" was written as `target.tolist()` where target = program.target_at(step) — exact same float → allclose passes trivially. OK.

9. Now — the one issue I want to nail down: **the witness's `sample_times` default includes t=0.5 for the STATIC call site (first, first, second, second)** — fine (redundant but harmless).

10. **The second call site passes `endpoint_errors=errors`** where errors can be None → witness defaults to zero errors. But the matching call at the same site passes endpoint_errors=None too. Consistent.

Hmm wait — actually at the second call site, `errors` is `(left_error[0][source_nodes], ...) if left_error is not None else None`. And the witness gets `endpoint_errors=errors`. If left_error is None (no endpoint errors), witness gets None → zero errors. The matching call also gets None. Consistent. If left_error is not None, both get the same errors. Consistent. Good.

11. One more: the witness at the second call site is called with (source0, source1, target0, target1) — the SWEPT endpoints. The witness interpolates linearly in t. The matching certificate also assumes linear paths. Consistent.

12. Now — a question about the witness's soundness claim at the second call site: the witness proves min-over-represented-overlap g < -tol over the SWEPT path (at sampled times). The matching certificate lower-bounds the same. The fall-through to overlap_local_swept_lower: the OLD code would have fallen through too (since matching < -tol means `matching_lower >= -tol` is False). Behavior-preserving. BUT — what if matching returns a value >= -tol despite the witness? That would mean matching is NOT a valid lower bound of min g (a bug in matching), or the witness is unsound. The witness firing + matching admitting would be a genuine inconsistency, but the code's fall-through treats the witness as authoritative (skips matching). If both are sound this can't happen. Fine.

13. Let me double-check `_validate_continuation_history_record`'s handling of `record.get("target")` when "target" is missing → np.asarray(None, dtype=float) → array(nan)? Actually np.asarray(None, dtype=float) gives array(nan). Shape () != (len(controls),) → raises ValueError. OK.

14. `type(step_index) is not int` — bool step_index (True) → type is bool → raises. OK.

Now let me check item 2/3: the placement of continuation_active and the import of solve_semismooth_increment in static_path.

## Preserved reviewer reasoning reasoning-a1c9909b-83c9-54f4-8c3a-c36ea81d9ae8-0

The restart validation is placed correctly: history validated (including continuation blocks) when continuation settings are on, before any Newton work. `continuation_active` at line 973 is after the restart restore. The import at line 105 confirms the monkeypatch target.

One more check on the eligibility block placement — line 973 onward. Let me view 960-1010 to see the eligibility checks and the state storage decision in the current file (I saw it in the diff, but let me confirm the final shape).

## Preserved reviewer reasoning reasoning-5e24c4ff-a427-58d7-8015-405197ab7ea1-0

The eligibility block is placed after state preparation and before activation. One observation: the eligibility check `type(committed_states) is not dict` runs on the prepared states. On restart, `committed_states = validated.element_states` — a plain dict presumably. OK.

Note: the eligibility check happens AFTER `_prepare_qualified_q4_states_for_nonlinear_solve` — which may itself create stores? The check `isinstance(committed_states, NonlinearStateStore)` catches that. And the plain-dict requirement. OK.

Now, one more thing to verify for question 2 — "correct physical committed origin". In the continuation, the substep attempts solve from `boundary` states, which after the first accepted substep is the substep's committed state. The macro rollback restores `macro_origin_states` (deepcopy at step start). One subtle thing: `macro_origin_states = copy.deepcopy(dict(committed_states))` — taken at step start. But `committed_states` at that point is the state after the previous step. If the previous step's states share mutable objects with... the deepcopy isolates. Good.

But — hmm, one potential issue: `macro_origin_states` is deep-copied ONCE per step (inside the step loop, before the macro attempt). The rollback restores `committed_states = macro_origin_states`. But if the rollback happens and then... the step breaks (failure) — no further use. If the rollback happens at the macro-refusal (before continuation), committed_states = macro_origin_states is then used as the origin for ALL substeps. Substep commits swap committed_states to new objects (plain dict commit = candidate_states). So macro_origin_states is never mutated (unless candidate states share mutable internals with the origin — for elastic states, the candidate states come from _assemble_nonlinear_system trials; whether these share mutable element state objects with the origin depends on the element implementation. The deepcopy at macro start protects the rollback snapshot ONLY if the origin's objects aren't mutated in place by assembly. If assembly mutates element state objects in place, the deepcopy protects macro_origin_states (it's a copy), but the boundary states passed as origins could be mutated... The old code had the same exposure for its single-step transaction (deepcopy at entry for history_friction only). Hmm — actually for the non-friction route, the OLD code did NOT deepcopy; it used _activate_nonlinear_state_storage (store-backed transactional). The continuation route replaces the store with plain dicts + deepcopy at macro start. The in-place mutation question: for the "frictionless elastic route" (no history materials — elastic), the element states are presumably immutable elastic mappings (that's why the plain mapping is safe for history_friction's "owned scalar candidate mappings"). The eligibility check restricts to this route. I'll note it as an assumption: elastic candidate states are not mutated in place by assembly; the fixture tests (rollback tests comparing exact reruns) give empirical support.

Now — remaining checks before the report:

A. The `_point_gap_budget_admissible` witness call: `overlap_violating_point_witness(first, first, second, second, gap_tolerance=self.gap_tolerance)[0]` — no endpoint_errors. The static pose positions are exact candidate endpoint positions — no error boxes at this gate. Consistent with the surrounding calls (q4_source_projected_gap_lower(first, second) — no errors). OK.

B. Question 3 mentions "chronology bounds and trace semantics. Check that reader accepts only the traces the declared producer/control contract can generate." I identified: the reader accepts spans that are any positive multiple of 2^-(H+1) (e.g., 3*2^-(H+1)), while the producer only generates spans that are exactly 0.5*2^-k (powers of two times 0.5) — plus the final stretched span (1-tau) which can be any multiple. Hmm wait — the final stretched span IS an arbitrary multiple of the granularity. So mid-trace spans of 3*2^-(H+1) cannot be produced (only the last substep can be a non-power-of-two span). The reader can't distinguish "last substep" stretches from mid-trace forgeries... actually it can: the reader could check that every substep except possibly the last has span equal to 0.5*2^-k. It doesn't. So the reader accepts traces the producer cannot generate (mid-trace non-dyadic-power spans, negative iterations, non-finite residual norms, halvings_used/trial_count inconsistencies). These are diagnostic/accounting fields; the physical restart state comes from the checkpoint's element states and coordinates, not the trace. So the gap is a validation-completeness issue, not a physics-admission issue. Worth stating.

C. Also for question 3: "default compatibility" — the OFF contract omits the four fields, preserving prior serialized shapes byte-for-byte. Verified in core._contact_settings_contract and request_identity. But one more: `ContactSolverSettings` is a dataclass with new fields with defaults — old serialized settings (e.g., from checkpoints storing asdict(settings)) would deserialize... the contract check compares dicts; an OLD checkpoint's contract lacks the four keys; a NEW run with defaults also omits them → compatible. Good.

D. One more potential compatibility hazard: `_contact_settings_contract` pops the four keys only when halvings == 0. If a user sets halvings=0 but non-default stagnation — validation raises (stagnation controls require halvings > 0). So the pop is safe.

E. Now — the witness docstring inaccuracy I found: "every enclosure is deliberately widened by one ULP outward, including the dyadic defaults, so no interval is claimed exact-width" — but `uu,vv = _interval(u), _interval(v)` and `tt = _interval(t)` are exact-width (not widened). mu/mv/mt are widened. The weights involving uu/vv directly (w1, w2, w3) have one exact-width factor. The final gap enclosure still encloses the true value (exact float values are valid enclosures of themselves; _mul/_add widen). So soundness is unaffected; the docstring claim is inaccurate. Minor.

F. Dead code: `target_norm` computed and validated but never used in the witness. Minor.

G. The witness's `checked` counter counts every (param, time) sample attempted including skipped charts — "samples_checked". Fine.

H. One more possible issue with the witness: `if squared[0]<=0.:continue` — squared is the target normal squared norm interval; requires the LOWER bound > 0. If the target triangle is degenerate at the sample (enclosure), skip. Conservative. OK.

I. `_divide_positive` docstring: "The caller must supply denominator[0] > 0." Both call sites check (projected[0] > 0, squared[0] > 0, actual_norm > 0). OK.

J. Now — one more scrutiny of the FIRST witness call site's soundness requirement. `_point_gap_budget_admissible` is a "Threshold-only D1 point certificate". The witness fires → return False. The claim: "every valid lower bound of this pose already refuses the budget". The final gate would compute `matching` and refuse iff max(lower, matching) < -tol. lower is already < -tol at that point (checked). So the old code would refuse iff matching < -tol OR isnan(matching). The witness proves matching < -tol (if matching is a valid lower bound). So the witness's refusal matches. BUT — what if matching is NOT a valid lower bound of min g? E.g., matching's chart admissibility fails → returns -inf → refuse (consistent). What if matching returns a value >= -tol due to being an INVALID bound (bug in matching)? Then the witness changes the decision. But that's a pre-existing certificate bug scenario, out of scope.

Hmm — wait, actually there's one more subtle case: matching_projection_swept_lower with `overlap_dual=True` (opt-in dev) — the dual tightens the numerator. The docstring says the dual "can only tighten this certificate" — i.e., the dual result is still a valid lower bound? The dual uses LP-style weight vectors to maximize the numerator lower bound — a valid lower bound of the true min numerator. So matching with dual is still <= min g. The witness proves min g < -tol → matching (with or without dual) < -tol. Consistent.

K. Now — the second call site: the witness fires → skip matching → overlap_local_swept_lower decides. The old code: matching decides first (if >= -tol → True). The witness proves matching < -tol, so old code would also fall to overlap_local. Behavior-preserving. BUT — one more consideration: `matching_lower` could be NaN → `matching_lower >= -tol` False → fall through. Same. OK.

L. Now — the semismooth stagnation: one more check that `merit` is defined before the stagnation block and is the pre-iteration merit. From the loop: `merit` is computed at the top of each iteration (the current point's merit). The acceptance condition `new_merit < merit*(1.0-1.0e-4*fraction)` — merit is the pre-iteration value. relative = (merit - accepted_merit)/merit. Yes.

M. One more: the stagnation bail returns `SemismoothStep(False, ...)` with `contact=None` (arg 7 is None) — the caller attempt_semismooth on `not step_result.completed` returns refused without touching step_result.contact. OK.

N. `stagnation_trace` grows unboundedly (one entry per improved iteration) — memory only, bounded by max_iterations. Fine.

O. Now — one more design-level check for question 2: "complete macro rollback on refusal/cancellation/exception, no partial publication/checkpoint". Verified: exception → restore + re-raise; cancellation → same (cancellation_safe_point raises SolveCancelled, a BaseException) → restore + re-raise; exhausted → restore + failure status; the record/history/checkpoint only after full acceptance. The one gap: `info["contact_failure"]` on exhausted includes cutback_reason/halvings/trials/accepted_substeps — diagnostic only.

P. One more: on the macro-attempt refusal path with continuation active, the code restores q/multipliers/normal_forces/normal_multipliers/committed_states — but does NOT restore... `manager.last_finite_deformation_maxima`? Only for finite profiles; continuation requires specific profiles? The eligibility doesn't check `finite`. Hmm — `finite` is for finite-rotation profiles. The continuation settings require the D1 route (d1_interior_profile, overlap_local_dev, jet2_q4_s3_dev, fine_nodal_q1, monolithic_active_set, primal_mortar, reference_linear, legacy). Can `finite` be true simultaneously? finite is set by profile selection... The D1 interior press fixture is not finite. If a finite profile also satisfied those settings, the continuation would run with finite seeds — the finite seed logic (q=seed) runs BEFORE the semismooth attempt... wait, look at the step loop: for finite, `q = seed` — the macro attempt then starts from q=seed, not start_q! And the rollback restores `q = start_q`. Hmm — in the old code, the same: on failure `q = start_q` (discarding the seed). And the continuation's boundary starts from `start_q` — NOT the seed! So under continuation with finite, the substeps would start from start_q while the macro attempt started from the seed. Is that a bug? The old code's failure path also restored q = start_q. The continuation's boundary["q"] = start_q — the macro ORIGIN is start_q (the accepted previous step), which is the physically committed origin. The seed is just a predictor starting guess. Starting substeps from start_q instead of the seed is fine (just a different initial guess — the solve converges to the same solution or fails). Not a soundness issue. And can finite + continuation coexist? The settings gate requires the D1 route; finite profiles are a different family. Probably mutually exclusive in practice. Not worth flagging beyond a note.

Q. `path_predictor` incompatible with continuation (validated). The finite seed is a different mechanism (finite_frame_seed) — not blocked. Minor note.

R. Now — one more check on `_validate_continuation_history_record`: it's only called when `settings.path_continuation_maximum_halvings` is truthy. On restart with continuation ON, EVERY history record is validated — including records from steps that had no cutback (no continuation block → continuation None → return). Good.

S. `record.get("step_index")` — the history record has "step_index". OK.

T. One more: the validator's `target` check uses `program.controls` length: `target.shape != (len(program.controls),)`. If program has no controls (force-only path), target is empty array — shape (0,)? `record.get("target")` = [] → np.asarray([]) shape (0,) == (0,) if len(controls)==0. np.all(np.isfinite([])) → True. np.allclose([], program.target_at(step), ...) → True. OK.

U. Now — the driver test's `_force_first_macro_refusal` monkeypatches `static_path.solve_semismooth_increment` — the closure calls the module-global name, so the patch intercepts. But note: the fake refusal returns a SimpleNamespace WITHOUT `contact`, `q`, etc. — attempt_semismooth's refusal path only accesses reason/diagnostics/iterations/candidate_evaluations/backtracks. OK.

V. One more accounting check: `summed_candidate_evaluations += sub_attempt["candidate_evaluations"]` — the refused macro attempt's candidate_evaluations (2) are included in `summed_candidate_evaluations` (initialized from attempt). The record's candidate_evaluations = summed. Includes refused work. Labeled as total work. Fine.

W. `record["semismooth_iterations"] = summed_iterations` — includes the refused macro attempt (3) + substeps. The test asserts this. OK — "numerical work accounting/labels" honest.

X. Now — the one remaining question: **`previous_steps` NonlinearStaticStep iterations = summed_iterations** — the restart `_static_step_from_restart(item)` reads iterations from the checkpoint steps. Fine.

Y. Let me also double check the first call site's witness: it's inside `_point_gap_budget_admissible`, which is called... where? For candidate endpoint admission during Newton iterations (evaluate at candidate points). The witness adds 27 sample evaluations per refusing pair — cost. The brief mentions timeouts (180s, 45s). The witness is cheap (27 samples of interval arithmetic) vs the 1024-node adaptive search. Should be a speedup when it fires. But when it does NOT fire, it's added cost before the matching search (27 interval samples). Bounded. Fine.

Z. One more potential issue at the first call site: the witness is called AFTER `lower = max(lower, local)` refuses, i.e., only for pairs already refusing cheaply. Good placement.

Now — let me also spot-check `_q4_s3_swept_chart_and_lower` and `overlap_local_sweptpt_lower` usage at the second site is unchanged (pre-existing). Yes, only the witness condition was inserted.

One more thing to check: question 1 says "witness may refuse but never admit". At the first site, witness found → return False (refuse). At the second site, witness found → skip matching → overlap_local decides (could admit!). Hmm — "never admit" means the witness itself never causes admission. At the second site, when the witness fires, the code falls to overlap_local which may return True → the pair is admitted DESPITE the witness proving min matching-gap < -tol. Is that a soundness hazard? This is the pre-existing structure: the old code also fell to overlap_local when matching refused. The pair admission is then based on the overlap-local certificate (a different gap formulation — the old overlap-local projection). So the acceptance gate is "whole_lower OR (matching if run) OR overlap_local" — a disjunction of sufficient conditions. The witness only removes the matching term when it's provably refusing. So admission via overlap_local with witness fired = same as old code with matching refusing. Consistent. The deeper question (whether overlap_local admitting while the matching gap violates is physically sound) is pre-existing formulation scope, not this diff.

Hmm — wait, actually let me reconsider: is it really true that the old code would always fall through when the witness fires? Old code: `if d1_interior_profile: matching_lower = matching_projection_swept_lower(...); if matching_lower >= -tol: return True`. If matching_lower is a valid lower bound and the witness proves min g < -tol, then matching_lower <= min g < -tol → matching_lower < -tol → `matching_lower >= -tol` False → fall through. YES — provided matching is sound. So behavior-preserving given both sound. Good.

Also note: at the second site the witness runs only when `whole_lower < -tol` (else already returned True). Good.

Now — the last remaining item: check `q4_overlap_local_bound.py`'s `_overlap_dual_joint_weight_lower` docstring change (the first hunk) — it clarifies zero-weight handling. Not a behavior change (docstring only). Fine.

Let me also quickly grep for any other new callers/tests referencing `path_continuation` outside the six files + tests, to make sure the wiring is complete (e.g., docs, scripts). And check that `verify_general_contact_request` handles the new revision key (request_identity diff showed the key added to the request dict; verify presumably hashes the request). The test covers it.

One more potential hazard: `identify_general_contact_request` adds "contact_path_continuation_revision" only when enabled. Two different enabled settings (halvings 6 vs 4) — both include the revision key and the settings block includes path_continuation_maximum_halvings → different identities. The test verifies mismatch detection. Good.

I think I've covered the scope. Let me also verify there are no other modified regions in the six files I haven't seen: the q4 diff had 3 hunks (docstring, _divide_positive+witness, and... the first hunk was the _overlap_dual_joint_weight_lower docstring). s3_patch_static: 2 hunks. static_path: I saw hunks at 404 (validator), 711 (contract), 844/909 (restart validation + eligibility), 1014 (attempt closure), the loop, record, and the tail. Let me confirm the diff is fully seen: 586 changed lines; I viewed the diff in 3 chunks (head -400, sed 400-800, sed 640-800). The sed '400,800p' output started mid-context and ended at the record hunk; sed '640,800p' showed the tail. Combined coverage: lines 1-800 of the diff, and the diff total... let me check the diff line count to be sure I've seen it all.

## Preserved reviewer reasoning reasoning-c7c56ca1-2591-59e7-86b7-a8b1c4302ec7-0

The static_path diff is 681 lines total; I viewed lines 1-400 (head -400), 400-800 (sed 400,800 — which covers to the end since total is 681), and 640-800 (tail overlap). So full coverage. semismooth diff 128 lines — fully seen. Continuation references confined to the three files. Good.

One last item: verify `_static_step_from_restart` and the restart `history` handling don't choke on the continuation block (it deepcopies history; the block is just extra dict keys). And check `summarize_work_history` (history_friction only) — not applicable.

Also — one more check on the record: `record["continuation"]` is appended to history, and the checkpoint's `path_state["history"] = history`. On restart, `_validate_continuation_history_record` validates. But ALSO: `to_restart_checkpoint()` on the result — the driver test accesses `checkpoint["path_state"]["history"]`. Fine.

Now let me also double-check one potential real bug I want to confirm: in the continuation loop, when a substep is REFUSED and halvings remain, the code restores q/multipliers/normal_forces from boundary — but it does NOT restore `committed_states`... committed_states is unchanged (still boundary's). Correct.

But WAIT — there's one more subtle thing: on substep refusal, `_discard_nonlinear_state_candidate(committed_states)` is called. For plain dicts it's a no-op. But under continuation, could committed_states be a NonlinearStateStore? No — eligibility rejected that. OK.

And one more: the `except BaseException` handler in the continuation loop calls `_discard_nonlinear_state_candidate(committed_states)` — committed_states at that point is the last accepted substep's states (or macro origin). No-op for plain dicts. Then restores macro origin. OK.

One more potential issue: **the macro attempt exception handler** (before continuation): `_discard_nonlinear_state_candidate(committed_states)` — committed_states is the step's origin (pre-attempt). No-op. Restores. OK.

Now — one more thing to check: `attempt_semismooth`'s success path calls `_discard_nonlinear_state_candidate(accepted_states)` AFTER the recovery assembly. For plain dicts: no-op. For store-backed (non-continuation macro attempt): discards the trial's pending candidate after commit... wait, commit_state_candidate for a store returns `candidate_states.commit(...)` — a new store state; the discard on accepted_states discards any ACTIVE trial on the new state? Hmm — `discard_active_state_candidate(accepted_states)`: if accepted_states is a NonlinearStateStore with has_active_trial — after commit, is there still an active trial? This mirrors the OLD code exactly (the old code did `_discard_nonlinear_state_candidate(committed_states)` after the recovery assembly with committed_states being the post-commit states). Same semantics preserved. OK.

Now — assemble the final findings. Let me also double check the one thing about `_validate_continuation_history_record`'s span check with maximum_halvings from settings vs the record's own "maximum_halvings" field — the producer writes `"maximum_halvings": settings.path_continuation_maximum_halvings` into the block, but the validator ignores it and uses current settings. Since the contract binds settings, a mismatch fails at contract validation first. But the ORDER: which runs first — contract validation or history validation? The restart flow: validate_nonlinear_checkpoint (contract) → then history validation. Contract mismatch raises first. So by the time history validation runs, settings match. The record's maximum_halvings field is then redundant. OK — but a tampered record could have maximum_halvings=99 inside the block while spans are consistent with current settings=6 — accepted. Diagnostic-only inconsistency. Minor missing check.

Also the validator does not check `cutback_reason` is a string/one of the producer's reasons, `halvings_used <= maximum_halvings`, `trial_count >= accepted_substep_count`, `iterations >= 0`, `residual_norm` finite. All producer-unreachable forgeries accepted. Accounting-level only.

One more genuine question about the chronology validator: `scaled = span * float(1 << (int(maximum_halvings) + 1))`. For maximum_halvings=12: 1<<13 = 8192. A span of 2^-13 → scaled=1. OK. But the producer with H=6 (test) uses granularity 2^-7; the validator with settings H=6 checks span*128 integer. The test tamper sets tau_end=0.3: span=0.3, 0.3*128=38.4 → not integer → raises. Good.

Now — one more scrutiny on a potential REAL issue in the continuation: **`tau_trial = 1.0 if tau + span >= 1.0 else tau + span`** — the final substep's target is exactly the macro target. But the final substep's `sub_force_values = (1-1)*prev + 1*force = force` exactly. Good.

**A subtle issue with `span` growth after the final stretch**: not applicable.

**Another subtle issue**: after a successful substep, `span = min(2.0*span, 0.5)`. Suppose the first substep at span 0.5 succeeds → tau=0.5, span=0.5. Next: tau+span=1.0 → tau_trial=1.0, a half-step. So the default continuation after one cutback tries [0,0.5] then [0.5,1]. If [0,0.5] fails → span 0.25 → [0,0.25] etc. Reasonable dyadic bisection.

**Trial limit vs halvings**: fine as analyzed.

**One more potential issue**: `halvings = 1` initial — with maximum_halvings=1, the FIRST substep failure exhausts. But note the macro attempt itself already failed once — is the macro attempt counted as a halving? The record's "halvings_used" starts at 1. Semantics: the cutback from macro to span-0.5 is halving #1. Consistent.

Now — **the biggest remaining soundness question for the whole continuation feature**: the substeps' acceptance uses the SAME gates as a macro step, but the substep targets are NOT program waypoints. The D1 admission gate `d1_interior_admission_issue(certificate, accepted_u, T, control_rows=rows)` — does it check the target/waypoint? It checks the certificate and displacement. The control constraint is enforced by solve_semismooth_increment against sub_target. So intermediate substeps satisfy equilibrium + contact + control constraint at intermediate targets. Physically consistent.

**The `record["target"]`** is the macro target; the continuation block documents the substep path. The validator checks record target vs program waypoint. Good.

**Work accounting**: `substep_work` trapezoid uses force interpolation — genuine. Labeled "not_exact_path_integral". Good.

Now — one more check on question 5 (test discrimination): the driver tests monkeypatch solve_semismooth_increment to force refusal — this bypasses the real stagnation mechanics (the fake refusal claims reason "contact_semismooth_stagnation" without running the real bail). So the REAL stagnation bail path (merit/fraction accumulation in solve_increment) is NOT exercised by any test — only its validation (patience=0 raises). Let me verify: is there any test that exercises the real stagnation bail? The witness_public tests don't. The driver tests fake the refusal. test_stagnation_controls_are_validated_before_any_work only checks validation. So: **the real stagnation bail logic (stagnation_run accumulation, the bail return) has no test coverage** — the cutback tests inject the refusal synthetically. That's a genuine missing check to report: no test drives solve_increment to a genuine stagnation bail on a real problem (would need a problem that stagnates). Also the real `contact_semismooth_stagnation` reason string from the bail is only produced by the untested code path.

Also — the semismooth stagnation code: is `stagnation_enabled` possible in production ONLY via continuation? `stagnation_controls` is not None only when continuation_active. And solve_increment's kwargs default None. Other callers of solve_increment? Let me check if solve_increment is called elsewhere (semismooth.py? other paths?). If another caller passes stagnation controls... grep.

## Preserved reviewer reasoning reasoning-763f042a-b9e4-5d50-8978-1152fc29925b-0

There's a sixth test file I missed: `tests/test_general_contact_admission_globalization_stagnation_check.py` — it didn't show in git status as untracked? Wait, git status showed only 5 test files as untracked (??). Let me check — maybe it was created after my initial listing, or I missed it. Let me read it and re-check git status for it.

## Required closure

Read this preserved context, then issue the final actionable findings report in your next response after at most four confirming read-only source calls. The prior context covered all six product diffs and test modules. If no defect found, state that scope and the six missing real driver checks, not engineering acceptance. Scrutinize restart trace bounds if not already resolved. Do not re-open unrelated investigations or numerical execution. No edits. MaxTurns12.