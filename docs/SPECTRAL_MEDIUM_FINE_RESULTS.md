# Medium/fine spectral gate — working results

Status: successor validation/cancellation optimization accepted for the
retained medium-panel buckling target. The earlier immutable-name-only
prototype remains rejected historical evidence.
Baseline solver `5883ae1d7ad1b5abea3a660cc8feecc7e65c7154`; adapter
`a377448dc235463b624226dd230f2fdb849acdd0`. Raw records are retained under
`C:\Github\ANYsolver\.tmp_spectral_medium_fine`.

## Panel observations

One numerical thread, five modes. These are single screening samples after
warm-up, not seven-pair benchmark medians. Geometry preparation is excluded.
Modal values time the solver call; buckling values time the real runtime adapter
including the static phase. Do not compare their scopes as equivalent workloads.

| Route | Shells / beams | First measured analysis | Retained analysis |
| --- | ---: | ---: | ---: |
| Medium panel static + buckling | 1,148 / 515 | 9.846 s | 5.442 s |
| Fine panel static + buckling | 2,160 / 722 | 18.690 s | 11.249 s |
| Medium panel modal | 1,148 / 515 | 2.902 s | 2.816 s |
| Fine panel modal | 2,160 / 722 | 5.541 s | 5.170 s |
| Medium cylinder static + buckling | 2,400 / 1,025 | 25.928 s | 25.967 s* |
| Fine cylinder static + buckling | 4,800 / 1,500 | 55.614 s | 56.292 s* |

*Cylinder end lids make the retained runtime context ineligible. This is a
repeated full analysis, not a cache-reuse measurement. The corrected effective
fixture includes 100 kPa pressure and the runtime GUI's 30 MNm default moment.

Retained medium/fine buckling validation: 1.263 / 2.562 s; geometric assembly:
0.539 / 1.029 s; factorization lookup/reuse: 0.0034 / 0.0056 s. Retained
medium/fine modal validation: 0.656 / 1.157 s; residual batches:
0.00076 / 0.00138 s; eigen iterations: 0.211 / 0.494 s.
Phase measurements need not sum to end-to-end runtime: wrapper guards and
other work are outside some existing phase timers.

Separate profiles confirm repeated qualified authority inspection remains
dominant. The older buckling profiles cover four analyses; the modal profiles
cover only the final retained analysis. Instrumented elapsed times are NOT
used as speed measurements and nested cumulative costs must not be added.

## Failure and review ledger

- Initial cylinder snapshot extraction lazily imported the GUI through missing
  optional load fields. Its two timed-out attempts remain preserved.
- The corrected coarse cylinder diagnostic finished. The corrected medium
  attempt logged a native access violation while a periodic stack dump was
  active, completed solve records but did not exit. It was terminated and its
  coordinator recorded failure. None of these records qualifies the cylinder.
  The stack dump is a suspected contributor, not a proven root cause.
- Successor runner removes asynchronous recurring stack dumps, suppresses
  Windows crash dialogs, rejects fatal logs, records process descendants and
  fails closed when memory/process inspection or cleanup is uncertain.
- Independent review found the cylinder fixture also omitted the runtime GUI's
  30 MNm default moment. Correct effective load selection before accepting
  cylinder buckling measurements. This is corrected and ten harness tests
  pass. Zero-moment observations remain diagnostic.
- Medium cylinder modal diagnostic `04` was stopped explicitly after several
  minutes of CPU activity without a first mode. No result was promoted and
  fine-modal escalation is withheld. This is not a 600-second timeout or proof
  of an eigensolver defect; locating its active phase remains a separate task.
- A bounded entry-only diagnostic observed cylinder modal dispatch with shape
  13,962 x 13,962, K nnz 631,988, M nnz 129,066, no shift, and
  `use_zero_shift_inverse=false`. The production branch therefore selects
  unshifted `eigsh(which="SM")`. No eigen iterations or modes were accepted
  from this probe. Its deliberate abort is caught by the solver and returns a
  failed result; the diagnostic's outer success expectation was not met.
  The earlier monkeypatch-based probe was rejected by numerical-authority
  checks and remains preserved. Neither probe weakens production guards.
- Parent verification: 116 focused validation/state-safety tests passed;
  eight runner tests passed. Independent source review found no guard-safety
  regression in immutable captured-class-name preparation.

## Three-pair screen and acceptance

Frozen harness/candidate `e9fc46e`; serial order B/C, C/B, B/C; five modes,
medium panel complete static-plus-buckling. Each process performs cold and
retained warm-ups before its samples. All six processes completed.

| Measurement | Baseline median / MAD / p95 | Candidate median / MAD / p95 |
| --- | ---: | ---: |
| First analysis | 9.8098 / 0.0161 / 9.8243 s | 9.6596 / 0.0233 / 9.9192 s |
| Retained analysis | 5.4851 / 0.0759 / 7.0156 s | 5.2876 / 0.0175 / 5.4135 s |

