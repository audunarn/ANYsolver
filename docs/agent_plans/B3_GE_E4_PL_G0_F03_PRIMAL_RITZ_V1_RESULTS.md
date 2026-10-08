# F03 independent primal Ritz reference v1: failed evidence gate

22 September 2026. **All five registered equilibrium processes completed,
but canonical adjudication returned FAILED_EVIDENCE. The reference is not
accepted; G0B remains open and G1 remains barred.** This consumed execution
must not be rerun, overwritten or relabelled.

## Source, contract and execution

Source `e7908c1ad3dcff1cf9bc957ba8fd0fe1fe49b5b5`, integration branch
`codex/b3-ge-e4-pl-integration`. The independent classical polynomial
reference and its evidence harness implement
`B3_GE_E4_PL_G0_F03_PRIMAL_RITZ_PROTOCOL.md`; the original mechanics-review
draft is preserved separately. This is not a native B3-GE/E4-PL owner,
installed-package qualification or a selected production attachment space.

Independent preregistration review granted GO contingent on a clean
source freeze. The observed worktree was clean after the commit. The exact
command was:

```text
python scripts/b3_e4_f03_primal_ritz.py --run-all --root .qualification/b3-ge-e4-pl/f03-primal-ritz-v1
```

All five numerical thread caps were1. Each degree received one equilibrium
solve, canonical polynomial/load integration and the separately frozen
assembly-only integration crosscheck. The sequence was serial. All five
children exited0 with complete raw receipts; the final runner exited1.
Orchestration took60.9037394s. Maximum sampled child RSS was231,493,632bytes
(220.77MiB). These are diagnostic resource observations, not performance
qualification or a guarantee about unsampled memory peaks.

| Degree | Primal coordinates | Child time s | Sampled RSS bytes | Child exit |
|---|---:|---:|---:|---:|
| 4 | 30 | 1.4153 | 44,679,168 | 0 |
| 8 | 126 | 2.6204 | 47,464,448 | 0 |
| 12 | 286 | 5.6319 | 55,046,144 | 0 |
| 16 | 510 | 11.4165 | 84,152,320 | 0 |
| 24 | 1150 | 37.2047 | 231,493,632 | 0 |

## Evidence failure and separate numerical findings

Every canonical case decision is FAILED_EVIDENCE, reporting
`ValueError: reference metric value changed`. A saved-only diagnosis of
degree4 found the path `details/perturbation_delta`: JSON reload produces
a Python float, while recomputation returns NumPy float64. Their numerical
values are exactly equal. The comparator's exact Python type check fails
after serialization, although the in-child comparison of two NumPy values
passed. This is an evidence-comparison defect; it does not establish any
physical acceptance.

Separately, the raw child reports contain numerical failures that must
survive any corrected evidence audit:

| Degree | Child-reported saved-action defect | Registered limit | Reported numerical outcome |
|---|---:|---:|---|
| 4, 8, 12 | Within the limit | 1e-11 | No reported failed predicate |
| 16 | 1.490569246047816e-11 | 1e-11 | Failed saved-action consistency |
| 24 | 1.153325509593225e-10 | 1e-11 | Failed saved-action consistency |

Independent saved-only review reproduced these predicates exactly.
Both failed components are the reconstructed transverse second derivative
at s=1. Physical discrepancies are8.0040e-15 and7.5026e-14 per metre,
respectively. Other derivative bindings pass, and all non-derivative
saved-action discrepancies are zero. Endpoint differentiation amplifying
projection roundoff is a plausible explanation, not an exemption from
the frozen limit. Correcting Python/NumPy numeric comparison cannot erase
the failures. Physical trend adjudication was not reached. No claim is made that
the reference converged, that existing finite-element families agree with
it, or that increasing degree would resolve the failure.

## Verification and review scope

The first integrated unit run passed51 checks. Following review findings,
23 focused operator/check tests passed and48 affected evidence/integration
tests passed. These inventories overlap and must not be summed.

Review corrections before execution included root-traction sign and tip
units, positive scaling identity, independent pose-derivative action
binding, completed-receipt consistency, and explicit numerical failure
semantics. Undefined diagnostic norms retain validity flags and cannot
pass; physical state and operator arrays remain finite.

The missed regression was JSON round-trip of actual computed metric types.
The comparator is now corrected to compare real-number values while
rejecting booleans and nonfinite values. Its existing1e-12 numerical
comparison is unchanged, and failures identify their exact metric path.
Twenty-five affected tests passed, including real computed metrics through
JSON serialization. Independent reviewer `/root/f03_port_mechanics`, who
did not implement this comparator, accepted that scoped correction.
Log: `.pytest_cache/primal-json-fix-6587570a6e2d4823a18746a43517b2bf.log`.
No mathematical operator or acceptance threshold changed.

Postexecution reviewer `/root/finite_pad_axis_review` accepted raw
integrity and retained HOLD on reference acceptance. The review verified
nine frozen source hashes, all five raw receipt/event chains and215 finite
arrays. Every recomputed metric matches the saved JSON numerical value
exactly. Assembly, pose-construction, equilibrium-solve and recovery entry
points were disabled during that audit. Audit tool chunk `cde66f` exited0;
an attempted scratch transcript write was denied, so the tool transcript
and reviewer messages are retained in parent-recorded provenance.

The reviewer separately evaluated physical settling as a diagnostic,
without replacing canonical adjudication. Final total-energy changes are
4.5247% and2.6019%; full-functional changes are2.8744% and3.1574%, with
absolute differences18,368.1N and19,955.7N. Only16/45 scalar sequences
pass. Nested energy identities have maximum scaled defect1.31e-16.
Thus physical convergence also remains unresolved even apart from the
two numerical failures. These diagnostic findings are not a new accepted
reference decision.

## Immutable evidence and next action

Root: `.qualification/b3-ge-e4-pl/f03-primal-ritz-v1`.

| Record | SHA-256 |
|---|---|
| Registration | `4a8cdf3a77d561c2d8bd3bcdaf59d7df8b1a67e731505ad6f9ac05f52b6bb65e` |
| Adjudication | `3a079523bd3c4329135c8a445962e39fc3031ade42d74c72c93b8c036f54cf09` |
| Orchestration | `454c7049977b44634ea83dd9183adab3354a010e16d1bba649256e4016f2d737` |
| Independent review | `ad3390d5f0fb048f205a9710ebcf8dbb4133918a5e9f176033e5bd01eefbcb34` |
| Execution provenance | `e8a0424c957880a37cfc38d91c2c4c19c089bf8108f552a7fa32ad0cd5e7d8db` |
| Completed inventory | `c89cd28009a193b611fe24e3d98add868f3fc62f9b719f7915d7f0a80823157b` |

The completed inventory binds36 files. Preserve this failed canonical
result. The JSON numeric-comparison correction has its own tested and
independently reviewed source change. Any further
formal use of the saved states requires a separately reviewed, versioned
read-only audit binding these exact raw files. It must retain the original
FAILED_EVIDENCE and any reproduced numerical failures; it is not permission
to consume the five equilibrium cases again.

Diagnose the saved-action failure before changing the reference evaluator.
Do not relax the registered tolerance, extend the degree series
automatically or advance to finite-element comparisons/native integration.
Main remains unchanged at the accepted0.4.7 baseline.
