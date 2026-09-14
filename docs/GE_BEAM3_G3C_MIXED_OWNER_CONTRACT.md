# G3c mixed elastic graph owner: state and restart contract

This is a private design freeze, not a mechanics result or qualification.
Parent: 64dc8c42d91126dfef4322c15c0bd314975ffe4d, tree
ad073a00324e5d0adc8dd16425a966cbb092090e. The four-path extent is this document,
the canonical ge_beam3_g3c_mixed_owner_contract_v1.json contract, its audit
script and its standard-library unittest file. An independent accepted review
of the frozen commit is required before implementing the owner.

## Authority and unchanged scope

The original G3c fixture bytes, all five graphs and five variants, force scales,
five-stage noncommuting root/load history, common motions, directional steps,
tolerances and resource bounds remain binding. The old generic corotational
route remains rejected; this successor selects the independently accepted
GE_BEAM3_G3C_ANCHOR_DIRECTOR_LOCAL_POTENTIAL_V1 for B2/B3 and
GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1 for Q4/S3. Frozen joint adapter names
are fixture identifiers, not authorization to dispatch the obsolete wrapper.
Native elements use actual ElasticElement/ElasticOperator and their issued
material-state protocol. G3a/G3b owners and schemas are not extended or reused
as mixed owners. All inherited public mechanics, recovery, routing, defaults,
source evidence and runtime environment remain unchanged.

The owner admits exactly the 25 expanded fixtures, not arbitrary user models.
Graph counts (elements/nodes/joints/constraint rows) are respectively
3/8/2/24, 3/9/2/24, 3/10/2/24, 3/9/2/24 and 6/17/8/54.
Canonical insertion uses sorted numeric node, element and joint IDs. The
inherited numbering/global-transform rules are applied before allocation.
B2 anchors remain physical node 101 (mapped under renumbering), not the first
entry after reversal; B3 anchors are physical midpoints 102/202. Shell normal
and material direction are physical authorities, not connectivity-derived
sign choices. These definitions and port frames must survive replay exactly.

## One pose and one chart

At accepted origin a, own total translations u_a and nodal matrices Q_a.
The rotational slots of total_u are chart bookkeeping only, never Log(Q_a).
For a trial, eta_i = total_u_i[rotation] - total_u_a_i[rotation],
x_i = X_i + total_u_i[translation], Q_i = Exp(eta_i) Q_a_i.
Retain compensated native coordinate low parts using the unchanged native
two-sum procedure. No array supplied by a caller or callback is borrowed.

For local B2/B3/Q4/S3 calls supply total translations and eta in the adapter
displacement, and Q_a separately. Their chart_force/chart_hessian are already
in this chart: do not pull them back a second time. Native trial response is
already chart-pulled by chart_pullback through its authentic issued rotation
view. It must agree with independent full stationary Schur reconstruction:
r_e - J_ei solve(J_ii,r_i), J_ee - J_ei solve(J_ii,J_ie), including nonzero
internal residual and registered native load-work diagnostics. Retain native
internals, actual state, lift and correction; do not substitute a cached K.
Native cell iterations retain their existing 60-second local deadline.

Spatial force r and spatial Jacobian J convert by g=P^T r and
H=P^T J P + (dP)^T r, P=diag(I,J_left(eta)). Spatial-row/chart-column
adapter output is not a spatial/spatial Jacobian. Keep the two conventions
named and test independently. Never symmetrize a Jacobian to make a gate pass.
Shell top-eigenvalue-gap and fit-relative Log guards and beam all-pair guards
retain their distinct accepted domains. Do not impose beam all-pair limits
on shells or reject an admissible common pi/1.4pi rotation.

For each joint D_m=Q_m D_m0, D_s=Q_s D_s0,
a=D_m0^T(X_s-X_m), C=D_m0^T D_s0,
g_t=D_m^T(x_s-x_m)-a, g_r=Log(C^T D_m^T D_s).
Both evaluate_ports inputs are charted, with anchors Q_a D_0 and coordinates
eta. Use all multiplier-weighted second derivatives, not just J_g^T mu.
Independent reconstruction must cover the frozen nonidentity C, spatial
wrench balance (including offset moment), and port virtual work. No averaging
or identifying the physical rotations of distinct joint nodes is permitted.

