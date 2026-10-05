# Guided S3 algebraic interval path — development results

Candidate parent: `f31ccee577e73522e092af11573f84384f51b57c`; candidate source
bytes are bound in the installed manifest and retained raw archive. This is
implemented, tested and independently source-reviewed development, not C6
scientific acceptance, release or general collision qualification.

## Change and scope

The explicit `s3_algebraic_path_dev` opt-in lifts the physical Newmark quadratic
through exact reference-linear elastic S3 algebraic penalty equilibrium. Three
represented pressure supports/eight active masks are an explicit admission cap.
All branch polynomial roots partition the interval; sign extrema, interval
coverage, continuity and finite arithmetic are checked. Physical corner minima
use a separate affine skin map. No rotational mass or hidden regularization is
added. Unsupported, singular, indefinite or unresolved paths fail explicitly.

Full lifted endpoints must match accepted nodal coordinates within explicit
position/rotation budgets. The new constant/history profiles bind those settings
into identity. Version3 retains the terminal support mask for grid-aligned
transition reporting through restart. Old profiles and schema identities remain.
Candidate rejection precedes commit; transition times are published only after
acceptance. Affine history-load work is integrated on the lifted path.

The [prospective derivation](../C6_S3_ALGEBRAIC_PATH_SLICE_20261001.md) and
[guide](../../GENERAL_CONTACT_C6_S3_DESCRIPTOR_DEV.md) state eligibility and limits.

## Checks actually run

| Run | Result | Purpose |
|---|---|---|
| Source v1 | 9 passed | Initial independent scalar/manifold checks |
| Source v2 | 5 passed | Crossing/grazing and arithmetic robustness |
| Source v3 | 6 passed | Corrected overflow counterexample, coverage, work and public tilted/history integration |
| Source v4 | 5 passed | Boundary restart, endpoint budgets, injected failure cleanup and historical directional compatibility |
| Final isolated installed artifact | 24 passed, no skips | Complete final path test file, three historical compatibility fixtures and CLI example |

The source selections overlap and must not be added as distinct test counts.
Final installed execution: 13.0469614s complete elapsed, 5.78s pytest,
176775168B peak process-tree RSS; 180s/999292928B caps. BLAS/Numba thread1,
JIT off. 449 source/wheel/site modules match and all 198 recorded solver imports
resolve to the isolated installed site. Wheel SHA256:
`e117be4d705034964960c04f4c531da1671d734be9926209e0d5974b6a48b253`.
Runtime settings, source/fixture hashes, dependency versions and the 24-case
inventory are retained. No complete-route speed improvement is claimed.

Independent references include scalar algebraic solutions, exact piecewise work,
separable constraints and a public tilted S3 fixture reconstructing pressure and
corner geometry independently and solving algebraic force with SciPy. The final
installed run repeats that oracle against the final endpoint checks. It verifies
the declared represented intervals, not arbitrary geometric search completeness.

## Review findings and retained uncertainty

Source review identified finite-input solve overflow, a quadratic-extremum
denominator overflow, missing-root coverage, endpoint consistency and boundary
restart reporting risks. Each was addressed with a focused regression. The initial
overflow example was corrected to a dense null basis before its final execution;
the original diagonal version also formed nonfinite intermediate products.
A misleading stationary-touch test name was corrected and a true grazing case
added. These are retained review findings, not retroactive numerical passes.

Mistral Read review produced useful source observations but reached its ten-turn
cap without a final assessment; it remains incomplete. Independent OpenAI source
and saved-evidence assessment is retained separately in `review.md`. No kernel
author supplied the sole assessment. Historical failures and consumed authorities
remain unchanged; no new numerical NONPASS occurred in these selected runs.

## Remaining programme work

The driver reports transitions on its discrete represented path but does not yet
subdivide physical integration at activation/release. This result is not exact
continuum event timing or conservative general dynamic collision control.
The admitted owner remains one guided small-motion elastic S3/fixed plane with
positive definite algebraic structural work; history base force has exactly zero
represented algebraic projection. General shells/classical beams, moving tools,
free bodies, nonlinear materials, native coupling and full C6 remain open.

## Reproduction and retention

`raw.zip` preserves source v1–v4 logs/runtime/selection/resource records, incomplete
Mistral review, exact candidate files, installed wheel/fixtures/runners/identity,
inventory and imports. Its embedded manifest and readback receipt bind every
archived file. The package directory is
`C:/ANYworkspaceWork/contact-algebraic-path-package-20261001`.
Run from that directory with `C:/Python/Python314/python.exe -X utf8`:

```text
run_bounded.py c6-algebraic-path test_general_contact_algebraic_path.py test_general_contact_transient_plane.py::test_q4_constant_nodal_load_matches_free_acceleration_and_restart test_general_contact_transient_s3_history.py::test_s3_history_knot_split_restart_binds_history_and_profile test_general_contact_descriptor_directional_rates.py::test_directional_s3_tilted_impact_restart_preserves_physical_newmark test_installed_example.py
```

Reexecution is unnecessary for this unchanged slice; these are reproduction
instructions, not renewal of any frozen programme authority.
