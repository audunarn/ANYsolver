# ANYsolver Sol Ultra Performance Report

- Report kind: `baseline`
- Generated: 2026-08-11T08:44:31.561161Z
- Revision: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Suite: `full` (1 warm repeats)
- Python: 3.13.9
- CPU: AMD Ryzen 9 7950X 16-Core Processor
- Cases: 16 completed, 0 failed

## Case summary

| Case | Status | Cold wall | Warm median | Cold / warm | Warm Python peak |
| --- | --- | ---: | ---: | ---: | ---: |
| `isotropic_s4_nonlinear_plate` | completed | 5.200293s | 0.012244s | 424.708x | 464.24 KiB |
| `weighted_mpc_panel` | completed | 0.206142s | 0.197249s | 1.045x | 8.99 MiB |
| `orthotropic_elastic_s4_plate` | completed | 0.198843s | 0.160939s | 1.236x | 2.18 MiB |
| `hill48_plastic_s4_plate` | completed | 2.912805s | 0.406896s | 7.159x | 1.18 MiB |
| `generalized_coupled_s4_plate` | completed | 2.511184s | 0.180779s | 13.891x | 2.49 MiB |
| `rotated_corotational_shell` | completed | 2.346232s | 0.009553s | 245.604x | 144.00 KiB |
| `rotated_corotational_beam` | completed | 0.003402s | 0.003214s | 1.059x | 34.18 KiB |
| `arc_length_post_buckling_oracle` | completed | 0.274385s | 0.241634s | 1.136x | 88.48 KiB |
| `nonlinear_impact_damage` | completed | 0.390694s | 0.194129s | 2.013x | 493.42 KiB |
| `repeated_multi_rhs_static` | completed | 0.012305s | 0.010611s | 1.160x | 117.01 KiB |
| `beam_column_buckling` | completed | 0.015002s | 0.014384s | 1.043x | 170.17 KiB |
| `long_transient_selected_output` | completed | 2.807943s | 2.848336s | 0.986x | 1.17 MiB |
| `large_stress_recovery` | completed | 0.449923s | 0.458265s | 0.982x | 806.61 KiB |
| `factorization_cache_reuse` | completed | 0.002050s | 0.001510s | 1.358x | 39.44 KiB |
| `linear_shell_K_M_assembly` | completed | 0.084251s | 0.086468s | 0.974x | 1.89 MiB |
| `selective_recovery_consistency` | completed | 0.132702s | 0.114125s | 1.163x | 187.51 KiB |

## Baseline qualification

- Immutable `performance_2`: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Contemporaneous `origin/main`: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Merge-base: `575ddd3fd7712378e6a24b901c647cf101d7b0dc`
- Full test suite: **624 passed in 231.26s**
- Full-suite command: `$env:PYPARDISO_MKL_RT='C:\Python\Python313\Library\bin\mkl_rt.3.dll'; C:\Github\ANYsolver\.venv\Scripts\python.exe -m pytest tests -q --basetemp=.pytest_tmp_sol_ultra_baseline`

### Setup incidents (not numerical regressions)

| Stage | Classification | Outcome | Causes |
| --- | --- | --- | --- |
| `global_interpreter_dependency_check` | environment_setup_failure | 59 collection errors in 3.01s | ModuleNotFoundError: anygeometry through ANYmesh; ModuleNotFoundError: anyfileio |
| `repository_venv_initial_full_suite` | test_temp_and_native_runtime_setup_failure | 616 passed, 1 failed, 7 errors in 259.36s | Seven pytest tmp_path setup errors raised PermissionError under C:\Users\AudunArnesenNyhus\AppData\Local\Temp\pytest-of-AudunArnesenNyhus; One PyPardiso backend status assertion failed because shared library mkl_rt was not found |
| `initial_nonlinear_assembly_benchmark` | benchmark_bootstrap_defect | failed in 1.9s | RuntimeError: Performance layer was not installed; original assembler is unavailable; Bootstrap status was installed=false while JIT eligibility was true |

### Mandated nonlinear assembly benchmarks

| Case | Legacy median | Persistent median | Direct median | Direct vs legacy |
| --- | ---: | ---: | ---: | ---: |
| `nonlinear_assembly_selector` | 0.006050s | 0.001448s | 0.000568s | 10.646x |
| `nonlinear_assembly_weighted_mpc` | 0.008926s | 0.001762s | 0.000680s | 13.128x |

Reproduction commands:

- `python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10`
- `python scripts/benchmark_nonlinear_assembly.py --nx 20 --ny 10 --repeats 10 --weighted-mpc-rows 12`

## Phase coverage

### Isotropic S4 nonlinear plate

nonlinear_local_response=0.001431s, total_wall_time=0.012244s

Correctness/result metrics: `{"plan_diagnostics":{"batch_b_installed":true,"constitutive_fallback":null,"elastic_constitutive_state_bytes":640,"elastic_fast_path_batch_count":1,"elastic_fast_path_element_count":4,"local_force_entries":96,"local_tangent_entries":2304,"non_shell_element_count":0,"num_layers":5,"plastic_batch_count":0,"quadratic_beam_batch_count":0,"quadratic_beam_element_count":0,"revision":[13,9,1,4],"setup_seconds":0.0010320000001229346,"shell_batch_count":1,"shell_element_count":4,"tangent_nnz":1764,"timings":{"calls":1,"force_scatter_seconds":3.819999983534217e-05,"initial_field_accelerated_elements":0,"initial_field_override_elements":0,"initial_field_override_seconds":2.8699985705316067e-05,"non_shell_seconds":6.700051017105579e-06,"residual_only_calls":0,"shell_kernel_seconds":0.0010380000458098948,"state_pack_seconds":0.0,"tangent_calls":1,"tangent_scatter_seconds":0.00016799999866634607,"total_seconds":0.001395899977069348},"total_dofs":54},"relative_force_error":1.5066412126590283e-16,"relative_tangent_error":1.1292293574952823e-16}`

