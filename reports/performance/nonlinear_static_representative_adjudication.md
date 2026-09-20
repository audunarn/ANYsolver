# Representative nonlinear evidence: terminal adjudication

Raw evidence SHA-256: `48691e0557d9b57bcab378c20a87a84d8c9ebd8ab1693683c278030b15bc2d8c`.
Compressed raw-evidence SHA-256: `22a9edd80f3f6ff91a3498f445172032a535f5806ad4a77d2d40931f6baa957f`.
Adjudication helper runner SHA-256: `44d83a6d0889dee3364cfb6ade50c73add8a4ec0d8375349d7ac48ee12b5424b`.
The raw campaign and its exit-1 decision are preserved. This report applies two bounded adjudication corrections without rerunning any solve.

## Performance

| Case | Baseline median (s) | Candidate median (s) | Reduction | Physics |
| --- | ---: | ---: | ---: | --- |
| easy_elastic_shell_control | 0.351579 | 0.342140 | 2.68% | PASS |
| large_deflection_shell_holdout | 5.344808 | 4.775538 | 10.65% | PASS |
| nonsymmetric_follower_shell_holdout | 6.330069 | 6.390719 | -0.96% | PASS |
| plastic_s3_reversal_holdout | 10.900443 | 8.695636 | 20.23% | PASS |
| prescribed_mpc_beam_holdout | 0.032404 | 0.027793 | 14.23% | PASS |

## Cost accounting

All values are medians across the seven alternating pairs; memory is peak process-tree RSS.

| Case | Revision | Complete route (s) | Assembly | Tangent | Residual only | Linear solves | Failed work | Peak RSS (MiB) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easy_elastic_shell_control | baseline | 0.351579 | 40 | 30 | 10 | 20 | 0 | 241.0 |
| easy_elastic_shell_control | candidate | 0.342140 | 30 | 30 | 0 | 20 | 0 | 217.7 |
| large_deflection_shell_holdout | baseline | 5.344808 | 120 | 100 | 20 | 80 | 0 | 216.4 |
| large_deflection_shell_holdout | candidate | 4.775538 | 100 | 100 | 0 | 80 | 0 | 217.8 |
| nonsymmetric_follower_shell_holdout | baseline | 6.330069 | 30 | 24 | 6 | 18 | 0 | 217.5 |
| nonsymmetric_follower_shell_holdout | candidate | 6.390719 | 24 | 24 | 0 | 18 | 0 | 219.4 |
| plastic_s3_reversal_holdout | baseline | 10.900443 | 89 | 69 | 20 | 49 | 0 | 215.8 |
| plastic_s3_reversal_holdout | candidate | 8.695636 | 69 | 69 | 0 | 49 | 0 | 216.1 |
| prescribed_mpc_beam_holdout | baseline | 0.032404 | 44 | 32 | 12 | 20 | 0 | 180.1 |
| prescribed_mpc_beam_holdout | candidate | 0.027793 | 32 | 32 | 0 | 20 | 0 | 180.5 |

## Globalization

| Case | Residual-decrease (s) | Armijo (s) | Evidence |
| --- | ---: | ---: | --- |
| large_deflection_shell_holdout | resource limit | resource limit | resource_terminal_no_solution |
| nonsymmetric_follower_shell_holdout | 11.946103 | 11.864198 | completed_samples |
| plastic_s3_reversal_holdout | 10.346621 | 10.491107 | completed_samples |

## Decision

- Evidence completeness: **PASS**
- Representative performance: **GO** (12.44% median reduction)
- Easy-control change: **2.68% faster**
- Armijo promotion: **NO-GO**

The performance gate passes. Armijo remains experimental: it added no difficult solve, did not reduce failed work, and both searches exhausted the warm-solve limit on the 90-degree consistent-tangent shell.

## Adjudication corrections

- `legacy-follower-diagnostic-compatibility`: Baseline lacks the candidate-only external_load_reduction.preprojected diagnostic; exact physical equality and all other frozen follower predicates are required before treating the legacy observation as current-load compliant.
- `resource-terminal-physical-not-applicable`: When both globalization methods terminate at a registered resource limit before producing a solution, the difficult-case attempt is complete NO-GO evidence and physical comparison is not applicable.
