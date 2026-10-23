# Single elastic law for qualified Q4 (implementation target, implemented on the R4 line, 2026-10-23)

Owner decision 2026-10-23: full replacement. Qualified Q4 elements without a
hardening curve use the same assumed-strain kernel as R4 (return map skipped,
von Karman cross terms on), so one elastic law holds in von Karman and
corotational nonlinear analyses. The owner waived elastic bit-identity for
qualified-Q4 nonlinear elastic results. Linear analyses and every non-Q4 path
(beams, legacy shells, S3) must stay bit-identical.

## HANDOVER (state at end of session, 2026-10-23)

Branches and tips:
* R4 line `claude/plastic-repair-20261023` = **4766868e7**. R4 plus review fixes,
  P2 test fixes, docs and staged contractions. Single law not yet merged into it.
* Single-law work `claude/plastic-repair-singlelaw-20261023` (worktree
  `.worktrees/singlelaw`) = this commit, on top of 4766868e7:
  0c2c48e41 (prototype routing), 0ce738657 (elastic initial fields), plus a test
  and handover commit.
* Scratch: `claude/plastic-repair-staged-20261023` 29fe95d83 (already applied to
  R4 as 4766868e7).

Done (single-law branch):
* Curve-less isotropic planar qualified Q4 is routed through `kernel_batch`
  with curve None:
  * `_q4_assumed_strain_plasticity.py:157` `elastic_route`, `:165` `route`, `:441` (no return map);
  * elastic initial fields as a constant layer offset: `:303` `layer_offsets`, `:428`.
* Scalar route: `e4_pl_element.py:4346` (`_assumed_strain_kernel`, elastic branch `:4368`).
* Direct compensated elastic route bypassed: core `:6328`, committed replay `:6364`.
* Reference batch: `nonlinear_static.py:1360` (group key), `:1487` (direct route skipped).
* Plans: `nonlinear_performance.py:1044` (batch kind); batch-B elastic fast path
  excluded: `nonlinear_performance_batch_b.py:521`.
* Element level: curve and no-curve elements agree to 5e-16 before yield. FD
  tangent 3e-10, also with initial fields (symmetric, FD 3e-11).
* Mixed-mesh test passes: `test_single_elastic_law_mixed_mesh_matches_pure_meshes`
  (von Karman and corotational, curve/plain/mixed agree to 1e-9).
* Linear static and stiffness hashes unchanged (n=8 plate, both material kinds).

Not done:
* The 12 tests below pin the old law or the bypassed routes: decide, re-baseline, document.
* Docs, CHANGELOG, source-binding records.
* Elastic-size table versus ccx, cost measurements, ANYfem barge, full test-set comparison.
* The plastic-law version tag (old-history refusal option C was tried on R4 and
  withdrawn: R4's own restart states reach the migration point unsealed;
  documented HIGH).

## Tests that pinned the old elastic law or the retired routes (retargeted)

Decision (owner, 2026-10-23): option (b), one code path. Each change keeps the
test's intent and keeps or strengthens its oracle. No tolerance was weakened.

