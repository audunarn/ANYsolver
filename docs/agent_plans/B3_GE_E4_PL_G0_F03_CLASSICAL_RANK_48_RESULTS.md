# F03 independent classical coupling: 48-case algebraic rank preflight

22 September 2026. The load-independent support-eliminated coupling matrix `C=[-Cs_free,Cb_free]` was assembled for each of the **12 proposed mesh tuples × Q4/CST × P0/P1 = 48** distinct interfaces. Source `49608b0cc90ba006fa02e903b5e51046a2977653` was clean and frozen before the single supervised execution. The source, case inventory, `1e-6` singular-ratio floor, one-thread environment, 8 GiB child RSS, 900 s/case and 7,200 s total limits were bound in the manifest. The observable is the smallest/largest singular ratio of **row-Euclidean-normalized C**, computed from the row Gram matrix; a direct SVD is required near the floor. This is an *algebraic row-rank screen*, not a physical inf-sup measure.

Immutable raw evidence: `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-classical-rank-48-v1/` contains manifest, 98-record JSONL stream, sampled RSS, stderr, and terminal result. SHA-256: manifest `8b9acf960c23191dc155603f6b475fa7d3465bcb55f9b4d3a46980fc83605816`; records `f359b4a7cdbbfc05287de5529c65caf680b84a4b5b9ecefc8ab5927c85f7b93f`; result `d936dba7ebdd3358a7c0e698df4394f7969f05447736085d6b9e34ea1fb2b63f`.

The independent read-only audit passed: manifest/child/terminal/post hashes agree with the frozen on-disk sources; actual two OpenBLAS pools had one thread each; the stream has identity, every ordered start/result pair, and a complete record. There are no malformed records, failed cases, or stderr entries. Exit 0; elapsed 63.842 s; sampled peak RSS 125,476,864 B; slowest individual case 3.580 s. All 48 cases have finite positive row norms, the expected multiplier row counts, and ratios above the frozen floor. No direct-SVD fallback was needed because the minimum was `0.14122798748888937`, more than 141,000 times the cutoff.

| Topology / law | Minimum ratio | Maximum ratio |
|---|---:|---:|
| Q4 / P0 | 0.379155629 | 0.752534037 |
| Q4 / P1 | **0.141227987** | 0.464050627 |
| CST / P0 | 0.466661812 | 0.757429368 |
| CST / P1 | 0.256923441 | 0.467943762 |

The weakest row ratio occurred at Q4/P1 `(Ns,Ny,Nb,Nm)=(32,32,256,32)`. Preserve the unfavorable one-axis trend: with fixed `(Ns,Ny,Nb)=(64,32,256)`, increasing `Nm=16→32→64` reduced Q4/P1 `0.464051→0.385047→0.264906` and CST/P1 `0.467944→0.396473→0.308720`. At fixed `(Ns,Ny,Nm)=(64,32,32)`, `Nb=128→256→512` reduced Q4/P1 `0.417763→0.385047→0.339058`. In contrast, the four joint Q4/P1 levels were `0.381434,0.414059,0.385047,0.397962`; no collapse appears over these finite joint levels. P1 ratios are lower than P0 and Q4 lower than CST across the registered tuples.

**Disposition:** the registered 48-case *algebraic* preflight passes. It neither selects the production multiplier space nor establishes norm-scaled stability, a convergent loaded physical response, continuous-gap acceptance, signed KKT behavior, external agreement, or a native B3-GE/E4-PL coupling law. F03 remains in progress, G0B open and G1 barred. The next reference step needs a frozen physical gap/response normalization and an independently reviewed loaded-comparison supervisor; adverse rank trends must remain visible in that decision.
