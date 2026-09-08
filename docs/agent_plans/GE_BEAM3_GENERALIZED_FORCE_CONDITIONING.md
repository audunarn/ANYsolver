# Current generalized nonlinear force conditioning diagnosis

Base `6ad3f7cfa7a16197b5903a0ba32de1a14d5aaa6d`.
The paired modal repeat gate passed. It does not establish force/Newton
conditioning. This research-only diagnostic exercises the actual native
generalized distributed-load program, not the older retained-state program.
No production operators, tolerances, loads, defaults or historical tests change.

Freeze the same one-macro straight/curved family and coupled elastic sections
as the modal slenderness diagnostic: nominal ratios 100, 10,000, 1,000,000;
identity and common rotation Exp(0.4,-0.3,0.2). Twelve ordered cases.
Use spatial reference-length force density (0.005,-0.003,0.002) and couple
density (0.002,-0.001,0.003), both transported by the common rotation.
The existing ellipsoidal law remains elastic for these intended small loads;
the diagnostic does not claim plastic or continuum-reference qualification.

Use the actual two-step, 24-iteration native distributed solver. Observe the
unchanged operator without modifying its inputs or returns. Save exact inputs,
progress and the last supplied operator evaluation. On an exception or
non-completed result preserve the failure and fail the test: no xfail, no
classification of a diagnostic capture as scientific success. Successful cases
must retain unchanged model/virgin input, pass current free/internal 1e-11
equilibrium and unchanged accepted-state recovery. Compare common-frame
covariance only when both original and transported cases genuinely complete.

Execute straight identity ratio100 as a smoke before any remaining cases.
If the smoke fails, stop the wave and diagnose its captured state; do not
automatically run larger ratios. If it passes, at most three simultaneous
fresh-directory workers may run the remaining eleven cases. Each child has
one numerical-library thread, 24GiB, 600 seconds and 120-second CPU inactivity;
the diagnostic wave is bounded to 1,800 seconds. No automatic retry. Guards
bind clean source/Python/runtime versions before and after every worker.
This version check is not complete environment-graph attestation.

Failure is actionable evidence for a formulation-preserving numerical successor
or a source-level defect diagnosis, not authority to relax tolerances. Preserve
all previous dense/paired modal and retained-state evidence. A successful small
diagnostic still leaves nonlinear reference engineering, full material/fibre
parity, broader postbuckling, packaging and objective shell connection pending.
Independent review PENDING; production qualification false.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
