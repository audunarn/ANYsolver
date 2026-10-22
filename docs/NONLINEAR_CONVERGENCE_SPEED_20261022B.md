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
