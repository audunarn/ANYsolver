# F03 classical upper-size assembly screen

22 September 2026. This is a **preflight assembly resource screen**, not a registered loaded comparison, factorization, convergence study, native B3-GE/E4-PL qualification, or proof that all 96 proposed cases fit the full job budget. The independently reviewed supervisor source was frozen in commit `e832ae3fadb98a8c337f9740258ba8c8369a67fb`; both runs used a clean isolated integration checkout, a one-thread child, the proposed largest mesh `(Ns,Ny,Nb,Nm)=(128,64,512,64)` and P1. The screen retains each single-use manifest, phase log, sampled RSS, stderr and result:

| Topology | Raw evidence directory | Shell nnz | Trace shell nnz | Support-eliminated KKT dimension / nnz | Complete-route assembly time | Sampled peak child RSS |
|---|---|---:|---:|---:|---:|---:|
| Q4 | `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-classical-upper-q4-v1/` | 593,668 | 12,352 | 36,418 / 669,509 | 5.936 s | 201,699,328 B |
| CST | `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-classical-upper-cst-v1/` | 462,596 | 11,312 | 36,418 / 537,381 | 5.530 s | 213,946,368 B |

Both supervisor results report process exit 0, all six phases from child identity through unfactorized KKT, no malformed phase lines, empty stderr, actual proposed-inventory identity and a clean source. The observed values are below the screen limits of 8 GiB sampled child RSS and 900 seconds per case. The support-eliminated KKT dimension is smaller than the 36,681 unconstrained combinatorial dimension; this is expected because shell outer-edge and beam-root coordinates are prescribed.

The supervisor's source/thread/phase and final-limit checks were independently reviewed before execution. A separate read-only audit of both raw directories **passed for this assembly-only scope**: all five source SHA-256 identities agree across the on-disk frozen source, manifest, child identity and post-check; Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1 and psutil 7.2.2 module paths were recorded; OpenBLAS reported one thread. Manifest SHA-256 values are `3c3254334b706a267812267c95b94849b090f1272a68ee8042cf698d5741d7f9` (Q4) and `10977922bbf20c14130db3c8047541b9a42de4023ce5c369d4d86b4fb99f59ab` (CST). The auditor independently reconciled 36,681 unconstrained variables minus 263 supports with the 36,418 KKT dimension. Sparse `nnz` may include explicit zeros.

This screen does **not** measure factorization fill, RHS/solve, full gap enclosure, rank/stability, external agreement, all inventory variants, or a nonlinear production model. It establishes only that these two upper-size classical assembly routes completed within the declared preflight envelope. F03 remains in progress, G0B open, and G1 barred.
