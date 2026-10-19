# Enriched-reference CI portability disposition

State: read-only source and SHA inspection; no tests, imports, solver/reference jobs, workers, Git mutations, source edits or historical evidence changes. Parent owns disposition and any future execution authority. Scope is the failure in test_original_matched238_complete_independent_seven_gates, CI job118318590634.

## Decision

This test executes a NEW complete independent scientific/development assay; it is not a saved-evidence validation. tests/test_general_contact_enriched_reference.py:140 calls runner.run; ENRICHED_REFERENCE_OUTPUT selects only the output directory. scripts/general_contact_enriched_reference_run.py:48 defaults the binding to a workstation path; after verification it builds the current matched238 model, asserts an unloaded owner, and calls assess. A missing INPUT_BINDING file is the first portability failure, not the whole missing fixture.

The narrow housekeeping disposition is to retain the four portable synthetic tests in ordinary CI and require an explicitly provided authenticated binding for this full historical assay. Skip this one assay with a precise unavailable-fixture / explicit-execution-required reason when that input is not supplied. Do not skip or weaken its seven assertions when explicitly activated. A supplied but invalid binding must FAIL, not skip. Do not merely inspect saved PASS gates while retaining the claim that this test executed an independent reference. Changing the runner to accept a selected binding path can be a small wiring change; changing its scientific/source binding acceptance is a separate contract decision.

No complete portable execution fixture can be derived by copying a single JSON or only the producer pair. Retaining a default-on full assay requires an explicitly adopted portable source-rebinding contract, source/input identity, numerical execution budget and environment; these are beyond a source-only fixture relocation. This review does not establish permission or current suitability for a rerun.

## What executes

reference.assess (line394) checks the full238/184/25 layout and executes seven gates in original order:

1. current_full_equilibrium
2. current_L1_NCP_and_independent_gap
3. current_force_moment_balance
4. independent_current_integration_force_moment_support
5. complete238_current_work_and_quadrature
6. independent_current_contact_KKT_equilibrium
7. independent_nonlinear_reference

No criteria change is recommended. The existing source fixes STEPS=(1e-5,3e-6), ORDERS=(4,8), equilibrium/force/moment/reference comparisons1e-6, NCP L1 limit1e-8, independent gap lower bound-50e-6m and quadrature predicate1e-7. full_work evaluates both perturbation signs for all238 coordinates at both h/order combinations; the original producer response and the independently solved endpoint each receive complete work checks if earlier gates pass. independent_reference starts from u=0,z=0, performs up to4 modified Newton steps using np.linalg.solve on the185-dimensional KKT matrix, and evaluates independent geometry/gap certificates. ContactOracle and rational/Bernstein bounds are active computation, not report replay. Scientific_acceptance remainsFalse even on PASS.

## Minimum exact inputs under the existing runner

- INPUT_BINDING.json itself, identified below, with18 directly hashed files.
- All18 direct files listed below. Several are authenticated provenance only but verify_binding still reads/hashes each; dropping them would alter the protected contract.
- ROOT_SOURCE_BEFORE.json includes3896 baseline source file members. verify_binding resolves relative names beneath C:/Github/ANYsolver/.worktrees/contact-portable-replay, and verifies every raw SHA. Exactly five owned-source replacements are admitted in source_exclusions, already enumerated in the binding. This means3891 other baseline members remain RAWexact. Seven reference/test files are also direct hashed entries (the five owned files plus polynomial helper and its test).
- Current executable model builder examples/general_contact_enriched_matched.py reads docs/d1_review_support/d1_actual_cutback_single_press_20260929.json, then scripts/general_contact_d1_interior_press_dev.build_saved_cycle reconstructs the original structural model/control definition. The built descriptor must equal the frozen producer descriptor exactly. The saved input is repository-relative, not the missing external INPUT_BINDING.
- Current executable package and helper dependencies. Historical hashes in the binding do not prove that the currently imported same-name code is those exact historical bytes; the fresh current execution identity remains material.

