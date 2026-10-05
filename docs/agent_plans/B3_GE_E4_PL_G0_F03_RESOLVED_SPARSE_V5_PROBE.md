# G0 F03 independent comparator v5: registered large refinement

21 September 2026. This is a **source-bound exploratory comparator
registration before execution**, not F03/G0B acceptance. Its source is
`scripts/probe_b3_ge_e4_pl_g0_f03_resolved_sparse_v5.py`, the single-use
runner `scripts/run_b3_ge_e4_pl_g0_f03_resolved_sparse_v5.py`, and the
frozen v4 classical membrane/Timoshenko source plus its independent
membrane operator. The runner hashes all four files, source revision,
the old v4 manifest and records, and the installed numerical versions.
Exclusive output root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-resolved-sparse-v5/`.

## Physical idealization and inventory

Use the same 1 m bonded interval, .2/.23 m four-point shell pose,
homogeneous exact-static conventional Timoshenko beam, classical plane
stress Q4/CST panels, boundary supports, smooth positive or signed sine
distributed load, material/section values and finite **station** ties as
v4. The new implementation assembles the same shell trace into sparse
rows. Eight small Q4/S3 × smooth/sine × 4/8 cases must reproduce the v4
matrix `nnz`, station poses, interface work, energy/support moment and
polynomial gap estimates within registered parity bounds before new
cases execute.

The 16 frozen cases, serially ordered, are:

1. Q4 and S3-V2D, smooth and sine, `(Ns,Ny,Nb)=(64,64,64)` as four direct
   sparse anchors against the immutable v4 records.
2. The same four cases at `(96,96,96)`, before any larger case.
3. The same four cases at `(128,128,128)`.
4. Q4 and S3-V2D, smooth load, `(128,64,128)` and `(128,128,64)` as
   four crossed width/beam-resolution controls.

The historical v4 `records.jsonl` SHA-256 is
`82d53a2487db070717113c3dd3a87ddc1ae9b21bfa326739784679b8ef449d83`;
the frozen source SHA-256 is
`5d067469ed5248f6039108fae611d778deeb428074daa58bc298118ac6409fd3`.
The original v4 run is not altered. No new case uses its output as a
constraint or target in the equations.

## Checks and disposition

The small parity check requires equal matrix `nnz`/constraint counts,
station pose and gap extrema absolute differences ≤`5e-11` m/rad, and
selected physical work/energy/moment normalized differences ≤`1e-9`.
All case records include beam/shell station poses, tip response, energy,
support force and moment, interface work, exact station residual and
floating-point extrema of the *discrete homogeneous field* gap.

For each topology and load, compare joint 64/96/128 tip displacement,
all nine station poses, shell and beam energy, support balance and work,
and the physical-scaled maximum of both translation gaps and `.46 m`
times yaw gap. Compare each smooth crossed case with the joint 128 case.
First directly compare the four new n64 records to their matching v4
joint records for tip, station poses, energy, reactions/work and gap
estimates; a mismatch bars use of a combined refinement trend.
An **even locally resolved comparator** requires tip and nine-station
relative changes from 96 to 128 below 1%, energy changes below 1%,
both crossed-tip changes below 1%, decreasing refinement differences,
force/moment/work discrepancies ≤`1e-8` in the frozen physical scales,
and physical-scaled maximum gap ≤1% of the joint 128 tip-motion scale.
Normalize a tip difference by `max(abs(tip128),1e-6 m)` and a station
displacement/rotation difference by the maximum physical scaled tip or
station value and `1e-6 m`. Record the separate component changes and
absolute values; no near-zero denominator alone can pass. If any
predicate fails, say the comparator is unresolved under this inventory.

The runner sets one BLAS thread, a 1,800 s per-case and 7,200 s overall
wall limit and a **sampled child RSS** limit of 24 GiB at .5 s polling.
This is cooperative supervision of its owned subprocess, not a hard
whole-process-tree memory limit. Stop after a resource-limit case, retain
its exit/child stdout/stderr and every completed record. Preserve any
numerical failure too. The evidence cannot be overwritten or rerun as
the same registered source/root.

Even if this comparator converges, it remains finite-station collocation,
not continuous exact multiplier coupling. Classical Q4/CST differ from
the E4-PL shell, and the conventional beam differs from native retained
B3. Its beam interior omits the load particular solution, and its gap
extrema are numerical estimates, not certified enclosures. It can inform
a physical target only with a documented idealization map and independent
review. The required native line-law stability, physical gap/work,
six-channel torque/shear and external comparisons remain open.
