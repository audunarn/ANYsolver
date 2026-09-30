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

## Addendum — loaded finite-motion V2, independent post-run disposition

2026-09-30. **Scoped local development PASS.** The preceding6076 bytes and their24-step unloaded verdict are preserved exactly, SHA256 `ddc65ace65c9769e9fd1fa671b05f52082bc79a78d224865eefe3b6c744d33f8`. No reviewer numerical execution or renewed audit.

Loaded V1 remains **NOT_EXECUTED**. Independent prospective review found that cloning the supplied load pattern regenerated its signatures before validation. V2 requires the supplied exact pattern against the actual mesh before cloning, revalidates it, compares original/owned canonical values and validates the owned copy. Stale line/couple and forged distributed-signature construction controls passed; changed current pattern and cancelled publication reject atomically without losing the ready candidate. The default None payload is preserved.

Reviewed V2 SHA256:

- Midpoint: `5931f8d1d5c123e85acaf22bb58ec94a80f4dd86f8e2beeba76f7149a143526c`.
- Dynamic elastic/load owner: `9586af4379a566f8bfa51c6454bba173dd110966d09a7d7f36ba967aedcd8498`.
- Test: `426f673d40e82a4d554c3964dc9b51b4ca5638f180f3f985e4ba85c974ebc05d`.
- [Frozen inputs](d6_native_loaded_temporal_v2_20260930.inputs.json): `3e3e38aba71d70492509a538e62c7f6f01a1e3306dffc1607a485ac431fc8ef9`.
- [Summary](d6_native_loaded_temporal_summary_v2_20260930.json): `5289a05c6cffc71fed9b1e627db9040c079963f59e9446c893968a1c7f5678d6`.

[Raw endpoints](d6_native_loaded_temporal_v2_20260930.json), source snapshots, [log](d6_native_loaded_temporal_v2_20260930.log), XML and [resource](d6_native_loaded_temporal_v2_20260930.resource.json) reconcile with all nine summary-bound hashes. The runtime verified managed imports, thread1 settings/cache and441 frozen bindings;436 package identities remain unchanged. The living development note was appended afterward. One new test PASS/five old checks deselected: exactly4 coarse/8 fine accepted epochs through0.004s, **31.4128209s/208.756736MB**, exit0 within180s/1GiB.

Actual stage and initial/end work/acceleration/consistency use the bound pattern at parameter1. The full physical load42 and spatial load Jacobian retain exact algebraic zeros. Independent scalar station integrals check nodal force, physical lift torque, constant spatial couple and `outer(lift,f)-(lift dot f)I`; map/J/wrench error is at most1.1233e-16. Full loaded-stage directional error is at most1.1274e-11.

Saved-data reconciliation independently reconstructs actual endpoint P/H changes and `T+Pi` minus accumulated exact physical work. Exact force work uses endpoint line displacement, couple work uses the issued left-Exp increment C dot phi, and path angular impulse uses its analytic average rotation. Midpoint generalized work and midpoint angular impulse remain separate. Normalized exact-work cumulative energy defects are4.366163299e-9/1.091924362e-9, fine/coarse **0.250087843**. The individual midpoint-minus-exact work difference remains visible, at most2.3106e-15J coarse/2.8954e-16J fine. P/path-H/midpoint-H defects are below the declared1e-10 floor; no measured momentum order is claimed. Endpoint energy is still T+Pi, not load work redefined as storage.

This closes the named12-step private loaded Level A slice. It establishes neither general temporal order nor fullC7 qualification/public finite-speed admission, and does not close contact, yielding, multiple elements or durable dynamic restart. V1 nonexecution and all earlier evidence retain their original scope.