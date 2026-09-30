# D6 native midpoint — bounded development result

2026-09-30. **Local development checks passed; no public/time-integration admission or C7 qualification.** Implementation is confined to two new files in managed worktree `C:/Users/AudunArnesenNyhus/.codex/worktrees/general-contact-native-dynamics/ANYsolver`, HEAD `23e845e131a8ea0c3457d10d9355ecdd5d1dd28e`:

- `src/anysolver/_ge_beam3_native_midpoint.py`, current SHA256 `6f5607aed1efcc23d4da96882882540236d2293ecb7f49f5e2909a3e2c09abab`.
- `tests/test_ge_beam3_native_midpoint.py`, current SHA256 `38cdec0d9a79315ca744f4434fcf8c937cedf4026b54d7ca4ac38fe0e92b34e3`.

Main package and all existing managed tracked files remain unchanged. The independently reviewed finite owner is reused unchanged (SHA256 `3334699c5a4c14ef67cbfcef3ad54c3be8c80a15b98f2c34aa6840be70d32f84`). Existing public finite-speed exclusions, static Context issuance and restart codecs are preserved.

## Implemented contract

`MidpointContext` admits exactly one centered generalized element, canonical 42 order and homogeneous full clamp on the first ordered node. API: `initialize`, `evaluate_stage`, `trial`, `commit`, `discard`; immutable issued states/candidates bind the current predecessor, epoch, time, full mechanical/material state and definition/inertia/support/context identities. The native analysis operation lock and a nonblocking midpoint transaction lock protect operations.

Common-stage translations/cell rotations use the reviewed midpoint map. All physical cells remain unknowns. Independent stage nodal frames/resultants have zero inertia. Velocity24 nodal-frame zeros are **inertial placeholders**, not zero derivatives of the solved algebraic frames. The unpulled spatial stage Jacobian is `(J_s+I_q)A + I_v V + M B`, with cell configuration block `0.5 J_left(0.5φ)`, physical velocity block `1/h` and acceleration block `2/h²`; no symmetry substitution. Endpoint algebraics are solved at fixed physical coordinates/velocity. Initial/endpoint physical acceleration is recovered from the supported physical mass and finite gyro work. Every material trial uses accepted origins and requires strictly elastic unchanged histories.

Static Context construction validates its reference genesis; its `record/stage` are not used for dynamic issuance. Its existing 120 s deadline remains active. Failed trial/commit/discard leaves accepted canonical state unchanged. A final audit identified the analysis **operation-exit** guard after tentative publication: a scoped fix now keeps `current` publicly at the preceding state until that guard succeeds, and restores issuance/material/mechanical/time/velocity bookkeeping on exit failure. This changes transaction handling only, not the method or mechanical operators.

## Measured evidence

One curved native elastic beam, physical section cross inertia, two nonzero initial cell spins, zero loads, eight accepted steps `h=1e−4 s`; one extra discarded trial solely exercises rollback. Full inputs and matrices are retained. Two distinct new tests passed across the retained runs:

| Evidence | Result |
|---|---|
| v1 | NONPASS, argv serialization defect before test execution; no mechanical checks ran; 3.194 s, 191.189 MB |
| v2 integrated mechanics | 1 PASS; 27.105 s, 200.339 MB; eight accepted steps |
| v3 new transaction-only control | 1 PASS, integrated check deselected; 3.382 s, 198.312 MB; no mechanical evaluations |

Each process had 180 s/1 GiB caps, threads1, frozen source/input snapshots and explicit writable `NUMBA_CACHE_DIR`. The actual process verified environment, hashes and managed import paths before pytest. V1 is retained unchanged.

Measured initial `C_z`: rank24, minimum singular value `3.44821060e−5`, condition `46731.819`. Free physical mass is SPD: minimum eigenvalue `0.124643075`, condition `16.1913`. These are numerical SI-coordinate matrix diagnostics, dependent on translation/rotation/resultant component scaling; they are not invariant universal conditioning thresholds. No singularity or method adjustment was needed.

Stage directional errors at perturbations `1e−5,2e−6`: physical ≤`5.454e−13`, algebraic ≤`1.583e−8`; endpoint algebraic derivative ≤`1.249e−11`. Independently differentiated linear/angular momentum rates, including fixed algebraic-frame reaction couples, agree with the instantaneous reaction wrench within `7.112e−13` relative. Final independent full mixed linear descriptor errors: physical configuration `9.492e−7`, velocity `1.926e−6`, algebraics `1.193e−5` relative. All stage/endpoint convergence gates passed. The last endpoint resultants differ from stage resultants by norm `0.00630915`; endpoint algebraic consistency is consequential and was solved explicitly.

Cancellation, valid discard, foreign/stale tokens, concurrent-operation rejection and immutable arrays passed in v2. V3 injects an operation-exit guard failure into commit, discard and initialization and verifies exact rollback/private tentative publication. V2 integrated mechanics used module SHA256 `9ba1d223af9e8e5db7865bdbdede6ad53dc2dbd082b1a4388f3c9605e53ec6fd`; it was not replayed after the transaction repair. Static AST comparison confirms all nine mechanical/rank/mass/derivative methods are unchanged. This impact analysis is explicit in the summary.

## Raw paths and limits

All raw artifacts are under main `docs/d1_review_support/`: `d6_native_midpoint_v{1,2,3}_20260930.inputs.json`, `.entry.source.py`, `.module.source.py`, `.test.source.py`, `.log`, `.resource.json`; v2/v3 have `.xml`. Complete measured mechanics and per-step arrays are in `d6_native_midpoint_v2_20260930.json`; combined status/source/AST impact evidence is `d6_native_midpoint_summary_v1_20260930.json`.

Independent review is still required for this midpoint owner. This slice does not measure discrete step energy/impulse defects, long-time/convergence accuracy, yielding, multiple elements, contact or durable dynamic restart. Instantaneous momentum balance and small-amplitude descriptor agreement do not establish general nonlinear stability or exact discrete conservation. No further numerical work was launched.

## Read-only next-slice admission finding

At lead request after closure, inspected zero-support admission only. `NativeBeamAnalysis.__init__` accepts `boundaries=()`; `_admit_boundaries` then returns `()`, and the definition/model guard still enforces no MPC/activity/point masses. This permits an exact native **definition**, not a zero-support static workflow: its force routes explicitly require nonempty supports (`_ge_beam3_native_analysis.py:244,280`). Retained `Context` cannot be constructed for that case: `_ge_beam3_native_generalized_restart._model:141` rejects `len(free)==n`. Moreover, `Context.record` calls the full static `step` at genesis; the free beam's exact physical rigid modes preclude using that static equilibrium inverse as a dynamic initializer. The new midpoint owner itself explicitly admits only the reviewed full clamp.

A future free-motion slice therefore needs a private dynamic mechanical/material evaluator bound to the exact native analysis, reusing `RetainedGeneralizedOperator.evaluate` and `spatial_jacobian` directly rather than bypassing/subclassing the supported static Context. Retain its existing guards unchanged. For one free element, independently validate canonical full42 order, all physical15 and algebraic27 coordinates, the 27×27 endpoint `C_z` and 15×15 physical mass before any temporal campaign. Their free-case ranks are **not measured** here; static whole-system rigid modes do not themselves establish singularity of the fixed-physical algebraic block. No hidden supports, added inertia, physical-cell condensation or common-stage equation change is proposed. Native analysis, retained Context and restart boundary source hashes match the identities frozen above. No free fixture or numerical run was started.
