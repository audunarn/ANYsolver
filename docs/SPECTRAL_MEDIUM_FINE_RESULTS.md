# Medium/fine spectral gate — working results

Status: diagnostic evidence, not an accepted performance optimization.
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
- Parent verification: 116 focused validation/state-safety tests passed;
  eight runner tests passed. Independent source review found no guard-safety
  regression in immutable captured-class-name preparation.

## Acceptance and next decision

No mechanics, tolerances, qualifications, defaults or public selectors changed.
The immutable-name preparation is an unpromoted prototype. It needs the frozen
three-pair screen; if it fails the 10% whole-route threshold, do not advance it
to the seven-pair campaign or integrate it as a performance improvement.

Current panel evidence favors eliminating repeated validation work before
changing matrix solvers. Geometric assembly is the next measurable target;
residual batching is already inexpensive. C++ and a new factorization backend
have no demonstrated whole-route justification on these panel measurements.
Cylinder conclusions remain open until its actual runtime fixture is measured.