### Weighted-MPC panel

model_preparation=0.003588s, constraint_plan_construction=0.063249s, reduced_coordinate_scatter=0.002027s, T.T @ F_projection=0.000097s, T.T @ K @ T_projection=0.001034s, total_wall_time=0.197249s

Correctness/result metrics: `{"relative_force_error":9.986874313577743e-17,"relative_tangent_error":1.1561587749332502e-16}`

### Orthotropic elastic S4 plate

model_preparation=0.002357s, linear_K_assembly=0.139364s, linear_M_assembly=0.018513s, total_wall_time=0.160939s

Correctness/result metrics: `{"mass_norm":4.488668861650112,"relative_symmetry_error":5.39418370305313e-17,"stiffness_norm":18958110903.294357}`

### Hill-48 plastic S4 plate

model_preparation=0.001715s, nonlinear_local_response=0.195036s, total_wall_time=0.406896s

Correctness/result metrics: `{"absolute_alpha_error":0.0,"maximum_alpha_active":0.0019295741691775828,"maximum_alpha_reference":0.0019295741691775828,"relative_force_error":0.0,"relative_tangent_error":7.459614818747141e-17,"state_element_count":12}`

### Generalized coupled A/B/D/As S4 plate

model_preparation=0.001685s, linear_K_assembly=0.095484s, linear_M_assembly=0.020102s, nonlinear_local_response=0.021314s, total_wall_time=0.180779s

Correctness/result metrics: `{"mass_norm":19.578900218328382,"nonzero_B_coupling":true,"relative_force_error":0.0,"relative_tangent_error":6.322531291429107e-17,"stiffness_norm":17282940147.61002}`

### Rotated-corotational shell

model_preparation=0.000825s, nonlinear_local_response=0.006776s, total_wall_time=0.009553s

Correctness/result metrics: `{"corotational_force_norm":6.88353606781236e-07,"rigid_rotation_degrees":75.0,"scaled_rigid_rotation_residual":3.495038604616173e-16,"tangent_norm":4273631917.13909,"von_karman_force_norm":1969516462.1989386}`

### Rotated-corotational beam

model_preparation=0.000568s, nonlinear_local_response=0.002112s, total_wall_time=0.003214s

Correctness/result metrics: `{"corotational_force_norm":6.594406526243611e-08,"rigid_rotation_degrees":75.0,"scaled_rigid_rotation_residual":6.199194853660462e-16,"tangent_norm":420089746.14228594,"von_karman_force_norm":106375209.71533565}`

### Arc-length post-peak oracle

total_wall_time=0.241634s

Correctness/result metrics: `{"exact_peak_load_factor":0.3849001794597505,"peak_load_factor":0.3848853378634734,"relative_peak_error":3.855959822611215e-05,"solver_status":"peak_confirmed","step_count":30}`

### Nonlinear impact with damage

total_wall_time=0.194129s

Correctness/result metrics: `{"impact_deleted_count":0,"impact_max_damage":0.025495334905325514,"impact_status":"completed","static_deleted_records":2,"static_max_fracture_utilization":2.0,"sub_softening_rebuilds_skipped":true}`

### Repeated multi-RHS static workflow

factorization=0.000243s, linear_solve=0.000463s, total_wall_time=0.010611s

Correctness/result metrics: `{"solution_matrix_norm":0.003071040956564302}`

### Beam-column buckling

linear_K_assembly=0.002047s, KG_assembly=0.002830s, total_wall_time=0.014384s

Correctness/result metrics: `{"critical_load_factor":647404.8509508282,"num_modes":2}`

### Long transient with selected output

linear_K_assembly=0.004444s, linear_M_assembly=0.004230s, factorization=0.000342s, total_wall_time=2.848336s

Correctness/result metrics: `{"history_storage_mode":"selected","num_saved_steps":101,"num_steps":500,"peak_displacement":0.019913318508363708,"saved_displacement_shape":[101,6],"saved_tip_history_shape":[101,6],"solver_status":"completed"}`

### Large S4 stress recovery

stress_recovery=0.450427s, total_wall_time=0.458265s

Correctness/result metrics: `{"all_values_finite":true,"recovered_element_count":200}`

### Factorization cache reuse

factorization=0.000253s, total_wall_time=0.001510s

Correctness/result metrics: `{"changed_matrix_new_handle":true,"same_handle_reused":true}`

### Linear shell K/M assembly

linear_K_assembly=0.033555s, linear_M_assembly=0.018589s, total_wall_time=0.086468s

### Selective recovery consistency

stress_recovery=0.052192s, total_wall_time=0.114125s

Correctness/result metrics: `{"num_stress_results":24,"results_match":true}`

## Known limitations

- Use matched revisions, native libraries, and thread policies for timing comparisons.
- Cold measurements are first-in-process measurements, not fresh-process startup measurements.
- Unavailable phase timers remain explicit null values; total wall time is always measured.
- Process peak RSS is cumulative on platforms that do not expose a resettable per-case peak.
- Representative workloads are intentionally bounded and do not replace numerical qualification tests.
