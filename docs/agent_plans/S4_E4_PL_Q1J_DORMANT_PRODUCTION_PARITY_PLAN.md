# E4-PL Q1J: Dormant Production Implementation and Parity Closure

## Purpose

Q1J converts the qualified Q1B–Q1I E4-PL mechanics into maintained production
code while keeping legacy `ShellElement` as the default.  The explicit
`e4-pl` factory alias is opt-in and exists so solver-level parity can be tested
before activation.

## Frozen mechanics boundary

- The four-node planar elastic tangent is the Q1B 35+3 stationary E4-PL
  operator accepted by Q1H/Q1I.
- Centre PL and retained drilling-hourglass operators remain separately
  recoverable numerical contributions.
- D4 numbering, registered distortion, local algebra, support/KKT, locking,
  and continuous-domain coercivity are inherited from Q1X–Q1I evidence.
- No scientific coefficient, case, tolerance, or terminal is changed here.

## Production design

- `QualifiedE4PLShellElement` subclasses `ShellElement` so existing mass,
  geometric stiffness, state, recovery, coupling, contact, and solver
  contracts continue to apply.
- The nonlinear path retains the mature geometric/material increment but
  replaces its zero-state elastic tangent with the qualified E4-PL baseline.
- Legacy compiled stiffness/nonlinear batches explicitly reject the candidate;
  warm local matrices are revision-safe cached until a dedicated equivalent
  batch exists.
- Faceted curved meshes use the direct E4-PL kernel.  Genuinely warped facets
  remain on an explicit, tested legacy fallback until their new-formulation
  qualification closes.
- Runtime shell dispatch uses `isinstance`, not exact class-name comparisons.
- Serialization is lossless and reconstructible through the opt-in type.

## Maintained parity authority

`docs/reference_cases/e4_pl_q1j_parity_matrix.json` is closed-world for every
public `Element`/`ShellElement` method and for the named ecosystem capabilities.
Tests fail if a public legacy method is added without a classification or if
the default is activated while a required capability contains a pending,
blocked, or legacy-fallback status.

## Remaining gates

1. Qualify and implement a non-legacy warped-facet formulation or explicitly
   accept the fallback in an independent release review.
2. Re-run the complete legacy S4 capability matrix with the opt-in alias.
3. Only after all required matrix rows close, change the four-node `shell`
   factory/default and retain legacy implementations solely for non-Q4
   topologies and documented compatibility routes.

## Required verification

- Focused E4-PL kernel, parity-matrix, and workflow suites.
- Generalized-section, orthotropic, contact, dynamics, buckling, activity,
  nonlinear-performance, and runtime regressions.
- Production-boundary review proving the `shell` factory is still legacy.
- Performance comparison for cold and warm assembled stiffness.
- Final default-activation and rollback tests in a separate reviewed stage.
