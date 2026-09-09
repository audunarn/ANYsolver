# N32 branch completion with validated local-operation scheduling

Successor of 08dfe7e6b7851bf871620e45b77f16d1d710db25. Preserve failed original
branch wave b2d15e2 and its archive without reclassification. No mechanics,
targets, tolerances, iteration, backtracking, seed, load or checkpoint schema changes.

Optimization acceptance: 61 tests passed in 26.25 seconds, including actual
cancellation before/after commit, load/reverse/restart byte equality and mutations.
Bounded N32 replay measurement at
`C:/Users/AudunArnesenNyhus/AppData/Local/Temp/ge-beam3-scoped-replay-08dfe7e-20260909`
completed in 9.446395 seconds (predecessor control 53.537046 seconds), peak tree
195047424 bytes. Full physical guard count reduced from 15877 to 421. Exact
checkpoint and state hashes equal preserved predecessor outputs. These are paired
diagnostic measurements, not a general statistical performance claim.

Run the original GE_BEAM3_N32_EXTENDED_BRANCH_GATE.md programme exactly: original
signed seeds at +/-0.0065; targets +/-(.0075,.010,.015); four signed replicas;
23 registered enrollment, advance, cancellation/resume and final replay workers.
Use original native Context/solve/restore and all original adjudication functions.
Only add the explicit GE_BEAM3_LOCAL_OPERATOR_VALIDATION_BOUNDARY_V1 scope.
The scoped worker writes a policy sidecar after the original worker completes.
Do not use profiling wrappers in scientific execution.

New exclusive root and new source commit; original failed worker IDs are consumed.
Smoke plus-a enrollment/target one first. Then the other enrollments/target one;
four target-two and target-three workers; positive before/after commit cancellation,
resume the actual before-cancel capsule; final fresh-owner replay of all four.
At most three concurrent workers, one numerical thread, 600 seconds/24GiB per
process tree, 120-second native context and CPU-inactivity, 1800-second wave.
On failure wait for already launched workers, preserve their genuine accepted
prefixes and do not launch dependent later stages. No automatic retry.

Require same-sign byte-identical complete output extents, including policy.json.
Require final replay checkpoint/state and recovery identity, and actual cancellation
and resume equality against ordinary accepted prefixes. Require accepted first-target
checkpoint bytes to match the preserved failed-wave successes. All 23 workers must
be terminal before an aggregate. Keep logs/timings externally, and record production
qualification, path-from-rest and independent-author review as false.

This completes branch lifecycle only if all gates pass. It cannot replace the
remaining independent reference/stability and production integration/parity review.
Existing B2/B3/Q4/S3/defaults and historical evidence remain unchanged.
