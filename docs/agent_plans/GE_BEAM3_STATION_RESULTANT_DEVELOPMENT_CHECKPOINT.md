# GE-B3 constrained station-resultant development checkpoint

## Disposition

The new research cell passes the unchanged `1e-11` force, compatibility,
section, plastic-history, and work checks, including section contrast `1e12`.
This is **not nonlinear beam qualification**. Independent review is **PENDING**.
The predecessor's failed cell remains genuine failed evidence; it is not edited
or reclassified. Existing B2/B3, Q4/S3, accepted straight GE-B3, and defaults
are unchanged. No public routing, version, package, release, or resource-ledger
change belongs to this checkpoint.

Base: `ac3e5e942d4eacce48c7043066dca60d5e3f84a3`, tree
`da18e83df3aa7cee8c4b81abacf081d004fea9f5`.

## Evidence and diagnosis

The preserved old cell failed force reconstruction at
`2.203355787243626e-11`. A separate source-equation Decimal audit evaluates
the old gradient at higher precision and still finds a force error of about
`2.88e-11`: this was not only final summation roundoff.
Solving the source equations at higher precision gives about `3.33e-12` after
rounding the gradient to one vector and about `1.01e-28` with a two-part vector.
These are arithmetic checks on supplied binary64 material and station data,
not an independent geometry proof or certified interval calculation.

The successor constructs the full section complementary energy in station
resultants. It minimizes over station axial/shear forces subject to the six
shared-cell force constraints, retains interpolated endpoint moments, then
solves the scalar station hardening increments with a bounded orthant method.
This differs from the audit's partial section Schur construction. Both were
written by the same author and do not replace independent review.

The compiler uses 80-digit Decimal arithmetic. First and second derivatives
come from the same constrained energy; no coefficients or tolerance changes
were made. High/low pairs represent gradients, compliance, station fields,
and plastic histories. Continuation must not silently drop their low parts.
The history format is `[z_high,z_low,p_high,p_low]` at each station. A response
only proposes history; it never commits it. Invalid, nonfinite, unnormalized,
or inadmissible paired history is rejected.

## Test inventories (separate runs)

- First collection: one syntax error, no cell evaluation; JUnit preserved.
- First cell implementation: 16 passed, 2.678 seconds.
- Loading/history development: 26 passed, 5.283 seconds.
- Final development cycle A: 37 passed, 5.539 seconds, no skips.
- Final development cycle B: 37 passed, 5.508 seconds, no skips.

The two final cycles have 26 byte-identical JSON pairs. Tests cover contrasts
1, 1e4, and 1e12, virgin and nonuniform prior plastic history, original section
equations, force and curvature integration, work, directional derivatives,
symmetry, pure trials, loading/unloading/reversal, paired-history replay,
invalid inputs, and cooperative compiler/evaluator deadlines.
No large model, benchmark, or formal resource request was run.

The external archive has 105 content files (2,226,659 bytes) plus its manifest:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-station-resultant-development-20260907-74d14825df89`.
The manifest is 16,814 bytes, SHA-256
`01cc98045e0d18bf287d7b7faacdedec369ce8402971cbc001e8ab949fc54076`.
The canonical development record binds source and evidence hashes.

## Next implementation step

Integrate this complementary cell into a successor retained-resultant
nonlinear element potential `p.k(q) - Psi*(p; accepted_history)`. Preserve
the verified objective kinematic map and its analytic variations. Keep
cell resultants in the global saddle solve; do not restore the inaccurate
nested condensation. Compute compatibility with both gradient parts and
recover physical fields from the represented station resultants/history.

Before accepting any nonlinear global step, verify equilibrium, compatibility,
section equations, and admissible state; publish history only at the global
commit point. Add cancellation, rollback, final-state replay, restart, and
load-reversal tests with the paired state bound to the new formulation/schema.
Existing elastic and historical V5 capsules must not be implicitly converted.

The current research class is not an immutable production section adapter or
a complete global solver. Its 60-second cooperative compiler/response checks
and 32 active-set updates are development bounds, not process-tree watchdogs.
Production integration still needs immutable capture, guard-bound state,
resource-safe runners, general nonlinear/fibre sections, complete loads/mass/
modal/buckling/postbuckling parity, independent review, and qualification.
Objective eccentric/curved beam-shell connections remain part of the goal.
