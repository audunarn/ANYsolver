# G3c objective beam-frame successor equation contract

Status: FROZEN_EQUATIONS_REQUIRING_INDEPENDENT_REVIEW; no runtime implementation
or qualification authority until the exact successor receives that review.
Candidate policy: GE_BEAM3_G3C_ANCHOR_DIRECTOR_LOCAL_POTENTIAL_V1.
Base: 10623490e83928d561349072566b9dc2ffbcd325,
tree d8422a3b3feafc19b8bd71e2ca65ecadd3f594f9.

## Exact correction extent

Preserve the G3c blocked record and independent P1 G3C-DR-01. This successor
replaces ONLY the proposed private B2/B3 finite mixed-interface wrapper.
It does not change BeamElement, QuadraticBeamElement, corotational.py, native
GE mechanics, Q4/S3 mechanics/recovery, existing adapters, defaults, aliases,
versions, or earlier evidence. No public legacy behavior is repaired by this
private candidate. Do not claim finite equality to the defective generic
legacy wrapper; require reference-linear equality to the actual local operator.

Retain all five G3c graphs, 25 variants, sections, load/target histories,
nonidentity port frames, negative cases, numerical thresholds and resource
bounds from the parent contract. Q4/S3 still require the separate reviewed
private variational shell map and their complete graph-level verification.
This gate cannot substitute for those adapters, global ownership, G4 or G5.

## Reference and physical variables

Reference nodes X_i are straight, endpoint-midpoint-end for B3, and distinct.
Set L=|X_last-X_first|, a=(X_last-X_first)/L. The explicit physical section
orientation is the existing beam local-z/web direction: project it onto
a-perp to obtain c0, then b0=c0 cross a, A0=[a,b0,c0]. This matches
elements._beam_rotation_matrix exactly. No global-axis fallback, swapped
local-y/local-z interpretation or new roll convention is allowed.

The owner provides current x_i=X_i+u_i and authoritative Q_i.
In its accepted-base chart Q_i(eta_i)=Exp(eta_i) Qaccepted_i.
No Log(Q_i) is formed, no total rotation vector is reconstructed, and rejected
proposals never become anchors. Unrestricted common rigid orientation is held
in Qaccepted; trial increments retain the inherited local cutback policy.

## Selected objective frame: persistent physical anchor

The new private policy takes an explicit immutable anchor_node_id.
For the retained B2 pair element11 use physical node101; in the multifamily
loop B2 element11 also uses101. B3 always uses its midpoint: pair element11
node102, loop element12 node202. These are fixture inputs, not a lookup of the
lowest numeric ID at runtime. Renumber the anchor with its physical node;
connectivity reversal does NOT switch it to the other endpoint. Checkpoint
and definition hashes bind it. This additional convention changes the private
finite deformation model, not the public legacy element. It is not inferred
from legacy parity or described as a mere coordinate implementation fix.

Let Q_A be the authoritative rotation at the immutable physical anchor.
Select R=Q_A, directly. Do NOT constrain R*a to the current chord, perform
a director average/fit, or form an absolute/principal nodal rotation Log.
The complete local potential is evaluated in this material-anchor frame.

This is an explicitly new private finite model, not a different spelling of
the defective generic legacy wrapper. In B2 it carries a distinguished
physical anchor endpoint; changing that endpoint can change finite response.
The anchor is a definition input transported with its physical node. It cannot
be silently selected by current node number, reversal order or solver state.
B3 uses its distinguished physical midpoint. No public B2/B3 definition changes.

Finite proper Q and reference geometry are required. Check all pairwise nodal
relative rotations <0.9*pi, and compute d_rotation_i=Log(Q_A^T Q_i) using
the same inherited bound. Pairwise admission directly implies every required
local Log is admitted because A is one of those nodes. There is no additional
current-chord direction, fit-uniqueness or roll-selection exclusion. Local
constitutive validity is still that of the explicitly reused elastic
von-Karman operators; no assertion of exact finite-strain engineering accuracy
or full legacy-domain parity follows from objectivity alone.

For a common rigid motion Q_i=W and x_i=W X_i+s, R=W and every local d is zero
for arbitrary W, including pi,1.4*pi and any number of accepted turns.
For common motion superposed on deformation, R*=W R and the whole local state
is invariant. No total-rotation-vector branch or accepted-frame drift occurs.

Rejected alternatives are preserved as explicit design witnesses:
(1) principal-log mean: parent DR-01, common pi discontinuity;
(2) one-director mean: unchanged x chord and all Q_i=Rz(-pi/2) projects to zero;
(3) two-director fit: B3 Q_i=Rx(-2pi/3),I,Rx(2pi/3) makes both means zero;
(4) chord-aligned anchor: a=x,Q_A=I,t=Ry(pi/2)a,Q_B=Rx(8pi/9).
Its selected R=Ry(pi/2) gives a local angle above0.9*pi, although
Ry(pi/2)Rx(4pi/9) keeps both angles below0.9*pi. These exclusions are NOT
adopted as extra domain restrictions in the selected direct-anchor map.
For (3), the midpoint anchor is I and local angles are2pi/3; for (4), the
anchor is I and local B2 relative angle8pi/9 remains below0.9*pi.

## Deformation, potential and derivatives

With arithmetic centroids xc and Xc:
d_translation_i = R^T (x_i-xc) - (X_i-Xc),
d_rotation_i = Log(R^T Q_i).
These d components are in the original reference-global coordinates, so the
unchanged element's own local section transform applies exactly once.

