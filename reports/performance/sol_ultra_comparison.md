# ANYsolver Sol Ultra baseline/final comparison

- Report status: **COMPLETE**
- Immutable initial `performance_2`: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Contemporaneous `origin/main`: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Merge-base: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Qualified source candidate on `performance_2`: `eb41e73c28205e7dc147895bc847b3153b0f879a`
- Baseline artifact: `reports/performance/sol_ultra_baseline.json`
- Final artifact: `reports/performance/sol_ultra_final.json`

## Environment

| Field | Baseline | Final | Match |
| --- | --- | --- | --- |
| `runtime.python_version` | 3.13.9 | 3.13.9 | yes |
| `runtime.python_implementation` | CPython | CPython | yes |
| `runtime.platform` | Windows-11-10.0.26200-SP0 | Windows-11-10.0.26200-SP0 | yes |
| `runtime.cpu` | AMD Ryzen 9 7950X 16-Core Processor | AMD Ryzen 9 7950X 16-Core Processor | yes |
| `runtime.physical_cores` | 16 | 16 | yes |
| `runtime.logical_cores` | 32 | 32 | yes |
| `packages.numpy` | 2.4.3 | 2.4.3 | yes |
| `packages.scipy` | 1.16.3 | 1.16.3 | yes |
| `packages.numba` | 0.65.0 | 0.65.0 | yes |
| `packages.llvmlite` | 0.47.0 | 0.47.0 | yes |
| `packages.pypardiso` | 0.4.7 | 0.4.7 | yes |
| `packages.mkl` | 2026.0.0 | 2026.0.0 | yes |
| `packages.threadpoolctl` | 3.6.0 | 3.6.0 | yes |
| `packages.ANYsolver` | 0.2.0 | 0.2.0 | yes |
| `packages.ANYmaterial` | 0.1.0 | 0.1.0 | yes |
| `packages.ANYmesher` | 0.1.0 | 0.1.0 | yes |
| `packages.ANYgeometry` | 0.1.0 | 0.1.0 | yes |
| `packages.ANYfileio` | 0.1.0 | 0.1.0 | yes |
| `jit.enabled` | yes | yes | yes |
| `jit.backend` | numba | numba | yes |

## Cold and warm timing

Speedup is `baseline / final`; values above 1 are faster. Each row is independent and is not averaged across unlike workloads.

| Case | Baseline status | Final status | Baseline cold | Final cold | Cold speedup | Baseline warm median | Final warm median | Warm speedup |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `isotropic_s4_nonlinear_plate` | completed | completed | 5.200293s | 4.723468s | 1.101x | 0.012244s | 0.012086s | 1.013x |
| `weighted_mpc_panel` | completed | completed | 0.206142s | 0.199119s | 1.035x | 0.197249s | 0.183748s | 1.073x |
| `orthotropic_elastic_s4_plate` | completed | completed | 0.198843s | 0.226361s | 0.878x | 0.160939s | 0.102021s | 1.578x |
| `hill48_plastic_s4_plate` | completed | completed | 2.912805s | 2.371865s | 1.228x | 0.406896s | 0.068243s | 5.962x |
| `generalized_coupled_s4_plate` | completed | completed | 2.511184s | 2.394625s | 1.049x | 0.180779s | 0.140153s | 1.290x |
| `rotated_corotational_shell` | completed | completed | 2.346232s | 2.378111s | 0.987x | 0.009553s | 0.006467s | 1.477x |
| `rotated_corotational_beam` | completed | completed | 0.003402s | 0.002852s | 1.193x | 0.003214s | 0.002767s | 1.161x |
| `arc_length_post_buckling_oracle` | completed | completed | 0.274385s | 0.281232s | 0.976x | 0.241634s | 0.249984s | 0.967x |
| `nonlinear_impact_damage` | completed | completed | 0.390694s | 0.232851s | 1.678x | 0.194129s | 0.190304s | 1.020x |
| `repeated_multi_rhs_static` | completed | completed | 0.012305s | 0.011698s | 1.052x | 0.010611s | 0.010048s | 1.056x |
| `beam_column_buckling` | completed | completed | 0.015002s | 0.014152s | 1.060x | 0.014384s | 0.013578s | 1.059x |
| `long_transient_selected_output` | completed | completed | 2.807943s | 0.304117s | 9.233x | 2.848336s | 0.301529s | 9.446x |
| `large_stress_recovery` | completed | completed | 0.449923s | 0.076784s | 5.860x | 0.458265s | 0.042273s | 10.841x |
| `factorization_cache_reuse` | completed | completed | 0.002050s | 0.001806s | 1.136x | 0.001510s | 0.001432s | 1.054x |
| `linear_shell_K_M_assembly` | completed | completed | 0.084251s | 0.175908s | 0.479x | 0.086468s | 0.091687s | 0.943x |
| `selective_recovery_consistency` | completed | completed | 0.132702s | 0.150459s | 0.882x | 0.114125s | 0.125261s | 0.911x |

