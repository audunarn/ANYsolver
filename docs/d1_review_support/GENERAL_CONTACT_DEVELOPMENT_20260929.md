# General contact — living task note

**Updated:** 29 September 2026. Worktree C:/ANYworkspaceWork/ANYsolver-general-contact, branch codex/general-contact-core. The user-designated [goal](GENERAL_CONTACT_GOAL.md) revision 2026-09-29.3 and [plan](GENERAL_CONTACT_PLAN.md) govern active D1-interior development. The full C0–C9 programme remains required. No independent acceptance or release is claimed.

**Policy transition:** Apply ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 revision 2026-09-24.2 prospectively. Preserve every programme numerical target, independent review, state/restart and installed-package gates, 5% no-contact regression, historical failures and frozen/consumed authorities. The new goal moves target-boundary cuts, active prescribed-edge pressure and source rim/tip contact to D2, and sets a prospective D1-interior pressure gate. It authorizes flexible sequencing, bounded development runs and selected D2 method options. This does not regrade prior evidence. [Archived history](docs/d1_review_support/GENERAL_CONTACT_RESTART_HISTORY_THROUGH_20260929.md) retains the preceding 26,140-byte note verbatim (SHA-256 B91EE2374611A9683776302A5840EFDD10E6E660DB46B3D30F097E3D57A1FD1C).

**Current candidate:** Fine nodal Q1 pressure, batched Jet2 Q4/S3 geometry and monolithic active-set static enforcement on the ordinary solver route. Existing four-Q4/two-S3 deformable-target press/slide/open/recontact and split-restart development paths work within their recorded bounds, but do not establish the newly scoped profile, three-mesh pressure stability, independent integrated response or D1 acceptance. The [D1 gap map](docs/GENERAL_CONTACT_D1_ACCEPTANCE_GAP_MAP.md) records reusable evidence and missing checks. The exact two-hat partial-overlap failure remains a D2 discriminator.

**Owned pause work preserved:** The unverified Q4 projected-shape inversion is parked in [this exact patch](docs/d1_review_support/d1_q4_inverse_dev_97fcf81f_20260929.patch) (SHA-256 7D885D63CB1F5623008614C1C827293C91D2A1E127142F9DADBAF0E0F1ED2FD8). Reverse application to the dirty file and forward application to the restored HEAD were checked. Production overlap.py is back at HEAD. The benchmark script and six raw/resource files remain for recovery; the observed 2.81× was local only and parity was not qualified. No owned process is running.

**Next integrated decision:** Reuse one small nonmatching Q4/deformable-S3 case, with the pressure source fully covered by the target union and active contact away from prescribed and physical source edges. Bring a narrow admission guard into the same route, then execute a bounded free-rotation force-controlled press with independent physical gap and a pressure-work measure. If it cannot equilibrate inside the profile, diagnose one specific cause and choose a permitted correction or a concrete escalation. Build the four-phase/control/restart claim on that same candidate.

**Current bounded development experiment:** `scripts/general_contact_d1_interior_press_dev.py` constructs eight Q4 source faces in a 4-by-2 patch over two deformable S3 target faces; the source is inside the target's projected union, source rotations are free, and one interior node receives 0.08 N downward load. The question is whether this existing-law, monolithic case reaches two accepted force-controlled steps with a physical gap and pressure away from the source rim. A failure is classified as mechanics, geometry/profile, or resource before changing the fixture. The first run is capped at 180 s and 1 GB process-tree RSS with `docs/d1_review_support/d1_bounded_single.py`; result and log go to `docs/d1_review_support/d1_interior_press_20260929.*`. This is exploratory and does not consume a frozen acceptance execution.

**First result and discriminator:** The worktree solver returned `contact_semismooth_backtracking_failed` at iteration 9 of step 1 after 55.3 s and 286 MB peak process-tree RSS; no step was accepted. Its reported normalized gaps were positive, five nodal forces remained positive, and the failed line search had no trial attempts. This points to a swept-fraction or active-branch issue rather than a measured resource limit; it does not yet distinguish them. One identical bounded rerun adds failure-only swept lower bounds, first fraction and pivot trace. If the fraction is zero while the current gap is admissible, investigate the event/branch step; if geometry is already invalid, correct the fixture or geometric guard instead.

**Discriminator outcome and next choice:** The identical trace failed after 36.2 s/302 MB: the current conservative gap lower was -4.99985e-5 m against the unchanged -5e-5 m limit, the proposed lower was -1.0127e-4 m, and the swept admissible fraction was zero. The 15 weighted nodal gaps remained positive (minimum 1.43e-5 m); pivoting predicted several active modes from the current open set. This identifies a conservative-gap/event stall in this coarse target fixture, not a resource limit or an accepted physical gap. The next single corrective run uses two target columns (four deformable S3 faces) to reduce target-face extent while retaining the same source mesh, force, material, law and gap budget. If that still stalls, inspect the relevant pair bound and overlap before any further mesh sweep.

**Fixture correction:** The four-S3 target run failed at its first Newton iteration with a 4e11 reduced-coordinate direction, before a contact event. A contact-free reduced structural/control matrix check on both the two- and four-S3 fixtures found a singular value near 1e-13–1e-14: the source had an unrestrained rigid rotation about its supported left edge. This explains why the first fixture's finite Newton path was not reliable evidence about the contact law. The fixture now restrains `ry` only on the left support line, leaving all interior source rotations and target rotations free. Recheck the contact-free matrix, then repeat one bounded integrated press; retain both failed runs as fixture-development evidence.

