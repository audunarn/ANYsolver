# F06 v4 bounded S3 independent pre-execution review

23 September 2026 — reviewer: `f02_raw_audit` (read-only scientific review; supervisor identity corrections owned separately).

**Disposition:** No remaining mechanics or adjudicator correctness blocker found for preparing a *one-use bounded S3 owned-rebase registration*. This is preparatory sign-off, not an accepted run, full F06/G0B qualification, or release. Registration must wait for the six source/test files and this note to be committed, a clean tracked tree against the registered HEAD, and a precreated writable evidence-specific `NUMBA_CACHE_DIR`. The formal child must attest the same effective environment. No frozen registration was executed in this review.

## Exact reviewed identity

The reviewed base HEAD was `92e849f1887c82a896d8b835a3f3822504f486e1`; the files below were uncommitted at review. SHA-256:

| File | SHA-256 |
|---|---|
| `scripts/probe_b3_ge_e4_pl_g0_f06_owned_rebase_v4.py` | `e1c14c96d34fbbbb8f76f045d7a28d6f6689b5749fa81cdace14b1ac801873c3` |
| `tests/test_b3_e4_f06_owned_rebase_v4.py` | `2ad40c211ac7cc48fa6da2d8108adc98c5c9eab5f588711b67b0f22e5bd6f962` |
| `scripts/adjudicate_b3_ge_e4_pl_g0_f06_v4.py` | `31cd183a8de8d7607c4d7b56a13d8221182d3d180dfb4e453849539a3f96b996` |
| `tests/test_b3_e4_f06_v4_adjudicator.py` | `169d9c702cd15bbce33d583579f6eff3af4b50b30d12eb353021837596b8fe1d` |
| `scripts/supervise_b3_ge_e4_pl_g0_f06_v4.py` | `3fedb5a414afc8f5f72dd77ee4fdaf0db688c9990c15e0352fe6a7b1d58cd623` |
| `tests/test_b3_e4_f06_v4_supervisor.py` | `a1257e601ddf479fe13726f6c0e4008a8038c1fea4d9db8957b99fc8bcd647cc` |
| `B3_GE_E4_PL_G0_F06_V4_SCIENTIFIC_CONTRACT_DRAFT.md` | `647687556752e1e7a6916cc8636a95dca0dd0acf0559e8d48d10af0ae7893982` |
| `B3_GE_E4_PL_G0_F06_OWNED_REBASE_V4_PROTOCOL.md` | `9daee7b3889d04ba40fe6f8adfed60d30d9e30753765a6b0f952d36caaf6949f` |

The runner's 25 measured source roles equal the supervisor/adjudicator measurement roles; the supervisor requires exactly 30 total roles. The SHA-256 of compact, sorted-key UTF-8 JSON mapping each of those 30 relative paths to its current file SHA-256 (no trailing newline) is `c1e53a2cee6d44002dccc0c5bed59610ce2426a0f8226298fdfcb02311584d15`. This is a review-time identity, not the future committed registration identity.

The latest **disposable, unregistered** measurement is `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/f06-v4-candidate-92e-10/metrics.json`, raw SHA-256 `88799a70c41aa04dc66863ba7fb5a974f95643f760018f606de7acb543ce35a3`. Its 25 source digests match the reviewed files and all four canonical sidecar digests match the metrics. It contains no supervisor resource attestation and cannot satisfy a one-use registration.

## Review findings and evidence

The fixed fixture, force/moment units, and reference scales are coherent: `F_ref=sqrt(5)*1e-4` is derived from the full dead tip force, `M_ref=F_ref*1`, and support reaction plus terminal load balances are evaluated at both cursors on both paths. The shell-chart conversion uses the left exponential Jacobian, mixed and isolated finite differences perturb actual shell/beam/joint/dead-load operators, and the point-work check differentiates the joint potential against its complete 12-port spatial residual. Its six rigid directions include `omega × x` at the physical eccentric port positions. Direct cursor-2 and cursor-3 restore performs current-state validation; full replay is a distinct audit. Indexed 18-role beam resultants and two members × eight stations × six generalized strain/resultant components retain their high/low splits and dimensioned floors.

The adjudicator now enforces the exact 30-role source map, effective child environment, canonical metrics/sidecars and hashes, all declared thresholds, both paths' residual/gap and four balance rows, raw vector recomputation for paired/FD/change metrics, indexed station and layer maxima, finite-difference plateaux, work conjugacy/rigid zero-work, nontrivial third-step change, and before/after head/generation for all seven typed negatives. It reports a candidate screen and never marks qualification accepted. The implementer reports 11 focused runner/adjudicator tests passed; I ran 15 disposable supervisor tests, all passed. I did not rerun the scientific measurement or the frozen gate.

The disposable measurement's finest mixed scaled FD errors are `5.272e-9` and `5.277e-9` (cursors 2/3), against `1e-6`. Cursor-3 fixed-reference force/moment closure is about `1.47e-9`/`1.09e-9` on each path, against `1e-8`; finest point-work errors are below `2e-11` scaled, against `1e-8`. The third-step beam rotation, support-force and support-moment changes (`1.461e-3`, `5.590e-5`, `1.12e-4`) exceed their declared lower bounds. These are candidate observations, not accepted scientific evidence.

**Limits before registration:** An initial worktree `.venv` Numba cache path hung for more than 180 seconds in Numba tempfile setup and was stopped. The root reviewer then precreated the writable cache `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f06-v4-env-cache-20260923`: a direct tempfile write took 0.0004 s, local ANYsolver import 0.949 s, and supervisor `_environment()` 0.037 s. The observed package identities were pywin32 311, Numba 0.65.1 and llvmlite 0.47.0. This resolves the local supervisor import smoke. The formal run must use a precreated writable evidence-specific cache and attest the child's exact `PYTHONPATH`/`PYTHONNOUSERSITE`, pywin32/Job Object, Numba/llvmlite, local ANYsolver import, thread and BLAS fields. The adjudicator recomputes reported formulas from preserved arrays but does not independently re-evaluate every constitutive operator from sidecar state; the reviewed, hash-bound runner is the source of those arrays. It also does not reconstruct the reported component joint-port projection or support reactions from checkpoint state, so source review and the registered clean-tree/identity guard remain part of the evidence chain. The 180-second/2-GiB process-tree limits have not yet been demonstrated by a frozen run.
