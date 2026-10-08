# Supporting source review: radial beam ends

Scope: `beam_radial_ends.py`, `beam_end_radial_geometry.py`, conditional `core.py` dispatch, and `test_general_contact_radial_beam_ends.py` in `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`. Read-only source scrutiny; no imports or tests executed. Same-family review, not independent acceptance.

## Findings

No concrete force/tangent or false-certificate defect found in the inspected implementation.

- `radial_point_work` differentiates the literal fixed map with `B.T @ unit` and `B.T @ (I-unit*unit.T) @ B / d`. Both `_integrate_cell` and endpoint `evaluate` use it, so the new line and endpoint laws share the same potential and map. The endpoint block is `ke*(a*a.T + g*H)`; force/moment accumulation has the expected physical sign and common origin.
- `end_controls` uses the actual B3 Bernstein endpoint derivative. `physical_beam_ends` supplies all-material-node incidence, including unselected B3 midpoint junctions.
- `ownership_path_admissible` proves each interval open or strictly signed in ownership. Its Bernstein sign test cannot silently pass an active double zero; unresolved cases exhaust the finite depth and return false. `radial_inactive` computes the exact quadratic minimum for affine point paths.
- `curve_gap_lower` uses exact squared-distance Bernstein lower bounds and outward conversion. `_swept_admissible` includes relative tool translation and a conservative mapped Bernstein velocity enclosure.
- `radial_cuts` treats nonlinear floating roots as proposals. Exact inactivity plus Bernstein sign-variation refinement protects against hidden additional pockets, including panels that already contain detected contact. This still does not make the Gauss error estimate a general integration certificate.
- Restart inherits line/swept limits and binds endpoint stiffness, physical ends, profile, and geometry revision. Dispatch is conditional on hemisphere selection; no-cap dispatch remains on the legacy manager.

## Consequential checks still missing from this test file

1. **Actual moving-tool path:** combine nonzero `path_translation` with beam motion; make endpoint poses open but the intermediate whole curve penetrated. Check the full manager's swept rejection, not only the isolated ownership helper. Add prescribed-tool work and fresh restart with changed path rejected.
2. **Tilted infinite cylinder:** check complete work/tangent with an oblique axis and common rigid covariance. The current coordinate-aligned cylinder does not discriminate literal `B.T` differentiation from the old projector simplification.
3. **New activation/budget code:** a genuinely quadratic radial curve with two narrow active pockets, a repeated grazing root, and deliberately insufficient line/swept budgets. Verify either resolved contributions or explicit failure; no sampled-zero success. The new helpers are not exercised by the existing capped-cylinder tests merely because they share some utilities.

These are targeted verification gaps, not demonstrated mechanics failures. Existing reported passes were not rerun or independently accepted here.

## Delta: `regular_curve_path`

Concrete B2 defect: its derivative has one Bernstein control per coordinate, but the reused `_restrict` utility supports only two or three controls. Whenever the initial component box cannot certify a B2 path, `midpoint=_restrict(middle,1/2,1/2)` attempts to unpack three entries from a one-entry lane. Example: B2 endpoint vectors change affinely from `(1,0,0)` to `(0,1,0)`. The curve speed stays at least `1/sqrt(2)`, but the first component box contains the origin, so this valid path reaches the unsupported restriction and raises. The collapsed reversal similarly raises instead of returning the intended boolean rejection.

Handle constant derivative lanes directly or provide degree-zero restriction. Add both the regular quarter-turn and collapsed reversal B2 cases. For B3, the derivative lanes have degree one: the tensor component-box lower bound and exact subdivision are conservative; no false-admission error found in those equations. No tests executed for this review delta.

## Lead disposition after implementation

The B2 derivative is promoted to two equal controls; the existing degree-one
restriction is then exact. Regular quarter-turn and collapsed reversal tests
pass. Full affine moving-tool/common-motion and through-crossing checks,
tilted-cylinder complete work/tangent/covariance, two quadratic pockets with an
independent analytic-root integral, exact repeated grazing and insufficient
line/swept budget checks are now included. Force/displacement, active/open fresh
restart, staged tool work, candidate failure, cancellation/reuse and local path
cleanup are exercised. Installed37checks pass31.110s/336408576B; retained raw
evidence and source parity are in summary.json. These are author-executed checks,
not a retrospective reviewer execution or independent engineering acceptance.