**Corrected fixture result and algorithmic change:** The left-edge rotational support raised the smallest contact-free reduced/control singular value to 4.10e-4 for both target meshes. The two-S3 corrected press then stopped after 6.7 s/275 MB at a monolithic active-set prediction cycle, before a candidate line search. The current active branch itself supplies a valid generalized Newton derivative. A narrowly scoped solver change now falls back to that direction when full-step pivot prediction cycles, subject to the existing swept certificate and merit backtracking. This does not change the mortar law, acceptance gates or physical state. Repeat the identical corrected fixture once and check the existing monolithic tests before deciding whether it helps.

**Profile finding:** The same left-supported fixture with the cycle fallback reached contact but stopped at the physical gap limit (-4.99993e-5 m) after 31.1 s/289 MB. Its only positive nodal forces were at source nodes 10 and 15 on the right physical rim, so it is outside D1-interior. This is not evidence against an interior pressure space. The next bounded case uses a simply supported source perimeter and the same interior point load, Q4/S3 geometry, constitutive law and gap budget; all source rotations remain free. The expected contact region is near interior node 8. A contact-free stiffness check precedes the solve. If active rim forces persist, treat the case as outside profile rather than relaxing the gate.

**Interior coarse-mesh result:** The perimeter support matrix remained nonsingular (smallest reduced/control singular value 4.10e-4). The two-S3 integrated solve stopped after 15.9 s/275 MB, with positive nodal force only at interior node 8. Its sampled physical gap reached -4.99990e-5 m while the weighted gap at node 8 was still +2.00e-5 m. This is an unresolved weak-versus-local gap discrepancy for this concentrated-load coarse mesh; neither a small residual nor active-set fallback can override the physical gap gate. One next case will distribute the same force over the interior of a 4-by-4 Q4 patch (same law and gap budget), after focused regression checks on the fallback. If that case also cannot resolve a physical gap, stop mesh/fixture tuning and assess the method with the pressure-stability evidence.

**Focused verification:** The active-set cycle fallback passed 9 existing monolithic restart and eccentric-source work tests in 84.8 s with 450 MB peak process-tree RSS. This is a local regression check, not D1 acceptance. The 4-by-4 Q4/nine-interior-load case is now the single next integrated discriminator under the unchanged 180 s/1 GB routine cap.

**4-by-4 integrated result:** The first of two force steps was accepted in the existing 180 s/1 GB route: one positive pressure mode at interior node 13, no rim pressure, physical gap -3.48733e-5 m within the unchanged -5e-5 m budget, and equal/opposite force and moment to roundoff. The second step stopped at -4.99999e-5 m physical gap with one interior active mode and zero swept-admissible Newton fraction. Total route: 42.9 s/348 MB. This is one development path, not independent physical-gap or pressure-space acceptance. Do not tune more fixture meshes/loads without a discriminating mechanics hypothesis; the three-mesh stability gate and integrated response reference remain open.

**Admission implementation in progress:** An opt-in D1-interior setting now carries explicit projected-coverage and boundary-force tolerances into restart identity. Preparation and candidate evaluation reject positive partial target coverage; accepted-step checks reject active physical-rim and prescribed-normal pressure using the full physical skin work map and constrained structural transform. A deliberately partial Q4/S3 fixture rejected at preparation with 0.025 m2 missing coverage; the same 4-by-4 first step completed with the guard in 17.4 s/278 MB. Four focused guard checks passed in 5.7 s/216 MB. Remaining before admission: certify coverage along the actual swept path, assess geometric and work-map derivatives independently, close pressure stability and full workflow; this development guard alone is not a capability acceptance.

**Route choice and named integrated run:** Adjacent monolithic work/displacement/block tests passed 16/16 in 55.3 s/378 MB. Rather than another mesh sweep, use the observed 0.04 N accepted interior press as the maximum load for one four-phase (press/slide/open/recontact) development route with the same 4-by-4 source, two deformable S3 target faces, normal law and 50 µm physical-gap budget. The question is whether this physically meaningful bounded path completes with the new admission guard, material transaction and work reports; it does not establish load-independent qualification. Run `scripts/general_contact_d1_interior_press_dev.py --source-support perimeter --source-rows 4 --load-shape interior_distributed --force-n 0.04 --four-phase` once, capped at 900 s/4 GB process-tree RSS under the goal's named integrated-development allowance. If it fails, classify whether geometry/profile, equilibrium/contact or state transition caused it before any repeat. Historical stricter/frozen runs are unaffected.

**Four-phase result and next bounded correction:** Both press steps completed with one interior active node, no rim pressure and gaps of -1.95e-5 and -3.48733e-5 m. The first slide step stopped before line search because full-step active-set prediction used its 12-pivot budget without a stable set (23.7 s/316 MB for the full attempted route). The already verified current-branch Newton direction exists at that limit as at a cycle. The solver now falls back to it within the existing line-search and swept limits. Repeat the same path once; if projection movement or physical gap still blocks sliding, retain that mechanics failure and select a targeted geometry/pressure action rather than another pivot-limit increase.

**Sliding outcome and refinement discriminator:** With the bounded pivot fallback, the same four-phase route kept both press steps but stalled in slide step 3 after 67.6 s/425 MB. The current sampled physical gap was -4.99992e-5 m (unchanged -5e-5 limit), and the Newton direction tried to decrease it further; no swept-admissible fraction remained. This is a physical-gap/resolution limit for this 4-by-4 case, not a pivot-budget failure. The next and only planned mesh discriminator is an 8-by-8 Q4 source against the same two deformable S3 faces, same 0.04 N smooth interior load, slide, law, tolerance and support. Hypothesis: contact/structural resolution reduces local penetration enough for the coupled path; competing result is the same gap wall despite refinement. The new case differs in geometry and load from the previously consumed 64-Q4 partial-front case. Preflight found 64 Q4, 2 S3, 49 interior force nodes, 128 candidate pairs and valid initial D1 coverage. Its single named integrated development run is capped at 900 s/4 GB process-tree RSS. A failure will prompt method analysis, not automatic larger refinement or weaker gaps.

