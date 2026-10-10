# M23 — barge-scale criteria, MPC holdout, node-envelope criteria, S2b profile

2026-10-09. Owner: Claude (Anthropic). Product source unchanged (M22 final).
New criteria C8a, C8b and the C5 associated-field extension, plus holdouts A5-L
and B1, were frozen in the living note before any M23 measurement.

## Holdout assessment (`.prepared-static-evidence/m23-assessment-01.json`): GO

All eight holdouts (A1-L, A2-L, A3-L, new A5-L, A1-A4) pass C1-C8. The MPC
holdout A5-L (supported S3, two MPC equations on node 4, compiled loads)
exercises the master-equivalent part of C4' (worst 0.000093 of the limit) and the
reaction envelopes (288 node-envelope entries). Node envelopes and associated
fields pass everywhere (largest: A3 432 node entries, 29,520 associated entries).

## Barge B1 (`../../evidence/m23-barge-assessment-01.json`): GO

Eight pre-registered samples, every recovered element and every node:

| Criterion | Entries | Failures | Worst ratio to limit |
|---|---:|---:|---:|
| C2 linear stresses | 3,414,240 | 0 | 0.0025 |
| C3 derived stresses | 322,720 | 0 | 0.00017 |
| C4' reactions, all buckets (7,560 master-equivalent) | 17,128 | 0 | 0.000094 |
| C5 stress envelope (identity differences: 0) | 41,400 | 0 | |
| C8 node envelopes (identity differences: 0) | 313,128 | 0 | |
| Associated fields | 354,528 | 0 | |
| C7 compiled versus native load | 8 cases | 0 | 0.0022 |
| C1 displacement versus native direct solve | 8 cases | 0 | worst 6.6e-15 absolute |

The reconstructed displacement at the 18 output DOFs is bitwise equal to the
route's emitted values; all eight samples reconstructed with compiled loads and
no fallback. Run m23-claude-02-barge-b1, 110.18 s.

## S2b profile (`../../evidence/m23-profile-cases/cases.pstats`)

40 vectorized barge cases, block 4, profiled case time 7.2 s (real about 0.14 s
per case):

| Cost | Profiled s | Share |
|---|---:|---:|
| Per-constraint records of the selected full diagnostics (about 7,200 MPC equations per case, record dicts, per-constraint norms, compaction) | about 2.8 | 39% |
| Per-case metadata copies (pickle) | 0.75 | 10% |
| Native authority checks per block | 1.05 | 15% |
| ANYfem original-time wet-pressure resolution | 0.65 | 9% |
| Thread-pool setup per block (threadpoolctl) | 0.27 | 4% |
| Vectorized stresses and envelope folds | about 0.35 | 5% |

The earlier expectation that metadata copies dominate was wrong: the model-wide
per-constraint records do. Both exist only because selected reactions request
full diagnostics. Lean selected-reaction output (reaction maps unchanged, no
model-wide records, norms or metadata copies unless requested) would remove about
half of per-case time, roughly 0.14 to 0.07-0.08 s per case; this amends adopted
contract item 7 ("full residual diagnostics") and needs the owner's decision.
Per-block costs (authority checks, thread-pool setup, about 19%) shrink with a
larger block size, which is a caller setting within the memory policy.

## Resources

Assessment checks 121.89 of 600 s (m23-claude-01-assessment 11.71, B1 110.18);
profiling epoch m23 100.15 of 300 s. No product edits, no Git operations.

## M24 — lean selected reactions (opt-in), implemented and benchmarked

`prepare_static_response_evaluator(..., stress_execution="certified_vectorized",
selected_reaction_diagnostics="lean")` (also through the ANYfem factory). Selected
case results keep `reactions` and the three force maps (filtered to the selected
nodes) with `constraint_forces["diagnostics"] = "lean_selected_reaction_maps"`;
the residual vector, norms, per-constraint records and metadata copies are not
produced. Default `"full"` is unchanged; other routes refuse `"lean"`.

Verification: on the MPC fixture lean reactions, force maps, stresses,
displacements and envelopes are bitwise equal to full mode; frozen C1-C8 pass with
lean on A1-L, A3-L, A5-L and A4 (`m24-assessment-01.json`, GO); solver regression
119 of 122 (pre-existing authority tests only). Checks 60.80 of 150 s.

Barge (epoch m24, 349.57 of 600 s), 300 cases, lean consumed output:

| History | Built model to output | Preparation | Case evaluation | Recovery phase |
|---|---:|---:|---:|---:|
| Lean, primary | 104.8 s | 86.5 s | 14.7 s | 5.0 s |
| Lean, holdout | 107.1 s | 88.7 s | 14.7 s | 4.9 s |
| Full diagnostics, primary (control) | 129.6 s | 86.3 s | 39.2 s | 27.6 s |

Against the M22 canonical runs (588.1 / 568.8 s): 5.61x primary, 5.31x holdout.
The full control ran about 7% faster than the identical M22 vectorized run
(machine drift), so a same-session canonical comparator would likely give about
5.2x / 5.0x. Lean, full-control and M22 vectorized histories and envelopes are
byte-identical (primary and holdout). Per case: about 0.05 s evaluation; preparation
is now about 82% of a 300-case workload. Projection only: 10,000 cases about
12 minutes lean versus about 4.6 hours canonical.