| test | pinned | retarget and reason | oracle | commit |
|---|---|---|---|---|
| c5_elastic_increment::test_scalar_direct_matches_inherited_law_and_components[0, +1, -1] | old law F = kernel + Cr u | new law F = kernel + Cr u + von Karman cross terms, same tolerances | independent `single_law_expected` (cross terms from the certified offset operator and the element's own Gauss data) | 739c78ac8 |
| c5_elastic_increment::test_actual_batch_assembly_uses_direct_offset_response -> test_actual_batch_assembly_uses_single_law_kernel | batch route = compensated direct route | batch assembly equals the single-law oracle; elastic route asserted | same oracle | 739c78ac8 |
| c5_elastic_increment::test_unsupported_routes_do_not_admit_direct_increment[custom_mapping, initial_field, yielding] (warped unchanged) | fallback = old law (exact) | direct-route admission assertions unchanged; fallback checked against the oracle (historical law on warped facets) | same oracle, 2e-12 | 739c78ac8 |
| c5_numpy_coordinate_admission::test_original_builder_cold_direct_activation[scalar, batch] | direct route activates for the original C5 builder inputs | the same inputs reach the single-law kernel (1 call for 1 element / 1 call for 4 elements); no direct-route call | profile hook on the actual kernel body, no replacement | 739c78ac8 |
| batch_b::test_batch_b_reuses_plan_buffers, ::test_elastic_batch_releases_history_work_arrays, ::test_isotropic_batch_build_reuses_one_constitutive_matrix, ::test_elastic_batch_does_not_overwrite_recovered_stress_with_zero | batch-B elastic fast path for qualified Q4 | same assertions on legacy shells (formulation='legacy'), which keep that path; new test asserts qualified Q4 uses the single-law batch kind, not batch-B | unchanged assertions | aa11a1cc3 |
## Remaining implementation steps (one line each)

1. DONE: option (b) chosen. Tests retargeted (table above). Cost within 1.5x of main (Cost section in the assumed-strain doc).
3. Merge the single-law commits into `claude/plastic-repair-20261023` (cherry-pick 0c2c48e41, 0ce738657 and the test/handover commit).
4. Re-run: C1 elastic regime n=4/8/16/32 (von Karman and corotational) against ccx 11.79 mm. Scratch scripts: `mixed3.py` and `mixed3_drive.py` in `C:\Users\AUDUNA~1\AppData\Local\Temp\claude\C--Github\c394618d-7d19-4caf-91f9-544fa9e83efd\scratchpad\pr`.
5. Re-run the hashes: five elastic cases (`hashes.py`, will now change), linear static (`linproof.py`), beams/non-Q4 shells (add a case), and the ANYfem barge (`barge.ps1`, linear: expect 5513c61fb259).
6. Cost: elastic nonlinear plate 4x4/8x8/16x16, corotational, arc-length, compared with R4 and main (batch-B fast path loss in option b).
7. Run the plastic test set (109 files, 11 shards: `shard.py <tag> 11`) and the 133-file single-law set (`shard.py <tag> 11 sl_files.txt <repo>`). Compare failing IDs with main.
8. Docs: update `docs/Q4_ASSUMED_STRAIN_PLASTICITY_20261023.md` (drop the mixed-mesh limitation; record the waiver and the elastic sizes), the CHANGELOG, and rebind source-binding records if a test reports them.

Resume command for the unfinished R4 baseline shards:
`py -3.14 <scratch>\pr\shard.py r4sl 11 <scratch>\pr\sl_files.txt C:\Github\ANYsolver\.worktrees\plastic-repair`

## Hazards

* The compensated direct elastic route (general-contact C5) exists to keep elastic
  increments exact under cancellation. Bypassing it may change contact restart and
  precision properties beyond the tests above. Option (a) avoids this.
* Batch-B elastic fast path loss: elastic nonlinear qualified Q4 gets slower (not measured).
* Orthotropic elastic and generalized-section qualified Q4 stay on the historical
  elastic law (the kernel is isotropic only). Different materials anyway, so there
  is no same-material interface effect.
* Recorded hashes in evidence/fixtures that pin nonlinear elastic Q4 bits outside
  the 133 files were not searched yet.

## OPEN-LOW items (Codex static review of 01cef1443, coordinator triage 2026-10-23)

* tests/test_e4_pl_s3_mixed_mesh_manifest.py (~509): the governed manifest was
  already red at base (the binding record bytes no longer match
  Q4_SOURCE_BINDING_SHA256). Its two pins on the retargeted C5 test files are
  now also stale. The predecessor binding is kept unchanged as history; a
  successor record is owed with the next full source rebinding (not a
  mechanical one-line change).
* tests/test_general_contact_c5_numpy_coordinate_admission.py (~177,
  mutation/cancellation) and tests/test_general_contact_compensated_contractions.py
  (~115, compensated dependency) still call the retired
  `_elastic_increment_response` helper directly. The helper still exists and is
  guarded, so the checks are valid for it. They are not yet retargeted through
  the single-law production route.
