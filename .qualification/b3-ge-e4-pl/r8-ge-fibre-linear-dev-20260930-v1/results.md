# Verified experimental native fibre-linear solver/consumer slice

Solver product `6b0b1131a9dcf055811901d55daabac049a4e2a0`; wheel SHA-256
`56deb65e27dd29abe94aec44e514276b10e1fef78ba91078dfe3df8d68358add`.
ANYfem runtime remains `a615c4b299e603264f67d292c8a4415168b1b9c6`;
tests-only follow-up `69184db3bc7e6ccdde0c7e1642fc6bb78afd7cf8`.
Consumer wheel `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`.
Both exact artifacts are retained in `solver/wheels/`.

The existing sparse GE point owner now accepts virgin reference-linear physical
axial/biaxial-fibre sections and mixed generalized/fibre members with Q4/S3.
Native equations/18+24 variables stay unchanged; the existing virgin section
derivative supplies scales only. Linear recovery, JSON/binary restart, compatible
loads and factor reuse operate. The example adds physical_fibre/mixed options,
keeping its generalized default. ANYfem's existing experimental v1 record
round-trips opaque raw/SHA native definitions without runtime edits.

## Checks

- Source52/52 plus added binary/cancel and corrected line-negative checks.
  Initial restore-negative fixture used a nonfresh owner; initial line-negative
  fixture had invalid trace length. Both failed logs remain. Source52 predates
  the two extras/public alias edit and is development evidence.
- Fresh installed solver54/54 (10 new,21 linear,23 finite), no skips/errors/
  failures,197.27s; guard202.6734299s,239112192B,exit0. Five frozen inputs,
  exact manifest/runners in `solver/`; command `python -u run_bounded.py`.
- Three installed headless families: equilibrium<=1.351e-13, gap<=1.671e-19,
  support-Z error<=1.43e-11N, exactly doubled tip and one factorization.
- Consumer source2/2; separate installed2/2,.71s; guard4.1212406s,206434304B,
  exit0, no skips/errors/failures. Exact record/native raw roundtrip, fresh
  solve/restore and2x continuation/factorization1. Two frozen inputs, input
  records and both reports are preserved under `consumer/`.
- Both runs observe Python3.14.2, BLAS pools one thread, JIT off,600s/8GiB guard.
  All384solver+97consumer source/wheel/site modules match;268solver-run and
  267consumer-run imports resolve onsite. Dependencies/settings, build/install
  logs, runners, hashes and JUnit inventories are retained.

Independent code/mechanics/artifact/consumer review has no unresolved finding
within this slice; see `review.md`. This is verified Level-A experimental use,
not a foundation/milestone qualification or performance claim. Matched elastic
sections share inherited mechanics. Finite fibre histories/stresses, line+fibre,
ordinary native projects, external comparisons, scale/platforms and complete
release remain open. Added cancellation coverage is before work, not during
factorization. Generalized-only finite behavior and legacy identities remain.