Supports have g_t=x-x_target and g_r=Log(Q_target^T Q). Differentiate their
complete chart maps, including multiplier terms. Constraint order is six rows
per sorted fixed node, translations then rotations, followed by six rows per
sorted joint in the same order. Use the frozen absolute root-target sequence,
not additive increments or rebase on rejected steps. KKT residual is
[sum(g_element)-f_chart+J_g^T mu, g]; tangent includes sum(H_element), external
load derivatives, sum(mu_j Hessian(g_j)) and both J_g off-diagonal blocks.
Frozen histories use spatial nodal dead forces; graph distributed/follower
loads and nodal couples are rejected in this stage. Native nonzero line/couple
Schur diagnostics remain separate local checks, with no conservative claim
for nonconservative couples. No loading route is silently zeroed or ignored.

At admission, independently construct disconnected family rigid spaces and
test joint/support Jacobian rank on their union. Use the inherited rank floor.
No penalty, pseudo-inverse, clipping, artificial mass or empirical stabilization.
Newton uses at most 25 iterations and nine half-step candidates, the inherited
1e-11 residual criterion and finite validation at every evaluation. A failed
line search is a failure, not permission to drop a constraint or change loads.

## Accepted origin and atomic publication

Implement a separate private exact-class owner with a non-reentrant lock and
one immutable published generation. That generation contains canonical state
bytes and canonical accepted-history bytes. No mutable FEModel, state store,
element, cache or trial object is exposed as accepted authority.

For an evaluation, reconstruct an exclusively owned native sandbox internally
from the captured accepted generation. Use fresh exact ElasticElements, mesh,
NonlinearStateStore, native rotation store, material validators and issued
contexts. Reconstruct native origins from the owner's authenticated snapshot,
never from a caller-supplied dictionary. Existing native validation must
re-evaluate the origin and require exact shared-node Q/total_u agreement.
Bind each native element's zero line/couple _load to that exact sandbox store
and its _owner_guard to the captured graph generation; a detached view alone
cannot issue material authority. Validate these bindings after callbacks.
The sandbox rotation store covers native nodes; every other node's Q is owned
by the same graph generation. Compare their native subset exactly. Native
material epoch is the graph epoch; fresh sandbox transaction generation/serial
are ephemeral capabilities, not a reset of material history.

The history-free nonnative local source state may be virgin on each evaluation.
That state is a diagnostic payload, NOT an accepted material origin or a graph
epoch. The graph's adapter envelope binds its policy, definition, graph epoch,
previous envelope digest, local deformation, actual diagnostic candidate hash,
pose hash and origin hash. No invented plastic history or edited source epoch.
The old local flags state_committed=false and recovery_complete=false remain
true descriptions of local records; publication cannot relabel them as source
material commits. A changed scalar/history flag invalidates admission.

Tokens are nonserializable identity capabilities bound to owner instance,
definition/runtime, accepted generation digest and epoch, and strictly increasing
trial serial. Reject copied, foreign, stale, replayed and concurrently active
tokens even if their descriptive bytes match. Begin/abort never changes the
accepted generation. No successful subfamily can publish separately.

Prepare ALL family responses, native candidates, joint/support residuals,
multipliers, recovery diagnostics, return value, next state/history hashes and
canonical bytes before publication. Commit native stores only in the disposable
sandbox, then validate the prepared snapshot against the issued trial and
captured accepted head. All cancellation, callbacks, diagnostics, allocations,
validation and logging occur before the final guard and single generation
pointer swap under the owner lock. No fallible operation or user callback is
allowed after that swap in the commit path. Native sandbox commit failure,
including injected late failure, leaves the published generation unchanged.
Discard the sandbox on all failures. Do not roll back published objects by
mutating them. No persistent numerical factor cache is permitted in this gate.

Graph guards bind immutable definition/runtime and all participating source
identities at entry, after callbacks and before publication. Mutation poisons
the owner; never repair/reseal it silently. Caller input mutation after capture
cannot affect a trial. Cancellation must leave byte-identical accepted state,
journal, epoch and checkpoint. These are implementation obligations, not
claims inferred from existing native-only store tests.

