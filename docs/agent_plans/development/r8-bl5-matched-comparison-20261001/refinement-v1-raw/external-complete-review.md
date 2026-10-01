# Independent completed external P0 family review

2026-10-01. Read-only source/JSON/hash review of `TEMP/r8-bl5-external-p0-family-v1`; no product/reference imports, solves, additional grids or source/evidence changes. This note is the only write. No consequential source, provenance or interpretation defect found within the declared development slice. Completion supplies matched external growing-space data, not qualification or a demonstrated 1% limit.

## Exact inventory and reuse

The frozen family source SHA256 is `0e5435e0d38952642662eb1aad7dd374c341c866c9d099c87d2e66ce135a21c0` (independently checked against the saved source). Helpers are P0 `180e2c33d1df17239fbf30f66d9c6b400eebbfa9e5f961d83e7c9b68bdc5fdac`, strong reference `6e1b3f25c2b479e1ade3700b57d996cef2f9709812a72108ce7e6a41e346293a`, recorder/recovery `506c5259afddfab1872c50c2a2544a7cb706b4cf14e6e7c6b4771d80a0ff98cc`, original reference `5d3616e5fc6f198adc8c0442e01c27c5b7b719e73059f5088561d0027e826f47`. The new scientific solves record Python 3.12.14/OpenSees 3.8.0 and binary SHA256 `25ba42e1672526137d765d9c3631d1403e091f54f5afcdb9242f9243c63c3a96`.

`execution.json` is terminal `COMPLETED_DEVELOPMENT_ONLY`: nine commands, nine passed/exit zero, exactly eight fresh external solves and one reuse (`n16/mz`). Reuse is not a ninth scientific solve. Its five original controls/inputs/raw/recovered/summary hashes independently match the retained completed P0 case. Explicit node **and element** remaps preserve connectivity, poses, global covectors, equations, fixes, loads and model commands; all nine first-level equivalence predicates are true. Old raw values are reprocessed through the family recovery. No unchanged first-level Mz authority is replayed.

| nx / ny / beam intervals | Physical nodes / poses | Elements / global covectors | P0 supports / rows |
|---|---:|---:|---:|
| 16 / 4 / 32 | 118 / 118 | 96 / 96 | 8 / 40 |
| 32 / 8 / 64 | 362 / 362 | 320 / 320 | 16 / 80 |
| 64 / 16 / 128 | 1234 / 1234 | 1152 / 1152 | 32 / 160 |

All declared/raw inventory predicates pass in all nine cases. Full physical node order, poses, nodal commands, element commands/connectivity, element global covectors, constraints and explicit model/analysis commands are retained. Namespace ranges remain disjoint; tags are not used as an interchangeable cross-domain physical identity.

## Physical alignment and work provenance

Independent JSON coordinate reconstruction found zero mismatches in all nine cases: shell occupies `[0,1] x [0,.2]` m at z=0; beam occupies x=[0,1], y=0, z=.0675 m. Section/transform command values are identical across levels/cases: E=210 GPa, nu=.3, G=80.76923076923077 GPa; shell thickness .035 m; beam A=.01 m2, J=1.6666666666666667e-5 m4, both I=8.333333333333334e-6 m4 and shear areas .008 m2. Global-z transformation declaration, shell-top arm +.0175 m and beam-bottom arm −.05 m remain fixed. The shell x=0 column is fully fixed; beam root coordinates 1..5 are directly grounded and normal spin is free. Fy=100 N, Mx=10 Nm or Mz=10 Nm is applied at the same physical beam tip, with moments and transfer wrenches about the beam-root origin.

One growing P0 support spans four beam intervals/two shell intervals. Exact union-piece P1/Q1 shape integrals yield five work rows (three surface translations plus rx/ry directors); all positive shape-integral and width-sum controls pass. Normal-spin columns are absent. The external beam rotation trace is continuous nodal P1; it does **not** establish equality to native retained-cell rotations, nor remove shell/beam discretization differences.

Recovery does not use raw nodeReaction as an interface/ground oracle. Each support has a free interior recovery node, independently checked isolated 5x5 block with positive integral weight; density solves `C_b^T lambda = L-G`. The full assembled row pullback is then checked on every free coordinate, including rz and coordinates outside the recovery selection. Resisting load is `+C^T lambda`; exerted connection load is its negative. Ground is `(G+C^T lambda-L)` only on prescribed coordinates. Thus root element G and first-support root interface load remain distinct from actual ground; complete-domain cuts and their common-origin wrenches are retained.