**Budget and authority:** The five-day active development clock started 29 September 2026 at 08:04:33 UTC on the user's resumption. Record elapsed active time at daily checkpoints and exclude user pauses. Routine checks retain 180 s/1 GB; named registered integrated runs may use at most 15 min/4 GB, subject to stricter historical limits. Do not merge, publish, release, alter the D1 law/targets or silently narrow scope.

**8-by-8 discriminator outcome:** The named 64-Q4/two-S3 run finished within its 900 s/4 GB cap (731.8 s, 454 MB). Both force-controlled press steps passed with sampled physical gaps -2.791e-6 and -7.908e-6 m, markedly below the 4-by-4 gaps. Slide step 3 exhausted 18 semismooth iterations with complementarity relative force 0.1939 and constraint error 0.009596 m. The last saved trial merit was 0.1939005. This distinguishes the coarse physical-gap wall from the fine route's nonlinear globalization failure. It does not show four-phase completion, pressure stability or acceptance. Raw result, log and resource evidence are in `d1_interior_cycle_8x8_004_20260929.*`. Do not automatically increase mesh size, iteration limit or gap budget.

**Guarded restart:** The focused active-press split checkpoint/resume and incompatible-profile-settings rejection passed in 49.5 s, 378 MB. See `d1_interior_guard_restart_20260929.*`. The guard still lacks a conservative swept-coverage certificate and independent geometry/work-map scrutiny. The next mechanical experiment needs a specific solver-path hypothesis tied to the saved 8-by-8 trace; a further refinement run is not justified by this result alone.

**Post-edit focused regression:** The combined monolithic restart, eccentric-source work and D1 guard test group passed 14/14 in 149.0 s, 480 MB under the routine cap after the pivot-limit fallback edit. Raw output and resource record are `d1_semismooth_fallback_final_20260929.*`. This verifies the changed local paths; it is not nonlinear acceptance or a no-contact performance gate.

**Step-size and path-control discriminators:** The original four-by-four fixture passed the first 5 mm slide increment with one interior active mode and -30.617 µm sampled gap (`d1_interior_short_slide_20260929.*`, 28.8 s/340 MB). Five prescribed 5 mm increments on the same source-edge path accepted through 15 mm, but the 20 mm candidate activated physical source-rim node 25 at 0.0085 N and was correctly rejected (`d1_interior_segmented_slide_20260929.*`, 46.7 s/417 MB). This shows a smaller step can help nonlinear progression while the path itself leaves D1 scope. A target-edge-translation variant accepted a 25 mm slide on the sloped reference geometry but opened contact: active modes 1 to 0 and normal force 1.374e-3 N to 0 N (`d1_interior_target_slide_first_20260929.*`, 29.5 s/322 MB). These are distinct mechanical/path outcomes, not evidence of completed sliding contact.

**Exact flat-seam counterexample:** Flat parallel surfaces with the same target-slide controls rejected before the first step on `vertex lies on a clipping boundary` (`d1_interior_flat_target_cycle_20260929.*`, 7.4 s/peak resource in file). Enabling the existing verified two-face artificial-shared-edge option did not complete the case. Its -3e-8 m smooth neighbor hit a second tiny Q4/S3 pair whose float/Jet2 support differed by 9.61e-25 m² on a 4.5e-16 m² wedge; current recovery is tied to one failed pair (`d1_interior_flat_target_tie_cycle_20260929.*`, 8.4 s/peak resource in file). Preserve this failure. No tolerance was relaxed and no additional mesh or load sweep was started. The next decision is a narrow multi-wedge derivative/error-bound review, followed by one implementation slice only if the aggregate work can be verified.

**Multi-wedge experiment disposition:** A development patch extended the existing two-face seam recovery to verify multiple tiny wedges independently and bound their aggregate force/tangent error. It passed eight pre-existing monolithic seam tests (43.9 s/344 MB), but the aligned flat fixture failed first on 17 local active coordinates versus the old 12-coordinate admission, then on an unresolved tiny pair area, and finally on the independently checked exact-seam gap direction after a capped local extension. These three raw development results are `d1_interior_flat_multiwedge_20260929.*`, `d1_interior_flat_multiwedge_count_20260929.*`, and `d1_interior_flat_multiwedge_workbound_20260929.*`. The candidate was **not promoted**. Its exact patch is `d1_multiwedge_experimental_20260929.patch` (SHA-256 `DA30CD1D41F3261B40AC6E41AABC9AF0C621289F4342190BAFF664D7C1C3DC80`); the two kernel files were restored to HEAD, and the patch was checked to apply to the restored source. Fully aligned multiple-tie handling remains open.

**Resolution-based tiny-overlap comparison:** A shallow common slope of 1e-4 avoided the simultaneous exact tie but initially rejected pair 5 at area 8.016e-12 m²: float/Jet2 area difference 3.433e-18 m² against propagated area resolution 1.217e-17 m². The development correction retains the ordinary local comparison when it passes and uses the existing 1 ppm value allowance only when a pair breaches the ordinary 0.25 ppm cap and its measured area resolution is at least 1 ppm of its area. The absolute resolution check, 1 ppm mismatch cap and force/tangent/integration gates remain. A focused captured-value test and all 18 Q4/S3 pair-resolution tests passed; all eight monolithic exact-seam tests passed after the change. The unchanged shallow-slope four-Q4/two-S3 eight-step route then completed in 66.0 s/412 MB (`d1_interior_shallow_target_resolution_20260929.*`): press and both 25 mm slide steps retained one interior active mode; opening released it; recontact restored it. Its worst sampled gap was -42.105 µm against the unchanged -50 µm limit. This is integrated development evidence, not a formal pressure-stability, tangent, response or installed-artifact acceptance.

