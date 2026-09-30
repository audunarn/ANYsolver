# D6 free native temporal slice — independent review

2026-09-30. Bounded source and saved-evidence review by `checkpoint_review`; no numerical execution or production edit. **Scoped local development PASS, with the identified gate binding defect repaired.** This does not accept C7, admit public finite-speed dynamics, integrate the managed modules into the main package, or release an artifact.

## Source and ownership

Reviewed managed `ANYsolver` at `C:/Users/AudunArnesenNyhus/.codex/worktrees/general-contact-native-dynamics/ANYsolver`, base HEAD `23e845e131a8ea0c3457d10d9355ecdd5d1dd28e`. Final SHA256:

- `_ge_beam3_native_midpoint.py`: `211665de1e62fc10dd69f30e9bb29c519bf90029647e202b2d3093b84aa73519`.
- `_ge_beam3_dynamic_elastic_state.py`: `8c3cd98ea263e43fa238964acd39f0d6502700467986fabceb707e560a72d032`.
- `tests/test_ge_beam3_native_midpoint.py`: `191409ab8e452b808c8d501a82a84c69b978d083daa7e4c67146669ec986392f`.

The explicit `dynamic_elastic` route uses free physical15/algebraic27 coordinates without a static inverse or hidden support. Default `legacy_clamp` keeps its original identity payload and static owner. The retained finite inertia owner is unchanged (`3334699c…`); its full42 embedding retains exactly zero algebraic mass, momentum and inertia derivatives. Existing static/public admission guards are unchanged.

`ElasticWorkSession` (dynamic module lines82–121,209–241,275–295) binds the exact active context and creator thread, rejects nested/foreign/closed use, and issues at most128 disposable states. Strong identity and canonical records authenticate issuance; scope exit clears these records before the native operation exit guard. Permanent standalone issuance is preserved, without eviction. Midpoint transaction publication (lines223–244) follows both session and native exits; exceptions restore predecessor, candidates, issuance and initial diagnostics. The tests exercise a real native exit followed by an injected failure, cancellation, and later successful reuse of the same ready candidate.

## Mechanics and evidence

The stage retains half physical translation/cell rotation, the actual nodal exponential chart and its Jacobian, independent resultant variables, `v=u/h`, and `a=2(v-v_n)/h`. The full derivative is `(J_s+I_q)A+I_v V+M B`; no symmetric tangent or static mass replacement is introduced. Initial and endpoint algebraic consistency are solved with physical coordinates fixed. Endpoint accounting evaluates actual accepted physical momentum and `T+Pi`, with the separate witness `abs(resultants18 dot R[24:42])`; it does not substitute stage storage for endpoint energy.

[Frozen temporal inputs](d6_native_free_temporal_v1_20260930.inputs.json), SHA256 `7dba6c5b1eb71d63dbb1a08e139d767ca1abe8290c9773d29fc5092664423c12`, bind436 package files plus five supporting files. [Raw endpoint data](d6_native_free_temporal_v1_20260930.json), [resource](d6_native_free_temporal_v1_20260930.resource.json), [log](d6_native_free_temporal_v1_20260930.log), XML and snapshots reconcile with all nine hashes in the [summary](d6_native_free_temporal_summary_v1_20260930.json). Actual process imports, threads1 and writable cache were verified before pytest. One test passed, two old checks were deselected: exactly24 accepted steps, 4 coarse/8 fine per case through0.004s; **42.2811512s/203.620352MB**, exit0 within180s/1GiB.

Saved-data reconstruction of endpoint momentum differences, total energy and the resultant witness agrees with the reported quantities:

| Maximum cumulative normalized defect | Coarse | Fine |
|---|---:|---:|
| Translation P / E | 0 / 0 | 0 / 0 |
| Translation H | 1.03175e-20 | 2.19207e-20 |
| Flexible anisotropic spin P | 2.07577e-12 | 5.19789e-13 |
| Flexible anisotropic spin H | 1.95248e-13 | 4.91220e-14 |
| Spin T+Pi | 5.83866e-9 | 1.46027e-9 |

The common-time energy ratio is0.250104, below the frozen0.6 criterion. P/H are below the declared1e-10 resolution floor; they establish no observed order. Translation preserves analytic velocity/frames and compensated position with error/L* at most3.0400e-20 under a2^40m origin translation. Spin develops nonzero elastic storage. Stage residual at most1.755e-13, endpoint algebraic residual3.890e-15 and normalized witness2.536e-20 meet unchanged gates. Endpoint algebraic rank27 and physical mass SPD are checked throughout; their SI-coordinate condition numbers are diagnostics, not universal stability bounds.

## Finding, repair and limits

Temporal V1 (`05e77d96…`, test `40417905…`) used new public `scale/length` aliases without binding them in the guard. Replacement could change acceptance under the same context identity. Final `_gate_inputs`, `_guard`, `_norm` and `_correction` (lines192–208,246–262,325–335) derive factors from the guarded selected owner and reject differing aliases. Dynamic reference coordinates are identity-bound; legacy factors and identity payload remain unchanged. The exact V1-to-final diff changes only gate derivation/check/use, with identical unmutated factors and stage/endpoint equations. Temporal evidence is reused on that explicit impact basis, rather than reattributed to a replay.

[Repair evidence](d6_native_midpoint_gate_binding_v1_20260930.json) records two new route-specific controls PASS, zero steps/three old checks deselected, **4.098055s/204.398592MB**. All eight evidence hashes and436 final package bindings match. The living development note was appended after the frozen processes; it is not an unchanged post-handoff input. Frozen V1 sources/data and prior failures remain preserved.

No remaining concrete blocker was found for this named private development slice. Principal remaining mechanics boundary: applied load/torque impulse and work balance and broader time/horizon convergence have not been demonstrated. Contact, yielding, multiple elements and durable dynamic restart also remain outside this result. Two short free trajectories and decreasing energy defect do not establish general temporal order, C7 qualification or application admission.
