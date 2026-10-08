# F03 local scientific attempt C: completed execution, failed evidence

23 September 2026. The third one-use attempt used clean committed candidate
`a721400963ccf674f5e78c217447d5ab74cadf03` and the isolated installed
ANYsolver 0.4.7 environment. It completed all five coordinator launches, but
does **not** establish a passed F03 screen or G0B acceptance.

- Run archive: `C:/Github/ANYsolver/.perf2-worktrees/f03-local-scientific-20260923-c`.
  Registration SHA-256:
  `f351ce7a6091e5b4e1b332a725e52b4e93156790397144899a2160f2a97b2249`.
  Aggregate receipt SHA-256:
  `a37f3a27c0a82558d20844d3222822005278c5b2759f858c6e43a36b40ed0b95`.
- The aggregate status is `FAILED_EVIDENCE`. Every case has a terminal and a
  failed case receipt. The run is consumed; do not rerun or modify it.
- Q1_L0 exited normally and wrote an evidence index. Saved-only adjudication
  then failed because its private lifecycle snapshot lacked `stdout.log` and
  `stderr.log`, although terminal validation requires those bounded files.
- Q1_L1 and Q2_L0 children failed at the exact-rational equilibrium resource
  cap. Q1_L2 failed at the saved six-block composition envelope. Q2_L1 failed
  at the combined sparse-pattern envelope. Their missing evidence indexes were
  reported by closure as `F03 evidence index exceeds declared bound`; this is
  a generic reader message for an absent index, not proof that serialized
  index bytes exceeded one MiB. The child stderr files preserve the actual
  first failures.

The lifecycle snapshot defect and the resource-cap failures are separate.
The latter need measured, justified case/budget reconciliation under a new
registration; numerical thresholds and failed observations must not be
silently relaxed. G0B remains open and G1 remains barred.