Median reductions: 1.53% first analysis; 3.60% retained. Three samples are a
screen, not a confidence interval or a reliable population-tail estimate.
The third retained baseline sample was 7.1856 s; it is not discarded and its
cause is not established. Each pair's eigenvalues were identical; full
five-mode subspace singular-value defects were at most 3.34e-15 and recorded
mode residuals at most 3.12e-14. This is not a substitute for the full frozen
physical-result, constraint, clustered-mode and installed-wheel promotion gate.

**Decision: do not promote.** The immutable-name prototype misses the 10%
whole-route threshold. No seven-pair campaign, ten-mode escalation or installed
wheel promotion campaign is warranted for this prototype. Independent review
accepted only the corrected diagnostic harness and unpromoted source prototype.

## Successor combined gate

The reviewed successor is frozen at
`114d2cd83b8a7e5c5eacc23bbe20b3f7f902afb2`. It combines call-local live
namespace-view reuse during qualified lifecycle validation with cheaper trusted
checks at genuine no-op spectral cancellation checkpoints. It does not cache
validated values, skip callback boundaries, change mechanics, or include the
interrupted geometric-coordinate prototype. Parent verification covered 164
focused authority, mutation, modal and buckling tests. Fresh independent review
returned `ship` with no findings; its separate 20-test inventory passed.

The three-pair screen reduced median first-analysis time from 9.8380 s to
9.1388 s (7.11%) and retained time from 5.4710 s to 4.8014 s (12.24%). The
retained target therefore advanced to the final seven-pair gate.

Final serial seven-pair results, alternating baseline/candidate order:

| Measurement | Baseline median / MAD / p95 | Candidate median / MAD / p95 | Median change |
| --- | ---: | ---: | ---: |
| First analysis | 9.8232 / 0.0103 / 10.1364 s | 9.2358 / 0.0644 / 9.3564 s | 5.98% faster |
| Retained analysis | 5.4830 / 0.0507 / 5.9665 s | 4.8514 / 0.0158 / 4.9157 s | **11.52% faster** |

Maximum sampled tree RSS was 608,718,848 bytes baseline and 608,206,848
bytes candidate. In all seven pairs, eigenvalues, recorded residuals and every
stored mode-vector array were exactly identical. Maximum recorded residual was
2.62e-14.

Bounded retained-route checks found no regression: fine-panel buckling improved
10.25% retained and 14.18% first-analysis; medium-panel modal improved 21.59%
retained and 17.29% first-analysis; medium-cylinder buckling improved 5.85%
retained and 5.92% first-analysis. These are single paired checks, not final
population timing estimates. Scientific artifacts were exact for each pair.

An isolated wheel was built from the clean frozen commit. Wheel SHA-256:
`6BC45678A501CCC38D04294EE13BAF91C2F2824963F67DF0CBF4B1BAD5A2CD57`.
The actual ANYstructure adapter imported ANYsolver from the external install
target and completed a retained coarse-panel five-mode solve with verified
repeat consistency.

## Decision and next priority

No mechanics, tolerances, qualifications, defaults or public selectors changed.
The successor is accepted for integration because its retained target clears
the 10% whole-route threshold, all retained routes improve, and the scientific
results are unchanged. Its first-analysis medium-panel gain is reported as
5.98%, not promoted as a separate 10% result. No new geometric-assembly
implementation is claimed: the interrupted privileged-coordinate prototype was
removed before the freeze because it lacked its promised mutation tests.

Current panel evidence favors eliminating repeated validation work before
changing matrix solvers. Geometric assembly is the next measurable target;
residual batching is already inexpensive. C++ and a new factorization backend
have no demonstrated whole-route justification on these panel measurements.
Cylinder buckling has a different cost mix: its medium/fine repeated full
analysis spends 2.21 / 4.45 s in factorization and 2.35 / 6.59 s in eigen
iterations, versus 2.62 / 5.74 s in validation and 1.21 / 2.38 s in geometric
assembly. Consequently, panel factor-cache
measurements alone cannot dismiss solver work for cylinders. First investigate
the cylinder modal rigid-mode/unshifted-search path, preserving its admission
and residual rules; then qualify deeper shared validation/geometric preparation
on both geometries. Do not select a C++ backend from kernel-only expectations.

The next measured target is qualified geometric-coordinate preparation and
geometric-stiffness assembly, but it must preserve the existing direct-state
revision in cache keys and prove descriptor/ABA mutation rejection before
timing. Fine-cylinder modal and ten-mode escalation remain deferred. C++ or a
new matrix backend is still not justified by the panel evidence; the cylinder
factor/eigen mix remains the workload where such a backend may later earn a
separate screen. No default change, version bump or publication is authorized.
