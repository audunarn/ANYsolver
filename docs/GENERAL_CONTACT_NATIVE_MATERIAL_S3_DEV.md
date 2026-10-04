# Retained native material patch / deformable S3 — development

Latest source `fbdd5c27`, 4 October 2026. One/two native beams now act through
multiple physical S3 maps in the existing owner (two to eight explicit pairs,
256-coordinate cap). Each represented S3 has its complete authoritative shell
columns; retained native coordinates and cross blocks are not condensed away.
This remains implemented/installed-tested development, not engineering acceptance.

`python examples/general_contact_native_material_s3.py --two-beams --two-facets`
uses three material patches, two orthogonal deformable S3 skins and all120
coordinates. `--two-facets` alone uses one beam and all78 coordinates. Both
facets press, open and recontact; an open-state checkpoint continues exactly.
The distinct multiple-patch profile is
`NATIVE_B3_GE_MULTIPLE_MATERIAL_PATCHES_S3_STATIC_DEV_V1`.

Vertex forces now follow the actual S3 work-map corner order. The previous
global-reshape report defect is corrected; residual/tangent numbering invariance
and physical wrench checks pass. Complete offset maps are validated against the
existing six-coordinate shell contract. Top skins with a nonpositive reference
face/director orientation reject explicitly; no normal is flipped. Area numerical
revision `anchored_projection_radius_reference_full_shell_work_v2` binds restart,
rejecting earlier area checkpoints. Legacy line checkpoint identity is preserved.
The uncompensated normal route keeps its existing18-column admission.

31 installed checks in two bounded groups:142.032s/188338176B and6.164s/325988352B.
All517 package files and223 imported modules match; JIT disabled, numerical pools1.
Private wheel SHA256 `db29c3e1c28a53f1d6e4cf5f56727f2216c8c953adf7fc77be46392b2bfdd360`.
The120-coordinate fixture has normalized support force/moment1.40e-9/1.25e-9,
owner directional errors9.76e-9/1.83e-9, and gap31.556um within its50um budget.
These are development checks, not spatial/enforcement convergence or acceptance.

Supplemental tests at`be0fa6bf` use the same production wheel: local plastic-branch
owner derivatives and disposable history pass (errors5.03e-8/2.35e-9). The existing
six-resultant associated ellipsoid law, not fibre/J2 plasticity, is exercised.
At declared yield1e-5 and penalty1e6N/m³, three targets.25/.5/.75 accept with
nonzero monotone accumulation; its exact plastic checkpoint restores. Target1
fails at the unchanged50um gap/backtracking gate. Penalty1e7 instead fails at
first-target gap/merit. Both failures preserve the complete accepted mechanical,
shell and material prefix; neither establishes successful full coupled yielding.
Three supplemental checks19.360s/185868288B and one changed restart check17.551s/
185135104B pass. The cumulative35outcomes include that one repeated changed check
(34unique cases). No further fixture tuning or convergence claim.

The separate bounded unload/reload test at`aec4148a` declares targets
.25,.5,.75,0,.25,.5,.75. It completes all7 with nonzero monotone plastic history,
normal storage0 at unloading, exact split restart, normalized supportF/M
4.67e-14/4.36e-14 and maximum penetration41.425um under50um. Its installed
check22.184s185233408B uses the same wheel. The current cumulative36outcomes
cover35unique cases including one changed restart repeat. Peak.75 is explicit;
the target1 and higher-penalty failures above retain their original disposition.
No engineering material, spatial/enforcement or programme acceptance follows.

Historical single owner `46ea65f6`: one strictly interior straight
B3-GE half-cell material patch now couples to one elastic S3 top physical skin
through the existing retained native/shell static owner. All 42 native and 18
shell coordinates remain; moving target normals and offset work are included.
This is implemented and installed-tested development, not engineering acceptance.

Run `python examples/general_contact_native_material_s3.py` in the reconciled
checkout. The example presses, opens and recontacts, reports both body wrenches
about the global origin, normal storage, continuous patch gap and checkpoint.
The experimental modules expose `NativeMaterialS3Patch`,
`NativeRetainedMaterialS3Work` and `NativeRetainedRoundS3Analysis`; public generic
FEModel/native insertion and application admission are unchanged.

`python examples/general_contact_native_material_s3.py --two-beams` uses the
existing public development factory with two independent native beams and one
shared S3. Its separate profile retains all84native+18shell coordinates.
`NativeS3ContactPair` binds each area's work and gap/path limits. Mixed line/area
laws and the separate activation controller reject through factory/direct construction.