The historical direct18 audit found17 matches and1 mismatch. The historical worktree test_general_contact_enriched_reference.py differs from its frozen hash. Therefore restoring the old absolute path layout would still fail source binding before science. This review did not hash all3896 baseline members and makes no claim that the remaining historical baseline is intact. Current-main helper raw hashes also differ from frozen direct helper hashes; no semantic-vs-line-ending equivalence was adjudicated.

## Exact identity inventory

Binding: C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-polynomial-reference-work-v15/INPUT_BINDING.json; SHA256 aa1be2f9dab42ccdf08d9ffd4864aad27a311933015924da19516f19e363dd85.
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/initial/child/science/MATCHED_ACCEPTED_RAW.json; expected SHA256 607bb11413fc7d4bd64685e7a57271918a8e5b6f9f4e3bc038c41d71b59aed4c; actual 607bb11413fc7d4bd64685e7a57271918a8e5b6f9f4e3bc038c41d71b59aed4c; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/ROOT_CLOSURE.json; expected SHA256 e012b5d201d88dc88c2383d05738b414ad24f4cafeb2430b2ded026974304934; actual e012b5d201d88dc88c2383d05738b414ad24f4cafeb2430b2ded026974304934; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/SOURCE_MANIFEST.json; expected SHA256 14a141d28631901e1ce1e76591fbf49ba571a2222771d5385ea96555bad846ba; actual 14a141d28631901e1ce1e76591fbf49ba571a2222771d5385ea96555bad846ba; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/initial/RESULT.json; expected SHA256 2569af744e48c8bc0b2ed99d0ccdfafaee8a3276b78f5c90ccc80e63bc8f567b; actual 2569af744e48c8bc0b2ed99d0ccdfafaee8a3276b78f5c90ccc80e63bc8f567b; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/initial/child/runtime-before.json; expected SHA256 2a271ca4b02f393c9e5ec150dd5447c8d2119b804d081c6aa1e7fd6a883abb5d; actual 2a271ca4b02f393c9e5ec150dd5447c8d2119b804d081c6aa1e7fd6a883abb5d; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/initial/child/runtime-after.json; expected SHA256 27adf6c6bcb81ccc7ef8869d52b8b9cea2fe0e4c3fc4b1ef0dced4569defeb4c; actual 27adf6c6bcb81ccc7ef8869d52b8b9cea2fe0e4c3fc4b1ef0dced4569defeb4c; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/ROOT_TERMINAL_AUDIT.json; expected SHA256 636c953b2ed0d6a384202f5736295e92452800d997b2066e5a946468901fa384; actual 636c953b2ed0d6a384202f5736295e92452800d997b2066e5a946468901fa384; matches=True
- C:/ANYworkspaceWork/contact_trackB_dependency_repair_20261013/d1-certified-small-cut-v13/final/RESULT.json; expected SHA256 8fb3135f8d4110daa7488c8b21c2f3f0ef6fc810711108f2aca9d764b7fafc63; actual 8fb3135f8d4110daa7488c8b21c2f3f0ef6fc810711108f2aca9d764b7fafc63; matches=True
- C:\ANYworkspaceWork\contact_trackB_dependency_repair_20261013\d1-polynomial-reference-work-v15\ROOT_SOURCE_BEFORE.json; expected SHA256 8d3f73cc7202cc669757f8c7e211f5d4168320d5da6734fcb836408b64d817e2; actual 8d3f73cc7202cc669757f8c7e211f5d4168320d5da6734fcb836408b64d817e2; matches=True
- C:\ANYworkspaceWork\contact_trackB_dependency_repair_20261013\d1-polynomial-reference-work-v15\ROOT_SOURCE_AUTHORITY.json; expected SHA256 175565a4760e67149ae3fda4dde2983aa2131aa036f8d706ca03543233c3b1a3; actual 175565a4760e67149ae3fda4dde2983aa2131aa036f8d706ca03543233c3b1a3; matches=True
- C:\ANYworkspaceWork\contact_trackB_dependency_repair_20261013\d1-polynomial-reference-work-v15\ROOT_METHOD_DECISION.json; expected SHA256 a37de35f0a59b5019ebe5dc0b403930e29a501b345044053636626269e817453; actual a37de35f0a59b5019ebe5dc0b403930e29a501b345044053636626269e817453; matches=True
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\scripts\general_contact_enriched_reference.py; expected SHA256 9f34b7bea76345e30b45942f36f971db7a23c6a52c0646e483f879c5e130be33; actual 9f34b7bea76345e30b45942f36f971db7a23c6a52c0646e483f879c5e130be33; matches=True
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\scripts\general_contact_enriched_reference_geometry.py; expected SHA256 c3c2cad445f43ada2cf39cfca4399aec2c4151948b8a719f6f2d55254709c3de; actual c3c2cad445f43ada2cf39cfca4399aec2c4151948b8a719f6f2d55254709c3de; matches=True
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\scripts\general_contact_enriched_reference_bounds.py; expected SHA256 7c8924a3a5b51219319e9717e185fcccdf357ab95fd2fdd804c667ae0a0e5fd3; actual 7c8924a3a5b51219319e9717e185fcccdf357ab95fd2fdd804c667ae0a0e5fd3; matches=True
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\scripts\general_contact_enriched_reference_run.py; expected SHA256 fe0d3a5fb1f688b7760859439be4b1122a8ee4a281de0ce5c61ad32a6c288d44; actual fe0d3a5fb1f688b7760859439be4b1122a8ee4a281de0ce5c61ad32a6c288d44; matches=True
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\tests\test_general_contact_enriched_reference.py; expected SHA256 134bf052ac301efd043cde067ee3d4949dd70863ba561aa8624c59219e9cd398; actual af30e876bba6b191902f9670fe14c7524db55459a16a42e4d02acba950bbe977; matches=False
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\scripts\general_contact_enriched_reference_polynomial.py; expected SHA256 8c31fb4603b81e26cc671bc1854102579a36726a9e7207b3c2b86896c1411027; actual 8c31fb4603b81e26cc671bc1854102579a36726a9e7207b3c2b86896c1411027; matches=True
- C:\Github\ANYsolver\.worktrees\contact-portable-replay\tests\test_general_contact_enriched_reference_polynomial.py; expected SHA256 66b4f1632598be8ac4093464be7238007fb262b301f94df04f1aca85ac753700; actual 66b4f1632598be8ac4093464be7238007fb262b301f94df04f1aca85ac753700; matches=True

