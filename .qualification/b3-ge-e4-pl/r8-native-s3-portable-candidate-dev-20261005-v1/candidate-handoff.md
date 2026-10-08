# S3 portable candidate checkpoint, 2026-10-05

Outcome: incomplete experimental candidate. Strict default, archive framing,
authoritative histories and original fixture remain unchanged. The explicit
policy is `B3_GE_S3_RESTART_PORTABLE_CONSISTENCY_V1_DEV`; it is not adopted or
qualified. No further numerical child is active.

Owned dirty product/test files:

- `src/anysolver/_stiffened_shell_s3_restart_certificate.py` (new)
- `src/anysolver/_stiffened_shell_ge_finite_experimental.py`
- `src/anysolver/_stiffened_shell_ge_experimental.py`
- `src/anysolver/_stiffened_shell_affine_endpoint.py`
- `src/anysolver/_stiffened_shell_displacement_control.py`
- `src/anysolver/_stiffened_shell_arc_publication.py`
- `tests/test_stiffened_shell_s3_portable_restart.py` (new)
- `docs/reference_cases/stiffened_shell_s3_portable_restart.md` (new)

The helper drafts directed 72-digit Decimal enclosures for physical/local
association, smooth-branch scalar plastic consistency, predecessor current
elastic/yield invariants, local resultants, the complete `P^-T D.T f` work map
and original equilibrium/gap caps. Opt-in restore uses an isolated owner,
retains original accepted histories/checkpoint bytes, reports policy and
equilibrium upper bound, and publishes only after validation/cancellation.
No V2D reader or plasticity-law file was modified. Proof review remains needed.

Preserved source checks, all with 600 s / 2 GiB / affinity 1 / pools 1 / JIT off:

| Run | Result | Actual numerical scope |
| --- | --- | --- |
| v1 | 3 PASS, 1 FAIL, 9.83 s pytest | Four initial certificate controls. Predecessor pose corruption incorrectly survived. |
| v2 | 4 PASS, 3 FAIL, 6.44 s pytest | Seven changed controls. Independent receiver gate rejects unchanged old seed; scalar/continuation setup fails there. |
| v3 | Startup failure, no pytest | Evidence-runner path typo selected missing CI site; actual-import guard rejected older global libraries. |
| v4 | 1 FAIL, 1.49 s pytest | Error witness only, first old-seed control. Corrected isolated path; no admission change. |
| v5 | 1 PASS, 1 FAIL, 3.09 s pytest | Source-derived rounded coefficient DAG: original predecessor pose corruption rejects; unchanged seed passes both physical/local families and fails predecessor yield admissibility. |

V4 supervisor: 4.064929 s, peak sampled tree 188428288 B, maximum sampled
numerical/unresolved count 1. Runtime verifies NumPy 2.5.3, SciPy 1.18.1,
Numba 0.68.0, llvmlite 0.50.0 from the isolated CI site, two actual Haswell BLAS
pools with one thread each, one CPU affinity and disabled JIT. Runtime,
source/fixture/wheel hashes and prelaunch source copies are retained in
`runtime-v4.json`, `binding-v4.json`, `executed-source-v4/`; raw output is in
`focused-v4/`, JUnit in `junit-v4.xml`. V1/V2 failure evidence was not replaced.

First unchanged-seed failure: predecessor local rotation flat index 3; preceding
translation components 0..2 pass. Exact saved value / certificate interval:

```
value = -2.57636486091036909078675895636270014137092498884840097161941230297088623046875E-11
lower = -2.57636486077163879219944527136605035995977989925617120483901906606104829E-11
upper = -2.57636485747967744175882934512556564888533454269959133822330549547295746E-11
```

Call chain: public isolated restore -> displacement endpoint -> affine arrays
-> finite `_restore_native_s3_histories` line 377 -> helper `association`
line 499 -> `_inside` line 617. V4 helper SHA256:
`8f6f3974546b74881e742dc20d1720050e1fa20491cb28e4d1185e4a38f0d870`.
Original fixture SHA256:
`bf25a2c7e16172cfbf40df921809371eba28db8ae8f7ada232d655addc4461d5`.

V1 hole repair: archive-independent receiver fit checks both accepted and
predecessor; predecessor static material fields and committed alpha/yield
admissibility consume family 1 uncertainty. Archive discrepancy does not become
its own gate allowance. The v2 material-corruption test rejects before this
static check, so downstream discrimination is still unverified.

Remaining exact obstruction: `_receiver_local_bounds` uses the exact centred
covariance / exact squared reference norm. The actual primal
`_ge_beam3_variational_shell._quaternion_jets` rounds means, norm/divisions,
assembles two separately rounded Davenport contributions, and refines

`q_rest = (lambda_producer I - M_rest)^-1 M_rest,pivot`.

A directed enclosure of the coefficient DAG is now implemented without archive
discrepancy in `_primal_fit_matrix`. It covers source-rounded means/subtractions,
norm dot/sqrt, divisions, separate covariance/Davenport blocks and final
addition. V5 checked source helper SHA:
`cb110ba696c4bd6a0117eac05af369e9ae5c67dc724d1002cea0ecdf4b07f0c0`.
Prelaunch snapshots and wheel/fixture/source bindings are in
`executed-source-v5/`, `binding-v5.json`; actual imports/pools are in
`runtime-v5.json`; raw diagnostics are in `focused-v5/`, `junit-v5.xml`.
Supervisor: 5.489773 s, peak 191139840 B, maximum numerical/unresolved 1;
same four exact CI libraries, Haswell pools, one thread/CPU and JIT off.

This bounded coefficient change advances the positive archive through both
physical/local gates. The legacy payload still lacks the producer
top eigenvalue/backward-error witness. A receiver-checked eigenvalue does not
prove an a priori error bound on that producer value. Source coefficient
rounding now suffices for these local gates; it does not establish a general
producer accuracy guarantee. Stable
translation computes the quaternion increment directly; there is no evaluated
diagonal-minus-one subtraction to justify an added allowance.

No empirical floor, widened scientific cap, dependency pin, CPU production
policy, history substitution/resealing, older-path replay or automatic
portable admission was introduced.

Final exact rejection is station 0 of loaded predecessor element 1 at helper
`_point(static=True)` line 683, after physical-field and current elastic
constitutive inclusion. Required original inequality:

`sup(phi_squared(C*(epsilon_physical-epsilon_p_committed)) - flow(alpha_committed)^2/3) <= inf(1e-10 * max(flow(alpha_committed)^2, 1))`.

The propagated interval cannot prove this bound. The run did not emit its
numeric endpoints, so no invented quantitative margin is reported. It did not
reach accepted same-parent replay/global work margin or continuation. Further
candidate expansion/tests stop as directed. Root must decide whether a bounded
dependency-tightening certificate can prove the original inequality; no cap
relaxation or acceptance substitution follows from this failure.

Required remaining outcomes: original old-seed restore and actual plastic
continuation, downstream corruption discrimination, original work/gap margin,
independent proof assessment and installed meaningful-boundary check. Present
status is an incomplete rejection-safe candidate, not a portable solution.
