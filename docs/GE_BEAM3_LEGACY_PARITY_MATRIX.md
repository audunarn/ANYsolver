# GE-B3 legacy parity matrix — frozen step 1

Baseline: ANYsolver 0.4.3, commit `74703a3202251edc0beafb21cd31f52c9304ceb8`, tree `64a18a8fe137946ec2f0d4841821a19066a2707f`.

Status: **planning inventory frozen; no new mechanics qualification**. This step changes no runtime, default, dependency, source equation or historical evidence. No scientific test was executed. Test links identify source definitions, not fresh passes.

## Scope and evidence rules

- Legacy B3 is the required element baseline. B2-only and synthetic/shared-framework tests identify additional obligations but do not certify B3 combinations.
- GE means the accepted native owned workflow. The older straight `ge-beam3` facade remains separate; neither interface inherits the other's acceptance.
- `TESTED` means a relevant test exists and was inspected, not full domain qualification. `PARTIAL` means scoped GE functionality exists but the broader route remains open.
- `LEGACY_REJECTED` includes explicit rejection or documented warning/skip. `LEGACY_PLACEHOLDER` is not physical functionality. Neither creates a requirement to copy a defect.
- `LEGACY_COVERAGE_UNESTABLISHED` requires a baseline audit/test before deciding whether it is parity work or a new capability. Absence of a test is not proof of unsupported code.
- Generic spring, shell-only, manifest and adapter tests are not beam numerical evidence. Parameter combinations must be expanded and inspected at the implementation gate.
- Full parity is closed only when each in-scope implementation obligation has accepted source, actual-route tests, reviewed evidence and an installed-wheel check. No percentage or estimated completion is inferred from this inventory.

## Required routes and current gaps

