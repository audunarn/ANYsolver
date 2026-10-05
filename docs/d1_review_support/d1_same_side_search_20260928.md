# D1 same-side overlap pruning: bounded development evidence

**Question.** Could the 16×8 fine-Q1 near-rim coupled case be made cheaper
without changing its contact mechanics or weakening duplicate-surface
rejection? The prior no-checkpoint solve took 113.18 s. One matched instrumented
replay found 55.05 s in ordinary pair geometry and 41.90 s in Jet2 pair work.
A saved accepted-pose profile attributed 5.08 of 7.86 s in one ordinary
geometry evaluation to the quadratic same-side overlap check.

**Change.** Every Q4/S3 face is still validated at the candidate pose. For
each first face, current vertices are projected onto its tangent/binormal
plane. A later face is skipped only when its projected coordinate interval is
separated by more than a 64-epsilon global-length margin on an axis. Possible
overlaps still use the original exact clipping and area threshold. This is a
conservative pruning rule; the loop still scans face pairs and makes no
subquadratic search claim.

**Identity and raw records.** Both matched runs used the same
`scripts/general_contact_d1_profile_coupled.py` blob
`21460d63cf8f2994f8e365f80e8fbeb719b2e214`, Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1, the same 16×8 `near_rim8` fine-Q1 fixture, 32-pivot
`block_response_dev` solver, no checkpoint, and the 180 s/1-GB process cap.
`PYTHONPATH` selected this worktree's `src` and scripts. The old overlap file
was HEAD `8ac42c56` blob `1eeb5e0b83c1ef6b61e377038542708d12a08644`;
the edited blob was `8d2add4422ecaccf669e3d179f045efc4bca9c2a`.
The [old result](d1_same_side_profile_before_20260928.json),
[new result](d1_same_side_profile_after_20260928.json), and
[old](d1_same_side_profile_before_resource_20260928.json)/[new](d1_same_side_profile_after_resource_20260928.json)
process resource records are retained. A first profiling attempt used the
script's old direct-solver/pivot defaults and stopped at a pivot limit before
any accepted step. Its [failure log](d1_same_side_mismatched_preflight_failure_20260928.txt)
is retained; the matched replay used the saved case's actual settings.

| Measured quantity | Old | Edited |
|---|---:|---:|
| Instrumented solver elapsed | 125.56 s | 82.07 s |
| Complete process elapsed | 127.41 s | 83.77 s |
| Ordinary pair geometry, 12 calls | 55.05 s | 25.00 s |
| Jet2 pair work, 1553 calls | 41.90 s | 40.15 s |
| Peak process-tree memory | 495.24 MB | 493.67 MB |
| One saved-pose ordinary geometry under cProfile | 7.86 s | 3.07 s |

The saved displacement array, contact result object and accepted step counters
are exactly equal in the two JSON records. The saved pose has 148 positive
overlap pairs and 1184 integration triangles in both runs. The
[old](d1_same_side_saved_pose_before_20260928.txt) and
[edited](d1_same_side_saved_pose_after_20260928.txt) call profiles retain the
function counts. This single matched route shows a 1.53× lower measured solver
time, not a repeatable whole-route speed estimate.

Independent read-only review found no concrete false-negative overlap or
newly admitted invalid face. The reviewer confirmed the projected-vertex
bound and exact mechanical/result parity, noted that pair scanning remains
quadratic, and requested near-touch numerical coverage. The focused test
compares with a separate exhaustive pre-search algorithm for rotated Q4/S3
scenes, a remote overlap, an invalid face and two large-coordinate near-touch
cases. It passed 11/11. The earlier focused patch run, before the two
near-touch cases were added, gave 16 passed/2 opt-in skipped, and the
changed-source four-Q4/two-S3
[eight-step split-restart test](d1_same_side_cycle_test_20260928.txt) passed
within [61.11 s/399.13 MB](d1_same_side_cycle_test_resource_20260928.json).

This is development cost and parity evidence. It does not qualify coupled
pressure-space stability, a larger spatial mesh, general boundary features,
or final D1 acceptance. The next spatial-evidence design must respect the
remaining 180 s/1-GB development cap; this one optimization does not by
itself justify an unpreflighted 32×16 coupled solve.
