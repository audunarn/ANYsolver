# Element activity and S4 integration handoff

## Delivery identity

- Branch: `native_hybrid_mesher`
- Baseline SHA: `61e2f45ae2ca4fa87a6e149b0f89fabf209e5279`
- Delivery commit: `1fd1c19`
- Owner: current native-hybrid-mesher task

## Owned changed paths

- `src/anysolver/activity.py`: canonical activity, deletion, restart, filtering, coupling, orphan-DOF, and diagnostic state.
- `src/anysolver/__init__.py`: public activity exports.
- `src/anysolver/fe_core.py`: `FEMesh.element_activity`, revision signature, and exact-ID model updates.
- `src/anysolver/boundary.py`: element-owned load, pressure, and gravity activity scaling; nodal loads remain node-owned.
- `src/anysolver/matrix_assembly.py`: local stiffness, mass, geometric-stiffness, damping, and follower-tangent scaling before scatter; zero-CSR compaction and diagnostics.
- `src/anysolver/assembly.py`: activity-aware reaction assembly.
- `src/anysolver/contact.py`: shared activity/deletion composition with contact and erosion ownership.
- `tests/test_element_activity.py`: policy, deletion, restart, filtering, coupling, orphan, and diagnostic contract tests.
- `tests/test_element_activity_integration.py`: assembly and load-path integration tests.

S4 should keep formulation and reference additions in disjoint modules until this delivery commit is available. It must not introduce a second activity map or scale global assembled matrices after constraints.

## Public seam

`ElementActivity(element_ids, activity=None, *, policy=None)` owns stable element IDs and dense activity values. Its required integration methods are:

- Mutation: `set_activity`, `soften`, `apply_damage`, `hard_delete`/`delete`.
- Contribution scales: `stiffness_scales`, `mass_scales`, `damping_scales`, `load_scales`, `contact_scales`, and generic `scale`/`scale_contributions`.
- Ownership filters: `load_filter`, `contact_filter`, `filter_loads`, `filter_contacts`.
- Couplings and topology diagnostics: `resolve_couplings`, `detect_orphan_dofs`, `find_orphan_dofs`.
- Restart: `restart_state`/`to_restart`, `load_restart`/`restore_restart`, `serialize`/`deserialize`.
- Qualification diagnostics: `conditioning_diagnostics`, `removed_mass_energy_diagnostics`, `diagnostics`.

Policies are expressed by `ElementActivityPolicy`/`ActivityPolicy`, `ContributionPolicy`, and `CouplingPolicy`. Hard deletion is irreversible unless an explicitly configured policy permits healing. Activity is applied to element-local contributions before assembly so constraints, reactions, eigenproblems, contact, and nonlinear tangents see one consistent operator.

## Merge order

1. Commit and publish this activity delivery on `native_hybrid_mesher`.
2. Rebase S4 onto that delivery, or merge/cherry-pick this delivery before S4 touches any owned hot-path file.
3. Route new S4 local stiffness, mass, geometric, damping, load, follower, and contact contributions through `ElementActivity`; do not copy policy logic.
4. Resolve any shared-file edits by retaining activity-before-scatter behavior and then layering S4 formulation calls around it.
5. Run the combined matrix below after integration.

## Combined regression matrix

- Activity contract: `tests/test_element_activity.py` and `tests/test_element_activity_integration.py`.
- Constraint and restart ownership: `tests/test_constraint_audit.py`, plus S4 restart tests.
- Linear/eigen: mass/modal and buckling suites.
- Transient/contact: dynamics and full contact suites.
- Nonlinear: static, limit-point, DNV, diagnostics, state-batch, and state-lifecycle suites.
- S4 formulation/reference/qualification modules added on its branch.

Current accepted full functional solver-mode evidence is 109 passed in 67.58 seconds for contact, nonlinear static/limit-point/DNV, nonlinear diagnostics/state, dynamics, modal, and buckling modules. This is functional regression evidence only, not scaling or performance evidence.