**Cycle restart:** The new shallow-slope route completed as an uninterrupted eight-step run and as six steps through opening followed by a split restart through recontact. Final displacements and each integrated contact-force vector agreed within 1e-10 absolute. The focused test passed in 144.5 s/496 MB (`d1_shallow_cycle_split_restart_20260929.*`). This locally verifies active/open/recontact state continuity for that fixture. It does not close cancellation, exception rollback, arbitrary material history or the final restart qualification claim.

**Fixture correction after review:** The `target_columns=1` helper uses target node order left-bottom, right-bottom, right-top, left-top. The development fixture chose `target_start` and `target_start+2` as its supposed left-edge clamp/slide controls; these are opposite corners. The completed eight-step and split-restart results above remain valid for that two-point diagonal-corner motion, but must not be described as left-edge translation. The helper now selects `target_start` and `target_start+3` for this topology, preserving the row-major `target_columns=2` convention separately. Rerun the corrected intended motion before using it as left-edge evidence. Historical results and tolerances are unchanged.

**Corrected left-edge result:** The corrected controls (target nodes 26 and 29) and corresponding left-edge support preflighted correctly, but the same shallow-slope 0.04 N full-cycle attempt stopped before accepting its first press increment after 53.8 s/396 MB (`d1_interior_left_edge_corrected_20260929.*`). The semismooth solver reached iteration 12 with equilibrium merit 4.36e-5 and active mode count one; full and backtracked candidates rejected on Q4/S3 tiny-wedge paired-area comparisons. One recorded pair had local area 2.599e-12 m², float/Jet2 area difference 6.632e-18 m² and propagated resolution 6.927e-18 m²; its 2.55 ppm relative difference exceeds the unchanged 1 ppm cap. This is a geometry arithmetic/admission question, not evidence that the correct left-edge mechanics fails. The old diagonal-corner selection is now named `target_diagonal_dev` in the development fixture and split-restart test. No new tolerance or run budget is authorized by this failure.

**Post-correction focused verification:** Five D1 guard and active-press tests passed in 63.8 s/384 MB under the corrected target-left-edge support used by the source-motion fixture (`d1_corrected_fixture_guard_tests_20260929.*`). The explicitly named diagonal-corner eight-step/open-restart test passed in 136.7 s/498 MB (`d1_named_diagonal_restart_20260929.*`). These reruns follow the fixture-input correction; they do not turn its diagonal path into left-edge evidence.

**Independent tiny-area oracle and corrected left-edge route:** A single capped failed-step capture retained five Q4/S3 tiny-overlap coordinates and float/Jet2 areas in d1_left_edge_area_capture_20260929.json. The separate Decimal script (80 digits, no production geometry import) produced d1_left_edge_area_decimal_oracle_20260929.json. Its input capture SHA-256 is 02d2f09e9edf48d8bb7cbf9ebb897e7f2d3ede124c6bd0fb0bd6c28f5a59dafc. Decimal matched Jet2 within 2.98e−22 m²; float differed by 3.87e−18 to 1.05e−17 m². Global-coordinate shoelace cancellation in the float overlap was replaced with origin-anchored triangle summation. The provisional relaxed comparator from 034feb29 was reverted to the strict predecessor. First corrected press passed in 21.4 s/316 MB (d1_left_edge_anchored_first_20260929.*); full genuine left-edge eight-step cycle passed in 91.5 s/417 MB (d1_left_edge_anchored_cycle_20260929.*). Worst sampled gap −35.966 µm versus unchanged −50 µm budget; one mode active through slide, zero during opening, active again on recontact. Forty-nine focused overlap/derivative tests passed in 82.1 s/289 MB (d1_anchored_overlap_tests_20260929.*). These are development outcomes and do not erase the earlier comparator failure.

**Saved-pose reaction tangent defect and correction:** A 174-DOF active slide pose and 25 fixed nodal-force entries were saved as tests/fixtures/general_contact_d1_left_edge_slide_pose.json, avoiding repeated coupled solves for derivative checks. The fixed-force full contact tangent was 5.548% from finite-difference force across 1, 0.5 and 0.25 µm steps, while gap derivative agreed near 1e−12. Reduced tangent error was about 1.3e−9, and pair-local Jet2 Hessian checks retained branch signatures and integration subdivision counts; the isolated near-zero support-Hessian noise was not the large discrepancy. Reaction rows on prescribed coordinates had been removed by the active-coordinate Hessian restriction. The new assembly keeps every residual row and restricts only columns unreachable by the reduced solution. The unchanged 1e−5 directional check, including reaction rows, then passed in 12.8 s/252 MB (d1_left_edge_tangent_rectangular_20260929.*). Failed traces and pair diagnostics remain under d1_left_edge_tangent_*, d1_left_edge_pair_hessian_* and d1_left_edge_tangent_reduced_20260929.*. Full integrated acceptance and independent review remain open.

**Corrected left-edge split restart:** The target-left-edge case now runs uninterrupted through all eight steps and separately to the six-step/open checkpoint, then resumes through recontact. Final displacement and every integrated contact-force history row agree within 1e−10 absolute. The focused test passed in 168.1 s/500 MB (d1_left_edge_split_restart_20260929.*). This verifies local path continuity for the corrected fixture, not broad cancellation/exception rollback or installed restart.

**Corrected-path cancellation and exception recovery:** A one-step-accepted press was interrupted at the second-step safe point. The same model then reran to completion and exactly matched a fresh model's serialized checkpoint, with displacement and integrated force agreement within 1e−10 absolute (d1_left_edge_cancel_reuse_20260929.*, 75.0 s/408 MB). A separate second-step injection raised RuntimeError after the contact linearization had returned; after restoring the original callable, the same model again matched a fresh solve and checkpoint (d1_left_edge_exception_reuse_20260929.*, 65.3 s/416 MB). These are local development checks for the corrected fixture. Swept cutback and broader material/contact transaction acceptance remain open.