| ID | Route | Legacy evidence class | Current GE | Next disposition |
|---|---|---|---|---|
| P01 | Factory, topology, DOF mapping | B2_B3_IMPLEMENTED | PARTIAL | IMPLEMENT |
| P02 | Straight geometry, Q2 interpolation and axis conventions | B2_B3_TESTED | SCOPED_ACCEPTED | RETAIN_AND_INTEGRATE |
| P03 | Reference linear stiffness, rigid modes and slender response | B2_B3_TESTED | SCOPED_ACCEPTED | RETAIN_AND_INTEGRATE |
| P04 | Standard isotropic sections and coupled SPD section protocol | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P05 | Orthotropy, directional shear, torsion and Hill recovery | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P06 | Section eccentricity, mass centre and rotary inertia | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P07 | Generic static assembly, multiple RHS and solver caches | SHARED_ROUTE_TESTED | PARTIAL | IMPLEMENT |
| P08 | Partial rotational supports and prescribed motion | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P09 | Affine/multilevel MPC, shared rotations and constraints | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P10 | Mixed sections, beam networks and mixed element models | SHARED_ROUTE_TESTED | PARTIAL | IMPLEMENT |
| P11 | Nodal force/moment, gravity and load combinations | B2_TESTED_B3_COVERAGE_GAP | PARTIAL | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P12 | General distributed beam loads/couples and follower classes | LEGACY_COVERAGE_UNESTABLISHED | PARTIAL | VERIFY_LEGACY_FIRST |
| P13 | Von Karman nonlinear force/tangent and P-delta | B2_B3_TESTED | SCOPED_ACCEPTED | RETAIN_AND_INTEGRATE |
| P14 | Corotational rigid motion and large-rotation beam response | B2_B3_TESTED | SCOPED_ACCEPTED | RETAIN_AND_INTEGRATE |
| P15 | Physical fibre plasticity and loading/unloading/reversal | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P16 | Initial stress/strain and staged material history | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P17 | Newton, line search, force/displacement/arc controls | SHARED_ROUTE_TESTED | PARTIAL | IMPLEMENT |
| P18 | General restart, serialization, cancellation and rollback | SHARED_ROUTE_TESTED | PARTIAL | IMPLEMENT |
| P19 | Station recovery, fibre stresses and common result objects | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P20 | Consistent mass and physical mass summaries | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P21 | Nodal point mass and distributed edge mass | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P22 | Reference and current-rest modal analysis | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P23 | Geometric stiffness, prestress and eigenvalue buckling | B2_B3_TESTED | PARTIAL | IMPLEMENT |
| P24 | Damping, linear transient and prescribed time histories | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P25 | Finite-velocity finite-rotation dynamics | LEGACY_COVERAGE_UNESTABLISHED | GAP | NEW_CAPABILITY_NOT_PROVEN_LEGACY |
| P26 | Beam contact/impact and beam fracture | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P27 | Activity, softening and hard deletion | B2_TESTED_B3_COVERAGE_GAP | GAP | IMPLEMENT_WITH_B3_BASELINE_TEST |
| P28 | General beam-shell joints, eccentric stiffeners and plastic coupling | SHARED_ROUTE_TESTED | PARTIAL | IMPLEMENT |
| P29 | Production size, sparse assembly, sessions and reuse | SHARED_ROUTE_TESTED | GAP | IMPLEMENT |
| P30 | Scalar/batch dispatch and performance diagnostics | B3_TESTED | PARTIAL | IMPLEMENT |
| P31 | Generated model adapters and application routing | SHARED_ROUTE_TESTED | GAP | IMPLEMENT |
| P32 | Limit points and postbuckling from a genuine loading path | B2_TESTED_B3_COVERAGE_GAP | PARTIAL | IMPLEMENT_WITH_B3_BASELINE_TEST |
| U01 | Curved midside legacy B3 | LEGACY_REJECTED | SCOPED_ACCEPTED | NO_PARITY_OBLIGATION |
| U02 | Generalized-section corotational legacy B3 | LEGACY_REJECTED | PARTIAL | NO_PARITY_OBLIGATION |
| U03 | Generalized section plus legacy fibre-plasticity option | LEGACY_REJECTED | PARTIAL | NO_PARITY_OBLIGATION |
| U04 | Legacy corotational static fracture combination | LEGACY_REJECTED | UNESTABLISHED | NO_PARITY_OBLIGATION |
| U05 | Physical stress from arbitrary generalized resultants; nonspatial mass summary | LEGACY_REJECTED | SCOPED_ACCEPTED | NO_PARITY_OBLIGATION |
| U06 | Capacity-based damage for beam contact targets | LEGACY_REJECTED | UNESTABLISHED | NO_PARITY_OBLIGATION |
| U07 | Inherited compute_internal_forces placeholder | LEGACY_PLACEHOLDER | SCOPED_ACCEPTED | NO_PARITY_OBLIGATION |
| U08 | Hinge/end-release object and thermal load API | LEGACY_COVERAGE_UNESTABLISHED | UNESTABLISHED | VERIFY_LEGACY_FIRST |
| U09 | General history checkpoint through Element.to_dict | LEGACY_PLACEHOLDER | SCOPED_ACCEPTED | NO_PARITY_OBLIGATION |
| U10 | Free dead-prestress pencil without descending geometric operator | LEGACY_REJECTED | PARTIAL | NO_PARITY_OBLIGATION |

## Exact route notes and corresponding tests

### P01 — Factory, topology, DOF mapping

beam selects B2; quadratic_beam selects B3. Native GE uses separate owned factories; generic FEModel parity is not conferred by ge-beam3 (the older straight facade).

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_fe_solver_infrastructure.py::test_public_all_symbols_importable`
- `tests/test_quadratic_beam_nonlinear.py::test_quadratic_beam_tangent_is_consistent_with_internal_force`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_mixed_p3_optin.py`
- `tests/test_ge_beam3_public_workflows.py::test_no_alias_or_legacy_fallback_before_construction`

### P02 — Straight geometry, Q2 interpolation and axis conventions

Legacy straight-sided B3 and section-axis conventions have direct tests. Native straight/regular-curved definitions are accepted only with physical triad authority; implicit legacy roll must not be copied blindly.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_beam_axis_conventions.py::test_cantilever_strong_axis_deflection_matches_Iy`
- `tests/test_quadratic_beam_nonlinear.py::test_quadratic_beam_rejects_curved_midside_geometry`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py::test_public_definition_owner_real_solve_and_restart_unchanged`

