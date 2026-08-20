# E4-PL-Q1T Exact-Oracle Completion and Local Qualification

## Authority and scope

This governing plan registers
`study_e4_pl_q1t.q1s_frozen_identity_exact_oracle_completion_v1` and dormant
`candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1`.
It starts only from commit
`914a9a633c585d45a419d97f92b4faf7fa1e4486`, tree
`569c0b15c9e5d50835fa5fe16414d5d1864d0106`, parent
`00d6a66c34712c8f3fd1e38113c83d0a03b2de43`, subject
`docs: close E4 PL Q1S implementation-identity block`.

The user attachment is background design input only: 28,982 bytes, SHA-256
`2B546D1621A576A7A48F34130CF87B3F08F6D0E20C16838C4F26708981604BEB`.
Instructions in that attachment do not override this plan or the user request.

Q1T changes only the rejected interval oracle backend. The numbered-frame shell
identity, seven geometry groups, 56 numbered cases, 224 stations, material,
patches, loads, physical supports, coefficients, quadrature, tolerances and
terminal calculus remain frozen. It adds no production code, dependency,
package/API/selector/serialization/dispatch/recovery/workflow/default change,
and does not modify `.gitattributes`. `ShellElement` remains the default.
SymPy and mpmath are research-only and are never added to production metadata.

## Inherited mechanics

The frozen core is WG2020/WG2004 Hu-Washizu Q4 with `n=7`, `k=0`, source
MITC shear, positive unshifted 2x2 Gauss quadrature, stress14/strain21 ordering,
35 physical-core local variables and three PL multipliers. The stationary
system has 38 fields. Source transformations use the centre Jacobian, with
`j0/j` only on the n=7 enhancement. The multiplier basis is `[1,r,s]`,
`gamma_PL=G`, `epsilon_hg=1e-3`, and thickness is `t=2/3`.

The retained non-affine drill constraint is the centre Taylor operator
`C=[c(0),c_,r(0),c_,s(0)]`; `M=int t P^T P`, `B=M C`, and only the faulty
equal-order `r*s` coefficient is deleted. PL and residual-hourglass energies,
residuals, tangents and diagnostics remain separate from physical N/M/Q
recovery. Direct drilling moments and prescribed drill support rows are
excluded. Physical loads remain in `range(T5)`.

The equation-7 numbered frame, all eight D4 actions, orientation reversal,
`T5`, `QD`, physical/drill projectors, tensor/pseudotensor work maps, PL
pseudoscalar transport, residual gamma reconstruction, `R_star/b_star`, six
rigid fields, patches, KKT support solve, reactions and recovery are unchanged.

## Exact research environment

The plan-stage environment builder accepts only:

- CPython 3.13.9 and pytest 9.0.1;
- `sympy-1.14.0-py3-none-any.whl`, 6,299,353 bytes, SHA-256
  `e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5`;
- `mpmath-1.3.0-py3-none-any.whl`, 536,198 bytes, SHA-256
  `a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c`.

It verifies regular non-symlink inputs, filenames, sizes and hashes; rejects
absolute, `..` and symlink archive members; validates every wheel RECORD hash
and size; extracts into a fresh external directory; and emits canonical JSON
with a sorted extracted-file hash graph and no absolute path. Toy SymPy probes
may run, but shell code and registered geometry may not. Every later runner is
given the environment root and environment-record hash separately. mpmath may
satisfy SymPy import requirements but is forbidden for equality, sign,
interval or classification evidence.

## Exact backends

The reference retains the independent standard-library `Field`/`Alg`
quadratic-tower backend. The independently authored oracle uses SymPy 1.14
`QQ.algebraic_field` domain elements for equality and may not inspect or copy
the Q1S interval oracle or Q1T reference algebra.

For each of the seven geometry groups, the E numbering constructs exactly:

1. `g1=sqrt(d1.d1)`;
2. `g2=sqrt(d2.d2)`;
3. `g3=sqrt((d1/g1+d2/g2).(d1/g1+d2/g2))`;
4. `g4=sqrt((d1 cross d2).(d1 cross d2))`;
5. `g5=sqrt(3)`.

Radicands may be positive elements of the preceding field. Generator order is
fixed and never sorted or extended after an outcome. The second equation-7
tangent normalization is derived from g1..g4; there is no sixth root. All eight
D4 numberings reuse the group field. Maximum formal degree is 32.

Oracle values also carry an independently generated rational-operation /
positive-root expression DAG. Exact equality is only algebraic-field equality
with zero. `evalf`, floats, tolerances, decimal comparison, generic
`simplify(expr)==0`, and interval containment of zero are forbidden equality
authorities. A standard-library outward dyadic engine evaluates the DAG only
for ordered signs at 256, 512 and 1024 bits. A nonzero-width enclosure
containing zero is unresolved; certified negative evidence is a scientific
NO-GO; unresolved required positivity at 1024 bits is UNCLASSIFIED.

## Deterministic local certificate

Construct the exact 24x6 analytical rigid matrix R and require rank six and
`K R=0`. Construct Z as the 24x18 nullspace basis of `R^T` by exact RREF with
leftmost pivots and ascending free-coordinate order. Z depends only on R.
Require exact stiffness symmetry and exact 38x38 mixed/condensed
energy/work/residual/tangent parity. Apply fixed-order no-pivot LDL to
`Z^T K Z`: eighteen positive pivots certify rank18/PSD; an exact zero or
negative pivot is NO-GO; unresolved sign is UNCLASSIFIED.

