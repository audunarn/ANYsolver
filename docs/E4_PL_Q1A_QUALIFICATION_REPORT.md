# E4-PL-Q1A aborted authority report

## Outcome

E4-PL-Q1A stopped before accepted preregistration with terminal
`BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY`. This is not a scientific no-go for the
source formulation. Candidate
`candidate_e4_pl_q1.wg2020_n7_k0_surface_pl_planar_linear_iso_v1` remains
`DORMANT_UNQUALIFIED`, Q1B is not authorized, and production remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED` with legacy `ShellElement` as the
default.

The canonical blocked status is 2,756 bytes with SHA-256
`97BC2D3F20D5D6B0DC2A8C7273CAB7A3BFAF97672FD3385B656843F2617233F9` at
`docs/reference_cases/e4_pl_q1a_status.json`.

## Why the program stopped

The independent preregistration review returned `REJECT_NOT_ACCEPTED` after
the sole correction cycle. It identified two remaining priority-one defects.

First, the D4 comparison action was not source-closed before execution. The
attempted oracle kept a fixed common frame for proper D4 operations and used
one reflected-frame repair for improper operations. WG2020 equation 7 instead
constructs the local frame from the numbered element diagonals. Renumbering
can therefore rotate or swap the source frame. The geometry contract did not
uniquely freeze the numbered-frame reconstruction, component transport,
multiplier transport, reversal action, and comparison frame before outcomes.

Second, the program required an accepted plan-only review and a first
preregistration commit before scientific execution. Exact mechanics were run
and observed covariance counts were written into intended input artifacts
before either barrier was satisfied. A later review cannot retroactively make
those artifacts preregistered.

Because plan authority precedes source and mechanics terminals, the accepted
terminal is `BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY`. The unclosed source-frame
action is retained only as subordinate cause
`BLOCKED_E4_PL_Q1A_SOURCE_OR_PLANAR_IDENTITY`.

## Nonclassifying correction-cycle evidence

For audit and successor design only, the attempted reference and independent
oracle agreed on conditional local-algebra results under the supplied
fixed-frame surrogate. The following records are explicitly
`NONCLASSIFYING_CORRECTION_CYCLE_EVIDENCE`:

- exact affine E4-0 reproduction and conditional 38-field invertibility;
- `R` rank four, positive `Kdd`, and the local drill Schur identity;
- conditional total rank 18 and nullity six;
- physical patch, recovery, support/projector, and 17-row DNV material-interface checks;
- canonical process agreement SHA-256
  `E2AB0103721712E610D203BA4A2649BBE86E8FDC4B8061BA8A9FBF8056C73BF5`;
- exploratory D4 counts 8/8, 4/8, 4/8, and 8/8 for the square,
  affine-skew, trapezoid, and tapered-skew cases under that surrogate action.

These observations cannot establish the source identity, classify covariance,
support a candidate GO or NO-GO, or authorize Q1B. No caller-bound contract or
canonical scientific output was created.

## Evidence and commit boundary

The aborted authority record was preserved in local commit
`0435fae39d02e6f3c946deba0b74f29522f90137`, tree
`13be1c75de0ae058b30e5e0d41188769d71df638`, with parent exact base
`97c3150c9ecd41cf42fc108e9ff476497154428c`. Its plan review is 9,561 bytes,
SHA-256 `342148665F7CA735335DC8BE7E824B2A98D9A5FACFEC2158BFEF8195926AC310`,
and verdict `REJECT_NOT_ACCEPTED`.

This first commit is deliberately named as preservation of an aborted
authority record, not as the preregistration commit requested by the rejected
program. The second local commit closes the authority block. That distinction
prevents the Git history from implying that science ran after a successful
preregistration.

The accepted E4 status, review, conditional plan, and detached 20-test record
remain unchanged. No `src/`, package, workflow, API, selector, serialization,
dispatch, production test, recovery implementation, or default changed. The
six historical evidence roots were neither staged nor cleaned.

## Successor boundary

A future study must use a newly preregistered identity, freeze the WG
numbered-frame reconstruction and every D4/reversal transport before any
mechanics execution, obtain an accepted plan-only review, and commit its
caller-bound inputs before running an oracle. This blocked closeout does not
itself authorize that successor.