### P03 — Reference linear stiffness, rigid modes and slender response

Keep existing GE algebra/slenderness acceptance. Integration tests need actual assembly and engineering response; do not demand identical element matrices from different discretizations.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_fe_solver_element_qualification.py::test_beam_qualification_metrics_cover_two_topologies_orientation_and_mass`
- `tests/test_beam_axis_conventions.py::test_cantilever_weak_axis_deflection_matches_Iz`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_mixed_p3_optin.py`

### P04 — Standard isotropic sections and coupled SPD section protocol

Legacy area/Iy/Iz/J/shear factors and external GeneralizedBeamSection protocol are not identical to native ellipsoid/fibre types. Provide explicit elastic/stateful adapters, including physical orientation and mass ownership.

Source: [src/anysolver/beam_sections.py](../src/anysolver/beam_sections.py).

Legacy test references:
- `tests/test_generalized_beam_sections.py::test_external_section_protocol_and_mapping_coercion`
- `tests/test_generalized_beam_sections.py::test_coupled_linear_energy_and_resultant_recovery`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py::test_unknown_section_and_foreign_provenance_rejected`

### P05 — Orthotropy, directional shear, torsion and Hill recovery

An anisotropic native resultant law is not automatic parity with the existing orthotropic material/fibre/Hill utilization contract. Map actual constitutive and physical recovery semantics.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_orthotropic_elements.py::test_quadratic_orthotropic_beam_matches_directional_energy_terms`
- `tests/test_orthotropic_elements.py::test_orthotropic_beam_fiber_plasticity_uses_x_strength`
- `tests/test_orthotropic_elements.py::test_beam_hill_equivalent_includes_xz_shear_and_torsion`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_generalized.py`

### P06 — Section eccentricity, mass centre and rotary inertia

Native physical inertia and one eccentric joint do not establish every legacy section-offset/mass-summary combination.

Source: [src/anysolver/mass_properties.py](../src/anysolver/mass_properties.py).

Legacy test references:
- `tests/test_generalized_section_mass_properties.py::test_physical_coupled_beam_mass_sets_mass_com_and_inertia`
- `tests/test_generalized_section_mass_properties.py::test_beam_section_offset_and_inertia_follow_local_frame_and_reference`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_coupled_modes.py`

### P07 — Generic static assembly, multiple RHS and solver caches

Native model-owned static solutions exist. General FEModel assembly, heterogeneous graph ownership and solver cache contracts must consume the current core explicitly.

Source: [src/anysolver/assembly.py](../src/anysolver/assembly.py).

Legacy test references:
- `tests/test_fe_solver_infrastructure.py::test_multiple_rhs_static_solve_matches_individual_solves`
- `tests/test_fe_solver_infrastructure.py::test_solve_linear_many_uses_revision_signature_for_factorization_cache`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_definition_graph_owns_real_native_model`

### P08 — Partial rotational supports and prescribed motion

Native ordinary supports are homogeneous and rotational triples all fixed or all free. Translation control does not supply general prescribed rotations/partial hinges.

Source: [src/anysolver/boundary.py](../src/anysolver/boundary.py).

Legacy test references:
- `tests/test_solver_control_contracts.py::test_force_control_ramps_nonzero_prescribed_displacement_by_increment`
- `tests/test_fe_solver_buckling.py::test_eigenvalue_buckling_returns_euler_column_scale_for_pinned_beam`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_unsupported_boundaries_rejected_during_construction`

### P09 — Affine/multilevel MPC, shared rotations and constraints

Legacy multilevel beam constraints have direct B2 fixtures. Native owners explicitly reject constraint_equations; shared SO(3) rotations require an objective constraint contract.

Source: [src/anysolver/constraint_audit.py](../src/anysolver/constraint_audit.py), [src/anysolver/assembly.py](../src/anysolver/assembly.py).

