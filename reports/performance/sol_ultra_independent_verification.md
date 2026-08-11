# Sol Ultra independent numerical verification

Overall status: **PASSED**

This report compares complete stored numerical payloads. SHA-256 signatures are provenance only; acceptance uses baseline-authoritative numerical tolerances.

## Revisions

| Artifact | Label | Commit | Branch | Dirty at capture | Solver root |
| --- | --- | --- | --- | --- | --- |
| Baseline | baseline | 575ddd3fd7712378e6a24b901c647cf101d7b0dc | unavailable | False | C:\Github\ANYsolver\.perf2-worktrees\numerical-baseline |
| Candidate | candidate-eb41e73 | eb41e73c28205e7dc147895bc847b3153b0f879a | unavailable | False | C:\Github\ANYsolver\.perf2-worktrees\qualification-eb41e73 |

## Environment

| Field | Baseline | Candidate |
| --- | --- | --- |
| platform | Windows-11-10.0.26200-SP0 | Windows-11-10.0.26200-SP0 |
| python | 3.13.9 | 3.13.9 |
| numpy | 2.4.3 | 2.4.3 |
| scipy | 1.16.3 | 1.16.3 |
| numba | 0.65.0 | 0.65.0 |
| pypardiso | 0.4.7 | 0.4.7 |
| anymaterial | 0.1.0 | 0.1.0 |
| anymesher | 0.1.0 | 0.1.0 |
| anyfileio | 0.1.0 | 0.1.0 |
| logical_cpu_count | 32 | 32 |
| pypardiso_mkl_rt_configured | True | True |

## Case summary

| Case | Result | Max relative L2 error | Candidate/baseline wall time | Candidate/baseline peak RSS |
| --- | --- | ---: | ---: | ---: |
| arc_length | passed | 0 | 0.994145 | 1.01088 |
| buckling | passed | 0 | 0.961725 | 1.00122 |
| contact_load | passed | 0 | 0.966489 | 1.00132 |
| corotational | passed | 1.59599e-16 | 0.731476 | 1.04344 |
| generalized_shell | passed | 0 | 0.891759 | 1.00513 |
| global_matrices | passed | 0 | 0.557778 | 1.00368 |
| hill48_material | passed | 0 | 0.905824 | 1.01748 |
| hill48_shell_path | passed | 2.00367 | 8.14695 | 2.36749 |
| linear_static | passed | 0 | 0.709045 | 1.00035 |
| modal | passed | 0 | 0.962261 | 1.00288 |
| nonlinear_impact | passed | 0.396226 | 0.727426 | 1.00707 |
| nonlinear_impact_direct_reduced | passed | 0.0787453 | 1.10818 | 1.07946 |
| nonlinear_internal | passed | 0 | 0.835353 | 1.02881 |

## Numerical acceptance criteria

| Gate | Method | Relative tolerance | Absolute tolerance | Source |
| --- | --- | ---: | ---: | --- |
| buckling_factor | relative_l2 | 1e-08 | 1e-12 | Sol Ultra plan: buckling-factor relative error |
| contact_history | relative_l2 | 1e-06 | 1e-09 | existing deterministic contact-history qualification tolerance |
| elastic_tangent | relative_l2 | 1e-10 | 1e-12 | Sol Ultra plan: elastic tangent relative norm |
| global_matrix | relative_l2 | 1e-12 | 1e-12 | Sol Ultra plan: K/M/KG relative matrix norm |
| internal_force | relative_l2 | 1e-11 | 1e-12 | Sol Ultra plan: internal force relative norm |
| linear_displacement | relative_l2 | 1e-10 | 1e-14 | Sol Ultra plan: linear displacement relative error |
| modal_frequency | relative_l2 | 1e-09 | 1e-12 | Sol Ultra plan: modal frequency relative error |
| nonlinear_history | relative_l2 | 1e-08 | 1e-10 | solver path tolerance for deterministic continuation histories |
| plastic_state | relative_l2 | 1e-09 | 1e-12 | existing Hill/J2 state qualification tolerance |
| plastic_tangent | relative_l2 | 2e-07 | 1e-05 | existing Hill-48 analytical/numerical tangent qualification |
| recovery | relative_l2 | 1e-10 | 1e-12 | component-wise committed-state recovery parity |
| recovery_stress | relative_l2 | 1e-10 | 1e-07 | existing scalar/compiled shell stress-recovery qualification; absolute floor applies only to physical recovered stress fields |

