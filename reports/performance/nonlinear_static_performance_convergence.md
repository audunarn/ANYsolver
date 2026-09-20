# Nonlinear static performance and convergence results

Date: 2026-09-20

Implementation base: `3499a04fa10c8d2bd5d6b8e401229ac787cb117e`

Reviewed candidate code: `7d4da21abf199704871d2c2ef39050ee8cabe81f`

Performance capture source: `32a97fda73369a99f4ce24cc55b0c35224199755`

Immutable-wheel qualification candidate:
`79fa3343f40e72bc64ae6532768288b6e8583119`

Package version: `0.4.6` (unchanged)

## Scope

The candidate adds analysis-local work counters, fixed dead-load projection,
generation-guarded accepted-force reuse for force-control reactions, a strict
residual recheck after residual-only trial promotion, and an opt-in scaled
Armijo search. Existing solver profiles, convergence tolerances, element
equations, and defaults are unchanged.

The paired performance workload is a 2x2 clamped Q4 shell under 20 kPa fixed
pressure, advanced through 40 physical increments at a residual tolerance of
`1e-9`. Seven serial pairs ran in alternating order after one warmup per
variant. The same-revision oracle forces full reaction reassembly; the reuse
route uses the accepted-force payload when its generation remains valid. This
isolates the feature within one revision and is not a base-to-candidate timing
comparison.

Environment: Python 3.14.2, ANYsolver 0.4.6, NumPy 2.4.6, SciPy 1.17.1,
Numba 0.65.1, Windows 11, `OMP_NUM_THREADS=1`. Other recorded thread variables
were unset. The JSON artifacts contain every sample, dependency and dispatch
diagnostic and the exact source revision of the completed capture. The samples
now expose every metric named by the manifest. Residual-only counts are derived
from the captured assembly identity; zero search and failed-work counts follow
from the fixed-increment route, where the only oracle residual-only calls are
the 40 reaction reassemblies and the reuse route has none.

## Results

| Route | Forced-reassembly oracle | Accepted-force reuse | Change | Assemblies | Reaction reassemblies | Physical digest |
|---|---:|---:|---:|---:|---:|---|
| Installed acceleration enabled | 0.467810 s | 0.458661 s | -1.96% | 185 to 145 | 40 to 0 | exact match |
| Acceleration disabled reference | 1.386127 s | 1.161419 s | -16.21% | 185 to 145 | 40 to 0 | exact match |

Median solver time changed by -2.87% with acceleration enabled and -16.79%
with acceleration disabled. Direct reduced assembly was active in all primary
candidate samples and inactive in the reference run, verifying both dispatch
routes. The primary traced Python peak changed from 1,050,608 to 1,050,066
bytes. The reference peak changed from 3,993,721 to 2,580,501 bytes.

The accelerated feature-isolation screen does not meet the declared 10%
median-time target. The acceleration-disabled screen exceeds 10%, but neither
screen supports a revision-level performance claim. A fresh run from
`de9b4bb` was stopped after ten minutes of cold numerical compilation before
the first sample; it produced no timing artifact and is not counted here.

The Armijo development screen and the existing residual-decrease search both
completed the cubic hardening spring with the same physical digest, six Newton
iterations, five linear solves, one rejected full step, two backtracks and no
failed increments. This screen does not meet the Armijo promotion rule because
it neither adds two difficult solves nor reduces failed work by 25%. Armijo
therefore remains explicit opt-in and no existing profile selects it.

A post-review production J2 plane-stress material-point test now loads through
yield, reverses the load, forces rejected Armijo trials and tangent promotion,
and compares the committed displacement and plastic history with both an
unperturbed same-increment oracle and an 80-increment reference.

## Immutable revision qualification

The registered installed-wheel gate compared base `3499a04f` with candidate
`79fa3343f40e72bc64ae6532768288b6e8583119`. Each revision was built and
installed separately. Persistent workers excluded startup and one warmup per
case, then ran seven serial pairs in alternating order with all recorded thread
limits set to one.

| Case | Base median | Candidate median | Change | Gate |
|---|---:|---:|---:|---|
| Declared nonlinear workload | 0.486453 s | 0.465312 s | -4.35% | 10% target not met |
| Easy elastic control | 0.262814 s | 0.256573 s | -2.37% | 5% regression limit met |

All 14 paired physical comparisons passed. The maximum displacement difference
was `2.052e-18`, the maximum reaction difference was `1.136e-9`, and load
factors, step counts and plastic-strain summaries matched. The declared route
reduced nonlinear assemblies from 185 to 145 and reaction reassemblies from 40
to zero while keeping 105 factorizations and solves. Traced Python peak memory
changed from 1,057,064 to 1,047,914 bytes.

The formal terminal is **NO-GO for performance promotion** because the
registered 10% median reduction was not met. The physical-equivalence and easy
control gates passed, so the verified implementation remains suitable for
delivery under the plan's smaller-repeatable-gain allowance. Armijo remains
opt-in and unpromoted. A preceding identity-incomplete run is retained only as
a rehearsal and has no authority over this terminal.

## Verification

- 54 post-review Armijo, reaction-reuse, follower-load and restart tests passed.
- 30 additional post-review diagnostics, control-contract, limit-point and
  state-lifecycle tests passed.
- Before independent review, 96 broader nonlinear mechanics, corotational,
  prescribed-motion, plastic state-lifecycle and diagnostics tests passed on
  `32a97fda`.
- The built wheel installed into an isolated directory and completed a Q4
  follower-pressure Armijo solve. It reported the resolved RMS characteristic
  length, two accepted-force reaction reuses, zero reaction reassemblies and a
  completed status.
- A final wheel built from `7d4da21`, imported from its isolated installation,
  and completed the translation-only zero-span Armijo regression with frozen
  characteristic length `1.0` and two backtracks.
- Source formatting checks and canonical JSON parsing passed.

Two independent reviews examined the complete implementation diff. They found
no high-severity defect and no mechanics sign error. Five review findings were
addressed through `7d4da21`: legacy restart casing, including the corotational
uppercase V1 edge case, is preserved; translation-only zero-span Armijo models
no longer require an irrelevant length; the real plane-stress
rejection/reversal test was added; and the evidence was relabeled and completed
without a revision-performance claim. Both reviewers re-examined the
corrections and approved closure with no remaining actionable finding. Armijo
remains unpromoted and unqualified.

## Evidence

- `reports/performance/nonlinear_static_performance_convergence.json`
- `reports/performance/nonlinear_static_performance_convergence_reference.json`
- `reports/performance/nonlinear_static_revision_qualification.json`
- `docs/reference_cases/nonlinear_static_performance_convergence_manifest.json`
