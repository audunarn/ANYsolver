# D6 contact-free native midpoint: prospective development contract

2026-09-30. Design only; no numerical execution or time-integration admission. The independently reviewed finite-inertia owner is locally tested. Full C7 qualification remains outstanding. This slice retains native centered geometry, physical section inertia, homogeneous supports and the generalized ellipsoidal section; excludes contact, yielding, prescribed motion, MPCs, activity, point masses and public dispatch changes.

## Owners and proposed API

Future private `_ge_beam3_native_midpoint.py` and its new focused test belong in the managed D6 worktree. Proposed `MidpointContext(analysis, *, inertia_order=24, max_iterations=12, max_backtracks=8)` consumes the exact `NativeBeamAnalysis` and its frozen definitions, `_inertias`, `_guard`, `_admit_boundaries` and owned model; it creates no generic FEModel or alternative element. `initialize(mechanical, physical_velocity24, *, time=0.)` issues an immutable `MidpointState`; `trial(accepted, *, dt)` returns an immutable, owner-bound candidate; `commit(candidate)` atomically issues the endpoint; `discard(candidate)` invalidates the candidate without changing the accepted state. No static checkpoint schema is reused.

Structural work is `RetainedGeneralizedOperator.evaluate`: `Pi=p·k(q)−Psi*(p;origin)`. `_ge_beam3_retained_generalized_state.Context.assemble` supplies full mixed spatial `R_s,J_s` through `operator_call`, `_ge_beam3_fibre_line_work.evaluate` and `_ge_beam3_generalized_static_boundary.spatial_jacobian`; `Context.make/histories/guard` retain coordinate, material and model validation. A zero-load static Context may supply these evaluations under its existing 120 s lifetime; never renew it to evade that limit. `Context.advance` is only a Newton retraction, not the time update. **`Context.record/stage` require static physical equilibrium and cannot issue a dynamic endpoint.** The new transaction owns dynamic validation separately; existing static owners/codecs are unchanged.

For one element, canonical 42 order is three interleaved `(translation3,nodal-frame3)` blocks, two physical cell-rotation3 blocks, then resultants18. Physical coordinates are translations9 + cell rotations6; algebraic coordinates are nodal frames9 + resultants18. Clamp node 1 in all six components: free physical12 and algebraic24. Velocity24 uses the finite owner's external18 + cell-spin6 order, with all nine nodal-frame entries exactly zero. Its mixed inertia extension has exactly zero algebraic rows/columns. State binds complete high/low positions, nodal/cell frames, resultants, material origins/histories, spatial physical velocity, time, epoch, predecessor and definition/support/inertia/load identities; arrays are immutable. Momentum uses the finite owner's explicit high/low origin, here world origin `(0,0,0)`.

## Common stage, endpoint and complete Newton derivative

Let `h=dt>0`, endpoint physical unknowns `(Δr,φ)` and independent stage algebraic unknowns `(η,p_m)`:

\[
r_m=r_0+\tfrac12\Delta r,\quad U_m=\operatorname{Exp}(\phi/2)U_0,
\quad r_1=r_0+\Delta r,\quad U_1=\operatorname{Exp}(\phi)U_0;
\]
\[
v_m=\Delta r/h,\quad\omega_m=\phi/h,\quad
a_m=2(v_m-v_0)/h,\quad\alpha_m=2(\omega_m-\omega_0)/h.
\]

Positions use compensated `split_sum`; all rotations are spatial left increments. Stage nodal frames are `Exp(η)Q_0`, independent of physical spin. Assemble **all free spatial rows** `F_m=R_s(q_m,z_m,t_m)+I(q_m,v_m,a_m)=0`, using `evaluate_centered_finite_inertia`, including configuration work and gyro terms. Algebraic rows are `C_m=R_{s,z}=0`; they receive no inertia. The first slice has zero external load; future dead-load extension must evaluate stage and endpoint loads at their respective times.

For Newton columns `u=(Δr,φ,η,p_m)`, the full mixed configuration map `A` has translation `½I`, cell rotation `½J_left(φ/2)`, nodal frame `J_left(η)`, resultant `I`. Velocity map `V` is `I/h` on physical columns only; acceleration map `B` is `2I/h²` there. With the finite owner's spatial `I_q,I_v,M`, the **unpulled spatial-row** Jacobian is