**Interior pressure-family preflight and stop:** The corrected left-edge press was enlarged from 16 Q4/two S3 to 32 Q4/four S3 with the same tent-weighted interior total 0.04 N force, shallow slope and perimeter support (d1_interior_pressure_family_8x4_20260929.*, 60.8 s/430 MB). It completed two steps with a single active mode at source node 22. The next open supported mode had +10.65 µm weighted gap and the independent minimum was −45.78 µm under the unchanged −50 µm budget. A single load-shape correction assigned equal force to all interior nodes at the same total force and geometry (d1_interior_pressure_family_uniform_8x4_20260929.*, 47.4 s/372 MB). It completed, still with only node 22 active, and minimum gap −35.78 µm. The fixture does not furnish a multi-mode stability family under these two loads. Stop this branch, retain both negative results and design an actual two-body multi-mode work fixture before new expensive mesh runs. The added uniform option is only a development-fixture parameter; it does not change contact mechanics.

**Two-control displacement pilot and stop:** A 16-Q4/four-S3 target-centre displacement fixture initially failed before solve because the no-load, two-control path was misclassified as force-driven (d1_target_normal_displacement_pilot_20260929.*). The existing contact-free elastic predictor was generalized to one-to-three controls with a single structural factorization, absolute reaction sums across control directions and the maximum over waypoints; the former single-control value and force-driven bound remain. The first explicit 0.04 N scale rejected against a measured 1.15667915e−4 N contact-free predictor for 10 µm (d1_target_normal_displacement_scale_20260929.*). With an explicit 5e−5 N scale, −10 µm target motion completed with zero contact and +40 µm minimum gap (d1_target_normal_displacement_integrated_20260929.*, 22.5 s/286 MB). A single corrected +60 µm upward motion reached contact but rejected first step on physical source rim node 5 with 5.97636e−5 N, as required by D1-interior (d1_target_normal_displacement_up_20260929.*, 16.1 s/279 MB). No active D1 displacement response follows. Stop this fixture branch. Eight focused predictor, ordinary displacement and force-scale regression tests passed in 28.5 s/381 MB (d1_multi_control_regression_run2_20260929.*); an initial test invocation named a nonexistent test, retained under d1_multi_control_regression_20260929.*.

**Full interior pressure-work screen:** Fresh matched 16-Q4/two-S3 press (d1_pressure_work_16q4_press_20260929.*, 28.6 s/342 MB) and existing 32-Q4/four-S3 press both had one active node but 9 and 21 signed interior pressure modes. Their smallest L²-mass-normalized two-body structural dual-work values were 1.020909e−5 and 1.043989e−6. Independently clipped frozen-reference-footprint Q1/S3 work, sharing the structural stiffness, gave 1.020915e−5 and 1.043977e−6 (d1_interior_work_spectrum_20260929.*). A current-skin attempt rejected because the oracle requires horizontal Q4 rows; its failure is retained. A separate exact hat–sine Kirchhoff source-only screen gave 2.524648e−5 and 2.229346e−6 at 128 modes, with discrete/idealized ratios 0.4044 and 0.4683 (d1_interior_sine_energy_20260929.*). One independent 24-point integral check passed. High-frequency pressure dual work naturally decreases in this L² norm; these finite screens neither prove nor disprove mesh-uniform two-body pressure stability. Stop eigenvalue-only diagnosis.

**Deformable 2D target discriminator:** The development fixture extended the target from two S3 faces to an eight-S3 2×2 grid with a free interior node; the source remained 16 Q4, perimeter supported, under the unchanged 0.04 N total press. The original monolithic run stopped at first-step iteration 3: all weighted gaps were open, one algorithmic nodal force remained positive, and all 12 trial fractions increased merit (d1_2d_target_press_20260929.*, 40.5 s/421 MB). A contact-free linear solve under the identical first-step force and controls had a conservative gap lower bound −105.53 µm against the −50 µm budget (d1_2d_target_open_predictor_20260929.*, 2.6 s/159 MB); contact was necessary. A bounded fallback using the current active-set generalized derivative, without changing merit, swept or gap gates, advanced the unchanged coupled run to iteration 16 and reduced merit from 0.09315 to 0.00215. It then stopped at a conservative lower gap −49.99998 µm with zero admissible fraction, versus sampled gap −9.67 µm (d1_2d_target_current_branch_20260929.*, 108.0 s/421 MB). Three focused work and rollback tests passed in 33.7 s/377 MB (d1_current_branch_focused_tests_20260929.*). This distinguishes the first globalization defect from a subsequent conservative-bound limit. It is neither accepted contact nor evidence to loosen the gap budget. Stop this fixture branch; derive and independently check a tighter overlap-local conservative certificate before another integrated deforming-target case.

**Overlap-local geometry screen, no solver admission:** One bounded replay saved the last rejected pose and all 128 Q4/S3 pair bounds (d1_2d_gap_pair_20260929.*, successful replay 97.0 s/415 MB). Its first replay completed the mechanics but failed to serialize a NumPy integer; the failed log/resource record is retained. All 128 current whole-face bounds were negative; 78 pairs had disjoint XY bounding boxes. The worst pair had −49.99998 µm bound despite 50 mm XY box separation. A second overlapping pair was nearly as loose, so pair pruning alone cannot resolve the wall. A development-only instantaneous bound subdivided the *same* bilinear Q4, discarded projected-box disjoint subfaces and bounded the target-plane height over retained parametric rectangles. On the saved pose, depths 0–5 gave minimum lower gaps −50.000, −50.000, −50.000, −46.736, −45.105 and −45.105 µm; depth 4 visited 12,000 subrectangles (d1_overlap_local_bound_20260929.*, 5.1 s/159 MB). Two independent planar-overlap controls passed in 3.1 s/212 MB after one test corrected its mistaken claim that this local bound must always beat the older cone bound. These checks support a targeted swept-bound derivation, not production use: a static bound cannot guard a moving trial path, and no complete coupled run was repeated. Preserve the existing −50 µm gate and current accepted/failed evidence.

