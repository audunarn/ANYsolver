# Nonlinear static performance and convergence results

Date: 2026-09-19

Baseline: `3499a04fa10c8d2bd5d6b8e401229ac787cb117e`

Candidate: `codex/solver-performance-armijo`

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
variant. The fallback oracle forces full reaction reassembly; the candidate
uses the accepted-force payload when its generation remains valid.

Environment: Python 3.14.2, ANYsolver 0.4.6, NumPy 2.4.6, SciPy 1.17.1,
Numba 0.65.1, Windows 11, `OMP_NUM_THREADS=1`. Other recorded thread variables
were unset. The JSON artifacts contain every sample, dependency and dispatch
diagnostic.

## Results

| Route | Baseline median | Candidate median | Change | Assemblies | Reaction reassemblies | Physical digest |
|---|---:|---:|---:|---:|---:|---|
| Installed acceleration enabled | 0.467810 s | 0.458661 s | -1.96% | 185 to 145 | 40 to 0 | exact match |
| Acceleration disabled reference | 1.386127 s | 1.161419 s | -16.21% | 185 to 145 | 40 to 0 | exact match |

Median solver time changed by -2.87% with acceleration enabled and -16.79%
with acceleration disabled. Direct reduced assembly was active in all primary
candidate samples and inactive in the reference run, verifying both dispatch
routes. The primary traced Python peak changed from 1,050,608 to 1,050,066
bytes. The reference peak changed from 3,993,721 to 2,580,501 bytes.

The primary production path does not meet the declared 10% median-time target;
the smaller repeatable gain is retained and reported. The acceleration-disabled
reference exceeds 10%, but it is not used to overstate the installed accelerated
result.

The Armijo development screen and the existing residual-decrease search both
completed the cubic hardening spring with the same physical digest, six Newton
iterations, five linear solves, one rejected full step, two backtracks and no
failed increments. This screen does not meet the Armijo promotion rule because
it neither adds two difficult solves nor reduces failed work by 25%. Armijo
therefore remains explicit opt-in and no existing profile selects it.

## Verification

- 49 focused Armijo, reaction-reuse, follower-load and restart tests passed.
- 96 broader nonlinear mechanics, corotational, prescribed-motion, plastic
  state-lifecycle and diagnostics tests passed.
- The built wheel installed into an isolated directory and completed a Q4
  follower-pressure Armijo solve. It reported the resolved RMS characteristic
  length, two accepted-force reaction reuses, zero reaction reassemblies and a
  completed status.
- Source formatting checks and canonical JSON parsing passed.

No independent reviewer was available in this task. The candidate is ready for
independent code and mechanics review; this report does not mark Armijo as
promoted or qualified.

## Evidence

- `reports/performance/nonlinear_static_performance_convergence.json`
- `reports/performance/nonlinear_static_performance_convergence_reference.json`
- `docs/reference_cases/nonlinear_static_performance_convergence_manifest.json`