\[
D_uF_m=(J_s+I_q)A+I_vV+MB.
\]

`exp_chart_terms` supplies exact left-Exp maps. Keep the spatial correction already in `spatial_jacobian`; do not symmetrize or use the symmetric-potential pullback. If chart-pulled residual rows are later chosen, their derivative additionally requires `D(A^T)F_m`; that is a different explicit row contract.

Set physical endpoint velocity `v_1=2v_m−v_0`, `ω_1=2ω_m−ω_0`. At **fixed** `(r_1,U_1,v_1,ω_1)`, solve endpoint algebraic equations `C_1=R_{s,z}(q_1,z_1,t_1)=0`, with Jacobian `C_z` and multiplicative nodal-frame retractions. Initialization likewise solves `C_0=0` at supplied physical coordinates. Physical acceleration at initialization/endpoint is recovered from `M_pp a=−R_{s,p}−I(q,v,0)_p` on free physical coordinates; it is not a static equilibrium condition. No physical cell coordinate is condensed or changed by algebraic consistency. A rank-deficient `C_z`, nonpositive physical mass, or inconsistent fixed support fails closed; stage convergence alone does not establish endpoint consistency. Such a failure requires an explicit full DAE constraint/velocity-consistency design, not lagged endpoint algebraics.

## Atomicity and one bounded implementation check

All stage/endpoint material evaluations use the accepted immutable origins. Require strictly `ELASTIC` station branches, histories equal to origins and zero dissipation; do not invoke a private elastic override to bypass yielding. Commit only after full stage residual/correction and endpoint algebraic residual/correction satisfy the existing `1e−11` scaled gates, with dynamic residual including inertia and exact zero support velocity. Recheck identities/cancellation immediately before publication. Publish material, mechanics, physical velocity and time together; any failed solve, exception, cancellation or stale/foreign candidate leaves accepted canonical bytes unchanged. Retain stage material/work identities and endpoint residual, acceleration, reaction and momentum diagnostics.

First fixture: exact native definition for the existing curved three-node geometry `x=(-1,0,1), y=.2(1−x²), z=0`, tangent `[1,−.4x,0]`, second director `[0,0,1]`; generalized section from `test_ge_beam3_generalized_slenderness_diagnostic.make(100,True,I)` (copy its declared data through native definitions, not its FEModel constructor), structural order4, reviewed physical cross-inertia fixture (mass2.7, COM `(.035,−.025,.012)`, COM inertia `diag(.12,.17,.19)`), inertia order24. Start virgin/reference configuration, zero translations velocity, cell spins `(.01,−.007,.004)` and `(−.006,.009,.005)` rad/s; clamp node1; zero loads; eight steps `h=1e−4 s`. Freeze inputs before one 180 s/1 GiB focused process, honoring the internal 120 s Context limit.

Checks: directional complete-stage/endpoint Jacobians on smooth branches (`1e−5` relative target with useful perturbations); zero algebraic inertia; endpoint consistency and rejection rollback; linearized full mixed descriptor midpoint against an independent block solve with singular mixed mass (eliminate algebraics only in this reference, retain physical cell rotations); independently differentiated instantaneous linear/angular momentum balance including clamped reaction wrench, retaining fixed algebraic-frame reaction couples. Report discrete step impulse/energy defects; exact midpoint energy/momentum conservation is not presumed, and small-amplitude descriptor agreement is not nonlinear qualification.

Source inspection closed at main HEAD `97a277d8fb4034d09f0df6569457cb6b9754a4a6`; SHA256: retained state `e4965fd3cc8cd8c498a8fd21247bc8ce09a073fdf245dca1b3b10b084cfde719`; structural boundary `8ea10a90290ab89a413d7c947a6cd3a50c71331f2a89e41e4b94f7248f1b2085`; retained operator `39121d4d76a5524579c2ea506c9bdf968a3d254cb7e6740de6173eb5aa7e6787`; native restart boundary `e933bfde2dc0339b6002d068af333118c3020e85ab9d5595917cb62527dc8c0a`. Reviewed managed finite owner remains at worktree HEAD `23e845e1`, SHA256 `3334699c5a4c14ef67cbfcef3ad54c3be8c80a15b98f2c34aa6840be70d32f84`.