## Failures

No numerical failures were detected.

## Unavailable or incomplete coverage

All cases were available in both artifacts.

## Warnings

- `{"case": "nonlinear_impact", "metric": "diagnostic.factorization_reuse_count", "reason": "extra_candidate_metric"}`
- `{"case": "nonlinear_impact", "metric": "diagnostic.tangent_assembly_count", "reason": "extra_candidate_metric"}`
- `{"case": "nonlinear_impact", "metric": "diagnostic.tangent_reuse_count", "reason": "extra_candidate_metric"}`

## Candidate path and fallback observations

### arc_length

```json
{
  "source_0.control.cutback_factor": 0.5,
  "source_0.nonlinear_performance.assembly.fallback_reason": "persistent_assembly_plan_not_selected",
  "source_0.nonlinear_performance.assembly.fallback_reason_counts": {
    "persistent_assembly_plan_not_selected": 140
  },
  "source_0.nonlinear_performance.assembly.plan_reuse_scope": "within_analysis",
  "source_0.nonlinear_performance.assembly.plan_reused": false,
  "source_0.nonlinear_performance.corotational.backend": "numba",
  "source_0.nonlinear_performance.corotational.backend_fallback_reason": null,
  "source_0.nonlinear_performance.corotational.eligible": false,
  "source_0.nonlinear_performance.corotational.fallback_reason": "kinematics_not_corotational",
  "source_0.nonlinear_performance.corotational.fast_path_name": "corotational_direct_3x3_blocks",
  "source_0.nonlinear_performance.direct_reduced_assembly.assembly_count": 0,
  "source_0.nonlinear_performance.direct_reduced_assembly.fallback_reason": "direct_reduction_context_not_active",
  "source_0.nonlinear_performance.direct_reduced_assembly.plan_reuse_scope": "within_analysis",
  "source_0.nonlinear_performance.direct_reduced_assembly.plan_reused": false,
  "source_0.nonlinear_performance.direct_reduced_assembly.residual_only_assembly_count": 0,
  "source_0.nonlinear_performance.hill48.eligible": true,
  "source_0.nonlinear_performance.hill48.fallback_reason": "hill48_not_exercised",
  "source_0.nonlinear_performance.hill48.fallback_reason_counts": {},
  "source_0.nonlinear_performance.hill48.fast_path": "hill48_flattened_numba_return_map",
  "source_0.nonlinear_performance.hill48.jit_backend": "numba",
  "source_0.nonlinear_performance.hill48.row_fallback_count": 0,
  "source_0.nonlinear_performance.hill48.scalar_fallback_call_count": 0,
  "source_0.nonlinear_performance.hill48.scalar_fallback_point_count": 0,
  "source_0.nonlinear_state_storage.eligible_batch_count": 0,
  "source_0.nonlinear_state_storage.fallback_reason": "no_plastic_shell_batch",
  "source_0.reaction_force_recovery.accepted_force_reuse_count": 30,
  "source_0.reaction_force_recovery.full_reassembly_count": 0,
  "source_0.result_case.analysis_case.settings.arc_length.cutback_factor": 0.5,
  "source_0.result_case.solver_backend": null
}
```

### buckling

```json
{
  "source_0.geometric_stiffness.diagnostics.vectorized_s4_geometric_stiffness.geometry_cache_hits": 0,
  "source_0.geometric_stiffness.diagnostics.vectorized_s4_geometric_stiffness.jit.backend": "numba"
}
```

### corotational

```json
{
  "source_0.5.batch_b_installed": true,
  "source_0.5.constitutive_fallback": null,
  "source_0.5.elastic_fast_path_batch_count": 1,
  "source_0.5.elastic_fast_path_element_count": 1,
  "source_0.5.generalized_elastic_fast_path_batch_count": 0,
  "source_0.5.generalized_elastic_fast_path_element_count": 0,
  "source_0.5.orthotropic_elastic_fast_path_batch_count": 0,
  "source_0.5.orthotropic_elastic_fast_path_element_count": 0,
  "source_0.5.plastic_batch_count": 0,
  "source_0.5.quadratic_beam_batch_count": 0,
  "source_0.5.shell_batch_count": 1,
  "source_1.5.batch_b_installed": true,
  "source_1.5.constitutive_fallback": null,
  "source_1.5.elastic_fast_path_batch_count": 0,
  "source_1.5.elastic_fast_path_element_count": 0,
  "source_1.5.generalized_elastic_fast_path_batch_count": 0,
  "source_1.5.generalized_elastic_fast_path_element_count": 0,
  "source_1.5.orthotropic_elastic_fast_path_batch_count": 0,
  "source_1.5.orthotropic_elastic_fast_path_element_count": 0,
  "source_1.5.plastic_batch_count": 0,
  "source_1.5.quadratic_beam_batch_count": 0,
  "source_1.5.shell_batch_count": 0
}
```