## Peak-memory evidence

`Final / baseline` below 1 uses less memory. Python peaks are per invocation. Process peak RSS can be process-lifetime cumulative on this platform and is therefore audit evidence, not an isolated per-case allocation measurement.

| Case | Baseline warm Python peak | Final warm Python peak | Final / baseline | Baseline process peak RSS | Final process peak RSS | Final / baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `isotropic_s4_nonlinear_plate` | 464.24 KiB | 465.26 KiB | 1.002x | 232.80 MiB | 236.18 MiB | 1.014x |
| `weighted_mpc_panel` | 8.99 MiB | 9.01 MiB | 1.001x | 232.80 MiB | 236.18 MiB | 1.014x |
| `orthotropic_elastic_s4_plate` | 2.18 MiB | 1.89 MiB | 0.867x | 232.80 MiB | 236.18 MiB | 1.014x |
| `hill48_plastic_s4_plate` | 1.18 MiB | 1.15 MiB | 0.977x | 235.66 MiB | 247.01 MiB | 1.048x |
| `generalized_coupled_s4_plate` | 2.49 MiB | 2.53 MiB | 1.016x | 247.96 MiB | 261.27 MiB | 1.054x |
| `rotated_corotational_shell` | 144.00 KiB | 130.66 KiB | 0.907x | 263.44 MiB | 277.36 MiB | 1.053x |
| `rotated_corotational_beam` | 34.18 KiB | 32.61 KiB | 0.954x | 263.44 MiB | 277.36 MiB | 1.053x |
| `arc_length_post_buckling_oracle` | 88.48 KiB | 114.58 KiB | 1.295x | 263.44 MiB | 277.36 MiB | 1.053x |
| `nonlinear_impact_damage` | 493.42 KiB | 536.89 KiB | 1.088x | 263.44 MiB | 277.36 MiB | 1.053x |
| `repeated_multi_rhs_static` | 117.01 KiB | 116.37 KiB | 0.995x | 263.44 MiB | 277.36 MiB | 1.053x |
| `beam_column_buckling` | 170.17 KiB | 164.08 KiB | 0.964x | 263.44 MiB | 277.36 MiB | 1.053x |
| `long_transient_selected_output` | 1.17 MiB | 504.57 KiB | 0.422x | 263.44 MiB | 277.36 MiB | 1.053x |
| `large_stress_recovery` | 806.61 KiB | 1.18 MiB | 1.497x | 263.44 MiB | 278.35 MiB | 1.057x |
| `factorization_cache_reuse` | 39.44 KiB | 38.84 KiB | 0.985x | 263.44 MiB | 278.35 MiB | 1.057x |
| `linear_shell_K_M_assembly` | 1.89 MiB | 1.89 MiB | 1.000x | 263.44 MiB | 290.98 MiB | 1.105x |
| `selective_recovery_consistency` | 187.51 KiB | 240.67 KiB | 1.284x | 263.44 MiB | 291.09 MiB | 1.105x |

## Normalized phase coverage

