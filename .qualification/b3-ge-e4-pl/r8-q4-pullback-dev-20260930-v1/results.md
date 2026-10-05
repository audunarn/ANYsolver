# Selected Q4 pullback development result

Implemented: optional STIFFENED_SHELL_Q4_ALGORITHMIC_PULLBACK_V1 in the existing
GE point owner. Historical defaults and package versions remain unchanged.
Q4 uses the unchanged admitted local elastic/DNVC-C208 J2 law with D.T f and its
complete fixed-predecessor derivative, including owned-anchor chart corrections.
The selected policy binds model/checkpoint identity. ANYfem uses a separate v3
experimental record and exercises public construction, solve, checkpoint/restore.

Installed outcome: 91/91, exact solver and consumer wheels; all 384 solver and
97 consumer wheel Python modules byte-match their respective source worktrees.
All 215 loaded solver and 62 loaded consumer modules resolve to the isolated site.
Effective BLAS threads: one; JIT disabled. Guarded runtime 429.7569040999806 s;
observed peak process-tree RSS 241692672 bytes; limits 600 s and 8 GiB.
No performance gain or scientific foundation acceptance is claimed.

Checks include independent SciPy pose/work oracles, fixed yielded predecessors,
actual zero/nonzero anchored derivatives, stable sampled plastic branch masks,
Q4-only and mixed Q4/S3 yielded unload/reload with beam yielding, per-layer state,
force/moment balance, immutable anchors, accepted-prefix cancellation, distinct
model identity and restart. Existing chart, owner, S3 and legacy defaults regressions
pass in the same installed suite.

Raw source failures are retained. They were new-test assumptions about a four-item
assembly tuple, a preflight field and fresh-owner restore; no product correction
was required. Only the affected reference-identity check was repeated after repair.
F05 still needs assembled actively plastic selected-Q4/S3 derivatives and one-sided
yield checks. F06 broader chart/history and all aggregate gates remain open.