Legacy test references:
- `tests/test_phase2.py::test_multilevel_mpc_cantilever`
- `tests/test_solver_control_contracts.py::test_general_constraint_equation_uses_common_affine_transformation`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_model_mutation_rejected_before_state_initialization`

### P10 — Mixed sections, beam networks and mixed element models

One native family per owner, no arbitrary mixed FEModel. Generalized and physical-fibre families and multiple shell connections need shared ownership without fallback.

Source: [src/anysolver/fe_core.py](../src/anysolver/fe_core.py).

Legacy test references:
- `tests/test_generalized_section_api_workflows.py::test_generated_geometry_resolves_named_shell_and_beam_sections`
- `tests/test_fe_solver_anystructure_fem_mode.py::test_generated_beam_collections_are_additive_not_first_alias_only`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_no_cross_family_workflow_or_legacy_fallback`
- `tests/test_ge_beam3_public_workflows.py::test_public_coupled_owner_selects_exact_v2_with_real_replay`

### P11 — Nodal force/moment, gravity and load combinations

Native nodal/dead-line programmes are scoped. Integrate LoadCase/LoadCombination, density-based gravity, reference measures and reaction accounting; B2 gravity coverage is not B3 proof.

Source: [src/anysolver/boundary.py](../src/anysolver/boundary.py).

Legacy test references:
- `tests/test_fe_solver_mass_modal.py::test_load_combination_forwards_material_density_for_gravity`
- `tests/test_fe_solver_corotational_beam.py::test_corotational_beam_axial_extension_matches_ea_over_l_response`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_analysis_nodal_program.py`
- `tests/test_ge_beam3_native_distributed.py`

### P12 — General distributed beam loads/couples and follower classes

Native line/couple programmes exist; frozen inventory does not establish a general legacy distributed/follower BEAM load API. Shell follower-pressure tests do not prove it. Enumerate actual load entry points before expanding the obligation.

Source: [src/anysolver/boundary.py](../src/anysolver/boundary.py).

Legacy test references:
- `tests/test_follower_pressure.py`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_distributed.py`
- `tests/test_ge_beam3_native_spatial_couples.py`

### P13 — Von Karman nonlinear force/tangent and P-delta

Legacy B3 elastic/fibre tangents and P-delta have direct tests; native operators need general solver integration, not substitution by legacy kinematics.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_quadratic_beam_nonlinear.py::test_quadratic_beam_tangent_is_consistent_with_internal_force`
- `tests/test_quadratic_beam_nonlinear.py::test_quadratic_beam_p_delta_amplification_matches_2node_and_theory`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py::test_public_definition_owner_real_solve_and_restart_unchanged`

### P14 — Corotational rigid motion and large-rotation beam response

Legacy corotational fibre tests include both topologies. Preserve GE multiplicative rotations and admitted finite static evidence; legacy generalized B3 corotational exception is U02.

Source: [src/anysolver/corotational.py](../src/anysolver/corotational.py).

Legacy test references:
- `tests/test_corotational.py::test_corotational_fiber_plasticity_matches_von_karman_at_small_rotation`
- `tests/test_corotational.py::test_quadratic_beams_have_nonlinear_response_and_no_fallback_warning`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py`

### P15 — Physical fibre plasticity and loading/unloading/reversal

Native physical fibre and resultant laws already support scoped histories. Missing work is external material/section contract parity, cross-family models and normal solver use, not redoing accepted histories.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_quadratic_beam_nonlinear.py::test_quadratic_beam_fiber_plasticity_matches_2node_reference`
- `tests/test_material_history_recovery.py::test_unified_recovery_uses_beam_fiber_history_and_labels_mixed_fallback`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_analysis_fibre_translation.py`
- `tests/test_ge_beam3_native_fibre_restart.py`

### P16 — Initial stress/strain and staged material history

Legacy initial-field admissibility and provenance are tested with beam fibres. General initial-field injection into native owned histories is not accepted by the published API; no checkpoint resealing.

Source: [src/anysolver/initial_field_state.py](../src/anysolver/initial_field_state.py).

Legacy test references:
- `tests/test_initial_fields_and_staged_history.py::test_self_equilibrated_beam_fiber_stress_persists_and_has_separate_provenance`
- `tests/test_initial_fields_and_staged_history.py::test_beam_scalar_alpha_restart_broadcasts_to_all_fibers`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py`