The two-beam example declares targets .25,.5,.75,1,0,.25,.5,.75,1. The coarser
.5,1 programme failed at the gap/merit gate. There are no hidden targets or changed
tolerances/caps. Each pair uses its own cell rotation block, radius and path proof.
Area summaries label the measure and return `None` for line-only active intervals.
Old line identities/summaries remain. A checkpoint captured from the prior46ea65f6
wheel replays exactly; cross-profile and changed-gap continuation reject.

## Work, geometry and transactions

For the admitted straight reference,
`x(t,alpha)=(1-t)*p0+t*p1+Uc*R0*rho(alpha)`.
The potential is `0.5*k*integral(min(g,0)^2 dA0)`, with explicit `k` in N/m³ and
fixed reference measure `radius*|reference chord| dt dalpha`. Axial active
integration is analytic; bounded angular Gauss8/16 controls energy, force and
tangent. Anchored trigonometric projection resolves near-extremum arithmetic;
unresolved queried angular boundary/extremum activation rejects before quadrature.
This does not prohibit first touch along a certified path.

S3 corners use the formulation-owned small-rotation map
`x_ref+u+physical_offset*(theta cross reference_director)`. This profile does not
introduce finite-rotation shell directors. The 60-coordinate derivatives include
target-normal changes, both-body blocks and physical section couples. Exactly
one native chart-to-spatial conversion occurs inside the shared area integral.
Reported shell orbital moments use physical corners, avoiding offset double count.

The existing native state owner, shell constraints and checkpoint chain are
reused. Candidate poses require positive reference orientation and whole-patch
rim clearance. The actual exponential native/affine shell trial path includes
material radius in gap and edge lever bounds; source orientation and reference
S3 orientation are certified separately. Bernstein controls conservatively
bound reference-normal positivity across the whole shell path. An unresolved
certificate rejects; safe paths can consequently require subdivision.

Physical commit follows all equilibrium/gap/path checks and checkpoint staging.
Cancellation or exception during staging retains the accepted native/shell prefix.
Definitions, numerical revision and settings bind restart; incompatible continuation
rejects. Both existing friction entry points explicitly reject this normal-area
owner. No friction history, transport or dynamics admission is implied.

## Evidence and remaining limits

Independent direct area quadrature checks energy, force and moment on full/partial
branches. Native finite section rotation, scalar virtual work, complete contact
and assembled-owner tangents, both-body wrench, hidden normal/edge crossings,
hidden reference inversion, rollback, split/open restart and the example pass.
The coupled fixture has nonzero deformable-target response. Normalized global
force/moment defects are about 1.24e-12/1.11e-12; owner directional errors are
2.18e-10/3.73e-10, against unchanged 1e-6/1e-5 development gates.

Explicit penalties 1e6/1e7 N/m³ give gaps 31.093/11.439 micrometres within the
unchanged 50 micrometre fixture budget; reaction changes 2.108%. Enforcement,
pressure/spatial convergence and engineering response acceptance remain open.
The single-owner evidence admits one beam, one S3 top skin and one strictly interior
straight untwisted half-cell patch. Current multiple maps extend this ownership,
not its geometry or material acceptance. Caps, interfaces, curved reference,
patch unions, friction, native dynamics and nonlinear-material
qualification remain required programme work. No free-rim continuum admission.

Historical `c211d4c9` admits two material patches through one shared18-DOF S3.
Coupled gap31.556um under50um, target displacement
norm65.527um; normalized force/moment1.41e-9/1.26e-9 under1e-6. Independent area work,
102-coordinate/owner tangents, second-beam hidden rotation, the actual cycle,
rollback and split/incompatible restart pass. A nearly uniform axial test pose
exhausted angular resolution under unchanged controls. That failure is not regraded
by the nonuniform smooth-branch pass. Robustness, convergence and acceptance remain open.

39 installed checks: 73.466 s, 349569024 B peak process-family memory.
517 package files and 222 imports match source; JIT disabled, numerical pools1.
[Raw identities, review and retained failures](d1_review_support/contact_native_material_s3_20261004/README.md).

Historicalc211 package:32checks135.178s331382784B;517files/217imports match,JIT0/pools1.
The earlier39checks above belong to46ea65f6. Current evidence is summarized above.
