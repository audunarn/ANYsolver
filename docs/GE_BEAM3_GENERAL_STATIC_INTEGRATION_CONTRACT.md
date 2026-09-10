# GE-B3 general static integration contract v1

Status: **FROZEN_DESIGN_NOT_IMPLEMENTED_OR_QUALIFIED**.
Contract ID: `GE_BEAM3_GENERAL_STATIC_INTEGRATION_V1`.

This freezes the next development interface, not a new formulation or a
qualification result. The companion canonical JSON binds this document, its
auditor/tests, the parity matrix and the source baseline. Changing these rules
requires a successor contract and an explicit impact review before execution.

## 1. Authority and scope

Parent is parity commit `8808886f2394450a606a2e5972ac8f4e64b17a1f`, tree
`321c5155befdcac010a39a43e35528e4aa429cc8`. Runtime baseline is released 0.4.3,
commit `74703a3202251edc0beafb21cd31f52c9304ceb8`, tree
`64a18a8fe137946ec2f0d4841821a19066a2707f`.

The target is integration of the accepted **native current core**, not the
older straight `ge-beam3` facade. Preserve all element/formulation/state IDs,
qualified Q4/S3 mechanics, legacy B2/B3, public selectors and defaults. Existing
`production_qualified=False` fields are not switches to flip. Acceptance of
`GE_BEAM3_NATIVE_OWNED_WORKFLOWS_V1` remains scoped to its existing artifacts.

Primary parity rows: P01, P04, P07, P08, P09, P10, P17, P18, P20. Related load,
material and recovery obligations: P05, P06, P11, P15, P16, P19, P28, P29.
This contract is not closure of those rows. U01-U10 remain distinguished from
genuine GE gaps; in particular B3 generalized-section/corotational rejection,
legacy zero internal-force placeholder and minimal `to_dict` are not behaviors
to reproduce as successful GE capabilities.

General static target: frozen model graphs, native shared nodes, standard
elastic section adapters, force/displacement control, constraints and reactions,
consistent assembly, global transactions, and authenticated restart. Each gate
admits only its explicitly tested subset. Mixed beam/legacy/shell graphs and
history-bearing section families remain required subsequent integration gates,
not capabilities inferred from this document or from two-element tests.

No dynamics, contact/activity, general plastic shell joints, new load laws,
ecosystem routing, default activation, release, or wholesale removal of owned
workflow bounds is authorized here. Static handling must preserve information
needed by later dynamic parity rather than precluding it.

## 2. State ownership and transaction protocol

One analysis owner owns the frozen graph, DOF ordering, translations, shared
nodal SO(3) operators, constraint chart, accepted load/control state and epoch.
There is exactly one physical rotation operator per native node, including
junctions with different incident element rolls. An element's reference triads
remain element-owned: its physical directors are the shared operator times its
own reference triads. Never average incident triads or overwrite material roll.

Global additive rotation slots are legacy-compatible chart bookkeeping, not
accumulated physical rotations. Match the existing committed-base rule:
`Q_trial = Exp(theta_trial - theta_committed) Q_committed`. Derive residual and
tangent pullbacks through that chart, including the Exp Jacobian and its
derivative. A spatial moment is work-conjugate to spatial virtual rotation, not
automatically to a finite chart increment. Never use `Exp(total_theta)` as the
authoritative rotation or compose successive rejected line-search proposals.

Each element owns 24 internal stationary variables, its local station histories,
and immutable reference/section definitions. Only the analysis owner can accept
their issued candidate state. No element-local commit, hidden mutable material
singleton, recovery-induced commit, or private nested owner competing with the
global owner is allowed. Reuse the native validation/context protocol through
an adapter; do not bypass issued tokens or reseal detached state.

Transaction states are `COMMITTED -> TRIAL -> PREPARED -> COMMITTED`, with
`TRIAL/PREPARED -> DISCARDED` leaving the prior committed snapshot unchanged.

1. Begin from an immutable accepted snapshot and issue a token binding owner,
   graph fingerprint, committed epoch/hash and trial sequence.
2. Build shared trial kinematics once. Every incident element receives a view
   of that same token and those same rotations/positions.
3. Repeated evaluation is pure relative to the accepted state. A warm internal
   iterate may accelerate a solve but cannot become a constitutive origin.
4. After global convergence, prepare all elements, material histories,
   constraints and loads. Validate exact accepted-displacement/pose linkage,
   local equilibrium, provenance and expected epoch before any publication.
5. Publish one new immutable global snapshot. If any preparation fails, commit
   none. Stale/replayed/foreign tokens and concurrent writes fail closed.
