# Event replay independent review

Mistral Read, six-turn bound, 2 October 2026. No reviewer edits or tests.
No scientific acceptance established.

Review complete. I read `s3_friction_replay.py` in full (focusing on `_step_events` 413-464, `_step_endpoint` 354-411, `_check_contact_intervals` 299-348, `_entry` 236-296, `restart_contract` 615-619, `restore` 630-659) and the named test. Three findings, each with a counterexample.

## Finding 1 — Event-mode replay of committed history uses live normal multipliers for midpoint pressures (history/work semantics)

- `src/anysolver/general_contact/s3_friction_replay.py:456` builds each stage frame via `self._frame(...)`, and `_frame` at line 191 computes pressure as `self.normal.law.evaluate(source,target,self.normal.normal_multipliers).pressure`. `normal_multipliers` is mutable solver state (`s3_patch_static.py:543`, `set_normal_multipliers` at 764-767; `equilibrated_pressure_pivot.py:38-138` mutates it during solves). Committed frames, by contrast, carry stored pressures (`checkpoint_state`, validated in `restore` at 647-650), and endpoint-mode replay uses only those.
- Consequence: replaying a **historical** segment in `query_material` (line 470-475) mixes immutable commit-time endpoint pressures with current-iterate midpoint pressures, so the dissipation attributed to already-committed segments — and hence the material history and current friction force — varies with the live multiplier estimate. This contradicts the module docstring ("immutable committed poses and pressures") and the `_step_events` docstring ("immutable pose segment"). It also reaches restart: `restore` recomputes the ledger per frame (line 651) with the restoring session's multipliers and requires 1e-10 agreement (line 655), so a checkpoint is only restorable if the normal state reproduces commit-time multipliers exactly.
- Counterexample: commit frame A at equilibrium with multipliers m*>0 (stored pressure p_A>0, sliding dissipation D enters `cumulative_dissipation`). Call `set_normal_multipliers(0)` (or run a pivot that lowers the estimate), then `query_material` on the same bary: the `[initial, A]` segment now has midpoint pressures ≈0 (Coulomb cap ≈0, no slip) but endpoint pressure p_A>0 — the same committed history replays to materially less dissipation than D, and `restore` of the just-produced checkpoint in that state fails the line-655 "work disagrees" check.

## Finding 2 — `event_stage_evaluations` is never reset by public `query_material` and is not rolled back on failure (stage budgeting)

- The cap check/increment sit on manager state at lines 450-452; the only resets are `__init__` (163) and `_integrate` (521). `query_material` (466-475) loops `_step` over every frame pair without resetting, and a `MemoryError` raised at line 451 leaves the counter elevated — `checkpoint_state()` does not include it, so the test's `checkpoint_state()==before` assertion cannot detect the leak.
- Consequence: repeated direct material queries — the documented way to inspect history, used throughout the tests — accumulate toward `maximum_event_stages` and eventually raise a spurious `MemoryError` on inputs that individually fit the budget; one failed call poisons all later calls.
- Counterexample: `event_subdivisions=16`, `maximum_event_stages=64`, one contact interval per frame pair. Each `query_material` over a 2-frame history performs ~2×17=34 stage evaluations (17 new fractions per pair; the per-call cache at line 426 does not survive the call). The second, identical call starts at 34, reaches 68>64, and raises "actual-pressure event stage cap exceeded" although each call alone needs only 34.

## Finding 3 — `_entry`'s boundary roundoff is scaled by batch-wide maxima, so entry classification is batch-dependent (query independence)

- Lines 267-268 compute `roundoff` using `np.max(np.linalg.norm(r,axis=1))` over **all** queries in the call; lines 269-273 snap `h0`/`h1` with it, which gates `entering` (277) and the root selection (281-291) that sets the first-touch anchor fraction. In event mode the batch passed to `_step_endpoint` is the fraction-group (`bary[indices]`, line 458), whose membership is decided by *other* queries' interval structure (line 443) — so a point's entry alpha and anchor depend on which unrelated queries happen to share its fraction tuple. This directly contradicts the docstring at 416-417 ("never on the other queries in a quadrature batch"), and the test's independence check (`single=owner._step(0,bary[:1],...)` with `assert_array_equal`) only exercises point *removal*, never addition of a far-away co-query.
- Counterexample: point P with boundary-edge coefficient h0=-1e-9, beta=+1e-3 (crosses just inside at t≈1e-6), |r_P|~1. Alone: roundoff ≈128·eps·|edge|·1 ≈ 3e-14, no snap, `entering` via h0<0, anchor at root 1e-6. Batch P with query Q at |r_Q|~1e6 sharing its fraction tuple: roundoff inflates to ~3e-8, `on_start` snaps h0 to 0, and since coefficients[1]>0 the point is no longer classified as entering — its anchor moves to the segment start. The two runs disagree by ~1e-6 of the segment in anchor and dissipation, failing the exact-equality independence the code and test claim; in quadratic cases (lines 285-291) the unsnapped chosen root can also fall outside [0,1] and flip clean acceptance into "replay entry root lacks a closing bracket".

## Review limits

Read-only inspection only; I ran no tests or code, so the counterexamples are analytical, not executed. I did not fully verify whether the normal restart path (`normal.restart_contract()`, `s3_patch_static.py:747`) restores multipliers bit-exactly — if it does, Finding 1's restart consequence narrows to the live-solve anachronism. I also did not audit `_split`/`_quadrature` partitioning or the coupled solver beyond what the named functions and test exercise.

## Lead disposition

1. Multiplier concern is outside the admitted profile: the template rejects augmented owners; penalty set_normal_multipliers rejects updates. Added an executable guard check. Do not generalize this dismissal to future augmented friction.
2. Valid. Public query_material now starts a fresh disposable stage budget; internal integration uses _query_material to share the enclosing candidate budget. Repeated-query check passes.
3. Valid. Boundary roundoff now uses each point's own distance. Addition of a far co-query leaves the near-edge event fraction exactly unchanged.

Focused fix evidence: contact-friction-replay-event-review-fixes-20261002.log, 2 passed in5.39s. Complete event-integrated coupled workflow timed out at the unchanged180s execution cap; resource.json reports190.079s including teardown and188133376B sampled peak. No coupled success or speedup claimed.