Unavailable means that the benchmark case exposed no normalized timer for that phase. It does not mean zero work and no phase speedup is inferred from a null value.

| Phase | Baseline available | Final available | Final unavailable |
| --- | ---: | ---: | ---: |
| `model_preparation` | 6/16 | 6/16 | 10/16 |
| `constraint_plan_construction` | 1/16 | 1/16 | 15/16 |
| `linear_K_assembly` | 5/16 | 5/16 | 11/16 |
| `linear_M_assembly` | 4/16 | 4/16 | 12/16 |
| `KG_assembly` | 1/16 | 1/16 | 15/16 |
| `nonlinear_local_response` | 5/16 | 5/16 | 11/16 |
| `constitutive_update` | 0/16 | 0/16 | 16/16 |
| `state_packing` | 0/16 | 0/16 | 16/16 |
| `state_commit` | 0/16 | 0/16 | 16/16 |
| `state_materialization` | 0/16 | 0/16 | 16/16 |
| `full_coordinate_scatter` | 0/16 | 0/16 | 16/16 |
| `reduced_coordinate_scatter` | 1/16 | 1/16 | 15/16 |
| `T.T @ F_projection` | 1/16 | 1/16 | 15/16 |
| `T.T @ K @ T_projection` | 1/16 | 1/16 | 15/16 |
| `contact_search` | 0/16 | 0/16 | 16/16 |
| `contact_load_construction` | 0/16 | 0/16 | 16/16 |
| `factorization` | 3/16 | 3/16 | 13/16 |
| `linear_solve` | 1/16 | 1/16 | 15/16 |
| `full_vector_reconstruction` | 0/16 | 0/16 | 16/16 |
| `stress_recovery` | 2/16 | 2/16 | 14/16 |
| `history_output_storage` | 0/16 | 0/16 | 16/16 |
| `total_wall_time` | 16/16 | 16/16 | 0/16 |

## Independent numerical qualification

- Overall status: **PASSED**
- Passed cases: 13
- Failed cases: 0
- Unavailable cases: 0
- Metric failures: 0
- Candidate commit: `eb41e73c28205e7dc147895bc847b3153b0f879a`
- Timing and memory in this artifact are informational; numerical tolerances alone determine its pass/fail result.

## Thread-scaling summary

- Evidence revision: `b3e04c29d3362994eb6fa33cb0a6c95fe530bb9f`
- Campaign status: **COMPLETED**
- Default policy changed: no

| Workload | Threads | Warm wall median | Warm phase | Phase median | Relative error vs one thread | Thread policy restored |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| `linear_solver` | 1 | 4.448107s | `solve_seconds` | 0.016607s | 0 | yes |
| `linear_solver` | 2 | 4.457484s | `solve_seconds` | 0.017000s | 0 | yes |
| `linear_solver` | 4 | 4.385145s | `solve_seconds` | 0.018343s | 0 | yes |
| `linear_solver` | 8 | 4.429161s | `solve_seconds` | 0.017141s | 0 | yes |
| `nonlinear_assembly` | 1 | 0.535102s | `solve_seconds` | 0.504726s | 0 | yes |
| `nonlinear_assembly` | 2 | 0.532079s | `solve_seconds` | 0.501583s | 0 | yes |
| `nonlinear_assembly` | 4 | 0.530139s | `solve_seconds` | 0.498774s | 0 | yes |
| `nonlinear_assembly` | 8 | 0.527180s | `solve_seconds` | 0.496788s | 0 | yes |
| `nonlinear_assembly` | 16 | 0.543791s | `solve_seconds` | 0.511014s | 0 | yes |
| `stress_recovery` | 1 | 0.026895s | `recovery_seconds` | 0.025861s | 0 | yes |
| `stress_recovery` | 2 | 0.052467s | `recovery_seconds` | 0.050951s | 0 | yes |
| `stress_recovery` | 4 | 0.061580s | `recovery_seconds` | 0.060194s | 0 | yes |
| `stress_recovery` | 8 | 0.124015s | `recovery_seconds` | 0.123027s | 0 | yes |