### generalized_shell

```json
{
  "source_0.backend": "serial",
  "source_0.metadata.batch_counts": {
    "scalar_legacy": 0
  },
  "source_0.metadata.compiled_batch_count": 0,
  "source_0.metadata.compiled_batch_seconds": 0.0,
  "source_0.metadata.eligible_element_count": 0,
  "source_0.metadata.fallback_element_count": 0,
  "source_0.metadata.fallback_reasons": {
    "below_recovery_plan_threshold": {
      "element_ids": [],
      "minimum_size": 100
    }
  },
  "source_0.metadata.native_thread_policy": {
    "phase": "stress_recovery_serial",
    "requested_threads": null,
    "restored": true,
    "status": "not_needed_serial"
  },
  "source_0.metadata.plan_reused": false,
  "source_0.metadata.recovery_backend": "scalar_legacy_small_selection"
}
```

### global_matrices

```json
{
  "source_0.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_1.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_2.diagnostics.vectorized_s4_geometric_stiffness.geometry_cache_hits": 0,
  "source_2.diagnostics.vectorized_s4_geometric_stiffness.jit.backend": "numba"
}
```

### hill48_shell_path

Unavailable diagnostics: `cutback_count`

```json
{
  "source_0.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_1.convergence_settings.cutback_factor": 0.5,
  "source_1.nonlinear_performance.assembly.fallback_reason": null,
  "source_1.nonlinear_performance.assembly.fallback_reason_counts": {},
  "source_1.nonlinear_performance.assembly.plan_reuse_scope": "within_analysis",
  "source_1.nonlinear_performance.assembly.plan_reused": true,
  "source_1.nonlinear_performance.assembly.plans.0.batch_b_installed": true,
  "source_1.nonlinear_performance.assembly.plans.0.constitutive_fallback": {
    "element_ids": [
      1
    ],
    "path": "general_element",
    "reason": "orthotropic_material"
  },
  "source_1.nonlinear_performance.assembly.plans.0.elastic_fast_path_batch_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.elastic_fast_path_element_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.generalized_elastic_fast_path_batch_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.generalized_elastic_fast_path_element_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.orthotropic_elastic_fast_path_batch_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.orthotropic_elastic_fast_path_element_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.plastic_batch_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.quadratic_beam_batch_count": 0,
  "source_1.nonlinear_performance.assembly.plans.0.shell_batch_count": 0,
  "source_1.nonlinear_performance.corotational.backend": "numba",
  "source_1.nonlinear_performance.corotational.backend_fallback_reason": null,
  "source_1.nonlinear_performance.corotational.eligible": false,
  "source_1.nonlinear_performance.corotational.fallback_reason": "kinematics_not_corotational",
  "source_1.nonlinear_performance.corotational.fast_path_name": "corotational_direct_3x3_blocks",
  "source_1.nonlinear_performance.direct_reduced_assembly.assembly_count": 0,
  "source_1.nonlinear_performance.direct_reduced_assembly.fallback_reason": "direct_reduction_context_not_active",
  "source_1.nonlinear_performance.direct_reduced_assembly.plan_reuse_scope": "within_analysis",
  "source_1.nonlinear_performance.direct_reduced_assembly.plan_reused": false,
  "source_1.nonlinear_performance.direct_reduced_assembly.residual_only_assembly_count": 0,
  "source_1.nonlinear_performance.hill48.eligible": true,
  "source_1.nonlinear_performance.hill48.fallback_reason": null,
  "source_1.nonlinear_performance.hill48.fallback_reason_counts": {},
  "source_1.nonlinear_performance.hill48.fast_path": "hill48_flattened_numba_return_map",
  "source_1.nonlinear_performance.hill48.jit_backend": "numba",
  "source_1.nonlinear_performance.hill48.last_call.fallback_reason_counts": {},
  "source_1.nonlinear_performance.hill48.last_call.scalar_fallback_points": 0,
  "source_1.nonlinear_performance.hill48.row_fallback_count": 0,
  "source_1.nonlinear_performance.hill48.scalar_fallback_call_count": 0,
  "source_1.nonlinear_performance.hill48.scalar_fallback_point_count": 0,
  "source_1.nonlinear_state_storage.eligible_batch_count": 0,
  "source_1.nonlinear_state_storage.fallback_reason": "no_plastic_shell_batch",
  "source_1.result_case.analysis_case.settings.convergence_settings.cutback_factor": 0.5,
  "source_1.result_case.solver_backend": null,
  "source_1.stiffness.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_1.thread_policy": {
    "active_solver_threads": null,
    "fallback_reason": null,
    "limiter_available": true,
    "requested_assembly_threads": null,
    "requested_solver_threads": null,
    "runtime_pools": [
      {
        "internal_api": "openblas",
        "num_threads": 1,
        "prefix": "libscipy_openblas",
        "user_api": "blas",
        "version": "0.3.31.dev"
      },
      {
        "internal_api": "openblas",
        "num_threads": 1,
        "prefix": "libscipy_openblas",
        "user_api": "blas",
        "version": "0.3.29.dev"
      },
      {
        "internal_api": "openmp",
        "num_threads": 32,
        "prefix": "vcomp",
        "user_api": "openmp",
        "version": null
      }
    ]
  },
  "source_2.backend": "serial",
  "source_2.metadata.batch_counts": {
    "scalar_legacy": 1
  },
  "source_2.metadata.compiled_batch_count": 0,
  "source_2.metadata.compiled_batch_seconds": 0.0,
  "source_2.metadata.eligible_element_count": 0,
  "source_2.metadata.fallback_element_count": 1,
  "source_2.metadata.fallback_reasons": {
    "below_recovery_plan_threshold": {
      "element_ids": [
        1
      ],
      "minimum_size": 100
    }
  },
  "source_2.metadata.native_thread_policy": {
    "phase": "stress_recovery_serial",
    "requested_threads": null,
    "restored": true,
    "status": "not_needed_serial"
  },
  "source_2.metadata.plan_reused": false,
  "source_2.metadata.recovery_backend": "scalar_legacy_small_selection"
}
```

