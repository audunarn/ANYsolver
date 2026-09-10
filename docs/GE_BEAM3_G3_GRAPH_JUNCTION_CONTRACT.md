# G3 concrete graph and junction fixture freeze

Status: **FROZEN_DESIGN_NOT_IMPLEMENTED_OR_QUALIFIED**.
Parent: accepted G2 closeout `d5acb45b0a35d6063d8d075bbb2082c56f26c9e4`,
tree `d0d67ce2e03893a1e9737299972c520aea923ee4`.
The canonical authority file binds this text, the explicit fixture JSON, the
standard-library auditor/tests, and exact parent source/evidence blobs.
This freeze runs no mechanics and confers no new runtime admission.

## Ordered slices and unchanged boundaries

1. **G3a / S15, native part of S18:** bounded native branches, cycles and
   disconnected supported components. Use the existing exact-elastic native
   element and one graph owner, not nested G1/G2 analysis owners.
2. **G3b / S16, mixed part of S18:** disjoint-ID native/legacy/shell graphs with
   explicit translation-only ties and independent rotations. The nonnative
   blocks are their existing reference-linear elastic operators only. This
   slice does not admit finite-rotation legacy/shell material response.
3. **G3c / S17:** common-pose rotational adapters require a separate reviewed
   equation/ownership contract and their own implementation/confirmation.
   Until then, the frozen S17 negative fixtures must reject before state work.

No slice closes all G3 obligations by passing expected-rejection tests. In
particular G3a/G3b acceptance cannot mark S17 positive adapter parity complete.
G4 history-bearing sections and G5 public integration remain later gates.
No Q4/S3/beam mechanics, production recovery, selectors, defaults, versions,
old qualification records or ecosystem repositories may change in this freeze.

Future G3a uses a new private owner, bounded to 8 total elements, 32 actual
nodes and 192 external DOFs; do not widen the accepted G1/G2 constructors or
their restart schemas. Check bounds before allocation/evaluation. Each native
element retains its 24 internal coordinates. A complete small reference system
therefore has at most 384 external-plus-internal coordinates before multiplier
rows. Use solves, not explicit inverses, penalties or pseudoinverses.

## S15: explicit native graphs

The fixture file stores actual coordinates, ordered connectivity, material
orientation vectors, roll angles, support nodes and load nodes:

| Fixture | Elements / nodes | Endpoint graph | Supports and exercise |
|---|---|---|---|
| N_BRANCH3 | 3 / 7 | x/y/z arms at one shared hub | All three outer ends fixed; loaded hub, distinct incident rolls |
| N_RING4 | 4 / 8 | square closed ring | One corner fixed; opposite corner loaded |
| N_BRACED5 | 5 / 9 | square plus diagonal | One corner fixed; opposite corner loaded, two independent cycles |
| N_DISJOINT2 | 2 / 6 | two spatially separate beams | Each root fixed independently, both tips loaded |

Node ordering per native element remains [end, midpoint, end]. Build each
right-handed reference triad from the explicit tangent and projected physical
orientation vector, then apply the specified roll about the tangent. Shared
nodes have one authoritative Q, but each incident element retains its own
reference triad. Never average or overwrite those triads.

For every native graph freeze these tests: deterministic sorted IDs/DOFs/CSR
indices, connectivity consistency, correct midpoint ownership, component and
cycle inventory, shared-Q identity across all incident elements, reference
rigid modes, supported equilibrium, physical reactions/work, full stationary
versus Schur linearization including nonzero internal residual, loaded nonlinear
continuation, cancellation and last-element preparation rollback, restart/replay.
At the reference state verify six analytical rigid modes per connected free
component, and positive quotient stiffness using a deterministic complement.
Never compare finite GE response to a linear legacy response as an equality.

Canonical traversal is sorted element IDs, sorted node IDs and local [u,r]
triples. COO duplicate contributions are accumulated in a fixed order before
CSR conversion. Shuffled insertion order must produce identical ordered
scientific evidence; node renumbering/reversal/global rotation instead use the
explicit physical transport maps and the invariant tolerance.

The finite load program is [0,0.5,1,0.25,0]. N_BRANCH3 and N_RING4 additionally
use the two frozen noncommuting prescribed-root orientation targets. Hold other
supports fixed. Check shared rotations from the committed base, not Exp(total).
Native elements keep registered internal convergence and chart bounds.

## S16: translation-only mixed interfaces

Freeze M_B2, M_B3, M_Q4, M_S3 and M_Q4_WEIGHTED. All native and nonnative node
IDs are disjoint, including coincident geometric points. The JSON specifies
each element and its fixed nodes. Constructors/classes are explicit:
`ElasticElement`, `BeamElement`, `QuadraticBeamElement`,
`QualifiedE4PLShellElement`, `NativeParityE4PLS3V2DShellElement`; never infer a
formulation from a current default. Legacy B3 keeps scalar section properties;
its unsupported generalized-section combinations are not GE acceptance cases.
Shell owner normal is explicitly +z, independent of numbering. S3 means the
accepted V2D route, not the older `QualifiedE4PLS3ShellElement` MITC3+ candidate.

M_B2/M_B3/M_Q4/M_S3 tie native tip translations to a coincident nonnative node,
one equation per x/y/z component. M_Q4_WEIGHTED ties a native tip at the square
centre to the four Q4 corner translations with exact weights 1/4. Weights sum
to one and reproduce the reference position. No rotational slot enters T, no
implicit node merging occurs, and no offset moment or hidden rigid arm is added.