Call the exact B2 or B3 local compute_nonlinear_response with history-free
scalar elastic sections and geometric_nonlinearity='von_karman'. Do NOT call
generic corotational_element_response or B2's separate corotational method.
Use an owned isolated immutable definition/cache and virgin elastic state.
Require actual local force f and tangent K, not a cached reference K*d.
If a supported local family is not conservative, do not manufacture a
potential: record the contradiction and block this selected variational route.

For z=(all u_i, eta_i), d=d(z), D=partial d/partial z:
g = D^T f,
H = D^T K D + sum_j f_j Hessian(d_j).
This is the first and second variation of the local elastic potential
Pi_local(d(z)), including ALL frame, normalization, Log and Exp terms.
Never symmetrize H after assembly or rotate f forward instead of pulling back.

Analytic derivative primitives: matrix products and centroid subtraction use
both first and mixed second product-rule terms. R is exactly the anchor's
Exp(eta_A)Qaccepted_A, differentiated jointly with all translations and nodal
rotations. No derivative of R is omitted when the anchor also receives a
joint or support residual. Exp and relative Log use the bound analytic
first/second maps, including their small-angle series. Second-order automatic
differentiation is permitted; numerical frame differentiation is not.
Independent checks reconstruct values without candidate helpers and verify
directional first/second derivatives at EACH inherited h, not the best h.

For spatial wrench output P=blockdiag(I,Jleft(eta_i)), solve P^T r=g.
Its spatial-row/chart-column derivative solves
P^T J=H-(dP)^T r. At eta=0, H is NOT automatically the derivative of spatial
wrench under composed increments; retain the connection correction.
The graph assembles chart covectors/Hessians and work-dual constraints.
No finite additive rotation slot is identified with a spatial moment.

## Objectivity, reference limit and reversal proofs

For common rigid motion x*=W*x+s, Q*=W*Q, with X,A0 fixed:
R*=Q_A*=W Q_A=W R, hence d*=d. This includes pi,1.4*pi and antiparallel
current/reference chords. Loads/supports use the parent left-action rule,
not coordinate re-expression. The formulation does not align to that chord.

For global coordinates changed by W,s, transform X,x,A0, material directions
and the anchor physical identity; Q*=W Q W^T, R*=W R W^T.
Thus d transforms by W and forces by the work-dual map.

Reversal permutes endpoints (B3 midpoint fixed), while Q_A and R are unchanged
because the physical anchor follows its node. Reorder nodal d/f/K. The physical
local-z direction c0 stays fixed; a and b0=c0 cross a reverse. Local section
axes transform diag(-1,-1,1), not a physical roll change. Preserve scalar Iy/Iz
along their physical axes and verify actual local force/stiffness/recovery
covariance. Switching the anchor defines a different finite model, so tests
must separately detect/reject an unapproved anchor mutation. Geometric
end-exchange with a different material-anchor definition is not conflated
with connectivity re-expression of one fixed definition.

At reference, d=0 and D removes only one infinitesimal common rigid translation
and rotation. Write D=I-B A with B the analytical six-column rigid basis.
The actual local K0 must satisfy K0 B=0 and B^T K0=0. Consequently
D^T K0 D=K0; the force-weighted Hessian term is zero at virgin reference.
Verify these equalities using actual B2 and B3 operators, not assumed symmetry.
Also check rank, all six rigid modes, component work and nonzero prestress terms.

## State, loads and recovery boundary

This local gate cannot accept/commit any analysis state, issue restart evidence,
or mutate a supplied origin. Every evaluation returns detached immutable d,
frame, derivatives and actual local recovery/provenance. The later global owner
must prepare every family before publication and retain the parent token,
cancellation, cache, lock, tamper and accepted-prefix replay requirements.

Acceptance rebases eta to zero with Qaccepted:=Qtrial; it does not alter X,A0,
local elastic potential, or reconstruct Q from stored additive slots.
History-free local d is reconstructed from accepted physical pose.
G4 history adapters require separately derived objective state transforms.

Nodal spatial dead forces use the graph's declared work policy. No new nodal
couple/distributed-load API is introduced. Physical station resultants come from
the unchanged local family evaluation, transformed with R/reference triads;
interface work and numerical shell drilling remain separate from section data.

## Required ordered evidence and limits

1. Independent equation/domain review and hash-bound source/fixture freeze.
2. Local kinematic smoke for BOTH B2 and B3. Retain DR-01 initial twists
   [-d,d] and [-2d,d,d], d=pi/10000, before and after common pi.
   Include common pi,1.4*pi, arbitrary-axis rotations, 90-degree transverse
   director/chord case and both rejected-fit counterexamples, proper global re-expression and endpoint reversal.
3. Actual local operator reference equality, finite work, force/Hessian checks,
   nonlinear local strain/resultants, mixed bend/twist, anisotropic scalar
   section, chart-rebase equality, pairwise/local-relative-log rejection.
4. Independent implementation review; only then resume the complete retained
   G3c positive graph/state/restart funnel. A local smoke is NOT all G3c.

No automatic retries. One numerical thread, 24 GiB/tree, 600 sec/child,
120 sec without CPU/output progress, <=3 children, <=1800 sec/wave.
Keep partial logs externally and no canonical partial output. Rehearsal then
two deterministic formal cycles occur only after the entire graph candidate
is frozen; do not rerun accepted G3a/G3b evidence.

Before independent acceptance this document is design-only. Retain the source
P1 record; a new accepted private policy may supersede its proposed-route use,
never erase or reclassify the public inherited defect. No gate is complete
until its full required evidence exists.