### linear_static

```json
{
  "source_0.assembly.stiffness.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_0.convergence_info.backend": {
    "auto_backend_policy": "scipy_small_matrix",
    "backend": "scipy_superlu",
    "factorization_count": 1,
    "factorization_time": 0.00020194053649902344,
    "failure_reason": null,
    "last_solve_thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "linear_solve",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    },
    "matrix_class": "symmetric_indefinite",
    "ordering": "COLAMD",
    "pypardiso_active_min_dimension": 10000,
    "pypardiso_active_min_nnz": 250000,
    "pypardiso_compatible_pattern_before_selection": false,
    "pypardiso_initialized": false,
    "pypardiso_initialized_before_selection": false,
    "pypardiso_min_dimension": 10000,
    "pypardiso_min_nnz": 250000,
    "pypardiso_retained_pattern_slots_before_selection": 0,
    "pypardiso_warm_thresholds_active": false,
    "shape": [
      18,
      18
    ],
    "signature": null,
    "solve_count": 1,
    "solve_time": 3.719329833984375e-05,
    "status": "ok",
    "thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "factorization",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    }
  },
  "source_0.result_case.solver_backend": "scipy_superlu",
  "source_0.thread_policy": {
    "active_solver_threads": null,
    "fallback_reason": null,
    "limiter_available": true,
    "requested_assembly_threads": null,
    "requested_solver_threads": null,
    "runtime_pools": [
      {
        "internal_api": "openblas",
        "num_threads": 1,
        "prefix": "libscipy_openblas",
        "user_api": "blas",
        "version": "0.3.31.dev"
      },
      {
        "internal_api": "openblas",
        "num_threads": 1,
        "prefix": "libscipy_openblas",
        "user_api": "blas",
        "version": "0.3.29.dev"
      },
      {
        "internal_api": "openmp",
        "num_threads": 32,
        "prefix": "vcomp",
        "user_api": "openmp",
        "version": null
      }
    ]
  }
}
```

### modal