Independent force/arm/director formulas match the exerted pullback. Both compatible and noncompatible virtual work identities are checked. Reported applied work is **L dot q**, in joules, not one-half elastic strain energy. Integrated position/director rows have units m2/m; multiplier densities N/m and Nm/m. Average gaps divide by actual support width, and force/moment checks use declared load magnitude with Lref=1 m. The 1e-12 J work floor, 1e-8 physical budgets, 1e-9 average-gap budget and separate 1e-6 derivative budget are unchanged.

All nine cases have all 14 passing physical checks (126 case-check instances). Worst physical error is `1.2223956846746374e-10` in n64Mz complete-domain cuts; its free-coordinate error is `2.5483348764510084e-11` and average gap `2.5013941723603557e-21`. These values must not be replaced by the former first-level 4.51e-12 bound. Three actual left-Exp derivative steps, six common rigid fields, reference/common finite pose and released-spin controls also pass at every level; worst derivative error is `5.454598155266096e-10`, separately normalized. They test the **virgin integrated trace derivative/objectivity**, not accepted nonlinear finite mechanics or chart/restart behavior.

## Convergence information and limits

| Case | L dot q at nx16, J | nx32, J | nx64, J | 16→32 | 32→64 |
|---|---:|---:|---:|---:|---:|
| Fy | .0004245743634895948 | .0004243221107215316 | .0004243818280950985 | −.0594131% | +.0140736% |
| Mx | .00006362381020081303 | .00006372935093888464 | .00006378061441660726 | +.1658825% | +.0804394% |
| Mz | .00001774153836642759 | .000016899890871449675 | .00001666831031253439 | −4.7439375% | −1.3703080% |

These are successive discrete changes, not errors against a known continuum limit. In particular, Mz fails even a last-step-under-1% reading, and small Fy/Mx work changes alone cannot prove converged transfer. Analytically integrated beam-exerted smooth-window Mz on fixed x=[.25,.75] m is Fy −.98084069/−.90857484/−.99022386 Nm, Mx −.34896055/−.32803811/−.32777146 Nm, and Mz 1.47173005/1.62353842/1.56482028 Nm. Fy/Mz are nonmonotone; root/interior partitions also evolve. No component-relative threshold is invented here. Total interface wrench balance is an equilibrium identity, not an independent transfer-convergence oracle.

The density measures are continuous P0 integrals: open/closed windows agree and endpoint atoms are exactly zero. Polynomial x moments and the declared unit-peak smooth polynomial are integrated on actual support intersections, retaining lever moments about the same origin. These measures are suitable for later matched common-quantity comparison; they cannot be confused with strong-station nodal atoms or unweighted nodal sums. No common field or native-family comparison is inferred from this external-only completion.

## Resource scope and disposition

The supervisor starts each child suspended, verifies single CPU affinity `[0]`, then resumes it; this closes the previous after-spawn affinity gap for these launches. Saved observations show sampled peak RSS at most 120016896 B, sampled total OS threads at most 8, and at most one start classified numerical-or-unresolved. The nine command elapsed times are .205–.877 s, including reuse bookkeeping. They are bounded launch/sampling observations. Environment requests are one thread, but effective OpenSees API configuration remains unverified. ntdll/COM start classifications do not prove what a thread did, sampling does not establish a lifetime bound, and PE import/literal absence does not exclude dynamically resolved worker/runtime behavior. No general effective-thread, lifetime resource, performance qualification or speed claim follows.

Defensible disposition: retain this complete matched external P0 family as development evidence and compare the separately frozen native growing-space family using the same physical supports/actions, fixed-distance smooth transfer and common-field/work measures. The combined outcome should identify whether common-limit/transfer agreement is demonstrated or which precise obstruction remains. Do not repair the five-channel law from the former strong/native 12.75% discrete discrepancy, select a multiplier space from these values, declare converged 1%, or automatically launch a fourth grid. Mandatory CalculiX/full convergence and formal F03 acceptance remain pending; this review consumes no formal authority.