6. Line-search rejection, cutback, cancellation and exceptions discard trial
   state and trial caches. Preserve a genuine accepted prefix for recovery.

Graph/section/constraint mutation invalidates the owner; construct a new model.
Cache keys include formulation, definition, graph, section fingerprint,
constraint chart, committed epoch, trial identity and tangent/load policy.
Multiple RHS may share a factor only for the identical operator and state;
independent load histories never share mutable state.

## 3. Constraints, MPCs and mixed-family interfaces

Freeze three explicit constraint kinds; no automatic coercion between them:

- `AFFINE_TRANSLATION`: `u = T z + u_bar(lambda)` for translational DOFs and
  explicitly compatible legacy-only blocks. Resolve nested affine MPCs in a
  deterministic acyclic order. Reject cycles, duplicate dependent DOFs,
  contradictory prescriptions, nonfinite coefficients and rank deficiency.
- `ORIENTATION_SUPPORT`: prescribed full or partial physical orientation.
  With physical director frame D, prescribed target D*, and fixed orthonormal
  columns B in the target frame, use `g = B^T Log(D*^T D) = 0`.
  B has 1, 2 or 3 columns; full support uses identity. Target frames and axes
  are explicit physical inputs. This is not an Euler-angle or additive-slot
  clamp; a legacy component restraint needs an explicit migration decision.
- `RELATIVE_POSE`: objective rigid connections, with declared material offset
  a and relative frame C: `x_s = x_m + D_m a`, `D_s = D_m C`.
  Partial relative orientation uses the same selected-log-component definition
  in the master-relative target frame. Translation-only ties are admitted
  separately and do not imply a rotational tie.

For orientation charts, relative angle must be strictly below `0.9*pi`;
otherwise issue typed cutback/refinement, with no hidden branch switch. Common
rigid rotation is unrestricted. Transform target frames/axes with the physical
model in objectivity tests. Prescribed histories are explicit SO(3) target
frames at load points, not silently interpolated accumulated rotation vectors.

Orientation/pose constraints use a multiplier residual and analytic first and
second derivatives in the current chart. For a conservative potential the
Newton block is `[K + sum(mu_i Hess(g_i)), J_g^T; J_g, 0]`; include prescribed
motion derivatives in control equations. Do not apply an affine transformation
alone to finite rotational MPCs. Keep the distinction between a spatial tangent
and a chart Hessian; symmetry is required only of the correctly pulled-back
conservative Hessian. Nonconservative residuals require their actual derivative.

Recover reactions from unreduced equilibrium with declared sign convention
`internal - applied + constraint = 0`; report support force/moment on the body
as minus the assembled constraint term. Account for prescribed-motion work and
eccentric force moments exactly once. Verify virtual work and action-reaction,
not only converged displacement. Numerical shell drill reactions remain separate
from physical section resultants.

At native/legacy/shell shared rotations, generic DOF equality is not sufficient.
Require a qualified common-pose adapter, its work-dual map and geometric tangent;
otherwise reject the mixed rotational junction before evaluation. The existing
one-shell elastic V2 joint is evidence for that subset only. Never fall back to
legacy mechanics. Native-only branches/junctions and translation-only mixed
ties have their own tests before the general mixed-graph gate.

## 4. Section adapters and recovery

Freeze order `[eps_x,gamma_xy,gamma_xz,kappa_x,kappa_y,kappa_z]` and
`[N,V_y,V_z,T,M_y,M_z]`. Section coefficients are in physical material axes,
including reference location/eccentricity. If `e' = A e`, use work-dual
`s = A^T s'` and `C = A^T C' A`; derive A from the actual frame/reference-line
map and test both energy and resultants. No duplicated eccentricity transform.

First implementation gate admits exact linear elastic adapters only:

- Isotropic section: map explicit positive E, G, area, Iy, Iz, J and directional
  shear factors to the documented axial/shear/torsion/bending stiffness, with
  the existing beam-axis convention verified by independent unit modes.
- External `GeneralizedBeamSectionContract`: snapshot the validated SPD 6x6
  matrix and stable serializable definition/fingerprint at capture. Retain
  existing validation semantics; do not modify global section tolerances.
  A changing external object or an unidentifiable restart definition is rejected.

The constitutive law is exactly `s=C e`, `psi=e^T C e/2`, tangent C and empty
history. A large artificial yield limit is not an elastic adapter. If the
current native kernel cannot express this law without a core change, stop that
implementation gate and propose a separately reviewed exact adapter extension;
do not modify the frozen core or substitute a nearly elastic law.

