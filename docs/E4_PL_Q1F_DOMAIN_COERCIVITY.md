# E4-PL-Q1F Domain-Coercivity Status

Q1F closes at `BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW` under first-match precedence 1. The required plan review rejected the packet, and premature implementation drafts had been created before accepted plan authority. The underlying technical finding remains `BLOCKED_E4_PL_Q1F_REDUCTION_IDENTITY`; it does not displace the earlier authority/review terminal.

## Bound authority

The blocked record is based on commit `61195c18a704438b4b3cf66e6e93d7839723b0fb`, tree `1249c9e9280d626c11c7194c1f2f5b164e5d99b7`. It binds the seven corrected preregistration inputs by byte count and SHA-256 in `e4_pl_q1f_status.json` and the independent 2,273-byte plan review with SHA-256 `DD3721F9E6C3CEC20E0C57B815467B695F37139DE444F9A9623790E511BB9891`.

The review verdict is `REJECT_Q1F_COERCIVITY_REDUCTION_P1`. The single finding is `P1_TRANSLATION_RIGID_MATRIX_CONGRUENCE`. The plan correction budget was one, and that one correction had already been used. Because the review did not accept the plan, the implementation stage was never promoted.

## Exact contradiction

The frozen rigid columns are ordered as three translations followed by three rotations. At node coordinates \((x,y)\), the rotational columns contain

```text
R1 = [0,0,y, 1,0,0]
R2 = [0,0,-x, 0,1,0]
R3 = [-y,x,0, 0,0,1]
```

After translating the geometry by \((c_x,c_y)\), these columns become

```text
R1' = R1 + c_y T3
R2' = R2 - c_x T3
R3' = R3 - c_y T1 + c_x T2
```

Consequently, the preregistered matrix identity

```text
R_raw = T_Q S_scale R_gauge
```

is false. Only the range identity is invariant unless a nonsingular 6-by-6 translation-dependent rigid-column basis change is included:

```text
range(R_raw) = range(T_Q S_scale R_gauge)
```

For column order `[T1,T2,T3,R1,R2,R3]`, the omitted basis change has the identity matrix plus entries `B[T3,R1]=c_y`, `B[T3,R2]=-c_x`, `B[T1,R3]=-c_y`, and `B[T2,R3]=c_x`; its determinant is one. The governing reduction contract did not freeze this matrix or formulate the quotient solely through the invariant rigid range. That satisfies the underlying precedence-2 reduction-identity predicate, but the rejected required review and premature stage activity already select precedence 1.

## Premature draft disposition

Eight premature, unpromoted drafts were created. Static draft tests were executed and recorded `2_PASSED_IN_2_42_SECONDS`; no scientific mechanics was executed. The eight files were moved intact outside all Git authority under the external sibling staging label `EXTERNAL_SIBLING_Q1F_IMPLEMENTATION_DRAFTS`. Their preservation policy is `NOT_AUTHORITY_DO_NOT_PROMOTE_OR_EXECUTE`.

The preserved identities are:

```text
e4_pl_q1f_bounded_runner.py       9390  F225DE8E8F9354007CF3AE733B8871D56789CB20AD7754489A715FC273674A6B
e4_pl_q1f_common.py              19330  1F1A751A1BFC3FA7EC40A254443EA3FF4BB6F654192E0A2E1D03B170B870017A
e4_pl_q1f_domain_checker.py       3270  DC451EBC0B91E58F6E3A43C8D376F166ED954B66275DD614C1F375BFD561A53A
e4_pl_q1f_domain_producer.py      3711  4836A4F58F51A4EBD3AAE4DA6B15EE13AA0455A916517CE0BD83AC0714196703
e4_pl_q1f_reduction_verifier.py   9508  7CF74C57C0B9EFC2B608FC275C3D166106CBE6C5631233E1FD63553217112420
test_e4_pl_q1f_interval_proof.py  1552  438211EFD61AE68129784A01CD3F156129FA060DC053A13A3AA49B9F966B4C8E
test_e4_pl_q1f_reduction.py       3171  640BF4908055154DCD6FFE9171377A2A5B93AFE0BE9BD7B2205E98A5026337F7
test_e4_pl_q1f_runner_bounds.py   4042  B9BD8AC3482AB12F7AEC48194A940CF811EDF58A1186822B82C9525792A5704F
```

All Q1F implementation-stage paths are absent from the current Q1F worktree. No execution contract, registered interval proof, scientific mechanics, scientific outcome, or Q1B integration was created or run. The external drafts are preservation evidence only and are not part of any Q1F authority chain.

The prospective blocked closeout is the exact 13-path `PLAN_BLOCK` commit with parent `61195c18a704438b4b3cf66e6e93d7839723b0fb` and subject `docs: close E4 PL Q1F authority-review block`.

Production restrictions are unchanged: `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`. Legacy `ShellElement` remains the default.
