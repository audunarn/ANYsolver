# Selected Q1 pressure knots on a refined Q4/S3 patch

**Status:** opt-in development candidate, 28 September 2026. C1 pressure
stability, installed-package qualification and independent acceptance remain
open.

## Interface and method

The existing refined Q4-source/S3-target augmented mortar route admits a
fixed pressure subspace with `ContactSolverSettings`:

```python
q4_source_pressure_basis="selected_q1_knots_dev"
q4_source_pressure_knot_columns=(0, 1, 3, 4)
```

Knot columns refer to the declared ordered Q4 source strip. They must be
strictly increasing structural-node columns from zero through the last
source cell. The resulting pressure basis is nonnegative, partitions unity,
has one stable material-node mode per selected knot on each strip row, and
remains fixed during the analysis. It interpolates linearly in ordered
reference face index between selected nodes. The original fine Q4 geometry,
common-refinement integration, physical-gap certificate and both bodies'
work maps remain in use. A quadrature refinement does not add multipliers.

Admission is limited to 2–128 ordered Q4 source cells against the admitted
refined S3 target, projected augmented normal contact, the Jet2 Q4/S3
derivative and exact pressure support. The selected knot list, basis version,
fine source IDs, mode IDs and full interpolation matrix are bound in restart.
An incompatible knot selection rejects the checkpoint. The option changes
neither the default fine pressure basis nor the historical macro-pair route.

## Evidence

The [pressure-space screen](reference_cases/general_contact_d1_pressure_space_screen_development.md)
motivated structural-node-aligned local knots, but uses a fixed-geometry
linearized model. Independent read-only scrutiny found no defect in its
mixed Q1 integration, constrained pressure solution or L2 comparison; it
did not assess this production implementation as accepted mechanics.

`tests/test_general_contact_pressure_basis.py` directly compares transformed
fine-face Q1 work with independent piecewise Q1 shape values, checks mode
rank and positivity, and verifies exact equivalence with the old macro-pair
transform where their knot selections coincide. The selected-manager test
checks admission, mapped active contact, a smooth-branch directional tangent,
mode identities and a changed-knot restart contract. The two focused basis
test files passed 34/34 in 9.16 s after the implementation.

The bounded ordinary nonlinear static four-Q4/two-S3 press with selected
knots `(0,1,3,4)` completed two force steps in 36.0 s. At the terminal
state it has eight supported pressure modes, scaled rank eight, two active
modes, −4.09 µm minimum gap against the declared 50 µm budget, 0.0320099 N
paired normal force on opposite bodies, 1.24×10⁻¹⁵ N equilibrium residual and
3.42×10⁻¹¹ Pa final multiplier change. A fresh model replayed the terminal
checkpoint exactly. Separately, a one-step checkpoint resumed through the
remaining load step to the same final displacement and checkpoint as the
uninterrupted solve; changing the knots rejected restart. The complete
development report and log are
`reports/general_contact_d1_selected_knots_4q4_split_restart_dev_20260928.json`
and its `.log` companion.

## Limits and next checks

The four-Q4 case demonstrates routing and local mechanics only. It does not
establish that the selected basis approximates the full pressure field in a
general moving-front problem. The 128-Q4 pressure comparison was in a
linearized source-only model and does not measure nonlinear whole-route
speed. A larger coupled run requires a registered pressure/response question,
independent mechanics reference, resource rationale and unchanged gap,
pressure and equilibrium gates. The next bounded check is coupled selected
versus fine pressure on an affordable partially contacting shell patch,
including pressure-space rank, virtual work and tangent under the
same mechanical inputs. No existing formal evidence is retroactively changed.
