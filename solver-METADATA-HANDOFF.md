# solver-METADATA-HANDOFF (checkpoint, 2026-10-12)

Living checkpoint for the exported-model-metadata slice of the recovery
capsule work. Phase A (admission fixes + runtime wheel) is complete; this
note records the metadata source facts, extraction design, unknowns and the
candidate plan before implementation consumes the remaining budget.

## State so far

- Admission fixes landed in `src/anysolver_results/capsule.py`:
  present-None `reconstruction` refused (adopted string extension);
  `_as_float_array` catches `OverflowError` (10**400 weights, 2**100
  indices stay typed refusals).
- Focused admission tests added to `tests/test_result_capsule_runtime.py`
  (reconstruction extension, completed statuses, duplicate
  (quantity_id, component) pairs, oversized indices/weights, per-case
  active_indices admission).
- Evidence: `output/result-capsule/runtime-admission-check-004.txt`
  (27 passed, exit 0, process wall 2.326 s, threads=1; failed attempts 002
  and 003 were test-fixture errors, retained).
- Runtime wheel built: `packages/results/dist/anysolver_results-1.0.0-py3-none-any.whl`
  (`output/result-capsule/runtime-wheel-build-001.txt`, wall 1.739 s).

## Concrete source attributes (verified by reading, not assumed)

- `evaluator._snapshot` is `PreparedStaticSnapshot`
  (`prepared_static_snapshot.py`); `snapshot.recovery_compilation` is
  `Optional[PreparedRecoveryCompilation]` with `.elements:
  Mapping[int, CompiledElementRecovery]`.
- `CompiledElementRecovery.local_recipe` is `OwnedLocalRecovery`
  (`prepared_static_recovery.py`): `.execution_owner` is the PRIVATE
  captured model tuple `(owned_element, owned_mesh, owned_material)` —
  plain clones, never the live original model. Metadata must be read from
  these owners only.
- S3 (`QualifiedE4PLS3ShellElement`):
  - Frame: `triangle_frame(coordinates, reference_normal)` from
    `e4_pl_s3_element` (wraps `qualified_s3_triangle_frame` in
    `e4_pl_s3_state.py`): `frame = np.column_stack((first, second,
    normal))` — columns are the local axes in global coordinates;
    `frame @ T_local @ frame.T == T_global`, `frame.T` maps global
    components to local. Coordinates come from
    `owned_element.get_node_coordinates(owned_mesh)`;
    `owned_element.reference_normal` is the owner-normal attribute.
  - Sampling: `owned_element.gauss_points` (7x2 natural triangle (r, s))
    and `owned_element.gauss_weights` (7,) — the same station table the
    stress recovery loop consumes (`TRIANGLE_QUADRATURE`), native order.
  - Record fields are per-station vectors, shape (7,).
- Beam2 (`BeamElement`):
  - Frame: `_beam_rotation_matrix(e1, owned_element._orientation)` with
    `e1 = (coords[1]-coords[0])/length` from the owned mesh coordinates;
    same column convention (local axes in global; `T` uses `R.T` as
    global-to-local).
  - Sampling: plain beam2 recovery is one section envelope scalar per
    element; the source exposes NO station coordinates for it. Export an
    explicit `element_section_scalar` rule with an unavailable-reason for
    coordinates; never invent a centroid.
- Beam3 (`QuadraticBeamElement`): exposes `GAUSS_POINTS` (3 natural xi
  stations) on the owner; rule with natural xi coordinates.
- Other element types (e.g. Q4 shell): no source-exact frame/sampling
  extraction verified in this slice -> explicit unavailable reason, no
  inference from sample counts.

## Candidate plan (implementation)

1. `result_capsule.py`: new private helper `_model_recovery_metadata(...)`
   building a once-per-model plain-JSON mapping, emitted under the new
   header key `model_recovery_metadata` (ANYpost preserves header
   extensions under `source_metadata`; no sibling change needed):
   - `frames`: convention label + per-element 3x3 nested lists (exact
     source floats, from the private owners only).
   - `sampling_rules`: deduplicated shared rule table (content-keyed ids):
     triangle natural (r, s) coordinates + weights in native order; beam3
     natural xi; beam2 section-scalar with explicit
     `coordinates_unavailable_reason`.
   - `element_bindings`: element id -> frame availability, sampling rule
     id, sample count, native field shapes.
   - `unavailable`: explicit reasons wherever source-exact capture is
     missing (no recipe, unsupported type, missing owner attributes).
   - No factorisations, stiffness, executables or owner objects in the
   capsule; only finite plain-JSON numbers.
2. Descriptors: compact refs into the shared tables (sampling rule ids,
   frame table reference) — no per-case duplication, no huge per-component
   copies. Existing `element_shapes` compatibility preserved; stored
   (canonical-route) fields additionally get their source shapes recorded.
3. Consumer: optional `model_recovery_metadata` plain-JSON admission check
   in `validate_capsule` (mirrors `model_provenance` handling).
4. Tests (new focused metadata tests): rotated S3 frame orthonormal +
   source-exact; native coordinates source-exact + native order; original
   model mutation after preparation does not change captured metadata;
   canonical/fallback route retains metadata; stream header consistent
   with final capsule; metadata is finite plain JSON with no executable
   content.
5. Docs: `docs/RESULT_CAPSULE.md` + `packages/results/README.md`.

## Unknowns / decisions taken

- `local_recipe` can be `None` on `CompiledElementRecovery` (defensive):
  binding gets an explicit unavailable reason.
- Principal-stress components: exported per-rank shape [n]; the native
  (n, 3) source shape is recorded in the shared bindings, rank/surface stay
  in descriptor metadata (existing behavior unchanged).
- No timing claims; checks bounded <= 120 s each, threads=1, small
  authoritative fixtures only.