Current-main read identities (not replacement authority):

- C:/Github/ANYsolver/docs/d1_review_support/d1_actual_cutback_single_press_20260929.json; SHA256 7cd7ff2300082179b084926e33de0bf5213b424244e83e0389c0ec01df6b82a7
- C:/Github/ANYsolver/scripts/general_contact_enriched_reference.py; SHA256 560482fefb4f921402a16c10261c46d65c35774ba80c1cdf38138220b1649786
- C:/Github/ANYsolver/scripts/general_contact_enriched_reference_geometry.py; SHA256 2d9fcb3213948bee90e0e947f318a8a41e3e1e8ed1ec1454848f0d0370ce94be
- C:/Github/ANYsolver/scripts/general_contact_enriched_reference_bounds.py; SHA256 8f1f6576f00c56206ae1f35a6941614bede4ce720df7615c248ebec7e4570f9b
- C:/Github/ANYsolver/scripts/general_contact_enriched_reference_run.py; SHA256 a7b7aa473b8616d75c61c19f5881a5fd094f2195971184ec60c90c1677578650
- C:/Github/ANYsolver/scripts/general_contact_enriched_reference_polynomial.py; SHA256 88676aeb856b18368f1e718af2db7e8a9ebc8221eeb48071aebb11c515efb91a
- C:/Github/ANYsolver/tests/test_general_contact_enriched_reference.py; SHA256 86c601c164e029612572db0527b27fb6dce47f7fa43d81e0cb922d3429004a67
