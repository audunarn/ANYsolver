# GE-B3 native physical fibre section — development checkpoint

Parent: `b297c72bfa73ae439224f2af13539e09f27c8827`, tree
`bb36f26c45f966b85b38f34ee5c3847ded278ca1`.
Independent review: **PENDING**. Production qualification: **false**.

## Implemented

A new private strain-controlled section supplies explicit physical fibres,
axial/biaxial plasticity, a declared coupled elastic background, physical fibre
recovery and immutable trial histories. It does not import legacy beam
mechanics. The equation map derives the fibre sign from the native right-handed
curvature and gives the complete incremental material potential.

Linear and continuous piecewise-linear hardening, including perfect-plastic
plateaus, have analytic energy integrals and bounded scalar return maps.
Generalized resultants and algorithmic tangents are the first and second
variations of that potential. Exact yield/table knots are labeled semismooth;
zero plastic tangent is retained without stabilization.

Paired binary64 histories and recovered responses are computed at 80 decimal
digits. The tests independently enumerate exact-rational material minima;
this is a different equation reconstruction, **not independent authorship**.
The material background permits explicit anisotropic generalized coupling.
No fibre geometry or centroid is inferred, and material-axis re-expression
preserves work and physical fibre stress.

ANYmaterial documents true-stress curves. Its linear/table numbers can only be
captured with an explicit native-parameter reinterpretation; no automatic
finite-strain measure conversion or equivalent material adapter is claimed.

## Separate test inventories

- Initial section inventory: 35 passed, 1.593 seconds.
- Final section plus directed-law regression cycle A: 62 passed, 1.696 seconds.
- Final section plus directed-law regression cycle B: 62 passed, 1.674 seconds.

The two final cycles have 11 byte-identical JSON pairs. They cover stiffness
contrasts 1, 10^4 and 10^12; loading/unloading/reversal; exact-rational potential,
resultants, tangent and physical recovery; material-roll covariance; virtual
work and directional derivatives; perfect plasticity and knots; immutable
inputs; trial discard/replay/cancellation; and invalid material/history data.
These are small correctness tests, not benchmarks or formal qualification.
No resource request was created or consumed.

## Preservation

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-section-development-20260907-49eb348ad25c`.
35 content files, 593,998 bytes. Manifest: 5,626 bytes, SHA-256
`84bb929e1f820503640d63010d2069b841ad730a15c1ecff9594a10905cb782d`.
Final source snapshots, all three inventories and emitted records are bound.
The initial inventory predates the explicit measure-capture guard and linear
curve-traversal refinement; no initial source-hash equivalence is claimed.
Original test outputs and all predecessor evidence remain preserved.

## Required next work

Derive and implement the coupled **station/fibre complementary problem** needed
by the retained-resultant beam. The existing one-plastic-direction-per-station
solver cannot be relabeled or reused as though fibres were independent under
stress control. Bind station-owned trial/commit/discard state, physical fibre
recovery, restart and final-state replay to the assembled adapter, then test
the curved two-macro loading/reversal cases and material tangents.

General nonlinear coupled sections and measure-consistent material adapters,
distributed loads/couples and their tangents, arc-length/cutback/postbuckling,
reference-backed buckling, broader straight/curved/slenderness campaigns,
package/performance gates, independent review, and objective eccentric/curved
beam-shell joints remain required. No public selector, default, existing
B2/B3/Q4/S3 mechanics, release or qualification record changes in this step.
