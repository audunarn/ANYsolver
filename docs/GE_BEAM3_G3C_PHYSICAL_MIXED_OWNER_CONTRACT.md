# Private physical mixed-owner successor — frozen integration contract

Status: FROZEN_DESIGN_CANDIDATE_PENDING_INDEPENDENT_REVIEW. Prepared from clean
accepted-recovery closeout ba4f4d793bb9494f3c116030c99577a1b3ebefe6, tree
47c29d6e5d60dc133544cedade3a11a78ee13b3c. This contract permits only the
additive successor mixed-owner implementation after independent design review.
It does not authorize smoke, rehearsal or full G3c execution. Public legacy
B2/B3, qualified Q4/S3, existing defaults and all historical evidence remain
unchanged.

## 1. Fixed inherited authority

Use the existing shared qualification harness and completion register. Preserve
old source, contracts, packets and their classifications; do not rename earlier
results into successor evidence. Exact raw-file bindings at preparation:

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| docs/reference_cases/ge_beam3_g3c_mixed_owner_contract_v1.json | 11446 | 471d05d2db6c604c39e30320e279e3a8ccd47186cb549969a596a00c62d967e5 |
| docs/reference_cases/ge_beam3_g3c_history_restart_contract_v1.json | 108973 | 7afe9d79096338c122280c20f83b6e7c5681ea0a382e32cb15e1e9349b9372e6 |
| docs/reference_cases/ge_beam3_g3c_rehearsal_contract_v1.json | 28474 | 34cab4da253e5abc7a643d28d88eafc6ad02ac862db00263f747ea167c86d9aa |
| docs/reference_cases/ge_beam3_b2_formal_supplement_review.json | 1412 | 95edd0b65da47a55a6d4d9312b9315d7532f744fc40302ddd3581ae68d6628ee |
| docs/reference_cases/ge_beam3_b2_formal_supplement_manifest.json | 16856 | 06a7acabca21be90301c299cf7800f6b63eefa2f82c2f940e237eff1a4f6c269 |
| src/anysolver/_ge_beam3_g3c_b2_physical_adapter.py | 8182 | 99fb7a4239728948037bf3150b91684f2b9f581cbfc2c6469b8711f2c86162df |
| src/anysolver/_ge_beam3_g3c_affine_q4_recovery.py | 23761 | 31caa236380a080ee9c95fac43df6e59508070b2694a70ad3540f86316bd9f0f |
| src/anysolver/_ge_beam3_g3c_stable/owner.py | 26550 | 71f1e7df808c9be814ee478cf4c2d785fe851aeb9be274d8870851c7378a37f5 |
| src/anysolver/_ge_beam3_g3c_stable/authority.py | 7347 | 6901dc75b3c36e4e06657dcba104b2558f202b9683677f81e0b9e16823608ece |

The inherited canonical fixture file hash is
d5fecc80c3203ac7d191b4031d64bf35c56d2900066cb01fc1dfa4276d24c006.
Bind its original source-blob authority as well as actual checkout bytes; no
line-ending normalization is evidence equality. Bind the complete new source
graph, environment and independent review in the existing runner's inventory.

B2 core freeze dc6077455fa254756f9e462612b8cdd98eb85889, tree
791bdb6334ad7078524826dbf3ade1cc1da77353; accepted science
3decea9d36003a657eed70bac780299c898f46512745e72e3c8311c0fdde05e9.
B2 adapter freeze 5121102cdd82a99c091ac2c1403afc79d5869742, tree
5d75a1597a47e898071c19f213bcd5b88e671cbe; accepted science
54efcaebebd0f8b292a3913a0d1eb7c088480a254a968038f91ffb1a34a1381d.
The supplemental review preserves original rehearsal/formal labels and adds
formal2 without rewriting prior packets. These are local, not graph acceptances.
Q4 numerical freeze is 62796d0340ee27c8cfe60fe96a7c9d2b371f3a1a, tree
9d84605b06662ea5b50e694a09ce9b328ebfee2f. Accepted formal science is453394
bytes, SHA-256 de4fde319f0c7e45eb549cfa8f71f94b60413213e28828ca414cbcbbf636b1ee.
Independent evidence review SHA-256
cdcd2e880d3e136cf05228e4c7f9c29b0ae1e2d693d6646d7a9e3b47b0472142 binds
evidence manifest SHA-256
65b56f19787cf842be45a97aeb66b4a1196de3667b530b83ea2f7e83361bea8f. Evidence
closeout is ba4f4d793bb9494f3c116030c99577a1b3ebefe6, tree
47c29d6e5d60dc133544cedade3a11a78ee13b3c. The retained exact recovery and
source-equivalence design authorities remain prerequisites, not replaced by
numerical agreement.

