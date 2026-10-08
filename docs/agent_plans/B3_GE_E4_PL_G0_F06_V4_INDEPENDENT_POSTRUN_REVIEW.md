# F06 v4 bounded S3 independent postrun evidence audit

23 September 2026 — reviewer: `f02_raw_audit`. Read-only audit of the **consumed** one-use evidence at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f06-v4-s3-scientific-20260923-v1`. No scientific execution or adjudicator run was repeated and no raw evidence was changed.

**Disposition:** I concur with the preserved `CANDIDATE_SCREEN_PASSED` result for the registered **bounded curved S3 owned-rebase case only**: 550 checks, zero failures, process exit 0. The receipt explicitly has `qualification_accepted=false`. This does not close full F06, Q4, beam-chart, G0B, or production release obligations.

## Identity and execution chain

The canonical `registration.json` is SHA-256 `c2cfb539a2efaebeab38fd75e053f2976f27523e29a733ab96ef2cfea346c199`; `execution.claim` is `98b45fff74fff36a46bf1a18f4cb12bb4315bd3202cabe97c5db72119d601b0f` and binds that registration digest. The frozen registration retains its initial `REGISTERED_UNEXECUTED_BOUNDED_S3` status; the exclusive claim and terminal receipt show that authority is now consumed. Registered source commit `77f787da3fdd8ca37056fc9415ef862e24035a80` matched the clean worktree HEAD at audit. All 30 registered source file digests matched the worktree and supervisor attestation; all 25 runner source digests matched the registration. The compact sorted-key JSON digest of the 30-path source map is `c1e53a2cee6d44002dccc0c5bed59610ce2426a0f8226298fdfcb02311584d15`. The two registered independent review hashes also matched: pre-execution `623593d8bc1de5b01eb3d0990f4ef90e4241ddd28c82e7d26770ad3744898a8c` and supervisor review `57bf45aee8956a38715ea43f14ef922816999d49828cc4a388e18b6f591f2115`.

The registered command, output path, 0.5/1.0/0.75 targets, prototype profile, definition hash `88521a9150412dccec6b29660aaae884340c40c94b8bb9d5c551eaf2973a8f62`, physical reference scales and all threshold/floor values matched the saved metrics and sidecars. Registered, supervisor-observed and child-recorded effective environments were equal, including local ANYsolver import, the evidence-specific Numba cache, Python path/site flags, pywin32/Job Object, Numba/llvmlite, one-thread settings and BLAS identities. The separate preserved pytest setup error log matches its registered SHA-256 `97730285fb9082469209cd2cc239f106f42d8c8873efb3eb43d577bd39913336`; the frozen `test.log` is `8ac1deed5d9d50de04b0fc8f090c1bc6f0bbb106242740549e5efc6733e974d7` and reports **26 passed**.

Supervisor attestation SHA-256 is `64536f3507d7b6ccb49f0cabab2482e18a9f70a5903cc5206f9101e6d2e10cd3`. It records 43.740 s against 180 s, 211,111,936 bytes (201.33 MiB) sampled peak process-tree RSS against 2 GiB, 435 RSS samples, exit 0, no resource violation or launch error, and matching child environment. The preserved stdout and empty stderr hashes match attestation. Canonical `metrics.json` SHA-256 is `2f1f39873f8b7ebd466a07d72610ffc7ae898481d430a013781039d43f6cb95d`; its internal payload digest and attested artifact descriptor match. Four canonical checkpoint sidecars match every reported SHA-256 and byte count:

| Sidecar | SHA-256 |
|---|---|
| base | `93663ba004343d4d507dcd1321a070117c62cdac0c4244afbb7ca84f8e2c2aec` |
| rebase | `86636a2c9c30a46e2b3037f37ea609e0b8bd5a3781afecb4314f6f1b42eed33c` |
| successor | `e9baee538caa240d66362a02e30925d834bc887d74c76833e9c0d974c7d1101a` |
| control | `5fdadbf65f1d0064f68b276e0b0766c077d3e3b3e6dcb89f6406c16ef7587cea` |

The preserved adjudication receipt SHA-256 is `474b4a8c3bf816f772096441566f0de6e2881113cbd66aa3fbf71f9a2a9763aa`.

## Scientific predicates checked from saved values

The control checkpoint shares the exact two-step base prefix; cursor/parameter records are 1/0.5, 2/1.0, 3/0.75. Rebase is at cursor 2 and successor generation 2 binds the rebase sidecar digest. Beam accepted histories are byte-equal at both cursors; shell history is byte-equal at cursor 2 and physically compared by layer at cursor 3. Direct-versus-optional-replay state digests match for rebase and successor. Cursor-3 accepted metric is `9.128e-13` and correction `1.745e-12`, each below `1e-11`.

| Recomputed saved-value maximum | Cursor 2 | Cursor 3 | Gate |
|---|---:|---:|---:|
| Paired pose, normalized | 0 | `4.40e-15` | `1e-9` |
| Paired force/moment, normalized | `1.39e-16` | `5.59e-10` | `1e-9` |
| Layer strain/stress, indexed normalized | 0 | `9.83e-15` | `1e-9` |
| Beam retained/section response, indexed normalized | 0 | `7.86e-15` | `1e-9` |
| Both-path and pairwise gap, absolute | `2.50e-16` | `1.86e-14` | `1e-9` |
| Free scaled residual and pair difference, absolute | `4.46e-14` | `9.13e-13` | `1e-11` |
| Finest assembled directional FD, scaled | `5.27e-9` | `5.28e-9` | `1e-6` |
| Finest isolated component FD, normalized | `9.26e-9` | `9.22e-9` | `1e-6` |
| Finest point-work FD, reference scaled | `2.59e-11` | `1.93e-11` | `1e-8` |

The four assembled FD rows decrease through the required first three halvings; dead-load derivative rows are exactly zero. Complete 12-port work parity and six eccentric compatible rigid zero-work modes are below `1e-8`. Force and moment closure were recomputed from each saved support reaction, support/tip position and fixed dead load about the common origin: cursor-3 maxima are `1.4694e-9` and `1.0907e-9` relative to fixed `F_ref=M_ref=sqrt(5)*1e-4`, below `1e-8`; cursor-2 values are smaller. The third-step beam rotation `1.461e-3`, support-force change `5.590e-5`, support-moment change `1.120e-4`, shell-work change `3.136e-7` and force-multiplier change `5.590e-5` exceed their registered nontrivial lower bounds. All seven negative cases have the expected `ValueError` or `SolveCancelled` reason and unchanged before/after accepted head and generation.

This audit verifies the preserved report and its recomputable formulas. Constitutive evaluations are supplied by the committed, hash-bound runner; the receipt is a bounded case result, not an independent proof of every operator outside this fixture.
