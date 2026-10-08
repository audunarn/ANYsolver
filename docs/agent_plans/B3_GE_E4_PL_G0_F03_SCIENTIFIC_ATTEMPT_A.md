# F03 local scientific attempt A: failed evidence, preserved

23 September 2026. This is the first one-use execution of the frozen five-case
F03 local scientific protocol. It is **not** a passed scientific screen or G0B
acceptance.

- Registered candidate: `ba0196cad1f7df017cd063b632d6166e7e7a5f3d` on
  `codex/b3-ge-e4-pl-integration`; accepted main and `origin/main`:
  `be41a77a62e1cd7e1767bda6e955253af0819f91`.
- Run archive: `C:/Github/ANYsolver/.perf2-worktrees/f03-local-scientific-20260923-a`.
  Registration SHA-256:
  `658cda1511ee46bc21e105c994861bf10542b1dbaf4c47169adb4a8f60a41c53`.
  Aggregate receipt SHA-256:
  `7fd5c5e873570b3fa29c4f88f3f1e29b498f6added99fe3ecb5bf8fe87909f5e`.
- The source was installed into the isolated `.venv`; the effective imported
  ANYsolver source was this candidate worktree, with metadata version 0.4.7.
  Numba used the explicit cache under `.venv/numba_cache`. The installed
  pre-run focused selection passed 356 tests with four Windows symlink-privilege
  skips.
- The one-use coordinator claimed and consumed the registration. It stopped
  after Q1_L0. The aggregate status is `FAILED_EVIDENCE` for all five cases
  because terminal receipts were absent. Do not rerun or modify this archive.
- The Q1_L0 child stderr identifies a separate first failing operation:
  `_b3_e4_f03_local_scientific_sparse_storage.py:92` compared empty CSR slices
  with shapes `(0,)` and `(3071,)` while writing operators. The coordinator's
  terminal writer then raised `F03 terminal process does not own its start
  marker`: on Windows the isolated `.venv` launcher PID differs from its Python
  child PID. The missing terminal receipts are thus an evidence-path failure,
  not a demonstrated mechanical discrepancy.

The next source revision fixes both defects. Sparse validation skips pairwise
ordering only for rows or columns with fewer than two entries. The lifecycle
records and verifies the child parent PID, then applies one ownership rule to
terminal writing, terminal reading, case adjudication, aggregate adjudication,
and cross-case snapshots. The start and terminal schemas advance to v2, so
attempt A's v1 markers cannot be mistaken for a new run. A focused installed
selection passed 76 tests; the broader F03 selection passed 1,338 with four
Windows symlink-privilege skips. Independent read-only reviews found no
actionable issue in the sparse or lifecycle fixes.

These fixes qualify a new candidate for a **new** one-use registration, not
attempt A for reinterpretation. G0B remains open and G1 remains barred.