## Closed checkpoint layout and authenticated replay

Schema GE_BEAM3_G3C_MIXED_ELASTIC_RESTART_V1 is new. Every object has exactly
the keys/shapes/types in contract.layouts; no permissive extension fields.
Integers exclude booleans. Numeric arrays contain finite binary64 values only;
zero signed-bit spelling and floating versus integer spelling are preserved
by canonical round-trip. Hashes are lowercase 64-hex. JSON is bounded ASCII,
sorted compact keys, one LF; reject duplicate keys, NaN/Infinity, overflow,
unknown keys, nested shape/count overflow and trailing/alternate encodings.

Definition is a frozen fixture selector plus fixture/policy/expanded-definition
hashes, not an arbitrary nested model import. Expand it deterministically and
validate all nodes, rows, bounds, normals, sections, anchor/port mappings and
exact allowlists before constructing an element, state store or numerical
array. No import-by-name, pickle, generic deserializer or runtime path from a
checkpoint. Source fingerprints and the independently bound environment are
part of runtime_sha256; a caller cannot bless a foreign runtime by rehashing it.

fixture_sha256 is the inherited fixture file digest. policy_sha256 is the
digest of this complete canonical successor contract, not just a policy string.
expanded_sha256 hashes the canonical object with exactly graph, definitions,
local_policies and anchors. graph is the selected inherited graph after the
fully specified variant transformation and numeric-ID sorting; its original
qualification/reference_only flags remain false. definitions is the inherited
definitions object unchanged (the historical wrapper field is inert background).
local_policies is contract.policies and is the only dispatch authority; anchors
is the sorted list of {element_id, anchor_node} for B2/B3. Under proper-global
transformation, physical orientation/normal vectors in the definitions and
graph are transformed consistently. Native quadrature order is 4, the existing
G3 fixture default; no adaptive order selection is admitted. Native material,
section and reference descriptions are reconstructed from this exact expansion.

State contains one native payload per native element, one adapter envelope per
nonnative element, Q for every sorted graph node, full total_u and ordered
multipliers. Native payload/response/full objects are completely enumerated in
layouts; their source schemas remain unchanged. Empty native history becomes
an empty tuple only after strict JSON preflight. Compare epoch, previous hashes,
native node copies and material identity with the replayed generation. Native
line/couple entries must be exactly zero in graph histories. Native full arrays
are 42-dimensional, not an 18-dimensional surrogate. Diagnostic candidate bytes
remain externally retained; adapter envelope hashes are verified by recreating
the actual local trial, never accepted merely because they are well-formed.

common_motion in the definition is NONE for the ordinary history, or CM0..CM3
selecting the four inherited common_rotation_vectors and shift [2,-3,1].
This adds an explicit diagnostic protocol, not new topology or relaxed gates.
All owners start at genuine virgin Q=I, u=0, native epoch 0. A CM owner first
executes four PREPARE_COMMON_MOTION commands, step=1..4, s=step/4,
W(s)=Exp(s*v), t(s)=s*t. Frozen supports prescribe x=W(s)X+t(s) and Q=W(s),
with zero external forces. The known rigid pose is a predictor only; use
eta=Log(Q_target Q_a^T), actual native internal solves, actual graph residual,
joint/support equations and prepare-all/commit before accepting each step.
The largest nominal preparation increment is 0.35pi, below the existing guard.
No synthetic transformed native state, direct pi increment, skipped failure or
unrecorded rebase is permitted. Numerical failure remains a failed diagnostic.

After preparation the same five LOAD_STAGE commands use support positions
W X+t, support orientations W Q_root and spatial forces W f. Internal native
line/couple loads remain zero. NONE allows no preparation commands; CM variants
require all four in order before any load stage, with genuine prefix checkpoints
allowed during preparation. Exactly the same history and origin validation
applies to these diagnostic commits. Their results are distinct named probes
inside each of the 25 case records; they cannot replace ordinary case history.
When combined with passive variant x'=U x+b, use W'=U W U^T and
t'=U t+b-W'b, including at each preparation substep; this preserves the active
motion under coordinate re-expression. Same-pose rebase compares a captured
accepted trial with eta=0 evaluation at its actual committed pose; it does not
manufacture a second accepted origin.