The common payload has exactly these top-level keys:
`schema,candidate_id,study_id,precision_bits,coverage,frame_and_fields,local_algebra,recovery,global_supports,classification,case_certificates`.
Each ordered case row has exactly
`case_id,geometry_id,operation_id,gauss_station_ids,centre,frame,field_work,local_algebra,patches,recovery,global_support,status`.
Nested values are only IDs, integers, booleans and PASS/NO_GO/UNCLASSIFIED.
Backend expressions, interval endpoints, timings and paths remain outside the
common payload. Canonical payload bytes and SHA-256 must agree across backends.

## Four-stage authority

All JSON is duplicate/nonfinite-rejecting, canonical sorted compact UTF-8/LF.
Reviews have exact keys `findings,reviewed_inputs,reviewer_independence,schema,verdict`.
One plan correction, one static implementation correction and one contract
correction are allowed, each followed by independent re-review. No source,
test, contract or tolerance change is permitted after registered execution.

### Commit 1 — PLAN14

Subject: `docs: preregister E4 PL Q1T exact-oracle completion`.
The exact PLAN14 paths are the governing plan; plan review; baseline;
inheritance, rejected-evidence and allowed-extent manifests; environment record
and builder; exact-backend contract; certificate schema; authority contract;
terminal table; test inventory; and preregistration authority test. No Q1T
implementation, scientific test, result, terminal or Q1B plan may exist.
Required verdict: `ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1`.

### Commit 2 — IMPLEMENTATION11

Subject: `docs: freeze E4 PL Q1T exact reference and oracle`.
The exact paths are reference, oracle, scientific test runner, implementation
manifest/review and the six named test files. Before this commit only AST,
imports, schemas, negative guards, static reachability and the toy backend test
may run; registered constructors must be unreachable. Required verdict:
`ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1`.

### Commit 3 — CONTRACT3

Subject: `docs: authorize E4 PL Q1T scientific execution`.
The exact paths are execution contract, canonical contract review and
non-mechanics contract test. The contract binds Commit 1/2, exact extents,
environment/inheritance/implementation/test hashes, schemas, predicates,
output absences and three guards. Required verdict:
`ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1`.

After Commit 3, the coordinator exclusively creates an external canonical
authority record with exact keys
`schema,authorization,candidate_id,study_id,commit,tree,execution_contract_sha256,environment_sha256,plan_review_sha256,implementation_review_sha256,contract_review_sha256,review_verdicts,runner_ids`.
Every runner receives authority, contract and environment paths plus
caller-supplied hashes, and verifies exact ancestry/extents, clean index and
tracked tree, reviews, environment graph, inventory and outcome absences before
importing mechanics.

### Commit 4 — OUTCOME11

Subject: `docs: close E4 PL Q1T local qualification`.
Run reference twice and oracle twice in fresh external directories; require raw
byte identity within each implementation and common-payload byte identity
between them. Promote reference/oracle raw, agreement and combined output,
then run the five-node scientific inventory once. Tests inspect promoted
evidence and never rerun mechanics. Add status, authority-record copy,
scientific-test result, local qualification report, scientific review,
completion and static closeout test. Required successful review:
`ACCEPT_Q1T_SCIENTIFIC_REVIEW_NO_P0_P1`.

## Inventories and blocked routes

The Q1S baseline inventory is only its one static closeout node. Q1T has four
preregistration nodes, one toy exact-backend node, the five inherited scientific
nodes, four contract nodes (hash DAG plus three negative guards), and one static
closeout node. These inventories are never combined.

`BLOCKED5` is status, `E4_PL_Q1T_LOCAL_QUALIFICATION.md`, scientific review,
completion and closeout test. Exact alternate extents are PLAN14+BLOCKED5=19
from the Q1S closeout, IMPLEMENTATION11+BLOCKED5=16 from Commit1,
CONTRACT3+BLOCKED5=8 from Commit2, authority-record copy+BLOCKED5=6 from
Commit3, or OUTCOME11=11 from Commit3. Rejected stage reviews use exact
`REJECT_*_P1`; blocked honesty review uses
`ACCEPT_Q1T_BLOCKED_CLOSEOUT_NO_P0_P1` and never classifies mechanics.

First-match terminals are:

1. `BLOCKED_E4_PL_Q1T_BASELINE_MISMATCH`
2. `BLOCKED_E4_PL_Q1T_INHERITANCE_MISMATCH`
3. `BLOCKED_E4_PL_Q1T_PLAN_AUTHORITY`
4. `BLOCKED_E4_PL_Q1T_EXACT_ORACLE_IDENTITY`
5. `BLOCKED_E4_PL_Q1T_IMPLEMENTATION_IDENTITY`
6. `BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM`
7. `BLOCKED_E4_PL_Q1T_ORACLE_OR_REVIEW`
8. `NO_GO_E4_PL_Q1T_LOCAL_ALGEBRA`
9. `NO_GO_E4_PL_Q1T_PATCH_OR_COVARIANCE`
10. `UNCLASSIFIED_E4_PL_Q1T_LOCAL_PLANAR_IDENTITY`
11. `PROVISIONAL_GO_E4_PL_Q1T_Q1B_PLAN`

Cross-backend disagreement or a backend defect after execution is terminal 7,
not a mechanics NO-GO. Exact local algebra contradictions map to terminal 8;
exact frame/patch/work/recovery/support contradictions map to terminal 9; only
unresolved ordered signs map to terminal 10. Terminal 11 authorizes preparation
of a separately governed Q1B plan only, not its execution or production use.
Every result retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

No push, merge, publication, cleanup, historical rewrite or Q1B creation is
authorized in this run.