```json
{
  "source_1.thread_policy": {
    "active_solver_threads": null,
    "fallback_reason": null,
    "limiter_available": true,
    "requested_assembly_threads": null,
    "requested_solver_threads": null,
    "runtime_pools": [
      {
        "internal_api": "openblas",
        "num_threads": 1,
        "prefix": "libscipy_openblas",
        "user_api": "blas",
        "version": "0.3.31.dev"
      },
      {
        "internal_api": "openblas",
        "num_threads": 1,
        "prefix": "libscipy_openblas",
        "user_api": "blas",
        "version": "0.3.29.dev"
      }
    ]
  }
}
```

### nonlinear_impact

Unavailable diagnostics: `internal_work`

```json
{
  "source_0.contact_public_materialization_count": 21,
  "source_0.contact_work_buffer.lazy_public_materialization": true,
  "source_0.contact_work_buffer.public_materialization_count": 21,
  "source_0.cutback_count": 0,
  "source_0.damage_matrix_plan_selection.cached_terms_refresh_count": 0,
  "source_0.damage_matrix_plan_selection.cached_terms_retained_bytes": 294912,
  "source_0.damage_matrix_plan_selection.fast_path_name": "incremental_damage_csr_updates",
  "source_0.damage_matrix_plan_selection.model_revision_fallback_count": 0,
  "source_0.damage_matrix_plan_selection.plan_update_fallback_count": 0,
  "source_0.direct_reduced_assembly_count": 0,
  "source_0.effective_stiffness_factorization": {
    "auto_backend_policy": "scipy_small_matrix",
    "backend": "scipy_superlu",
    "factorization_count": 1,
    "factorization_time": 9.34600830078125e-05,
    "failure_reason": null,
    "matrix_class": "symmetric_indefinite",
    "ordering": "COLAMD",
    "pypardiso_active_min_dimension": 10000,
    "pypardiso_active_min_nnz": 250000,
    "pypardiso_compatible_pattern_before_selection": false,
    "pypardiso_initialized": false,
    "pypardiso_initialized_before_selection": false,
    "pypardiso_min_dimension": 10000,
    "pypardiso_min_nnz": 250000,
    "pypardiso_retained_pattern_slots_before_selection": 0,
    "pypardiso_warm_thresholds_active": false,
    "shape": [
      54,
      54
    ],
    "signature": "sphere_impact.nl.effective:0.002500000000000002:6",
    "solve_count": 0,
    "solve_time": 0.0,
    "status": "ok",
    "thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "factorization",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    }
  },
  "source_0.factorization_count": 64,
  "source_0.factorization_reuse_count": 42,
  "source_0.full_coordinate_assembly_count": 130,
  "source_0.impact_reduced_assembly.direct_reduced_assembly_count": 0,
  "source_0.impact_reduced_assembly.direct_reduced_residual_assembly_count": 0,
  "source_0.impact_reduced_assembly.direct_reduced_tangent_assembly_count": 0,
  "source_0.impact_reduced_assembly.fallback_detail": null,
  "source_0.impact_reduced_assembly.fallback_reason": "plastic_damage_or_erosion_enabled",
  "source_0.impact_reduced_assembly.full_coordinate_assembly_count": 130,
  "source_0.initial_mass_factorization": {
    "auto_backend_policy": "scipy_small_matrix",
    "backend": "scipy_superlu",
    "factorization_count": 1,
    "factorization_time": 0.00013017654418945312,
    "failure_reason": null,
    "last_solve_thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "linear_solve",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    },
    "matrix_class": "symmetric_semidefinite",
    "ordering": "COLAMD",
    "pypardiso_active_min_dimension": 10000,
    "pypardiso_active_min_nnz": 250000,
    "pypardiso_compatible_pattern_before_selection": false,
    "pypardiso_initialized": false,
    "pypardiso_initialized_before_selection": false,
    "pypardiso_min_dimension": 10000,
    "pypardiso_min_nnz": 250000,
    "pypardiso_retained_pattern_slots_before_selection": 0,
    "pypardiso_warm_thresholds_active": false,
    "shape": [
      54,
      54
    ],
    "signature": "sphere_impact.nl.initial_mass",
    "solve_count": 1,
    "solve_time": 2.2172927856445312e-05,
    "status": "ok",
    "thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "factorization",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    }
  },
  "source_0.linear_matrix_terms_cached": true,
  "source_0.mass.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_0.nonlinear_config.max_cutbacks": 4,
  "source_0.nonlinear_config.tangent_reuse_iterations": 2,
  "source_0.refresh_reason_counts.missing_cached_factorization": 20,
  "source_0.refresh_reason_counts.reuse_budget_exhausted": 17,
  "source_0.result_case.analysis_case.settings.nonlinear.max_cutbacks": 4,
  "source_0.result_case.analysis_case.settings.nonlinear.tangent_reuse_iterations": 2,
  "source_0.result_case.solver_backend": "scipy_superlu",
  "source_0.tangent_assembly_count": 64,
  "source_0.tangent_reuse": {
    "active_contact_set_changes": 4,
    "contact_classification_changes": 1,
    "enabled": true,
    "factorization_count": 64,
    "factorization_reuse_count": 42,
    "max_reuse_iterations": 2,
    "plastic_relative_threshold": 0.005,
    "plastic_state_change_max": 0.03779876201443244,
    "refresh_reason_counts": {
      "active_contact_set_change": 4,
      "contact_classification_change": 1,
      "damage_scale_change": 3,
      "deletion_change": 1,
      "first_iteration": 20,
      "missing_cached_factorization": 20,
      "plastic_active_set_change": 18,
      "plastic_state_change": 7,
      "residual_stall": 1,
      "reuse_budget_exhausted": 17
    },
    "residual_stall_ratio": 0.9,
    "tangent_assembly_count": 64,
    "tangent_reuse_count": 42
  },
  "source_0.tangent_reuse_count": 42
}
```