## 2. Minimal additive implementation and explicit identities

Exact permitted implementation extent after independent contract review:

- src/anysolver/_ge_beam3_g3c_physical_owner.py: distinct exact-class owner;
  mechanically scoped successor of stable/owner.py, not a subclass or monkeypatch.
- src/anysolver/_ge_beam3_g3c_physical_authority.py: inert closed graph expansion,
  exact policy/recipe/runtime association, derived from stable/authority.py.
- scripts/ge_beam3_g3c_physical_history_owner.py: composition-only checkpoint,
  genuine replay and continuation, preserving the old history wrapper.
- scripts/ge_beam3_g3c_physical_restart_preflight.py: inert nested validation,
  preserving scripts/ge_beam3_g3c_restart_preflight.py.
- tests/test_ge_beam3_g3c_physical_owner.py: local composition, one-chart, work,
  Schur, graph, transport, atomicity, token, definition and recovery nodes.
- tests/test_ge_beam3_g3c_physical_history_restart.py: smoke histories, exact
  ten-history rehearsal, prefix/replay, continuation and negative probes.
- tests/test_ge_beam3_qualification_runner.py: inert registered-inventory and
  process/evidence guards only.
- docs/reference_cases/ge_beam3_g3c_physical_owner_contract_review_v1.json:
  canonical independent design review.
- scripts/run_ge_beam3_qualification.py and
  docs/GE_BEAM3_QUALIFICATION_COMPLETION_REGISTER.md: extend the existing shared
  harness/register. No second resource, publication, authority or review framework.

Freeze these NEW identifiers, with no fallback aliases:

| Meaning | Literal |
| --- | --- |
| Owner policy | GE_BEAM3_G3C_PHYSICAL_MIXED_ELASTIC_OWNER_V1 |
| Composite operator graph | GE_BEAM3_G3C_PHYSICAL_OPERATOR_GRAPH_V1 |
| Definition schema | GE_BEAM3_G3C_PHYSICAL_GRAPH_DEFINITION_V1 |
| State schema | GE_BEAM3_G3C_PHYSICAL_MIXED_ELASTIC_STATE_V1 |
| Adapter envelope | GE_BEAM3_G3C_PHYSICAL_ADAPTER_ENVELOPE_V1 |
| Restart schema | GE_BEAM3_G3C_PHYSICAL_GRAPH_RESTART_V1 |

These identify composition and ownership; they do not rename any underlying
physical formulation. B2 dispatches only PhysicalB2Adapter from the bound
physical adapter, policy GE_BEAM3_G3C_B2_PHYSICAL_MATRIX_ADAPTER_V1, core
GE_BEAM3_G3C_B2_PHYSICAL_FLEXIBILITY_V1. Q4 dispatches only
AffineQ4PhysicalRecovery(construction_id), with physical source operator
E4_PL_QUALIFIED_Q4_HYBRID_V2, recovery
GE_BEAM3_Q4_AFFINE_CHART_PHYSICAL_RECOVERY_V1, representation
GE_BEAM3_Q4_AFFINE_STATION_RECOVERY_64_V1, chart numerics
GE_BEAM3_Q4_AFFINE_INCREMENT_RESOLVED_CHART_NUMERICS_V1, and association
GE_BEAM3_Q4_NATURAL_COORDINATE_BIJECTION_V1. Native, B3, S3 and joint equation
implementations stay unchanged and receive exact inherited bindings.

No old stable/mixed/G1/G2/G3a/G3b, public or hypothetical checkpoint is accepted
under the new restart ID, including an old packet with only its outer ID/hash
replaced. Before any element/material/array construction, verify complete
schema, known runtime/environment/policy identities, fixture expansion, family
policy, recipe association, counts and every nested type/link. Unknown numerical
constructor-dependent commitments remain untrusted until genuine replay;
preflight must not invoke constructors to bless them. Old source schemas inside
authentic native payloads remain unchanged; changing the graph schema does not
permit fabricated native material authority.

