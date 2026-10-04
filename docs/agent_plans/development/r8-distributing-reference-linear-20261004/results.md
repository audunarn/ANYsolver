# Private distributing reference-linear compiler — 4 October 2026

Implementation/test status: IMPLEMENTED_NOT_QUALIFIED. This slice adds one
model-bound local operator, with no public facade, owner wiring or qualification.
Scientific F04/G0/G2 acceptance remains open. No legacy law/default changed.

The separate identity is
`GE_FLAT_Q4_DISTRIBUTING_DIRECTOR_POLAR_REFERENCE_LINEAR_V1_EXPERIMENTAL`.
It extracts the existing area-mean/director/polar-yaw prototype; it is distinct
from the historical position-only Procrustes candidate and BL5's released spin.
Exactly two adjacent Cartesian XY Q4 hosts, six explicitly identified shell
nodes and one existing physical beam nodal port are admitted. Reference-spatial
axes are declared identity; unsupported geometry/frames fail explicitly.

Frozen clipped integrals give area-mean translation and independent area-mean
director roll/pitch. Yaw is half the averaged planar displacement curl; shell
drilling coordinates supply no port action. The local constraint is6x42, never
a global dense matrix. Exact rational integration on stored reference coordinates
is converted once to binary64. Owned immutable buffers retain model IDs,
physical gather slots, centroid/offset, weights and source-bound identity.

For e0=b0-centroid, the declared reference-linear work law is
dc_t=du_b-dmean+[e0]cross domega_s, dc_R=domega_b-domega_s.
The transpose gives beam(f,m), shell force-f and shell moment about the area
centroid -(m+e0cross f). It preserves resultant virtual work while allowing
local nonrigid deformation; it does not enforce a pointwise welded surface.

ONE focused source suite passed34 checks in.32s (whole supervised2.191s,
sampled process-tree peak174104576B, actual numerical pools1/JIT off). Checks
cover both host orientations/asymmetric cuts, independently integrated bilinear
weights, all six infinitesimal rigid fields, director-only and distinct shear
fields, physical yaw force-couple work, eccentric force/moment/work balance,
an admissible transverse slope rejected by the existing rigid reference map,
renumbering/reordering, immutable arrays, geometry/mapping negatives and finite
input overflow. Six-row local rank is not a combined-model stability result.

Independent source review caught finite-input overflow returning nonfinite gaps
or work. The fix rejects unrepresentable computed results; new controls pass.
No numerical case was run before this correction. Different-family scientific
acceptance remains open. Actual root-source imports and command/runtime logs:
[development evidence](../../../../.qualification/b3-ge-e4-pl/r8-distributing-reference-linear-dev-20261004-v1/).

Helper SHA9768b46ab0d3fb89d083e9547f7aebe38046d800e23286ba8abe359ab1d77816;
tests SHA20d073ef846c9b20bdaddf7f53171c310a4d77a1b6af25b32ce15b56b56220ef.
No installed-wheel check is claimed for this private source-only slice. Earlier
installed results retain their original artifact scope. Next integration must
verify actual nodal-coordinate pullback and sparse/dense equilibrium/reactions
before any experimental owner admission. Finite objective pose, Hessian/chart
transport, shell energy/thinning/refinement, other hosts, overlap audits,
external comparisons and the complete footprint programme remain mandatory.

## Actual GE reference assembly bridge

The private adapter `_stiffened_shell_ge_distributing_reference.py` now binds
the derivative to actual GE model IDs, geometry, nodal gather and sparse global
numbering. Candidate rows are independent of the owner's original point/rigid
rows; it leaves the original operator, state and public definitions untouched.
Model/state guards exclude advanced or finite-chart use. This is reference-only
implementation/test evidence, not public owner admission or F04 acceptance.

A three-Q4 clamped panel places the two-host attachment outside the fixed edge.
One native B3 retains all24 internal coordinates. The same material K, supports
and physical load vector are used for the six-row distributing candidate and
36-row full-vertex rigid control. Both are solved through general sparse KKT;
a separately congruence-balanced dense LU oracle is checked against the original
unscaled equations. No SPD assumption, tangent averaging or static condensation.