Subsequent section integration admits existing ellipsoidal and physical-fibre
laws under their exact identities, with station-owned trial/commit/discard.
Different element families may coexist only after mixed-family transactions
pass; material and section histories cannot be shared by instance identity.
Active plastic tangents need not be SPD. Preserve the algorithmic accepted
origin and loading/unloading/reversal history; never rebuild plastic state from
final strain alone. Initial-field adapters and arbitrary legacy material laws
remain gaps until their own native semantics and tests are frozen.

Recovery uses accepted internal coordinates and the same section state that
formed equilibrium. Expose native strain/resultants, frame and provenance.
Fibre stresses/utilization are available only from a supplying physical law;
do not infer them from a general 6x6 resultant law. Retain optional section
inertia metadata without inventing static-only inertia or claiming dynamics.

## 5. Internal variables and global assembly

Per element retain external q (18) and internal a (24: 18 resultants plus six
physical cell rotations). They are not 24 dispensable numerical modes. Form
the actual residual blocks including internal external-load work. With
`r=(r_q,r_a)` and tangent blocks H, elimination is

`K_c = H_qq - H_qa solve(H_aa,H_aq)`

`r_c = r_q - H_qa solve(H_aa,r_a)`

`delta_a = -solve(H_aa,r_a + H_aq delta_q)`.

These are Newton elimination identities at the same trial state. At converged
internal equilibrium r_a vanishes to its frozen native acceptance criterion;
never discard its correction prematurely or commit unconverged local history.
Use reusable factorizations, not explicit inverses. H_aa may be indefinite;
do not assume Cholesky applicability. Singular/unhealthy solves produce typed
cutback/failure, not pseudoinverse, artificial stiffness or legacy fallback.
Retain existing kernel conditioning/convergence guards; new scaling criteria
need a successor numerical policy, not ad hoc relaxation during tests.

Assembly must preserve graph DOF maps, analytical chart/constraint pullbacks,
load measures, internal load condensation, and accepted state ownership. Static
and nonlinear drivers must call the true residual/tangent interface, not the
legacy `compute_internal_forces` zero placeholder. Compare full stationary and
condensed constrained solves, including nonzero r_a and internal loads.

Store internal rotations/resultants and material origins for recovery/restart.
Static Schur elimination is never permission to replace physical cell inertia
in modal/transient problems. No mass implementation occurs in this step.

## 6. Restart and persistence

Introduce a versioned integration envelope, distinct from element definition,
ordinary mesh serialization and every existing owned-workflow checkpoint.
Required content groups are frozen in the canonical contract. Store graph and
ordered IDs; exact native definitions/formulation IDs; physical reference triads;
section law/schema/parameters; constraint kinds, axes/offsets/targets and order;
load/control history; accepted translations/chart coordinates/shared Q; element
internal variables and station origins/history; epoch/hash chain; solver/chart/
quadrature policies; and runtime/source/acceptance provenance.

Only complete COMMITTED snapshots may be published. Serialize canonically,
reject duplicate keys, nonfinite/overflow values, unexpected keys, bad shapes,
unknown IDs, missing history, and stale or altered definitions. Never pickle or
import a class named by input. A self-hash detects corruption but is not external
authority: require the caller's expected digest and authenticated source/history.
Write exclusively to a same-volume staging path, validate complete bytes, then
atomically publish. A failed write leaves the previous accepted checkpoint
usable; partial data is diagnostic only.

Restore a fresh owner only after graph/section/constraint/load identity checks
and authenticated replay of the accepted history. Verify recovered internal
stationarity, actual accepted pose and material origin, and continuation
equivalence. Preserve existing checkpoint byte/owner limits; a larger graph
needs a separately tested bounded envelope, not silently widened old schemas.
Direct state restoration without replay is deferred until independently proven;
replay may not manufacture an absent or failed accepted step.

Missing-ID historical B2/B3 records remain legacy with a diagnostic. Reject hot
restart across formulations, section families, incompatible runtime policies or
definition edits. New-integration import of old native checkpoints requires an
explicit verified migration adapter; until then reject rather than reseal.
Failed/cancelled analyses export only their genuine accepted prefix.

## 7. Required gates and test IDs

These are preregistered obligations, **not assertions that tests already exist
or passed**. The frozen parity inventory supplies actual legacy/native test
pointers. G0 is the present document/schema audit; later gates require separate
candidate/test/fixture hashes and independent review before formal execution.

