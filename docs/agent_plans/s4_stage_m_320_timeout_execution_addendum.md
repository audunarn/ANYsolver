# S4 Stage-M 320-digit shard timeout execution addendum

Status: plan-only execution amendment; no scientific result and no production authority.

## 1. Authority and frozen boundary

This addendum is subordinate to `docs/S4_STAGE_M_MECHANICS_SELECTION_PLAN.md`
(raw SHA-256 `4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B`)
and changes only the caller deadline for the two 320-decimal-digit precision
workers. The user has transferred execution approval to this task and has
explicitly removed the PERF-lease requirement.

The following accepted inputs remain byte-frozen:

- cases: `912E07377C174E1FE031EEBA98DD5E8406C9A294AF2B3032D9AB5B38F67C7B94`;
- oracle: `1B123591388AE73E83E3BA7082E82D0A579BE856669D461AA500BF41FE772D48`;
- contract: `2FBB419F0C09D909F2B6A1D4FF77285EB078E8A6E7DB10286ECC47282D1F90DA`;
- interval module: `05C086DB11548AA4B77A5B31A5171792E08C053F93682D5FBED2D16425C16CC3`;
- energetic derivation: `ACD03B67474BF35A06B2183830E3195843D4254DB17F04A5540724F42EC9F3A5`;
- constrained record: `577BD98FC5609629BC078B27719ED72985E4BA81536A7C6D76CBA687322D5488`.

No equation, fixture, precision, multiplier, quadrature rule, tolerance,
classification, coverage row, environment identity, terminal precedence, or
output schema may change under this addendum.

## 2. Observed operational boundary

The accepted sharded wrapper completed and atomically preserved:

- `set1_080.json`: 892,218 bytes, SHA-256
  `986679725F248E282FBA91F0A8CD72BA170CA6781C8EEF73C9454A7E1923EC5F`;
- `set1_160.json`: 1,086,218 bytes, SHA-256
  `74B824A14C4E4ACDF898FD11FC2FD7BCA09B7DA07B3BC94E8A11CDD817A834D1`.

`set1_320` then reached the exact 7,200-second caller deadline. The worker was
terminated and reaped; no stdout packet, final shard, pending shard, merge,
completion manifest, or scientific result was produced. The two completed
shards are immutable qualification evidence and must be validated and reused,
never rerun, overwritten, deleted, or cleaned.

## 3. Sole executable change

After independent acceptance of this addendum, edit only
`tests/test_s4_stage_m_mechanics.py` so the wrapper selects the caller timeout
by precision:

- 80 digits: 7,200 seconds;
- 160 digits: 7,200 seconds;
- 320 digits: 14,400 seconds.

The cases file continues to record the original 7,200-second shard boundary;
the wrapper must still validate that frozen value. This addendum supersedes it
only for the two literal 320-digit subprocess calls. The oracle, cases,
contract, and already completed shard identities therefore remain unchanged.
The merge deadline remains 300 seconds.

The wrapper must record no timing, PID, set, or path data in a shard. The
increased deadline is operational only and cannot affect canonical shard bytes,
the dps-320 merge context, scientific summary, or terminal decision.

## 4. Resume and stop rules

Resume through the same exact opt-in pytest node. Its existing prefix validator
must re-read and validate the two completed shards before starting the next
missing literal path, `set1_320.json`. Continue serially through set 2 and both
merges only after each predecessor validates. Preserve the existing
no-overwrite pending/fsync/atomic-promotion, byte-equality, environment, identity,
and COMPLETE-last gates.

If either 320-digit worker reaches 14,400 seconds, or any identity, environment,
schema, canonical-byte, prefix, process-reaping, or transport check fails, stop
without further execution. Preserve all completed and partial evidence; do not
tune science, extend the deadline again, clean, merge incomplete data, or claim a
Candidate-B scientific terminal without a separately reviewed amendment.

## 5. Scope exclusions and closeout

This addendum authorizes no production source, selector, export, solver,
assembly, activity, nonlinear, buckling, recovery, batch, dependency, branch,
push, publication, cleanup, Candidate-A, or CalculiX/PrePoMax change. Candidate B
remains comparison-only and cannot resolve the overall
`BLOCKED_PRIMARY_SOURCE_UNAVAILABLE` Stage-M status.

After the two deterministic shard sets and merges complete, materialize the
accepted merged packet, bind its raw SHA-256 in the wrapper, run the registered
focused/default gates, write the selection report, obtain independent read-only
closeout, and commit only the registered proof paths plus this addendum.