| Measure | Distributing | Rigid |
|---|---:|---:|
| Full coordinates / retained |90 /24|90 /24|
| KKT dimension / nnz |84 /2888|114 /3636|
| Scaled sparse/dense q difference |2.0023e-12|9.0609e-13|
| Scaled sparse/dense multiplier difference |1.7992e-16|6.8442e-13|
| Scaled equilibrium |7.8581e-13|1.4382e-13|
| Scaled constraint residual |5.8884e-21|2.4187e-21|
| External work F.q, J |0.011270906243963727|0.006182536679271101|

Eleven focused source checks PASS in.98s; whole supervised2.7651s, sampled
process-tree peak179613696B, numerical pools1/JIT off, empty stderr. Checks include
native retained equations, original dense KKT residuals, physical support and
side force/moment balance, transpose work, an admissible nonrigid slope, actual
point-coordinate pullback, reordered inputs, immutable arrays and stale/wrong/
closed-owner negatives. The distinct compliance is an outcome of these different
connection laws, not a physical superiority criterion or a general stability proof.

One pre-test startup attempt selected a runtime without psutil; it launched no
test child or numerical work. Its failure is retained. The successful run uses
the preceding Python3.14 environment, NumPy2.4.6/SciPy1.17.1/pytest9.0.3.
No installed-artifact result is claimed. Supporting independent OpenAI source
review found no blocking defect; different-family scientific acceptance remains
open. Guards cover model/state/mapping, not arbitrary mutation of private element
objects or K buffers. Saved JSON response arrays rely on the separate source and
input bindings, rather than proving their own physical admissibility.

Adapter SHAaaabc0f02721cca7a71531a1b4ce0afbc99028e8a34ccf67e5f9224ff6d376cc;
tests SHA02c11ffeb4cd5c25097f85bceb32558fdc8009abb35543633c787e80610dd608.
[Commands, runtime, responses and review](../../../../.qualification/b3-ge-e4-pl/r8-distributing-ge-reference-dev-20261004-v1/).
Next product boundary is explicit experimental reference-linear owner admission
and lifecycle/recovery integration; finite pose/Hessian/chart transport, other
geometry/materials, physical references and complete footprint acceptance stay open.

## Public experimental reference-linear owner

The existing `stiffened_shell.create_analysis` owner now admits the appended
`LinearDefinition.distributing_footprints` option and public
`GEReferenceDistributingFootprint`, `GEReferenceDistributingFootprintSelection`
and `GEReferenceDistributingFootprintWrench` types. No alternate solver is added.
Empty options preserve legacy identity payloads/capabilities/checkpoints. Selected
records are compiled once into six-row blocks after point rows, with explicit
multiplier slices, combined supported audits and the existing sparse factor cache.
All native retained variables remain. Accepted recovery reports exerted `-C.T lambda`
actions, shell moments about the area centroid and beam moments about its node.

Reference-linear nodal dead loads, accepted-prefix cancellation, selected physical
recovery and JSON/binary checkpoint/restore/resume are implemented and tested.
Finite/controller/chart operations, material updates, modes and external load
wrappers reject before work. Direct load compilation and modal admission also
reject mixed point/distributing models. Checkpoints bind the new law/geometry/
mapping identity; nonlinear kinds, corrupt bytes and retained-coordinate loads
are rejected. Supporting source review found missing public export entries and
inconsistent deep-JSON validation; both were corrected before the first run.

Source and installed suites each pass63 controls (6.05s/5.91s pytest; whole8.086s/
7.798s; sampled tree193679360B/193331200B). Actual declared imports and eight
source files match the artifact. Pools1/JIT off and empty test stderr verified.
The suite includes the earlier independent reference-KKT comparison, unchanged
historical identity oracle and legacy checkpoint/cancellation/factor controls.
Supporting independent OpenAI review is clear; different-family scientific
acceptance remains open. No old frozen checkpoint campaign was repeated.

Wheel `anysolver-0.4.7-py3-none-any.whl`,2225629B,
SHAf0267b0f5803ce69c1a181bfd7aa22bde06fa1aafdb65cbd56bba4d550745b4e.
Build/install succeeded with no download/dependency installation; build stderr
contains normal build phases and already excluded reports/scripts messages.
The source/import inventory binds NumPy2.4.6, SciPy1.17.1, pytest9.0.3,
ANYmaterial0.2.0, ANYmesher0.5.0 and ANYfileio0.3.2. Earlier wheels retain their
own evidence scope. No version/default/publishing/main change follows.

