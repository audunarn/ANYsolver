# Q4 structural and Q1 pressure-resolution screen

**Status:** linearized development evidence, 28 September 2026. No new
coupled contact solve, acceptance candidate or historical execution authority
is created by this screen.

## Decision question and method

The [fixed-geometry discriminator](general_contact_d1_linearized_front_development.md)
reproduced the completed coupled 16/24/32-Q4 partial-contact fields. This
screen separates structural resolution from pressure resolution before
another expensive coupled solve.

`scripts/general_contact_d1_pressure_space_screen.py` uses the same
source-only Q4 tangent, 0.3 N distributed load and 40 µm initial gap. It
integrates Q1 pressure against structural Q1 displacement over a common
refinement of their separate x grids, using exact two-point Gauss integration
for the polynomial products. Its quadratic pressure solution is refined by
active-set stationarity and checked for nonnegative pressure, weak gap,
complementarity, structural equilibrium and an independent physical gap over
the represented flat overlap. Equal structural and pressure grids replay the
previous fine-basis trends.

The raw policy/sweep report and log are
`reports/general_contact_d1_pressure_space_final_dev_20260928.json`
and its `.log` companion. The final 24 unique structural/pressure systems took
16.1 s in this source run; that is a development observation, not a
whole-route performance comparison with the nonlinear solver.

## Separate mesh effects

With **16 pressure columns fixed**, relative adjacent full-field pressure
changes decrease from 2.00% at 16→24 Q4 to 0.0199% at 96→128 Q4. But at
128 Q4, the fixed 16-column field still differs by 10.83% from the matched
128-column pressure field. Integrated pressure force differs by only
3.84×10⁻⁵ N. A stable structural refinement sequence at fixed pressure
resolution therefore cannot certify pressure-space accuracy.

At **128 Q4 fixed**, the full-field differences from its 128-column
pressure result are:

| Pressure columns | 8 | 16 | 24 | 32 | 48 | 64 | 96 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Relative L2 difference | 22.10% | 10.83% | 11.68% | 12.48% | 4.02% | 7.62% | 4.01% |

This pressure refinement is nonmonotone. The 8-column case reaches
−0.144 µm minimum physical gap; the 16–128-column cases stay above
−0.011 µm in the flat-overlap check. Those gaps are development diagnostics,
not the coupled solver's independent gap certificate.

## Structural-node-aligned front refinement

`scripts/general_contact_d1_front_cluster_screen.py` starts from 16
pressure cells over the full x span and subdivides the four cells in
`x∈[9/16,13/16]`, around the observed contact front. The selected pressure
knots are a subset of structural Q4 x nodes when the subdivision count is
`structural Q4 columns / 16`. The method retains nonnegative first-order
pressure functions and keeps pressure modes fixed during an analysis.

| Structural Q4 columns | 32 | 48 | 64 | 96 | 128 |
|---|---:|---:|---:|---:|---:|
| Clustered / fine pressure modes | 42 / 66 | 50 / 98 | 58 / 130 | 74 / 194 | 90 / 258 |
| Clustered vs fine relative L2 | 0.119% | 0.00136% | 0.000268% | 4.30×10⁻⁷% | 1.30×10⁻⁹% |

At 128 Q4, the aligned cluster reproduces the full fine-field within
1.30×10⁻¹¹ relative L2 with 90 rather than 258 modes. Its integrated force
and physical-gap minimum agree to numerical precision. This is a promising
**candidate for multiplier-space cost reduction** in this fixture, not a
measured solver speedup or continuum pressure convergence.

The deliberately over-resolved, nonmatching local cluster with ten pressure
subcells per base cell has 106 pressure modes but differs from the fine field
by 28.06% at the same 128-Q4 structure. Its active pressure-work map is full
row rank, yet the scaled active compliance condition rises to 4.62×10⁶,
versus 3.45×10⁵ for the aligned eight-subcell cluster. More pressure modes
or a smaller local pressure cell do not by themselves improve the result.

The raw aligned/nonmatching cluster report and log are
`reports/general_contact_d1_front_cluster_nested_screen_dev_20260928.json`
and its `.log` companion.

## Next action and limits

An opt-in structural-node-aligned selected-knot basis has now been added to
the existing mortar pressure transform, with stable material-node mode IDs,
explicit knot identity and restart binding. Its first bounded coupled press
and local work/tangent checks are recorded in the
[selected-basis development profile](../GENERAL_CONTACT_C1_SELECTED_Q1_PRESSURE_DEV.md).
Further coupled pressure-space and response checks are required before
comparing whole-route cost. Its knot selection
was informed by observed development states; a formal claim needs an
independent mechanics reference and frozen candidate inputs. It must not
weaken existing physical-gap, pressure or equilibrium gates.

The matched 128-column pressure field is a **discrete comparator**, not an
accepted continuum oracle. The nested basis reproduces that discrete field
on the tested meshes; it does not establish pressure convergence of the
underlying Q4/S3 partial-contact problem.
