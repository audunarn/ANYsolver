# Early native/multiple-S3 design checkpoint — SOURCE ONLY

Root: C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001; clean fc608387.
Old single-pair source/evidence/defaults stay protected; no imports or jobs.

## Actual assembly boundary and obstruction

_RetainedMidpointAssembly already assembles native shared nodes/frames once and
keeps each native element's physical cell rotations and18 retained resultants.
Its explicit subclass admission hooks can accept disjoint native bodies while
legacy ConnectedDynamicAnalysis keeps its existing connected graph guard.
The current shell owner has hard-coded42+18 maps, one shell K/M and one contact.
These cannot be multiplied into independent child owners: shared S3 nodes and
mass would be duplicated. The new owner will extend the SAME midpoint/endpoint/
transaction/trajectory services with one global shell vector and structural sum.

Let N_b be unique native nodes, E_b native elements, N_s unique shell nodes across
explicit distinct shell bodies. Full coordinates=6N_b+24E_b+6N_s; physical=
3N_b+6E_b+3N_s; algebraic=3N_b+18E_b+3N_s. Native local42 maps are the existing
Boolean maps. Shell body DOF slots append one authoritative vector per FEModel;
local element18 K/M scatter through actual formulation node DOFs and are assembled
ONCE per structural element, including unselected structural triangles. Contact
W9 uses the existing skin adapter's global body DOFs. A pair local map scatters
native42+bodyDOFs residual/Hessian into this same full global system. Preserve
native own-block spatial-work conversion and BOTH native/shell cross blocks
before the one global midpoint chart. No independent steppers or condensation.

## Proposed explicit API/profile

Frozen records NativeContactBody(body_id,definitions tuple),
S3ContactBody(body_id,model), and NativeS3ContactPair(native_body_id,
native_element_id,shell_body_id,shell_element_id). Canonical sorting by IDs gives
stable layout; duplicate pairs/body IDs/FEModel aliases and cross-body shared
native node IDs are refused. Several pairs can share the same beam or target:
all refer to the same captured native map/body vector, never copied bodies.
Factory accepts explicit shared dimensioned normal controls and aggregate limits.
Selector ge_beam3_native_multi_s3_small_motion_transient_dev; profile
NATIVE_MULTI_B3_GE_S3_SMALL_MOTION_DESCRIPTOR_MIDPOINT_DEV_V1. Existing selectors,
profiles, guards and identities remain unchanged. Root owns public exports.

S3 bodies may contain multiple exact elastic V2D triangles with shared nodes.
All structural nodes must be represented and every element contributes once.
Initial bounded admission: planar top/+polarity, common director/offset within a
body, no overlapping triangle interiors, edge multiplicity<=2, no supports/loads.
Physical exterior edges are labelled separately from shared internal edges.
The existing interior kernel excludes every selected triangle edge by a strict
feature band; on shared edges this is an UNADMITTED_PATCH_TRANSITION_BAND, not a
physical rim or edge force. All whole native half-curves must remain in their
selected face interiors. A crossing/unresolved or duplicate selection is refused,
not switched, dropped or summed twice. Broader feature-union contact stays open.

## Aggregate resource and restart proposal

One contact-work ledger per atomic owner operation (ephemeral one-call ledger for
standalone whole-assembly evaluation) charges EVERY pair geometry and recursive
integration visit before work. One shared swept visited count covers BOTH actual
legs across ALL pairs, including repeated path checks within that operation.
Declared operation geometry/integration/swept caps never renew per pair.
Restore of a long prefix must fit the same explicit finite caps or refuse.
Report deterministic per-path deltas, not operation-dependent accumulated totals,
so accepted records reproduce exactly during replay. Failures expose actual
ledger counts. Global E/F/K error gates use conservatively reserved per-pair
shares plus whole-aggregate final accounting; no local tolerance multiplied by
pair count. Native/shell/contact energy partitions and full state maps remain
explicit. Endpoint shell rotations are algebraic and affect both actual skin legs.

Concrete reserved ownership request: minimal OPTIONAL private work-budget hooks
in existing general_contact/native_retained_line_s3.py and
native_retained_line_s3_work.py are needed to debit geometry and recursive visits
BEFORE they occur; results currently expose accepted intervals, not all visits.
Default None path must keep old signatures' behavior/fingerprints/results intact.
No quadrature, law, tolerance or kernel algorithm change is proposed.
The new owner creates/passes the ledger; no callback restart or hidden mode.

## Finite fixtures and remaining work

Main candidate:4 independent native beams,2 S3 bodies; first body has2 triangles
sharing an edge (4 unique nodes), second body1 triangle (3 nodes). Three beams
contact the first body's two patches, including2 beams on ONE common face;
fourth beam contacts the second body. Total210 retained coords,81 physical,129
algebraic. This discriminates shared-target structural coupling and multiple
patch/body assembly. Additional source fixture shares one beam with two distinct
target-body selections to verify one native map, without claiming overlapping
same-body face contact or patch-edge transitions. No selected-cell-only route.

Prepare10-12 focused tests: body/element mass inventory/shared DOFs; complete
work/tangent/cross blocks; no-contact independent sums; actual coupled trajectory;
genuine checkpointed continuation/tamper; cancellation/rollback/mutation; strict
shared-edge feature refusal; topology/overlap/alias refusal; global operation/
path budget exhaustion; existing single-owner compatibility. All numerical tests
remain UNEXECUTED. Next: adopt reserved API/admission/resource/kernel-hook delta,
implement new owner/factory/fixture/tests/guide, AST/hash/snapshot handoff and a
separate measured execution proposal. No old480-second authority is available
for this new fixture.