Decision: keep one thread as the qualification and recommended explicit policy. Do not infer an automatic default from logical-core count.

## Backend and fallback observations

### `weighted_mpc_panel`

- Backend `diagnostics.reduced_plan.mapping_kind`: `weighted_mpc`

### `orthotropic_elastic_s4_plate`

- Backend `diagnostics.vectorized_shell_groups.0.backend`: `numba`

### `generalized_coupled_s4_plate`

- Backend `diagnostics.vectorized_shell_groups.0.backend`: `numba`

### `arc_length_post_buckling_oracle`

- Backend `diagnostics.nonlinear_performance.corotational.backend`: `numba`
- Backend `diagnostics.nonlinear_performance.direct_reduced_assembly.plan.mapping_kind`: `selector`
- Fallback `diagnostics.nonlinear_performance.corotational.fallback_reason`: `kinematics_not_corotational`
- Fallback `diagnostics.nonlinear_performance.hill48.fallback_reason`: `hill48_not_exercised`
- Fallback `diagnostics.nonlinear_state_storage.fallback_reason`: `no_plastic_shell_batch`

### `repeated_multi_rhs_static`

- Backend `backend.backend`: `scipy_superlu`

### `long_transient_selected_output`

- Backend `results.history_storage_mode`: `selected`

### `large_stress_recovery`

- Backend `resources.backend`: `serial`
- Backend `resources.metadata.recovery_backend`: `compiled_isotropic_s4`

### `selective_recovery_consistency`

- Backend `resources.serial.backend`: `serial`
- Backend `resources.serial.metadata.recovery_backend`: `scalar_legacy_small_selection`
- Backend `resources.threaded.backend`: `thread_pool`
- Backend `resources.threaded.metadata.recovery_backend`: `scalar_legacy_small_selection`
- Fallback `resources.serial.metadata.fallback_reasons`: `{"below_recovery_plan_threshold":{"element_ids":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],"minimum_size":100}}`
- Fallback `resources.threaded.metadata.fallback_reasons`: `{"below_recovery_plan_threshold":{"element_ids":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],"minimum_size":100}}`

## Promoted, deferred, and rejected workstreams

| Workstream | Qualification and evidence | Decision |
| --- | --- | --- |
| Persistent nonlinear state | Static/arc commit, rejection, restart, initial-field, snapshot, and materialization parity; 9.08x synthetic transaction throughput and qualified lifecycle parity | **Promote** qualified von Karman static/arc lifecycle; **defer** nonlinear-impact state transactions |
| Hill-48 | Scalar-oracle parity for canonical curves, mixed elastic/yielding rows, state, and tangent; 5.962x final case | **Promote** compiled canonical-curve path; retain scalar and numerical-tangent row fallbacks |
| Orthotropic S4 | Material-axis and geometry parity; focused 11.571x linear and 127.745x nonlinear; 1.578x final case | **Promote** qualified homogeneous orthotropic S4 |
| Generalized S4 | Force, tangent, mass, nonsymmetric `B`, and resultants-only recovery parity; 1.290x final case | **Promote** qualified pre-integrated `A/B/D/As` S4 |
| Rotated corotational | Rigid rotation, objectivity, force, and tangent checks; 1.477x shell and 1.161x beam final cases | **Promote** direct 3x3 block rotations; **defer** broader frame/local-response batching and consistent-frame replacement |
| Impact tangent reuse | Exact zero-budget oracle; contact, active-set, damage, deletion, plastic, cutback, and refresh checks; 46--59% fewer factorizations | **Promote** conservative opt-in modified Newton |
| Direct reduced impact | Selector and weighted-MPC parity; 3.113x assembly and 98.97% of eligible full assemblies avoided | **Promote** elastic, zero-affine-offset scope; **defer** plastic/fiber/damage/deletion/affine scope |
| Compact impact contact | Exact force/order/sticky/public-record parity and fivefold fewer record materializations | **Promote** solve-local compact work buffers |
| Incremental damage matrices | Exact K/M and point-mass parity; combined cached-term plus plan memory gate; 11-update break-even | **Promote** only when event-density and combined-memory gates pass |
| Analysis session | Reuse/no-reuse parity; topology, geometry, material, constraint, value, foreign-plan, close, and concurrent-cache tests; 2.562x repeated static evidence | **Promote** optional caller-owned bounded sessions |
| Transient reduced data | Exact preprojected-load and selected-row parity; 9.446x final case | **Promote** selected-output/reduced-load path |
| Recovery batches | Component, frame, surface, ordering, provenance, and fallback parity; 10.841x large final case | **Promote** large qualified S4 recovery; retain scalar path below 100 selected elements and for unsupported formulations |
| Arc-length bookkeeping | Exact reaction/history/progress/constraint contracts and accepted-force reuse; final and 11-repeat audits within five percent | **Promote** qualified force-driven optimizations; prescribed paths retain their exact affine formulation |
| Automatic thread selection | Zero numerical differences, but no repeatable scaling benefit and recovery worsened with more workers | **Reject** automatic/default scaling; qualify and recommend explicit thread count 1 |
| Experimental CSR linear assembly | Production performance gate was not demonstrated | **Reject** production promotion; retain qualified COO implementation |

