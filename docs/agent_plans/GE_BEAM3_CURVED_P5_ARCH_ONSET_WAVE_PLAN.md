# P5 lateral-onset refinement — one-use bounded research wave

Implementation parent: `3d7dd492180f4d6658d832d5a71ca7a4a028aadb`, tree
`5807119f9c8b56b98fe43cad63347cdea292350d`. The freeze contains exactly this
plan, `ge_beam3_curved_p5_arch_onset_wave.py` and its test file. The runner
requires that exact parent, path set, clean HEAD and supplied commit. It binds
the resulting tree without self-referencing its own commit hash.

## Question, mechanics and evidence boundary

Locate the earliest *observed* lateral sign crossing on the frozen sampled
arch branch for 4, 8 and 16 elements. Compare endpoint drops and recovered
loads with the separately reconstructed, knot-resolved continuum endpoints.
This addresses the unresolved critical-onset mesh error after the earlier
16-element arclength run and static mode-shape comparison. A matched shape
is not proof of a correctly located critical point.

Reuse the unchanged parabolic arch, height 0.1 and span 2, both ends clamped,
section diagonal `[1000,400,400,0.02,0.01,0.02]`, eight-point integration per
half-element, elastic directed-hardening adapter, full spatial assembly,
transactional displacement controller and sampled-inertia inspector. No
operator, quadrature, section coefficient, reference equation, uncertainty
formula, tolerance, production recovery or default changes are included.

The fixed grid is thirteen drops `0,0.005,...,0.060`. It is completed even
after an observed sign crossing. The first adjacent positive/negative pair
preceded by only positive sampled values receives at most sixteen bisections,
to width `1e-7` or an uncertain midpoint. An uncertain midpoint retains the
last sign-separated bracket; an uncertain earlier grid point prevents a
claimed first observed positive/negative bracket. Failure propagates without
retry, cutback or interval extension. Each midpoint starts from its saved
accepted positive endpoint. No lateral coordinate is constrained or removed.

The complete conservative Hessian is inspected, not the displacement-control
Schur matrix. Full/even/odd spectra, uncertainty bands and lowest mode vectors
remain external diagnostics. Numerical sign intervals are not rigorous
intervals. Sampling cannot prove no hidden crossing between grid points.
Load values are explicitly values **at** bracket endpoints, not extrema or a
rigorous critical-load enclosure.

## Frozen source and runtime inputs

ANYfileIO must remain clean at commit
`b48ba51c7b79e6d64b3f99c1fb131b9b602e7e1d`, tree
`29cb248a8d320607e21424c68625c4af6a949da1`.

The Python executable is `C:\Python\Python313\python.exe`, SHA-256
`08A64DC73AC3E3776B49F0097C6306BDB9C8F7990A037065213324D328467BF5`,
Python 3.13.9 (AMD64). Installed NumPy 2.4.3 has 935 bound non-bytecode
distribution files; SciPy 1.16.3 has 1,532. Their complete sorted per-file
byte/hash inventory digests are respectively:

- `CA360CFCB5B3FFF3454E9888DF8C9E0398852AC89E329CC2CFFA542BDC853948`
- `A58331DE4413CEBCE1BC7D1CDC6B3F1B4ADF3887DC4B702A3E274970BE28F9D6`

The canonical environment record digest is
`2CD226A5CF78C9CC833DCBAF7E4CD0C8EAB92DD8566AF69412E13D346DC298F4`.
This binds the numerical distributions and executable, not a claim that
every operating-system/stdlib dependency is independently qualified.

