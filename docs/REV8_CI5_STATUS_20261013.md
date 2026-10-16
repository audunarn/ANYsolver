# Rev8 CI5 — local verification and remaining failures

## Delivery

Branch `codex/rev8-ci5`, isolated worktree
`C:/Github/ANYsolver/.worktrees/rev8-ci5`, started from
`cc6f0962d0f9d39c9989c317df2bc7ddbbf63177`.

The retained changes add bounded exact-value diagnostics to the existing V2D
committed-displacement refusal, with three focused regression tests, and increase
the ordinary CI shard timeout from 1800 to 2400 seconds. The ordinary portable
runner default now matches 2400 seconds. Development's 600-second default and
the native 120-second context deadline remain unchanged.

This is a diagnostic/resource repair, not a claim that the six failing nodes or
the programme are accepted. No exact binding, physical criterion, frozen fixture,
qualification inventory, expected hash, material law or convergence control was
weakened. No skip/xfail or test-inventory exclusion was added. No pushes,
GitHub workflow executions, main merge, sibling edits or contact communication.
Main's unrelated work and previous worktrees were left untouched.

## Verification against the six requested nodes

All executions used `scripts/run_portable_ci.py`, one numerical job/thread,
2 GiB limit, JIT enabled. Commands, actual imported source, effective pools,
process-wall receipts and full output are retained under `.restart-ci/ci5`.
Windows used Python 3.13.9; WSL Ubuntu used Python 3.12.3. A separate Windows
Python 3.14 run checked the three native nodes at the CI Python version.

| Requested test | Windows 3.13 | WSL 3.12 default | Disposition |
|---|---|---|---|
| `test_b3_e4_f03_local_footprint_work.py::test_c1_axial_only_sixteen_cell_line_transfer_is_balanced` | PASS, 109.239 s process wall | PASS, 75.257 s | CI's 120-second native deadline discrepancy remains open. Raising shard time does not repair that deadline. |
| `test_e4_pl_s3_mixed_mesh_manifest.py::test_qualification_contract_and_replay_hotfix_bind_q4_mechanics_symbols` | FAIL | FAIL | Real Q4 source drift after the bound inventory; remains red. |
| `test_s3_v2d_default_activation.py::test_activation_candidate_binds_accepted_v6w_and_unchanged_q4` | FAIL | FAIL | Real Q4/S3 Git-blob drift; remains red. |
| `test_stiffened_shell_native_arc.py::test_native_arc_fixed_predecessor_restart_and_cancel[False-s3-fibre]` | PASS | PASS | Both default passes are insufficient: controlled Haswell dispatch reproduces exact restore failure. Remains open. |
| `test_stiffened_shell_native_fibre_bl5_material.py::test_native_material_lifecycle_and_fixed_predecessor_tangent[False]` | PASS, 48.392 s | PASS, 42.667 s | CI adaptive-increment exhaustion not reproduced locally; remains unresolved. |
| `test_stiffened_shell_native_s3_fibre_chart.py::test_simultaneous_s3_fibre_rebase_restore_and_signed_continuation` | PASS | PASS | Same controlled dispatch-sensitive restore failure as the arc node. Remains open. |

The two V2D nodes plus BL5 `[False]` also passed on Windows Python 3.14:
3 passed, 107.420 seconds process wall. An earlier sandbox-blocked 3.14 attempt
did not reach tests; its receipt is preserved separately. It is not a mechanics
failure or a pass.

The retained patch's focused refusal, existing V2D corotational/state, and
development-runner controls passed **35/35 on each platform** (Windows 16.024 s,
WSL 14.450 s process wall). These are the same 35 tests, not 70 distinct cases.
Effective BLAS and Numba thread counts were one. No installed-artifact or full
shard acceptance is claimed.

The owner-paused lifecycle node
`test_stiffened_shell_native_fibre_bl5_material.py::test_native_material_lifecycle_and_fixed_predecessor_tangent[True]`
was not rerun or masked. Its earlier unresolved scientific failure remains red.

## Findings and attempted repair

The identity failures are not line-ending differences. Q4's current blob is
`6b996905e67374b6e755b44978f2cd2c69acef82`, versus the activation record's
`bd6c0dc2cb3661eb73942fc0fea56e527aa8d0b4`. The legitimate `natural_points`
stress-recovery addition at `3bcd3211` changes the mechanics symbol inventory
after its registered successor at `9049d185`. S3 source also changed after its
recorded activation. Updating expectations to observed current values would
not supply missing successor acceptance. Historical records were preserved.

For the two restore nodes, holding source, immutable `unloaded-v1.bin` fixture
and test nodes fixed while selecting `OPENBLAS_CORETYPE=Haswell` causes both to
fail at the first restore. This shows dispatch-sensitive reconstruction; it
does not isolate a particular operation or prove that every backend is invalid.
The final diagnostic caller check still refuses both snapshots. For element 1,
nodes `[1, 2, 5]`, four of 18 entries differ; the first stored value is
`0x1.8000000000000p-68`, versus reconstructed `0x1.0000000000000p-67`.
Exact refusal remains in force despite the small physical magnitude.

One same-equation Rayleigh-value refinement candidate was tested and rejected:
it failed both frozen default-dispatch restores (15.032 s process wall). The
original `_ge_beam3_variational_shell.py` was restored byte-for-byte, SHA-256
`e03107c5322d50f110a631b2791c293fe85ec46eb95e8337e1e0a71d5ce6cf3d`.
An earlier replacement failure left the original implementation in place; its
two passes are explicitly baseline/diagnostic evidence, not candidate passes.
No further candidate, fixture rewrite, backend pin or tolerance relaxation was
adopted. Details and failed evidence remain in `QUATERNION_CANDIDATE.md`.

Mistral authored the retained diagnostic/test slice. Root inspected actual
changes and evidence, trimmed coverage with the same owner, and verified the
production callers. The later Mistral numerical assignment left useful analysis
but no candidate/handoff; root recorded the follow-through limitation before
the single reversible attempt. No numerical-core repair is retained.

## Shard budgets and next disposition

Run `38351792519` at the base hit 1800 seconds on Ubuntu 3.13 shard 5/subshard 2,
Windows 3.12 shard 2/subshard 0, and Windows 3.13 shard 4/subshard 0. The shared
2400-second setting is authorized prospectively. Those full shards were not
replayed locally and must not be called resolved before the owner's next CI run.

Remaining decisions are specific: prospective source-successor acceptance for
the changed qualification bindings, and a reviewed numerical reconstruction /
snapshot compatibility policy that satisfies the exact contract. BL5's CI-only
failure and native deadline remain separate runtime issues. This batch does not
authorize further lifecycle candidates or a new scientific campaign.

The fresh CI5 ordinary-verification ledger accounts for 575.894205742 seconds
of a 1200-second cumulative allowance, including failed and aborted attempts;
624.105794258 seconds remain, with a 60-second final reserve. Earlier ledgers
were neither transferred nor renewed. Raw receipts, source manifests, runtime
records, stdout/stderr, worker logs and decisions are preserved locally at
`C:/Github/ANYsolver/.worktrees/rev8-ci5/.restart-ci/ci5/`.