### nonlinear_impact_direct_reduced

```json
{
  "source_0.contact_public_materialization_count": 49,
  "source_0.contact_work_buffer.lazy_public_materialization": true,
  "source_0.contact_work_buffer.public_materialization_count": 49,
  "source_0.cutback_count": 0,
  "source_0.damage_matrix_plan_selection.cached_terms_refresh_count": 0,
  "source_0.damage_matrix_plan_selection.cached_terms_retained_bytes": 0,
  "source_0.damage_matrix_plan_selection.fast_path_name": "incremental_damage_csr_updates",
  "source_0.damage_matrix_plan_selection.model_revision_fallback_count": 0,
  "source_0.damage_matrix_plan_selection.plan_update_fallback_count": 0,
  "source_0.direct_reduced_assembly_count": 107,
  "source_0.effective_stiffness_factorization": {
    "auto_backend_policy": "scipy_small_matrix",
    "backend": "scipy_superlu",
    "factorization_count": 1,
    "factorization_time": 0.00010991096496582031,
    "failure_reason": null,
    "last_solve_thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "linear_solve",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    },
    "matrix_class": "symmetric_indefinite",
    "ordering": "COLAMD",
    "pypardiso_active_min_dimension": 10000,
    "pypardiso_active_min_nnz": 250000,
    "pypardiso_compatible_pattern_before_selection": false,
    "pypardiso_initialized": false,
    "pypardiso_initialized_before_selection": false,
    "pypardiso_min_dimension": 10000,
    "pypardiso_min_nnz": 250000,
    "pypardiso_retained_pattern_slots_before_selection": 0,
    "pypardiso_warm_thresholds_active": false,
    "shape": [
      4,
      4
    ],
    "signature": "sphere_impact.nl.effective:0.002499999999999988:1",
    "solve_count": 1,
    "solve_time": 8.344650268554688e-06,
    "status": "ok",
    "thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "factorization",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    }
  },
  "source_0.factorization_count": 63,
  "source_0.factorization_reuse_count": 43,
  "source_0.full_coordinate_assembly_count": 1,
  "source_0.impact_reduced_assembly.direct_reduced_assembly_count": 107,
  "source_0.impact_reduced_assembly.direct_reduced_residual_assembly_count": 44,
  "source_0.impact_reduced_assembly.direct_reduced_tangent_assembly_count": 63,
  "source_0.impact_reduced_assembly.fallback_detail": null,
  "source_0.impact_reduced_assembly.fallback_reason": null,
  "source_0.impact_reduced_assembly.full_coordinate_assembly_count": 1,
  "source_0.initial_mass_factorization": {
    "auto_backend_policy": "scipy_small_matrix",
    "backend": "scipy_superlu",
    "factorization_count": 1,
    "factorization_time": 0.0001201629638671875,
    "failure_reason": null,
    "last_solve_thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "linear_solve",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    },
    "matrix_class": "symmetric_semidefinite",
    "ordering": "COLAMD",
    "pypardiso_active_min_dimension": 10000,
    "pypardiso_active_min_nnz": 250000,
    "pypardiso_compatible_pattern_before_selection": false,
    "pypardiso_initialized": false,
    "pypardiso_initialized_before_selection": false,
    "pypardiso_min_dimension": 10000,
    "pypardiso_min_nnz": 250000,
    "pypardiso_retained_pattern_slots_before_selection": 0,
    "pypardiso_warm_thresholds_active": false,
    "shape": [
      4,
      4
    ],
    "signature": "sphere_impact.nl.initial_mass",
    "solve_count": 1,
    "solve_time": 3.62396240234375e-05,
    "status": "ok",
    "thread_policy": {
      "coordination": "reader_inherited",
      "fallback_reason": null,
      "limiter_available": true,
      "phase": "factorization",
      "pools_active": [],
      "pools_after": [],
      "pools_before": [],
      "requested_threads": null,
      "restored": true,
      "status": "inherited_default"
    }
  },
  "source_0.linear_matrix_terms_cached": false,
  "source_0.mass.diagnostics.vectorized_shell_groups.0.backend": "numba",
  "source_0.nonlinear_config.max_cutbacks": 4,
  "source_0.nonlinear_config.tangent_reuse_iterations": 2,
  "source_0.refresh_reason_counts.missing_cached_factorization": 48,
  "source_0.refresh_reason_counts.reuse_budget_exhausted": 13,
  "source_0.result_case.analysis_case.settings.nonlinear.max_cutbacks": 4,
  "source_0.result_case.analysis_case.settings.nonlinear.tangent_reuse_iterations": 2,
  "source_0.result_case.solver_backend": "scipy_superlu",
  "source_0.tangent_assembly_count": 63,
  "source_0.tangent_reuse": {
    "active_contact_set_changes": 2,
    "contact_classification_changes": 0,
    "enabled": true,
    "factorization_count": 63,
    "factorization_reuse_count": 43,
    "max_reuse_iterations": 2,
    "plastic_relative_threshold": 0.005,
    "plastic_state_change_max": 0.0,
    "refresh_reason_counts": {
      "active_contact_set_change": 2,
      "first_iteration": 48,
      "missing_cached_factorization": 48,
      "residual_stall": 1,
      "reuse_budget_exhausted": 13
    },
    "residual_stall_ratio": 0.9,
    "tangent_assembly_count": 63,
    "tangent_reuse_count": 43
  },
  "source_0.tangent_reuse_count": 43
}
```