**Swept overlap-local candidate:** A separate development function bounds a linear physical nodal path, using quadratic Bernstein controls for the parent Q4 projection normal, fixed-frame boxes expanded for possible normal-projection drift, and space/time bounds on each retained source subrectangle. It retains the broad conservative fallback when the projection/physical-normal cone cannot be admitted. On the captured zero-length path, depth-4/5 lower bounds both equal −45.1047 µm, consistent with the instantaneous screen (d1_overlap_zero_sweep_20260929.*, 20.6 s/162 MB). Five focused checks passed in 3.6 s/213 MB (d1_overlap_swept_samples_20260929.*): planar exact-overlap controls, between-endpoints crossing, and sampled physical gaps on eight moving warped Q4/S3 poses. Two prior invocations failed on a generator passed to NumPy stack and then a sign error in a test fixture; their logs remain under d1_overlap_swept_tests*. This is a bounded development candidate, not a certified solver-path guarantee. Capture and compare the actual last Newton proposal before considering an explicit experimental solver profile. No contact law, solver certificate or numerical limit has changed.

**Actual proposal and explicit profile:** A third replay captured the first-step rejected Newton proposal (d1_2d_gap_proposal_20260929.*, 96.9 s/413 MB). Against the unchanged −50 µm gap budget, the old swept certificate admitted fraction zero; the experimental depth-3/4 overlap-local bounds admitted the full proposal at −47.401/−45.757 µm, while independent path samples reached −9.849 µm. The same was true for fractions 1/2, 1/4 and 1/8 (d1_actual_swept_gap_20260929.*, successful 22.2 s/161 MB). The first evaluator run failed only at JSON encoding of a NumPy bool; its log is retained. The candidate was then added behind explicit `overlap_local_dev`, a distinct capability profile and restart identity; default certificate and contact law remain. Eight focused geometry/work/rollback checks passed in 30.4 s/372 MB (d1_overlap_profile_focused_tests_20260929.*).

**Named integrated outcome and stop:** The explicit-profile 16-Q4/eight-S3 two-step press accepted step 1 with conservative gap −47.401 µm, sampled gap −9.849 µm and source/target wrenches equal and opposite to roundoff. Step 2 stopped at iteration 5 with equilibrium merit 0.17943, complementarity 2.86e−9, conservative start gap −49.9991 µm and zero admissible swept fraction (d1_2d_overlap_profile_20260929.*, 60.85 s/357 MB). The second-step proposal was captured in a 59.3 s/356 MB replay and independently sampled along its linear physical nodal path. At fraction 1/8, depth-3/4 lower bounds were −57.221/−55.399 µm, while sampled gap was −9.973 µm (d1_overlap_step2_swept_20260929.*, 19.0 s/161 MB). Source-only subdivision of its limiting face through depth 7 remained −55.172 µm, showing target-side variation still controls this bound. A saved-first-step test confirmed the profile/restart distinction and old/new swept decision; five geometry/profile tests passed in 6.7 s/215 MB (d1_overlap_profile_saved_test_20260929.*). The 2D fixture branch stops here. This is a partial development capability, not a D1 handoff, independent acceptance or evidence of a complete-route speedup. Joint source/target subdivision may be considered only under a new discriminating task; retain the unchanged gap budget and pressure-space questions.


## D2 projected finite-penalty slice — 30 September 2026

D1-interior is accepted at package0b2; checkpointb38cb6ce. Selected the
explicit projected weak-gap penalty over new agglomerated/dual spaces after
early independent equations review. New opt-in `projected_penalty` keeps
algorithmic multipliers zero, fineQ1 supports and the full generally nonsymmetric
Jet2 moving-support Jacobian. Existing `penalty` and D1 augmented definitions
and restart contracts stay distinct. Storage is not projected contact work.
The bounded scalar discriminator and its interpretation retain the failed
reaction-sign/branch-crossing checks; no rerun. Small-cut supports stay positive;
stiffness sensitivity remains unresolved. Next question: can one compatible
partially covered, prescribed-boundary coupled shell fixture meet equilibrium
and independent physical gaps while showing controlled stiffness sensitivity?
Use one routine180s/1GB slice before further refinement; no rim/edge-only or
finite-rotation claim. Review consequential work/state wiring independently.


**D2 wiring review/checks:** checkpoint_review independently identified and
closed the omitted projected-profile reduced-variation whitelist, ordinary API
law mislabeling and unsupported-control bypass. The new law now validates actual
force/displacement control before ordinary scope creation and reports selected
identity; zero multipliers are read-only. Reviewer found no legacy/default change.
Seven scalar/plane/admission/restart controls passV2 (4.68s/219.46MB), a separate
both-body physical-skin tangent check passes over1e-6/3e-7/1e-7 steps (4.89s/225.27MB),
and unsupported ordinary/scope control guard passes (4.17s/212.22MB). InitialV1
three invalid-settings test fixtures failed before reaching profile validation;
corrected fixture controls preserve those failed logs. A development metadata
witness matches the installed0b2 augmented restart+open-result bytes exactly:
2421bytes SHA86323f87e317bc3e71858ea7e86436b991a1b1dd9456272aa43f7ff3c35dfd3f.
Its first JSON helper attempt failed on numpy.bool encoding, then converted only
NumPy scalar item(); no accepted solve was repeated. This is compatibility
evidence, not fresh D1 scientific qualification.

