# Native beams and multiple S3 patches at one midpoint — development

Status: **implemented but unverified**. No numerical execution, solver import,
pytest, build or install has been authorised for this new fixture. Prior
single-pair evidence and its consumed allowance do not qualify this route.

## Entry and admission

`create_native_transient_multi_shell_analysis` and
`solve_native_transient_multi_shell` use the exact selector
`ge_beam3_native_multi_s3_small_motion_transient_dev` and profile
`NATIVE_MULTI_B3_GE_S3_SMALL_MOTION_DESCRIPTOR_MIDPOINT_DEV_V1`.
Frozen `NativeContactBody`, `S3ContactBody` and `NativeTransientS3ContactPair`
records bind stable body/element IDs. The existing static `NativeS3ContactPair`
record and every older selector/owner retain their identity.

Native elements within a body share actual nodes and must form a connected
reference graph. Distinct native bodies have disjoint node IDs; native element
IDs are globally unique. Each shell body owns one distinct exact `FEModel`.
Shell node/element numbers may repeat across distinct bodies. Duplicate body IDs,
pairs, model aliases, unused structural nodes and overlapping/nonmanifold triangles
are refused. Inputs sort canonically by body and pair identity.

The admitted native geometry is straight, centered, elastic and has exact zero
half-cell lifts, positive diagonal physical inertia and the existing retained
SO3 mechanics. Shell bodies consist entirely of exact elastic S3 V2D triangles,
with actual translation-only formulation mass, centered reference offset, planar
reference geometry, a common positive director and top physical offset within
each body. The explicit chart limits bound nodal translation and rotation;
rotation is at most .05 rad. No supports, applied loads, point masses or activity
maps are admitted. Contact is frictionless round-line penalty with explicit
radius (m), line stiffness (N/m²), boundary clearance (m) and geometry controls.
Penetration is strictly smaller than the radius.

Every selected pair represents both complete native half-cells against one
physical offset triangle. The whole line must remain strictly inside that face.
Exterior edges retain `PHYSICAL_EXTERIOR_RIM` identity. Shared mesh edges retain
`UNADMITTED_PATCH_TRANSITION_BAND` identity; they are not physical rims.
Neither kind produces an edge force. Kernel boundary refusal is reported as
`UNADMITTED_SELECTED_PATCH_BOUNDARY` with the complete selected-face edge
inventory, since that kernel does not identify the nearest failing edge.
Feature-union contact and crossing between neighbouring faces remain open.
Pairs are explicit interaction selections; unselected interactions are not
claimed to have been searched. Repeated contacts on a beam/target share the
same authoritative coordinates.

## Global descriptor and mechanics

With Nb unique native nodes, Eb native elements and Ns shell nodes across bodies,
the full field size is `6Nb + 24Eb + 6Ns`, physical size `3Nb + 6Eb + 3Ns`,
and algebraic size `3Nb + 18Eb + 3Ns`. Cheap authoritative-count preflight rejects
more than the existing512-coordinate cap before dense shell allocation or native
preparation. Exact maps subsequently confirm that count.

The state contains complete native positions/low parts, nodal algebraic frames,
physical cell rotations,18 retained resultants per native element and one
concatenated shell displacement vector. All native internal coordinates retain
the existing exact length/slice. Shell nodal translations are physical; its
rotations are algebraic. Zero rotational rate/acceleration slots are non-inertial
placeholders and do not describe skin material velocity.

All structural shell triangles, including unselected faces, assemble K and M
ONCE into their body's shared nodal vector using actual DOF slots. Shared vertices
and all triangle mass contributions are retained once. Shell physical momentum
is gathered by node DOF identity, including permuted insertion order; angular
momentum uses actual translated midsurface coordinates about global zero.

A contact contributor maps native42 plus body-global shell DOFs into the ONE
assembly. It adds both residuals and all crossblocks. The native own block receives
the existing spatial-work Jacobian conversion before the common midpoint chart.
No local condensation, child stepper, lagged force, trace inertia, damping or
restitution is added. The contributor interface is additive; mixed beam–beam
and beam–shell integration through this owner remains a future programme row.

The existing `_RetainedMidpointAssembly` and `_solve_retained_transient` own
stage/endpoint equilibrium, Newton control, transactions and journals. Native
physical positions/cell rotations use the existing half-stage chart and Exp
maps; native algebraic nodal rotations use the existing full chart. Shell stage
translations are half physical increments, shell algebraic rotations are full
increments. Endpoint rotational consistency solves at fixed physical endpoint.
All shell structural faces revalidate side/area, including unselected faces.

The swept path has two shell affine legs through the ACTUAL shared stage and
projected endpoint, coupled to native affine zero-lift geometry/Exp rotations.
The existing exact Bernstein signed-height/rim certificate covers every selected
pair, including both uniform arithmetic envelopes (sample-to-exact and
exact-to-rounded-family). Unselected structural faces also certify orientation
along both legs. Clear sampled states alone do not certify the interior path.
Unresolved motion fails/cuts back within existing finite controller limits.
Direct fresh initialization and restore rerun chart, side/area and pair admission.

Energy records separate native elastic, shell elastic, contact regularization
storage and kinetic energy. Total is their sum; no exact energy conservation or
impact/temporal qualification is claimed. Pair forces are negative potential
gradients; assembly residuals are positive internal potential gradients. Moments
refer to `(0,0,0)` m. Stage work uses the actual accepted shell increment,
including endpoint algebraic projection.

## Aggregate resources and error chart

