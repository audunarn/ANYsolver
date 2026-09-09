# GE-B3 four-macro arch: preserved process failure and serialization successor

Frozen failed candidate: `3f05a4ee728f632aace088e67bdf9d97bcf805ed`, tree
`38789c9edc62b1903000d053afc59dacfce00ac2`.
Consumed request: `b89e903dc17d44408ce0c42d11c6b61f`.
Exact registered execution: 2026-09-07 10:45:37.3260414 through
10:45:46.6399782 UTC, exit 1. The request ran once, after the administrator's
explicit grant and ledger approval, under its matching global lock.

## Actual terminal evidence

The native controller committed all four prescribed targets. Worker control
flow reached all four REFERENCE_COMPARISON progress records, after the native
checkpoint restore and the zero-plastic-history checks. The worker then failed
`validate_ready` with `ValueError('finite diagnostic fields')`. Its parent
reported exit 1. Neither pending nor canonical comparison was created.

The Windows Job cleanup completed; no registered Python process remained.
The matching resource lock was released. No retry occurred. The original
worktree and external checkpoint/stdout/stderr/transcript remain unchanged.
No successful qualification or accepted canonical comparison is inferred from
the completed native solve or from the worker's progress messages.

## Reproduced cause and narrow correction

The reference work-error expression combines a Python float energy derivative
with a numpy.float64 force component and therefore returns numpy.float64.
The comparator forwarded it unchanged into the in-memory ready packet. The
strict ready validator requires `type(value) is float` for diagnostic numbers.
JSON can encode this numpy.float64 scalar identically to a Python float, but
validation happens before that conversion, so publication correctly stopped.

New synthetic comparator regression tests reproduced three failures for zero,
a small positive value and the smallest positive binary64 subnormal. No BVP
or native beam solve is invoked by those tests. The successor changes only
`work=reference.work_error` to `work=float(reference.work_error)` at the
comparison serialization boundary. It does not change continuum equations,
the native operator, quadrature, tolerances, branch conditions or validation.

The tests verify exact scalar bits and unchanged canonical JSON, reject the
original pre-conversion packet, accept the converted packet, and continue to
reject nonfinite and negative diagnostics. Final bounded unit invocation:
37 passed, one deliberately deselected BVP test, in 0.64 seconds. It includes
mocked process limits/publication, not a repeated arch resource execution.

## Read-only diagnostic observation, not repaired canonical evidence

The failed checkpoint's bytes, outer seal and record hash chain were verified
without replaying mechanics. Its four native loads were compared arithmetically
with the already committed nominal continuum loads in the original comparison
evidence. No reference was recomputed and no absent worker row was fabricated.

| Crown drop | Two-macro load error | Four-macro load error |
|---|---:|---:|
| 0.010 | 5.7910% | 2.0851% |
| 0.025 | 12.3857% | 4.9592% |
| 0.040 | 19.5049% | 7.2241% |
| 0.055 | 27.0851% | 8.7488% |

All four saved histories remain elastic and reflection errors are below
3e-16. This supports refinement progress, not the required finest-mesh
accuracy, same-equilibrium-branch proof, stability or independent review.
The preserved nominal continuum is not an exact dyadic section certificate.
This audit is not the missing canonical result of the failed request.

## Continuation boundary

Preserve this incident and review the clean serialization successor before
new resource execution. Never reuse the failed request, overwrite its output,
or rerun its native solve automatically. Prefer a separately frozen read-only
comparison of preserved data when sufficient; any new reference, replay or
refinement execution needs its own exact scope and resource request.

Further beam engineering convergence, nonlinear section/state parity, current
modal/buckling/restart, independent review and objective shell coupling remain
open. No public selector, default, existing beam/shell mechanics, package or
historical qualification evidence changes. This successor does not authorize
activation, publication or reinterpret the failed request as PASS.