### P17 — Newton, line search, force/displacement/arc controls

Dedicated GE drivers exist; unify ordinary dispatch, cutback, affine prescribed motion and accepted state ownership. Generic restart/arc tests use a spring and are explicitly not beam qualification.

Source: [src/anysolver/nonlinear_static.py](../src/anysolver/nonlinear_static.py).

Legacy test references:
- `tests/test_solver_control_contracts.py::test_force_control_restart_holds_supplied_prescribed_state`
- `tests/test_nonlinear_restart_checkpoint.py::test_arc_length_checkpoint_exact_nonzero_split_continuation`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_failed_native_force_preserves_only_valid_accepted_prefix`
- `tests/test_ge_beam3_native_arc.py`

### P18 — General restart, serialization, cancellation and rollback

Native authenticated restart/durable replay already works. Integrate general checkpoint/result contracts and establish scalable continuation without weakening old immutable checkpoints. Element.to_dict alone is not a history checkpoint.

Source: [src/anysolver/nonlinear_restart.py](../src/anysolver/nonlinear_restart.py).

Legacy test references:
- `tests/test_nonlinear_restart_checkpoint.py::test_checkpoint_rejects_duplicate_nonfinite_hash_and_model_mutation_before_assembly`
- `tests/test_solver_control_contracts.py::test_progress_observer_can_request_cooperative_cancellation`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_durable_coupled.py::test_cancel_after_commit_returns_prefix_replayable_by_fresh_facade`
- `tests/test_ge_beam3_public_workflows.py::test_public_definition_owner_real_solve_and_restart_unchanged`

### P19 — Station recovery, fibre stresses and common result objects

Legacy B3 station histories and weighted resultants are tested. Connect native objective recovery to standard FE results/visualization without inventing stresses for resultant-only sections.

Source: [src/anysolver/recovery.py](../src/anysolver/recovery.py).

Legacy test references:
- `tests/test_recovery_qualification.py::test_quadratic_beam_history_preserves_stations_and_weighted_resultants`
- `tests/test_fe_solver_element_quality.py::test_quadratic_beam_axial_stress_recovery_uses_end_nodes`
- `tests/test_material_history_recovery.py::test_create_fe_result_exposes_history_provenance_and_committed_states`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py`

### P20 — Consistent mass and physical mass summaries

Retain physical GE internal inertia; do not substitute static Schur reduction for dynamics. General mass assembly and summary protocols need integration.

Source: [src/anysolver/matrix_assembly.py](../src/anysolver/matrix_assembly.py).

Legacy test references:
- `tests/test_generalized_beam_sections.py::test_generalized_section_mass_matrix_overrides_material_geometry`
- `tests/test_generalized_section_mass_properties.py::test_physical_coupled_beam_mass_sets_mass_com_and_inertia`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_actual_reference_modal_retains_cell_inertia`

### P21 — Nodal point mass and distributed edge mass

Point mass has direct B2 modal tests; native owner rejects point_masses. Distributed edge mass is an API to inventory separately, not established by the point-mass test.

Source: [src/anysolver/boundary.py](../src/anysolver/boundary.py).

Legacy test references:
- `tests/test_fe_solver_mass_modal.py::test_point_mass_enters_mass_matrix_and_shifts_frequency`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_model_mutation_rejected_before_state_initialization`

### P22 — Reference and current-rest modal analysis

Legacy beam qualification and B2 free modes are covered; native scoped reference/current-rest pencils exist. General sparse modal, mixed graphs and mode selection need integration; active-yield states are not silently conservative.

Source: [src/anysolver/modal.py](../src/anysolver/modal.py).

Legacy test references:
- `tests/test_fe_solver_element_qualification.py::test_beam_qualification_metrics_cover_two_topologies_orientation_and_mass`
- `tests/test_fe_solver_mass_modal.py::test_free_free_beam_modal_solver_identifies_six_rigid_modes`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_actual_reference_modal_retains_cell_inertia`
- `tests/test_ge_beam3_coupled_modes.py`

### P23 — Geometric stiffness, prestress and eigenvalue buckling

