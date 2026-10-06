# Independent native physical-fibre BL5 displacement source review

Disposition: the inspected connected implementation is mechanically compatible with the existing fixed translation-control and endpoint replay contract; no consequential source defect was identified in this bounded Read audit. The scientific verification is incomplete: tests-v1 has 2 FAIL / 7 PASS. This is DEV source assessment, not acceptance, different-family qualification, or closure of the failed original transverse force programme.

## Actual scope and bindings

Repository: C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001; author declared source-ready after initial implementation. I read the public solve/restore/rebase path, affine endpoint, displacement corrector/publication/checkpoint, native mixed-history services, example and new test. No solver/numerical evaluation, Git operation, protected campaign or sibling inspection was performed.

The eight current source/example/test hashes were compared with binding-tests-v1.json and all matched:
- affine_endpoint.py: 7f9de1a678f675cc730c1787b600d9ec6b54c5e31381fb77b2dd386e16ec5f80
- displacement_control.py: 623ded3fbadf9715cd7dc3e283e500c1be38c237b4c1b16221066a2569bdd92d
- displacement_corrector.py: a2e1a671c52acd64605e8bdfd286f4c35fb53fab44b292c7cd3fb51f5a15aa94
- displacement_checkpoint.py: 55801aaf5d8e1744b4146828b7e8cac42165946f41e60a2b2c00260ba40615fa
- ge_checkpoint_binary.py: 401f059c4780834aa42ade36cdf7e928fea4bf5a3eb63b8df72db5227bfe91f3
- ge_experimental.py: 6d5be44f86ce443edd65861de074735b51e8f573e5c1b053675927ba2b680281
- example: 27bb43be7331b5cfeac466a3723a6af46546a9b83c37377b902feb2c343bda41
- test_native_fibre_bl5_displacement.py: cfaaebc3b0b2e6e02c4033e8e61fc54fc62a2ea7fad0dc28c8f4be04ba5752fc

## Connected mechanics and ownership

The separate uses_native_material_history predicate preserves the old point predicate while admitting the new BL5 material owner. It is used together for native history shape/layout, packing, replay and authoritative saved-history installation. Beam high/low fibre histories and generalized histories are reconstructed from compiled section identities; every trial uses the same captured accepted shell/beam origins. They are not replaced by successive scratch candidates.

The bordered correction solves the actual free mechanical/multiplier rows with the affine load-amplitude column and physical translational control row (corrector.py bordered_path_correction and correct()). The fixed dual-work merit includes multiplier rows; eq <= 1e-8, gap <= 1e-9 and the existing reference-length control tolerance remain mandatory. Native retained resultants are advanced separately from additive q. Existing _increment_origin returns the same native BL5 chart, and this route does not introduce a constitutive return law or event proposal.

Continuation requires exact control DOF, load direction and trial-policy signatures (control.py:181-188), and exact base + amplitude*direction equality with the accepted applied load (corrector.py). The ordinary nonadaptive force-seed restriction rejects any force adaptive cursor before snapshot construction; public solve rejects adaptive displacement, rebase rejects native material BL5, and adaptive restore envelopes are refused before nested replay. The distinct finite_displacement_native_fibre_bl5 / B3_GE_NATIVE_FIBRE_BL5_DISPLACEMENT_V1_DEV identity has chart/event policies None; decode refuses added chart/event metadata, and affine replay requires identity shell anchors. Publication prepares privately, then checks live driver/generation and cancellation before commit.

Endpoint replay checks actual mechanics and saved accepted/predecessor histories, retaining saved accepted histories to prevent restore drift. Its explicit contract does not authenticate the whole historical loading path; the seed digest is provenance, not proof of every historical step.

## Observed evidence and actionable gaps

screen-v1/result.json and execution.json report completed exit 0, 13.5553629 s, sampled peak tree 168357888 B and sampled numerical/unresolved maximum 1. The axial biaxial/J2 example starts at an ordinary nonadaptive force seed .001, controls 1e-6 -> 1e-5 -> 5e-6, records shell alpha 2.181664e-6 and fibre alpha 4.940944e-5, eq 1.441698e-10 and gap 1.375504e-17. Fresh restore and resumed continuation are byte equal. This is a useful public-path loading/unloading/history result. Accumulated activity does not independently prove current plastic-branch activity or an algorithmic tangent.

tests-v1/stdout.log and execution.json report 2 FAIL / 7 PASS, exit 1, 63.68 s pytest / 65.8984514 s supervisor; failures are preserved.
1. test_refusals_and_restore_are_atomic calls control.restore(...) on the already-live owner. The public fresh-owner RuntimeError occurs before the intended corrupted fibre/origin/applied-load and later metadata/adaptive-envelope checks. Use separate fresh owners for the intended tampered-checkpoint replay/refusal assertions, and verify unchanged empty state/generation on rejection. Earlier cancellation, signature and rebase assertions did execute; later refusal coverage did not.
2. test_force_seed_parity_and_fixed_origin_tangent uses a target 4.431906339454822e-10. That target is within the existing 1e-9 reference-length control tolerance; amplitude 0 can satisfy the declared contract. Its expected amplitude .001 is therefore not a discriminating oracle at this scale. Choose a compatible physical parity fixture whose controlled displacement is clearly above the existing floor, while preserving all criteria. The FD assertions were not reached, so there is no derivative verdict from this test.

The identities() function also repeats an identical native BL5 guard at lines 23/26. This is harmless dead redundancy, not a mechanics blocker.

Remaining decision: repair the two caller-test defects within existing authority and inspect their actual outcomes; neither a source review nor helper counts close the original force route, simultaneous material/tangent qualification, physical accuracy or release gates. The original transverse force full-target failure remains separate and unresolved. No automatic new scientific run or criterion change is recommended.

