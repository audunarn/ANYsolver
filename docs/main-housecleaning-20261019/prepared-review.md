# Prepared response / capsule read-only review — 2026-10-19

State: inspection only. Supporting OpenAI review; not different-family qualification. No numerical runs, builds, tests, source edits, Git mutations or workers launched. Existing failed evidence untouched. Reviewed under ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 revision 2026-09-24.2 with solver-METADATA-HANDOFF.md and prepared evaluator plan. Parent requested immediate handoff after user limited work to existing housecleaning/CI; findings below are deferred unless existing checks demonstrate them.

## Findings and limitations

1. **Standalone results source archive risk (static evidence, no reproduced build).** packages/results/pyproject.toml:31,34 locate package sources at ../../src; the existing src/anysolver_results.egg-info/SOURCES.txt lists ../../src/anysolver_results/*.py. Local setuptools _distutils/command/sdist.py:454–492 copies manifest members to join(release_base, member), then archives release_base. These parent-relative members resolve outside the release tree, so that recorded manifest does not form a self-contained source archive. Existing packages/results/dist contains only a stale 1.0.0 wheel, whereas project metadata is 2.1.1. Do not treat the old wheel as current package validation. A clean extracted-sdist-to-wheel check would decide this packaging issue; if confirmed, a staged project with local src/anysolver_results and relative src configuration preserves one canonical source tree. No build was authorized to this reviewer.

2. **Detailed prepared-response formula mutation concern (static, unexecuted).** prepared_static_recovery.py:829,841 import shell_surface_von_mises/beam_von_mises from anysolver_results.formulas inside each invocation. prepared_static_response.py:980–1006 captures callable globals transitively, but those imported symbols are locals and therefore do not pin the referenced module entry. Rebinding formulas.beam_von_mises after preparation could alter the certified_library detailed recovery route without changing the captured wrapper. Public capsule exports additionally run capsule_runtime_guard, which traverses registry.formulas module entries and should catch that mutation; do not generalize this concern to capsule export without reproduction. If development is later authorized, a public detailed-response mutation regression and explicit pinned shared formula bindings would settle the scope. Deferred under latest no-new-development instruction.

No other definite integration defect identified within this bounded review. This is not an exhaustive numerical or security audit.

## Proportionate existing-check selection for parent

Finite existing test files covering affected contracts: test_prepared_recovery_staging.py; test_prepared_static_response_preparation.py; test_native_affinity_fallback.py; test_result_capsule_numeric.py; test_result_capsule_metadata.py; test_result_capsule_runtime.py; test_result_capsule_export.py; test_native_authority_dag.py; test_native_guard_code_grammar.py; test_supported_rigid_mode_memory.py. Include existing result principal/surface-component tests if checking the moved shared formulas. Tests exercise refusal, mutation, cancellation, immutable snapshots, actual fallback routes and memory accounting rather than helpers alone.

CPython 3.12 exercises the Python native-guard fallback; it cannot establish cp311-win_amd64 C++ backend behavior. Native C++ tests/installed-artifact evidence require their applicable environment and existing authority. A passing source import does not establish wheel dependency resolution or standalone results package delivery.

## Handoff

Changed files: only this report. Checks actually run: read-only Git status/diff and source/config/manifest inspection. Failures: no runtime failures measured; one missing packages/results/MANIFEST.in observation and an initial Windows rg glob mismatch were read-command diagnostics, not product failures. Parent owns any repair, existing-test execution, packaging decisions, Git integration, publication and acceptance.

## CI bootstrap reconciliation follow-up

Implemented installation wiring only in .github/workflows/ci.yml. Resolver builds a same-checkout results runtime wheel into .results-wheels and supplies it as an explicit candidate to binary-only coordinated resolution. The pytest, numba, pardiso, both ecosystem compatibility endpoints and wheel jobs install ./packages/results before root installation/build. Clean wheel --target installation explicitly includes ./packages/results, so it does not depend on the global preinstall. No package source relocation, source archive framework, formulas or physics changes.

pyproject.toml retains its preassignment dirty contents: an initially considered matplotlib dev dependency was removed after source inspection showed the existing prepare_suite fixture does not call model_visual; only the external-reference run_suite path does. No test changes were needed.

Pure checks actually run: root/results TOML parsed using stdlib tomllib; all32 matrix entries compare identically to HEAD; 3editable jobs and six runtime preinstall sites verified; resolver wheel candidate and clean-target package entry verified; workers2/timeout2400/8x4sharding retained; git diff --check passes. System Python has no PyYAML, so no full YAML parser claim is made. No tests, builds, pip installs, numerical processes, workers or Git mutations were executed. Parent owns final YAML/CI acceptance and publication. The earlier root-external results sdist concern remains deferred.