B3 Euler and both-topology section Kg tests exist. Native frozen-current buckling is scoped; integrate common prestress consumers and constraints while preserving conservative-state restrictions.

Source: [src/anysolver/buckling.py](../src/anysolver/buckling.py).

Legacy test references:
- `tests/test_beam_axis_conventions.py::test_euler_column_quadratic_beam`
- `tests/test_generalized_beam_sections.py::test_generalized_geometric_stiffness_ignores_legacy_section_geometry`
- `tests/test_generalized_state_recovery.py::test_generalized_beam_recovery_and_prestress_use_committed_von_karman_state`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_coupled_modes.py`
- `tests/test_ge_beam3_native_buckling.py`

### P24 — Damping, linear transient and prescribed time histories

Legacy Newmark and activity-scaled Rayleigh damping tests exercise B2. Native current-rest modes do not establish transient solver parity; preserve physical internal coordinates.

Source: [src/anysolver/dynamics.py](../src/anysolver/dynamics.py).

Legacy test references:
- `tests/test_fe_solver_dynamics.py::test_newmark_step_load_matches_axial_sdof_solution`
- `tests/test_fe_solver_dynamics.py::test_newmark_undamped_free_vibration_conserves_energy`
- `tests/test_element_activity_integration.py::test_activity_scales_local_matrices_and_invalidates_revision`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py`

### P25 — Finite-velocity finite-rotation dynamics

Legacy transient/contact availability is not proof of objective finite-rotation inertia or gyroscopic terms. Native release excludes this domain. Freeze an independent dynamics extension if the user requires it, rather than relabel legacy tests.

Source: [src/anysolver/dynamics.py](../src/anysolver/dynamics.py).

Legacy test references:
- `tests/test_fe_solver_dynamics.py`
- `tests/test_nonlinear_impact_plasticity.py`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py`

### P26 — Beam contact/impact and beam fracture

Opt-in beam-segment contact and beam erosion have explicit B2 fixtures. Need B3 baseline confirmation and native contact/inertia/state integration. Capacity-based damage skips beam targets (U06).

Source: [src/anysolver/contact.py](../src/anysolver/contact.py).

Legacy test references:
- `tests/test_fe_solver_contact.py::test_beam_contact_targets_detect_strike_and_balance`
- `tests/test_fe_solver_contact.py::test_impact_fracture_erodes_struck_beam_target`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py`

### P27 — Activity, softening and hard deletion

Generated-beam activity scales K/M/C and hard deletion removes contributions without topology deletion. Native owner rejects activity; preserve rollback and accepted-state/provenance semantics.

Source: [src/anysolver/activity.py](../src/anysolver/activity.py).

Legacy test references:
- `tests/test_element_activity_integration.py::test_activity_scales_local_matrices_and_invalidates_revision`
- `tests/test_element_activity_integration.py::test_hard_deletion_keeps_topology_but_removes_contributions`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_model_mutation_rejected_before_state_initialization`

### P28 — General beam-shell joints, eccentric stiffeners and plastic coupling

Legacy generated coupling metadata/MPC routes exist. Accepted GE connection is one owned elastic Q4/S3 plus generalized beam; multiple joints and plastic/fibre-shell coupling remain open.

Source: [src/anysolver/mesh_gen.py](../src/anysolver/mesh_gen.py).

Legacy test references:
- `tests/test_fe_solver_anystructure_fem_mode.py::test_generated_beam_shell_coupling_metadata_is_preserved`
- `tests/test_mesher_improvements.py::test_stiffened_panel_adapter_preserves_neutral_numbering_and_couplings`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py::test_public_coupled_owner_selects_exact_v2_with_real_replay`
- `tests/test_ge_beam3_durable_coupled.py`

### P29 — Production size, sparse assembly, sessions and reuse

Native owner caps 16 elements with restricted N32. General sessions/caches exist in legacy framework; no unlimited-size guarantee is inferred. Qualify larger graphs, sparse paths and bounded restart/recovery cost before changing guards.

Source: [src/anysolver/analysis_session.py](../src/anysolver/analysis_session.py).

