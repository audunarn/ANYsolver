# GE-B3 native Schur controller transaction parity

Parent `fc2590b91b3226fbf6fb467833a5ffef6fb0ddf1`, tree
`f0f3fe9e0cc54e5782fea5e5fadf0cd514b7341e`. Previous gate proved local
resultant elimination against the complete Newton matrix without changing any
mechanical operator. This successor selects it in a new private controller.

Inherit the exact conservative line work, spatial residual Jacobian, accepted
state owner, recovery and checkpoint replay. Preserve the dense controller and
its historical evidence. Bind the Schur policy, factor-reuse rule and full
increment recovery in a new program identity and genesis; reject cross-program
restart in both directions. Do not relabel or translate an old checkpoint.

For each Newton iteration, factor the complete spatial Jacobian with local
resultant elimination. Reuse that factor for the Newton increment and the
natural-correction line-search merit. Recover all internal increments, retain
the existing chart fraction and backtracking rules, and commit only after the
unchanged 1e-11 equilibrium/compatibility checks and native state replay pass.
Failure or cancellation returns only the last accepted checkpoint.

New development cases (not reruns of historical paths), all one macrocell and
the unchanged full coupled physical-fibre section:

- Straight elastic: line force (.12,-.04,.02), targets (.2,.6,1.,.35,0.).
- Curved elastic: line force (.11,-.035,.025), the same targets and the existing
  height .0625 on the unit-length test fixture.
- Straight plastic load/unload/reversal: line force (.82,.025,-.015), targets
  (.2,.55,1.,.4,0.,-.4,0.), existing yield .25 and hardening 2.

Compare dense and Schur state, origins, histories, reactions and physical
recovery at normalized 1e-11. Compare each backend's own complete versus
paused/resumed checkpoints byte-for-byte, not cross-backend hash identities.
Exercise cancellation before trial, after factorization and before commit;
injected factor failure, exhausted iterations and changed program authority.
No trial history may escape. No spectrum, historical load path or public
workflow is run by this gate.

After rehearsal, freeze source and run two fresh test cycles, each bounded by
one numerical thread, 24 GiB, 600 seconds wall and 120 seconds activity. Existing
120-second native controller/context limits and 60-second local linear-solver
limits remain. Preserve raw records and failure logs; no automatic retries.
Require identical canonical scientific packets between cycles. Record timing
as diagnostics only. Independent review and production qualification remain
pending. Dense assembly, broad scalability, general section parity and the
objective beam-shell connection are not closed by this controller change.

Unfrozen rehearsal incident: one test passed and ten fixture errors occurred.
All three dense paths completed, but the initial unrefined Schur controller
accepted zero targets. Local back-substitution left approximately 1e-19 to
4e-18 spurious force in exactly unloaded rows: componentwise backward error
was 1 despite excellent normwise step agreement. Preserve these failures.

The correction is a separate refined linear-solver successor; the frozen
unrefined solver remains unchanged. Permit at most three iterative-refinement
actions on the complete linear-system defect, reusing the same factor. No
new element evaluation, factor retry, zero clipping, absolute tolerance floor,
state advance or convergence relaxation is permitted. The original 1e-11
componentwise condition must pass before the controller can use an increment.
The refined policy is bound into the new controller identity. Regression
tests must reproduce the initial defect and show refinement removes it.

The bounded V2 refinement rehearsal also failed: two passed, three failed and
ten fixture errors, with zero Schur targets accepted. Repeated reduction of an
exactly homogeneous row's absolute defect does not guarantee its componentwise
relative condition. Do not increase iteration limits or weaken the condition.

V3 therefore binds an explicit full-mixed sparse-LU fallback to the SAME supplied
Jacobian when the three refinement actions cannot pass. Cache that full factor
for subsequent RHS in this Newton iteration, and apply the unchanged 1e-11
componentwise check to its answer too. Report the chosen route and both
factorizations. This supersedes the V2 no-additional-factor rule based on the
observed failure, not a performance target. No element/state recomputation or
process retry occurs within this linear fallback. A performance claim must
account for fallbacks; never claim every Newton solve is half-sized.

The four local V3 checks found that COLAMD-ordered full sparse LU also failed
the curved exactly-unloaded-row check (two passed, two failed). No full path
was launched after that local failure. V4 uses a cached full LAPACK partial-
pivot LU for the fallback, matching the existing dense solver's algebraic
method, still with the SAME componentwise check. The preserved bounded dense
matrix is already available; no geometry-dependent ordering or coefficient
tuning is introduced. Reduced sparse solves remain the first route. Keep all
V1/V2/V3 preparation evidence and report fallback use without a speed claim.
