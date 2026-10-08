# F03 Q6 three-grid saved-input certificate rehearsal

**24 September 2026. Unregistered source-process diagnostics. F03/G0B remain
open; G1 remains barred.** The same committed certificate producer and
saved-only replay (`af5ba8d3`) ran serially for the fixed X0/X1/X2 grids.
Only evidence and ignored-archive paths changed between runs. Each producer
saved a bounded canonical scaled KKT matrix/RHS, physical coordinate scales,
candidate state and every inverse column. Each replay consumed only those
saved inputs: no model assembly, factorization or equilibrium solve.

| Grid | KKT order / inverse columns | Source elapsed / peak RSS | Replay elapsed / peak RSS | Diagnostic condition upper | Amplified backward upper |
|---|---:|---:|---:|---:|---:|
| X0 | 3,289 / 3,289 | 297.28 s / 328,466,432 B | 196.33 s / 256,921,600 B | 624606.8922703825 | 7.458894411015157e-10 |
| X1 | 4,405 / 4,405 | 527.75 s / 470,347,776 B | 374.57 s / 347,074,560 B | 646745.140539819 | 7.911937515884004e-10 |
| X2 | 5,893 / 5,893 | 927.41 s / 691,101,696 B | 671.62 s / 497,348,608 B | 716122.4783910362 | 9.032413569067423e-10 |

All six [source X0](B3_GE_E4_PL_G0_F03_Q6_X0_SYSTEM_ARCHIVE_REHEARSAL_20260924/measurement.json),
[X1](B3_GE_E4_PL_G0_F03_Q6_X1_SYSTEM_ARCHIVE_REHEARSAL_20260924/measurement.json),
[X2](B3_GE_E4_PL_G0_F03_Q6_X2_SYSTEM_ARCHIVE_REHEARSAL_20260924/measurement.json)
and [replay X0](B3_GE_E4_PL_G0_F03_Q6_X0_SAVED_REPLAY_BOUND_REHEARSAL_20260924/measurement.json),
[X1](B3_GE_E4_PL_G0_F03_Q6_X1_SAVED_REPLAY_BOUND_REHEARSAL_20260924/measurement.json),
[X2](B3_GE_E4_PL_G0_F03_Q6_X2_SAVED_REPLAY_BOUND_REHEARSAL_20260924/measurement.json)
routes have completed exit-zero supervisor receipts. For each pair, the raw
archive and inverse SHA-256 values match the source measurement, the parent's
attempt source hash equals the child's consumed-measurement hash, and the
replayed certificate dictionary exactly equals the source. All three report
`CERTIFIED_WITHIN_LIMIT` **as a diagnostic status**. The X2 inverse and
canonical KKT/RHS hashes repeat the earlier bound-system X2 rehearsal.

The strict source archives occupy 19,288,414 / 32,656,126 / 49,788,494 B;
the complete inverse archives occupy 86,540,168 / 155,232,200 / 277,819,592
B. These raw numerical files are locally retained and Git-ignored; tracked
measurements preserve hashes and inventories. X0's earlier replay attempts
remain intact, with the final bound replay selected here. Focused storage,
archive and certificate tests passed 50/50 before the X1/X2 runs, with no
product code change afterward. A separate [independent conditional arithmetic
review](B3_GE_E4_PL_G0_F03_Q6_INTERVAL_ARITHMETIC_REVIEW_20260924.md)
found no local compiled-path counterexample, but does not constitute an
installed scientific proof.

This establishes **three-grid source-level saved-input reproducibility and
resource feasibility**. It does not establish an installed one-use identity,
independent compiled arithmetic proof, primal positivity, physical-observable
error propagation, the full signed/functional/spatial three-grid adjudication,
or native beam/shell interface mechanics. No G0 acceptance or speedup is
claimed. A formal registration must use fresh exact installed artifacts and
the complete acceptance matrix.