### nonlinear_internal

```json
{
  "source_0.5.batch_b_installed": true,
  "source_0.5.constitutive_fallback": null,
  "source_0.5.elastic_fast_path_batch_count": 1,
  "source_0.5.elastic_fast_path_element_count": 4,
  "source_0.5.generalized_elastic_fast_path_batch_count": 0,
  "source_0.5.generalized_elastic_fast_path_element_count": 0,
  "source_0.5.orthotropic_elastic_fast_path_batch_count": 0,
  "source_0.5.orthotropic_elastic_fast_path_element_count": 0,
  "source_0.5.plastic_batch_count": 0,
  "source_0.5.quadratic_beam_batch_count": 0,
  "source_0.5.shell_batch_count": 1
}
```

## Methodology and reproduction

Cases use fixed meshes, fixed random seeds, fixed continuation/time-step bounds, and optional per-case subprocess timeouts. Iteration, retry, and cutback counts are compared where exposed. Timing and memory are informational and must be evaluated with the separate matched performance benchmark.

```powershell
$env:PYPARDISO_MKL_RT = '<path-to-mkl_rt.dll>'
$harness = 'C:\Github\ANYsolver-verification\scripts\verify_sol_ultra_numerics.py'
C:\Github\ANYsolver\.venv\Scripts\python.exe $harness capture --solver-root C:\Github\ANYsolver-baseline --label baseline --suite full --output baseline.json
C:\Github\ANYsolver\.venv\Scripts\python.exe $harness capture --solver-root C:\Github\ANYsolver-candidate --label candidate --suite full --output candidate.json
C:\Github\ANYsolver\.venv\Scripts\python.exe $harness compare --baseline baseline.json --candidate candidate.json
```