| ID | Gate | Required check / independent comparison |
|---|---|---|
| S01 | G1 | Two native beams sharing a node; one issued Q, different reference rolls |
| S02 | G1 | Rejected/noncommuting trial sequence equals fresh committed-base evaluation |
| S03 | G1 | Inject preparation failure in second element: no partial commit |
| S04 | G1 | Stale/foreign/replayed token and concurrent writer rejection |
| S05 | G1 | Isotropic six unit modes and fully coupled SPD section work |
| S06 | G1 | Full 42-variable versus Schur response, nonzero internal residual/load |
| S07 | G1 | Two-element elastic static assembly, true residual and accepted recovery |
| S08 | G1 | Elastic checkpoint continuation and atomic-write failure |
| S09 | G2 | Nonzero translations, nested/multimaster affine MPC, cycle/conflict rejection |
| S10 | G2 | One/two/three orientation constraints; unconstrained rotations remain free |
| S11 | G2 | Prescribed noncommuting orientation, chart cutback, unrestricted common rotation |
| S12 | G2 | Eccentric relative pose: Jacobian, curvature, force/moment reaction work |
| S13 | G2 | Constrained Newton and full multiplier solve agree; constraint rank guards |
| S14 | G2 | Common rigid transform, node permutation and reversal covariance |
| S15 | G3 | Branch/cycle native graph, disjoint IDs, deterministic sparse ordering |
| S16 | G3 | Mixed translation ties; reject unsupported shared rotational adapters |
| S17 | G3 | Qualified common-pose beam/B2/B3/Q4/S3 adapters: work and reaction checks |
| S18 | G3 | Cache invalidation, multiple RHS isolation and immutable graph checks |
| S19 | G4 | Mixed elastic/ellipsoid/fibre station ownership and rollback |
| S20 | G4 | Load/unload/reverse, algorithmic origin and final-state replay |
| S21 | G4 | Newton, line search, cutback, cancellation and control-path continuation |
| S22 | G4 | Restart tamper: graph, Q, section, constraint, load, internal state, provenance |
| S23 | G4 | Reject legacy/cross-family/unknown-schema restart and missing accepted history |
| S24 | G4 | Recovered work/resultants match accepted state; no invented fibre stresses |
| S25 | G5 | Actual legacy routes/regressions, not only synthetic springs; unsupported cases distinct |
| S26 | G5 | Installed-wheel isolation, native provenance, unchanged aliases/core/defaults |

G1 is the next implementation slice: shared transaction/static adapter with a
two-element elastic graph, complete support triples, existing admitted loads
and restart. G2 adds constraints, G3 general/mixed graphs, G4 history-bearing
adapters/solver continuation, G5 integration closure. Partial gates do not close
the general-static parity claim; failed G1 does not authorize skipping to G2.

Reference comparisons must be independently assembled from source equations or
existing frozen native results for the identical definitions, not cached
candidate matrices. Do not require GE and legacy element matrices to coincide.
For invariant/work/covariance/Schur checks require normalized error <=1e-11;
directional residual/tangent checks <=1e-7. Nondimensionalize using registered
length, force and moment scales before `norm(a-b)/max(1,norm(a),norm(b))`.
Register those scales and perturbation sequences per case before execution;
do not select the best perturbation afterward. Exact reference-linear identities
use exact arithmetic. Existing stricter local native guards remain mandatory.
Binary-identical hashes/state bytes are used for rollback/determinism, not a
floating-point tolerance. Engineering and performance expansion is deferred to
its frozen reference/case gate; no new unbound 2% or speed claim is made here.

Smoke then complete rehearsal precedes formal execution. Each future child:
one numerical-library thread, <=24 GiB process-tree memory, <=600 seconds;
<=3 concurrent children and <=1800 seconds per wave. Inactivity threshold is
120 seconds without checkpoint/output or CPU-time progress. Terminate the whole
child tree on a resource breach. Report checkpoints at capture, trial, local
solve, assembly, acceptance, restart validation and output completion. Preserve
partial logs outside canonical evidence; no automatic retries or reused formal
request. Only a frozen reviewed candidate may run two fresh-directory canonical
cycles; scientific aggregates must be byte-identical. Timings stay diagnostics.

Terminal precedence: authority/schema failure; process/evidence failure;
state/restart correctness failure; constraint/work failure; section/internal
algebra failure; assembly/regression failure; then scoped static-integration GO.
Every unsupported route must reject before state mutation. Any correctness or
state-safety finding blocks the relevant gate regardless of review severity.

## 8. Completion boundary

This freeze adds no implementation, executes no scientific campaign and grants
no new runtime acceptance. Completing G1 warrants recommending G2, not silently
implementing it. General static integration closes only after G1-G5 pass with
updated parity evidence; full legacy domain parity additionally needs the
remaining dynamic, contact, activity, material, ecosystem and other matrix rows.

**Recommended next step:** implement and test G1 in a successor worktree, first
checking whether an exact elastic adapter fits the unchanged native kernel.
