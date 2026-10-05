# Final impact-evidence addendum

Read-only delta review; no numerical execution or test run by reviewer. The completed review and prior evidence were not modified.

`installed-impact/stdout.log` records four passed in 5.42 s. `execution.json` records completed/exit zero and 6.2108477 s supervised elapsed time. The selected cases are the Q4, mixed and all-S3 parameters of `test_linear_physical_wrench_reference_restart_and_selection`, plus `test_explicit_curved_point_owner_reference_finite_restart[True-100.0]`. They exercise reference-linear recovery/checkpoint selection and curved-owner reference/finite/restart behavior. Together with the previously reviewed 47 distinct cases, retained installed evidence now covers 51 distinct passed cases, while preserving the original helper-import failures and separate repair results.

`run-impact.py:9` replaces the preceding broader path assignment with PYTHONPATH = installed site first, repository root second. The supervisor passes this environment and uses the TEMP evidence directory as child cwd. The standalone pytest.ini adds no src path. The copied test files contain no sys.path/PYTHONPATH edits; neither repository root nor fixtures-v3 contains an anysolver package, and the installed site package exists. This supplies installed-site import admission. This impact run does not separately log actual Python module __file__ paths; the already reviewed complete 417 source/site byte bindings remain the artifact provenance evidence.

All six fixture-impact-binding.json hashes match both current source test files and the preserved fixtures-v3 copies. Stderr retains an ignored pytest atexit cleanup PermissionError for the pytest-current link. It occurs after the passed results and did not change exit status; it is not a numerical/test failure.

No new correctness issue found in this evidence delta. Scientific qualification, effective external OpenSees threads and the previously stated open gates remain unchanged.