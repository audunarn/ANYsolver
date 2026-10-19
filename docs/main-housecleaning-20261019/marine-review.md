# Marine / SESTRA source reconciliation review

State: source inspection only; supporting OpenAI review, not different-family scientific acceptance.
Repository: C:/Github/ANYsolver; assigned main baseline HEAD 49d2536c2. Scope: untracked marine_*.py, sestra_*.py, corresponding tests/docs and scripts. No product edits, Git mutations, imports, tests, numerical jobs or external execution performed. Only this report was created.

Read governing global AGENTS, repository ECOSYSTEM_GUIDE and canonical ecosystem philosophy revision 2026-09-24.2. Read the existing SESTRA living task note before source inspection. Historical failed comparisons, protected reports and execution authority remain unchanged.

## Actionable findings

1. **P1: process timeout cleanup dependency is checked after launching the process.** `src/anysolver/sestra_verification.py:377` `_kill_tree` imports psutil, but `execute_reference` first launches at line 431 and reaches that import only on timeout (line 436). `pyproject.toml` declares psutil solely in the dev extra. Under a base installation without psutil, an authorized external launch may time out, raise ModuleNotFoundError during cleanup, leave the owned process running, and omit execution.json. The surrounding run_verification catches the exception but cannot clean the process. Fail closed by importing/checking cleanup support before Popen, or supply a guaranteed cleanup implementation/dependency. Add a mocked missing-psutil refusal test that asserts Popen is never called; retain the existing timeout/evidence regression. Existing test at tests/test_sestra_verification.py:128 exercises timeout with psutil present and does not cover missing cleanup support. No actual subprocess was launched by this review.

2. **P2: the structure benchmark CLI has an undeclared mandatory plotting dependency.** `src/anysolver/sestra_structure_benchmarks.py:252` calls model_visual before native_solution in every native/compare case. model_visual imports matplotlib at line 169. matplotlib appears in neither runtime nor dev dependency declarations. A base+dev installation can prepare the suite but then reports all native/compare cases failed due to ModuleNotFoundError before computing mechanics. A documented tooling extra or explicit optional plotting behavior resolves the mismatch. `scripts/build_accuracy_report.py:10` similarly requires undeclared reportlab, but is a standalone report script rather than the solver path.

## Integration and claims observations

- Marine implementations use numpy/scipy and internal modules; optional ANYloads/ANYhydro imports inspected are localized to enabled provider contracts. No unconditional optional-provider import defect established in the reviewed source.
- Reviewed marine documentation consistently identifies development scope, excluded real-source/large-excursion domains and remaining W4/W6/W8/W9/W10 acceptance. No new dangerous qualification claim established.
- SESTRA living handoff explicitly retains measured failed components and distinguishes tooling from qualification/release. docs/SESTRA_LINEAR_VERIFICATION.md explicitly requires the source ANYfileIO routing used for its retained development evidence; this is not an installed ANYfileIO compatibility proof.
- tests/test_sestra_three_case.py:8 depends on `reports/sestra_development/correction_parent/reference_snapshot/20261008_140714_T1.FEM`. That file exists in this checkout, but is a historical report fixture; do not assume it accompanies a clean source checkout. test_sestra_deep_diagnostics uses a synthetic tmp_path seed and is portable with the required ANYfileIO APIs. An initial checkpoint mistakenly described the former as an ANYstructure baseline; corrected to the parent immediately after exact source reading.
- Full test_marine_linear.py includes convergence, analytical and frequency response numerical cases. Selecting the entire module is broader than a short housekeeping contract check. Broad numerical assessment was not authorized to this reviewer.

## Proportionate short check selection for the parent

Use the parent's authorized disposable harness, exact runtime settings and existing budget. Recommended initial contract/integration selection (not executed here):

- tests/test_marine_linear.py selected with `-k "invalid_inputs or caller_arrays or result_contract or cancellation or cancel_contract or exponential_kernel_builder or newmark_constants"`; omit full convergence/frequency-domain sweeps for this housekeeping pass.
- tests/test_marine_contributions.py: history commit/refusal, cancellation, immutability, transport failure and malformed provider cases.
- tests/test_marine_potential_flow_serde.py (two roundtrip/refusal tests), tests/test_marine_seabed.py (closed-form/refusal checks), and tests/test_marine_clock.py (short <=3 step context checks).
- tests/test_sestra_deep_diagnostics.py and tests/test_sestra_verification.py source-admission/refusal/prepare tests. The existing subprocess failure/timeout tests launch only small mock Python processes, not SESTRA; run them only under the parent's expressly permitted disposable-check authority after cleanup repair, including the new missing-dependency refusal case.
- Run tests/test_sestra_three_case.py only with the baseline fixture intentionally retained/available. test_sestra_structure_benchmarks.py has synthetic preparation/admission tests but also a native Castigliano solve; select by impact and the parent's numerical budget.

For marine touched by any concrete repair, include the corresponding production-path contract tests rather than treating generic helper checks as integration evidence. A fresh install/metadata inspection can establish dependency availability; this read-only review did not claim any install or import succeeded.

Remaining limits: this is a bounded hygiene/integration review, not a mathematical audit of every marine tangent, a frozen qualification run, installed-artifact acceptance, or a release recommendation. Parent owns repair, measured verification and final acceptance.
