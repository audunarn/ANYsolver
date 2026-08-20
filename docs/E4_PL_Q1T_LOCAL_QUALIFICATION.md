# E4-PL-Q1T contract-authority blocked closeout

## Outcome

E4-PL-Q1T stops at
`BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM`, precedence 6. The PLAN14 and
IMPLEMENTATION11 gates remain accepted and content-addressed. The independent
execution-contract review rejected the proposed CONTRACT3 packet with four
priority-one findings, so Commit 3 was not created and scientific execution
was never authorized.

This is a contract-authority block, not a mechanics GO, NO-GO, or
UNCLASSIFIED result. The scientific classification is `NOT_ESTABLISHED`.
Candidate
`candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1`
remains `DORMANT_UNQUALIFIED`. Q1B plan preparation and execution are not
authorized. Production remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, and
legacy `ShellElement` remains the default.

The canonical blocked status is 6,178 bytes with SHA-256
`0A718447DDB1AAC9399A5E395E902329D420372024483F612CF67391B2EAE088` at
`docs/reference_cases/e4_pl_q1t_status.json`.

## Exact accepted authority

The mandatory base is Q1S blocked closeout commit
`914a9a633c585d45a419d97f92b4faf7fa1e4486`, tree
`569c0b15c9e5d50835fa5fe16414d5d1864d0106`, with parent
`00d6a66c34712c8f3fd1e38113c83d0a03b2de43` and exact subject
`docs: close E4 PL Q1S implementation-identity block`.

Q1T Commit 1 is
`658619184d354401f55fc7a6640a4770d900ded7`, tree
`c4b9d5ef80779ba26912bbb2d53e5d547a47c629`, with the mandatory base as
parent, exact subject `docs: preregister E4 PL Q1T exact-oracle completion`,
and exact PLAN14 extent. Its independent review verdict remains
`ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1`.

Q1T Commit 2 is
`083044167f9826e9868851c2709017112bc7553d`, tree
`3b52b601e509b1348145cffdb40cb1d478b9227f`, with Commit 1 as parent, exact
subject `docs: freeze E4 PL Q1T exact reference and oracle`, and exact
IMPLEMENTATION11 extent. Its independent review verdict remains
`ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1`. The accepted plan and static
implementation identities are preserved; the contract rejection does not
rewrite or demote either accepted gate.

The canonical status records every path in PLAN14 and IMPLEMENTATION11. No
path is dynamically substituted.

## Rejected CONTRACT3 packet

The proposed execution contract is 26,735 bytes with SHA-256
`473A36EBCA88B553F068DD19CAC0AB112632BEAEB96ECE77672CAEB03F57E062` at
`docs/reference_cases/e4_pl_q1t_execution_contract.json`. The non-mechanics
contract test is 6,300 bytes with SHA-256
`3BBC0B0A47AF511A5686D0321035B1F372AA4BE5BB5724E043A12BCC9C07EFD6` at
`tests/test_e4_pl_q1t_contract.py`.

The independent rejection review is 2,411 bytes with SHA-256
`5D5359EC96158455A3CF86C0C137400FEB714573910F49AD064CCBD0EB15356A`
at `docs/reference_cases/e4_pl_q1t_contract_review.json`. Its exact verdict is
`REJECT_Q1T_EXECUTION_CONTRACT_P1`.

The four priority-one causes are:

1. The committed scientific runner requires `environment.path`, while the
   contract, reference runner, and oracle runner require
   `environment.record_path`. An authorized scientific run would fail before
   environment-graph verification.
2. The committed scientific runner requires
   `BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD`, while the contract and both
   mechanics runners require
   `BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD`. Its authority guard cannot
   accept the proposed contract.
3. The oracle and scientific runners do not verify the exact
   `reviewed_inputs` and `reviewer_independence` content required for every
   stage review; the scientific runner also does not require empty findings.
4. The contract hash-DAG test omits required exact assertions for nested
   schemas, Commit-1/2 ancestry and extents, inherited Git objects, review
   content, runtime, terminals, agreement, production boundaries, and the
   prospective CONTRACT3 commit.

These are contract and pre-mechanics guard defects. They do not establish any
registered element rank, patch, covariance, recovery, support, reaction, or
stability result. Because the affected runner and oracle sources are frozen
in accepted Commit 2, the rejected contract packet cannot authorize execution
without violating the staged identity.

## Evidence disposition and repository boundary

The proposed contract, rejection review, and contract test are retained only
as rejected contract-stage evidence in the preregistered
`CONTRACT3_UNION_BLOCKED5` route. That route has exact parent Commit 2 and
exact path count eight. It does not create an accepted Commit 3.

No external or committed execution-authority record, registered process, raw
reference or oracle output, agreement, combined output, scientific-test
result, scientific mechanics classification, or Q1B plan exists. No absent
artifact is fabricated.

There is no `.gitattributes`, `src/`, `.github/`, dependency, package,
workflow, public API, selector, serialization, dispatch, recovery,
production-test, export, or default change. No push, merge, publication,
cleanup, historical rewrite, or Q1B work is authorized.