The new closed adapter envelope retains element ID, epoch, pose, deformation,
origin/previous links and definition digest, adds its envelope schema plus exact
operator/recovery/representation/chart/station identities where applicable,
and a recovery-witness digest. Define family-specific closed schemas, not a
permissive dictionary with optional guessed fields. B2/B3 material-candidate
digest remains canonical null; Q4/S3 candidate digest binds actual virgin-source
diagnostic bytes. source_material_committed=false remains mandatory. Any
physical_recovery_verified flag is limited to this registered scalar graph
scope and must bind the actual checked witness; it is never a qualification or
source-material-commit flag and is not accepted on declaration alone.

## 3. One actual chart and one assembly

Capture one immutable accepted generation containing total translations,
rotation matrices, bookkeeping rotation slots, multipliers, native origins and
journal. eta is trial bookkeeping minus captured accepted bookkeeping;
Qa is the captured physical nodal matrix. B2 construction is
PhysicalB2Adapter(tuple(node_ids), coordinates, physical_anchor, E,nu,section),
then evaluate(u_with_total_translations_and_eta,Qa_subset). Q4 construction is
the exact graph/variant registry ID, then the same evaluate displacement/Qa
convention. Never supply an arbitrary approximately matching reference.

B2 supplies chart_force/chart_hessian and physical station work. Q4 supplies
chart_force/chart_hessian including the separately identified PL/hourglass
channels; physical_chart_force/physical_chart_hessian and recovered physical
stations remain separately available. Scatter each total chart force/Hessian
exactly once. Do not call the old family scalar operator as a second residual,
perform a second chart pullback, or sum physical and total outputs twice.
Native responses retain actual issued-context pullback and full42 stationary
system,24 internal coordinates, Schur lift/correction and accepted-origin checks.

For independent work, use Q4 e=M d+n(d), s=C e and all4 weighted station fields;
verify full64 stationary residual/inverse/coupling and direct-versus-Schur
24-chart Hessian, including geometric second strain derivatives. Also retain
source35 linear stationary identities. Q4 PL/hourglass energy, force and
Hessian contribute to numerical equilibrium but never physical section stress,
resultants or physical work. B2 physical integrated station work must reproduce
its actual chart force; no signed diagnostic or effective-shear substitute.
For each family verify physical force/moment and frame provenance at the real
accepted pose, not only zero-reference stiffness or manufactured local poses.

Spatial comparisons use r=P^-T g and J_chart=P^-T(H-Cconnection), with the
same actual eta and analytic P=diag(I,Jleft). Same-pose spatial-input tangent
is J_chart P^-1. No post-hoc symmetrization. Joint/support assembly retains
all multiplier Hessians and the actual nonidentity port C, offsets and work;
external graph loads remain the registered spatial dead nodal forces only.

One owner generation is the sole publication point. All preparation, callback,
allocation, diagnostics, native sandbox commits, hash/serialization checks and
cancellation occur before its final guarded swap. Fresh history-free adapter
diagnostics are not accepted material states. Immutable Q4 stationary caches
may be reused only if explicitly bound to the full definition and checked
before observations, after callbacks and finalization; no persistent global
factor or replay-result cache is added. Each resumed owner is genuinely fresh.

## 4. Exact finite graph coverage — no geometry substitution

All five variants, in order: BASE, SHUFFLED_INSERTION, RENUMBERED,
CONNECTIVITY_REVERSED, PROPER_GLOBAL_TRANSFORM. Node/element/joint sorting,
number maps, original absolute target program and director/anchor rules are
unchanged. The geometry and policy are separate: legacy fixture wrapper strings
remain inert historical background, never executable dispatch authority.

| Graph | Elements/nodes/joints/constraint rows | Successor change |
| --- | --- | --- |
| J_B2_PAIR | 3/8/2/24 | B2 element11 physical adapter; anchor physical101 |
| J_B3_PAIR | 3/9/2/24 | B3 unchanged; midpoint anchor physical102 |
| J_Q4_PAIR | 3/10/2/24 | Q4 element11, registry J_Q4_PAIR::variant |
| J_S3_PAIR | 3/9/2/24 | S3-V2D unchanged |
| J_MULTIFAMILY_LOOP | 6/17/8/54 | B2 element11 anchor101, Q4 element13; B3 midpoint202 and S3 unchanged |

