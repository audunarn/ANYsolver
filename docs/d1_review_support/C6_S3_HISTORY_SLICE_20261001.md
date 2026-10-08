# C6 guided S3 load-history slice — 1 October 2026

Development authority: resumed full programme; prospective risk-proportionate
process. Historical frozen authorities and acceptance boundaries remain unchanged.

## Question and decision

Extend the existing guided elastic single-S3 descriptor Newmark route to a
piecewise-linear dead nodal load history, using the existing history, knot split,
work, and restart infrastructure. This closes a named D5 implementation gap;
it does not admit general S3 dynamics, plasticity, tools, or free bodies.

For algebraic basis Z, admit the complete base load only when Z.T f_base=0,
including when its initial scale is zero. Then G(q,t)=Z.T F_internal(q) is
independent of the scalar history: existing algebraic velocity/acceleration
recovery remains applicable. Time-dependent algebraic forcing is rejected.
Use a distinct development profile for S3 history; unchanged constant-load
S3 and Q4 callers retain their identities. Restart binds history and profile.

## Ownership

Mistral Edit: src/anysolver/general_contact/transient.py and one new focused
tests/test_general_contact_transient_s3_history.py. No other edits or numerical
execution; the other programme currently owns the numerical slot.
Lead: this note, plan/restart/ledger/docs, integration and supervised verification.
Independent reviewer: resulting equations, implementation and tests; no authorship.
No commits, branch changes, shared exports, guard or application dispatch edits.

## Checks and stopping rule

Add independent uniform free-flight analytical ramp checks, history-knot split
restart parity/work, and rejection of an algebraic base load hidden by zero
initial scale. Exercise active contact with existing independently derived
mass-spring/reference machinery where feasible. Preserve physical offset,
descriptor rates, endpoint and declared cubic-path checks. Run focused changed
checks once the numerical slot is available, under 180s/1GB/thread1/JIT-off.
Failure leads to one cause-specific correction; no automatic cap increase.

After integration, add cancellation using existing token/state-cleanup machinery
as the next bounded slice. Cancellation must not introduce arbitrary callbacks
into prepared-model evaluation. Broader C6 remains open.
