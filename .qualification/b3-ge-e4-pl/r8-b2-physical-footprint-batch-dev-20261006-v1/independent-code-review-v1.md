# Independent physical-footprint batch code review V1

2026-10-06. Supporting non-author OpenAI Read assessment. No numerical imports, runs, workers, Git actions or product edits. Current governing note is `docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md` (6 October); the older Current Checkpoint is historical. Body/F03/closed-campaign restrictions remain intact. This review concerns batching and public selected recovery, not renewed mechanics qualification or different-family acceptance.

## Inspection checkpoint

No consequential batch product defect was discovered in the candidate inspected below. Its five-row selection/result dispatch, retained data bounds and complete-prefix behavior are coherent with the existing batch contract. Candidate development testing is incomplete at this checkpoint: V1 preserves two failed test premises; the author is adding repaired/affected checks and an actual nonfirst-pad selection fixture. The final frozen follow-up and terminal evidence must be inspected before closing this review.

## Connected caller and recovery contract

`_stiffened_shell_b2_q4_panel_experimental.py:1859–1860` dispatches the physical selection validator only for the new family. Old six-row selection remains on its original path. The new selected case and batch result types (`493–505`) have distinct physical law identity, selected physical wrench records and compact multiplier/gap arrays. They do not inherit full displacement/reaction arrays.

Selected constraint rows (`1888–1890`) retain actual global row numbers, footprint/node identities and three translation/two director labels. Per-case extraction indexes the full completed static result using those global row IDs (`1958–1962`). Row metadata appears once per batch. It follows compiled incidence order; selected wrench order follows the requested footprint IDs. Two director multipliers remain work coefficients in the declared tangent basis; Cartesian couples are obtained through the existing actual `-C.T lambda` wrench service.

The route keeps one transient full static result/RHS at a time and retains only selected DOFs, reactions, requested member stations, selected pad wrenches and selected pad multiplier/gap values for completed cases. It does not retain an N-case full displacement or full-constraint matrix. Omitting `recover_members` preserves the existing batch default `{}`; single-solve `None` still has its original meaning. With no selected footprint, retained row/multiplier/gap/wrench tuples are empty. This is bounded retained storage proportional to requested outputs, not a claim of measured memory savings.

Typed physical body loads reject before any RHS solve (`1886–1887`); old POINT/body and six-row routes remain on the existing dispatch branches. Public modes/POINT coexistence restrictions are not loosened. Facade changes export the new result types; the adopted mechanical law is unchanged.

## Failure, mutation and lifetime

Inventory pairs and selection/recovery are owned before solving. Every load is initially snapshot/fingerprint validated (`1903–1909`), then rechecked immediately before its RHS (`1944–1946`). Invalid later loads therefore prevent a valid earlier RHS from being solved. Later value mutation is a programming/ownership error that propagates, rather than a numerical failed-prefix status. Callback exceptions also propagate. Replacing caller list pairs cannot rewrite the owned submitted inventory.

Counts are captured independently of factor lifetime (`1901–1902`) and updated from each static result. A failed result returns `failed` before appending a case (`1951–1952`), preserving only completed cases/envelopes and the failure's case identity. The case is appended only after complete physical solve/recovery, then its callback runs (`1973–1984`). Close/cancel after an intermediate completed case returns a cancelled prefix; close/cancel after the final completed case returns completed. Closing clears the owner's factor without invalidating captured counts or returned immutable records. The preflight/loop token checks retain the old cancellation meaning.

Factorization is eager in owner construction, not lazy on the first batch RHS. The correct refusal/pre-cancellation criterion is unchanged entry factorization/solve counts and zero additional RHS solves. Requiring initial factorization_count zero would alter an existing owner contract. Batch success should reuse the one eligible factorization; no new factor service is introduced.

## Meaningful tests and gaps returned to the owner

New tests cover 1/10/100 ordered cases, one-factor counts, selected output shapes, single-solve parity, member selection, signed first-case envelopes, no unselected recovery, immutable results, inventory/recovery mutation, changed later loads, callback errors, complete-prefix/final-close/final-cancel behavior, injected factor-solve failure before/after the first case, and public scaled-model/global-frame/member-reversal covariance. The dimensional transformation correctly scales E by force/length^2, area by length^2, inertias by length^4, translational loads by force and moments by force*length. This tests the batch/public path for the declared isotropic fixture; it is not broad material/geometry qualification.

Important initial coverage gap: all initial new batch cases used a single pad whose rows were 0..19. That cannot distinguish true subset extraction from retaining the entire constraint vector or using compact prefix indices. I returned an actual public multiple-disjoint-pad fixture selecting only a nonfirst pad: compare compact values to full single-result entries at advertised global row IDs and ensure no unselected wrench is recovered. Root/author are adding this control. Reversed selection order may additionally document the distinct row/wrench ordering.

Other initial gaps: direct typed-body-before-RHS refusal, an actual failed-factor status path in addition to an injected solve exception, and declared nonzero-prescription refusal/behavior if applicable. These are caller/development controls, not authority for a body campaign. At inspection the reference-case document still said batching refused; updating that statement and stating bounded selection/order/lifetime behavior is a handoff obligation, not evidence of an absent implementation.

## V1 source and evidence binding

Runtime V1 source bindings for the inspected candidate:

- panel `a2474667e43067ddd2f81e30af656a2f99ae57dc78308ebca86668431554caf4`
- facade `c5e6d427cb9d1016ce6b949aa0485454f648a40310003ec54b92fe2b388c4f7b`
- new batch tests `812618c5f72fd6de0aa0054176e8150e2e231b6820fe3fce7ff4a228a1d1f4b9`
- existing physical-footprint tests `8f296eb56cd747b03af7f277d03e1b532f3f881b09c58a176c0ca6f93047256f`
- example `95bb6b383e8895003ba164f4615f25dbfc89da62401fc0f8a5dfc263017379f4`
- old six-row tests `77dc4a3a25950d4feac6c718e3e24fd7c80ff4db9a5192958d23af9e718f306d`

Actual V1 JUnit inspected: **26 tests, 2 failures, 0 errors/skips, 6.857 s**, hence 24 passes. Failures are `test_precancel_and_selection_refusal_do_not_factor` and `test_invalid_later_load_and_recovery_prevalidate_without_factor`, both expecting factorization_count zero where the owner has already factored once. Root reports supervised 10.81968 s / 224751616 bytes and is adjudicating effective runtime controls. The reviewer did not launch or poll the job and has not yet independently checked the final repaired runtime evidence. Original failures must remain preserved; repairing the test premise must not change product factory behavior or numerical tolerance.

## Remaining disposition

Handoff state: candidate inspected, V1 source-development evidence partially passing; focused repaired/new evidence pending. Root owns final integration and adoption. Full physical accuracy, external/refinement/drilling/cancellation-datum breadth, installed new-batch verification, complete F12/F13/B14 and different-family assessment are not established by this batch review. The unchanged prior mechanics is not redundantly reviewed here.

## Final focused V2 closure

The pending implementation/development concerns above are now resolved within this assigned slice. No consequential product correctness finding remains open from this batch review. Root retains final adoption/integration and all scientific/installed gates.

Product panel/facade hashes are unchanged between V1 and V2. The two failing tests now compare entry factorization/solve counts instead of expecting an unfactored owner. A new public three-cell/three-member/two-disjoint-pad fixture selects only the second pad: compact rows are exactly global IDs 20..39; multiplier/gap values match those indices in the full single result, and the selected wrench contains only that pad's actual nodes. This closes the subset-indexing/retention coverage gap. A metadata-only typed-body negative replaces RHS snapshot with a forbidden sentinel and proves rejection precedes every RHS snapshot; it performs no acceleration map/body driver or barred body campaign. The added nonzero-offset factory test forces actual factorization failure to propagate before an owner can return any offset-only case. It does not claim arbitrary prescribed offsets are now forbidden.

Actual V2 JUnit independently inspected: **5 tests, 0 failures/errors/skips, 1.640 s**. They are the two corrected entry-count controls, factory factor failure with offset, nonfirst disjoint-pad compact provenance and typed-body-before-RHS refusal. Receipt: child PID127120, exit0, supervised5.588849199935794 s, sampled tree RSS220495872 bytes, one numerical job, limits600 s/2 GiB. V1 receipt was also inspected: PID117008, exit1,10.819680700078607 s,224751616 bytes. Both effective post-runtime records confirm affinity[0], JITdisabled, Numba1 and all observed BLAS/OpenMP pools1, with pinned source/dependency origins. This is inspected author-run evidence; the reviewer ran no numerical job and sampled RSS is not peak-memory qualification.

Combining actual V1/V2 case identities gives **29 unique latest passing development cases**: 24 unaffected V1 passes plus five repaired/new V2 passes. Product and unchanged test/example bindings match across the runs; this is impact reuse, not a clean29-case campaign or29 scientific acceptances. Existing old six-row batch/lifetime controls remained in the executed selection. V1's failed records remain intact.

All six listed V2 worktree and `source-snapshot-v2` files matched their runtime SHA256 bindings. Panel/facade/existing footprint test/example/old six-row test hashes remain those recorded above. Final new batch test hash is `73640f4e8a8771084dd546dc3857fa702d2d4ff35510d884e56b578da6e182e4`.

The reference-case document now admits selected batches, states actual global row ordering versus requested wrench ordering, eager factor reuse, inventory/value mutation behavior, failed/cancelled complete prefixes, final-case close/cancel semantics and metadata-only body refusal. It distinguishes physical SI model scaling from alternate field units and local section sign conventions. Installed batch verification and aggregate/external/different-family/full F12/B14 remain explicitly open.

Final handoff state: **implemented and verified against the assigned source-development batch controls**, supported by non-author source/evidence review. Broader physical accuracy and the prior mechanics qualification gaps are unchanged. No new installed, performance-saving or different-family acceptance claim follows.

## Final caller-metadata delta

Root identified that both public methods' selection annotations still named only the historical selector. Final `solve_linear:1600` and `solve_linear_many:1839` now declare `B2NodalRigidFootprintSelection | B2PhysicalRigidFootprintSelection | None`, matching the existing runtime dispatch. The physical type was already imported; no runtime admission or implementation body changed.

Final panel SHA256 is `5f67a9604775dec26f9a0ada4703ee01b32ce4895a5934d5e92a090a0fd5f5a5`. I independently compared the complete final source text with the tested V2 snapshot after replacing exactly the two old annotation strings: equality is true. The author's `final-annotation-verification-v1.json` additionally records AST statement-body equality for both methods against tested panel `a2474667e43067ddd2f81e30af656a2f99ae57dc78308ebca86668431554caf4` and reports the correct final annotations.

No numerical rerun occurred after this metadata correction. The29 unique source-development passes apply by unchanged statement-body/dependency reuse; they are not execution of the final panel bytes. Fresh installed verification remains Root's subsequent gate. Root will bind this appended review independently because the author manifest preceded this final review hash. No remaining annotation finding is open.
