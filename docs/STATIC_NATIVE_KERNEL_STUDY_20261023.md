# Static path native-kernel study (2026-10-23)

Base: claude/t34-merge-20261022 (953d189a3). py -3.14, OMP_NUM_THREADS=1, single machine.
Harness: `scripts/benchmark_static_native_study.py CASE [--profile]` (cold JIT pass, timed warm pass,
SHA-256 of result arrays). Raw profiles/digests are outside the repo (C:\ANYworkspaceWork\static-native-bench).
Investigation only: no solver source changed.

## Identity baseline (warm wall, hash of displacement/stress bytes)
| case | wall s (2 runs) | hash | note |
|---|---|---|---|
| lin_plate 24x24 Q4, p=1e4, 3750 dof | 3.96 / 4.04 | 7222baada3fcea0a | solve 1.9 s + recovery 1.9 s |
| nl_elastic_plate 12x12 von_karman 5 steps | 1.44 / 1.47 | 8fe7761492c5e055 | 15 Newton it |
| nl_plastic_plate 6x6 t=.005 p=3e4 | 0.75 / 0.72 | 5bee6d38c6b38e1c | 31 it |
| stiffened_beam_shell (examples/beam_shell_coupling.py) | 1.21 / 1.16 | 0153b9608e69923f | 30 it |
| arc_panel 6x6 shallow, 25 steps | 14.0-18.7 | 5143840cb56fe3a3 | wall noisy ~30% (unexplained), hash stable; maximum_steps_reached |
| prepared_envelope (mixed_free_model, 4 cases) | 0.57 / 0.64 | ce0eb52265a73eeb | |

## Ranked profile (share of profiled tottime; profiler roughly doubles wall)
Dominant in every case: per-call authority/guard/lifecycle checking on the qualified route, not numerics.
| function | lin | nl_el | nl_pl | stiff | arc | prep |
|---|---|---|---|---|---|---|
| e4_pl_element.formulation_class_guard (:7672) + genexpr (:7682) | 17.7 | 14.9 | 10.5 | - | 13.0 | 17+ |
| _require_authority_array_metadata (e4_pl_s3_state:424) | 5.0 | 3.9 | 2.9 | - | 3.7 | 4.9 |
| _require_q4_quadrature_instance_authority | 4.1 | 4.8 | 3.7 | - | 4.4 | 3.9 |
| _static_mro_attribute / instance_guard | 6.3 | 6.3 | - | - | 2.7+ | 6.1 |
| e4_pl_s3_state signature + _canonical_value (seal) | - | 8.0 | 13.9 | 17.8 | 4.0 | 4.2 |
| list.sort (canonical JSON) | - | - | 2.2 | 8.1 | - | - |
| _compensated_contractions (already Numba) | 5 | - | - | - | 12.5 | - |
| corotational.py + _corotational_batch.py | - | - | - | 18 | - | - |
Module aggregates: e4_pl_element.py 36-58% (7% stiffened), e4_pl_s3_state.py 6-23%, numpy 5-19%.
matrix_assembly.py/nonlinear_reduced_assembly.py have near-zero tottime.

## Linear algebra and pattern reuse (measured)
splu cumulative: 0.2% (lin_plate 13 ms), 0.06 s over 11 calls (nl_elastic), 0.013 s over 26 (nl_plastic),
0.029 s over 51 (arc), 0.002 s (stiffened). Factorisation is negligible at these sizes, so the symmetric-mode
SuperLU (diag_pivot_thresh) idea and symbolic-factorisation/sparsity reuse have no headroom here
(<1% of any case); not pursued, not adopted. (Large-model PARDISO regime >10k DOF not measured here.)

## Compilable vs not
- Not compilable (Python introspection of classes/MROs, lifecycle scans, canonical-JSON seals): the top rows above,
  ~40-60% of the time. Speeding them up means caching/relaxing guards or a new seal format: a governance decision
  (hash-pinned files e4_pl_element.py, e4_pl_s3_state.py; fail-closed authority), not a native-kernel task.
- Compilable but small: corotational rotation_matrix_from_vector/_so3_weighted_mean (~5% end to end on the
  stiffened case only, ~3% after discounting), Voigt/rotation transforms, numpy-internal glue. Assembly scatter and
  sparse pattern building do not appear (tottime ~0) in any case.
- Already native: compensated contractions (arc 12.5%, lin 5%).

## Decision
No candidate reaches the >=10%-of-representative-solve threshold for a compiled kernel; none implemented
(measured, not worth it): assembly scatter, sparse pattern, recovery arithmetic, SuperLU option changes,
symbolic reuse, corotational rotations. The real lever is the guard/seal chain (formulation_class_guard alone
10-18%, seals up to 18%); a safe approach needs owner decision and a successor record, e.g. per-class memoised
guard verdicts invalidated on class/MRO mutation, and cached canonical seals keyed on immutable state identity.

## Not run / open
No tests run (no source change). arc_panel wall variance unexplained. Plasticity depth of nl_plastic_plate
not inspected. Not reviewed by Codex (nothing to review).