Legacy test references:
- `tests/test_analysis_session.py::test_modal_and_buckling_session_parity`
- `tests/test_fe_solver_infrastructure.py::test_factorization_cache_reuses_same_matrix_and_separates_changed_values`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py`

### P30 — Scalar/batch dispatch and performance diagnostics

Legacy B3 batch/scalar equality is directly tested. Release preserved B2/B3 timing baseline, not GE production throughput parity. Native batching is optional if scalar route meets defined application needs.

Source: [src/anysolver/nonlinear_performance_batch_b.py](../src/anysolver/nonlinear_performance_batch_b.py).

Legacy test references:
- `tests/test_nonlinear_performance.py::test_quadratic_beam_batch_matches_scalar_rotated_elements`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_delivery_gate.py`

### P31 — Generated model adapters and application routing

ANYsolver generated-geometry/ANYstructure-mode tests are not current ANYfem/ANYstructure UI qualification. Freeze sibling-specific adapter/test inventories before their integration; no sibling modifications in this step.

Source: [src/anysolver/mesh_gen.py](../src/anysolver/mesh_gen.py).

Legacy test references:
- `tests/test_fe_solver_anystructure_fem_mode.py::test_generated_stiffeners_and_girders_are_created_as_beams`
- `tests/test_generalized_section_api_workflows.py::test_generated_geometry_resolves_named_shell_and_beam_sections`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py::test_no_alias_or_legacy_fallback_before_construction`

### P32 — Limit points and postbuckling from a genuine loading path

Legacy tests demonstrate stopping near a limit point, not general stable postbuckling. GE signed/seeded unstable branches remain valid but cannot certify a stable from-rest path. Separate continuation parity from a new stable-branch claim.

Source: [src/anysolver/arc_length.py](../src/anysolver/arc_length.py).

Legacy test references:
- `tests/test_fe_solver_nonlinear_limit_point.py::test_nonlinear_load_stepping_stops_near_eigenvalue_limit_point`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_arc.py`

### U01 — Curved midside legacy B3

Legacy B3 rejects curved reference geometry. Native regular curved Q2 is an existing additional capability, not a missing legacy requirement.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_quadratic_beam_nonlinear.py::test_quadratic_beam_rejects_curved_midside_geometry`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py`

### U02 — Generalized-section corotational legacy B3

B3 rejects this combination; B2 generalized corotational support does not transfer to B3. Native coupled-section finite rotation may exceed the B3 baseline.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_generalized_beam_sections.py::test_cross_section_opt_in_and_ambiguous_inputs_fail_closed`
- `tests/test_generalized_beam_sections.py::test_generalized_beam2_corotational_response_routes_section_coupling`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_generalized.py`

### U03 — Generalized section plus legacy fibre-plasticity option

Legacy constructors reject mixing generalized_section and fiber_plasticity. Explicit native section laws remain separate; no contradictory combination is required for parity.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- `tests/test_generalized_beam_sections.py::test_cross_section_opt_in_and_ambiguous_inputs_fail_closed`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_analysis.py::test_no_cross_family_workflow_or_legacy_fallback`

### U04 — Legacy corotational static fracture combination

The legacy nonlinear-static corotational scope test rejects fracture. This does not erase the separate supported B2 impact-erosion route.

Source: [src/anysolver/nonlinear_static.py](../src/anysolver/nonlinear_static.py).

Legacy test references:
- `tests/test_corotational.py::test_corotational_scope_rejects_bad_kinematics_and_fracture`

GE test references (scope/implementation pointers, not new qualification):
- None claimed.

### U05 — Physical stress from arbitrary generalized resultants; nonspatial mass summary

Legacy generalized recovery deliberately lacks physical/von-Mises stress and nonspatial inertia cannot define physical mass summaries. Preserve those distinctions in GE adapters.

Source: [src/anysolver/beam_sections.py](../src/anysolver/beam_sections.py).

Legacy test references:
- `tests/test_generalized_beam_sections.py::test_coupled_linear_energy_and_resultant_recovery`
- `tests/test_generalized_section_mass_properties.py::test_non_spatial_generalized_beam_inertia_fails_scalar_summary`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py`