Read-only continuum inputs are under
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-lateral-knot-20260906-e10841364c644b29b60f7c057c20a41e`:

- `root-stride-1.json`: 29,126 bytes, SHA-256
  `64C47952DACD030D81EC3A631744179C300C33052551E1EBE5C16A9E191019FC`.
- `root-stride-2.json`: 29,139 bytes, SHA-256
  `A7917C813953D181DF20748C5E54179E0F84597585650B641FBD46B90E8F073C`.

Both are immutable successor endpoint packets. No continuum re-solve, old
arclength rerun or replacement of failed/accepted historical evidence occurs.
Both retained reference interpolation strides are reported, not selected by
which gives the smaller error.

## Execution and failure handling

After this freeze, create one new resource request for the coordinator's
exact emitted PowerShell command and a fresh external output directory.
Obtain the resource administrator's exact APPROVED ledger row. Acquire only
that request, run its stored command byte-for-byte once, and release in
`finally` after all process trees are terminal. No consumed ID is reused.
The runner requires exactly one approval and no terminal ledger row at entry
or finalization, then creates a permanent exclusive per-request claim.

Run workers **serially** in order 4, 8, 16. Each receives a distinct external
directory, one numerical-library thread, a 24-GiB complete-tree Windows Job
limit, a 600-second envelope and 300-second CPU/checkpoint inactivity limit.
The existing containment helper starts its termination timer early enough
to allow tree drainage. The coordinator has a 1,780-second hard watchdog,
within the 1,800-second wave ceiling; remaining budget reduces a later
child's envelope rather than allowing overrun. No automatic retry occurs.

Full authority/environment/reference checks precede numerical imports and
repeat at worker and coordinator finalization. Raw trial files, progress,
stdout/stderr, PID/start records and process CPU/peak-memory/wall diagnostics
remain external. State-start/complete and probe-complete checkpoints are
written; the existing finite controller additionally records bounded Newton
checkpoints inside each raw completed trial. A stalled incomplete trial is
still bounded by process CPU/inactivity/wall monitoring.

On process, evidence or authority failure, retain raw/partial files and an
external blocked diagnostic, stop launching workers, and create no canonical
aggregate. Earlier completed workers are diagnostic partial evidence, not a
completed wave. A resource manager completion PASS means successful resource
execution only, never element qualification.

## Independent integrity checks and interpretation

The coordinator verifies strict canonical JSON (including duplicate and
nonfinite rejection), exact IDs, raw byte counts and hashes, allowed worker
files, node/station counts, iteration budgets, accepted origin epochs,
elastic histories, loads, physical equilibrium/planarity/fixed constraints,
and every raw tangent's full/even/odd spectral reconstruction. It replays
the deterministic search algorithm against bound raw samples to reject
changed intervals, origins, ordering, missing/excess samples or dispositions.

This is integrity and numerical spectral recomputation, **not** an
independently authored element-mechanics checker or independent review. A
coordinated change to every raw operator cannot be ruled out by rehashing and
spectral checks alone. Production qualification still needs independent
mechanics/source review and the other outstanding programme gates.

Only after all three workers terminate and validate, publish the exclusive
canonical aggregate `RESEARCH_ONSET_DIAGNOSTICS_COMPLETE`, retaining each
mesh's actual search disposition and both continuum endpoint comparisons.
No new accuracy threshold is introduced. Signed relative drop/load errors
are diagnostics used to select the next engineering step; uncertainty and
missing brackets remain visible. Every result has
`production_qualified=false`, `accuracy_qualified=false`, and
`first_critical_point_proven=false`.

## Pre-freeze tests

Runner suite: **38 passed in 2.91 seconds**, including a three-state,
two-element raw-integrity smoke, rehashed mutations, strict parsing,
lease/authority rejection, deterministic inspection, and synthetic process
failure preservation. No multi-mesh solve ran in that suite.

Three unchanged Windows containment tests passed in **2.81 seconds**:
normal/timeout child, a small allocation rejected by its Job memory limit,
and timeout termination of both root and sleeping descendant. These are
short disposable correctness tests, not performance or qualification waves.
Their pytest directories are fresh external temporary directories.

Final focused regressions (runner, search, controller and sampled inertia):
**102 passed in 10.33 seconds**, using a fresh explicit temporary directory.
`git diff --check` passed. Confirm the exact three-path research-only extent
and no production delta when committing.
Preserve the frozen worktree during the resource execution. Report the
request, candidate, output hashes and actual process outcome in a later
closeout; do not edit this frozen contract during the run.

No push, merge, version/default change or activation is authorized by this
research checkpoint. Full nonlinear/material parity, mass/dynamics,
restart, packaging and objective beam-shell connections remain open.

NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