[Runnable public example](../../../../examples/stiffened_shell_ge_distributing_reference.py)
completed against the wheel: area2m2, centroid(2,0,0),24 retained coordinates,
constraint max5.8884e-21/equilibrium7.8581e-13,2064-byte checkpoint, onefactor
for repeated unchanged nodal solves. Shell exerted centroid action
(0,20,0,-2,0,23) and beam nodal action(0,-20,0,0,0,-23) include the eccentric
lever arm. These are this fixture's outputs, not external agreement.

ANYfem's point-modal `from_definition` converter now fails closed for the new
attachment instead of stripping it. One focused predicate PASS/.13s with the
installed solver and actual source consumer; the probe explicitly verifies the
new field so the conditional branch cannot skip. This is not installed new
ANYfem verification or a distributing consumer workflow; that route remains open.
Before committing, canonical LF normalization avoids a misleading whole-file
consumer diff. Original tested bytes are retained as consumer-source-v1.py;
byte comparison proves only newline representation changed. The changed-byte
consumer-v2 predicate passed/.11s (whole2.229s/sample175415296B), unchanged
installed solver. Consumer source SHA22788c4353ef24316ad692c9097852e52f737e0d522949d2a7ea4aebe446ab60;
the earlier mixed-ending identity and successful run remain retained.
[Raw commands/imports/resources/review](../../../../.qualification/b3-ge-e4-pl/r8-distributing-ge-owner-dev-20261004-v1/).
Public implementation remains EXPERIMENTAL_NOT_QUALIFIED: two adjacent Cartesian
XY Q4 hosts, generalized native reference response, identity selected beam triad,
and nodal dead loads only. Other geometry/material/finite/load/mass/spectral,
external/scale and aggregateF04/G0/G2 requirements remain mandatory.

## ANYfem installed workflow completion — 4 October

ANYfem product9b7482b and evidence6013db0 complete the separate strict
reference-distributing consumer. Empty point tuples remain empty; owned input
construction, standalone/native Project save/reopen, selected physical recovery,
checkpoint/resume, factor reuse, cancellation and unsupported-control rejection
are directly exercised. Source and installed suites each42PASS/4.78s;
whole7.069s/6.791s, peaks222838784B/189267968B. Actual pools1/JIToff and source/
wheel/site imports match. Supporting complete source/runtime review is clear,
not different-family scientific acceptance.

Consumer wheelSHA3b8e563dd5e8cf0ecfe42f4cc9f5a8f34d46780d50dd1b0f217c510259e5cc8f;
unchanged solverf0267b0f... reused without repeating its passed campaign. Installed
example has24retained/6constraints/onefactor, generations1/2/2/3, zero resumed
coordinate difference, equilibrium7.8581e-13/constraint2.9442e-21. It labels exerted
moments at the correct centroid/beam origins. Different-family, external physical
accuracy, finite law/material/spectral/scale and aggregateF04/G0/G2/G6 remain open.
[Consumer scope and exact evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-distributing-consumer-20261004.md).

The precommit byte check stopped on Git configuration newline normalization;
the commit occurred before inspection. Complete postcommit check proves37/39
file blobs byte-exact (all tested product/evidence), with only .gitattributes/
.gitignore newline-only changes. Original worktree inventory and complete
verification remain retained; no tested-source rewrite or replacement run.

Next physical question: no inspected existing CalculiX case is equivalent to
the new area law. Rigid-tip C3D20R reference has complete REF/ROT wrench/work
outputs but rigidifies the entire patch. Folded-web shared-node output lacks
sided actions, and the U1/US3 shear canary is explicitly closed at its current
discretization. Do not replay those cases as area-law accuracy evidence. A
beam-free common-action comparator needs independently derived midsurface-mean,
through-thickness director and polar-yaw work maps before external execution.

## Executed common-action feasibility — 4 October

The missing route now exists and has executed. It is a development comparison,
not a converged accuracy finding or F04/G0 acceptance. Both models use a1x.2m
panel,t.02m,E210GPa/nu.3, clampedx0, padx(.8,1)/y(-.05,0), port(.9,-.025,.05).
Native10x4Q4 has one six-row distributing pad and an unloaded free GE stub.
Resolved80C3D20R receives the independent observable's exact transpose loads,
without a rigid patch, invented point ties or a loaded beam idealization.

