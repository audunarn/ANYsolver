# S3 material-anchor friction integration — development result

Source parent474a96c6, plus the changes in this checkpoint. Plan2026-10-02.8.
This is implementation/testing evidence; C5 acceptance and application admission
remain open. The accepted normal D1/D2 profiles are unchanged.

## Decision and independent reference

At flat uniform normal pressure5Pa, mu=.3, kt=1000Pa/m and source slide.39m,
the returned source triangle translates.3885m. Target node7's shape is
max(.1885-.4*bary0,0). With independent reference-triangle density2(1-bary0),
its exact mean is A²/B−A³/(3B²), independently checked by scalar quadrature.
Exact residual force is−.00898521771875N. The prospective case-specific
integration budget remains0.2%; it is not a universal application tolerance.

| Reference refinement | Material points per source face | Selected nodal force relative error |
|---|---:|---:|
| 0 | 3 | 8.474462965% |
| 1 | 12 | 0.225010894% |
| 2 | 48 | 0.225010894% |
| 3 | 192 | 0.048795539% |

Levels1/2 form a plateau; no convergence-order claim follows. Positive weights,
first/second moments and the complete four-target-node force distribution pass.
Normal pressure remains the same three nodal unknowns. Level0 remains available
for compatibility; the material-anchor example explicitly selects level3.
Material coordinates/weights and refinement bind restart, with a preallocation cap.

## Focused verification and actual failures

- Baseline3-point exact-force check failed at8.47446%; retained unchanged.
- Initial source4checks passed. Coupled coarse/refined runs both completed
  press/stick/slide/reverse/open/recontact, solved target motion and exact split
  history restart; incompatible refinement/property checkpoints rejected.
- Installed focused-v2:24passed,1failed. The new test incorrectly required the
  *entire* global tangent column to vanish after restriction. The normal owner
  restricts physical-coordinate derivatives and the driver subsequently applies
  TᵀKT; its global column can remain. Corrected assertion checks friction's
  column and preserves nonzero constrained reaction. Direct cached/full maps,
  normal variations and equal/opposite translations pass. No production equation
  or numerical acceptance tolerance changed to resolve this test defect.
- Corrected installed selection:2passed. Union covers25distinct checks, including
  coarse/refined1e-5 directional tangents, all anchor/state/seam tests, legacy
  static history/context checks, retained-spin work and both example modes.
- First installed invocation used a nonexistent test selector: exit4, no tests
  executed. Retained as runner-input error; not a mechanics result.

## Installed artifact and resources

Artifact: C:/ANYworkspaceWork/contact-friction-quadrature-package-20261002.
Wheel SHA256154d32192c8d456b83ca3f546fd3ce56c9f3fdf11971f4a1a6f618cc0b1d71bf.
456source/wheel/site modules match.237onsite imports in the full selection,
225in the corrected selection. Actual JIToff and BLAS/Numba1 checked pre/post.

Build13.5463412s/124596224B sampled process-tree peak. Focused-v2
60.7496113s/185835520B; corrected-check3.1236272s/177225728B. All within
180s/999292928B. The refined coupled full/split/restart check took15.53s versus
4.55s coarse in the source run; these have different quadrature accuracy, so
no speedup claim follows. Local map caching bounds refinement cost and avoids
per-point full-model dense maps; it is not a whole-route performance qualification.

## Scrutiny, reuse and remaining work

[Independent review and disposition](independent_review.md). Old accepted normal
and no-contact evidence reused by impact analysis: this changes the opt-in
material-anchor owner only, not structural/sphere/default paths. No release,
no-contact5% performance or general C5 qualification claim is made.

Next principal question: event/step accuracy of activation and endpoint/chord
dissipation, then partial-overlap history transfer. Fixed reference refinement
does not solve adaptive history repartitioning, physical rims, finite rotation,
warped/crease surfaces, beam/native friction, nonlinear materials or arc length.
The full C0–C9 programme remains active. See raw_index.json/raw.zip for retained
source bindings, failed inputs/logs, installed inventories and review logs.
