All evidence is in hand. Final gate report follows.

---

# Rotating-offset compatibility gate — finish report (Read-only)

## Recommendation: UNRESOLVED — conditional PASS; STOP not supported by source evidence

The candidate conversion is mathematically correct as a coordinate transformation, and it does not change local element kinematics. What it does require — reading the wrapper's moment blocks as spatial torques — is only approximately established by the production route, at the same approximation order the production corotational formulation itself already carries. A Read-only gate cannot run the two numerical pairing checks the review requires, so final PASS cannot be issued here; nothing found supports STOP.

## Verified production facts (all confirmed by successful reads this session)

- nonlinear_static.py:1507-1518 dispatches to `corotational.corotational_element_response`; the direct beam helper is not the production route. Confirmed.
- Local deformation: `u_d[node,3:] = rotation_vector_from_matrix(R_rig.T @ R_node)` — i.e. θ_loc = Log(R_rig^T Exp(θ)) (corotational.py:283-285). Confirmed.
- Wrapper returns `E f_ref` with E block-diagonal, same `R_rig` on translation and moment 3-blocks (corotational.py:307-314, 380-382; corotational_performance.py:23-32, 94-105). Confirmed.
- Consistent tangent is the exact additive-coordinate Jacobian of that residual, deliberately nonsymmetric, with the D-matrix chain `Jr^{-1}(θ_loc) Jr(θ_i)` (corotational.py:583-644, esp. 610-617). Confirmed — this is derivative consistency, not a work-conjugacy or energy claim; the docstring says so explicitly.
- Current reduction is fixed affine: `residual = -T.T @ F_int` (nonlinear_static.py:3522), `K_red = T.T @ K_T @ T` (3537), `full_displacement = T @ q + ...` (6514-6519). Confirmed — the exact nonlinear reduction is genuinely new adapter work.
- `Jr` exists (corotational.py:491-505) and its series matches the standard right Jacobian. Confirmed.

## Pairing and tangent equations (source-backed)

With nodal rotation vector θ (R_node = Exp(θ)), local deformational rotation θ_loc, local moment m_loc:

1. Exact spatial torque: t = R_node Jr(θ_loc)^{-T} m_loc. The wrapper delivers R_rig m_loc. Discrepancy: t − R_rig m_loc = R_rig (skew(θ_loc)/2) m_loc + O(θ_loc²) — first order in deformational rotation, zero for pure rigid rotation. Translation blocks pair exactly under rotation.
2. Exact additive-coordinate covector: p = A(θ)^T t with A = blockdiag(I, R_node Jr(θ)) — the same Jr(θ) the consistent tangent already uses, so A is consistent with in-repo kinematics.
3. Reduction: r = J^T p, K = J^T Kp J + Σ_a p_a H(g_a), Kp = A^T Ks + (∂A^T/∂u)s, where Ks must be the consistent-mode tangent (corotational.py:583-644). The default "rotated" mode is not the derivative of the residual and would break exactness.

## Counterexample — independently re-derived and confirmed

θ = α e_z, r0 = a e_x, slave force f e_z: physical moment M = af(sin α, −cos α, 0); additive covector p = L^T M = af((1−cos α)/α, −sin α/α, 0). I re-derived both from scratch (including the Jr series with [θ×] = α skew(e_z)) and they match the review's numbers exactly. At α = 30°: af(0.256, −0.955, 0) vs af(0.5, −0.866, 0). Naive J^T s without the A^T conversion conflates these — refuted. The review's counterexample is now verified, not merely asserted.

## Why not STOP

The adapter consumes the production residual in the role the production solver already gives it (equilibrated against external moment vectors) and adds only exact transformations. The O(θ_loc) moment character is inherited from the formulation, not introduced: the production solver's own converged moment balance carries the identical first-order term. Local element kinematics (corotational.py:238-285) and element output conventions are untouched; the work fits the permitted narrow attachment adapter.

## Conditions for PASS (the unresolved part)

1. Parent explicitly accepts the inherited first-order-in-θ_loc moment approximation (error ≈ (θ_loc × m_loc)/2 per node) rather than requiring exact spatial torques — exactness would need R_node Jr(θ_loc)^{-T} m_loc, a wrapper output change outside narrow-adapter scope, which would then be STOP.
2. Adapter uses consistent tangent mode for Ks; opt-in profile only.
3. The review's two required numerical pairing checks (physical-resultant and additive-covector) pass in a later authorized numerical gate. This Read-only gate ran no numbers by instruction.

## Uncertainties and limits

- The O(θ_loc) discrepancy is an analytical derivation; no numerical verification was permitted.
- I did not inspect how external moments are applied in the production route (would strengthen the "inherited approximation" argument); no broad searches per instructions.
- I did not inventory all T usages, so integration risk of a state-dependent J plus Hessian term at nonlinear_static.py:3522/3537 is unquantified.
- Shell-side R_rig comes from `_shell_center_frame` (corotational.py:247); the same moment-block structure applies, but shell attachment specifics were not inspected.
- The prior 18-turn report had no final recommendation; nothing from it was relied on beyond the review file's pointers, all of which I re-verified.