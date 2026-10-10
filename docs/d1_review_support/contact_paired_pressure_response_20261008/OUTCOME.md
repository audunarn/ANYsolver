# Paired pressure response outcome

Implemented and exercised a diagnostic of the actual nonsymmetric finite-Q4 monolithic equations. An authenticated 60-degree source-sliding pose was compared with one prospectively fixed source-X refinement through the installed public contact path. This is verified development evidence; pressure admission, mesh-uniform stability, engineering acceptance and release remain false.

## Results

All positive fine-Q1 supports were retained. The literal constrained selector removed static BC and path-control coordinates, preserving complete angular triplets. Force detection, displacement response and chart-gap response are separate reported matrices with dimensional scales from README.md. Full pressure-domain null vectors are exposed even when the matrix is wide.

| Quantity | Base: 6 pressure modes | Refinement: 10 pressure modes |
| --- | ---: | ---: |
| Numerically resolved force-detection rank | 6 | 10 |
| Smallest scaled force-detection singular value | 0.02205140626 | 0.01135455535 |
| Full paired gap-response condition number | 9564.979709 | 166607.0357 |
| Active two-mode gap-response condition number | 34.86293864 | 36.29378500 |
| Positive support sum (m^2) | 0.7919999361 | 0.7919999722 |
| Minimum positive support (m^2) | 0.06195196465 | 0.01742399333 |
| Dimensionless solve backward error | 1.1361e-17 | 1.2963e-17 |

The full gap-response condition number increased by 17.41844110. Both matrices retain measured nonsymmetry; these are singular-value diagnostics, not a symmetric coercivity result or a universal pressure cutoff.

The maximum common-material-node normal displacement difference was 5.3922143e-7 m. The physical source contact-resultant difference had norm 1.6853289e-5 N, against the separately declared 1e-4 N force scale. These are meaningful response differences, without a registered spatial-convergence pass criterion. Structural and pressure spaces both changed, so their effects are not isolated. The two full-reference Q1 bin traces are numerical pressure diagnostics, not overlap-supported physical bin forces.

## Checks actually run

- Manufactured nonsymmetric response and independent wide-matrix nullspace oracle: PASS.
- Authenticated base 60-degree pose: independent spatial-spin work error 3.1722e-16; complete q/z, chart-gap and complementarity directional checks had maximum relative error 5.4045e-9, below 1e-5: PASS.
- Fresh installed refined path in five checkpoint-connected jobs ending at steps 4, 8, 12, 13 and 14: PASS. Accepted snapshot inventory is exactly 1 through 14. Opening/recontact steps 15/16 were not executed in this slice.
- Independent accepted-pose skin reconstruction and exact-binary gap bound, physical wrench, complementarity and equilibrium over all static-BC-free coordinates including control reactions: PASS. Maximum normalized L1 equilibrium was 2.02435e-7; maximum normalized complementarity was 5.44892e-11. The unchanged dimensional gap gate is 50 um.
- Current installed saved-matrix consumer and profile, selector, partial-angular, general-MPC, scale and nonfinite-input refusal controls: PASS.

Nine testcase invocations passed. One earlier base invocation failed at the new wrapper's contributor-profile guard before the equations ran: the static contributor profile was mistaken for the outer path-state profile. The exact guard was corrected in V2; V1 package, failure, logs and source snapshots remain intact. Pre-proof test corrections fixed inherited one-based gap-oracle node indexing and the distinction between compliance-free coordinates and scientific static-free equilibrium coordinates. Initial and corrected source manifests are preserved; unaffected algebra was not rerun or regraded.

## Accounting and provenance

Scope PAIRED_PRESSURE_RESPONSE_DEV600 used 273.9786295999802 of 600 measured process-wall seconds across 12 serial jobs, including two private builds and the retained failure. Remaining authority is 326.0213704000198 s; the protected 60 s reserve was not released. Every job stayed below 60 s and 953 MiB. Peak process-tree RSS was 213.4140625 MiB. Runtime evidence records JIT disabled, Numba/pools one and 2943 authenticated private imports. No active process remains.

Current V2 wheel SHA256: d38c213f96ae85175a5bd0ead0a1628ba385884b555244a4670e6e2516ca4fb2. Private site: C:/ANYworkspaceWork/contact_paired_pressure_response_20261008/candidate-v2/site. It contains 634 payloads: all 633 preceding payloads are byte-identical, plus the diagnostic module. Exact commands, per-attempt inputs/results/runtime hashes, failed evidence, ledger and CLOSURE.json are under C:/ANYworkspaceWork/contact_paired_pressure_response_20261008.

## Disposition and next dependency

The supported signed pressure spaces are numerically detected under the declared source-scoped norms, while the full response conditioning and physical response change materially under the single directional refinement. This does not close pressure/spatial acceptance. The next useful dependency is a matched diagnostic separating pressure-trace resolution from structural compliance at fixed geometry, with independently overlap-supported physical response. Any change to the existing fine-Q1 solver pressure space requires a separate architecture/scientific decision; no additional refinement, stabilization or law change was made here.
