# F03 local scientific attempt B: failed evidence, preserved

23 September 2026. This was a separate one-use registration of corrected
candidate `f2c37945e39cdc06338a2f25221c07ad5d817f8e`. It does **not**
establish a passed scientific screen or G0B acceptance.

- Run archive: `C:/Github/ANYsolver/.perf2-worktrees/f03-local-scientific-20260923-b`.
  Registration SHA-256:
  `aab5be7599eb402259f8370f60456d6dbef882582201c311d44a84cddb8dbe61`.
  Aggregate receipt SHA-256:
  `ebea81a7239fd5a84ffc8691478c1e7b6c1c571010d22bf2bb1763b709ff8507`.
- The same isolated installed-candidate environment and explicit Numba cache
  were used. The pre-run F03 regression selection passed 1,338 tests with four
  Windows symlink-privilege skips.
- The coordinator consumed the registration. Q1_L0 produced its bounded
  mechanical artifacts but failed before writing `evidence_index.json` and a
  terminal receipt. The aggregate was sealed as `FAILED_EVIDENCE` for all five
  cases. This archive must not be rerun or modified.
- The child stderr records `BrokenPipeError: [Errno 32] Broken pipe` while the
  Windows no-follow evidence reader reopened `stderr.log`. The supervisor's
  parent process had opened that file for writing before child launch. Windows
  reported a sharing violation. The parent then rejected the changed log while
  trying to write the terminal receipt. This is an execution/evidence
  interaction, not a demonstrated mechanical failure.

The next candidate buffers the supervisor's already capped streams privately
and creates the two case log files exclusively after the child returns, before
terminal sealing. The child can inventory its own scientific files without an
open parent log writer. Focused coordinator, supervisor, and evidence-index
tests passed 46 cases with one Windows symlink-privilege skip. The complete
F03 selection passed 1,339 cases with four such skips. Independent read-only
review found no remaining actionable issue. A fresh registration is required
to assess this changed candidate. G0B remains open;
G1 remains barred.