**First coupled pilot:** finite1e6Pa/m shell path completed press/open/recontact,
active counts2/0/2, in10.49s/275.08MB. The independent diagnostic stopped on
exact-zero guided coordinates despite deviations<=1.04e-23m. Raw nonpass remains;
saved-only assessment is underway before any second-stiffness solve. Prescribed
left support pressures are zero in this fixture; active prescribed-pressure
contact remains open. No full D2 acceptance or runtime-speedup claim.


**Integrated outcomes and next decision:** first1e6 pilot's retained final pose
passes saved-only assessment (7.03s/274.93MB), physical penetration31.1739µm,
wrench1.89e-13, virtualwork5.55e-17. Original raw nonpass and missing earlier
pose vectors stay explicit. Second-only1e7 run passes all3pose checks in
12.31s/275.35MB, allposevectors/final4states retained. Gap26.7827µm; wrench
1.64e-12. Targetreaction+1.69843% and normal-displacementL2+2.76810% relative
to1e6; this is stiffness sensitivity, not continuum accuracy. Prescribed pressure
rows remain inactive; their force map is checked independently with active
pressures and excluded variation columns (4.29s/220.55MB).

Ordinary-driver review found projected work was incorrectly classed symmetric
when augmentation was off. Both force/displacement branches now use GENERAL
without enabling augmentation; reviewer verified full assembly, residual merit,
gap/swept checks, commit/discard/cleanup and contract-bound restart hooks.
The direct ordinary-force check preserves pilot controls as BCs, solves load
factor.5 prefix then resumes1.0 with a strict checkpoint. It passes12.60s/275.63MB,
all7factorizations actuallyGENERAL, correctlawreporting, independent gap budget,
zeroµ and finaldisplacement/pressure differences2.31e-10/3.91e-8 versuspilot.
Raw docs/d1_review_support/d2_projected_penalty_ordinary_force_v1_20260930.*.
No freshD1 run. Ordinary force now has no artificial two-path-control limitation;
custom nested path programs still needtwo controls. This is development proof,
not independently accepted/releasedD2.

Principal remaining uncertainty: response/gap accuracy on partially cut/contact
fronts, rather than a solver-wiring failure. A next stiffness value is justified
only as a single test of1/k asymptotic response (predict fromsaved1e6/1e7 before
run); persistent local gap must be addressed by spatial/contact resolution, not
an indefinite stiffness increase. Physical rim/edge-only/collision, active
prescribed-edge equilibrium, finite-rotation/search/self-contact and future
programme rows remain open.

**30 September fixed-geometry reference decision:** independent exact rectangle
Q1 integrals with declared structural K input reproduce saved 1e6/1e7 normal
displacements (relative <=1.607e-8), target reactions (<=2.875e-8) and physical
gaps (<=4.27e-13m), in1.403s/137.08MB. Reviewer found no blocker for this
fixed-geometry discrete comparison; moving horizontal work/tangent and continuum
accuracy are outside its scope. The full saved-state reference residual reaches
9.88e-7 relative, so tiny displacement differences alone do not qualify mechanics.
Exact v1 source snapshot retained with SHA19289672813fe374a05a737e2590fbddab5a8886aca0545adb0843a27afd0db9.

Weighted-gap release does not enforce a clipped edge gap. If the active right-hat
branch persists and the left gap remains positive, its zero average condition
permits negative clipped-edge gap. Two finite-stiffness results do not establish
that limit. Skip another coupled stiffness run. One independent 4x2 prediction
at unchanged k=1e7, geometry/material/load/supports, followed only if useful by
one coupled 4x2 comparator, distinguishes spatial representation error from
production contact error. Routine180s/1GB applies; no mesh sweep or new criteria.
Worker owns reference helper/output; lead owns coupled comparator. New-law-only
ordinary small-rotation guard independently reviewed, focused negative check
passed3.289s/211.41MB. Legacy branches remain unchanged.

**Spatial prediction outcome and narrowed action:** the4x2 independent reference
completed1.444s/138.38MB, residual4.75e-16N, all15supports retained. It predicts
62.7135µm penetration at(1,.1), versus26.7827µm coarse, and targetreaction
.3499983N versus.3466726N. Structural and contact discretizations both changed;
point loads and prescribed rotations prevent a monotone continuum interpretation.
This is a useful gap-budget nonpass, not proof of universal formulation failure.
Withhold the coupled solve predicted to fail the unchanged50µm limit. One
candidate-only evaluation of production contact at independent q instead checks
normal operator parity, complete physical work/wrench and actual gap rejection.
No equilibrium solve, physical commit or displacement-verification claim.
Command under180s/1GB: d1_bounded_single.py invokes
d2_projected_penalty_spatial_coupled_dev.py --candidate-only --reference
d2_fixed_geometry_penalty_spatial_v1_20260930.json, unique
d2_spatial_reference_pose_operator_v1_20260930 raw output/log/resource paths.
If operators agree and both gap checks reject, stop the stiffness/grid diagnostic
and select the next bounded boundary/contact-representation delivery slice;
otherwise correct the specifically identified production discrepancy.

**Spatial operator decision:** candidate-only check completed6.384s/266.44MB.
Pressure/reaction errors3.326e-6/2.991e-6 exceed1e-6; source equilibrium/wrench
at imposed linear q also exceed their gates. Preserve NONPASS. Both independent
and production gaps reject; actual physical work mapping, conversion and all15
supports pass. Reviewer identifies omitted moving projection/support/physical
normals as the plausible discrepancy: weighted-gap change exceeds measured
integration error by610x. This is not a moving-operator qualification, actual
equilibrium, or demonstrated production defect. No tolerance changes or rerun.
End this stiffness/grid branch rather than force a favourable comparison.

