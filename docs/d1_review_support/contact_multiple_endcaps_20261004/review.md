# Supporting review: multiple fixed-rigid physical ends

Scope: current `src/anysolver/general_contact/multiple_beam_rigid.py` and its scoped diff in `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`; inspected the plane child result field spelling. No imports or tests executed. Same-family supporting scrutiny, not engineering acceptance.

## Concrete finding

`MultipleBeamRigidResults.to_dict` sums `field.get('candidate_endpoints', 0)`, but `_BeamPlaneResults.to_dict` publishes `endpoint_candidates`. Every plane child's physical-end candidates are silently omitted from the aggregate. A composition containing only hemisphere plane children therefore reports zero candidates even with active endpoints. Normalize the plane spelling at this composition boundary while preserving the legacy child schema. Add a mixed plane/radial/capped result check, including two interactions targeting the same body.

## Other inspected mechanics

- The residual and tangent sum complete child outputs on common global coordinates; no additional endpoint force is assembled at the composition level.
- Duplicate `(element, body.name)` pairs reject before child construction. With the existing all-material-node physical-end topology, different elements sharing a node do not each create a physical end there. The same end against distinct explicitly declared bodies is separate pair work, not accidental duplicate assembly.
- Pair and per-body force/moment sums retain the children's common world origin. Sorted interaction construction keeps body-name/result associations aligned.
- The common trial fraction is rechecked through every child's full swept predicate, so a smaller fraction is not assumed automatically safe for ownership events. Any child exception fails the operation; no child failure is silently dropped.
- Restart embeds each child's complete contract and the aggregate candidate limit. The new profile separates hemisphere/capped-cylinder compositions; legacy no-cap plane/sphere/infinite-cylinder profile, summation order, and restart shape are retained by the inspected diff.
- Moving bodies and non-penalty laws remain rejected by `_parts`; child validation continues to enforce the specific geometry and mechanics restrictions.

No further concrete mechanics defect found within this bounded scope. Important integration discriminators are a child-specific swept rejection propagating through the common fraction, full mixed-child directional tangent, and restart rejection after one child's endpoint stiffness or topology changes.

## Delta: regularity and limiter composition

The plane candidate-count spelling is now normalized. The new regularity checks deduplicate physical cells by element ID and cover initial, evaluated, and swept configurations for `PROFILE_ENDS` only.

No concrete limiter or restart defect found in this delta. The regular prefix is established before invoking child trial limiters; their returned fractions are correctly multiplied by that prefix scale. The final actual endpoint is then rechecked against both regularity and every child's swept predicate. Failure to certify within the declared loop limits returns zero/false. The new composition revision distinguishes this contract, while the old no-cap branch retains its previous revision and limiter arithmetic.

Diagnostic caveat: reductions made exclusively by the initial regular-prefix loop do not increment the composition's `swept_trial_cutbacks`; a successful shortened trial can consequently leave that counter unchanged. This does not invalidate the mechanical certificate, but the counter should not be interpreted as counting every regularity-induced step reduction.

No tests executed or author test results independently accepted in this delta review.

## Lead disposition

The aggregate now counts regular-prefix reduction once per proposal, including
exhaustion. The hidden-collapse test checks that the counter increases. Plane
candidate counts normalize both child spellings; mixed-plane/radial/capped tests
assert four pair/end candidates and two active ends. Installed27checks pass with
the common limiter, shared-body wrench, independent two-ended bar, restart,
cleanup and legacy/no-contact cases. These are author-run checks recorded in
summary.json, not a reviewer execution or independent engineering acceptance.
