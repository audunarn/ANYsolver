# S3 internal-seam generalized friction tangent — development result

2 October2026; parent6fe80cec; worktree `ANYsolver-contact-main-reconcile-20261001`,
branch `codex/contact-main-reconcile-20261001`. Level A development; C5 scientific
acceptance, physical rims and full programme completion remain open. Existing normal
equations, accepted subsets, dimensional tolerances and consumed authorities remain.

## Changed behavior and discriminators

The physical return chooses a stable-ID target facet. Its affine equations are
extended only for disposable derivative probes, with that same facet held fixed
for every FE column. This supplies one generalized member at an internal seam
rather than averaging different target-facet branches. Real candidates and commits
still require nonnegative material coordinates and full source coverage. Physical
target rims retain explicit non-success. The derivative identity and explicit
barycentric-probe resolution bound are part of restart identity.

One-sided force and moment directional errors meet1e-5 over h=1e-4 and2e-5 using
a second-order same-side oracle. The first development attempt used first-order
forward differences and failed: force relative error2.84e-4 at h=1e-4. Its error
reduces between4x and6x when h reduces5x, and the corrected same-side oracle passes
without changing h, the source equations or the tolerance. Preserve that failed
output; it is a test-resolution discrepancy, not a regraded pass.

A real static solve with rigid tangential translation constraints and free source
normal coordinates lands at a material seam. Its pressure is taken from the solved
press response to position the return point on the diagonal. The normal response
differs from fully prescribed motion, the path continues beyond the seam, and a
2/3 split reproduces the accepted history/displacement. The preceding genuinely
deformable-target workflow remains covered by the final installed selection.

## Observed evidence

| Run | Outcome |
|---|---|
| seamv1 source |1failed/2passed; forward truncation failure retained, solved seam/restart and probe-isolation checks passed |
| seamv2 source |1passed; second-order same-side force/moment check and first-order scaling discriminator |
| guardv3 source |2passed; forbidden physical evaluation/invalid topology/large probes rejected atomically and smooth pressure tangent retained |
| isolated build |Passed;14.1133430s/125308928B sampled process-tree peak |
| current installed candidate |**15passed**;39.3181718s/178593792B sampled process-tree peak |

Installed scope: all10 current material-anchor tests,2 legacy static/restart/context
checks, retained nonproportional-spin check and2 example modes. All456 Python modules
match source/wheel/site;237 imported modules resolve inside the isolated site.
Effective JIT off and BLAS/Numba1 asserted before/after.180s/999292928B caps unchanged.
Wheel SHA256: `69427166669b317a825b73686ae2dcd1087da750d40e5265d30231b97ba437da`.
Artifact: `C:/ANYworkspaceWork/contact-anchor-seam-package-20261002`.

The bounded Mistral Read [assessment/disposition](independent_review.md) supports
the construction and led to stricter probe isolation, topology-list validation and
an explicit resolution bound. It ran no tests and is not a C5 acceptance assessment.
Unchanged physical mappings/history are covered by current installed checks and
impact reuse of the [prior anchor evidence](../contact_c5_s3_material_anchor_20261002/results.md).
No complete-route speedup,5% no-contact performance disposition, release or application
admission is claimed. Full C0–C9 goal remains active.

## Next principal uncertainty

Friction uses3 fixed source quadrature points. Target nodal work is piecewise in
material-facet ownership, so even a constant traction can require integration
refinement as those points cross target facets. Quantify its error in the solved
deformable-target workflow with the same normal pressure basis, then improve the
friction integration/history representation. Preserve separate structural, contact
integration, tangential regularization and step refinement. Partial-overlap history,
finite rotations/creases, swept beam/native surfaces, nonlinear materials, arc length
and frictional impact remain required.