**Next integrated boundary slice:** original2Q4/S3 cut geometry,1e7, unchanged
50µm gap gate; prescribe source normals1/4 through two real path controls from
0 to−130µm, open and recontact, two steps persegment, no nodal forces. Remove
their former zero-normal BC; fix node2's former zero in-plane controls. All6
pressure rows and physical reaction rows remain. Node4's supported pressure
hat is represented, although its node lies outside y=1; no uncovered-tip
collision claim. Independently check actual positive controlled pressures,
joint-free equilibrium, both-body wrench/work, control.T multipliers and named
supports, exact represented gap and production gap at each pose. This closes
a distinct active-prescribed-pressure delivery requirement; it does not repair
the retained point-load spatial nonpass or claim continuum accuracy.
One180s/1GB execution: d2_active_prescribed_edge_dev.py --output
d2_active_prescribed_edge_v1_20260930.json, bounded wrapper with matching
unique log/resource paths. If pass, proceed to front motion/state admission;
if nonpass, classify its single principal discrepancy before another experiment.

**Active prescribed-source result:** completed13.908s/275.46MB, all6poses pass
the retained local checks; source modes1/4 active2.760174/5.053446Pa during
press/recontact. Gap minimum−30µm, all production certificates pass. Actual
control reactions[−.432175107,−.421057883]N oppose+.853232990N source contact;
remaining named supports reconcile exactly. Maximum both-body wrench1.768e-9,
control reconciliation8.856e-10, work1.110e-16. Independent read-only scrutiny
closed row/sign/admission/reaction findings. This is locally tested development,
not D2 acceptance; emitted active checkpoint does not establish continuation.
Handle96728closed. Next moving boundary-front/restart slice uses this method,
not another refinement screen. ANYfem summary-result persistence progresses in
its existing separate contact-intent worktree;16focused tests pass, independent
review pending, no solve/admission broadening. Full programme remains active.

**Next moving-front implementation:** extend the same parameterized controlled
edge runner with --slide. Keep the two source normal controls; add one target
x translation control with exact shared-translation MPCs, removing only target
ux zero BCs. Remaining target coordinates/directors stay fixed. Press, translate
through .08/.16m while pressed, open, recontact, two steps persegment. This
crosses the source/target x=.1 boundary within a swept segment without placing
an endpoint at the tie; unresolved candidate geometry still rejects. All source
pressure modes remain; no friction or uncovered-tip collision inference.
Independent gap uses the verified actual translated planar target rectangle;
per-body wrench recovery includes MPC/control actions, target x generalized
reaction is the sum of target nodal x residuals. Compare actual named supports,
normal controls, moving support, physical gap/work at every pose. One new
180s/1GB run d2_active_prescribed_edge_dev.py --slide with unique
d2_moving_prescribed_edge_v1_20260930 output/log/resource. Failed geometry means
targeted ownership diagnosis, not an automatic fixture/stiffness/budget sweep.

**Moving-front result:**10poses pass18.224s/275.54MB, sixpositive supports,
18.5734%support change, sourcecontrolled modes active throughslide, open/recontact
correct. Both-body wrench1.247e-9, generalized-control reconciliation6.237e-10,
work2.220e-16, independentgap minimum−30µm; productiongapallpass. Reviewer found
no row/MPC/reaction blocker. The existing swept limiter is exercised, but raw
endpoint checks do not independently qualify continuous crossing or uncovered
tips. No restart claim from final emission alone. Handle11331closed.

**Restart slice:** ordinary static entry already forwards max_load_factor to
the registered path prefix fraction. Reuse that contract to produce real active
(.6) and open(.8) checkpoints, canonical-byte persist/parse, then continue1.0
on fresh models. No manual root creation, fingerprint override or payload edit.
Compare actual tenpose mechanics/complete finalmaterial states against retained
fullpath, and reject changed stiffness with the authentic open checkpoint.
One180s/1GB execution d2_moving_edge_restart_dev.py --reference
d2_moving_prescribed_edge_v1_20260930.json --output
d2_moving_edge_restart_v1_20260930.json; unique bounded log/resource and
_active/_open.checkpoint.json side outputs. The prefix rerun is required to
exercise changed continuation input and genuine serialization; no D1 replay.
If pass, use this working boundary workflow for method-appropriate acceptance
preparation; if fail, correct the explicit state/identity discrepancy only.

**Restart outcome:**25.426s/278.40MB, genuine active6/open8 roots persist and
resume on fresh models; allten pose differences exactlyzero. Complete final
checkpoint (including material state) equals uninterrupted fullpath. Authentic
open root with changedstiffness2e7 rejects analysis-contract incompatibility.
Independent scrutiny closed state/identity findings. Development PASS only;
no methodaccuracy, continuouscollision or D2acceptance/release claim. Handle80486
closed. ANYfem summary bridge checkpointc138d41 is locallytested/reviewed, with
owner failure/identity/SI/capability semantics retained and appadmissionfalse.

**Next pairing slice:** reuse the existing projected-normal class and Jet2 S3
geometry for qualified S3-V2D/S3-V2D finite-penalty static contact. No newbasis,
ADengine or mechanicalenforcement. Worker owns core.py, s3_patch_static.py and
newS3focusedtests only; lead owns static_path.py/ordinarydriver/coupledexamples.
Fix profile names/admission boundaries first, verify fullbothbody work/tangent,
scalarpressure/support and newnegativeadmission under180s/1GB, then one ordinary
coupled case. OldQ4/S3 law/report/restart selections remain. This advances D2
pairing breadth while method-appropriate spatial/conditioning acceptance remains
open; no broadaccepted/releasedflag or recreatedD1 evidence.