Explicit1..4096 caps bound geometry evaluations, recursive integration visits
and swept intervals over ONE atomic owner operation, all contributors and both
path legs. Repeated evaluation/path checks debit the same operation purse. A
standalone internal assembly uses one complete-assembly purse. No per-pair
renewal occurs. Private defaultNone hooks only debit geometry/integration before
work; historical kernel fingerprints/equations/results remain unchanged.
All failed visited work is retained in `last_operation_work` or exception fields.
A long replay may exceed declared resource admission; that failure is distinct
from corrupted physical history. Numerical process/resource authority is separate.

Kernel error estimates are componentwise in27 physical sample coordinates in
metres. For admitted zero-lift geometry the sample map is affine, has zero
geometric curvature and zero native rotational contact components. Shell offset
rotation columns are included. Define frozen positive L as the minimum native
end-to-end reference length. The global dimensioned chart uses translations in
metres and rotational coordinates `L*theta`; force scale F is in N, moment scale
`L*F` is in Nm, and tangent scale K is in N/m.

Both maximum row and column absolute sums of the full dimensioned sample map are
bounded by `B=max(4,1+2*abs(offset)/L)`. Boolean scatter within a contributor is
isometric; shell offset mapping is not. Thus the Euclidean map norm is at most B.
Componentwise gradient/Hessian errors convert to Euclidean/operator bounds using
`sqrt(27)`/27. Each pair reserves global E/count, F/(count*sqrt27*B),
K/(count*27*B²), rounded downward. Actual errors are transformed with outward
rounding and summed exactly/rationally then outward rounded for FINAL unchanged
global E/F/K gates. Under this exact admission no geometric-curvature or contact
spatial-rotation correction term remains; the prepared map/curvature selector
checks that premise. No curved-map guarantee is implied. These are quadrature
estimators, not independent continuum-error qualification.

## Prepared verification and separate execution proposal

The example builds FOUR native beams and TWO shell bodies. Body7 has two triangles
sharing four nodes; two beams load its first face and a third its second face.
Body8 has one triangle and a fourth beam. One210-coordinate system has81 physical
and129 algebraic coordinates. The fixture uses the already explicit stable SO3
and precise-work arithmetic option,2 steps of .003 s and a .006 s horizon.

Ten focused selectors are prepared (no pass claims):

1. Actual shared-node structural/mass assembly once and no-contact independent sums.
2. Full210 common-stage derivative/work at two original perturbations, shell rotation and both crossblocks.
3. Actual dimensioned row/column bounds, zero curvature and final aggregate error gates.
4. Public coupled trajectory, all selected pairs, both target responses and both path legs.
5. Genuine full2 = fresh1+1 restart/bytes and authenticated translation/work tamper refusal.
6. Aggregate geometry/integration/two-leg exhaustion, rollback and exact consumed counts.
7. Internal/exterior edge refusal and actual skin orientation/chart admission.
8. Topology/alias/duplicate/mutation/preallocation refusal.
9. Cancellation/path rollback and multiple targets sharing one native42 map.
10. DefaultNone historical line-S3 result/identity compatibility (same helper selector also checks optional ledger).

Scientific targets remain1e-5 tangent/work,1e-11 stage/endpoint equilibrium,
1e-6 normalized pair force/moment balance (separate frozen5 N/5 Nm response references) and explicit global1e-8 J/1e-7 N/1e-6 N/m
error controls. No criteria are relaxed to obtain a pass.

Propose a separately authorised **600 measured seconds**, including private
build/install, these checks, changed-kernel single-owner compatibility, public
CLI and scoped repairs; one process tree≤60 s,953 MiB, protected60 s reserve,
JIT disabled/Numba1/observed pools1 and all private import hashes checked.
This is an estimate, NOT a grant or a measured runtime claim. Build≤25 s,
install≤10 s; short source/oracle/refusal groups≤55 s; full derivative≤55 s;
actual trajectory≤55 s; CLI≤55 s. Restart's three fresh trajectories should
use authentic immutable prefix/full/resumed artifacts in separate≤55 s jobs
followed by exact byte/chain and tamper checks; no omitted solve or fake result.
Operation resource admission remains frozen and separate from process caps.
If an assigned check cannot fit, preserve its failure/partial evidence and report
that unmet gate. Do not pool any historical allowance.

Broad finite shell rotation, true shell patch-union/physical rim enforcement,
curved native geometry, friction, arbitrary topology, general collision discovery,
mixed native-pair contributors and independent engineering acceptance remain open.

## Pending measured harness

Raw `native_multi_shell_run_v3.py` and `native_multi_shell_pending_manifest_v3.json`
freeze the new source/build inputs and15 proposed groups. Approved seconds are0;
child dispatch fails closed. Runner was syntax inspected, never invoked. Future
private paths are `native_multi_shell_dist_v1`, `native_multi_shell_site_v1` and
`native_multi_shell_wheel_identity_v1.json` in the new raw root.

Restart producer groups write authentic final public payload/capsule to unique
`nms8_restart_prefix_v1`, `nms8_restart_full_v1`, `nms8_restart_resumed_v1`
attempt directories. The resumed input must first enter an immutable manifest
revision. A post-producer stdlib binder must validate exact product/wheel/source,
commands/settings, private-runtime/resource terminal outcomes, predecessor chain
and all artifact hashes, then bind the three results/capsules and producer evidence
into a new manifest and `NMS8_RESTART_REPLAY`/binding digest. This binder remains
**unimplemented preparation work**; the verification group refuses dispatch
without that raw binding. Ordinary pytest continues to perform three fresh solves.
No saved record can establish a new solve or erase a failed attempt.
