# P5 two-element seed diagnostic and restart handoff — 2026-09-06

Research checkpoint after `9538b8702a1f9a19b04fc2b18c19bc8ddc8f4b6f`, tree
`68df9fd71d4dd6ed7b45c9d807d994b93e37a0f8`. This is not an independently
authored review, formal certificate, selected solver correction or qualification.
The two-element postcritical seed failure remains unresolved.

## Preserved case and observation scope

Use the unchanged `specimen(2)` in
`tests/test_ge_beam3_curved_p5_seeded_equilibrium_probe.py`: length 2,
EA=1000, GA=400, EI=1, continuum tip angle 0.6, compressive dead load
0.6449785996190569, two macroelements, order 8, virgin elastic section histories.
The old bounded seed algorithm allows sixteen global updates, ten backtracks
and 512 mixed evaluations. No coefficient, potential, tolerance, accepted
history, original failure or earlier four/eight-element success is changed.

The local trace wraps evaluation on a fresh probe. The assembly trace attaches
instrumentation only to a deep copy, not to the class or supplied model.
Evaluation order and budget consumption follow the old algorithm. Histories
are not committed in the supplied model. Tracing is an explicit diagnostic,
not an automatic retry mechanism or a scientific canonical publisher.

The following results were observed in completed ordinary diagnostic commands
before the restart/context handoff. They were recovered from the saved task
output. No external raw JSON packet was created for these traces; there is no
raw-packet hash or formal resource receipt to claim. The restart continuation
did not rerun these failed seed attempts.

## Observed failure sequence

Both initial local solves completed in two updates / three evaluations:

| Element | Final local residual | Trace input SHA-256 |
|---:|---:|---|
| 0 | 3.5839387013680835e-15 | `de4bf24c6ef20032bec8af8019e364474f47f6734255aa492757f350a88b8896` |
| 1 | 7.119825562451609e-14 | `bf2dc933beb74c891547d377115e405e0af5676b5b27eefc089d796218c9098b` |

The instrumented old global solve made 85 complete assembly evaluations and
one partial evaluation before exhausting 512 mixed evaluations. Each complete
assembly used three local evaluations per element; 85*2*3=510. The final
assembly exhausted the budget after two local evaluations of its first element.
Completed local stationarity residuals remained below 1e-11; the interrupted
local solve's last residual was about 2.54e-5 and was not a completed result.

Global residual decreased from 1.3381954246673584 to 0.027085390842010146 on
the first full correction. Later full candidates had much larger residuals;
repeated backtracking accepted small steps. The last observed accepted residual
was 0.02670209340440684. The old solve failed with
`SeededEquilibriumError` caused by `AssemblyPathError: assembly mixed-evaluation
budget exhausted`. This locates poor global progress on the observed path; it
does not yet establish its mathematical root cause or a successful repair.

## Failed alternatives retained as experiments

1. `ge_beam3_curved_p5_correction_seed_probe.py` changes only the line-search
   merit to a length-scaled Newton correction, evaluating candidate residuals
   with the current Jacobian. The physical convergence criterion remains
   unchanged. The exact two-element case reached the line-search bound.
   This is a simple experimental merit, not a claim to implement a complete
   published affine-invariant Newton algorithm. No external solver code was
   copied into it.
2. `ge_beam3_curved_p5_shape_seed_probe.py` temporarily fixes the x-y tip angle
   while solving for load, then returns to the original dead load. It shares
   the sixteen-update / 512-mixed-evaluation budget across phases and stages
   all state changes on a copy. The exact two-element case exhausted that
   budget. Its failing phase and intermediate factor were not recorded.
   No claim of successful angle-controlled equilibrium follows. The chart is
   benchmark-specific, not general objective joint/MPC support.

Both modules are marked FAILED DEVELOPMENT EXPERIMENT. Small unit-test passes
do not promote either algorithm. Do not silently select one, raise its budget,
relax residual tolerances or retry a consumed formal request.

## Recovered directional derivative diagnostic

The last command before the context handoff completed successfully in 2.872 s.
Its output was recovered, not rerun. At the initial seed and after its first
full Newton correction, it compared the existing spatial residual derivative
with centered differences in the normalized Newton direction. Rotations were
perturbed by left multiplication with Exp; local equilibrium was reconstructed
at each perturbation.

| Perturbation | Initial state normalized error | After first correction |
|---:|---:|---:|
| 1e-4 | 2.2872598971390703e-9 | 4.585533900839234e-7 |
| 1e-5 | 2.0722769057989217e-10 | 4.126308452776391e-8 |
| 1e-6 | 1.2779230341221255e-9 | 3.8804513717564766e-7 |

Only the middle perturbation at the second state meets the existing 1e-7
directional-check scale. The nonmonotonic errors are compatible with numerical
differencing/local-solve sensitivity, but this is not a proved explanation.
One direction at two states neither proves a tangent defect nor certifies all
derivatives. In particular, do not reclassify this table as an all-pass formal
tangent gate or tune a new acceptance tolerance from it.

## Tests, extent and transfer

The new diagnostic suite passed **15 tests in 2.13 seconds** with one numerical
thread. It covers deterministic local tracing, class/caller isolation,
correction-merit invariances, agreement on a previously resolved small elastic
case, source-level restriction of the experimental merit change, zero-budget
atomicity, the 3D tip-angle derivative, singular-chart rejection, invalid-bound
rejection before evaluation and explicit failed-experiment labels.
It does not retry the failed full two-element benchmark.

The existing continuation and postcritical-reference regression suites passed
**37 tests in 13.26 seconds**, separately from the diagnostic inventory. These
ordinary test durations are not performance or resource-qualification evidence.

Implementation/test SHA-256 values:

- local trace: `4BE3A53F6BE9B528CB14DBACADE06675CF86CBCDAA75ADB18A6005613A61BF57`
- correction experiment: `3306B89E4E43E40C97E1BFF5BF141F13A8AC14FE2A88F941079A09FDE8ADE624`
- shape experiment: `DD347CB0F7982CC112FD5EA3BBC22AAFF53EAC0C740D30C9763B059FACA0C4DC`
- tests: `DE64B7B65CC936DC47F64E5682CAEDE7EC10F47C89BE151D1FC9E4EC9F957B14`

The checkpoint adds exactly these four research/test paths and this handoff.
Existing tracked mechanics, tests and authority records are unchanged. Main
remains at `09351645ba17a0a5b130a1c7a48007d36dd08ada`; no push, merge,
publication, alias or default change is part of this checkpoint.

## Next bounded diagnostic, not yet executed

Before another full seeded solve, inspect the first rejected global correction
and the angle-controlled bordered equations separately. Record phase IDs,
load factor, free residual components, tangent conditioning, correction norm,
constraint gap, backtracking scale and local budgets. Verify the derivative
in multiple directions without using finite differences as the mechanics
implementation. A new attempt must be explicitly scoped, bounded and retained;
the failed alternatives are not automatically retried.

Use the findings to distinguish coordinate/derivative errors, branch selection
and globalization before changing solver code. Preserve the physical potential,
loads, original comparison, tolerances, original algorithms and failed outcomes.
Do not infer a constitutive or element defect solely from bounded solver failure.

The broader goal remains active and incomplete: wider coupled/curved/slender
coverage, robust local stationary solves, general nonlinear section parity,
actual arch limit points, prestressed modes/dynamics, production integration,
independent review and objective eccentric/curved beam-shell joints remain open.
Existing B2/B3/Q4/S3 mechanics and accepted qualification evidence are untouched.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