### U06 — Capacity-based damage for beam contact targets

Legacy emits an explicit warning that this damage model skips beams. It is distinct from beam fracture/erosion. Do not call shell capacity tests beam qualification.

Source: [src/anysolver/contact.py](../src/anysolver/contact.py).

Legacy test references:
- `tests/test_fe_solver_contact.py::test_capacity_impact_damage_warns_it_skips_beam_contact_targets`

GE test references (scope/implementation pointers, not new qualification):
- None claimed.

### U07 — Inherited compute_internal_forces placeholder

B2/B3 inherit Element.compute_internal_forces returning zeros. Physical force parity must use overridden compute_nonlinear_response, not reproduce the placeholder. Source assertion only; no dedicated legacy regression was found.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- None found for this precise claim; source-only boundary.

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_native_delivery_gate.py`

### U08 — Hinge/end-release object and thermal load API

Partial boundary restraints/MPCs are real requirements (P08/P09). A dedicated end-release or thermal-beam API and its B3 tests are not established by this audit. Do not turn generic shell/load tests into a legacy support claim.

Source: [src/anysolver/boundary.py](../src/anysolver/boundary.py).

Legacy test references:
- `tests/test_solver_control_contracts.py`

GE test references (scope/implementation pointers, not new qualification):
- None claimed.

### U09 — General history checkpoint through Element.to_dict

Element.to_dict exports ID/class/nodes/material only, not nonlinear history or full section definition. Real checkpoint parity belongs to P18.

Source: [src/anysolver/elements.py](../src/anysolver/elements.py).

Legacy test references:
- None found for this precise claim; source-only boundary.

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_public_workflows.py`

### U10 — Free dead-prestress pencil without descending geometric operator

Legacy explicitly rejects a free-free buckling pencil whose geometric operator does not descend to the quotient. Parity must preserve valid-domain rejection, not force eigenvalues from an inadmissible problem.

Source: [src/anysolver/buckling.py](../src/anysolver/buckling.py).

Legacy test references:
- `tests/test_fe_solver_buckling.py::test_free_free_dead_prestress_fails_closed_when_geometric_operator_does_not_descend`

GE test references (scope/implementation pointers, not new qualification):
- `tests/test_ge_beam3_coupled_modes.py`

## Completeness and limitations

The inventory binds 73 referenced source/test/status files and enumerates all 792 baseline `tests/test_*.py` modules by Git blob. Every public member declared by Element/B2/B3 is mapped to a row, including inherited placeholders. Constructors, public selectors and shared solver families are covered by the route rows. This is a closed snapshot inventory, not a proof of every dynamically reachable combination.

Other test modules remain visible as `NOT_USED_AS_DIRECT_PARITY_EVIDENCE`; they are not deleted, excluded from CI, or classified as scientifically irrelevant. The matrix does not claim to inventory live sibling repositories. ANYfem/ANYstructure consumer audits are an explicit P31 follow-up, not silently counted as covered by solver adapter tests.

Canonical matrix: [JSON](reference_cases/ge_beam3_legacy_parity_matrix_v1.json). Hash/object authority and complete test-module index: [inventory](reference_cases/ge_beam3_legacy_parity_inventory_v1.json).

## Recommended next step — general static integration contract

Freeze the current-core FEModel integration design for P01/P07/P08/P09/P10/P18/P20. Specify shared SO(3) state ownership, supported constraints, static internal elimination, retained physical inertia, heterogeneous sections and checkpoint transactions before coding. Begin with elastic straight/curved two-element and beam-network cases; add a B3 fixture where existing proof is B2-only. Reuse accepted GE records without rerunning closed campaigns.

Later gates: nonlinear/material and joint parity; transient/contact/activity; production scale and ecosystem consumers. Full finite-velocity dynamics and stable postbuckling must not be mislabelled as already-established legacy requirements.

Implementation remains a subsequent user-requested step. After each completed step, report its actual outcome and recommend the next gate. Scientific children remain bounded at 600 seconds/24 GiB/one numerical thread, at most three concurrent workers, 1800 seconds per wave and no automatic retry. This static audit needs no mechanics run.
