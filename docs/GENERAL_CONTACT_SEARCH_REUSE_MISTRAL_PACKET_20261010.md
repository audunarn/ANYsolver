# Bounded independent review: search-local contact certificate reuse

Mode: Read. No implementation or engineering acceptance authority. Review source and tests below; do not run numerical checks, write files, launch workers, access siblings, change Git/configuration or replay old executions. Give actionable defects, counterexamples, unsupported claims and missing coverage; distinguish actual tool observations from unverified evidence summaries. Do not infer whole-surface safety from sampled nonviolations.

## Exact scope

Repository: C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001.
Changed source: src/anysolver/general_contact/s3_patch_static.py, functions _search_start_point_key, _search_start_point_admissible, _swept_admissible and admissible_step_fraction. Source SHA256059801f3fdf1f61ba51397fc42d6078e0518954e0a81242788546637d4899bf7. Tests: tests/test_general_contact_search_start_certificate.py (16 cases).

The new code reuses only a successful first-point gap-budget decision inside one enabled admissible-step search. It must preserve end/path checks, exceptions, owner validation, position/error reconstruction, default-False behavior, immutable dependency identity, reentrant context restoration and existing caller cancellation boundaries. It does not retain physical/material/multiplier history or modify pressure/work/tangents, gap limits, subdivisions or force controls. No in-search cancellation callback is claimed. Inspect needed adjacent symbols in s3_patch_mortar_energy.py and semismooth_path.py to check these contracts.

## Evidence summary supplied by integrating lead

Private wheel ee0388151c9e872eb2ff39903916a81746072eeea7141423b3580d81a822d48a:654 exact payloads; sole s3_patch_static.py delta. Focused installed16 PASS,0failures/errors/skips. Literal recorded step2/iteration7 proposal tested separately in old46359304 and newee packages: all12 sweep endpoints and admission decisions and fraction0.00048828125 match. Point checks24→13; single instrumented search spans24.7857709→15.0947005s, process durations35.1477876→25.0911089s. This is one local comparison, not balanced whole-route performance qualification. Latest full trajectory previously timed out180s at iteration8; iteration8 proposal was not persisted and is not reconstructed as an observed call.

Closest refused endpoint is source element7/target element30:matching conservative lower bound−50.0132255814micrometres with50micrometre budget,43 nodes/spatial depth exhausted, node cap not exhausted. This is unresolved certification, not proven penetration. Independent witness on all pairs located full-proposal violation on different pair7/35; it does not cover refusal pair7/30. That coverage gap is explicitly retained; no safety or infeasibility claim follows.

All checks above are supplied evidence descriptions; this Read review does not replay them. Raw preserved outside this repo: C:/ANYworkspaceWork/contact_d1_merit_direction_repair_20261010/overlap-dual-start-reuse-v1/. Do not access external paths under this assignment.

## Requested disposition

Review consequential cache dependencies, method receiver identity, mutation/refusal/exception behavior, context lifetime, real caller coverage and admissible claims. Report files/symbols actually inspected, defects with examples, missing tests and whether a compatible repair is needed. Existing Astra feedback is supporting only and must not be treated as independent acceptance. C0-C9 engineering acceptance/release and pressure-core assessment remain open. No author can be the sole independent assessor.

## Focused continuation context

The first configured Mistral Read run successfully inspected source and helpers (22 completed tool effects) but its14-turn bound ended after a tool event, without a readable assessment. Its last assistant text was locating Git history. This is incomplete review progress, not acceptance or service unavailability. The relevant reuse code is CURRENT UNCOMMITTED WORKING-TREE code at SHA059801f3 above. HEAD5e121923 is the earlier overlap-dual integration; do not inspect commit history or confuse that delta with this reuse slice. Read the exact current functions and16-case test file and return a concrete review report. Limit further inspection to needed functional dependencies; no Git-history/status investigation or repeated full catalogs. Final response is required before the continuation turn limit.