Q4 pair reference is [(0,0,.125),(1,0,.125),(1,1,.125),(0,1,.125)].
Loop Q4 reference is [(0,.5,.125),(2,.5,.125),(2,1.5,.125),(0,1.5,.125)].
The ten graph/variant constructions already exist in the finite affine registry.
Verify exact node IDs/order, bytes, normal and material-direction agreement
against the independently expanded graph before construction. Material direction
is physical +X (U times +X in PROPER_GLOBAL_TRANSFORM), NOT the element's +Z
orientation field; shell reference_normal supplies the director. Reversal does
not reverse physical director. Numbering maps physical anchors, not array slots.
No additional Q4 reference geometry is required for this inherited25-case
inventory. Generic affine/nonaffine geometry remains a later parity obligation.

Each graph/variant has force scales .01,1,10 and motions NONE,CM0,CM1,CM2,CM3:
25 ordered graph records,375 histories. NONE has5 LOAD_STAGEs; each CM has4
genuine preparation commits plus5 LOAD_STAGEs:3075 accepted events and3450
prefix0..final replay/continuation probes per cycle. Q4-bearing subset is10
graph variants,150 histories,1230 events,1380 prefixes, not extra records.
Load factors [0,.5,1,.25,0], force [.1,.2,-.3], registered root rotations and
all h=1e-4,1e-5,1e-6 remain unchanged. Common CM3 reaches1.4pi by four genuine
preparation stages; never synthesize accepted matrices to skip native solves.

## 5. Complete MO01–MO18 fixture mapping

Each original obligation retains its exact canonical name/list in the source
contract. Proposed test groups below must be expanded to collected concrete
pytest IDs in the same runner before implementation freeze; no table row is a
claim that tests exist or have passed.

| Obligation | Required actual successor fixture/check |
| --- | --- |
| MO01 registered25/boundary | Every expansion; wrong family/normal/anchor, extra node/element/constraint, unsupported section and stale identity before construction |
| MO02 issued context/origin | Both native elements in every graph at every commit; real source context/store ownership and exact shared-node Q/translation |
| MO03 full Schur/load | Every native full42/internal24 Schur stage; nonzero internal residual and registered nonzero local load work; Q4 source35 and physical64 witnesses where present |
| MO04 four adapters/one chart | Actual B2/B3/Q4/S3 responses, force-weighted chart Hessian, no double pullback; all5 graphs and solved stages |
| MO05 joint work/wrench | All joints including nonidentity C and offset moments; independent constraint derivative and physical work in every graph |
| MO06 support KKT | Every support/root stage, multiplier-weighted Hessians; inherited nonzero perturbation/direction and all3 steps before load stage0 of each history |
| MO07 loads/history | All375 genuine histories, fixed force-scale within each program, unloading/reversal and noncommuting roots |
| MO08 transport/rebase | All25 variants, all4 CM preparations and NONE; passive/common block maps, actual same-pose rebase, immutable original accepted diagnostic hashes |
| MO09 late atomicity | Last nonnative family, last native sandbox commit and prepublication failure in every family; preceding bytes/epoch/journal identical |
| MO10 callbacks/cancel | Input mutation, cancellation, reentry and concurrent capture; clean lock/sandbox drain and no accepted mutation |
| MO11 tokens | Authentic foreign/stale/copied/replayed capabilities, owner/generation/runtime/serial mismatches |
| MO12 definition/cache | Coherent resealing, complete valid-definition swap, runtime/operator/recipe/chart/station/cache association replacement before and during observation |
| MO13 nested preflight | Every closed nested schema/hash/count; old-ID and rebound-old-packet rejection before element/material/array construction sentinel |
| MO14 prefixes | All3450 fresh prefix imports plus genuine continuation, every prior prefix checked; final full unprojected bytes equal uninterrupted history |
| MO15 rehashed attacks | Inherited24 categories/71 members at both actual origins:142 probes; actual semantic forgeries must pass syntax then fail corresponding genuine replay, not arbitrary exception |
| MO16 recovery | Physical B2 station strains/resultants/work and Q4 source-consistent station fields/full64 Schur at actual solved stages; B3/S3 actual recovery retained; numerical channels excluded; explicit open-domain flags |
| MO17 process/evidence | Memory/timeout/inactivity/peer failure, complete process-tree drain, no partial canonical output, no authority reuse/retry |
| MO18 full acceptance | Complete rehearsal, independent implementation review, two deterministic full375/3075/3450 cycles, independent evidence review |

