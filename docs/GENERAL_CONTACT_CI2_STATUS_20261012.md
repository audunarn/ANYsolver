# General-contact CI2 handoff — 12 October 2026

Branch: codex/contact-ci2, based on main 9e4b0f68489357ff4a6b1415df61dd48fdd78da9. Local implementation and verification only; no push or qualification/release claim.

## Changes

- Saved radial-field fixture identity uses its original frozen CRLF record form on either checkout platform. Frozen evidence, its hash and the validator are unchanged.
- Native curved-fibre/S3 owners reuse the already evaluated initial pose through the existing exact identity/configuration/intactness checks. Changed poses recompute; mutation, cancellation and transaction cleanup are tested.
- The scalar Decimal Taylor loop completes early only when the value and flags of the original 80-pair loop are certified unchanged. Independent review identified and corrected import-context, subnormal-predicate and integer-bound issues. Cache policy and scientific tolerances are unchanged.
- Hermite midpoint subdivision uses exact common-denominator integer arithmetic and returns the same Fraction children as the original algorithm. Original-arithmetic caller certificates, arbitrary denominators, cancellation and exhaustion are covered.

## Verification

All original nine contact nodes pass in focused local default-dispatch checks, but this is not portable CI acceptance.

| Installed check | Result | Process wall |
| --- | --- | ---: |
| Windows native/radial/construction |31passed; separate direct-entry setup error preserved|7.560s|
| Windows direct-entry, owned temporary directory |1passed|1.660s|
| Linux native/radial/construction/exactsplit initial |53passed;1new test-fixture failure preserved and repaired|5.555s|
| Windows corrected sweep/refusal suite |109passed|10.273s|
| Linux corrected sweep/refusal suite |109passed|5.086s|
| Linux original six replay nodes, default dispatch |6passed|77.455s|
| Windows original two-fibre route |1passed, original 120 s guard|80.790s|
| Linux original two-fibre route |1passed, original 120 s guard|69.768s|
| Windows original KKT, Python 3.12 |1passed, original 1e-6 target|23.555s|
| Windows original KKT, Python 3.14.7 |1passed, original 1e-6 target|35.999s|
| Windows original KKT, Python 3.14.7/Haswell |1failed, unchanged target|25.958s|

Windows uses isolated installed environments under AppData/Local; Linux uses a native Linux candidate checkout and isolated installed environment. Numerical pins: NumPy 2.5.4, SciPy 1.18.1, Numba 0.68.0, llvmlite 0.50.0, pytest 9.1.1. Public dependency source pins match the workflow. Default full-group reproductions used Python 3.12 on both systems; the KKT discriminator also uses the hosted Windows minor version3.14. This does not reproduce every hosted Python/CPU combination.

## Unresolved scientific and portability gates

Do not mask or relax these failures:

1. Original nonlinear KKT comparison, test_general_contact_d1_two_body_nonlinear_oracle.py::test_saved_slide_matches_independent_current_contact_kkt: verified Haswell dispatch reproduces the exact hosted control-reaction discrepancy 1.4948506139016305e-5 against 1e-6. Default dispatch passes on both local Windows minor versions. Dispatch sensitivity is demonstrated; no physical-formulation or oracle cause is adjudicated.
2. Six exact physical replay/byte gates fail in the preserved baseline Linux Haswell discrimination run, while default candidate checks pass: anchored enclosure active replay; curved-pair cancellation/exception rollback; curved-S3 active/open restart; fibre enforcement preflight; fibre committed recovery; fine staged lifecycle opening. Full node IDs/errors are in the original failure map and completion report. Small physical-field differences must not be deleted from checkpoints or rounded to force a pass. These failures do not by themselves prove engineering-response inaccuracy.

Unrelated numerical-route failures remain red in reproduced baseline groups: coupled BL5 material history and native fibre/BL5 lifecycle exhaust their existing nonlinear/cutback budgets. Other reproduced failures concern prepared authority, native predecessor tags and gauge helper identity; no shared/rev8 source is changed here.

Exact six replay selectors (retained red under the saved Haswell discrimination):

- tests/test_general_contact_native_anchored_enclosure.py::test_anchored_accepted_fixture_exact_replay[active-1-98d22bd2aff840df5d7b1034298891b179ed438ec9246a9f76b89445a7a15347]
- tests/test_general_contact_native_curved_pair_lifecycle.py::test_nonvirgin_rejected_trial_cancellation_and_exception_roll_back
- tests/test_general_contact_native_curved_s3_restart.py::test_curved_s3_active_restart_opens_and_preserves_prefix
- tests/test_general_contact_native_fibre_enforcement.py::test_enforcement_coarse_independent_gap_and_fixture_preflight
- tests/test_general_contact_native_fibre_results.py::test_committed_recovery_energy_units_origins_and_separate_storage
- tests/test_general_contact_native_fine_lifecycle.py::test_anchored_fine_policy_staged_lifecycle[opening]

## Whole-route reproduction

Unmodified command:
python scripts/run_portable_ci.py --workers 2 --timeout-seconds 1200 --matrix-shard-index I --matrix-shard-count 8 --matrix-subshard-index J --matrix-subshard-count 4

All 15 original selected baseline groups were run:5 passed,7 failed,3 shared 1200 s timeouts. Their private PYTHONPATH dependency targets were not retained by children that deliberately removed PYTHONPATH; those installed-child results are environment-limited and corrected focused checks are recorded above.

File-size-based partitioning changes when tests change. Same shard arguments do not imply the same selected modules. Candidate node map binds actual coverage; original nodes were checked directly where moved. Candidate installed Windows 6/3 fails an unrelated gauge helper identity check; Linux 5/3 passes 444 tests but no longer selects the radial module. The retained clipped-transient target remains in Linux 5/2; final disposition is appended below.

No matched complete-route speedup is claimed. The original 1200 s shared CI limit, native120s guard, physical models, tolerances, references, restart records and runner inventory are unchanged.

## Evidence and restart

Full logs, exact commands, source patches, explicit new-test hashes, process-wall accounting, failed attempts, stacks, worker handoffs and final reconciliation remain at:
.development/contact-ci2-20261012/COMPLETION_REPORT.md
.development/contact-ci2-20261012/COMPLETION_REPORT.json

This local evidence directory is not committed. GENERAL_CONTACT_RESTART.md preserves the previous restart history and links this handoff. Main and previous worktree source are preserved.


Final Linux5/2 disposition: exit124 at the original shared1200s limit, supervised process wall1205.663412064s, sampled tree RSS1294.1MiB. One partition completed178tests; the other was still in the original clipped-contact transient case. The exact-sweep repair does not close this timeout. A nonblocking stack locates current work in S3Jet2 differentiation/contact evaluation; this is not a profile or a quantified whole-route bottleneck. Retain the timeout and numerical gates.

The next contact performance outcome should address the complete clipped transient route with measured preparation/evaluation reuse, while preserving its original independent reference, all timesteps/events, derivative controls and physical-gap gates. Do not increase the limit, split away a failing scientific assertion, alter the fixture or begin another unbounded tuning campaign. Coordinate any runner architecture change separately with its owner.
