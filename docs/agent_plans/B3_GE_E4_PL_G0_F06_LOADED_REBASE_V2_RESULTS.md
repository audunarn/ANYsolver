# F06 v2: S3 numeric parity; Q4 state-path diagnostic failed

21 September 2026. Frozen source/contract `846ab225e64f0a8c3d531a9d37070a268c5f4226`.
Exclusive one-time raw root:
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/g0b-f06-loaded-rebase-v2/`.
SHA-256: `manifest.json`
`245ecc70d1b386a2faf4eefd71deef786fc5664360a4ca7bb2b1364e08fd9b97`,
`results.jsonl`
`c46e93c630b0ace3943cf756268519bcc8089012bac6e4a2158d4090576acda6`.
The runner exited `1` and retained all four typed records. This is a
failed exploratory experiment, not F06 or G0B acceptance.

Both loaded S3-V2D cases passed the registered numeric representation
checks with nontrivial shell rotations (norm approximately `.0025949`),
nonzero stress/strain state and unchanged accepted checkpoint. Largest
reported shell spatial tangent discrepancy was `1.63e-17`; supported
reaction parity was `0` and full loaded residual discrepancy at most
`6.22e-20` under the registered aggregate, mixed-unit numerical scale.
These are evidence about a local alternate chart description of the
existing accepted state, not evidence of an owner rebase operation.

Both Q4 cases recorded `ValueError: shell candidate numeric state lacks
matched nontrivial paths` at the whole numeric-state comparison. Because
the frozen source did not distinguish path mismatch from a zero/small
numeric norm in that error, the raw records do not establish which
predicate failed. No Q4 metrics were emitted. Do not infer a mechanics
violation or a successful Q4 rebase from this result. A new diagnostic
must report those predicates and compare physically meaningful material
fields while retaining the failed v2 evidence. Independent post-run
read-only audit matched the frozen source and raw hashes and all four
records. It traced the likely Q4 cause to the qualified elastic shortcut,
which returns a virgin all-zero candidate history even when shell force
and tangent are nonzero. The v2 record itself does not disambiguate the
two predicates; v3 must explicitly separate them and qualify that
elastic policy rather than weaken an active material-state requirement.