## Known limitations

- Use matched revisions, native libraries, and thread policies for timing comparisons.
- Cold measurements are first-in-process measurements, not fresh-process startup measurements.
- Unavailable phase timers remain explicit null values; total wall time is always measured.
- Process peak RSS is cumulative on platforms that do not expose a resettable per-case peak.
- Representative workloads are intentionally bounded and do not replace numerical qualification tests.
- Workstream microbenchmarks establish path-specific gates; this report does not relabel them as full-suite end-to-end measurements.
- The benchmark JSON does not record Git dirty state. Release captures must be made from a separately verified clean checkout; the independent numerical artifact records this provenance.
- Normalized phase coverage is intentionally sparse. Nested diagnostic counters may be more specific but are not substituted for absent phase timers.

## Reproduction

```powershell
$env:PYPARDISO_MKL_RT = 'C:\Python\Python313\Library\bin\mkl_rt.3.dll'
$python = 'C:\Github\ANYsolver\.venv\Scripts\python.exe'
$baselineRoot = 'C:\Github\ANYsolver\.perf2-worktrees\baseline'
$candidateRoot = (Resolve-Path -LiteralPath .).Path

& $python -m pytest tests -q --basetemp=.pytest_tmp_sol_ultra_final
$dirty = git status --porcelain
if ($dirty) { throw "Qualified source checkout is dirty before numerical capture: $dirty" }
& $python scripts/verify_sol_ultra_numerics.py capture --solver-root $candidateRoot --label candidate --suite full --output .sol_ultra_verify_candidate.json
& $python scripts/verify_sol_ultra_numerics.py capture --solver-root $baselineRoot --label baseline --suite full --output .sol_ultra_verify_baseline.json
& $python scripts/verify_sol_ultra_numerics.py compare --baseline .sol_ultra_verify_baseline.json --candidate .sol_ultra_verify_candidate.json --json-report reports/performance/sol_ultra_numerical_comparison.json --markdown-report reports/performance/sol_ultra_independent_verification.md

& $python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10
& $python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10 --weighted-mpc-rows 12
& $python scripts/benchmark_sol_ultra_performance.py --suite full --repeats 3 --label final --output reports/performance/sol_ultra_final.json --no-markdown
& $python scripts/benchmark_sol_ultra_thread_scaling.py --repeats 3 --output .sol_ultra_thread_scaling.json
& $python scripts/compare_sol_ultra_performance.py --baseline reports/performance/sol_ultra_baseline.json --final reports/performance/sol_ultra_final.json --numerical reports/performance/sol_ultra_numerical_comparison.json --thread-scaling .sol_ultra_thread_scaling.json --decision-log reports/performance/sol_ultra_decision_log.md --output reports/performance/sol_ultra_comparison.md
```
