# Nonlinear convergence and speed abuse sweep, 2026-10-22 (session B)

Branch `claude/solver-convergence-speed-20261022` on 82d4a0ca7. Not merged, not pushed.
Harness: small plates (2x2..8x8), cantilever beams, shallow curved panels; each case one process, one thread.

## Delivered (local commits)
1. `_compensated_contractions.py` vectorised, bitwise identical to the scalar policy
   (240k randomized differential cases by the reviewer, 0 value differences; exception type
   matches after the weighted_sum replay fix). 8x8 corotational thin plate 24.7 -> 6.5 s;
   arc-length curved 4x4, 8 steps 41.5 -> 10.1 s. Batching Gauss points and memoising
   products measured no gain (dropped). Further gain needs a native backend (module contract forbids).
   OPEN: source-binding sha for this file in docs/reference_cases/e4_pl_q4_source_binding_*.json needs a successor record.
2. Default `NonlinearConvergenceSettings.line_search` "auto" -> "rescue". Eager residual-decrease
   line search crawls on non-monotone-convergent Newton (von_karman cantilever, 5 steps: 14138 -> 12
   iterations, 47521 -> 12 in another case). Shell plates elastic: identical. Plastic plates: same stops,
   some stop at different load factors. OWNER DECISION before merge. Side effect: restart contracts and
   fingerprints embed `line_search`; contracts written with default settings by older code no longer match (fail closed).
3. NaN/inf refusal at construction for RigidSphereImpact and all float fields of SphereContactConfig.

## Open findings (not fixed)
- Plastic clamped plate (4x4, t=3 mm, 50 kPa, von_karman): stops at load factor 0.2 with 5 steps, 0.5 / 0.67 /
  0.455 / 0.49 with 2 / 3 / 50 / 100 steps, completes with 1 or 20; no profile/line search fixes it. Newton
  6-cycles even for a 0.0002 increment from the committed state. Tangent matches finite differences in the loading
  regime (1e-10) and is kinked at the exact yield state. 1-step answer (umax 0.131) differs from 20-step (0.190):
  large-increment return-mapping error. Needs investigation in the governed plasticity path.
- Corotational 1-step thin plate (t=1 mm, 50 kPa): converged rotation DOFs carry 2*pi*k offsets
  (same rotation matrix); translations identical. Output normalisation candidate.
- Corotational/qualified shell evaluation cost is dominated by the pure-Python-contract contractions (~19 ms/element evaluation).
- Hard impact line search (contact.py) still caps corrections rather than a coupled merit search (prior note).

## Overnight outcome (2026-10-22/23)
- Items 1-3 above (native contractions, line_search default `rescue`, NaN/inf refusal) are on local main (b7494ed66).
- Plastic-plate stall: ROOT CAUSE FOUND. The default Q4 shell added an indefinite constant elastic correction
  `Cr = K_hybrid - K_legacy` that stayed elastic under plastic flow, so the element stiffness went negative and the
  converged states on main were spurious in-plane plastic mechanisms (1-step 0.131 / 2-step 0.382 / 20-step 0.190 were
  all wrong). Fix (branch claude/plastic-stall-20261022, NOT merged: last Codex round still OPEN, see
  docs/OVERNIGHT_20261022_STATUS.md on that branch): apply Cr to the elastic displacement part only,
  `F_c = Cr(u - u_p)`, exact nonsymmetric tangent; all step counts 1..100 complete, centre deflection 0.04358 -> 0.04310 m
  (1.1 % spread, 0.25 % for >= 2 steps). Cost: plastic state identity (old plastic states refused), general matrix class,
  flagged symmetrised views for buckling/modal. Eight Codex rounds each found one more route by which a legacy plastic
  state could enter a solve; stopped at the retry limit.
- Corotational speed (claude/t34-merge-20261022): authority-guard overhead, not arithmetic, dominates. Exact-type
  float/ndarray recheck skips and a pre-screen hoist are bit-identical; a plain-attribute fast path was REMOVED after
  Codex found 4 P1 integrity holes. Fused Numba shell kernel (bitwise identical, FMA/pow-guarded self-check):
  corot 8x8 14.3 -> 10.4 s, arc-length panel 2.64 -> 2.26 s.
- 2*pi rotation offsets: reproduced (simply supported 4x4, t = 1 mm, 1 step); NOT normalised: DOFs are updated
  additively, so wrapping changes later increments (5e-2 for a 0.05 step), restarts and post-processing. Compare with
  `rotation_matrix_from_vector`.
- Remaining cost is the authority guards (21-60 % of every case; e4_pl_s3_state.signature, formulation_class_guard,
  lifecycle API checks): algorithmic memoisation inside authority code, owner decision.
