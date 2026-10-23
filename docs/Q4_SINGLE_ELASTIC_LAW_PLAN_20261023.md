# Single elastic law for qualified Q4 (implementation target, 2026-10-23)

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

## Tests that pin elastic bits or the bypassed routes (single law vs R4, same 133 files)

R4 baseline was partial (shards 5 and 10 not finished; resume command below).

| test | what it pins | kind of change |
|---|---|---|
| test_general_contact_c5_elastic_increment.py:45 test_actual_batch_assembly_uses_direct_offset_response | qualified Q4 uses the compensated direct elastic route | real: route no longer used for qualified Q4 |
| ...:103 test_scalar_direct_matches_inherited_law_and_components[+-1] | force == old law (inherited + Cr u) to 2e-12 | real: new law adds cross terms (0.7 % here) |
| ...:117 test_unsupported_routes_do_not_admit_direct_increment[custom_mapping, initial_field, yielding] | admission predicate of the direct route | real: direct route is now never admitted for qualified Q4 |
| test_general_contact_c5_numpy_coordinate_admission.py:60 test_original_builder_cold_direct_activation[batch, scalar] | direct route activates | real: same as above |
| test_nonlinear_performance_batch_b.py:70 / :90 / :129 / :217 (reuses plan buffers, recovered stress, releases work arrays, one constitutive matrix) | batch-B elastic fast path used for qualified Q4 | real: fast path excluded for qualified Q4 |

No test failed because of a pure hash re-baseline. Every failure is a route or
law assertion.

## Remaining implementation steps (one line each)

1. Design choice (owner): either (a) keep the compensated direct route and the batch-B elastic fast path and ADD the cross terms there (`e4_pl_element.py:6484` `_elastic_increment_response`; `nonlinear_performance_batch_b.py` elastic kernel), preserving their precision and speed; or (b) accept the bypass and rewrite the 12 tests to assert the new routing.
2. If (b): rewrite the 12 tests listed above with stated reasons; no weakened tolerances.
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