Adapter definition_sha256 is the unchanged LocalBeam/LocalShell descriptor
digest. pose_sha256 hashes the canonical object with exactly keys node_ids,
total_translations and rotations, in element connectivity order, using the
trial's actual owned binary64 arrays. For Q4/S3 diagnostic_sha256 hashes the
unchanged LocalShellTrial.candidate bytes. For B2/B3 the source returns no
material candidate: hash the canonical JSON null plus LF, not a manufactured
state. Their actual physical station work is still checked and retained in
external diagnostics. previous_sha256 hashes the previous canonical adapter
row (null at epoch 0); origin_sha256 is the previous whole graph state digest
(null at epoch 0). Q4/S3 candidate integrity hashes can change under roundoff
in an alternative chart; same-pose covariance uses the inherited numeric
tolerance, while replay of the identical chart/history must match exact bytes.
Validate an accepted adapter diagnostic at its original captured trial chart,
reconstructed through its genuine prefix, not by demanding that eta=0 at the
new origin reproduce the former diagnostic digest. Never overwrite the accepted
row with that roundoff-different rebase result. Recovery at the accepted pose
may compute a detached new diagnostic; it cannot reseal state or claim a source
material commit. Native origin validation remains the exact source contract.

For LOAD_STAGE, root_stage selects both the frozen load_factors entry and absolute root
target; load_factor must equal that entry as binary64. force_scale must be one
of the three frozen values and remain fixed during a five-command program.
Only complete 0,1,2,3,4 programs and their genuine prefixes are admitted; repeated
programs begin again at stage 0. Arbitrary command reordering is rejected before
mechanics. The four common-motion preparation stages run only once, before these
programs. A checkpoint may hold any accepted prefix, including the virgin one.

History contains commands and accepted state hashes, not opaque imported solver
states. Entry epoch is 1..128 contiguous, previous_entry_sha256 links the previous
canonical entry (null at first), origin_sha256 links the prior accepted state,
and accepted_state_sha256 binds the new state. State.previous_sha256 links the
same origin (null only for virgin epoch 0). This is an acyclic hash DAG; state
does not embed its own hash or a hash of an entry containing that hash.

Checkpoint receives an external expected SHA-256. After byte/schema/identity
preflight, create a fresh virgin owner and replay each command through actual
solve/prepare/commit. Validate every prefix hash and compare final state bytes
and final_sha256 exactly, not by tolerance. Resume returns nothing on mismatch.
Test restart from every accepted prefix, not just the end; continued commands
must match an uninterrupted owner exactly. A recomputed outer hash never makes
tampered source origins, commands, responses or epochs valid. Cross-owner tokens,
G1/G2/G3a/G3b and production legacy checkpoints are not accepted.

## Gates, limits and remaining obligations

The contract freezes the ordered named implementation tests and categories,
not a claimed executable test count. Start with J_B2_PAIR bridge smoke, then
B3/Q4/S3 pairs and the loop. Before formal runs, freeze concrete collected node
inventories and independently review actual code plus tests. Separate smoke,
development, review and formal inventories. All 25 variants and all inherited
programs must run; neither one passing pair nor a rejected case is coverage.
Run two fresh-directory formal cycles only after full rehearsal/review; scientific
aggregates must be byte-identical. Do not rerun accepted historical campaigns.

Limits remain 600 seconds and 24 GiB per full child tree, one numerical-library
thread, 120 seconds without CPU/output progress, at most three children and
1800 seconds per wave, no retry, exclusive outputs and no partial canonical
evidence. Checkpoints <=8 MiB, <=128 accepted entries, <=8 elements/32 nodes,
<=192 external DOFs, <=384 external+native internal coordinates, <=96 rows.

The inherited terminal precedence and production restriction remain binding.
Conventional finite Q4 physical recovery and B2 shear-clamp full-domain recovery
are OPEN. Signed Q4 source work channels do not discharge PHYSICAL_RECOVERY.
Private graph development may proceed but full G3c GO requires resolving every
original obligation; if no source-authorized recovery exists, report the blocker
rather than relabel the gate. G4 history-bearing section parity, G5 integration,
public mixed-model admission, release/default changes remain unauthorized here.