Retain mutation origins B2 BASE S0 NONE prefix2 and MULTIFAMILY_LOOP BASE S2
CM3 prefix9. Require both fresh positive resumes first, then inherited142
authentic negative probes, plus concrete new-identity/recovery/cache payload
members frozen before execution. If adding members, report original142 and
new successor extras separately; never silently change the original count.

## 6. Replay, scheduling and truthful adjudication

Checkpoint is strict bounded canonical ASCII JSON plus independently supplied
expected SHA. Duplicate keys, nonfinite/overflow, unknown keys, alternative
spelling, integer/float substitutions and booleans in integer fields reject.
Preserve native layouts and exact epoch/history DAG. Reconstruct every command
through actual native solve/prepare/commit. A syntactically coherent state/hash
is not proof of a valid numerical origin. Compare every prefix and full final
bytes, never only selected physical fields; diagnostic transport projections
retain only the precisely inherited allowed omissions and are not restart input.

Start with five separate BASE/NONE/.01 family smoke cases (zero then first
finite stage), then ten complete BASE rehearsal histories: NONE/.01 and CM3/10
for each graph,70 events/80 saved prefixes. Run positive resumes and authentic
negatives, full work/transport/atomicity rehearsal before full formal dispatch.
No earlier-operator rehearsal packet substitutes for these successor histories.
Measure each work unit and estimate total375-history/prefix cost before formal
dispatch. Partition units before freezing; never enlarge600-second bounds or
skip prefixes because timings disappoint. Complete full rehearsal success and
all MO prerequisite checks are required before TWO formal cycles.

Reuse scripts/run_ge_beam3_qualification.py: at most3 children, each one numerical
thread,24GiB entire tree,600 seconds,120-second inactivity; wave1800 seconds.
Binding includes candidate/tree/environment/review and entire ordered assignment
inventory before imports. Child checks exact assignment; slots advance only
after terminal/drained trees. Exclusive external outputs, no automatic retries,
no consumed authority reuse. Process failure/pytest crash/timeout is BLOCKED,
not invented scientific NO_GO. A scientific contradiction requires completed
typed payload independently sufficient to verify it. Preserve failed raw logs
outside canonical aggregate; never count unexecuted or aborted nodes as passed.

Freeze this terminal precedence exactly:

1. BLOCKED_GE_BEAM3_G3_AUTHORITY
2. BLOCKED_GE_BEAM3_G3_PROCESS_OR_EVIDENCE
3. NO_GO_GE_BEAM3_G3_STATE_OR_RESTART
4. NO_GO_GE_BEAM3_G3_JUNCTION_OR_WORK
5. NO_GO_GE_BEAM3_G3_GRAPH_OR_ASSEMBLY
6. PROVISIONAL_GO_GE_BEAM3_G3C_COMMON_POSE_ELASTIC_GRAPH_ONLY

The first five are inherited from the accepted G3 contract. The sixth is the
already preregistered scoped G3c terminal and authorizes only the finite registered
elastic graph slice described here. Do not invent a replacement success or relax
tolerances. Two
canonical scientific aggregates must match byte-for-byte; external timings and
process IDs are separate diagnostics. Independent final review must have no
correctness/state-safety finding, regardless of severity label.

## 7. What this next gate does not finish

This is registered, scalar, virgin/history-free nonnative mixed static graph
closure. Accepted Q4 local numerical fixtures do not prove solved graph histories;
the history campaign supplies that evidence. It does not establish unrestricted
affine/nonaffine shells, wider B2 geometry admission, history-bearing generalized
or plastic sections, G4 S19–S24, G5 loads/inertia/spectra/transients/contact,
all legacy P01–P32/U01–U10 rows, consumer interfaces or installed-wheel parity.
Those remain explicitly OPEN, not classified legacy-unsupported without tests.
No defaults, tags, version changes or publication follow from this subgate.
Every outcome retains NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.

Next action: independently review this frozen successor contract and exact path
extent; implement only the additive integration and freeze every collected test
node before numerical execution. Then run the five family smokes and complete
ten-history rehearsal under fresh bounded authority. Full G3c formal execution
is separately frozen only after every prerequisite passes.
