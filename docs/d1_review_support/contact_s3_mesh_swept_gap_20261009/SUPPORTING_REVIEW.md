# Supporting review — whole-chord S3 material-gap candidate

Read-only early mathematical review, before the new source file existed. Same-family development input, not engineering acceptance.

The proposed inequality is a valid *sufficient* certificate when the raw target normal `N(t)` is nonzero throughout the interval: `Q(t)=G²(N·N)-(N·r)² >= 0` implies `|N·r|/||N|| <= G`. For affine physical point maps, `r` is degree 1, `N=(c1-c0)×(c2-c0)` degree at most 2, so `Q` has degree at most 6. A strict positive Bernstein lower control is conservative; exact contact at `|gap|=G` may be refused. Binary `G` must be promoted exactly (not ideal decimal 50 µm), with outward enclosures for original mapped physical positions and target facet corners. The old whole-chord union, rounded chart, source-ray and orientation prerequisites remain necessary.

Implementation checks once source is ready: (1) prove target-facet `N·N` has a positive lower bound (or an equivalent component sign/floor) for every accepted child; do not infer nondegeneracy solely from `Q>=0`, which also holds at `N=0`; (2) include all source-face corners and stored material points against every actual target facet over the original affine DOF chord, independent of pressure activation; (3) restrict original interval polynomials with exact dyadic coefficients, not recomputed rounded child poses; (4) require every subdivision leaf to pass and refuse on cap exhaustion, unresolved Bernstein controls, nonfinite inputs or preparation mismatch; (5) bind method, G, scope and limits in exact public/restart identity while leaving old weak/hard contracts unchanged.

This geometric bound cannot establish pressure/history-event absence, friction work along the chord, or accuracy of floating projection/Jet2 normal contact beyond the inherited guards. A safe-endpoint/unsafe-interior witness is essential because endpoint-only source is already known to pass such paths.

## Source-ready delta

`s3_friction_swept_gap.py` now exists. `point_facet_certified` forms the squared polynomial inequality with exact binary `G` promoted to `Fraction`, raw target normal and original mapped polynomial intervals (`:25-32, 40-44`). It separately requires a positive Bernstein lower bound for `N·N` (`:27-29`), so the `N=0, Q=0` false admission is avoided. `certify_material_gap` traverses every concatenated source corner and stored dense point against every target facet at each dyadic level (`:42-61`); success requires every segment at one level, and exhausting all levels raises (`:68`). `restrict` acts on original point polynomials, not rounded child poses. The owner first invokes inherited union/chart/source-ray and prepared-geometry guards (`:75-83`), while its new settings/factory/public profile and restart method identity are exact-type separated from the old weak/hard profiles. No witness/test or installed evidence existed at this source read.

**Actionable boundedness defect:** `MAX_SEGMENTS=256` and `levels=min(8, maximum_swept_subdivisions)` cap the number of segments, but the nested point×facet loop has no maximum *evaluation* count (`:18, 45-67`). `evaluations` is only accumulated and returned on success. The adopted checkpoint explicitly requires an evaluation ceiling; an admitted larger mesh/material-point set can multiply 256 segments by all points and facets before failing. Add a fixed or validated setting-bound evaluation cap checked before the next pair, fail closed when reached, and bind/report that cap in restart/result. This is a resource/domain guarantee, not a change to the Q inequality.

**Repair observed:** The owner added `maximum_material_gap_evaluations` to the exact new settings, checks it before each point-facet evaluation (`s3_friction_swept_gap.py:40-60`), and binds/reports it (`:69-71, 97-102`). Exhaustion raises rather than promoting a partial result. This resolves the evaluation-count issue at source level; installed refusal evidence remains pending.

**Witness domain gap:** `tests/test_general_contact_s3_mesh_swept_gap.py:21-32` constructs target plane `z=t*x` and material point `x=t, y=(1-t)/4, z=t`. The exact numerator at `t=1/2` is 1/4, while both endpoints have zero gap. This proves the Q algebra defeats endpoint sampling, but the point lies on the target triangle boundary at `t=0` and at a vertex at `t=1`. The inherited rounded strict-interior chart would not admit these endpoints as an actual material path. For a discriminating domain-relevant witness, use `x=1/5+3t/5, y=1/10, z=4t/5`: both endpoints are strictly interior and on the plane, while the midpoint numerator is 3/20 and `N·N=5/4`. A full source-face/mesh witness would additionally establish both chart domains and source-patch coverage. Current algebraic test should not be described as an admitted public-path counterexample until that is shown.


## Lead reconciliation of later source and saved evidence

The algebraic boundary-point example remains labelled algebraic only. The final
test additionally constructs a strict full-patch small-slope binary path, checks
the inherited mesh union/chart prerequisites and both safe endpoint certificates,
and independently proves the actual midpoint violation from persisted reference
coordinates/work maps using Fraction arithmetic. The source and installed proof
jobs pass. Thus the earlier point-domain limitation is addressed by this separate
production-geometry witness, not by relabelling the old example. Explicit cap,
nondegeneracy and every-part refusal tests pass; cached budget/cap mutation is
refused. Installed suffix, state/rollback/refusal and CLI evidence is bound in
CLOSURE.json and LEAD_INSPECTION.json. Same-family supporting assessment only;
pressure/history events, path energy and engineering acceptance remain open.