Compare independently assembled block-diagonal reference operators plus the
explicit multiplier rows against affine/nullspace elimination: displacement,
reaction, constraint residual, energy and virtual work. The independent assembly
may use unchanged native/legacy element operators, but not the candidate graph
assembler or its cached matrices. This qualifies orchestration, not replacement
element mechanics. Reference-linear residual for a frozen legacy block is K*u;
never use a legacy zero internal-force placeholder as successful equilibrium.
Check equal/opposite tie forces, zero rotational tie rows, weighted work and
net force/moment balance using physical locations. With moments applied to only
one tied side, prove there is no artificial rotational equality.

All mixed models use reference-linear elasticity on both sides for this gate;
nonzero finite rotation programs on mixed graphs reject before evaluation.
Two histories must have separate mutable state. Native stationary recovery
remains native; nonnative recovery uses that family's admitted linear path.
Joint numerical/drill work must not leak into physical section resultants.

## S17: explicit shared-rotation admission

Native-native shared nodes: admissible only to the future G3a owner after its
gate passes, with one shared Q and distinct element-owned reference triads.
Native-native remote RELATIVE_POSE: G2 semantics carry forward only inside the
native graph slice and require G3 graph-level transaction/work tests.

Any native/nonnative shared node ID, affine rotational tie, or cross-family
RELATIVE_POSE without an accepted adapter is rejected before constructing trial
state, calling element mechanics, invoking callbacks or committing. Do not
convert the request to a translation tie, legacy mechanics or an owned joint.
Coincident distinct nodes alone create no coupling.

Freeze the negative matrix across B2, legacy B3, qualified Q4 and qualified S3:
shared six-DOF node, rotational affine row, unregistered relative-pose adapter,
wrong-family adapter, stale/mutated authority, wrong reference normal, and
attempted use of the older owned shell-beam context as a general graph adapter.
Existing RigidPoseJoint, ShellBeamTrialAssembly and CoupledShellBeamAnalysis
are source-bound background/specialized routes, not a universal G3 allowlist.

A later positive adapter contract must bind both families/formulation IDs,
reference frames and physical normal, multiplicative/additive chart maps,
first/second pullbacks, conservative/nonconservative work policy, shell drill
participation, issued trial tokens, prepare-all atomic publication, histories,
recovery and restart fingerprints. Require independent work/tangent/covariance,
nonzero multipliers, noncommuting loading/unloading and last-family failure
rollback before adding any exact adapter ID to the empty current allowlist.

## S18: graph authority, cache and restart fixtures

Use N_BRACED5 and M_Q4 as cache/transaction fixtures. Freeze mutation of node
coordinates, connectivity, section law/roll, constraints/order, supports, load
channel, activity, free-DOF map and owner callbacks, including final prepare.
Reject without changing committed bytes, shared-Q/store generations, accepted
history or checkpoint; leave no trial. Reject G1/G2 base-solve dispatch on G3.
Validate every connected component's supported rigid space independently.
Unsupported disconnected components, duplicate IDs, orphan nodes, malformed
ties, cycles in affine dependencies and bounds overflow are negative cases.

Factor keys include canonical graph/DOF order, formulations, sections, triads,
normal authority, constraints, accepted epoch, current trial pose, tangent and
load policy. RHS-only reuse is allowed only for an identical operator and
constraint chart; altered epoch/pose/section/constraint must miss or reject.
Use two RHS vectors f and -0.5*f, compare separate solves with multi-RHS solves,
and verify cache mutation cannot couple independent accepted histories.
Record cache counters as diagnostics, not speed qualification.

Future GE_BEAM3_G3_GRAPH_ELASTIC_RESTART_V1 must bind all graph components,
explicit mixed-family policies and adapter allowlist, schemas, section/normal
authority, ordered DOFs, constraints, native internal variables, committed
poses, load/target history and runtime. Authenticate with external digest and
replay from a new owner. Reject foreign G1/G2 envelopes and cross-family hot
restart; no migration by resealing. Freeze byte/count bounds before that owner
is implemented; this fixture contract selects 8 MiB and 128 accepted entries.

## Verification and execution authority

All fixture cases are **planned/unexecuted**, including those expected to pass.
The companion matrix names proposed tests separately from existing source/test
anchors. Source anchors are not claims of coverage for the new graph fixtures.

Keep G2 unit scales and normalized norm(a-b)/max(1,norm(a),norm(b)) <= 1e-11;
directional checks <= 1e-7 at every h in [1e-4,1e-5,1e-6]. Exact affine weights
and graph incidence identities use rational equality. Rigid-space/support rank
uses the existing explicit 64*eps*max(shape)*max(1,sigma_max) resolution floor,
never silently removes rows. A rank/conditioning failure blocks, not relaxes.
No new formulation or coefficient is authorized by these fixtures.

Before each slice's formal execution: implement smoke fixtures, complete bounded
rehearsal, freeze exact candidate/test inventory and independently reviewed
runner, then run two fresh-directory cycles with byte-identical scientific
aggregates. Separate G1, G2, G3 and infrastructure inventories. Limits per
child: one numerical thread, 24 GiB/tree, 600 seconds, 120-second CPU/output
inactivity; at most 3 children and 1800 seconds per wave. Emit capture, local
solve, assembly, acceptance, restart and output checkpoints. Kill the complete
process tree on breach; retain partial logs, retry nothing automatically.
No formal mechanics or resource request is issued by this planning freeze.

Terminal precedence per slice: authority/schema; process/evidence; state/restart;
constraint/junction/work; graph/assembly/regression; then that slice's scoped GO.
Unexpected acceptance of a negative fixture is a correctness failure. Expected
rejection is a passed negative test, not positive adapter qualification. S17
positive work remains explicitly deferred, so no all-G3 closure is claimed.

**Next recommended action:** implement G3a native graphs and S18 native-state
guards under this freeze, beginning with N_BRANCH3 smoke; do not enable mixed
translation or rotational junctions implicitly.