For pad areaA and thicknesst, m=mean(u_mid), omega_x=−mean(uy_top−uy_bottom)/t,
omega_y=mean(ux_top−ux_bottom)/t, omega_z=.5mean(dxuy_mid−dyux_mid).
The port displacement is m+omega×e; centroid wrench is(F,M+e×F).
Pitch/roll use opposite face tractions; yaw uses curl/perimeter work, and
translation uses midsurface work. This is not a pointwise welded top face or
3D material-polar director. Symmetric3Dshear and zero-pose warping counterexamples
are retained. Functional agreement on the admitted Q4 trace subspace does not
equate the shell and solid models' full deformation spaces.

Independent source review found three admission gaps: world-ULP geometry
tolerance could hide large-origin distortion, volume coverage did not prove
shared-face continuity, and scalar coercion admitted nonreal inputs. The repaired
helper bounds geometric residual by64eps*span, rejects unresolved worldULP/span,
checks complete nonoverlapping coverage and matching full faces/eight actual
nodeIDs, and accepts only finite real Python/NumPy scalars. Local6x60 tables and
shared midsurface ownership remain bounded. No global dense mechanical operator.

Focused map/deck/parser57PASS/v4; final nonzero rigid-field/root-couple parser
consequence12PASS/v5. Nativev3 independently records actual retained station
strain<=9.6072e-33/resultants<=2.6900e-29, rigid nodal/cell coordinates and
negligible covectors/stub work. Root-wrench error<=2.6084e-11; centroid transfer
error0. One factorization serves both loads. The quadratic work identity holds;
native equilibrium<=1.022e-12/weak gap<=1.695e-21. These are reference-linear
controls, not finite-strain validation of the unloaded stub.

| Quantity | Mx1Nm | EccentricFy10N |
|---|---:|---:|
| Native final external pairing,J | 1.9479439072217055e-5 | 1.3535404088164468e-5 |
| Solid final external pairing,J | 2.0343889583333332e-5 | 1.4022239458333334e-5 |
| Native relative difference | −4.24918995% | −3.47188031% |
| Solid pairing decimal print bound,J | 8.33333333e-12 | 1.26875e-11 |

All six resolved support-wrench discrepancies are inside their decimal output
bounds. Printed RF is insufficient for a1e-8 external balance certificate;
rounding bounds are not solver-error bounds. Native root moments include both
nodal moments and position×force; resolved moments use actual physical root-node
positions. No raw logarithmic multiplier is substituted for physical moments.

Windows/Python3.14, pools1/JIToff; unchanged solverwheel
f0267b0f5803ce69c1a181bfd7aa22bde06fa1aafdb65cbd56bba4d550745b4e reused.
CCX2.23 executable27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f
and actual reported singleCPU bind both completed runs. Each used1671physical
rows/80elements,600s/2GiB limits, one serial job at a time. Whole nativev3
3.0116s/161517568B; externalMx/Fy .1216s/.1206s and sampled8257536B/9306112B.
Sampling is not an exact peak measurement. No optimization speedup is claimed.

Rawroot `.qualification/b3-ge-e4-pl/r8-e02-distributing-area-feasibility-dev-20261004-v1`
retains inputs/commands, source/artifact hashes, actual imports, thread samples,
complete stdout/stderr/DAT/STA/FRD, parsed observations and failures. Final native
isv3; CCX isv2, reused unchanged after native root instrumentation. The initial
collection failure(v1), overstrict roundoff-control failure(v2) and nativev1
read-only SciPy buffer failure remain; they were repaired prospectively.
The roundoff assertion now uses gamma20*sumabs, not a relaxed scientific gate.
`.copy()` changes only the writable reporting buffer. Supporting OpenAI source
and runtime review clears the complete slice; different-family acceptance open.

Decision: feasibility is resolved; engineering discrepancy/convergence is not.
The existing native compiler admits exactly two hosts. The fixed physical pad
needs8/32hosts on20x8/40x16; separate two-host constraints would change the law.
Next extend only the reference-linear local compiler/binding to a bounded
conforming multi-host rectangle, keep exactly six rows and identical historical
two-host payloads/checkpoints, then assess paired refinement. Do not launch an
isolated finer-solid/axial campaign or infer formulation failure from this coarse
difference. Shell/solid kinematics, clamp layers and reduced integration remain
possible contributors. Mandatory external/G0/G2/complete-release gates stay open;
formalF03 authority remains unconsumed.
